from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import json
from datetime import datetime, timedelta
import os
from random import shuffle

# تنظیمات اولیه فلسک
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # کلید رمزنگاری برای سشن‌ها
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'  # آدرس دیتابیس
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# تعریف مدل‌های دیتابیس
class User(db.Model):
    """مدل کاربر برای ذخیره اطلاعات کاربران"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    quizzes = db.relationship('QuizResult', backref='user', lazy=True)
    friends = db.relationship('Friend', backref='user', lazy=True)

class Question(db.Model):
    """مدل سوال برای ذخیره سوالات کوییز"""
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    question_text = db.Column(db.String(500), nullable=False)
    correct_answer = db.Column(db.String(200), nullable=False)
    wrong_answers = db.Column(db.String(500), nullable=False)  # JSON string
    difficulty = db.Column(db.String(50), nullable=False)  # سطح دشواری سوال (easy, medium, hard)

    def __repr__(self):
        return f'<Question {self.id} - {self.category}>'


class QuizResult(db.Model):
    """مدل نتایج برای ذخیره نتایج کوییزها"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    time_taken = db.Column(db.Integer, nullable=False)  # زمان به ثانیه


class Friend(db.Model):
    """مدل دوستان برای ذخیره روابط دوستی بین کاربران"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class DailyChallenge(db.Model):
    """مدل چالش روزانه برای ایجاد سوالات ویژه هر روز"""
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    question = db.relationship('Question', backref='daily_challenges')


class QuizFeedback(db.Model):
    """مدل نظرات و پیشنهادات کاربران"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz_result.id'), nullable=False)
    feedback_text = db.Column(db.String(500), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


# مسیرهای برنامه
@app.route('/')
def index():
    """صفحه اصلی برنامه"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # دریافت دسته‌بندی‌های موجود از دیتابیس
    categories = db.session.query(Question.category).distinct().all()
    categories = [cat[0] for cat in categories]

    # چالش روزانه
    today_challenge = DailyChallenge.query.filter_by(date=datetime.utcnow().date()).first()
    
    return render_template('index.html', categories=categories, today_challenge=today_challenge)


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


@app.route('/daily_challenge', methods=['GET'])
def daily_challenge():
    """چالش روزانه"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    challenge = DailyChallenge.query.filter_by(date=datetime.utcnow().date()).first()
    if not challenge:
        flash('چالش روزانه برای امروز وجود ندارد')
        return redirect(url_for('index'))

    question = challenge.question
    return render_template('daily_challenge.html', question=question)


@app.route('/quiz/<category>', methods=['GET'])
def quiz(category):
    """نمایش کوییز برای یک دسته‌بندی خاص"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    questions = Question.query.filter_by(category=category).limit(10).all()
    if not questions:
        flash('سوالی در این دسته‌بندی وجود ندارد')
        return redirect(url_for('index'))

    quiz_questions = []
    for q in questions:
        wrong_answers = json.loads(q.wrong_answers)
        options = wrong_answers + [q.correct_answer]
        shuffle(options)

        quiz_questions.append({
            'id': q.id,
            'question': q.question_text,
            'options': options,
            'correct_answer': q.correct_answer
        })

    return render_template('quiz.html',
                           questions=quiz_questions,
                           category=category)


@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    """ثبت نتیجه کوییز"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    data = request.get_json()
    score = data.get('score')
    category = data.get('category')
    time_taken = data.get('time_taken')

    if not all([score, category, time_taken]):
        return jsonify({'error': 'اطلاعات ناقص است'}), 400

    result = QuizResult(
        user_id=session['user_id'],
        category=category,
        score=score,
        time_taken=time_taken
    )

    db.session.add(result)
    db.session.commit()

    return jsonify({'success': True, 'message': 'نتیجه با موفقیت ثبت شد'})


@app.route('/profile')
def profile():
    """نمایش پروفایل کاربر و نتایج کوییزها"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    results = QuizResult.query.filter_by(user_id=session['user_id']).order_by(QuizResult.date.desc()).all()

    return render_template('profile.html', user=user, results=results)


@app.route('/friends')
def friends():
    """نمایش لیست دوستان و مقایسه نتایج"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    friends = [f.friend_id for f in user.friends]

    friend_results = []
    for friend_id in friends:
        results = QuizResult.query.filter_by(user_id=friend_id).all()
        friend_results.append({'friend_id': friend_id, 'results': results})

    return render_template('friends.html', friend_results=friend_results)


@app.route('/add_question', methods=['GET', 'POST'])
def add_question():
    """اضافه کردن سوال جدید"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        category = request.form['category']
        difficulty = request.form['difficulty']
        question_text = request.form['question_text']
        correct_answer = request.form['correct_answer']
        wrong_answers = request.form.getlist('wrong_answers')

        new_question = Question(
            category=category,
            difficulty=difficulty,
            question_text=question_text,
            correct_answer=correct_answer,
            wrong_answers=json.dumps(wrong_answers)
        )

        db.session.add(new_question)
        db.session.commit()

        flash('سوال جدید با موفقیت اضافه شد')
        return redirect(url_for('index'))

    return render_template('add_question.html')


@app.route('/remove_question/<question_id>', methods=['POST'])
def remove_question(question_id):
    """حذف سوال از دیتابیس"""
    question = Question.query.get(question_id)
    if question:
        db.session.delete(question)
        db.session.commit()
        flash('سوال با موفقیت حذف شد')
    return redirect(url_for('index'))

# تحلیل عملکرد کاربران
@app.route('/user_performance')
def user_performance():
    """تحلیل عملکرد کاربران"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    results = QuizResult.query.filter_by(user_id=session['user_id']).all()

    total_questions = len(results)
    correct_answers = sum([result.score for result in results])
    success_rate = (correct_answers / total_questions) * 100 if total_questions > 0 else 0

    # مقایسه با میانگین کل کاربران
    all_users = User.query.all()
    all_user_results = QuizResult.query.all()
    avg_success_rate = sum([r.score for r in all_user_results]) / len(all_user_results) if len(all_user_results) > 0 else 0

    return render_template('user_performance.html', user=user, success_rate=success_rate, avg_success_rate=avg_success_rate)


# تحلیل سوالات
@app.route('/question_analysis')
def question_analysis():
    """تحلیل سوالات"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    questions = Question.query.all()
    question_analysis_data = []
    for question in questions:
        total_answers = QuizResult.query.filter_by(category=question.category).count()
        correct_answers = QuizResult.query.filter_by(category=question.category).filter_by(score=1).count()
        success_rate = (correct_answers / total_answers) * 100 if total_answers > 0 else 0

        question_analysis_data.append({
            'question': question.question_text,
            'success_rate': success_rate
        })

    # شناسایی سوالات مشکل‌دار
    problematic_questions = [q for q in question_analysis_data if q['success_rate'] < 50]

    return render_template('question_analysis.html', question_analysis_data=question_analysis_data, problematic_questions=problematic_questions)


# تحلیل دسته‌بندی‌ها
@app.route('/category_analysis')
def category_analysis():
    """تحلیل دسته‌بندی‌ها"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    categories = db.session.query(Question.category).distinct().all()
    category_data = []

    for category in categories:
        category_questions = Question.query.filter_by(category=category).all()
        correct_answers = 0
        total_time = 0
        for question in category_questions:
            correct_answers += QuizResult.query.filter_by(category=category).filter_by(score=1).count()
            total_time += QuizResult.query.filter_by(category=category).filter_by(score=1).first().time_taken

        success_rate = (correct_answers / len(category_questions)) * 100 if len(category_questions) > 0 else 0
        avg_time = total_time / len(category_questions) if len(category_questions) > 0 else 0

        category_data.append({
            'category': category[0],
            'success_rate': success_rate,
            'avg_time': avg_time
        })

    return render_template('category_analysis.html', category_data=category_data)

@app.route('/analytics')
def analytics():
    """صفحه انتخاب کاربر برای مشاهده آمار"""
    users = User.query.all()
    return render_template('select_user.html', users=users)


@app.route('/admin_user_analytics/<int:user_id>')
def admin_user_analytics(user_id):
    """صفحه آمار یک کاربر خاص"""
    user = User.query.get_or_404(user_id)
    user_results = QuizResult.query.filter_by(user_id=user.id).all()

    avg_score = db.session.query(db.func.avg(QuizResult.score)).filter(QuizResult.user_id == user.id).scalar() or 0

    return render_template('analytics.html', selected_user=user, user_results=user_results, avg_total_score=avg_score)

# تحلیل زمانی
@app.route('/score_trend')
def score_trend():
    """تحلیل روند نمرات در طول زمان"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    results = QuizResult.query.filter_by(user_id=session['user_id']).order_by(QuizResult.date).all()
    scores_by_date = {}

    for result in results:
        date_str = result.date.strftime('%Y-%m-%d')
        if date_str not in scores_by_date:
            scores_by_date[date_str] = []
        scores_by_date[date_str].append(result.score)

    return render_template('score_trend.html', scores_by_date=scores_by_date)

@app.route('/difficulty_analysis')
def difficulty_analysis():
    """تحلیل سطح دشواری"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    difficulties = db.session.query(Question.difficulty).distinct().all()
    difficulty_data = []

    for difficulty in difficulties:
        difficulty_name = difficulty[0]
        questions_in_difficulty = Question.query.filter_by(difficulty=difficulty_name).all()

        # تعداد سوالات در این سطح
        total_questions = len(questions_in_difficulty)
        
        # توزیع نمرات
        scores = []
        for question in questions_in_difficulty:
            results = QuizResult.query.filter_by(category=question.category).all()
            scores.extend([result.score for result in results])

        # نرخ موفقیت
        correct_answers = sum([1 for score in scores if score == 1])
        success_rate = (correct_answers / len(scores)) * 100 if len(scores) > 0 else 0

        # زمان متوسط
        total_time = 0
        total_responses = 0
        for question in questions_in_difficulty:
            results = QuizResult.query.filter_by(category=question.category).all()
            for result in results:
                total_time += result.time_taken
                total_responses += 1

        avg_time = total_time / total_responses if total_responses > 0 else 0

        difficulty_data.append({
            'difficulty': difficulty_name,
            'total_questions': total_questions,
            'success_rate': success_rate,
            'avg_time': avg_time
        })

    return render_template('difficulty_analysis.html', difficulty_data=difficulty_data)


# شاخص‌های کلیدی عملکرد (KPIs)
@app.route('/kpi')
def kpi():
    """شاخص‌های کلیدی عملکرد (KPIs)"""
    total_quizzes = QuizResult.query.count()
    avg_score = db.session.query(db.func.avg(QuizResult.score)).scalar()
    completed_quizzes = QuizResult.query.filter(QuizResult.score > 0).count()
    user_growth = len(User.query.all())  # تعداد کاربران جدید

    return render_template('kpi.html', total_quizzes=total_quizzes, avg_score=avg_score, completed_quizzes=completed_quizzes, user_growth=user_growth)


# رتبه‌بندی کاربران
@app.route('/user_ranking')
def user_ranking():
    """رتبه‌بندی کاربران"""
    rankings = db.session.query(User.username, db.func.avg(QuizResult.score).label('average_score'))\
        .join(QuizResult, User.id == QuizResult.user_id)\
        .group_by(User.id)\
        .order_by(db.func.avg(QuizResult.score).desc()).all()

    return render_template('user_ranking.html', rankings=rankings)


if __name__ == '__main__':
    db.create_all()  # ایجاد دیتابیس
    app.run(debug=True)
