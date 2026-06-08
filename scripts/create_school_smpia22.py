"""
Buat sekolah "SMPIA 22 Sentra Primer" (status ACTIVE) dan jadikan
admin@smpi-alazhar22.sch.id sebagai admin sekolah (langsung bisa login).

Idempotent: aman dijalankan berulang.

Admin:
    Email    : admin@smpi-alazhar22.sch.id
    Password : passwd

Jalankan:
    python scripts/create_school_smpia22.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import create_app, db
from app.models import School, SchoolStatus, User, UserRole

SCHOOL_NAME = "SMPIA 22 Sentra Primer"
SCHOOL_SLUG = "smpia-22-sentra-primer"
ADMIN_EMAIL = "admin@smpi-alazhar22.sch.id"
ADMIN_NAME = "Admin SMPIA 22 Sentra Primer"
ADMIN_PASSWORD = "passwd"


def run():
    app = create_app()
    with app.app_context():
        # 1) Sekolah (reuse jika sudah ada berdasarkan slug)
        school = School.query.filter_by(slug=SCHOOL_SLUG).first()
        if school:
            print(f"Sekolah sudah ada (id={school.id}). Memastikan status ACTIVE.")
            school.status = SchoolStatus.ACTIVE
        else:
            school = School(
                name=SCHOOL_NAME,
                slug=SCHOOL_SLUG,
                email=ADMIN_EMAIL,
                admin_email=ADMIN_EMAIL,
                status=SchoolStatus.ACTIVE,
            )
            db.session.add(school)
            db.session.flush()
            print(f"Sekolah dibuat (id={school.id}): {SCHOOL_NAME}")

        # 2) Admin sekolah (reuse jika email sudah ada)
        admin = User.query.filter_by(email=ADMIN_EMAIL).first()
        if admin:
            print("User admin sudah ada. Memperbarui ke admin sekolah ini.")
            admin.role = UserRole.ADMIN
            admin.school_id = school.id
            admin.is_active = True
            admin.email_verified = True
        else:
            admin = User(
                name=ADMIN_NAME,
                email=ADMIN_EMAIL,
                role=UserRole.ADMIN,
                school_id=school.id,
                is_active=True,
                email_verified=True,
            )
            admin.set_password(ADMIN_PASSWORD)
            db.session.add(admin)
            print(f"Admin dibuat: {ADMIN_EMAIL} (password: {ADMIN_PASSWORD})")

        db.session.commit()

        print("\nSelesai.")
        print(f"  Sekolah  : {school.name} (slug: {school.slug}, status: {school.status.value})")
        print(f"  Admin    : {ADMIN_EMAIL}")
        if not User.query.filter_by(email=ADMIN_EMAIL).first().check_password(ADMIN_PASSWORD):
            print("  (Catatan: password admin tidak diubah karena user sudah ada sebelumnya.)")


if __name__ == "__main__":
    run()
