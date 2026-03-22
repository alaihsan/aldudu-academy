import os
import sys

sys.path.append(os.getcwd())

from app import create_app
from app.models import db, User, UserRole

def check_admin():
    app = create_app()
    with app.app_context():
        admin = User.query.filter_by(email="admin@aldudu.com").first()
        
        if admin:
            print(f"\n{'='*60}")
            print(f"Account Details: admin@aldudu.com")
            print(f"{'='*60}")
            print(f"ID:              {admin.id}")
            print(f"Name:            {admin.name}")
            print(f"Email:           {admin.email}")
            print(f"Role:            {admin.role.value}")
            print(f"is_active:       {admin.is_active}")
            print(f"email_verified:  {admin.email_verified}")
            print(f"school_id:       {admin.school_id}")
            print(f"school:          {admin.school.name if admin.school else 'None'}")
            print(f"{'='*60}\n")
            
            # Check if role is SUPER_ADMIN
            if admin.role != UserRole.SUPER_ADMIN:
                print(f"WARNING: Role is {admin.role.value}, NOT super_admin!")
                print(f"Updating role to SUPER_ADMIN...")
                admin.role = UserRole.SUPER_ADMIN
                db.session.commit()
                print(f"Role updated to SUPER_ADMIN successfully!\n")
            else:
                print(f"Role is already SUPER_ADMIN ✓\n")
        else:
            print("Account admin@aldudu.com not found!\n")

if __name__ == "__main__":
    check_admin()
