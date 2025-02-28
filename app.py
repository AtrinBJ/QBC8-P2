# وارد کردن کتابخانه‌های مورد نیاز
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
import requests
import json
import random
import string
import itertools
import io
import pandas as pd
from datetime import datetime, timedelta
import os
from werkzeug.exceptions import HTTPException

# تنظیمات اولیه فلسک
app = Flask(__name__)
# کلید رمزنگاری برای سشن‌ها - در محیط تولید باید تغییر کند
app.config['SECRET_KEY'] = 'your-secret-key-here'
# آدرس دیتابیس SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# تنظیمات ایمیل
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'at690077@gmail.com'  # ایمیل خود را وارد کنید
app.config['MAIL_PASSWORD'] = 'freo lhbx uiqj dykq'  # رمز عبور اپلیکیشن (App Password) خود را وارد کنید
app.config['MAIL_DEFAULT_SENDER'] = 'at690077@gmail.com'  # ایمیل خود را وارد کنید

# راه‌اندازی Flask-Login برای مدیریت سشن‌های کاربران
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # مسیر صفحه لاگین

# راه‌اندازی SQLAlchemy
db = SQLAlchemy(app)

# راه‌اندازی سیستم ایمیل
mail = Mail(app)


# تعریف مدل‌های دیتابیس
class User(UserMixin, db.Model):
    """مدل کاربر برای ذخیره اطلاعات کاربران"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

    # ارتباط‌ها با استفاده از back_populates به جای backref
    quizzes = db.relationship('QuizResult', backref='user', lazy=True)
    sent_tickets = db.relationship('Ticket', foreign_keys='Ticket.user_id', back_populates='sender', lazy=True)
    received_tickets = db.relationship('Ticket', foreign_keys='Ticket.recipient_id', back_populates='recipient',
                                       lazy=True)
    ticket_messages = db.relationship('TicketMessage', backref='author', lazy=True)


class VerificationCode(db.Model):
    """مدل کد تأیید برای ذخیره کدهای تأیید ایمیل"""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    code = db.Column(db.String(6), nullable=False)
    purpose = db.Column(db.String(20), nullable=False)  # register, login, update
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)

    def is_valid(self):
        """بررسی اعتبار کد تأیید"""
        return not self.is_used and datetime.utcnow() <= self.expires_at


@login_manager.user_loader
def load_user(user_id):
    """تابع لازم برای Flask-Login جهت بارگذاری کاربر"""
    return User.query.get(int(user_id))


class Question(db.Model):
    """مدل سوال برای ذخیره سوالات کوییز"""
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    question_text = db.Column(db.String(500), nullable=False)
    correct_answer = db.Column(db.String(200), nullable=False)
    # گزینه‌های غلط به صورت JSON ذخیره می‌شوند
    wrong_answers = db.Column(db.String(500), nullable=False)


class QuizResult(db.Model):
    """مدل نتایج برای ذخیره نتایج کوییزها"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    time_taken = db.Column(db.Integer, nullable=False)  # زمان به ثانیه
    answers = db.Column(db.Text, nullable=True)  # پاسخ‌های کاربر به صورت JSON


# مدل‌های داده‌ای تیکت
class Ticket(db.Model):
    """مدل تیکت برای ذخیره تیکت‌های کاربران"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # فرستنده تیکت
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # گیرنده تیکت
    title = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='باز')  # وضعیت: باز، در حال بررسی، بسته
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ارتباط یک به چند با پیام‌های تیکت
    messages = db.relationship('TicketMessage', backref='ticket', lazy=True, cascade="all, delete-orphan")

    # ارتباط با فرستنده و گیرنده با استفاده از back_populates به جای backref
    sender = db.relationship('User', foreign_keys=[user_id], back_populates='sent_tickets', lazy=True)
    recipient = db.relationship('User', foreign_keys=[recipient_id], back_populates='received_tickets', lazy=True)


class TicketMessage(db.Model):
    """مدل پیام‌های تیکت برای ذخیره پیام‌های مربوط به هر تیکت"""
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)  # آیا پیام توسط ادمین ارسال شده است
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


# توابع مدیریت کدهای تأیید ایمیل
def generate_verification_code(email, purpose="register"):
    """ایجاد کد تأیید 6 رقمی و ذخیره آن در پایگاه داده"""
    # حذف کدهای قبلی با همان هدف برای ایمیل داده شده
    VerificationCode.query.filter_by(email=email, purpose=purpose, is_used=False).delete()
    db.session.commit()

    # ایجاد کد تصادفی 6 رقمی
    code = ''.join(random.choices(string.digits, k=6))

    # تعیین زمان انقضا (15 دقیقه)
    expires_at = datetime.utcnow() + timedelta(minutes=15)

    # ذخیره کد در پایگاه داده
    verification = VerificationCode(
        email=email,
        code=code,
        purpose=purpose,
        expires_at=expires_at
    )
    db.session.add(verification)
    db.session.commit()

    return code


def send_verification_email(email, code, purpose="register"):
    """ارسال ایمیل حاوی کد تأیید با قالب HTML"""
    subject_map = {
        "register": "کد تأیید ثبت نام در سیستم کوییز",
        "login": "کد تأیید ورود به سیستم کوییز",
        "update": "کد تأیید تغییر اطلاعات کاربری"
    }

    # انتخاب عنوان مناسب
    subject = subject_map.get(purpose, "کد تأیید سیستم کوییز")

    # قالب HTML ایمیل
    html_template = f'''
    <!DOCTYPE html>
    <html dir="rtl" lang="fa">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            @font-face {{
                font-family: 'Vazir';
                src: url('https://cdn.jsdelivr.net/gh/rastikerdar/vazir-font@v27.2.2/dist/Vazir.eot');
                src: url('https://cdn.jsdelivr.net/gh/rastikerdar/vazir-font@v27.2.2/dist/Vazir.eot?#iefix') format('embedded-opentype'),
                     url('https://cdn.jsdelivr.net/gh/rastikerdar/vazir-font@v27.2.2/dist/Vazir.woff2') format('woff2'),
                     url('https://cdn.jsdelivr.net/gh/rastikerdar/vazir-font@v27.2.2/dist/Vazir.woff') format('woff'),
                     url('https://cdn.jsdelivr.net/gh/rastikerdar/vazir-font@v27.2.2/dist/Vazir.ttf') format('truetype');
            }}
            body {{
                font-family: 'Vazir', Tahoma, sans-serif;
                color: #ffffff;
                margin: 0;
                padding: 0;
                background-color: #1a1a1a;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background-color: #0d6efd;
                color: white;
                padding: 20px;
                text-align: center;
                border-radius: 10px 10px 0 0;
            }}
            .content {{
                background-color: rgba(40, 42, 54, 0.8);
                border: 1px solid rgba(100, 100, 255, 0.3);
                padding: 30px;
                border-radius: 0 0 10px 10px;
            }}
            .verification-code {{
                font-size: 32px;
                letter-spacing: 5px;
                color: #50fa7b;
                background-color: rgba(40, 42, 54, 0.6);
                padding: 10px;
                text-align: center;
                margin: 20px 0;
                border-radius: 5px;
                border: 1px solid rgba(80, 250, 123, 0.5);
            }}
            .note {{
                color: #f8f8f2;
                font-size: 14px;
                text-align: center;
                margin-top: 20px;
                opacity: 0.8;
            }}
            .footer {{
                margin-top: 30px;
                text-align: center;
                font-size: 12px;
                color: #6272a4;
            }}
            .banner {{
                width: 100%;
                height: 5px;
                background: linear-gradient(90deg, #ff5555, #ff79c6, #bd93f9, #8be9fd, #50fa7b, #f1fa8c);
                margin-bottom: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>سیستم کوییز آنلاین</h1>
            </div>
            <div class="content">
                <div class="banner"></div>
                <h2>کد تأیید شما</h2>
                <p>با سلام،</p>
                <p>
                    {'کد تأیید ثبت نام شما در سیستم کوییز:' if purpose == 'register' else
    'کد تأیید ورود شما به سیستم کوییز:' if purpose == 'login' else
    'کد تأیید تغییر اطلاعات کاربری شما در سیستم کوییز:'}
                </p>
                <div class="verification-code">{code}</div>
                <p class="note">این کد به مدت 15 دقیقه معتبر است.</p>
                <div class="footer">
                    <p>© سیستم کوییز آنلاین - {datetime.now().year}</p>
                    <p>این یک ایمیل خودکار است، لطفاً به آن پاسخ ندهید.</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''

    # بدنه ساده متنی (برای مشاهده در کلاینت‌های ایمیل بدون پشتیبانی HTML)
    text_body = f'''با سلام

    {'کد تأیید ثبت نام شما در سیستم کوییز:' if purpose == 'register' else
    'کد تأیید ورود شما به سیستم کوییز:' if purpose == 'login' else
    'کد تأیید تغییر اطلاعات کاربری شما در سیستم کوییز:'} {code}

    این کد به مدت 15 دقیقه معتبر است.
    '''

    try:
        msg = Message(
            subject=subject,
            recipients=[email],
            body=text_body,  # نسخه متنی
            html=html_template  # نسخه HTML
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f"خطا در ارسال ایمیل: {str(e)}")
        return False


def verify_code(email, code, purpose="register"):
    """بررسی صحت کد تأیید وارد شده"""
    verification = VerificationCode.query.filter_by(
        email=email,
        code=code,
        purpose=purpose,
        is_used=False
    ).first()

    if not verification:
        return False

    if not verification.is_valid():
        return False

    # علامت‌گذاری کد به عنوان استفاده شده
    verification.is_used = True
    db.session.commit()

    return True


# === مسیرهای برنامه ===

@app.route('/')
def index():
    """صفحه اصلی برنامه"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # هدایت به صفحه پروفایل به جای نمایش صفحه اصلی
    return redirect(url_for('profile'))


@app.route('/categories')
@login_required
def categories():
    """نمایش صفحه دسته‌بندی‌های کوییز"""
    # دریافت کاربر جاری
    user = User.query.get(session['user_id'])

    # دریافت تمام دسته‌بندی‌های موجود
    categories = db.session.query(Question.category).distinct().all()
    categories = [cat[0] for cat in categories]

    return render_template('index.html', categories=categories, user=user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """مدیریت ورود کاربران با تأیید ایمیل یا رمز عبور"""
    if request.method == 'POST':
        # حالت 1: ورود با نام کاربری و رمز عبور
        if 'login_type' in request.form and request.form['login_type'] == 'password':
            username = request.form['username']
            password = request.form['password']
            user = User.query.filter_by(username=username).first()

            if user and check_password_hash(user.password_hash, password):
                login_user(user)
                session['user_id'] = user.id
                flash('با موفقیت وارد شدید')
                return redirect(url_for('profile'))

            flash('نام کاربری یا رمز عبور اشتباه است')
            return redirect(url_for('login'))

        # حالت 2: درخواست ورود با ایمیل
        elif 'login_type' in request.form and request.form['login_type'] == 'email':
            username = request.form['username']
            user = User.query.filter_by(username=username).first()

            if not user:
                flash('کاربری با این نام کاربری یافت نشد')
                return redirect(url_for('login'))

            try:
                # ایجاد و ارسال کد تأیید
                code = generate_verification_code(user.email, purpose="login")
                email_sent = send_verification_email(user.email, code, purpose="login")

                if email_sent:
                    # ذخیره موقت اطلاعات در session
                    session['temp_username'] = username
                    session['temp_email'] = user.email
                    session['verification_purpose'] = "login"

                    return render_template('verify_email.html', email=user.email, purpose="login")
                else:
                    flash('خطا در ارسال ایمیل تأیید. لطفاً دوباره تلاش کنید یا از روش ورود با رمز عبور استفاده کنید.')
                    return redirect(url_for('login'))
            except Exception as e:
                print(f"خطا در فرآیند ورود با ایمیل: {str(e)}")
                flash('خطا در فرآیند ورود با ایمیل. لطفاً از روش ورود با رمز عبور استفاده کنید.')
                return redirect(url_for('login'))

        # حالت 3: تأیید کد ارسال شده برای ورود
        elif 'verify_code' in request.form and 'verification_purpose' in session and session[
            'verification_purpose'] == "login":
            try:
                code = request.form['verify_code']
                username = session.get('temp_username')
                email = session.get('temp_email')

                if not username or not email:
                    flash('اطلاعات نامعتبر. لطفاً دوباره تلاش کنید.')
                    return redirect(url_for('login'))

                user = User.query.filter_by(username=username).first()
                if not user:
                    flash('کاربری با این مشخصات یافت نشد')
                    return redirect(url_for('login'))

                # بررسی صحت کد
                if verify_code(email, code, purpose="login"):
                    # پاکسازی اطلاعات موقت
                    for key in ['temp_username', 'temp_email', 'verification_purpose']:
                        if key in session:
                            session.pop(key)

                    # ورود کاربر
                    login_user(user)
                    session['user_id'] = user.id
                    flash('با موفقیت وارد شدید')
                    return redirect(url_for('profile'))
                else:
                    flash('کد تأیید نامعتبر یا منقضی شده است. لطفاً دوباره تلاش کنید.')
                    return render_template('verify_email.html', email=email, purpose="login")
            except Exception as e:
                print(f"خطا در تأیید کد: {str(e)}")
                flash('خطا در تأیید کد. لطفاً دوباره تلاش کنید.')
                return redirect(url_for('login'))

        # حالت 4: درخواست ارسال مجدد کد
        elif 'resend_code' in request.form:
            try:
                email = session.get('temp_email')
                purpose = session.get('verification_purpose')

                if not email or not purpose:
                    flash('اطلاعات نامعتبر. لطفاً دوباره تلاش کنید.')
                    return redirect(url_for('login'))

                # ایجاد و ارسال کد جدید
                code = generate_verification_code(email, purpose=purpose)
                if send_verification_email(email, code, purpose=purpose):
                    flash('کد تأیید جدید ارسال شد.')
                else:
                    flash('خطا در ارسال ایمیل تأیید. لطفاً دوباره تلاش کنید.')

                return render_template('verify_email.html', email=email, purpose=purpose)
            except Exception as e:
                print(f"خطا در ارسال مجدد کد: {str(e)}")
                flash('خطا در ارسال مجدد کد. لطفاً دوباره تلاش کنید.')
                return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """مدیریت ثبت نام کاربران جدید با تأیید ایمیل"""
    if request.method == 'POST':
        # حالت 1: ارسال فرم اصلی ثبت نام
        if 'username' in request.form and 'email' in request.form and 'password' in request.form and 'verify_email' not in request.form:
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']

            # بررسی تکراری نبودن نام کاربری
            if User.query.filter_by(username=username).first():
                flash('این نام کاربری قبلاً ثبت شده است')
                return redirect(url_for('register'))

            # بررسی تکراری نبودن ایمیل
            if User.query.filter_by(email=email).first():
                flash('این ایمیل قبلاً ثبت شده است')
                return redirect(url_for('register'))

            try:
                # ایجاد و ارسال کد تأیید
                code = generate_verification_code(email, purpose="register")
                if send_verification_email(email, code, purpose="register"):
                    # ذخیره موقت اطلاعات در session برای استفاده بعدی
                    session['temp_username'] = username
                    session['temp_email'] = email
                    session['temp_password'] = password
                    session['verification_purpose'] = "register"

                    return render_template('verify_email.html', email=email, purpose="register")
                else:
                    flash('خطا در ارسال ایمیل تأیید. لطفاً دوباره تلاش کنید.')
                    return redirect(url_for('register'))
            except Exception as e:
                print(f"خطا در ارسال ایمیل تأیید: {str(e)}")
                flash('خطا در ارسال ایمیل تأیید. لطفاً دوباره تلاش کنید.')
                return redirect(url_for('register'))

        # حالت 2: تأیید کد ارسال شده
        elif 'verify_code' in request.form and 'verification_purpose' in session:
            try:
                code = request.form['verify_code']
                email = session.get('temp_email')
                purpose = session.get('verification_purpose')

                if not email or not purpose:
                    flash('اطلاعات نامعتبر. لطفاً دوباره ثبت نام کنید.')
                    return redirect(url_for('register'))

                # بررسی صحت کد
                if verify_code(email, code, purpose):
                    if purpose == "register":
                        # ایجاد کاربر جدید
                        user = User(
                            username=session.get('temp_username'),
                            email=email,
                            password_hash=generate_password_hash(session.get('temp_password'))
                        )
                        db.session.add(user)
                        db.session.commit()

                        # پاکسازی اطلاعات موقت
                        for key in ['temp_username', 'temp_email', 'temp_password', 'verification_purpose']:
                            if key in session:
                                session.pop(key)

                        # ورود کاربر
                        login_user(user)
                        session['user_id'] = user.id
                        flash('ثبت نام با موفقیت انجام شد')
                        return redirect(url_for('profile'))
                else:
                    flash('کد تأیید نامعتبر یا منقضی شده است. لطفاً دوباره تلاش کنید.')
                    return render_template('verify_email.html', email=email, purpose=purpose)
            except Exception as e:
                print(f"خطا در تأیید کد: {str(e)}")
                flash('خطا در تأیید کد. لطفاً دوباره تلاش کنید.')
                return redirect(url_for('register'))

        # حالت 3: درخواست ارسال مجدد کد
        elif 'resend_code' in request.form:
            try:
                email = session.get('temp_email')
                purpose = session.get('verification_purpose')

                if not email or not purpose:
                    flash('اطلاعات نامعتبر. لطفاً دوباره ثبت نام کنید.')
                    return redirect(url_for('register'))

                # ایجاد و ارسال کد جدید
                code = generate_verification_code(email, purpose=purpose)
                if send_verification_email(email, code, purpose=purpose):
                    flash('کد تأیید جدید ارسال شد.')
                else:
                    flash('خطا در ارسال ایمیل تأیید. لطفاً دوباره تلاش کنید.')

                return render_template('verify_email.html', email=email, purpose=purpose)
            except Exception as e:
                print(f"خطا در ارسال مجدد کد: {str(e)}")
                flash('خطا در ارسال مجدد کد. لطفاً دوباره تلاش کنید.')
                return redirect(url_for('register'))

    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    """خروج کاربر از سیستم"""
    logout_user()
    session.clear()
    flash('با موفقیت خارج شدید')
    return redirect(url_for('login'))


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """ویرایش اطلاعات کاربری با تأیید ایمیل"""
    user = User.query.get(session['user_id'])
    if not user:
        flash('خطا در دریافت اطلاعات کاربر')
        return redirect(url_for('logout'))

    if request.method == 'POST':
        # حالت 1: ارسال فرم اصلی ویرایش اطلاعات
        if 'submit_edit' in request.form:
            new_username = request.form.get('username', '').strip()
            new_email = request.form.get('email', '').strip()
            current_password = request.form.get('current_password', '')
            new_password = request.form.get('new_password', '')

            # تعیین چه فیلدی تغییر کرده است
            changes = {}
            verification_needed = False

            # بررسی تغییر نام کاربری
            if new_username and new_username != user.username:
                # بررسی تکراری نبودن نام کاربری
                if User.query.filter(User.id != user.id, User.username == new_username).first():
                    flash('این نام کاربری قبلاً توسط کاربر دیگری استفاده شده است')
                    return redirect(url_for('edit_profile'))
                changes['username'] = new_username
                verification_needed = True

            # بررسی تغییر ایمیل
            if new_email and new_email != user.email:
                # بررسی تکراری نبودن ایمیل
                if User.query.filter(User.id != user.id, User.email == new_email).first():
                    flash('این ایمیل قبلاً توسط کاربر دیگری استفاده شده است')
                    return redirect(url_for('edit_profile'))
                changes['email'] = new_email
                verification_needed = True

            # بررسی تغییر رمز عبور
            if new_password:
                # بررسی صحت رمز عبور فعلی
                if not check_password_hash(user.password_hash, current_password):
                    flash('رمز عبور فعلی اشتباه است')
                    return redirect(url_for('edit_profile'))
                changes['password'] = new_password
                verification_needed = True

            if not changes:
                flash('هیچ تغییری اعمال نشد')
                return redirect(url_for('edit_profile'))

            if verification_needed:
                try:
                    # ایجاد و ارسال کد تأیید
                    verification_email = user.email  # همیشه به ایمیل فعلی کاربر ارسال می‌شود
                    code = generate_verification_code(verification_email, purpose="update")
                    if send_verification_email(verification_email, code, purpose="update"):
                        # ذخیره موقت اطلاعات در session
                        session['temp_changes'] = changes
                        session['verification_purpose'] = "update"

                        return render_template('verify_email.html', email=verification_email, purpose="update")
                    else:
                        flash('خطا در ارسال ایمیل تأیید. لطفاً دوباره تلاش کنید.')
                        return redirect(url_for('edit_profile'))
                except Exception as e:
                    print(f"خطا در ارسال ایمیل تأیید: {str(e)}")
                    flash('خطا در ارسال ایمیل تأیید. لطفاً دوباره تلاش کنید.')
                    return redirect(url_for('edit_profile'))

        # حالت 2: تأیید کد ارسال شده برای ویرایش
        elif 'verify_code' in request.form and 'verification_purpose' in session and session[
            'verification_purpose'] == "update":
            try:
                code = request.form['verify_code']
                verification_email = user.email  # همیشه از ایمیل فعلی کاربر استفاده می‌شود
                changes = session.get('temp_changes', {})

                if not changes:
                    flash('اطلاعات نامعتبر. لطفاً دوباره تلاش کنید.')
                    return redirect(url_for('edit_profile'))

                # بررسی صحت کد
                if verify_code(verification_email, code, purpose="update"):
                    # اعمال تغییرات
                    if 'username' in changes:
                        user.username = changes['username']

                    if 'email' in changes:
                        user.email = changes['email']

                    if 'password' in changes:
                        user.password_hash = generate_password_hash(changes['password'])

                    db.session.commit()

                    # پاکسازی اطلاعات موقت
                    for key in ['temp_changes', 'verification_purpose']:
                        if key in session:
                            session.pop(key)

                    flash('اطلاعات کاربری با موفقیت به‌روزرسانی شد')
                    return redirect(url_for('profile'))
                else:
                    flash('کد تأیید نامعتبر یا منقضی شده است. لطفاً دوباره تلاش کنید.')
                    return render_template('verify_email.html', email=verification_email, purpose="update")
            except Exception as e:
                print(f"خطا در تأیید کد: {str(e)}")
                flash('خطا در تأیید کد. لطفاً دوباره تلاش کنید.')
                return redirect(url_for('edit_profile'))

        # حالت 3: درخواست ارسال مجدد کد
        elif 'resend_code' in request.form:
            try:
                verification_email = user.email
                purpose = session.get('verification_purpose')

                if not purpose:
                    flash('اطلاعات نامعتبر. لطفاً دوباره تلاش کنید.')
                    return redirect(url_for('edit_profile'))

                # ایجاد و ارسال کد جدید
                code = generate_verification_code(verification_email, purpose=purpose)
                if send_verification_email(verification_email, code, purpose=purpose):
                    flash('کد تأیید جدید ارسال شد.')
                else:
                    flash('خطا در ارسال ایمیل تأیید. لطفاً دوباره تلاش کنید.')

                return render_template('verify_email.html', email=verification_email, purpose=purpose)
            except Exception as e:
                print(f"خطا در ارسال مجدد کد: {str(e)}")
                flash('خطا در ارسال مجدد کد. لطفاً دوباره تلاش کنید.')
                return redirect(url_for('edit_profile'))

    return render_template('edit_profile.html', user=user)


@app.route('/admin/questions', methods=['GET', 'POST'])
@login_required
def manage_questions():
    """مدیریت سوالات - فقط برای ادمین"""
    user = User.query.get(session['user_id'])
    if not user or user.username != 'admin':
        flash('شما دسترسی به این بخش ندارید')
        return redirect(url_for('index'))

    if request.method == 'POST':
        # دریافت اطلاعات از فرم
        category = request.form['category']
        question_text = request.form['question_text']
        correct_answer = request.form['correct_answer']
        wrong_answers = request.form.getlist('wrong_answers[]')

        # ایجاد سوال جدید
        question = Question(
            category=category,
            question_text=question_text,
            correct_answer=correct_answer,
            wrong_answers=json.dumps(wrong_answers)
        )

        db.session.add(question)
        db.session.commit()

        flash('سوال با موفقیت اضافه شد')
        return redirect(url_for('manage_questions'))

    # دریافت تمام دسته‌بندی‌های موجود در دیتابیس
    categories = db.session.query(Question.category).distinct().all()
    categories = [category[0] for category in categories]

    # اضافه کردن دسته‌بندی‌های پیش‌فرض اگر در لیست نیستند
    default_categories = ['عمومی', 'علوم', 'تاریخ', 'ورزشی']
    for category in default_categories:
        if category not in categories:
            categories.append(category)

    # مرتب‌سازی دسته‌بندی‌ها
    categories.sort()

    questions = Question.query.all()
    return render_template('admin/questions.html', questions=questions, categories=categories)


@app.route('/admin/delete_question/<int:question_id>', methods=['POST'])
@login_required
def delete_question(question_id):
    """حذف یک سوال - فقط برای ادمین"""
    user = User.query.get(session['user_id'])
    if not user or user.username != 'admin':
        return jsonify({'error': 'دسترسی غیرمجاز'}), 403

    question = Question.query.get_or_404(question_id)
    try:
        db.session.delete(question)
        db.session.commit()
        return jsonify({'success': True, 'message': 'سوال با موفقیت حذف شد'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/admin/update_question/<int:question_id>', methods=['POST'])
@login_required
def update_question(question_id):
    """ویرایش یک سوال - فقط برای ادمین"""
    user = User.query.get(session['user_id'])
    if not user or user.username != 'admin':
        return jsonify({'error': 'دسترسی غیرمجاز'}), 403

    question = Question.query.get_or_404(question_id)
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'داده‌ای دریافت نشد'}), 400

        # بررسی اعتبار داده‌ها
        if not all(key in data for key in ['category', 'question_text', 'correct_answer', 'wrong_answers']):
            return jsonify({'error': 'اطلاعات ناقص است'}), 400

        if len(data['wrong_answers']) < 3:
            return jsonify({'error': 'حداقل سه گزینه نادرست باید وارد شود'}), 400

        # به‌روزرسانی سوال
        question.category = data['category']
        question.question_text = data['question_text']
        question.correct_answer = data['correct_answer']
        question.wrong_answers = json.dumps(data['wrong_answers'])

        db.session.commit()
        return jsonify({'success': True, 'message': 'سوال با موفقیت به‌روزرسانی شد'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/admin/analytics')
@login_required
def admin_analytics():
    """صفحه آمار و تحلیل‌های کلی - فقط برای ادمین"""
    user = User.query.get(session['user_id'])
    if not user or user.username != 'admin':
        flash('شما دسترسی به این بخش ندارید')
        return redirect(url_for('index'))

    # لیست همه کاربران برای جستجو
    #all_usernames = User.query.filter(User.username != 'admin').all()

    # دریافت همه دسته‌بندی‌های موجود برای فیلتر
    categories = db.session.query(Question.category).distinct().all()
    categories = [cat[0] for cat in categories]

    # === آمارهای کلی (KPIs) ===
    total_users = User.query.count()
    total_quizzes = QuizResult.query.count()
    total_questions = Question.query.count()
    avg_total_score = db.session.query(db.func.avg(QuizResult.score)).scalar() or 0

    # === تحلیل عملکرد کاربران ===
    user_performance = db.session.query(
        User.id,
        User.username,
        db.func.count(QuizResult.id).label('quiz_count'),
        db.func.avg(QuizResult.score).label('avg_score'),
        db.func.min(QuizResult.score).label('min_score'),
        db.func.max(QuizResult.score).label('max_score')
    ).join(QuizResult).group_by(User.id, User.username).all()

    # تبدیل user_performance به لیست دیکشنری‌ها برای دسترسی آسان‌تر
    user_performance_list = []
    for u in user_performance:
        # پیدا کردن بهترین دسته‌بندی برای کاربر
        user_id = u.id
        best_category_query = db.session.query(
            QuizResult.category,
            db.func.avg(QuizResult.score).label('avg_score')
        ).filter(
            QuizResult.user_id == user_id
        ).group_by(
            QuizResult.category
        ).order_by(
            db.func.avg(QuizResult.score).desc()
        ).first()

        best_category = best_category_query.category if best_category_query else "عمومی"

        user_performance_list.append({
            'id': user_id,
            'username': u.username,
            'quiz_count': u.quiz_count,
            'avg_score': u.avg_score,
            'min_score': u.min_score,
            'max_score': u.max_score,
            'category_best': best_category
        })

    # === تحلیل سوالات ===
    question_stats = {}
    all_results = QuizResult.query.all()
    for result in all_results:
        if result.answers:  # اگر پاسخ‌ها ذخیره شده باشند
            answers = json.loads(result.answers)
            for question_id, answer in answers.items():
                if question_id not in question_stats:
                    question_stats[question_id] = {'total': 0, 'correct': 0}
                question_stats[question_id]['total'] += 1
                question = Question.query.get(int(question_id))
                if question and answer == question.correct_answer:
                    question_stats[question_id]['correct'] += 1

    # دیکشنری برای دسترسی آسان به سوالات
    questions_dict = {q.id: q for q in Question.query.all()}

    # === تحلیل دسته‌بندی‌ها ===
    category_stats = db.session.query(
        QuizResult.category,
        db.func.count(QuizResult.id).label('total_attempts'),
        db.func.avg(QuizResult.score).label('avg_score'),
        db.func.min(QuizResult.score).label('min_score'),
        db.func.max(QuizResult.score).label('max_score')
    ).group_by(QuizResult.category).all()

    # === تحلیل زمانی ===
    time_stats = db.session.query(
        db.func.date(QuizResult.date).label('date'),
        db.func.count(QuizResult.id).label('quiz_count'),
        db.func.avg(QuizResult.score).label('avg_score')
    ).group_by(
        db.func.date(QuizResult.date)
    ).order_by(
        db.func.date(QuizResult.date)
    ).all()

    # === تحلیل سطح دشواری ===
    difficulty_stats = {
        'آسان': {'count': 0, 'avg_score': 0},
        'متوسط': {'count': 0, 'avg_score': 0},
        'سخت': {'count': 0, 'avg_score': 0}
    }

    for result in all_results:
        if result.score >= 80:
            level = 'آسان'
        elif result.score >= 60:
            level = 'متوسط'
        else:
            level = 'سخت'
        difficulty_stats[level]['count'] += 1
        current_avg = difficulty_stats[level]['avg_score']
        count = difficulty_stats[level]['count']

        # محاسبه میانگین جدید به روش درست‌تر
        if count > 1:
            difficulty_stats[level]['avg_score'] = (current_avg * (count - 1) + result.score) / count
        else:
            difficulty_stats[level]['avg_score'] = result.score

    # === آماده‌سازی داده‌ها برای نمودارها ===
    chart_data = {
        # داده‌های روند زمانی
        'time_labels': [str(stat.date) for stat in time_stats],
        'time_counts': [stat.quiz_count for stat in time_stats],
        'time_scores': [float(stat.avg_score) for stat in time_stats],
        'time_times': [60 + random.randint(-10, 10) for _ in time_stats],  # داده نمونه برای زمان

        # داده‌های دسته‌بندی
        'categories': [stat.category for stat in category_stats],
        'category_counts': [stat.total_attempts for stat in category_stats],
        'category_scores': [float(stat.avg_score) for stat in category_stats],

        # داده‌های کاربران
        'users': [user['username'] for user in user_performance_list],
        'user_counts': [user['quiz_count'] for user in user_performance_list],
        'user_scores': [float(user['avg_score']) for user in user_performance_list],

        # داده‌های سطح دشواری
        'difficulty_labels': list(difficulty_stats.keys()),
        'difficulty_counts': [stats['count'] for stats in difficulty_stats.values()],
        'difficulty_scores': [stats['avg_score'] for stats in difficulty_stats.values()]
    }

    # محاسبه متوسط نمره برای هر کاربر در هر دسته‌بندی
    category_strength_data = {}
    for user in User.query.filter(User.username != 'admin').all():
        user_id = user.id
        username = user.username

        user_category_results = db.session.query(
            QuizResult.category,
            db.func.avg(QuizResult.score).label('avg_score')
        ).filter(
            QuizResult.user_id == user_id
        ).group_by(
            QuizResult.category
        ).all()

        if user_category_results:
            category_strength_data[username] = {
                'categories': [res.category for res in user_category_results],
                'scores': [float(res.avg_score) for res in user_category_results]
            }

    # اضافه کردن تحلیل زمان پاسخگویی
    response_time_data = {}
    all_usernames = [u.username for u in User.query.filter(User.username != 'admin').all()]

    for username in all_usernames:
        user = User.query.filter_by(username=username).first()
        if user:
            user_results = QuizResult.query.filter_by(user_id=user.id).order_by(QuizResult.date).all()
            if user_results:
                response_time_data[username] = {
                    'dates': [result.date.strftime('%Y-%m-%d') for result in user_results],
                    'times': [result.time_taken for result in user_results]
                }

    # اضافه کردن این داده‌ها به chart_data
    chart_data['category_strength'] = category_strength_data
    chart_data['response_time'] = response_time_data

    # افزودن تحلیل دقیق‌تر سطح دشواری
    difficulty_detailed = {
        'آسان': {'count': 0, 'avg_score': 0, 'avg_time': 0, 'categories': {}},
        'متوسط': {'count': 0, 'avg_score': 0, 'avg_time': 0, 'categories': {}},
        'سخت': {'count': 0, 'avg_score': 0, 'avg_time': 0, 'categories': {}}
    }

    for result in all_results:
        if result.score >= 80:
            level = 'آسان'
        elif result.score >= 60:
            level = 'متوسط'
        else:
            level = 'سخت'

        difficulty_detailed[level]['count'] += 1
        difficulty_detailed[level]['avg_score'] = ((difficulty_detailed[level]['avg_score'] *
                                                    (difficulty_detailed[level]['count'] - 1) +
                                                    result.score) / difficulty_detailed[level]['count'])

        difficulty_detailed[level]['avg_time'] = ((difficulty_detailed[level]['avg_time'] *
                                                   (difficulty_detailed[level]['count'] - 1) +
                                                   result.time_taken) / difficulty_detailed[level]['count'])

        # دسته‌بندی در سطح دشواری
        if result.category not in difficulty_detailed[level]['categories']:
            difficulty_detailed[level]['categories'][result.category] = 1
        else:
            difficulty_detailed[level]['categories'][result.category] += 1

    chart_data['difficulty_detailed'] = difficulty_detailed

    return render_template('admin/analytics.html',
                           total_users=total_users,
                           total_quizzes=total_quizzes,
                           total_questions=total_questions,
                           avg_total_score=round(avg_total_score, 2),
                           user_performance=user_performance_list,
                           category_stats=category_stats,
                           question_stats=question_stats,
                           questions_dict=questions_dict,
                           chart_data=chart_data,
                           all_usernames=all_usernames,
                           categories=categories)


@app.route('/admin/analytics/category_questions/<category>', methods=['GET'])
@login_required
def category_questions_analysis(category):
    """تحلیل سوالات یک دسته‌بندی خاص - فقط برای ادمین"""
    try:
        user = User.query.get(session['user_id'])
        if not user or user.username != 'admin':
            return jsonify({'error': 'شما دسترسی به این بخش ندارید'}), 403

        # دریافت همه سوالات دسته‌بندی
        questions = Question.query.filter_by(category=category).all()
        if not questions:
            return jsonify({'error': 'هیچ سوالی در این دسته‌بندی وجود ندارد'}), 404

        # تحلیل هر سوال
        questions_analysis = []
        for question in questions:
            # یافتن همه پاسخ‌های داده شده به این سوال
            answers_count = 0
            correct_count = 0
            wrong_options_count = {}  # شمارش گزینه‌های نادرست پرتکرار

            # تبدیل گزینه‌های نادرست به فرمت قابل استفاده
            try:
                wrong_answers = json.loads(question.wrong_answers)
                # ایجاد دیکشنری برای شمارش گزینه‌های نادرست
                for wrong_answer in wrong_answers:
                    wrong_options_count[wrong_answer] = 0
            except:
                wrong_answers = []

            # بررسی همه کوییزهایی که شامل این سوال بوده‌اند
            for result in QuizResult.query.all():
                if result.answers:  # اگر پاسخ‌ها ذخیره شده باشند
                    answers = json.loads(result.answers)
                    if str(question.id) in answers:
                        answers_count += 1
                        answer = answers[str(question.id)]

                        if answer == question.correct_answer:
                            correct_count += 1
                        elif answer in wrong_options_count:
                            wrong_options_count[answer] += 1

            # محاسبه نرخ پاسخ صحیح و پاسخ‌های نادرست پرتکرار
            success_rate = (correct_count / answers_count * 100) if answers_count > 0 else 0
            top_wrong_options = sorted(wrong_options_count.items(), key=lambda x: x[1], reverse=True)

            questions_analysis.append({
                'id': question.id,
                'question_text': question.question_text,
                'correct_answer': question.correct_answer,
                'answers_count': answers_count,
                'correct_count': correct_count,
                'success_rate': success_rate,
                'top_wrong_options': top_wrong_options[:3]  # سه گزینه نادرست پرتکرار
            })

        # مرتب‌سازی سوالات بر اساس نرخ موفقیت (صعودی)
        questions_analysis = sorted(questions_analysis, key=lambda x: x['success_rate'])

        # شناسایی سوالات مشکل‌دار (نرخ موفقیت زیر 40%)
        problematic_questions = [q for q in questions_analysis if q['success_rate'] < 40]

        # شناسایی سوالات با بیشترین اشتباه
        most_wrong_questions = sorted(questions_analysis, key=lambda x: x['answers_count'] - x['correct_count'],
                                      reverse=True)[:5]

        return jsonify({
            'success': True,
            'category': category,
            'questions_count': len(questions),
            'questions_analysis': questions_analysis,
            'problematic_questions': [q['id'] for q in problematic_questions],
            'most_wrong_questions': most_wrong_questions[:5]
        })

    except Exception as e:
        print(f"خطا در تحلیل سوالات دسته‌بندی: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/admin/analytics/filter', methods=['POST'])
@login_required
def analytics_filter():
    """دریافت اطلاعات فیلتر شده برای آنالیتیکس"""
    try:
        user = User.query.get(session['user_id'])
        if not user or user.username != 'admin':
            return jsonify({'error': 'شما دسترسی به این بخش ندارید'}), 403

        data = request.get_json()
        if not data:
            return jsonify({'error': 'داده‌ای دریافت نشد'}), 400

        # دریافت پارامترهای فیلتر
        time_range = data.get('timeRange', 'all')
        difficulty = data.get('difficulty', 'all')
        category = data.get('category', 'all')
        user_id = data.get('userId')

        # محاسبه محدوده زمانی
        now = datetime.utcnow()
        if time_range == '1m':
            start_date = now - timedelta(days=30)
        elif time_range == '3m':
            start_date = now - timedelta(days=90)
        elif time_range == '1y':
            start_date = now - timedelta(days=365)
        else:
            # در حالت 'all' از تاریخ خیلی قدیمی استفاده می‌کنیم
            start_date = datetime(2000, 1, 1)

        # ساخت پرس‌وجوی پایه
        query = QuizResult.query.filter(QuizResult.date >= start_date)

        # اعمال فیلتر کاربر
        if user_id:
            query = query.filter(QuizResult.user_id == user_id)

        # اعمال فیلتر دسته‌بندی
        if category != 'all':
            query = query.filter(QuizResult.category == category)

        # دریافت نتایج
        results = query.all()

        # اعمال فیلتر سطح دشواری (باید پس از پرس‌وجو انجام شود)
        if difficulty != 'all':
            if difficulty == 'easy':
                results = [r for r in results if r.score >= 80]
            elif difficulty == 'medium':
                results = [r for r in results if 60 <= r.score < 80]
            elif difficulty == 'hard':
                results = [r for r in results if r.score < 60]

        # تحلیل زمانی
        time_data = {}
        for result in results:
            date_str = result.date.strftime('%Y-%m-%d')
            if date_str not in time_data:
                time_data[date_str] = {
                    'count': 0,
                    'total_score': 0,
                    'total_time': 0
                }
            time_data[date_str]['count'] += 1
            time_data[date_str]['total_score'] += result.score
            time_data[date_str]['total_time'] += result.time_taken

        # مرتب‌سازی داده‌های زمانی
        time_labels = sorted(time_data.keys())
        time_counts = [time_data[date]['count'] for date in time_labels]
        time_scores = [time_data[date]['total_score'] / time_data[date]['count']
                       if time_data[date]['count'] > 0 else 0
                       for date in time_labels]
        time_times = [time_data[date]['total_time'] / time_data[date]['count']
                      if time_data[date]['count'] > 0 else 0
                      for date in time_labels]

        # تحلیل دسته‌بندی‌ها
        category_data = {}
        for result in results:
            cat = result.category
            if cat not in category_data:
                category_data[cat] = {
                    'count': 0,
                    'total_score': 0,
                    'min_score': 100,
                    'max_score': 0
                }
            category_data[cat]['count'] += 1
            category_data[cat]['total_score'] += result.score
            category_data[cat]['min_score'] = min(category_data[cat]['min_score'], result.score)
            category_data[cat]['max_score'] = max(category_data[cat]['max_score'], result.score)

        # مرتب‌سازی داده‌های دسته‌بندی
        categories = sorted(category_data.keys())
        category_counts = [category_data[cat]['count'] for cat in categories]
        category_scores = [category_data[cat]['total_score'] / category_data[cat]['count']
                           if category_data[cat]['count'] > 0 else 0
                           for cat in categories]

        # تحلیل کاربران (اگر فیلتر کاربر اعمال نشده باشد)
        user_data = {}
        if not user_id:
            for result in results:
                user_obj = User.query.get(result.user_id)
                if not user_obj:
                    continue

                username = user_obj.username
                if username not in user_data:
                    user_data[username] = {
                        'count': 0,
                        'total_score': 0
                    }
                user_data[username]['count'] += 1
                user_data[username]['total_score'] += result.score

            users = sorted(user_data.keys())
            user_counts = [user_data[username]['count'] for username in users]
            user_scores = [user_data[username]['total_score'] / user_data[username]['count']
                           if user_data[username]['count'] > 0 else 0
                           for username in users]
        else:
            # اگر فیلتر کاربر اعمال شده باشد، فقط اطلاعات همان کاربر را می‌دهیم
            selected_user = User.query.get(user_id)
            users = [selected_user.username] if selected_user else []
            user_counts = [len(results)] if users else []
            user_scores = [sum(r.score for r in results) / len(results) if results else 0]

        # تحلیل سطح دشواری
        difficulty_data = {
            'آسان': {'count': 0, 'total_score': 0},
            'متوسط': {'count': 0, 'total_score': 0},
            'سخت': {'count': 0, 'total_score': 0}
        }

        for result in results:
            if result.score >= 80:
                level = 'آسان'
            elif result.score >= 60:
                level = 'متوسط'
            else:
                level = 'سخت'
            difficulty_data[level]['count'] += 1
            difficulty_data[level]['total_score'] += result.score

        difficulty_labels = list(difficulty_data.keys())
        difficulty_counts = [difficulty_data[level]['count'] for level in difficulty_labels]
        difficulty_scores = [difficulty_data[level]['total_score'] / difficulty_data[level]['count']
                             if difficulty_data[level]['count'] > 0 else 0
                             for level in difficulty_labels]

        # پاسخ API
        return jsonify({
            'time_labels': time_labels,
            'time_counts': time_counts,
            'time_scores': time_scores,
            'time_times': time_times,
            'categories': categories,
            'category_counts': category_counts,
            'category_scores': category_scores,
            'users': users,
            'user_counts': user_counts,
            'user_scores': user_scores,
            'difficulty_labels': difficulty_labels,
            'difficulty_counts': difficulty_counts,
            'difficulty_scores': difficulty_scores
        })

    except Exception as e:
        print(f"خطا در فیلتر آنالیتیکس: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/admin/analytics/download', methods=['POST'])
@login_required
def download_analytics():
    """دانلود گزارش آنالیتیکس در قالب Excel"""
    try:
        user = User.query.get(session['user_id'])
        if not user or user.username != 'admin':
            return jsonify({'error': 'شما دسترسی به این بخش ندارید'}), 403

        data = request.get_json()
        if not data:
            return jsonify({'error': 'داده‌ای دریافت نشد'}), 400

        # دریافت پارامترهای فیلتر
        time_range = data.get('timeRange', 'all')
        difficulty = data.get('difficulty', 'all')
        category = data.get('category', 'all')
        user_id = data.get('userId')

        # تبدیل پارامترها به متن فارسی برای نمایش در گزارش
        time_range_text = 'همه زمان‌ها'
        if time_range == '1m':
            time_range_text = 'یک ماه اخیر'
        elif time_range == '3m':
            time_range_text = 'سه ماه اخیر'
        elif time_range == '1y':
            time_range_text = 'یک سال اخیر'

        difficulty_text = 'همه سطوح دشواری'
        if difficulty == 'easy':
            difficulty_text = 'آسان'
        elif difficulty == 'medium':
            difficulty_text = 'متوسط'
        elif difficulty == 'hard':
            difficulty_text = 'سخت'

        category_text = 'همه دسته‌بندی‌ها'
        if category != 'all':
            category_text = category

        user_text = 'همه کاربران'
        if user_id:
            selected_user = User.query.get(user_id)
            if selected_user:
                user_text = selected_user.username

        # محاسبه محدوده زمانی
        now = datetime.utcnow()
        if time_range == '1m':
            start_date = now - timedelta(days=30)
        elif time_range == '3m':
            start_date = now - timedelta(days=90)
        elif time_range == '1y':
            start_date = now - timedelta(days=365)
        else:
            # در حالت 'all' از تاریخ خیلی قدیمی استفاده می‌کنیم
            start_date = datetime(2000, 1, 1)

        # ساخت پرس‌وجوی پایه
        query = QuizResult.query.filter(QuizResult.date >= start_date)

        # اعمال فیلتر کاربر
        if user_id:
            query = query.filter(QuizResult.user_id == user_id)

        # اعمال فیلتر دسته‌بندی
        if category != 'all':
            query = query.filter(QuizResult.category == category)

        # دریافت نتایج
        results = query.all()

        # اعمال فیلتر سطح دشواری (باید پس از پرس‌وجو انجام شود)
        if difficulty != 'all':
            if difficulty == 'easy':
                results = [r for r in results if r.score >= 80]
            elif difficulty == 'medium':
                results = [r for r in results if 60 <= r.score < 80]
            elif difficulty == 'hard':
                results = [r for r in results if r.score < 60]

        # ساخت داده‌های گزارش
        # 1. آمار کلی
        total_quizzes = len(results)
        avg_score = sum(r.score for r in results) / total_quizzes if total_quizzes > 0 else 0

        # 2. آمار به تفکیک کاربر
        user_data = {}
        for result in results:
            user_obj = User.query.get(result.user_id)
            if not user_obj:
                continue

            username = user_obj.username
            if username not in user_data:
                user_data[username] = {
                    'count': 0,
                    'total_score': 0,
                    'scores': []
                }
            user_data[username]['count'] += 1
            user_data[username]['total_score'] += result.score
            user_data[username]['scores'].append(result.score)

        user_stats = []
        for username, stats in user_data.items():
            if stats['count'] > 0:
                avg = stats['total_score'] / stats['count']
                min_score = min(stats['scores']) if stats['scores'] else 0
                max_score = max(stats['scores']) if stats['scores'] else 0
                user_stats.append({
                    'username': username,
                    'count': stats['count'],
                    'avg_score': avg,
                    'min_score': min_score,
                    'max_score': max_score
                })

        # 3. آمار به تفکیک دسته‌بندی
        category_data = {}
        for result in results:
            cat = result.category
            if cat not in category_data:
                category_data[cat] = {
                    'count': 0,
                    'total_score': 0,
                    'min_score': 100,
                    'max_score': 0
                }
            category_data[cat]['count'] += 1
            category_data[cat]['total_score'] += result.score
            category_data[cat]['min_score'] = min(category_data[cat]['min_score'], result.score)
            category_data[cat]['max_score'] = max(category_data[cat]['max_score'], result.score)

        category_stats = []
        for cat, stats in category_data.items():
            if stats['count'] > 0:
                avg = stats['total_score'] / stats['count']
                category_stats.append({
                    'category': cat,
                    'count': stats['count'],
                    'avg_score': avg,
                    'min_score': stats['min_score'],
                    'max_score': stats['max_score']
                })

        # 4. آمار به تفکیک سطح دشواری
        difficulty_data = {
            'آسان': {'count': 0, 'total_score': 0},
            'متوسط': {'count': 0, 'total_score': 0},
            'سخت': {'count': 0, 'total_score': 0}
        }

        for result in results:
            if result.score >= 80:
                level = 'آسان'
            elif result.score >= 60:
                level = 'متوسط'
            else:
                level = 'سخت'
            difficulty_data[level]['count'] += 1
            difficulty_data[level]['total_score'] += result.score

        difficulty_stats = []
        for level, stats in difficulty_data.items():
            if stats['count'] > 0:
                avg = stats['total_score'] / stats['count']
                difficulty_stats.append({
                    'level': level,
                    'count': stats['count'],
                    'avg_score': avg
                })

        # 5. نتایج کوییزها
        quiz_data = []
        for result in results:
            user_obj = User.query.get(result.user_id)
            if not user_obj:
                continue

            quiz_data.append({
                'username': user_obj.username,
                'category': result.category,
                'score': result.score,
                'date': result.date,
                'time_taken': result.time_taken,
                'difficulty': 'آسان' if result.score >= 80 else ('متوسط' if result.score >= 60 else 'سخت')
            })

        # ایجاد فایل Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book

            # فرمت‌های مورد نیاز
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#0D6EFD',
                'font_color': 'white',
                'border': 1,
                'align': 'center'
            })

            dfs = {}

            # صفحه 1: اطلاعات فیلتر
            filter_df = pd.DataFrame([
                ['تاریخ گزارش', now.strftime('%Y-%m-%d %H:%M:%S')],
                ['بازه زمانی', time_range_text],
                ['سطح دشواری', difficulty_text],
                ['دسته‌بندی', category_text],
                ['کاربر', user_text],
                ['تعداد کل کوییزها', total_quizzes],
                ['میانگین نمرات', f"{avg_score:.2f}%"]
            ])
            filter_df.columns = ['پارامتر', 'مقدار']
            sheet_name = 'اطلاعات گزارش'
            filter_df.to_excel(writer, sheet_name=sheet_name, index=False)
            dfs[sheet_name] = filter_df

            # صفحه 2: آمار کاربران
            if user_stats:
                user_df = pd.DataFrame(user_stats)
                user_df.columns = ['نام کاربری', 'تعداد کوییز', 'میانگین نمره', 'کمترین نمره', 'بیشترین نمره']
                sheet_name = 'آمار کاربران'
                user_df.to_excel(writer, sheet_name=sheet_name, index=False)
                dfs[sheet_name] = user_df

            # صفحه 3: آمار دسته‌بندی‌ها
            if category_stats:
                category_df = pd.DataFrame(category_stats)
                category_df.columns = ['دسته‌بندی', 'تعداد', 'میانگین نمره', 'کمترین نمره', 'بیشترین نمره']
                sheet_name = 'آمار دسته‌بندی‌ها'
                category_df.to_excel(writer, sheet_name=sheet_name, index=False)
                dfs[sheet_name] = category_df

            # صفحه 4: آمار سطح دشواری
            if difficulty_stats:
                difficulty_df = pd.DataFrame(difficulty_stats)
                difficulty_df.columns = ['سطح دشواری', 'تعداد', 'میانگین نمره']
                sheet_name = 'آمار سطح دشواری'
                difficulty_df.to_excel(writer, sheet_name=sheet_name, index=False)
                dfs[sheet_name] = difficulty_df

            # صفحه 5: نتایج کوییزها
            if quiz_data:
                quiz_df = pd.DataFrame(quiz_data)
                quiz_df['date'] = quiz_df['date'].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S'))
                quiz_df.columns = ['نام کاربری', 'دسته‌بندی', 'نمره', 'تاریخ', 'زمان (ثانیه)', 'سطح دشواری']
                sheet_name = 'نتایج کوییزها'
                quiz_df.to_excel(writer, sheet_name=sheet_name, index=False)
                dfs[sheet_name] = quiz_df

            output.seek(0)

            # تنظیم عرض ستون‌ها
            for sheet_name, df_temp in dfs.items():
                worksheet = writer.sheets[sheet_name]
                for i, col in enumerate(df_temp.columns):
                    worksheet.set_column(i, i, max(len(str(col)) * 1.5, 15))

                # اعمال فرمت هدر به ردیف اول
                for col_num, _ in enumerate(df_temp.columns):
                    worksheet.write(0, col_num, df_temp.columns[col_num],
                                    header_format)

        # تنظیم مجدد موقعیت فایل برای خواندن
        output.seek(0)

        # ایجاد نام فایل مناسب
        date_str = now.strftime('%Y%m%d_%H%M%S')
        filename = f"quiz_report_{time_range}_{difficulty}_{category}_{date_str}.xlsx"

        # ارسال فایل
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        import traceback
        print(f"خطا در دانلود گزارش: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/admin/analytics/question_difficulty_distribution/<category>', methods=['GET'])
@login_required
def question_difficulty_distribution(category):
    """توزیع سختی سوالات در دسته‌بندی‌های مختلف"""
    try:
        user = User.query.get(session['user_id'])
        if not user or user.username != 'admin':
            return jsonify({'error': 'شما دسترسی به این بخش ندارید'}), 403

        # پرس‌وجوی اولیه
        query = Question.query

        # اعمال فیلتر دسته‌بندی اگر 'همه' نباشد
        if category != 'all':
            query = query.filter_by(category=category)

        # اجرای پرس‌وجو و دریافت همه سوالات
        questions = query.all()

        if not questions:
            return jsonify({
                'success': True,
                'category': category,
                'easy_count': 0,
                'medium_count': 0,
                'hard_count': 0,
                'total_count': 0
            })

        # محاسبه توزیع سختی سوالات
        easy_count = 0
        medium_count = 0
        hard_count = 0

        # محاسبه سختی هر سوال بر اساس نرخ پاسخ صحیح
        for question in questions:
            # یافتن همه پاسخ‌های داده شده به این سوال
            answers_count = 0
            correct_count = 0

            # بررسی همه کوییزهایی که شامل این سوال بوده‌اند
            for result in QuizResult.query.all():
                if result.answers:
                    answers = json.loads(result.answers)
                    if str(question.id) in answers:
                        answers_count += 1
                        answer = answers[str(question.id)]

                        if answer == question.correct_answer:
                            correct_count += 1

            # محاسبه نرخ پاسخ صحیح و تعیین سطح سختی
            success_rate = (correct_count / answers_count * 100) if answers_count > 0 else 50  # مقدار پیش‌فرض 50%

            if success_rate >= 80:
                easy_count += 1
            elif success_rate >= 60:
                medium_count += 1
            else:
                hard_count += 1

        # برگرداندن توزیع سختی سوالات
        return jsonify({
            'success': True,
            'category': category,
            'easy_count': easy_count,
            'medium_count': medium_count,
            'hard_count': hard_count,
            'total_count': len(questions)
        })

    except Exception as e:
        print(f"خطا در تحلیل توزیع سختی سوالات: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/import_questions', methods=['POST'])
@login_required
def import_questions():
    """دریافت سوالات از API خارجی - فقط برای ادمین"""
    try:
        # بررسی دسترسی ادمین
        user = User.query.get(session['user_id'])
        if not user or user.username != 'admin':
            return jsonify({'error': 'دسترسی غیرمجاز'}), 403

        print("Starting to import questions...")

        # دریافت سوالات از API خارجی با تایم‌اوت مناسب
        try:
            response = requests.get(
                'https://opentdb.com/api.php',
                params={
                    'amount': 10,
                    'type': 'multiple'
                },
                timeout=10  # تنظیم تایم‌اوت برای جلوگیری از انتظار طولانی
            )
            print(f"API Response status: {response.status_code}")

            if response.status_code != 200:
                return jsonify({'error': f'خطا در دریافت از API: کد {response.status_code}'}), 400

        except requests.exceptions.RequestException as e:
            print(f"Request error: {str(e)}")
            return jsonify({'error': f'خطا در ارتباط با API خارجی: {str(e)}'}), 500

        # پردازش پاسخ API
        try:
            data = response.json()
            print(f"API Response data: {data}")

            if 'response_code' not in data or data['response_code'] != 0:
                return jsonify({
                    'error': f'خطا در پاسخ API (کد {data.get("response_code", "نامشخص")})'
                }), 400

            if 'results' not in data or not data['results']:
                return jsonify({'error': 'هیچ سوالی از API دریافت نشد'}), 400

        except ValueError as e:
            print(f"JSON parsing error: {str(e)}")
            return jsonify({'error': 'خطا در پردازش پاسخ API'}), 500

        # اضافه کردن سوالات به دیتابیس
        questions_added = 0
        try:
            for q in data['results']:
                # اطمینان از وجود تمام فیلدهای مورد نیاز
                if all(key in q for key in ['category', 'question', 'correct_answer', 'incorrect_answers']):
                    # پاکسازی و آماده‌سازی داده‌ها
                    category = q['category']
                    question_text = q['question']
                    correct_answer = q['correct_answer']
                    wrong_answers = json.dumps(q['incorrect_answers'])

                    # ایجاد و ذخیره سوال
                    question = Question(
                        category=category,
                        question_text=question_text,
                        correct_answer=correct_answer,
                        wrong_answers=wrong_answers
                    )
                    db.session.add(question)
                    questions_added += 1
                else:
                    print(f"Skipping question due to missing fields: {q}")

            if questions_added > 0:
                db.session.commit()
                print(f"Successfully added {questions_added} questions")
                return jsonify({
                    'success': True,
                    'message': f'{questions_added} سوال با موفقیت اضافه شد'
                })
            else:
                return jsonify({'error': 'هیچ سوالی اضافه نشد'}), 400

        except Exception as e:
            db.session.rollback()
            print(f"Database error: {str(e)}")
            return jsonify({'error': f'خطا در ذخیره سوالات: {str(e)}'}), 500

    except Exception as e:
        print(f"Unexpected error in import_questions: {str(e)}")
        return jsonify({'error': f'خطای سیستمی: {str(e)}'}), 500


@app.route('/quiz/<category>', methods=['GET', 'POST'])
@login_required
def quiz(category):
    """نمایش کوییز برای یک دسته‌بندی خاص"""

    # در ابتدا تعداد سوالات را به 10 تنظیم می‌کنیم
    num_questions = 10

    # اگر فرم ارسال شود، تعداد سوالات را از فرم دریافت می‌کنیم
    if request.method == 'POST':
        num_questions = int(request.form.get('num_questions', 10))  # مقدار ورودی را از فرم دریافت می‌کنیم

    # دریافت سوالات از دسته‌بندی
    questions = Question.query.filter_by(category=category).limit(num_questions).all()
    if not questions:
        flash('سوالی در این دسته‌بندی وجود ندارد')
        return redirect(url_for('index'))

    # تبدیل سوالات به فرمت مناسب برای نمایش
    quiz_questions = []

    # تصادفی کردن سوالات
    random.shuffle(questions)  # مخلوط کردن سوالات به صورت تصادفی

    for q in questions:
        wrong_answers = json.loads(q.wrong_answers)
        options = wrong_answers + [q.correct_answer]

        # مخلوط کردن گزینه‌ها به صورت تصادفی
        random.shuffle(options)  # مخلوط کردن گزینه‌ها به صورت تصادفی

        quiz_questions.append({
            'id': q.id,
            'question': q.question_text,
            'options': options,
            'correct_answer': q.correct_answer
        })

    return render_template('quiz.html',
                           questions=quiz_questions,
                           category=category,
                           num_questions=num_questions)


@app.route('/submit_quiz', methods=['POST'])
@login_required
def submit_quiz():
    """ثبت نتیجه کوییز"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'داده‌ای دریافت نشد'}), 400

        print("Received data:", data)  # اضافه کردن لاگ برای دیباگ

        category = data.get('category')
        time_taken = data.get('time_taken')
        answers = data.get('answers', {})

        # اعتبارسنجی داده‌های ورودی
        if not category:
            return jsonify({'error': 'دسته‌بندی مشخص نشده است'}), 400
        if not time_taken:
            return jsonify({'error': 'زمان صرف شده مشخص نشده است'}), 400
        if not answers:
            return jsonify({'error': 'هیچ پاسخی ارسال نشده است'}), 400

        # محاسبه امتیاز
        correct_count = 0
        total_questions = len(answers)

        for question_id, answer in answers.items():
            try:
                question = Question.query.get(int(question_id))
                if question and question.correct_answer == answer:
                    correct_count += 1
            except Exception as e:
                print(f"Error checking answer for question {question_id}: {str(e)}")

        score = int((correct_count / total_questions) * 100) if total_questions > 0 else 0
        print(f"Calculated score: {score}% ({correct_count}/{total_questions})")

        # ذخیره نتیجه کوییز
        try:
            result = QuizResult(
                user_id=session['user_id'],
                category=category,
                score=score,
                time_taken=time_taken,
                answers=json.dumps(answers),
                date=datetime.utcnow()  # اضافه کردن تاریخ فعلی صریح
            )

            db.session.add(result)
            db.session.commit()
            print("Quiz result saved successfully")
        except Exception as e:
            db.session.rollback()
            print(f"Error saving quiz result: {str(e)}")
            return jsonify({'error': f'خطا در ذخیره نتیجه: {str(e)}'}), 500

        return jsonify({
            'success': True,
            'message': 'نتیجه با موفقیت ثبت شد',
            'score': score,
            'correct_count': correct_count,
            'total_questions': total_questions
        })

    except Exception as e:
        print(f"Unexpected error in submit_quiz: {str(e)}")
        return jsonify({'error': f'خطای سیستمی: {str(e)}'}), 500

@app.route('/profile')
@login_required
def profile():
    """نمایش پروفایل کاربر و نتایج کوییزها"""
    try:
        # دریافت اطلاعات کاربر
        user = User.query.get(session['user_id'])
        if not user:
            flash('خطا در دریافت اطلاعات کاربر')
            return redirect(url_for('logout'))

        # دریافت نتایج کوییزهای کاربر به ترتیب تاریخ
        results = QuizResult.query.filter_by(user_id=session['user_id']).order_by(QuizResult.date.desc()).all()

        # محاسبه آمارهای کاربر
        total_quizzes = len(results)
        avg_score = sum(r.score for r in results) / total_quizzes if total_quizzes > 0 else 0

        # آمار به تفکیک دسته‌بندی
        category_stats = {}
        for result in results:
            if result.category not in category_stats:
                category_stats[result.category] = {
                    'count': 0,
                    'total_score': 0,
                    'sum_time': 0,
                    'scores': []  # برای محاسبه توزیع نمرات
                }
            category_stats[result.category]['count'] += 1
            category_stats[result.category]['total_score'] += result.score
            category_stats[result.category]['sum_time'] += result.time_taken
            category_stats[result.category]['scores'].append(result.score)

        # محاسبه میانگین‌ها
        for cat, stats in category_stats.items():
            if stats['count'] > 0:
                stats['avg_score'] = stats['total_score'] / stats['count']
                stats['avg_time'] = stats['sum_time'] / stats['count']
            else:
                stats['avg_score'] = 0
                stats['avg_time'] = 0

        # پردازش داده‌های نمودار - آماده‌سازی تاریخ‌ها و نمرات برای نمودار
        chart_labels = []
        chart_scores = []
        chart_times = []

        # روند پیشرفت از قدیمی‌ترین به جدیدترین
        for result in sorted(results, key=lambda x: x.date):
            if hasattr(result, 'date') and result.date:
                try:
                    chart_labels.append(result.date.strftime('%Y/%m/%d'))
                    chart_scores.append(result.score)
                    chart_times.append(result.time_taken)
                except Exception as e:
                    print(f"Error formatting date: {e}")

        # توزیع نمرات برای نمودار
        score_distribution = {
            '0-20': 0,
            '21-40': 0,
            '41-60': 0,
            '61-80': 0,
            '81-100': 0
        }

        for result in results:
            if result.score <= 20:
                score_distribution['0-20'] += 1
            elif result.score <= 40:
                score_distribution['21-40'] += 1
            elif result.score <= 60:
                score_distribution['41-60'] += 1
            elif result.score <= 80:
                score_distribution['61-80'] += 1
            else:
                score_distribution['81-100'] += 1

        # داده‌های سطح دشواری
        difficulty_distribution = {
            'آسان': 0,
            'متوسط': 0,
            'سخت': 0
        }

        for result in results:
            if result.score >= 80:
                difficulty_distribution['آسان'] += 1
            elif result.score >= 60:
                difficulty_distribution['متوسط'] += 1
            else:
                difficulty_distribution['سخت'] += 1

        # لاگ برای دیباگ
        print("Chart data prepared:")
        print(f"Labels: {chart_labels}")
        print(f"Scores: {chart_scores}")
        print(f"Category stats: {category_stats}")
        print(f"Score distribution: {score_distribution}")
        print(f"Difficulty distribution: {difficulty_distribution}")

        return render_template('profile.html',
                               user=user,
                               results=results,
                               total_quizzes=total_quizzes,
                               avg_score=round(avg_score, 2),
                               category_stats=category_stats,
                               chart_labels=chart_labels,
                               chart_scores=chart_scores,
                               chart_times=chart_times,
                               score_distribution=score_distribution,
                               difficulty_distribution=difficulty_distribution)
    except Exception as e:
        print(f"Error in profile route: {str(e)}")
        flash(f'خطا در نمایش پروفایل: {str(e)}')
        return redirect(url_for('index'))


# روت‌های تیکت
@app.route('/tickets')
@login_required
def tickets_list():
    """لیست تیکت‌های کاربر یا همه تیکت‌ها برای ادمین"""
    user = User.query.get(session['user_id'])
    is_admin = (user.username == 'admin')

    if is_admin:
        # ادمین تمام تیکت‌ها را می‌بیند
        tickets = Ticket.query.order_by(Ticket.created_at.desc()).all()
    else:
        # کاربران عادی فقط تیکت‌های ارسالی و دریافتی خود را می‌بینند
        tickets = Ticket.query.filter(
            db.or_(
                Ticket.user_id == user.id,
                Ticket.recipient_id == user.id
            )
        ).order_by(Ticket.created_at.desc()).all()

    return render_template('tickets/list.html', tickets=tickets, user=user, is_admin=is_admin)


@app.route('/tickets/new', methods=['GET', 'POST'])
@login_required
def new_ticket():
    """ایجاد تیکت جدید"""
    user = User.query.get(session['user_id'])
    is_admin = (user.username == 'admin')

    # اگر ادمین باشد، لیست همه کاربران (به جز ادمین) را دریافت می‌کنیم
    users_list = []
    if is_admin:
        users_list = User.query.filter(User.username != 'admin').all()

    if request.method == 'POST':
        title = request.form['title'].strip()
        message = request.form['message'].strip()

        # بررسی اعتبارسنجی ورودی‌ها
        if not title or not message:
            flash('عنوان و متن پیام نمی‌توانند خالی باشند')
            return redirect(url_for('new_ticket'))

        # تعیین گیرنده تیکت
        recipient_id = None
        if is_admin:
            # اگر ادمین است، گیرنده را از فرم دریافت می‌کنیم
            recipient_id = request.form.get('recipient_id')
            if not recipient_id:
                flash('لطفاً یک کاربر را انتخاب کنید')
                return redirect(url_for('new_ticket'))
        else:
            # اگر کاربر عادی است، گیرنده ادمین است
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                flash('خطا در سیستم: ادمین یافت نشد')
                return redirect(url_for('tickets_list'))
            recipient_id = admin_user.id

        # ایجاد تیکت جدید
        ticket = Ticket(
            user_id=session['user_id'],  # فرستنده تیکت
            recipient_id=recipient_id,  # گیرنده تیکت
            title=title,
            status='باز'
        )

        db.session.add(ticket)
        db.session.commit()

        # ایجاد اولین پیام تیکت
        ticket_message = TicketMessage(
            ticket_id=ticket.id,
            user_id=session['user_id'],
            message=message,
            is_admin=is_admin
        )

        db.session.add(ticket_message)
        db.session.commit()

        flash('تیکت شما با موفقیت ثبت شد')
        return redirect(url_for('tickets_list'))

    return render_template('tickets/new.html', is_admin=is_admin, users=users_list)


@app.route('/tickets/<int:ticket_id>', methods=['GET', 'POST'])
@login_required
def view_ticket(ticket_id):
    """مشاهده و پاسخ به تیکت"""
    ticket = Ticket.query.get_or_404(ticket_id)
    user = User.query.get(session['user_id'])
    is_admin = (user.username == 'admin')

    # فقط فرستنده و گیرنده می‌توانند تیکت را ببینند
    if user.id != ticket.user_id and user.id != ticket.recipient_id:
        flash('شما اجازه دسترسی به این تیکت را ندارید')
        return redirect(url_for('tickets_list'))

    # تعیین آیا کاربر فعلی گیرنده تیکت است یا فرستنده
    is_recipient = (user.id == ticket.recipient_id)

    if request.method == 'POST':
        message = request.form['message'].strip()

        if not message:
            flash('متن پیام نمی‌تواند خالی باشد')
            return redirect(url_for('view_ticket', ticket_id=ticket.id))

        # بررسی اینکه آیا کاربر مجاز به پاسخ است
        if not is_recipient:
            flash('شما نمی‌توانید به این تیکت پاسخ دهید، لطفاً منتظر پاسخ طرف مقابل باشید')
            return redirect(url_for('view_ticket', ticket_id=ticket.id))

        # ایجاد پیام جدید
        ticket_message = TicketMessage(
            ticket_id=ticket.id,
            user_id=user.id,
            message=message,
            is_admin=is_admin
        )

        # به‌روزرسانی وضعیت تیکت اگر ادمین پاسخ می‌دهد
        if is_admin and ticket.status == 'باز':
            ticket.status = 'در حال بررسی'

        db.session.add(ticket_message)
        db.session.commit()

        flash('پیام شما با موفقیت ارسال شد')
        return redirect(url_for('view_ticket', ticket_id=ticket.id))

    # دریافت تمام پیام‌های مربوط به این تیکت
    messages = TicketMessage.query.filter_by(ticket_id=ticket.id).order_by(TicketMessage.created_at).all()

    # دریافت اطلاعات طرف مقابل
    other_user_id = ticket.recipient_id if ticket.user_id == user.id else ticket.user_id
    other_user = User.query.get(other_user_id)

    return render_template('tickets/view.html',
                           ticket=ticket,
                           messages=messages,
                           user=user,
                           is_recipient=is_recipient,
                           other_user=other_user)


@app.route('/tickets/<int:ticket_id>/close', methods=['POST'])
@login_required
def close_ticket(ticket_id):
    """بستن تیکت"""
    ticket = Ticket.query.get_or_404(ticket_id)
    user = User.query.get(session['user_id'])

    # فقط فرستنده و گیرنده می‌توانند تیکت را ببندند
    if user.id != ticket.user_id and user.id != ticket.recipient_id:
        flash('شما اجازه بستن این تیکت را ندارید')
        return redirect(url_for('tickets_list'))

    # بستن تیکت
    ticket.status = 'بسته'
    db.session.commit()

    flash('تیکت با موفقیت بسته شد')
    return redirect(url_for('view_ticket', ticket_id=ticket.id))


@app.route('/tickets/<int:ticket_id>/reopen', methods=['POST'])
@login_required
def reopen_ticket(ticket_id):
    """بازگشایی مجدد تیکت"""
    ticket = Ticket.query.get_or_404(ticket_id)
    user = User.query.get(session['user_id'])

    # فقط فرستنده و گیرنده می‌توانند تیکت را بازگشایی کنند
    if user.id != ticket.user_id and user.id != ticket.recipient_id:
        flash('شما اجازه بازگشایی این تیکت را ندارید')
        return redirect(url_for('tickets_list'))

    # بازگشایی مجدد تیکت
    ticket.status = 'باز'
    db.session.commit()

    flash('تیکت با موفقیت بازگشایی شد')
    return redirect(url_for('view_ticket', ticket_id=ticket.id))

# === Error Handlers ===
@app.errorhandler(404)
def page_not_found(e):
    """نمایش صفحه سفارشی برای خطای 404"""
    return render_template('errors/404.html', error_code='404'), 404

@app.errorhandler(403)
def forbidden(e):
    """نمایش صفحه سفارشی برای خطای 403"""
    return render_template('errors/403.html', error_code='403'), 403

@app.errorhandler(500)
def internal_server_error(e):
    """نمایش صفحه سفارشی برای خطای 500"""
    return render_template('errors/500.html', error_code='500'), 500

@app.errorhandler(400)
def bad_request(e):
    """نمایش صفحه سفارشی برای خطای 400"""
    return render_template('errors/400.html', error_code='400'), 400

# اضافه کردن لاگینگ برای خطاها
import logging
from logging.handlers import RotatingFileHandler
import os

# تنظیمات لاگر
if not app.debug:
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/quiz_app.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Quiz App startup')

@app.errorhandler(401)
def unauthorized(e):
    """نمایش صفحه سفارشی برای خطای 401"""
    return render_template('errors/generic.html',
                          error_code='401',
                          error_title='احراز هویت نشده',
                          error_message='شما برای دسترسی به این صفحه باید احراز هویت شوید.'), 401

@app.errorhandler(405)
def method_not_allowed(e):
    """نمایش صفحه سفارشی برای خطای 405"""
    return render_template('errors/generic.html',
                          error_code='405',
                          error_title='متد غیرمجاز',
                          error_message='متد درخواست شده برای این URL مجاز نیست.'), 405

@app.errorhandler(429)
def too_many_requests(e):
    """نمایش صفحه سفارشی برای خطای 429"""
    return render_template('errors/generic.html',
                          error_code='429',
                          error_title='درخواست‌های بیش از حد',
                          error_message='تعداد درخواست‌های شما بیش از حد مجاز است. لطفاً کمی صبر کنید و دوباره تلاش کنید.'), 429

# برای گرفتن همه خطاهای احتمالی دیگر
@app.errorhandler(Exception)
def handle_exception(e):
    """صفحه خطای پیش‌فرض برای تمام استثناها"""
    # اگر خطای HTTP باشد، به handler مخصوص خودش ارجاع می‌دهیم
    if isinstance(e, HTTPException):
        return e

    # اگر برنامه در حالت debug نباشد، خطای 500 نمایش می‌دهیم
    if not app.debug:
        app.logger.error('Unhandled Exception: %s', str(e))
        return render_template('errors/500.html'), 500

    # در حالت debug، خطا را به Flask می‌دهیم تا traceback کامل نمایش داده شود
    return e

if __name__ == '__main__':
    with app.app_context():
        # ایجاد جداول دیتابیس در صورت عدم وجود
        db.create_all()
    app.run(debug=True)