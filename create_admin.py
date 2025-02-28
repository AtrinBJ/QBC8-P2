import os
import sys
from app import app, db, User
from werkzeug.security import generate_password_hash


def create_admin():
    with app.app_context():
        # چک کردن اینکه آیا کاربر ادمین قبلاً وجود دارد
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print("کاربر ادمین قبلاً وجود دارد.")
            return

        # ساخت کاربر ادمین جدید
        admin = User(
            username='admin',
            email='admin@example.com',
            password_hash=generate_password_hash('your-admin-password')
        )

        try:
            db.session.add(admin)
            db.session.commit()
            print("کاربر ادمین با موفقیت ایجاد شد.")
        except Exception as e:
            print(f"خطا در ایجاد کاربر ادمین: {str(e)}")
            db.session.rollback()


if __name__ == '__main__':
    create_admin()