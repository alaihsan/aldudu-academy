"""
Debug script to check teacher courses
"""
import os
os.environ['DATABASE_URL'] = 'mysql+pymysql://root:passwd@localhost:3306/aldudu_academy'

from app import create_app
from app.models import db, User, Course, AcademicYear, UserRole
from app.helpers import get_courses_for_user

app = create_app()

with app.app_context():
    print("=" * 60)
    print("CHECKING TEACHER COURSES")
    print("=" * 60)
    
    # 1. Check all users
    print("\n1. ALL USERS:")
    users = User.query.all()
    print(f"   Total users: {len(users)}")
    for u in users:
        print(f"   - ID:{u.id} {u.name} ({u.email}) - Role: {u.role.value}, School: {u.school_id}")
    
    # 2. Check teachers specifically
    print("\n2. TEACHERS (role=GURU):")
    teachers = User.query.filter(User.role == UserRole.GURU).all()
    print(f"   Total teachers: {len(teachers)}")
    for t in teachers:
        print(f"   - ID:{t.id} {t.name} - School: {t.school_id}")
        
        # Check courses for this teacher
        courses = Course.query.filter_by(teacher_id=t.id).all()
        print(f"     Courses (all): {len(courses)}")
        for c in courses:
            print(f"       - {c.name} (Year ID: {c.academic_year_id})")
    
    # 3. Check academic years
    print("\n3. ACADEMIC YEARS:")
    years = AcademicYear.query.all()
    print(f"   Total years: {len(years)}")
    for y in years:
        print(f"   - ID:{y.id} Year: {y.year}, School: {y.school_id}, Active: {y.is_active}")
    
    # 5. Test with year_id=-1 (all courses for teachers)
    print("\n5. TESTING get_courses_for_user() with year_id=-1 (ALL COURSES):")
    for t in teachers:
        if t.id == 34:  # Only test ichsan
            print(f"   Teacher {t.name} (year_id=-1):")
            courses = get_courses_for_user(t, -1)
            print(f"     -> Returns {len(courses)} courses")
            for c in courses:
                print(f"        - {c.name} (Year ID: {c.academic_year_id})")
