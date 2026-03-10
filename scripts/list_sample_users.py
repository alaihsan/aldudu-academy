import os
import sys

# Ensure we can import from the root
sys.path.append(os.getcwd())

from app import create_app
from app.models import db, User, UserRole

def list_users():
    app = create_app()
    with app.app_context():
        print("Super Admin Accounts:")
        admins = User.query.filter_by(role=UserRole.ADMIN).limit(3).all()
        for admin in admins:
            print(f"- Name: {admin.name}, Email: {admin.email}")

        print("\nGuru Accounts:")
        gurus = User.query.filter_by(role=UserRole.GURU).limit(3).all()
        for guru in gurus:
            print(f"- Name: {guru.name}, Email: {guru.email}")

        print("\nMurid Accounts:")
        murids = User.query.filter_by(role=UserRole.MURID).limit(3).all()
        for murid in murids:
            print(f"- Name: {murid.name}, Email: {murid.email}")

if __name__ == "__main__":
    list_users()
