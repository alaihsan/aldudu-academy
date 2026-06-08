import sys
import os
from pathlib import Path

# Tambahkan project root ke path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import create_app, db
from app.models.user import User

def reset_passwords():
    app = create_app()
    with app.app_context():
        print("Mencari semua user...")
        users = User.query.all()
        total = len(users)
        print(f"Ditemukan {total} user.")
        
        for i, user in enumerate(users, 1):
            user.set_password("passwd")
            if i % 50 == 0:
                print(f"Diproses {i}/{total}...")
        
        print("Menyimpan perubahan ke database...")
        db.session.commit()
        print("✅ Berhasil! Semua password user telah diatur menjadi 'passwd'.")

if __name__ == "__main__":
    reset_passwords()
