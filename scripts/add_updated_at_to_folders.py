"""
Script untuk menambahkan kolom updated_at ke tabel content_folders
Jalankan: python scripts/add_updated_at_to_folders.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # Check if column already exists
        result = db.session.execute(text("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'content_folders' 
            AND COLUMN_NAME = 'updated_at'
        """)).fetchone()
        
        if result:
            print("✅ Kolom updated_at sudah ada di tabel content_folders")
        else:
            print("⏳ Menambahkan kolom updated_at...")
            
            db.session.execute(text("""
                ALTER TABLE content_folders 
                ADD COLUMN updated_at DATETIME NULL DEFAULT NULL
            """))
            print("✅ Kolom updated_at berhasil ditambahkan")
            
            # Update existing records with current timestamp
            db.session.execute(text("""
                UPDATE content_folders 
                SET updated_at = created_at 
                WHERE updated_at IS NULL
            """))
            print("✅ Updated existing records")
            
            db.session.commit()
            print("\n🎉 Migrasi berhasil!")
    
    except Exception as e:
        db.session.rollback()
        print(f"\n❌ Error: {e}")
        sys.exit(1)
