from flask import Flask, redirect, url_for
from flask_login import LoginManager
from dotenv import load_dotenv
import os

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

login_manager = LoginManager()
login_manager.init_app(app)






@app.route('/accounts')  
def accounts():
    return redirect(url_for("signup"))

@app.route('/accounts/signup')  
def signup():
    return "Signup Page"  

@app.route('/accounts/login') 
def login():
    return "Login Page"  

if __name__ == "__main__":
    app.run()