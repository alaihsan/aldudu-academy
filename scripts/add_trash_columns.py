"""
Tambahkan kolom `is_trashed` & `trashed_at` ke tabel quizzes, assignments, files, links
untuk fitur Ruang TPS (Tempat Pembuangan Sementara) — soft-delete dengan
auto-purge 30 hari. Non-destruktif & idempotent.

Jalankan:
    python scripts/add_trash_columns.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import create_app, db
from sqlalchemy import inspect, text


TABLES = ['quizzes', 'assignments', 'files', 'links']


def add_columns():
    app = create_app()
    with app.app_context():
        insp = inspect(db.engine)
        for table in TABLES:
            cols = {c['name'] for c in insp.get_columns(table)}
            with db.engine.begin() as conn:
                if 'is_trashed' not in cols:
                    print(f"  + {table}.is_trashed")
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN is_trashed BOOLEAN NOT NULL DEFAULT 0"))
                    conn.execute(text(f"CREATE INDEX ix_{table}_is_trashed ON {table} (is_trashed)"))
                else:
                    print(f"  = {table}.is_trashed sudah ada")
                if 'trashed_at' not in cols:
                    print(f"  + {table}.trashed_at")
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN trashed_at DATETIME NULL"))
                else:
                    print(f"  = {table}.trashed_at sudah ada")
        print("Selesai.")


if __name__ == "__main__":
    add_columns()
