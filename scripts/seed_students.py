"""
Seed Script - Add 144 Students to Each School
All students will have password: 123456
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models import School, SchoolStatus, User, UserRole, AcademicYear
from datetime import datetime

# Student name patterns
STUDENT_FIRST_NAMES = [
    "Ahmad", "Budi", "Citra", "Dewi", "Eko", "Fitri", "Gunawan", "Hana", "Indra", "Joko",
    "Kartini", "Lukman", "Maya", "Nurul", "Omar", "Putri", "Qori", "Rudi", "Siti", "Taufik",
    "Umar", "Vina", "Wawan", "Xena", "Yusuf", "Zainab", "Andi", "Bella", "Candra", "Diana",
    "Erwin", "Farah", "Galih", "Hesti", "Irfan", "Jihan", "Kevin", "Lina", "Muhammad", "Nadia",
    "Opick", "Putra", "Qomar", "Rina", "Syahrin", "Tomi", "Ussy", "Vicky", "Wendi", "Yuni",
    "Zaskia", "Arie", "Bayu", "Chelsea", "Dimas", "Elly", "Fajar", "Gita", "Harris", "Isyana",
    "Jefri", "Kris", "Lyodra", "Marion", "Niki", "Oka", "Prilly", "Qiandra", "Raffi", "Sherina",
    "Tiara", "Ulta", "Via", "Wika", "Xabiru", "Yura", "Ziva", "Afgan", "Bunga", "Dewa",
    "Ebiet", "Fiersa", "Glenn", "Iwan", "Judika", "Kahitna", "Letto", "Mahalini", "Noah", "Oddie",
    "Peter", "Queen", "Radja", "Sheila", "Tulus", "Ungu", "Virgoun", "Wali", "Yovie", "Zivilia",
    "Adi", "Bella", "Coki", "Dinda", "Edo", "Fani", "Gading", "Hanna", "Iqbal", "Jessica",
    "Kenzo", "Luna", "Miko", "Nayla", "Oscar", "Putra", "Qalbi", "Rizky", "Salsa", "Teuku",
]

STUDENT_LAST_NAMES = [
    "Pratama", "Santoso", "Wijaya", "Kusuma", "Putra", "Sari", "Dewi", "Lestari", "Handayani", "Nugroho",
    "Setiawan", "Hidayat", "Rahman", "Fauzi", "Saputra", "Aulia", "Ramadhan", "Siregar", "Nasution", "Harahap",
]

DEFAULT_PASSWORD = "123456"
STUDENTS_PER_SCHOOL = 144


def generate_student_name(index):
    """Generate unique student name"""
    first_name = STUDENT_FIRST_NAMES[index % len(STUDENT_FIRST_NAMES)]
    last_name = STUDENT_LAST_NAMES[(index // len(STUDENT_FIRST_NAMES)) % len(STUDENT_LAST_NAMES)]
    return f"{first_name} {last_name}"


def add_students_to_schools():
    """Add 144 students to each existing school"""
    
    app = create_app()
    
    with app.app_context():
        print("=" * 80)
        print("👨‍🎓 SEEDING STUDENTS TO SCHOOLS")
        print("=" * 80)
        
        # Get all active schools
        schools = School.query.filter_by(status=SchoolStatus.ACTIVE).all()
        
        if not schools:
            print("\n❌ No active schools found!")
            return
        
        print(f"\n📊 Found {len(schools)} active school(s)")
        print(f"📝 Target: {STUDENTS_PER_SCHOOL} students per school")
        print(f"📈 Total students to create: {len(schools) * STUDENTS_PER_SCHOOL}")
        
        total_students_added = 0
        
        for i, school in enumerate(schools, 1):
            print(f"\n{'='*80}")
            print(f"📌 School {i}/{len(schools)}: {school.name}")
            print(f"{'='*80}")
            
            # Check existing students
            existing_students = User.query.filter_by(
                school_id=school.id,
                role=UserRole.MURID
            ).count()
            
            if existing_students >= STUDENTS_PER_SCHOOL:
                print(f"   ⏭️  Already has {existing_students} students, skipping...")
                continue
            
            # Calculate how many students to add
            students_to_add = STUDENTS_PER_SCHOOL - existing_students
            print(f"   📝 Adding {students_to_add} students...")
            print(f"   📊 Current: {existing_students}, Target: {STUDENTS_PER_SCHOOL}")
            
            # Get starting index for this school
            name_start_index = (i - 1) * STUDENTS_PER_SCHOOL
            
            # Add students in larger batches for better performance
            students_to_create = []
            
            for j in range(students_to_add):
                student_name = generate_student_name(name_start_index + j)
                student_email = f"murid{i}.{j+1}@{school.slug}.sch.id"
                
                # Check if email already exists
                existing_user = User.query.filter_by(email=student_email).first()
                if not existing_user:
                    student = User(
                        name=student_name,
                        email=student_email,
                        role=UserRole.MURID,
                        school_id=school.id,
                        is_active=True,
                        email_verified=True,
                    )
                    student.set_password(DEFAULT_PASSWORD)
                    students_to_create.append(student)
            
            # Add all students at once
            db.session.add_all(students_to_create)
            db.session.commit()
            
            print(f"   ✅ Added {len(students_to_create)} students")
            
            total_students_added += students_to_add
            final_count = User.query.filter_by(
                school_id=school.id,
                role=UserRole.MURID
            ).count()
            print(f"   ✅ Completed! Total students: {final_count}/{STUDENTS_PER_SCHOOL}")
        
        print("\n" + "=" * 80)
        print("✅ SEEDING COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print(f"\n📊 Summary:")
        print(f"   • Schools processed: {len(schools)}")
        print(f"   • Students added: {total_students_added}")
        print(f"   • Students per school: {STUDENTS_PER_SCHOOL}")
        print(f"   • Default password: {DEFAULT_PASSWORD}")
        
        print(f"\n📋 Login Credentials:")
        for i, school in enumerate(schools, 1):
            student_count = User.query.filter_by(
                school_id=school.id,
                role=UserRole.MURID
            ).count()
            print(f"\n   {school.name}:")
            print(f"   • Total students: {student_count}")
            print(f"   • Email format: murid{i}.[1-{STUDENTS_PER_SCHOOL}]@{school.slug}.sch.id")
            print(f"   • Example: murid{i}.1@{school.slug}.sch.id")
            print(f"   • Password: {DEFAULT_PASSWORD}")
        
        print("\n" + "=" * 80)


if __name__ == "__main__":
    add_students_to_schools()
