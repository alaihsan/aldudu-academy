"""
Tambahkan kolom `nis` ke tabel users (non-destruktif, data lama aman).

Kolom ini dipakai siswa untuk login. Aman dijalankan berulang (idempotent).

Jalankan:
    python scripts/add_nis_to_users.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import create_app, db
from sqlalchemy import inspect, text


def add_nis_column():
    app = create_app()
    with app.app_context():
        insp = inspect(db.engine)
        cols = [c['name'] for c in insp.get_columns('users')]
        if 'nis' in cols:
            print("Kolom 'nis' sudah ada. Tidak ada perubahan.")
            return

        print("Menambahkan kolom 'nis' ke tabel users...")
        with db.engine.begin() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN nis VARCHAR(30) NULL"))
            conn.execute(text("CREATE UNIQUE INDEX ix_users_nis ON users (nis)"))
        print("Selesai. Kolom 'nis' berhasil ditambahkan.")


if __name__ == "__main__":
    add_nis_column()
