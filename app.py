# وارد کردن کتابخانه‌های مورد نیاز
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import json
from datetime import datetime
import os
import itertools

# تنظیمات اولیه فلسک
app = Flask(__name__)
# کلید رمزنگاری برای سشن‌ها - در محیط تولید باید تغییر کند
app.config['SECRET_KEY'] = 'your-secret-key-here'
# آدرس دیتابیس SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# راه‌اندازی Flask-Login برای مدیریت سشن‌های کاربران
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # مسیر صفحه لاگین

# راه‌اندازی SQLAlchemy
db = SQLAlchemy(app)


# تعریف مدل‌های دیتابیس
class User(UserMixin, db.Model):
    """مدل کاربر برای ذخیره اطلاعات کاربران"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    # ارتباط یک به چند با نتایج کوییز
    quizzes = db.relationship('QuizResult', backref='user', lazy=True)


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
    """مدیریت ورود کاربران"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            session['user_id'] = user.id
            flash('با موفقیت وارد شدید')
            # تغییر مسیر به صفحه پروفایل بعد از ورود
            return redirect(url_for('profile'))

        flash('نام کاربری یا رمز عبور اشتباه است')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """مدیریت ثبت نام کاربران جدید"""
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # بررسی تکراری نبودن نام کاربری
        if User.query.filter_by(username=username).first():
            flash('این نام کاربری قبلاً ثبت شده است')
            return redirect(url_for('register'))

        # ایجاد کاربر جدید
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()

        # ورود کاربر پس از ثبت‌نام
        login_user(user)
        session['user_id'] = user.id
        flash('ثبت نام با موفقیت انجام شد')

        # هدایت به صفحه پروفایل
        return redirect(url_for('profile'))

    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    """خروج کاربر از سیستم"""
    logout_user()
    session.clear()
    flash('با موفقیت خارج شدید')
    return redirect(url_for('login'))


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


@app.route('/admin/analytics')
@login_required
def admin_analytics():
    """صفحه آمار و تحلیل‌ها - فقط برای ادمین"""
    user = User.query.get(session['user_id'])
    if not user or user.username != 'admin':
        flash('شما دسترسی به این بخش ندارید')
        return redirect(url_for('index'))

    # === آمارهای کلی (KPIs) ===
    total_users = User.query.count()
    total_quizzes = QuizResult.query.count()
    total_questions = Question.query.count()
    avg_total_score = db.session.query(db.func.avg(QuizResult.score)).scalar() or 0

    # === تحلیل عملکرد کاربران ===
    user_performance = db.session.query(
        User.username,
        db.func.count(QuizResult.id).label('quiz_count'),
        db.func.avg(QuizResult.score).label('avg_score'),
        db.func.min(QuizResult.score).label('min_score'),
        db.func.max(QuizResult.score).label('max_score')
    ).join(QuizResult).group_by(User.username).all()

    # تبدیل user_performance به لیست دیکشنری‌ها برای دسترسی آسان‌تر
    user_performance_list = []
    for u in user_performance:
        # پیدا کردن بهترین دسته‌بندی برای کاربر
        user_id = User.query.filter_by(username=u.username).first().id
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
            'username': u.username,
            'quiz_count': u.quiz_count,
            'avg_score': u.avg_score,
            'min_score': u.min_score,
            'max_score': u.max_score,
            'category_best': best_category
        })

    # روند پیشرفت هر کاربر در طول زمان
    user_progress = db.session.query(
        User.username,
        QuizResult.date,
        QuizResult.score
    ).join(QuizResult).order_by(User.username, QuizResult.date).all()

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
        difficulty_stats[level]['avg_score'] = (
                                                       difficulty_stats[level]['avg_score'] + result.score
                                               ) / 2 if difficulty_stats[level]['avg_score'] > 0 else result.score

    # === آماده‌سازی داده‌ها برای نمودارها ===
    chart_data = {
        # داده‌های روند زمانی
        'time_labels': [str(stat.date) for stat in time_stats],
        'time_counts': [stat.quiz_count for stat in time_stats],
        'time_scores': [float(stat.avg_score) for stat in time_stats],

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
        'difficulty_scores': [stats['avg_score'] for stats in difficulty_stats.values()],

        # داده‌های پیشرفت کاربران
        'progress_data': {}
    }

    # پردازش داده‌های پیشرفت کاربر با استفاده از itertools.groupby
    for username, group in itertools.groupby(user_progress, lambda x: x[0]):
        chart_data['progress_data'][username] = {
            'dates': [],
            'scores': []
        }
        for _, date, score in group:
            chart_data['progress_data'][username]['dates'].append(str(date.date()))
            chart_data['progress_data'][username]['scores'].append(float(score))

    return render_template('admin/analytics.html',
                           total_users=total_users,
                           total_quizzes=total_quizzes,
                           total_questions=total_questions,
                           avg_total_score=round(avg_total_score, 2),
                           user_performance=user_performance_list,
                           category_stats=category_stats,
                           question_stats=question_stats,
                           questions_dict=questions_dict,
                           chart_data=chart_data)


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


@app.route('/quiz/<category>')
@login_required
def quiz(category):
    """نمایش کوییز برای یک دسته‌بندی خاص"""
    # دریافت 10 سوال تصادفی از دسته‌بندی انتخاب شده
    questions = Question.query.filter_by(category=category).limit(10).all()
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
                answers=json.dumps(answers)
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
    user = User.query.get(session['user_id'])

    # ساده‌سازی کوئری برای اجتناب از خطا
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
                'total_score': 0
            }
        category_stats[result.category]['count'] += 1
        category_stats[result.category]['total_score'] += result.score

    for stats in category_stats.values():
        stats['avg_score'] = stats['total_score'] / stats['count']

    # پردازش داده‌های نمودار - آماده‌سازی تاریخ‌ها و نمرات برای نمودار
    chart_labels = []
    chart_scores = []

    for result in reversed(results):
        if hasattr(result, 'date') and result.date:
            try:
                chart_labels.append(result.date.strftime('%m/%d'))
                chart_scores.append(result.score)
            except Exception as e:
                print(f"Error formatting date: {e}")

    return render_template('profile.html',
                           user=user,
                           results=results,
                           total_quizzes=total_quizzes,
                           avg_score=round(avg_score, 2),
                           category_stats=category_stats,
                           chart_labels=chart_labels,
                           chart_scores=chart_scores)

@app.route('/edit', methods=['POST'])
def edit():
    id = request.form['id']
    user = db.session.get(User, id)
    try:
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


if __name__ == '__main__':
    with app.app_context():
        # ایجاد جداول دیتابیس در صورت عدم وجود
        db.create_all()
    app.run(debug=True)