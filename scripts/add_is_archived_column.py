"""
Script untuk menambahkan kolom is_archived ke tabel quizzes
Jalankan: python scripts/add_is_archived_column.py
"""
import sys
import os

# Add project root to path
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
            AND TABLE_NAME = 'quizzes' 
            AND COLUMN_NAME = 'is_archived'
        """)).fetchone()
        
        if result:
            print("✅ Kolom is_archived sudah ada di tabel quizzes")
        else:
            print("⏳ Menambahkan kolom is_archived...")
            
            # Add column
            db.session.execute(text("""
                ALTER TABLE quizzes 
                ADD COLUMN is_archived BOOLEAN NOT NULL DEFAULT FALSE
            """))
            print("✅ Kolom is_archived berhasil ditambahkan")
            
            # Create indexes
            try:
                db.session.execute(text("""
                    CREATE INDEX idx_quizzes_is_archived ON quizzes(is_archived)
                """))
                print("✅ Index idx_quizzes_is_archived dibuat")
            except Exception as e:
                print(f"⚠️ Index idx_quizzes_is_archived mungkin sudah ada: {e}")
            
            try:
                db.session.execute(text("""
                    CREATE INDEX idx_quizzes_course_archived ON quizzes(course_id, is_archived)
                """))
                print("✅ Index idx_quizzes_course_archived dibuat")
            except Exception as e:
                print(f"⚠️ Index idx_quizzes_course_archived mungkin sudah ada: {e}")
            
            db.session.commit()
            print("\n🎉 Migrasi berhasil!")
    
    except Exception as e:
        db.session.rollback()
        print(f"\n❌ Error: {e}")
        sys.exit(1)
