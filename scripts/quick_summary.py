"""Quick summary of all users"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import User, UserRole, School

app = create_app()

with app.app_context():
    schools = School.query.all()
    
    print("\n" + "=" * 80)
    print("📊 GRAND TOTAL USERS SUMMARY")
    print("=" * 80)
    
    total_teachers = 0
    total_students = 0
    total_admins = 0
    
    for school in schools:
        teachers = User.query.filter_by(school_id=school.id, role=UserRole.GURU).count()
        students = User.query.filter_by(school_id=school.id, role=UserRole.MURID).count()
        admins = User.query.filter_by(school_id=school.id, role=UserRole.ADMIN).count()
        
        total_teachers += teachers
        total_students += students
        total_admins += admins
        
        print(f"\n{school.name}:")
        print(f"   👨‍🏫 Teachers: {teachers}")
        print(f"   👨‍🎓 Students: {students}")
        print(f"   👤 Admins: {admins}")
    
    print("\n" + "=" * 80)
    print(f"👨‍🏫 TOTAL TEACHERS: {total_teachers}")
    print(f"👨‍🎓 TOTAL STUDENTS: {total_students}")
    print(f"👤 TOTAL ADMINS: {total_admins}")
    print(f"📈 GRAND TOTAL: {total_teachers + total_students + total_admins} users")
    print("=" * 80 + "\n")
