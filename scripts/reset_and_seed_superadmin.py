"""
Reset total database + buat 1 akun superadmin.

PERINGATAN: Script ini MENGHAPUS SELURUH DATA (drop_all + create_all),
termasuk semua user, sekolah, kelas, dan seluruh konten. Tidak bisa dibatalkan.

Setelah reset, dibuat 1 akun superadmin:
    Email    : ichsan@smpi-alazhar22.sch.id
    Password : passwd

Jalankan:
    python scripts/reset_and_seed_superadmin.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import create_app, db
from app.models import User, UserRole

SUPERADMIN_EMAIL = "ichsan@smpi-alazhar22.sch.id"
SUPERADMIN_PASSWORD = "passwd"


def reset_and_seed():
    app = create_app()
    with app.app_context():
        print("Menghapus seluruh tabel (drop_all)...")
        db.drop_all()
        print("Membuat ulang skema (create_all)...")
        db.create_all()

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

        print("Selesai. Akun superadmin dibuat:")
        print(f"  Email    : {SUPERADMIN_EMAIL}")
        print(f"  Password : {SUPERADMIN_PASSWORD}")


if __name__ == "__main__":
    confirm = input(
        "Ini akan MENGHAPUS SEMUA DATA dan tidak bisa dibatalkan.\n"
        "Ketik 'RESET' untuk melanjutkan: "
    )
    if confirm.strip() == "RESET":
        reset_and_seed()
    else:
        print("Dibatalkan.")
