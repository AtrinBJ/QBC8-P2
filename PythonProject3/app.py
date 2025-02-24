from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import json
from datetime import datetime
import matplotlib
matplotlib.use('Agg')  # Use a non-GUI backend
import matplotlib.pyplot as plt


# تنظیمات اولیه فلسک
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # ?????????کلید رمزنگاری برای سشن‌ها
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'  # آدرس دیتابیس
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# تعریف مدل‌های دیتابیس
class User(db.Model):
    """مدل کاربر برای ذخیره اطلاعات کاربران"""
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    quizzes = db.relationship('QuizResult', backref='user', lazy=True)
    join_datetime = db.Column(db.DateTime, nullable=False)


class Question(db.Model):
    """مدل سوال برای ذخیره سوالات کوییز"""
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    question_text = db.Column(db.String(500), nullable=False)
    correct_answer = db.Column(db.String(200), nullable=False)
    wrong_answers = db.Column(db.String(500), nullable=False)  # JSON string


class QuizResult(db.Model):
    """مدل نتایج برای ذخیره نتایج کوییزها"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)#???????????
    category = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)#??????????
    time_taken = db.Column(db.Integer, nullable=False)  # زمان به ثانیه\????????????


# مسیرهای برنامه
@app.route('/')
def index():
    """صفحه اصلی برنامه"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # دریافت دسته‌بندی‌های موجود از دیتابیس
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
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('این نام کاربری قبلاً ثبت شده است')
            return redirect(url_for('register'))

        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            first_name=first_name,
            last_name=last_name,
            join_date=datetime.now()
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

    # بررسی دسترسی ادمین
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

    # نمایش لیست سوالات موجود
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


@app.route('/quiz/<category>')
def quiz(category):
    """نمایش کوییز برای یک دسته‌بندی خاص"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if not questions:
        flash('سوالی در این دسته‌بندی وجود ندارد')
        return redirect(url_for('index'))

    # تبدیل سوالات به فرمت مناسب برای نمایش
    quiz_questions = []
    for q in questions:
        wrong_answers = json.loads(q.wrong_answers)
        options = wrong_answers + [q.correct_answer]
        # مخلوط کردن گزینه‌ها
        from random import shuffle
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


@app.route('/edit', methods=['POST'])
def edit():
    id = request.form['id']
    user = db.session.get(User, id)
    results = QuizResult.query.filter_by(user_id=session['user_id']).order_by(QuizResult.date.desc()).all()
    try:
        user.first_name = request.form['first_name']
        user.last_name = request.form['last_name']
        if user.password_hash != request.form['password']:
            user.password_hash = generate_password_hash(request.form['password'])
        user.email = request.form['email']
        db.session.commit()
        flash('پروفایل به روز شد')
        return redirect("/profile")
    except Exception as e:
        print(e)
        flash(message='خطا در به روز رسانی پروفایل', category='error')
        return redirect("/profile")


@app.route('/plot')
def plot():
    # Fetch quiz results from the database, ordered by date
    results = QuizResult.query.filter_by(user_id=session['user_id']).order_by(QuizResult.date).all()

    # Extract dates and scores
    dates = [result.date for result in results]
    scores = [result.score for result in results]

    # Create the plot
    plt.figure(figsize=(10, 5))  # Set the figure size
    plt.plot(dates, scores, marker='o', linestyle='-', color='r')
    plt.title('Quiz Scores Over Dates')
    plt.xlabel('Date')
    plt.ylabel('Scores')
    plt.grid()

    # Save the plot as an image file
    plot_path = 'static/plot.png'  # Save in a static directory
    plt.savefig(plot_path)
    plt.close()  # Close the plot to free memory

    return send_file(plot_path)  # Serve the image file

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # ایجاد جداول دیتابیس در صورت عدم وجود
    app.run(debug=True, port=5001)