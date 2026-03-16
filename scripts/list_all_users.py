"""
List All Users in Table Format
Shows complete user information for all schools
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import User, UserRole, School

app = create_app()

with app.app_context():
    print("\n" + "=" * 150)
    print("📋 DAFTAR LENGKAP SEMUA USER DI SISTEM")
    print("=" * 150)
    
    # Get all schools
    schools = School.query.order_by(School.name).all()
    
    total_users = 0
    total_teachers = 0
    total_students = 0
    total_admins = 0
    
    for school in schools:
        print(f"\n{'='*150}")
        print(f"🏫 {school.name.upper()}")
        print(f"   Slug: {school.slug} | Status: {school.status.value.upper()}")
        print(f"{'='*150}")
        
        # Get all users for this school
        users = User.query.filter_by(school_id=school.id).order_by(User.role, User.name).all()
        
        if not users:
            print("   ⚠️  Tidak ada user di sekolah ini")
            continue
        
        # Print table header
        print(f"\n{'No':<4} {'Nama':<30} {'Email':<45} {'Role':<12} {'Status':<10} {'Verified':<10}")
        print("-" * 150)
        
        school_teachers = 0
        school_students = 0
        school_admins = 0
        
        for i, user in enumerate(users, 1):
            status = "✅ Active" if user.is_active else "❌ Inactive"
            verified = "✅ Yes" if user.email_verified else "❌ No"
            
            # Count by role
            if user.role == UserRole.GURU:
                school_teachers += 1
                total_teachers += 1
            elif user.role == UserRole.MURID:
                school_students += 1
                total_students += 1
            elif user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
                school_admins += 1
                total_admins += 1
            
            total_users += 1
            
            # Truncate long names/emails
            name = user.name[:28] + ".." if len(user.name) > 30 else user.name
            email = user.email[:43] + ".." if len(user.email) > 45 else user.email
            role = user.role.value.upper()
            
            print(f"{i:<4} {name:<30} {email:<45} {role:<12} {status:<10} {verified:<10}")
        
        print("-" * 150)
        print(f"   📊 School Summary:")
        print(f"      👨‍🏫 Teachers: {school_teachers}")
        print(f"      👨‍🎓 Students: {school_students}")
        print(f"      👤 Admins: {school_admins}")
        print(f"      📈 Total: {len(users)} users")
    
    # Grand total
    print(f"\n{'='*150}")
    print("📊 GRAND TOTAL SUMMARY")
    print(f"{'='*150}")
    print(f"   🏫 Total Schools: {len(schools)}")
    print(f"   👨‍🏫 Total Teachers: {total_teachers}")
    print(f"   👨‍🎓 Total Students: {total_students}")
    print(f"   👤 Total Admins: {total_admins}")
    print(f"   📈 TOTAL USERS: {total_users}")
    print(f"{'='*150}\n")
    
    # Quick reference for teacher logins
    print("\n🔑 QUICK REFERENCE - TEACHER LOGIN CREDENTIALS")
    print("=" * 150)
    print(f"{'School':<5} {'School Name':<35} {'Email Pattern':<50} {'Password':<10}")
    print("-" * 150)
    
    for i, school in enumerate(schools, 1):
        email_pattern = f"guru{i}.[1-10]@{school.slug}.sch.id"
        print(f"{i:<5} {school.name[:33]:<35} {email_pattern:<50} 123456")
    
    print("=" * 150)
    print("\n💡 Example Login:")
    print("   • Email: guru1.1@sman5-bandung.sch.id")
    print("   • Password: 123456")
    print("=" * 150 + "\n")
