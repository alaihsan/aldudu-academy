import os
import sys

# Ensure we can import from the root
sys.path.append(os.getcwd())

from app import create_app
from app.models import db, User, UserRole

def create_admin():
    app = create_app()
    with app.app_context():
        # Check if user already exists
        admin_email = "admin@aldudu.com"
        existing_user = User.query.filter_by(email=admin_email).first()
        
        if existing_user:
            print(f"User {admin_email} already exists.")
            return

        admin = User(
            name="Super Admin",
            email=admin_email,
            role=UserRole.ADMIN,
            is_active=True,
            email_verified=True
        )
        admin.set_password("admin123")
        
        db.session.add(admin)
        db.session.commit()
        print(f"Superadmin account created successfully!")
        print(f"Email: {admin_email}")
        print(f"Password: admin123")

if __name__ == "__main__":
    create_admin()
