"""
Script untuk menambahkan kolom is_archived ke tabel links
Jalankan: python scripts/add_is_archived_to_links.py
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
            AND TABLE_NAME = 'links' 
            AND COLUMN_NAME = 'is_archived'
        """)).fetchone()
        
        if result:
            print("✅ Kolom is_archived sudah ada di tabel links")
        else:
            print("⏳ Menambahkan kolom is_archived...")
            
            db.session.execute(text("""
                ALTER TABLE links 
                ADD COLUMN is_archived BOOLEAN NOT NULL DEFAULT FALSE
            """))
            print("✅ Kolom is_archived berhasil ditambahkan")
            
            try:
                db.session.execute(text("""
                    CREATE INDEX idx_links_is_archived ON links(is_archived)
                """))
                print("✅ Index idx_links_is_archived dibuat")
            except Exception as e:
                print(f"⚠️ Index mungkin sudah ada: {e}")
            
            db.session.commit()
            print("\n🎉 Migrasi berhasil!")
    
    except Exception as e:
        db.session.rollback()
        print(f"\n❌ Error: {e}")
        sys.exit(1)
