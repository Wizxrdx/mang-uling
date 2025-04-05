from flask import render_template, Blueprint, redirect, url_for, session, flash, request, jsonify, send_file
from datetime import datetime, timedelta
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length
from fpdf import FPDF
import io

from app.file_generation import MyPDF
from app.utils import get_first_day_of_iso_week, get_readable_week_of_month

from .models import BagType, DailyProduction, Employee
from .data import IS_BUSY, DATA, WEEKLY_LOG, TODAY, lock, update_production_record

# Blueprint setup
main = Blueprint('main', __name__)

# Flask-WTF Login Form
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data  

        # Fetch employee from the database
        employee = Employee.query.filter_by(username=username).first()

        if employee and employee.check_password(password):  # Verify password
            session['username'] = username  # Store user session separately
            session['name'] = employee.name
            return redirect(url_for('main.index'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html', form=form)

@main.route('/logout', methods=['GET'])
def logout():
    if request.method == 'GET':
        session.pop('username', None)
        flash('You have been logged out.', 'info')
        return redirect(url_for('main.login'))

@main.route('/', methods=['GET'])
def index():
    if 'username' not in session:
        flash('You need to log in to access the dashboard.', 'warning')
        return redirect(url_for('main.login'))
    
    name = session.get('name', "Guest")

    return render_template(
        'index.html',
        user_name=name,
        current_date=datetime.now().strftime("%Y-%m-%d")
    )

@main.route('/status', methods=['GET'])
def status():
    if 'username' not in session:
        flash('You need to log in to access the dashboard.', 'warning')
        return redirect(url_for('main.login'))

    if IS_BUSY != False:
        return render_template('status.html',
                               color="#00FF00",
                               message="RUNNING")
    else:
        return render_template('status.html',
                               color="#FFFF00",
                               message="IDLE")

@main.route('/status/<size>', methods=['PUT'])
def put_status(size):
    global IS_BUSY
    if 'username' not in session:
        flash('You need to log in to access the dashboard.', 'warning')
        return redirect(url_for('main.login'))
    
    if request.method == 'PUT':
        if size == "stop":
            IS_BUSY = False
            return jsonify({"status": "success", "message": "Status updated successfully.", "value": IS_BUSY})
        
        if size in DATA:
            IS_BUSY = size
            return jsonify({"status": "success", "message": "Status updated successfully.", "value": IS_BUSY})
        return jsonify({"status": "error", "message": "Invalid size."})

@main.route('/count/<size>', methods=['PUT'])
def count(size):
    global DATA, IS_BUSY
    if request.method == 'PUT':
        update_production_record(size, 1)
        if DATA[size]["count"] >= DATA[size]["quota"]:
            IS_BUSY = False
        return jsonify({"status": "success", "message": "Count updated successfully."})
    
@main.route('/quota/<size>', methods=['GET'])
def get_quota(size):
    if 'username' not in session:
        flash('You need to log in to access the dashboard.', 'warning')
        return redirect(url_for('main.login'))
    
    if size not in DATA:
        return jsonify({"status": "error", "message": "Invalid size."}), 400
    
    msg = f"{str(DATA[size]["count"])}/{str(DATA[size]["quota"])} bags"
    prog = (DATA[size]["count"] / DATA[size]["quota"]) * 100
    run_button = f"""<button class="control-button" id="run-{size}" tooltip="Run the process">
<span class="material-symbols-outlined" id="icon">manufacturing</span>
</button>"""
    stop_button = f"""<button class="control-button" id="stop-{size}" tooltip="Stop the process">
<span class="material-symbols-outlined" id="icon">&#xe5c9;</span>
</button>"""
    edit_button = f"""<button class="control-button" id="edit-{size}" tooltip="Decrement">
<span class="material-symbols-outlined" id="icon">edit_square</span>
</button>"""
    button = stop_button if IS_BUSY == size else run_button
    return render_template('control.html',
                           title=f"{str(DATA[size]["size"])} kg bags",
                           subtitle="Packing Progress Report",
                           id=size,
                           start_button=button,
                           edit_button=edit_button,
                           message=msg,
                           value=DATA[size]["count"],
                           max=DATA[size]["quota"],
                           progress=f"{prog:.2f}%",
                           eta="ETA: 2 hours")

@main.route('/quota/<size>/<count>', methods=['POST'])
def post_quota(size, count):
    global DATA
    if 'username' not in session:
        flash('You need to log in to access the dashboard.', 'warning')
        return redirect(url_for('main.login'))
    
    if size not in DATA:
        return jsonify({"message": "Invalid size."}), 400
    
    try:
        count = int(count)
    except ValueError:
        return jsonify({"message": "Invalid count. Must be a number."}), 400
    
    if DATA[size]["count"]+1 > count:
        return jsonify({"message": "Quota must be greater than current count."f" Current count: {DATA[size]['count']}"}), 400
    
    DATA[size]["quota"] = count
    return jsonify({"status": "success",
                    "message": "Quota updated successfully.",
                    "value": DATA[size]})

@main.route('/log', methods=['GET'])
def log():
    if 'username' not in session:
        flash('You need to log in to access the dashboard.', 'warning')
        return redirect(url_for('main.login'))

    start_of_week = TODAY - timedelta(days=TODAY.weekday())  # Monday of current week
    end_of_week = start_of_week + timedelta(days=6)  # Sunday of current week

    return jsonify({
        "data": WEEKLY_LOG,
        "start_date": start_of_week.strftime("%b. %d, %Y"),
        "end_date": end_of_week.strftime("%b. %d, %Y")
    })

@main.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    selected_weeks = request.json.get('weeks', [])

    pdf = MyPDF(orientation="P", unit="mm", format="Letter")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Add an image at the top of the page
    pdf.image('app/static/logo.jpg', x=5, y=20, w=40)

    pdf.ln(10)
    pdf.set_font("Arial", style='B', size=32)
    pdf.cell(0, 8, txt="Weekly Sales Report", ln=True, align='C')
    pdf.ln(20)

    for week in selected_weeks:
        # Parse the week number from the input (e.g., "2025-W14")
        year, week_num = map(int, week.split('-W'))

        week_title = get_readable_week_of_month(year, week_num)
        pdf.set_font("Arial", style='B', size=14)
        pdf.cell(200, 10, f"{week_title}, {year}", ln=True)

        # Get the first day (Monday) of the week using the iso year and week
        week_start_date = get_first_day_of_iso_week(year, week_num)
        week_end_date = week_start_date + timedelta(days=6)

        # Query the daily sales data
        daily_sales = DailyProduction.query \
            .join(BagType) \
            .filter(
                DailyProduction.production_date.between(week_start_date.strftime('%Y-%m-%d'), week_end_date.strftime('%Y-%m-%d'))
            ) \
            .all()
        
        pdf.set_font("Arial", size=12)
        if not daily_sales:
            pdf.cell(200, 10, "No sales data available", ln=True)
            continue

        # Create the table header with day of the week (Monday to Sunday)
        pdf.set_fill_color(200, 220, 255)
        pdf.cell(15, 8, "", border=1, fill=True, align='C')
        for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun", "Total"]:
            pdf.set_font("Arial", style='B', size=12)
            pdf.cell(22, 8, day, border=1, fill=True, align='C')
        pdf.ln()

        # Initialize a dictionary to store daily sales for each day of the week
        weekly_data = {day: {"1kg": 0, "10kg": 0} for day in range(7)}  # Monday to Sunday

        # Populate weekly data from the sales records
        for record in daily_sales:
            production_date = datetime.strptime(record.production_date, "%Y-%m-%d")
            day_of_week = production_date.weekday()  # Monday = 0, Sunday = 6
            bag_type = record.bag_type.type
            quantity = record.quantity

            if bag_type == "1kg":
                weekly_data[day_of_week]["1kg"] += quantity
            elif bag_type == "10kg":
                weekly_data[day_of_week]["10kg"] += quantity

        # Add 1kg values row
        pdf.set_font("Arial", style='B', size=12)
        pdf.cell(15, 8, "1kg", border=1, align='C')
        for day in range(7):
            pdf.set_font("Arial", size=12)
            pdf.cell(22, 8, str(weekly_data[day]["1kg"]), border=1, align='C')
        total = str(sum(weekly_data[day]["1kg"] for day in range(7)))
        pdf.cell(22, 8, total, border=1, align='C')
        pdf.ln()

        # Add 10kg values row
        pdf.set_font("Arial", style='B', size=12)
        pdf.cell(15, 8, "10kg", border=1, align='C')
        for day in range(7):
            pdf.set_font("Arial", size=12)
            pdf.cell(22, 8, str(weekly_data[day]["10kg"]), border=1, align='C')
        total = str(sum(weekly_data[day]["10kg"] for day in range(7)))
        pdf.cell(22, 8, total, border=1, align='C')
        pdf.ln()

        pdf.ln(5)

    # Output PDF to memory
    pdf_output = io.BytesIO()
    pdf_output.write(pdf.output(dest="S").encode("latin1"))
    pdf_output.seek(0)

    return send_file(pdf_output, mimetype="application/pdf", as_attachment=False, download_name="log_report.pdf")