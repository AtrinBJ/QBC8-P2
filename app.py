from flask import Flask, redirect, url_for,render_template,request,flash,get_flashed_messages
from flask_login import LoginManager,UserMixin,login_user,logout_user,current_user,login_required
from dotenv import load_dotenv
from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,SubmitField
from wtforms.validators import DataRequired,Email,EqualTo,Length,Regexp
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import os

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
csrf = CSRFProtect(app)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, 'database', 'main.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DATABASE_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)



login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'You MUST Log in first!'
login_manager.login_message_category = 'error'


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200))
    reset_token = db.Column(db.String(200), nullable=True)  # New column for the reset token
    token_expiration = db.Column(db.DateTime, nullable=True)
    role = db.Column(db.String(20), default="user")  # Role column with default "user"
    created_at = db.Column(db.DateTime, default=datetime.now)

    def set_password(self, password):
        """Hash and set the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if the entered password matches the hashed password."""
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        """Check if the user has admin privileges."""
        return self.role == 'admin'



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



class Signupform(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(message="Username is required"), 
        Length(min=3, max=20, message="Username must be 3-20 characters long"),  # Length constraint
        Regexp(
            r'^[A-Za-z0-9_-]+$',
            message="Username can only contain letters, numbers, underscores, or hyphens"
        )
    ])
    email = StringField('Email', validators=[
        DataRequired("Email is required"),
        Length(min=3, max=80, message="Email must be 3-80 characters long"),  # Length constraint
        Email(message="Please enter a valid email address"),
        Regexp(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$',message="Please enter a valid email address. Example: yourname@example.com")
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, max=20, message="Password must be at least 8 characters long"),
        Regexp(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', 
               message="Password must contain at least one letter, one number, and one special character")
    ])    
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        Length(max=30, message="Password too long"),
        EqualTo('password', message='Passwords must match')
        ])
    submit = SubmitField('Sign Up')  # This is the submit button


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log in')

class RequestResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    username = StringField('Username', validators=[DataRequired()])
    submit = SubmitField('Request Password Reset')

class ResetPasswordForm(FlaskForm):
    # New Password Field with Validators
    password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, max=20, message="Password must be at least 8 characters long"),
        Regexp(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', 
               message="Password must contain at least one letter, one number, and one special character")
    ])

    # Confirm Password Field with Validators
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        Length(max=30, message="Password too long"),
        EqualTo('password', message='Passwords must match')
    ])

    submit = SubmitField('Reset Password')






@app.route('/')
def index():
    return render_template('index.html')


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.route('/accounts')  
@app.route('/accounts/')
def accounts():
    return render_template('index.html')

@app.route('/accounts/signup', methods=['GET', 'POST'])
def signup():
 if current_user.is_authenticated:
        return redirect(url_for("index")) 
 form = Signupform()
 if form.validate_on_submit():
    existing_user = User.query.filter_by(username=form.username.data).first()
    existing_email = User.query.filter_by(email=form.email.data).first() 
    if existing_user:
        flash('Username already exists. Please choose a different one.', 'error')
    elif existing_email:
        flash('Email already exists. Please use a different email.', 'error')
    else:
        new_user = User(username=form.username.data, email=form.email.data)
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit() 
        flash('Signup successful. Please log in.', 'success')
        return redirect(url_for('login'))  # Redirect to login after signup
 return render_template('signup.html', form=form)


@app.route('/accounts/login', methods = ['GET', 'POST'] ) 
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index")) 
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Login failed. Check your username and/or password.', 'error')    
    return render_template('login.html', form=form)

@app.route('/request_reset', methods=['GET', 'POST'])
def request_reset():
    form = RequestResetForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data, username=form.username.data).first()
        if user:
            token = os.urandom(16).hex()
            expiration = datetime.now() + timedelta(minutes=5) 
            user.reset_token = token
            user.token_expiration = expiration
            db.session.commit()
            flash('Password reset request received. Use the link below to reset your password.', 'info')
            return redirect(url_for('reset_password', token=token))
        flash('The combination of email and username was not found!', 'error')
        return redirect(url_for('request_reset'))
    return render_template('request_reset.html', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    # Check if user exists with the reset token
    user = User.query.filter_by(reset_token=token).first()

    if user and user.token_expiration > datetime.utcnow():  # Token is valid
        form = ResetPasswordForm()

        if form.validate_on_submit():
            # Hash the new password
            hashed_password = generate_password_hash(form.password.data)

            # Update the user's password and reset token
            user.password_hash = hashed_password
            user.reset_token = None  # Clear the reset token after reset
            user.token_expiration = None  # Clear the expiration time

            db.session.commit()  # Commit changes to the database

            flash('Your password has been successfully updated!', 'success')
            return redirect(url_for('login'))  # Redirect to login page after success
        
        return render_template('reset_password.html', form=form, token=token)

    else:
        flash('The reset link is either invalid or has expired.', 'danger')
        return redirect(url_for('request_reset'))



@app.route('/accounts/admin/dashboard')
@login_required
def admin():
    if current_user.is_admin():
        return render_template('admin_dashboard.html')
    else:
        flash('You do not have permission to access this page.', 'warning')
        return redirect(url_for('index'))
@app.route('/accounts/user/dashboard')
@login_required
def user_dashboard():
    if current_user.is_admin():
        return render_template('admin_dashboard.html')
    return render_template('user_dashboard.html')


@app.route('/accounts/logout')
@login_required  
def logout():
    logout_user()
    flash('You have been successfully logged out', 'success')
    return redirect(url_for("index"))   




if __name__ == "__main__":
  app.run(debug=True)