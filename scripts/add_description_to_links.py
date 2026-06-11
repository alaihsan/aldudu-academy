"""
Tambahkan kolom `description` ke tabel links (non-destruktif, idempotent).

Jalankan:
    python scripts/add_description_to_links.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import create_app, db
from sqlalchemy import inspect, text


def add_column():
    app = create_app()
    with app.app_context():
        cols = [c['name'] for c in inspect(db.engine).get_columns('links')]
        if 'description' in cols:
            print("Kolom 'description' sudah ada di tabel links. Tidak ada perubahan.")
            return
        print("Menambahkan kolom 'description' ke tabel links...")
        with db.engine.begin() as conn:
            conn.execute(text("ALTER TABLE links ADD COLUMN description TEXT NULL"))
        print("Selesai.")


if __name__ == "__main__":
    add_column()
