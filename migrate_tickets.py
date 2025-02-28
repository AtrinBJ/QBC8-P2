# migrate_tickets.py - اسکریپت به‌روزرسانی دیتابیس تیکت‌ها
from app import app, db, User, Ticket
from sqlalchemy import text
from sqlalchemy.orm import Session


def upgrade_ticket_model():
    """افزودن فیلد recipient_id به جدول تیکت‌ها و به‌روزرسانی داده‌های موجود"""
    with app.app_context():
        # بررسی اینکه آیا ستون قبلاً وجود دارد
        inspector = db.inspect(db.engine)
        has_recipient_column = False

        try:
            columns = [column['name'] for column in inspector.get_columns('ticket')]
            has_recipient_column = 'recipient_id' in columns
        except Exception as e:
            print(f"خطا در بررسی ستون‌ها: {str(e)}")
            return False

        if not has_recipient_column:
            try:
                # اضافه کردن ستون recipient_id به جدول تیکت با استفاده از SQL خام
                with db.engine.begin() as conn:
                    conn.execute(text("ALTER TABLE ticket ADD COLUMN recipient_id INTEGER REFERENCES user(id)"))
                    print("ستون recipient_id با موفقیت اضافه شد")

                # پیدا کردن ادمین
                admin = User.query.filter_by(username='admin').first()
                if not admin:
                    print("خطا: کاربر ادمین پیدا نشد")
                    return False

                # به‌روزرسانی تیکت‌های موجود
                session = Session(db.engine)

                try:
                    # به‌روزرسانی تیکت‌های ایجاد شده توسط کاربران عادی (گیرنده: ادمین)
                    session.execute(
                        text("UPDATE ticket SET recipient_id = :admin_id WHERE user_id != :admin_id"),
                        {"admin_id": admin.id}
                    )

                    # پیدا کردن اولین کاربر غیر ادمین
                    first_user = User.query.filter(User.username != 'admin').first()

                    if first_user:
                        # به‌روزرسانی تیکت‌های ایجاد شده توسط ادمین (گیرنده: اولین کاربر غیر ادمین)
                        session.execute(
                            text("UPDATE ticket SET recipient_id = :user_id WHERE user_id = :admin_id"),
                            {"user_id": first_user.id, "admin_id": admin.id}
                        )

                    session.commit()
                    print("داده‌های تیکت‌ها با موفقیت به‌روزرسانی شدند")

                except Exception as e:
                    session.rollback()
                    print(f"خطا در به‌روزرسانی داده‌ها: {str(e)}")
                    return False
                finally:
                    session.close()

                return True
            except Exception as e:
                print(f"خطا در اضافه کردن ستون: {str(e)}")
                return False
        else:
            print("ستون recipient_id قبلاً وجود دارد")
            return True


if __name__ == '__main__':
    with app.app_context():
        # ایجاد جداول اگر وجود ندارند
        db.create_all()

        # به‌روزرسانی مدل تیکت
        success = upgrade_ticket_model()

        if success:
            print("مهاجرت دیتابیس با موفقیت انجام شد")
        else:
            print("خطا در مهاجرت دیتابیس")