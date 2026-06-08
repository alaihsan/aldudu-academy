"""
Bersihkan SEMUA user + data yang bergantung pada user, lalu buat 1 superadmin.

Dipertahankan : schools, academic_years (struktur sekolah & tahun ajaran).
Dikosongkan   : users, courses, quizzes, submissions, dan seluruh konten lain
                (karena terikat foreign key NOT NULL ke users).

Superadmin yang dibuat:
    Email    : ichsan@smpi-alazhar22.sch.id
    Password : passwd

Jalankan:
    python scripts/clean_users_seed_superadmin.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import create_app, db
from app.models import User, UserRole
from sqlalchemy import inspect, text

SUPERADMIN_EMAIL = "ichsan@smpi-alazhar22.sch.id"
SUPERADMIN_PASSWORD = "passwd"

# Tabel yang TIDAK dikosongkan
KEEP = {"schools", "academic_years", "alembic_version"}


def clean_and_seed():
    app = create_app()
    with app.app_context():
        insp = inspect(db.engine)
        tables = [t for t in insp.get_table_names() if t not in KEEP]

        print(f"Mengosongkan {len(tables)} tabel (pertahankan: {', '.join(sorted(KEEP))})...")
        with db.engine.begin() as conn:
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
            for t in tables:
                conn.execute(text(f"TRUNCATE TABLE `{t}`"))
                print(f"  - dikosongkan: {t}")
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))

        admin = User(
            name="Super Admin",
            email=SUPERADMIN_EMAIL,
            role=UserRole.SUPER_ADMIN,
            is_active=True,
            email_verified=True,
        )
        admin.set_password(SUPERADMIN_PASSWORD)
        db.session.add(admin)
        db.session.commit()

        print("\nSelesai. Akun superadmin dibuat:")
        print(f"  Email    : {SUPERADMIN_EMAIL}")
        print(f"  Password : {SUPERADMIN_PASSWORD}")


if __name__ == "__main__":
    clean_and_seed()
