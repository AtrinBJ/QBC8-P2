from flask import Flask, redirect, url_for
from flask_login import LoginManager,UserMixin,login_user,logout_user
from dotenv import load_dotenv
import os

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

login_manager = LoginManager()
login_manager.init_app(app)


class User(UserMixin, db.Model):
    pass

@login_manager.user_loader
def load_user():
    pass









@app.route('/accounts')  
def accounts():
    return redirect(url_for("signup"))

@app.route('/accounts/signup')  
def signup():
    return "Signup Page"  

@app.route('/accounts/login') 
def login():
    login_user()
    return "Login Page"

@app.route('/accounts/logout')  
def logout():
    logout_user()
    return redirect(url_for("login"))   

if __name__ == "__main__":
    app.run()