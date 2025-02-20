from app import app, db
from app import User
from werkzeug.security import generate_password_hash

def create_admin():
    with app.app_context():
        # Admin details
        username = "admin"
        email = "admin@example.com"
        password = "admin_password"  # Replace with a secure password

        # Check if admin already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"User '{username}' already exists!")
            return

        # Create admin
        admin = User(
            username=username,
            email=email,
            role="admin"
        )
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        print(f"Admin '{username}' created successfully!")

if __name__ == "__main__":
    create_admin()