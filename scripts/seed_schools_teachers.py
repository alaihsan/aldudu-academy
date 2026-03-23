"""
Seed Script - Create 10 Schools with 10 Teachers Each
All users will have password: 123456
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models import School, SchoolStatus, User, UserRole, AcademicYear
from datetime import datetime

# School data templates
SCHOOLS_DATA = [
    {"name": "SMA Negeri 1 Jakarta", "slug": "sman1-jakarta", "email": "info@sman1jakarta.sch.id"},
    {"name": "SMA Negeri 2 Bandung", "slug": "sman2-bandung", "email": "info@sman2bandung.sch.id"},
    {"name": "SMA Negeri 3 Surabaya", "slug": "sman3-surabaya", "email": "info@sman3surabaya.sch.id"},
    {"name": "SMA Negeri 4 Yogyakarta", "slug": "sman4-yogya", "email": "info@sman4yogya.sch.id"},
    {"name": "SMA Negeri 5 Semarang", "slug": "sman5-semarang", "email": "info@sman5semarang.sch.id"},
    {"name": "SMA Negeri 6 Medan", "slug": "sman6-medan", "email": "info@sman6medan.sch.id"},
    {"name": "SMA Negeri 7 Makassar", "slug": "sman7-makassar", "email": "info@sman7makassar.sch.id"},
    {"name": "SMA Negeri 8 Palembang", "slug": "sman8-palembang", "email": "info@sman8palembang.sch.id"},
    {"name": "SMA Negeri 9 Denpasar", "slug": "sman9-denpasar", "email": "info@sman9denpasar.sch.id"},
    {"name": "SMA Negeri 10 Balikpapan", "slug": "sman10-balikpapan", "email": "info@sman10balikpapan.sch.id"},
]

# Teacher name templates (expanded to 100 names)
TEACHER_NAMES = [
    "Ahmad Fauzi", "Budi Santoso", "Citra Dewi", "Dewi Lestari", "Eko Prasetyo",
    "Fitri Handayani", "Gunawan Wijaya", "Hana Pertiwi", "Indra Kusuma", "Joko Widodo",
    "Kartini Sari", "Lukman Hakim", "Maya Putri", "Nurul Hidayah", "Omar Abdullah",
    "Putri Anggraini", "Qori Azzahra", "Rudi Hartono", "Siti Nurhaliza", "Taufik Hidayat",
    "Umar Faruq", "Vina Amelia", "Wawan Setiawan", "Xena Patricia", "Yusuf Ibrahim",
    "Zainab Alatas", "Andi Saputra", "Bella Saphira", "Candra Wijaya", "Diana Kusuma",
    "Eka Putri", "Farhan Maulana", "Gita Permata", "Hendra Gunawan", "Ika Sari",
    "Joko Susilo", "Kirana Putri", "Leo Pratama", "Mega Dewi", "Nanda Putra",
    "Olivia Tan", "Putra Sejati", "Qamaruddin", "Rina Susanti", "Syahrul Ramadhan",
    "Tari Kusuma", "Usman Harun", "Vina Panduwinata", "Wahyu Hidayat", "Yulia Rachman",
    "Zainal Abidin", "Arif Rahman", "Bambang Pamungkas", "Citra Lestari", "Doni Pratama",
    "Erna Sari", "Fajar Nugroho", "Gita Gutawa", "Harris Alatas", "Indah Permata",
    "Joko Anwar", "Kiki Fatmawati", "Lukman Sardi", "Maya Hasan", "Nizar Kurniawan",
    "Opick Ramadhan", "Putri Titian", "Qory Sandioriva", "Raffi Ahmad", "Sherina Munaf",
    "Titi Kamal", "Umar Syihab", "Vicky Prasetyo", "Wulan Guritno", "Xabiru Sandora",
    "Yovie Widianto", "Zaskia Gotik", "Arie Untung", "Bunga Citra", "Dewa Budjana",
    "Ebiet Gade", "Fiersa Besari", "Glenn Fredly", "Iwan Fals", "Judika Sihite",
    "Kahitna Band", "Letto Band", "Mahalini Raharja", "Noah Band", "Oddie Agam",
    "Peterpan", "Queen Band", "Radja Band", "Sheila On 7", "Tulus",
    "Ungu Band", "Virgoun Band", "Wali Band", "Yovie Nuno", "Zivilia Band",
    "Adi Bing Slamet", "Bella Saphira", "Coki Pardede", "Dinda Hauw", "Edo Kondologit",
    "Fani Rahmawati", "Gading Marten", "Hanna Alatas", "Iqbal Ali", "Jessica Iskandar",
    "Kenzo Wijaya", "Luna Maya", "Miko Lee", "Nayla Denny", "Oscar Mahendra",
    "Putri Uno", "Qalbi Qolbu", "Rizky Billar", "Salsa Billa", "Teuku Ryan",
]

DEFAULT_PASSWORD = "123456"
DEFAULT_EMAIL_DOMAIN = "teacher@{school_slug}.sch.id"


def create_schools_and_teachers():
    """Create 10 schools with 10 teachers each"""
    
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("🏫 SEEDING SCHOOLS AND TEACHERS")
        print("=" * 60)
        
        # Check if schools already exist
        existing_schools = School.query.count()
        if existing_schools > 0:
            print(f"\n⚠️  Found {existing_schools} existing school(s)")
            print("✅ Skipping - schools already exist")
            print("\n📊 Existing Schools:")
            for school in School.query.all():
                teacher_count = User.query.filter_by(school_id=school.id, role=UserRole.GURU).count()
                print(f"   • {school.name}: {teacher_count} teachers")
            return
        
        created_schools = []
        created_teachers = 0
        
        for i, school_data in enumerate(SCHOOLS_DATA, 1):
            print(f"\n📌 Creating School {i}/10: {school_data['name']}")
            
            # Create School
            school = School(
                name=school_data['name'],
                slug=school_data['slug'],
                email=school_data['email'],
                admin_email=f"admin@{school_data['slug']}.sch.id",
                status=SchoolStatus.ACTIVE,
                approved_at=datetime.now(),
            )
            db.session.add(school)
            db.session.flush()  # Get school ID
            
            print(f"   ✅ School created (ID: {school.id})")
            created_schools.append(school)
            
            # Create 10 Teachers for this school
            for j in range(10):
                teacher_name = TEACHER_NAMES[(i - 1) * 10 + j]
                teacher_email = DEFAULT_EMAIL_DOMAIN.format(school_slug=school_data['slug'].replace(' ', '-'))
                # Make email unique per teacher
                teacher_email = f"guru{i}.{j+1}@{school_data['slug']}.sch.id"
                
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
                created_teachers += 1
            
            print(f"   ✅ Created 10 teachers")
            
            # Create Academic Year for this school
            academic_year = AcademicYear(
                year="2025/2026",
                is_active=True,
                school_id=school.id,
            )
            db.session.add(academic_year)
            print(f"   ✅ Created academic year 2025/2026")
            
            # Commit after each school to avoid memory issues
            db.session.commit()
        
        print("\n" + "=" * 60)
        print("✅ SEEDING COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"\n📊 Summary:")
        print(f"   • Schools created: {len(created_schools)}")
        print(f"   • Teachers created: {created_teachers}")
        print(f"   • Default password: {DEFAULT_PASSWORD}")
        print(f"\n📝 Login Format:")
        print(f"   • Email: guru{school_num}.[1-10]@[school-slug].sch.id")
        print(f"   • Password: {DEFAULT_PASSWORD}")
        print(f"\n📋 Example Login Credentials:")
        for i, school in enumerate(created_schools[:3], 1):  # Show first 3 as examples
            print(f"\n   {school.name}:")
            print(f"   • Email: guru{i}.1@{school.slug}.sch.id")
            print(f"   • Password: {DEFAULT_PASSWORD}")
        
        print("\n" + "=" * 60)


if __name__ == "__main__":
    create_schools_and_teachers()
