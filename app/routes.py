from flask import render_template, Blueprint, redirect, url_for, session, flash, request, jsonify
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length

# Blueprint setup
main = Blueprint('main', __name__)

# Mock user data (replace with a database in a real app)
USERS = [
    {
        'username': 'admin',
        'password': '1234',
        'name': 'Admin'
    },
    {
        'username': 'user',
        'password': '1234',
        'name': 'User'
    }
]

IS_BUSY = False
DATA = {
    "1kg": {
        "size": 1,
        "count": 10,
        "quota": 100
    },
    "10kg": {
        "size": 10,
        "count": 25,
        "quota": 50
    },
}

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

        user = next((user for user in USERS if user['username'] == username), None)
        
        if user and user['password'] == password:
            session['username'] = username
            session['name'] = user['name']
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
    if request.method == 'GET':
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
    global IS_BUSY
    if 'username' not in session:
        flash('You need to log in to access the dashboard.', 'warning')
        return redirect(url_for('main.login'))
        
    if IS_BUSY:
        return render_template('status.html', id="status-running", message="RUNNING")
    else:    
        return render_template('status.html', id="status-idle", message="IDLE")

@main.route('/status/<size>', methods=['PUT'])
def put_status(size):
    global IS_BUSY
    if 'username' not in session:
        flash('You need to log in to access the dashboard.', 'warning')
        return redirect(url_for('main.login'))
    
    if request.method == 'PUT':
        if size == "":
            IS_BUSY = False
        
        if size in DATA:
            IS_BUSY = size
            return jsonify({"status": "success", "message": "Status updated successfully.", "value": IS_BUSY})
        return jsonify({"status": "error", "message": "Invalid size."})

@main.route('/count/<size>', methods=['PUT'])
def count(size):
    global COUNT
    
    if 'username' not in session:
        flash('You need to log in to access the dashboard.', 'warning')
        return redirect(url_for('main.login'))
        
    if request.method == 'PUT':
        DATA[size]["count"] += 1
        return jsonify({"status": "success", "message": "Count updated successfully."})
    
@main.route('/quota/<size>', methods=['GET', 'POST'])
def quota(size):
    if 'username' not in session:
        flash('You need to log in to access the dashboard.', 'warning')
        return redirect(url_for('main.login'))
    
    if size not in DATA:
        return jsonify({"status": "error", "message": "Invalid size."})
    
    if request.method == 'POST':
        DATA[size]["quota"] += 1
        return jsonify({"status": "success",
                        "message": "Quota updated successfully.",
                        "value": DATA[size]})
    
    msg = f"{str(DATA[size]["count"])}/{str(DATA[size]["quota"])} bags"
    prog = (DATA[size]["count"] / DATA[size]["quota"]) * 100
    return render_template('control.html',
                           title=f"{str(DATA[size]["size"])} kg bags",
                           subtitle="Packing Progress Report",
                           message=msg,
                           value=DATA[size]["count"],
                           max=DATA[size]["quota"],
                           progress=f"{prog:.2f}%",
                           eta="ETA: 2 hours")