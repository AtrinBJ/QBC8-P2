from flask import Flask, redirect, url_for,render_template,request,flash,get_flashed_messages
from flask_login import LoginManager,UserMixin,login_user,logout_user,current_user,login_required
from dotenv import load_dotenv
from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,SubmitField
from wtforms.validators import DataRequired,Email,EqualTo,Length,Regexp
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
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
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default="user")  # Role column with default "user"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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
    username = StringField('username', validators=[DataRequired()])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message="Please enter a valid email address"),
        Regexp(r'[a-zA-Z0-9._%+-]+@[a-zA-Z.-]+\.[a-zA-Z]{2,3}',message="Invalid email address format")
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message="Password must be at least 8 characters long"),
        Regexp(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', 
               message="Password must contain at least one letter, one number, and one special character")
    ])    
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
        ])
    submit = SubmitField('Sign Up')  # This is the submit button


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log in')






@app.route('/')
def index():
    return 'hello'


@app.route('/accounts')  
@app.route('/accounts/')
def accounts():
    return render_template('accounts_landing.html')

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
        flash('Signup successful. Please log in.')
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

@app.route('/accounts/admin')
@login_required
def admin():
    if current_user.is_admin():
        return render_template('admin.html')  # Use a template
    else:
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('index'))



@app.route('/accounts/logout')
@login_required  
def logout():
    logout_user()
    return redirect(url_for("index"))   




if __name__ == "__main__":
  app.run(debug=True)