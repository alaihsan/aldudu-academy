"""
Quick seed demo users for testing
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import create_app, db
from app.models import User, UserRole, School, Course, AcademicYear
from datetime import datetime

app = create_app()

with app.app_context():
    print("=" * 60)
    print("🌱 SEEDING DEMO USERS")
    print("=" * 60)
    
    # Get first school
    school = School.query.first()
    if not school:
        print("❌ No school found. Run seed_schools_teachers.py first!")
        sys.exit(1)
    
    print(f"\n🏫 Using school: {school.name}")
    
    # Create demo teacher
    teacher_email = f"guru@{school.slug}.sch.id"
    teacher = User.query.filter_by(email=teacher_email).first()
    if not teacher:
        teacher = User(
            name='Guru Demo',
            email=teacher_email,
            role=UserRole.GURU,
            school_id=school.id,
            is_active=True,
            email_verified=True
        )
        teacher.set_password('123')
        db.session.add(teacher)
        db.session.commit()
        print(f'✅ Created teacher: {teacher_email} / 123')
    else:
        print(f'✓ Teacher exists: {teacher_email} / 123')
    
    # Create demo student
    student_email = f"murid@{school.slug}.sch.id"
    student = User.query.filter_by(email=student_email).first()
    if not student:
        student = User(
            name='Murid Demo',
            email=student_email,
            role=UserRole.MURID,
            school_id=school.id,
            is_active=True,
            email_verified=True
        )
        student.set_password('123')
        db.session.add(student)
        db.session.commit()
        print(f'✅ Created student: {student_email} / 123')
    else:
        print(f'✓ Student exists: {student_email} / 123')
    
    # Create admin if not exists
    admin_email = "admin@aldudu.com"
    admin = User.query.filter_by(email=admin_email).first()
    if not admin:
        admin = User(
            name='Super Admin',
            email=admin_email,
            role=UserRole.ADMIN,
            is_active=True,
            email_verified=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print(f'✅ Created admin: {admin_email} / admin123')
    else:
        print(f'✓ Admin exists: {admin_email} / admin123')
    
    # Create demo course
    course = Course.query.filter_by(teacher_id=teacher.id).first()
    if not course:
        # Get academic year
        academic_year = AcademicYear.query.filter_by(year=str(datetime.now().year), is_active=True).first()
        if not academic_year:
            academic_year = AcademicYear(
                year=str(datetime.now().year),
                is_active=True,
                school_id=school.id
            )
            db.session.add(academic_year)
            db.session.flush()
        
        course = Course(
            name='Matematika X',
            class_code='MTK-X-01',
            teacher_id=teacher.id,
            academic_year_id=academic_year.id
        )
        db.session.add(course)
        db.session.commit()
        
        # Enroll student
        course.students.append(student)
        db.session.commit()
        
        print(f'✅ Created course: {course.name} (Code: {course.class_code})')
        print(f'✅ Student enrolled in course')
    else:
        print(f'✓ Course exists: {course.name}')
    
    print('\n' + '=' * 60)
    print('🎉 SEED COMPLETED!')
    print('=' * 60)
    print('\n📋 LOGIN CREDENTIALS:')
    print(f'  👨‍🏫 Teacher: {teacher_email} / 123')
    print(f'  👨‍🎓 Student: {student_email} / 123')
    print(f'  🔧 Admin:    {admin_email} / admin123')
    print('\n📚 Course: Matematika X (Code: MATH-X-001)')
    print('=' * 60)
