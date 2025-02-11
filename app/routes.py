from flask import render_template, Blueprint, redirect, url_for, session, flash
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
COUNT = 100
QUOTA = 10

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

@main.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.login'))

@main.route('/')
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

@main.route('/status')
def status():
    if 'username' not in session:
        flash('You need to log in to access the dashboard.', 'warning')
        return redirect(url_for('main.login'))
    
    if IS_BUSY:
        return render_template('status.html', id="status-running", message="RUNNING")
    else:    
        return render_template('status.html', id="status-idle", message="IDLE")
    
@main.route('/count')
def count():
    if 'username' not in session:
        flash('You need to log in to access the dashboard.', 'warning')
        return redirect(url_for('main.login'))
    
    return render_template('label.html', title="Packed Today", message=str(COUNT) + " bags")
    
@main.route('/quota')
def quota():
    if 'username' not in session:
        flash('You need to log in to access the dashboard.', 'warning')
        return redirect(url_for('main.login'))
    
    return render_template('label.html', title="Packing Quota", message=str(QUOTA) + " bags")