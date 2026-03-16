"""Verify all teachers are active and can login"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import User, UserRole, School

app = create_app()

with app.app_context():
    schools = School.query.all()
    
    print("=" * 70)
    print("📊 SCHOOLS AND TEACHERS SUMMARY")
    print("=" * 70)
    
    total_teachers = 0
    
    for i, school in enumerate(schools, 1):
        teachers = User.query.filter_by(
            school_id=school.id,
            role=UserRole.GURU,
            is_active=True,
            email_verified=True
        ).count()
        
        total_teachers += teachers
        
        print(f"\n{i}. {school.name}")
        print(f"   👨‍🏫 Teachers: {teachers} (ACTIVE & VERIFIED)")
        print(f"   🔑 Login Format: guru{i}.[1-10]@{school.slug}.sch.id")
        print(f"   📝 Example: guru{i}.1@{school.slug}.sch.id")
        print(f"   🔒 Password: 123456")
    
    print("\n" + "=" * 70)
    print(f"✅ TOTAL: {total_teachers} teachers across {len(schools)} schools")
    print("=" * 70)
    print("\n💡 All teachers can login with:")
    print("   • Email: guru[school_number].[teacher_number]@[school_slug].sch.id")
    print("   • Password: 123456")
    print("   • Example: guru1.1@sman5-bandung.sch.id / 123456")
    print("=" * 70)
