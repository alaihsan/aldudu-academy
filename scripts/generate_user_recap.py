"""
Generate User Recap Text File
Creates a comprehensive text file with all users, access rights, and passwords
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import User, UserRole, School
from datetime import datetime

app = create_app()

with app.app_context():
    schools = School.query.order_by(School.name).all()
    
    # Generate report
    report = []
    report.append("=" * 100)
    report.append("REKAP LENGKAP DAFTAR USER - ALDUDU ACADEMY")
    report.append("=" * 100)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    report.append("=" * 100)
    report.append("DAFTAR HAK AKSES (ROLE PERMISSIONS)")
    report.append("=" * 100)
    report.append("")
    report.append("1. SUPER_ADMIN")
    report.append("   - Akses penuh ke seluruh sistem")
    report.append("   - Manage semua sekolah")
    report.append("   - Manage semua user")
    report.append("   - View semua data")
    report.append("")
    report.append("2. ADMIN (Admin Sekolah)")
    report.append("   - Manage sekolah sendiri")
    report.append("   - Manage guru di sekolahnya")
    report.append("   - Manage murid di sekolahnya")
    report.append("   - Manage kelas di sekolahnya")
    report.append("   - View laporan sekolah")
    report.append("")
    report.append("3. GURU (Pengajar)")
    report.append("   - Create & manage kelas")
    report.append("   - Create quiz, tugas, materi")
    report.append("   - Input nilai siswa")
    report.append("   - Kelola diskusi kelas")
    report.append("   - Catat KBM (Kegiatan Belajar Mengajar)")
    report.append("   - View buku nilai")
    report.append("")
    report.append("4. MURID (Siswa)")
    report.append("   - Join kelas via class code")
    report.append("   - Kerjakan quiz & tugas")
    report.append("   - View materi pembelajaran")
    report.append("   - Participate dalam diskusi")
    report.append("   - View nilai sendiri")
    report.append("")
    
    total_users = 0
    total_teachers = 0
    total_students = 0
    total_admins = 0
    
    report.append("=" * 100)
    report.append("DAFTAR USER PER SEKOLAH")
    report.append("=" * 100)
    
    for school in schools:
        report.append("")
        report.append("-" * 100)
        report.append(f"SEKOLAH: {school.name}")
        report.append(f"Slug: {school.slug}")
        report.append(f"Status: {school.status.value.upper()}")
        report.append("-" * 100)
        report.append("")
        
        # Get all users for this school
        users = User.query.filter_by(school_id=school.id).order_by(User.role, User.name).all()
        
        if not users:
            report.append("   (Tidak ada user)")
            continue
        
        # Group by role
        admins = [u for u in users if u.role == UserRole.ADMIN]
        teachers = [u for u in users if u.role == UserRole.GURU]
        students = [u for u in users if u.role == UserRole.MURID]
        
        # Admin section
        report.append("📌 ADMIN SEKOLAH:")
        report.append(f"   Total: {len(admins)} user")
        report.append("")
        for i, user in enumerate(admins, 1):
            status = "ACTIVE" if user.is_active else "INACTIVE"
            verified = "YES" if user.email_verified else "NO"
            report.append(f"   {i}. Nama     : {user.name}")
            report.append(f"      Email    : {user.email}")
            report.append(f"      Password : 123456")
            report.append(f"      Role     : {user.role.value.upper()}")
            report.append(f"      Status   : {status} | Verified: {verified}")
            report.append(f"      Hak Akses: Admin sekolah, manage guru & murid, manage kelas")
            report.append("")
        
        # Teachers section
        report.append("📌 GURU (PENGAJAR):")
        report.append(f"   Total: {len(teachers)} user")
        report.append(f"   Format Email: guru[no].[1-10]@{school.slug}.sch.id")
        report.append(f"   Password Default: 123456")
        report.append("")
        report.append(f"   {'No':<4} {'Nama':<30} {'Email':<45} {'Password':<12}")
        report.append(f"   {'-'*4:<4} {'-'*30:<30} {'-'*45:<45} {'-'*12:<12}")
        
        for i, user in enumerate(teachers, 1):
            name = user.name[:28] + ".." if len(user.name) > 30 else user.name
            email = user.email[:43] + ".." if len(user.email) > 45 else user.email
            report.append(f"   {i:<4} {name:<30} {email:<45} {'123456':<12}")
        
        report.append("")
        report.append(f"   Hak Akses Guru:")
        report.append(f"   - Create & manage kelas")
        report.append(f"   - Create quiz, tugas, materi, link")
        report.append(f"   - Input nilai siswa")
        report.append(f"   - Kelola forum diskusi")
        report.append(f"   - Catat KBM (Kegiatan Belajar Mengajar)")
        report.append(f"   - View buku nilai kelas")
        report.append("")
        
        # Students section
        report.append("📌 MURID (SISWA):")
        report.append(f"   Total: {len(students)} user")
        report.append(f"   Format Email: murid[no].[1-144]@{school.slug}.sch.id")
        report.append(f"   Password Default: 123456")
        report.append("")
        report.append(f"   {'No':<4} {'Nama':<30} {'Email':<45} {'Password':<12}")
        report.append(f"   {'-'*4:<4} {'-'*30:<30} {'-'*45:<45} {'-'*12:<12}")
        
        for i, user in enumerate(students, 1):
            name = user.name[:28] + ".." if len(user.name) > 30 else user.name
            email = user.email[:43] + ".." if len(user.email) > 45 else user.email
            report.append(f"   {i:<4} {name:<30} {email:<45} {'123456':<12}")
        
        report.append("")
        report.append(f"   Hak Akses Murid:")
        report.append(f"   - Join kelas via class code")
        report.append(f"   - Kerjakan quiz & tugas")
        report.append(f"   - View materi pembelajaran")
        report.append(f"   - Participate dalam diskusi")
        report.append(f"   - View nilai sendiri")
        report.append("")
        
        # School summary
        school_total = len(admins) + len(teachers) + len(students)
        total_admins += len(admins)
        total_teachers += len(teachers)
        total_students += len(students)
        total_users += school_total
        
        report.append("-" * 100)
        report.append(f"TOTAL USER SEKOLAH INI: {school_total} user")
        report.append(f"   - Admin: {len(admins)}")
        report.append(f"   - Guru: {len(teachers)}")
        report.append(f"   - Murid: {len(students)}")
        report.append("")
    
    # Grand total
    report.append("=" * 100)
    report.append("GRAND TOTAL SUMMARY")
    report.append("=" * 100)
    report.append(f"Total Schools: {len(schools)}")
    report.append(f"Total Admins: {total_admins}")
    report.append(f"Total Teachers: {total_teachers}")
    report.append(f"Total Students: {total_students}")
    report.append(f"GRAND TOTAL USERS: {total_users}")
    report.append("")
    report.append("=" * 100)
    report.append("QUICK LOGIN REFERENCE")
    report.append("=" * 100)
    report.append("")
    report.append("GURU LOGIN:")
    report.append("   Format: guru[no_sekolah].[no_guru]@[slug_sekolah].sch.id")
    report.append("   Password: 123456")
    report.append("")
    report.append("   Contoh:")
    for i, school in enumerate(schools[:3], 1):
        report.append(f"   - guru{i}.1@{school.slug}.sch.id / 123456")
    report.append("")
    report.append("MURID LOGIN:")
    report.append("   Format: murid[no_sekolah].[no_murid]@[slug_sekolah].sch.id")
    report.append("   Password: 123456")
    report.append("")
    report.append("   Contoh:")
    for i, school in enumerate(schools[:3], 1):
        report.append(f"   - murid{i}.1@{school.slug}.sch.id / 123456")
        report.append(f"   - murid{i}.144@{school.slug}.sch.id / 123456")
    report.append("")
    report.append("=" * 100)
    report.append("END OF REPORT")
    report.append("=" * 100)
    
    # Write to file
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'laporan')
    os.makedirs(output_dir, exist_ok=True)
    
    filename = os.path.join(output_dir, f"REKAP_USER_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    print(f"\n✅ Report berhasil dibuat!")
    print(f"📄 File: {filename}")
    print(f"📊 Total users: {total_users}")
    print(f"🏫 Total schools: {len(schools)}")
    print("\n" + "=" * 80)
