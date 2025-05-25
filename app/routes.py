import time
import threading
from flask import render_template, Blueprint, redirect, url_for, session, flash, request, jsonify, send_file, Response
from datetime import datetime, timedelta
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length
from fpdf import FPDF
import io

from app.file_generation import MyPDF
from app.utils import get_first_day_of_iso_week, get_readable_week_of_month

from .models import BagType, DailyProduction, Employee
from .data import State, get_production_record

# Blueprint setup
main = Blueprint('main', __name__)
notification_flag = False

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

        employee = State().login(username, password)

        if employee:  # Verify password
            session['username'] = username  # Store user session separately
            session['name'] = employee.name
            session['id'] = employee.id
            return redirect(url_for('main.index'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html', form=form)

@main.route('/logout', methods=['GET'])
def logout():
    if request.method == 'GET':
        session.pop('username', None)
        session.pop('name', None)
        session.pop('id', None)
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
        user_name=name
    )

@main.route('/date-range')
def date_range():
    if 'username' not in session:
        flash('You need to log in to access the dashboard.', 'warning')
        return redirect(url_for('main.login'))

    return render_template('date_range.html')

@main.route('/profile', methods=['GET'])
def profile():
    if 'username' not in session:
        flash('You need to log in to access the dashboard.', 'warning')
        return redirect(url_for('main.login'))
    
    return render_template('profile.html',
                           name=session.get('name', "Guest"),
                           username=session.get('username', ""))

@main.route('/update-profile', methods=['POST'])
def update_profile():
    if 'username' not in session:
        return jsonify({"status": "error", "message": "Not logged in"}), 401
    
    data = request.get_json()
    new_name = data.get('name', '').strip()
    new_password = data.get('password', '').strip()
    
    if not new_name and not new_password:
        return jsonify({"status": "error", "message": "No changes provided"}), 400
    
    employee = State().get_employee_record_by(session['id'])
    if not employee:
        return jsonify({"status": "error", "message": "User not found"}), 404
    
    try:
        if new_name:
            if len(new_name) < 2:
                return jsonify({"status": "error", "message": "Name must be at least 2 characters long"}), 400
            State().update_profile(session['username'], new_name, session['username'], new_password)
            session['name'] = new_name
        
        if new_password:
            if len(new_password) < 6:
                return jsonify({"status": "error", "message": "Password must be at least 6 characters long"}), 400
            State().update_profile(session['username'], session['name'], session['username'], new_password)
        
        # Clear all session data
        session.clear()
        
        return jsonify({
            "status": "success", 
            "message": "Profile updated successfully. Please log in again.",
            "redirect": url_for('main.logout')
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@main.route('/status', methods=['GET'])
def status():
    current_status = State().get_is_busy()

    if 'username' not in session:
        flash('You need to log in to access the dashboard.', 'warning')
        return redirect(url_for('main.login'))

    if current_status != False:
        # Running
        return render_template('status.html',
                               background_color_running="#00FF00",
                               color_running="#000000",
                               background_color_idle="#d3d3d3",
                               color_idle="#b0b0b0")
    else:
        # Idle
        return render_template('status.html',
                               background_color_running="#d3d3d3",
                               color_running="#b0b0b0",
                               background_color_idle="#FFFF00",
                               color_idle="#000000")

@main.route('/status/<size>', methods=['PUT'])
def put_status(size):
    current_status = State().get_is_busy()
    DATA = State().DATA

    if 'username' not in session:
        flash('You need to log in to access the dashboard.', 'warning')
        return redirect(url_for('main.login'))
    
    if request.method == 'PUT':
        if size == "stop":
            res = State().start(None)
            return jsonify({"status": "success", "message": "Status updated successfully.", "value": current_status})
        
        if size in DATA:
            res = State().start(size)
            return jsonify({"status": "success", "message": "Status updated successfully.", "value": current_status})
        return jsonify({"status": "error", "message": "Invalid size."})

@main.route('/count/<size>', methods=['PUT'])
def count(size):
    DATA = State().DATA

    if request.method == 'PUT':
        State().update_production_record(size, 1)
        if DATA[size]["count"] >= DATA[size]["quota"]:
            State().set_notification(size)
            State().auto_start()
        return jsonify({"status": "success", "message": "Count updated successfully."})
    
@main.route('/quota/<size>', methods=['GET'])
def get_quota(size):
    current_status = State().get_is_busy()
    DATA = State().DATA

    if 'username' not in session:
        flash('You need to log in to access the dashboard.', 'warning')
        return redirect(url_for('main.login'))
    
    if size not in State().DATA:
        return jsonify({"status": "error", "message": "Invalid size."}), 400
    
    msg = f"{str(DATA[size]['count'])}/{str(DATA[size]['quota'])} bags"
    prog = (DATA[size]["count"] / DATA[size]["quota"]) * 100
    run_button = f"""<button class="control-button" id="run-{size}" tooltip="Run the process">
<span class="material-symbols-outlined" id="icon">play_arrow</span>
</button>"""
    stop_button = f"""<button class="control-button" id="stop-{size}" tooltip="Stop the process">
<span class="material-symbols-outlined" id="icon">stop</span>
</button>"""
    edit_button = f"""<button class="control-button" id="edit-{size}" tooltip="Decrement">
<span class="material-symbols-outlined" id="icon">edit_square</span>
</button>"""
    button = stop_button if current_status == size else run_button
    return render_template('control.html',
                           title=f"{str(DATA[size]['size'])} kg bags",
                           subtitle="Packing Progress Report",
                           id=size,
                           start_button=button,
                           edit_button=edit_button,
                           message=msg,
                           value=DATA[size]["count"],
                           max=DATA[size]["quota"],
                           progress=f"{prog:.2f}%",
                        #    eta="ETA: 2 hours"
                           )

@main.route('/quota/<size>/<count>', methods=['POST'])
def post_quota(size, count):
    DATA = State().DATA

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
    
    State().update_quota(datetime.now(), size, count)
    return jsonify({"status": "success",
                    "message": "Quota updated successfully.",
                    "value": DATA[size]})

@main.route("/api/notify", methods=["GET"])
def check_notification():
    return jsonify({"message": State().get_notification()})

@main.route('/log', methods=['GET'])
def log():
    if 'username' not in session:
        flash('You need to log in to access the dashboard.', 'warning')
        return redirect(url_for('main.login'))

    start_of_week = State().TODAY - timedelta(days=State().TODAY.weekday())  # Monday of current week
    end_of_week = start_of_week + timedelta(days=6)  # Sunday of current week

    return jsonify({
        "data": State().get_weekly_log(),
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
        daily_sales = get_production_record(week_start_date, week_end_date)
        
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
        weekly_data = {day: {"1kg": 0, "5kg": 0} for day in range(7)}  # Monday to Sunday

        # Populate weekly data from the sales records
        for record in daily_sales:
            production_date = record[0]
            day_of_week = datetime.strptime(production_date, "%Y-%m-%d").weekday()
            bag_type = record[1]
            quantity = record[2]

            if bag_type == "1kg":
                weekly_data[day_of_week]["1kg"] += quantity
            elif bag_type == "5kg":
                weekly_data[day_of_week]["5kg"] += quantity

        # Add 1kg values row
        pdf.set_font("Arial", style='B', size=12)
        pdf.cell(15, 8, "1kg", border=1, align='C')
        for day in range(7):
            pdf.set_font("Arial", size=12)
            pdf.cell(22, 8, str(weekly_data[day]["1kg"]), border=1, align='C')
        total = str(sum(weekly_data[day]["1kg"] for day in range(7)))
        pdf.cell(22, 8, total, border=1, align='C')
        pdf.ln()

        # Add 5kg values row
        pdf.set_font("Arial", style='B', size=12)
        pdf.cell(15, 8, "5kg", border=1, align='C')
        for day in range(7):
            pdf.set_font("Arial", size=12)
            pdf.cell(22, 8, str(weekly_data[day]["5kg"]), border=1, align='C')
        total = str(sum(weekly_data[day]["5kg"] for day in range(7)))
        pdf.cell(22, 8, total, border=1, align='C')
        pdf.ln()

        pdf.ln(5)

    # Output PDF to memory
    pdf_output = io.BytesIO()
    pdf_output.write(pdf.output(dest="S").encode("latin1"))
    pdf_output.seek(0)

    return send_file(pdf_output, mimetype="application/pdf", as_attachment=False, download_name="log_report.pdf")

@main.route('/date-range-data', methods=['POST'])
def date_range_data():
    try:
        if 'username' not in session:
            return jsonify({"error": "Unauthorized"}), 401
        
        data = request.get_json()
        if not data or 'start_date' not in data or 'end_date' not in data:
            return jsonify({"error": "Missing date range parameters"}), 400

        start_date = datetime.strptime(data.get('start_date'), '%Y-%m-%d')
        end_date = datetime.strptime(data.get('end_date'), '%Y-%m-%d')
        
        # Query daily production data for the selected date range
        daily_production = get_production_record(start_date, end_date)
        
        if not daily_production:
            return jsonify({
                'labels': [],
                'datasets': []
            })
        
        # Process the data for chart visualization
        chart_data = {
            'labels': [],
            'datasets': []
        }
        
        # Get unique bag types
        bag_types = set(dp[1] for dp in daily_production)
        
        # Initialize datasets for each bag type
        for bag_type in bag_types:
            chart_data['datasets'].append({
                'label': f'{bag_type} kg bags',
                'data': [],
                'borderColor': f'rgb({hash(bag_type) % 255}, {hash(bag_type) % 255}, {hash(bag_type) % 255})',
                'fill': False
            })
        
        # Group data by date
        date_groups = {}
        for dp in daily_production:
            date_str = dp[0]  # Already a string in YYYY-MM-DD format
            if date_str not in date_groups:
                date_groups[date_str] = {}
            if dp[1] not in date_groups[date_str]:
                date_groups[date_str][dp[1]] = 0
            date_groups[date_str][dp[1]] += dp[2]
        
        # Sort dates and populate chart data
        sorted_dates = sorted(date_groups.keys())
        chart_data['labels'] = sorted_dates
        
        for date in sorted_dates:
            for i, bag_type in enumerate(bag_types):
                count = date_groups[date].get(bag_type, 0)
                chart_data['datasets'][i]['data'].append(count)
        
        return jsonify(chart_data)
    except Exception as e:
        print(f"Error in date_range_data: {str(e)}")  # Add logging
        return jsonify({"error": str(e)}), 500