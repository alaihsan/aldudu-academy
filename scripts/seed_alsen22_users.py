"""
Seed users for alsen22 school
Creates:
- 1 Super Admin
- 1 Admin for alsen22
- 1 Guru for alsen22
- 2 Murid for alsen22

Default password: passwd
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import create_app, db
from app.models import User, UserRole, School, SchoolStatus

app = create_app()

DEFAULT_PASSWORD = 'passwd'

with app.app_context():
    # Create or get school alsen22
    school = School.query.filter_by(slug='alsen22').first()
    if not school:
        school = School(
            name='alsen22',
            slug='alsen22',
            email='info@alsen22.sch.id',
            admin_email='admin@alsen22.sch.id',
            status=SchoolStatus.ACTIVE
        )
        db.session.add(school)
        db.session.commit()
        print(f'✅ Created school: alsen22 (id={school.id})')
    else:
        print(f'✓ School alsen22 exists (id={school.id})')

    # 1. Create Super Admin (not tied to any school)
    super_admin = User.query.filter_by(email='superadmin@aldudu.com').first()
    if not super_admin:
        super_admin = User(
            name='Super Admin',
            email='superadmin@aldudu.com',
            role=UserRole.SUPER_ADMIN,
            is_active=True,
            email_verified=True,
            school_id=None
        )
        super_admin.set_password(DEFAULT_PASSWORD)
        db.session.add(super_admin)
        print(f'✅ Created Super Admin: superadmin@aldudu.com / {DEFAULT_PASSWORD}')
    else:
        print(f'✓ Super Admin exists: superadmin@aldudu.com / {DEFAULT_PASSWORD}')

    # 2. Create Admin for alsen22
    admin = User.query.filter_by(email='admin@alsen22.sch.id').first()
    if not admin:
        admin = User(
            name='Admin alsen22',
            email='admin@alsen22.sch.id',
            role=UserRole.ADMIN,
            is_active=True,
            email_verified=True,
            school_id=school.id
        )
        admin.set_password(DEFAULT_PASSWORD)
        db.session.add(admin)
        print(f'✅ Created Admin: admin@alsen22.sch.id / {DEFAULT_PASSWORD}')
    else:
        print(f'✓ Admin exists: admin@alsen22.sch.id / {DEFAULT_PASSWORD}')

    # 3. Create Guru for alsen22
    guru = User.query.filter_by(email='guru@alsen22.sch.id').first()
    if not guru:
        guru = User(
            name='Guru alsen22',
            email='guru@alsen22.sch.id',
            role=UserRole.GURU,
            is_active=True,
            email_verified=True,
            school_id=school.id
        )
        guru.set_password(DEFAULT_PASSWORD)
        db.session.add(guru)
        print(f'✅ Created Guru: guru@alsen22.sch.id / {DEFAULT_PASSWORD}')
    else:
        print(f'✓ Guru exists: guru@alsen22.sch.id / {DEFAULT_PASSWORD}')

    # 4. Create 2 Murid for alsen22
    murid1 = User.query.filter_by(email='murid1@alsen22.sch.id').first()
    if not murid1:
        murid1 = User(
            name='Murid 1 alsen22',
            email='murid1@alsen22.sch.id',
            role=UserRole.MURID,
            is_active=True,
            email_verified=True,
            school_id=school.id
        )
        murid1.set_password(DEFAULT_PASSWORD)
        db.session.add(murid1)
        print(f'✅ Created Murid 1: murid1@alsen22.sch.id / {DEFAULT_PASSWORD}')
    else:
        print(f'✓ Murid 1 exists: murid1@alsen22.sch.id / {DEFAULT_PASSWORD}')

    murid2 = User.query.filter_by(email='murid2@alsen22.sch.id').first()
    if not murid2:
        murid2 = User(
            name='Murid 2 alsen22',
            email='murid2@alsen22.sch.id',
            role=UserRole.MURID,
            is_active=True,
            email_verified=True,
            school_id=school.id
        )
        murid2.set_password(DEFAULT_PASSWORD)
        db.session.add(murid2)
        print(f'✅ Created Murid 2: murid2@alsen22.sch.id / {DEFAULT_PASSWORD}')
    else:
        print(f'✓ Murid 2 exists: murid2@alsen22.sch.id / {DEFAULT_PASSWORD}')

    db.session.commit()
    
    print('\n🎉 Seed completed!')
    print('\nLogin credentials:')
    print(f'  Super Admin: superadmin@aldudu.com / {DEFAULT_PASSWORD}')
    print(f'  Admin: admin@alsen22.sch.id / {DEFAULT_PASSWORD}')
    print(f'  Guru: guru@alsen22.sch.id / {DEFAULT_PASSWORD}')
    print(f'  Murid 1: murid1@alsen22.sch.id / {DEFAULT_PASSWORD}')
    print(f'  Murid 2: murid2@alsen22.sch.id / {DEFAULT_PASSWORD}')
