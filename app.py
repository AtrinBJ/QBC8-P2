from flask import Flask, redirect, url_for,render_template,request,flash,get_flashed_messages
from flask_login import LoginManager,UserMixin,login_user,logout_user,current_user,login_required
from dotenv import load_dotenv
from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,SubmitField
from wtforms.validators import DataRequired,Email,EqualTo,Length,Regexp
from flask_wtf.csrf import CSRFProtect
import os

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
csrf = CSRFProtect(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'You MUST Log in first!'


class User(UserMixin, db.Model):
    pass


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



class Signupform(FlaskForm):
    username = StringField('usename', validators=[DataRequired()])
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









@app.route('/accounts')  
def accounts():
    return redirect(url_for("signup"))

@app.route('/accounts/signup', methods=['GET', 'POST'])
def signup():
    form = Signupform()
    if form.validate_on_submit():
            ###make new user , check duplicates
            username=form.username.data,
            email=form.email.data
            password = form.password.data
            flash('Signup successful. Please log in.')
            return render_template('login.html')
    return render_template('signup.html', form=form)

@app.route('/accounts/login', methods = ['GET', 'POST'] ) 
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index")) 
    
    if request.method == 'POST':       
        login_user()
        return "Login Page"

    return redirect(url_for("login"))

@app.route('/accounts/logout')
@login_required  
def logout():
    logout_user()
    return redirect(url_for("index"))   

if __name__ == "__main__":
    app.run()