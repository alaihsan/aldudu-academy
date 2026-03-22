import os
import sys

# Ensure we can import from the root
sys.path.append(os.getcwd())

from app import create_app
from app.models import db, User

def fix_admin_verification():
    app = create_app()
    with app.app_context():
        # Find all admin/superadmin users
        admins = User.query.filter(User.role.in_(['admin', 'super_admin'])).all()
        
        print(f"\n{'='*60}")
        print(f"List of Admin Accounts ({len(admins)} total)")
        print(f"{'='*60}")
        
        for i, admin in enumerate(admins, 1):
            was_unverified = not admin.email_verified
            if was_unverified:
                admin.email_verified = True
            status = "✓ Fixed" if was_unverified else "✓ Already verified"
            print(f"{i}. {admin.email} - {admin.role.value} - {status}")
        
        db.session.commit()
        print(f"{'='*60}\n")

if __name__ == "__main__":
    fix_admin_verification()
