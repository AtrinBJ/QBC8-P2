from app import app, db

with app.app_context():
    # ساخت تمام جداول
    db.create_all()
    print("تمام جداول با موفقیت ایجاد شدند!")