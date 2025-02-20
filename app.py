from flask import Flask, redirect, url_for,render_template,request,flash,get_flashed_messages
from flask_login import LoginManager,UserMixin,login_user,logout_user,current_user,login_required
from dotenv import load_dotenv
import os

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'You MUST Log in first!'


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