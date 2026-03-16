"""
Seed Script - Add 10 Teachers to Each Existing School
All users will have password: 123456
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models import School, SchoolStatus, User, UserRole, AcademicYear
from datetime import datetime

# Teacher name templates (enough for 10 schools x 10 teachers = 100 teachers)
TEACHER_NAMES = [
    "Ahmad Fauzi", "Budi Santoso", "Citra Dewi", "Dewi Lestari", "Eko Prasetyo",
    "Fitri Handayani", "Gunawan Wijaya", "Hana Pertiwi", "Indra Kusuma", "Joko Widodo",
    "Kartini Sari", "Lukman Hakim", "Maya Putri", "Nurul Hidayah", "Omar Abdullah",
    "Putri Anggraini", "Qori Azzahra", "Rudi Hartono", "Siti Nurhaliza", "Taufik Hidayat",
    "Umar Faruq", "Vina Amelia", "Wawan Setiawan", "Xena Patricia", "Yusuf Ibrahim",
    "Zainab Alatas", "Andi Saputra", "Bella Saphira", "Candra Wijaya", "Diana Kusuma",
    "Erwin Kurniawan", "Farah Quinn", "Galih Pamungkas", "Hesti Purwadinata", "Irfan Hakim",
    "Jihan Mulyani", "Kevin Sanjaya", "Lina Marlina", "Muhammad Rizky", "Nadia Safitri",
    "Opick Ramadhan", "Putri Tanjung", "Qomaruddin", "Rina Nose", "Syahrini",
    "Tomi Samekto", "Ussy Sulistiawaty", "Vicky Prasetyo", "Wendy Walters", "Yuni Shara",
    "Zaskia Gotik", "Arie Untung", "Bayu Skak", "Chelsea Olivia", "Dimas Anggara",
    "Elly Sugigi", "Fajar Alfian", "Gita Gutawa", "Harris Vriza", "Isyana Sarasvati",
    "Jefri Nichol", "Krisdayanti", "Lyodra Ginting", "Marion Jola", "Niki Zefanya",
    "Oka Antara", "Prilly Latuconsina", "Qiandra Razak", "Raffi Ahmad", "Sherina Munaf",
    "Tiara Andini", "Ulta Berlian", "Via Vallen", "Wika Salim", "Xabiru",
    "Yura Yunita", "Ziva Magnolya", "Afgan Syahreza", "Bunga Citra Lestari", "Dewa 19",
    "Ebiet G Ade", "Fiersa Besari", "Glenn Fredly", "Iwan Fals", "Judika",
    "Kahitna", "Letto", "Mahalini", "Noah Band", "Oddie Agam",
    "Peterpan", "Queen", "Radja", "Sheila On 7", "Tulus",
    "Ungu", "Virgoun", "Wali Band", "Yovie Nuno", "Zivilia",
]

DEFAULT_PASSWORD = "123456"


def add_teachers_to_schools():
    """Add 10 teachers to each existing school"""
    
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("👨‍🏫 SEEDING TEACHERS TO EXISTING SCHOOLS")
        print("=" * 60)
        
        # Get all active schools
        schools = School.query.filter_by(status=SchoolStatus.ACTIVE).all()
        
        if not schools:
            print("\n❌ No active schools found!")
            print("Please create schools first or run seed_schools_teachers.py")
            return
        
        print(f"\n📊 Found {len(schools)} active school(s)")
        
        total_teachers_added = 0
        
        for i, school in enumerate(schools, 1):
            print(f"\n📌 Processing School {i}/{len(schools)}: {school.name}")
            
            # Check existing teachers
            existing_teachers = User.query.filter_by(
                school_id=school.id,
                role=UserRole.GURU
            ).count()
            
            if existing_teachers >= 10:
                print(f"   ⏭️  Already has {existing_teachers} teachers, skipping...")
                continue
            
            # Calculate how many teachers to add
            teachers_to_add = 10 - existing_teachers
            print(f"   📝 Adding {teachers_to_add} teachers...")
            
            # Use modulo to cycle through names if needed
            name_start_index = (i - 1) * 10
            
            for j in range(teachers_to_add):
                teacher_name = TEACHER_NAMES[(name_start_index + j) % len(TEACHER_NAMES)]
                teacher_email = f"guru{i}.{j+1}@{school.slug}.sch.id"
                
                # Check if email already exists
                existing_user = User.query.filter_by(email=teacher_email).first()
                if existing_user:
                    print(f"   ⚠️  Teacher {teacher_email} already exists, skipping...")
                    continue
                
                teacher = User(
                    name=teacher_name,
                    email=teacher_email,
                    role=UserRole.GURU,
                    school_id=school.id,
                    is_active=True,
                    email_verified=True,
                )
                teacher.set_password(DEFAULT_PASSWORD)
                db.session.add(teacher)
                
                # Ensure academic year exists
                academic_year = AcademicYear.query.filter_by(
                    year="2025/2026",
                    school_id=school.id
                ).first()
                if not academic_year:
                    academic_year = AcademicYear(
                        year="2025/2026",
                        is_active=True,
                        school_id=school.id,
                    )
                    db.session.add(academic_year)
            
            db.session.commit()
            total_teachers_added += teachers_to_add
            print(f"   ✅ Added {teachers_to_add} teachers")
        
        print("\n" + "=" * 60)
        print("✅ SEEDING COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"\n📊 Summary:")
        print(f"   • Schools processed: {len(schools)}")
        print(f"   • Teachers added: {total_teachers_added}")
        print(f"   • Default password: {DEFAULT_PASSWORD}")
        
        print(f"\n📋 Login Credentials:")
        for i, school in enumerate(schools, 1):
            teacher_count = User.query.filter_by(
                school_id=school.id,
                role=UserRole.GURU
            ).count()
            print(f"\n   {school.name}:")
            print(f"   • Total teachers: {teacher_count}")
            print(f"   • Email format: guru{i}.[1-10]@{school.slug}.sch.id")
            print(f"   • Example: guru{i}.1@{school.slug}.sch.id")
            print(f"   • Password: {DEFAULT_PASSWORD}")
        
        print("\n" + "=" * 60)


if __name__ == "__main__":
    add_teachers_to_schools()
