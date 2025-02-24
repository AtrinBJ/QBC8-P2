from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import json
from datetime import datetime
import os

# فلسک
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  #کلید رمز
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'  # آدرس دیتابیس
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


#دیتابیس
class User(db.Model):
    """مدل کاربر برای ذخیره اطلاعات کاربران"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    quizzes = db.relationship('QuizResult', backref='user', lazy=True)


class Question(db.Model):
    """مدل سوال برای ذخیره سوالات کوییز"""
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    question_text = db.Column(db.String(500), nullable=False)
    correct_answer = db.Column(db.String(200), nullable=False)
    wrong_answers = db.Column(db.String(500), nullable=False)  


class QuizResult(db.Model):
    """مدل نتایج برای ذخیره نتایج کوییزها"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    time_taken = db.Column(db.Integer, nullable=False) 


#program routs
@app.route('/')
def index():
    """صفحه اصلی برنامه"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    categories = db.session.query(Question.category).distinct().all()
    categories = [cat[0] for cat in categories]

    return render_template('index.html', categories=categories)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """صفحه ورود کاربران"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            flash('با موفقیت وارد شدید')
            return redirect(url_for('index'))

        flash('نام کاربری یا رمز عبور اشتباه است')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """صفحه ثبت نام کاربران جدید"""
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('این نام کاربری قبلاً ثبت شده است')
            return redirect(url_for('register'))

        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()

        flash('ثبت نام با موفقیت انجام شد')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/logout')
def logout():
    """خروج کاربر از سیستم"""
    session.clear()
    flash('با موفقیت خارج شدید')
    return redirect(url_for('login'))


@app.route('/admin/questions', methods=['GET', 'POST'])
def manage_questions():
    """صفحه مدیریت سوالات (فقط برای ادمین)"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # admin dastrasi
    user = User.query.get(session['user_id'])
    if not user or user.username != 'admin':
        flash('شما دسترسی به این بخش ندارید')
        return redirect(url_for('index'))

    if request.method == 'POST':
        # getting info 
        category = request.form['category']
        question_text = request.form['question_text']
        correct_answer = request.form['correct_answer']
        wrong_answers = request.form.getlist('wrong_answers[]')

        # create new questions
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

    # available questions
    questions = Question.query.all()
    return render_template('admin/questions.html', questions=questions)


@app.route('/admin/import_questions', methods=['POST'])
def import_questions():
    """دریافت سوالات از API خارجی"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if not user or user.username != 'admin':
        return jsonify({'error': 'دسترسی غیرمجاز'}), 403

    try:
        response = requests.get('https://opentdb.com/api.php', params={
            'amount': 10,
            'type': 'multiple'
        })

        data = response.json()

        if data['response_code'] == 0:
            for q in data['results']:
                question = Question(
                    category=q['category'],
                    question_text=q['question'],
                    correct_answer=q['correct_answer'],
                    wrong_answers=json.dumps(q['incorrect_answers'])
                )
                db.session.add(question)

            db.session.commit()
            return jsonify({'success': True, 'message': 'سوالات با موفقیت اضافه شدند'})

        return jsonify({'error': 'خطا در دریافت سوالات'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/admin/delete_question/<int:question_id>', methods=['POST'])
def delete_question(question_id):
    """حذف سوال با شناسه مشخص از دیتابیس"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if not user or user.username != 'admin':
        flash('شما دسترسی به این بخش ندارید')
        return redirect(url_for('index'))

    question = Question.query.get_or_404(question_id)
    db.session.delete(question)
    db.session.commit()

    flash('سوال با موفقیت حذف شد')
    return redirect(url_for('manage_questions'))


@app.route('/admin/analyze_results')
def analyze_results():
    """تحلیل عملکرد کاربرها و سوالات"""
    # amalkard karbar
    total_users = User.query.count()
    total_quizzes = QuizResult.query.count()
    total_score = db.session.query(db.func.sum(QuizResult.score)).scalar()
    average_score = total_score / total_quizzes if total_quizzes else 0

    # tahlil soalat
    question_analysis = db.session.query(
        Question.id,
        db.func.count(QuizResult.id).label('attempts'),
        db.func.sum(QuizResult.score).label('correct_answers')
    ).join(QuizResult, Question.id == QuizResult.category).group_by(Question.id).all()

    # tahlil gategory
    category_analysis = db.session.query(
        Question.category,
        db.func.count(QuizResult.id).label('attempts'),
        db.func.sum(QuizResult.score).label('correct_answers')
    ).join(QuizResult, Question.id == QuizResult.category).group_by(Question.category).all()

    # kpis
    total_quizzes = QuizResult.query.count()
    total_score = db.session.query(db.func.sum(QuizResult.score)).scalar()
    average_score = total_score / total_quizzes if total_quizzes else 0

    return render_template('admin/analyze_results.html', 
                           total_users=total_users, 
                           average_score=average_score,
                           question_analysis=question_analysis,
                           category_analysis=category_analysis)


@app.route('/profile')
def profile():
    """نمایش پروفایل کاربر و نتایج کوییزها"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    results = QuizResult.query.filter_by(user_id=session['user_id']).order_by(QuizResult.date.desc()).all()

    return render_template('profile.html', user=user, results=results)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # create database jadval
    app.run(debug=True)
