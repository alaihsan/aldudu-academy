"""
Seed demo users untuk development
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import create_app, db
from app.models import User, UserRole

app = create_app()

with app.app_context():
    # Create teacher
    teacher = User.query.filter_by(email='guru@aldudu.com').first()
    if not teacher:
        teacher = User(
            name='Guru Demo',
            email='guru@aldudu.com',
            role=UserRole.GURU,
            is_active=True,
            email_verified=True
        )
        teacher.set_password('123')
        db.session.add(teacher)
        print('✅ Created teacher: guru@aldudu.com / 123')
    else:
        print('✓ Teacher already exists: guru@aldudu.com / 123')
    
    # Create student
    student = User.query.filter_by(email='murid@aldudu.com').first()
    if not student:
        student = User(
            name='Murid Demo',
            email='murid@aldudu.com',
            role=UserRole.MURID,
            is_active=True,
            email_verified=True
        )
        student.set_password('123')
        db.session.add(student)
        print('✅ Created student: murid@aldudu.com / 123')
    else:
        print('✓ Student already exists: murid@aldudu.com / 123')
    
    db.session.commit()
    print('\n🎉 Seed completed!')
    print('\nLogin credentials:')
    print('  Teacher: guru@aldudu.com / 123')
    print('  Student: murid@aldudu.com / 123')
