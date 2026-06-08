"""
Tambahkan kolom `gender` ke tabel users (non-destruktif, idempotent).

Menyimpan jenis kelamin siswa: 'L' (Laki-laki) / 'P' (Perempuan).

Jalankan:
    python scripts/add_gender_to_users.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import create_app, db
from sqlalchemy import inspect, text


def add_gender_column():
    app = create_app()
    with app.app_context():
        cols = [c['name'] for c in inspect(db.engine).get_columns('users')]
        if 'gender' in cols:
            print("Kolom 'gender' sudah ada. Tidak ada perubahan.")
            return
        print("Menambahkan kolom 'gender' ke tabel users...")
        with db.engine.begin() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN gender VARCHAR(1) NULL"))
        print("Selesai. Kolom 'gender' berhasil ditambahkan.")


if __name__ == "__main__":
    add_gender_column()
