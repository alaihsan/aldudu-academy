"""
Fast Seed Script - Add 144 Students to Each School using Bulk Insert
All students will have password: 123456
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models import School, SchoolStatus, User, UserRole, AcademicYear
from werkzeug.security import generate_password_hash
from datetime import datetime

DEFAULT_PASSWORD = "123456"
STUDENTS_PER_SCHOOL = 144

# Generate password hash once
password_hash = generate_password_hash(DEFAULT_PASSWORD, method='pbkdf2:sha256')


def generate_student_name(index):
    """Generate unique student name"""
    first_names = [
        "Ahmad", "Budi", "Citra", "Dewi", "Eko", "Fitri", "Gunawan", "Hana", "Indra", "Joko",
        "Kartini", "Lukman", "Maya", "Nurul", "Omar", "Putri", "Qori", "Rudi", "Siti", "Taufik",
        "Umar", "Vina", "Wawan", "Xena", "Yusuf", "Zainab", "Andi", "Bella", "Candra", "Diana",
        "Erwin", "Farah", "Galih", "Hesti", "Irfan", "Jihan", "Kevin", "Lina", "Muhammad", "Nadia",
        "Opick", "Putra", "Qomar", "Rina", "Syahrin", "Tomi", "Ussy", "Vicky", "Wendi", "Yuni",
    ]
    last_names = [
        "Pratama", "Santoso", "Wijaya", "Kusuma", "Putra", "Sari", "Dewi", "Lestari", "Handayani", "Nugroho",
        "Setiawan", "Hidayat", "Rahman", "Fauzi", "Saputra", "Aulia", "Ramadhan", "Siregar", "Nasution", "Harahap",
    ]
    first_name = first_names[index % len(first_names)]
    last_name = last_names[(index // len(first_names)) % len(last_names)]
    return f"{first_name} {last_name}"


def add_students_fast():
    """Add 144 students to each school using bulk insert"""
    
    app = create_app()
    
    with app.app_context():
        print("=" * 80)
        print("👨‍🎓 FAST SEEDING - 144 STUDENTS PER SCHOOL")
        print("=" * 80)
        
        schools = School.query.filter_by(status=SchoolStatus.ACTIVE).all()
        
        if not schools:
            print("\n❌ No active schools found!")
            return
        
        print(f"\n📊 Found {len(schools)} schools")
        print(f"📝 Target: {STUDENTS_PER_SCHOOL} students per school")
        
        total_added = 0
        
        for i, school in enumerate(schools, 1):
            print(f"\n[{i}/{len(schools)}] {school.name}...")
            
            # Check existing
            existing = User.query.filter_by(
                school_id=school.id,
                role=UserRole.MURID
            ).count()
            
            if existing >= STUDENTS_PER_SCHOOL:
                print(f"   ✅ Already has {existing} students")
                continue
            
            # Create student records
            students_data = []
            for j in range(STUDENTS_PER_SCHOOL - existing):
                student_num = existing + j + 1
                name = generate_student_name((i - 1) * STUDENTS_PER_SCHOOL + j)
                email = f"murid{i}.{student_num}@{school.slug}.sch.id"
                
                students_data.append({
                    'name': name,
                    'email': email,
                    'password_hash': password_hash,
                    'role': 'murid',
                    'school_id': school.id,
                    'is_active': True,
                    'email_verified': True,
                })
            
            # Bulk insert using raw SQL
            if students_data:
                db.session.execute(
                    User.__table__.insert(),
                    students_data
                )
                db.session.commit()
                print(f"   ✅ Added {len(students_data)} students")
                total_added += len(students_data)
        
        print("\n" + "=" * 80)
        print(f"✅ COMPLETED! Total students added: {total_added}")
        print("=" * 80)
        
        # Show summary
        print("\n📊 FINAL SUMMARY:")
        for i, school in enumerate(schools, 1):
            count = User.query.filter_by(
                school_id=school.id,
                role=UserRole.MURID
            ).count()
            print(f"   {school.name}: {count} students")
        
        print("\n🔑 Login: murid[school_num].[1-144]@[school_slug].sch.id / 123456")
        print("=" * 80 + "\n")


if __name__ == "__main__":
    add_students_fast()
