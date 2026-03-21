"""
Script untuk menjalankan migration Rasch Model ke database MySQL
Versi 4: Execute procedure secara manual
"""

import sys
import os
import re

# Tambahkan project root ke path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.config import Config
import pymysql


def run_migration():
    """Main migration function"""
    
    migration_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'migrations',
        '002_rasch_model_mysql.sql'
    )
    
    if not os.path.exists(migration_file):
        print(f"❌ Migration file tidak ditemukan: {migration_file}")
        return False
    
    print(f"📄 Reading migration file: {migration_file}")
    
    app = create_app()
    
    with app.app_context():
        # Get database config
        db_url = Config.SQLALCHEMY_DATABASE_URI
        
        # Parse MySQL connection string
        if db_url.startswith('mysql+pymysql://'):
            db_url = db_url.replace('mysql+pymysql://', '')
            parts = db_url.split('/')
            database = parts[1] if len(parts) > 1 else 'aldudu_academy'
            
            auth_host = parts[0].split('@')
            host_port = auth_host[1].split(':') if len(auth_host) > 1 else ['localhost', '3306']
            host = host_port[0]
            
            user_pass = auth_host[0].split(':')
            user = user_pass[0] if user_pass[0] else 'root'
            password = user_pass[1] if len(user_pass) > 1 else 'passwd'  # Default password
        else:
            host = 'localhost'
            user = 'root'
            password = 'passwd'  # Default password
            database = 'aldudu_academy'
        
        try:
            print(f"🔗 Connecting to MySQL ({host}/{database})...")
            connection = pymysql.connect(
                host=host,
                user=user,
                password=password,
                database=database,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False
            )
            
            cursor = connection.cursor()
            
            print("   Disabling foreign key checks...")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            connection.commit()
            
            # Read file
            with open(migration_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # Remove comments
            sql_content = re.sub(r'--.*?$', '', sql_content, flags=re.MULTILINE)
            sql_content = re.sub(r'/\*.*?\*/', '', sql_content, flags=re.DOTALL)
            
            # Extract procedure definition manually
            print("\n📋 Creating stored procedure for grade_items modification...")
            
            procedure_sql = """
            DROP PROCEDURE IF EXISTS add_rasch_columns_to_grade_items
            """
            cursor.execute(procedure_sql)
            connection.commit()
            
            procedure_sql = """
            CREATE PROCEDURE add_rasch_columns_to_grade_items()
            BEGIN
                IF NOT EXISTS (
                    SELECT * FROM information_schema.COLUMNS 
                    WHERE TABLE_SCHEMA=DATABASE() 
                    AND TABLE_NAME='grade_items' 
                    AND COLUMN_NAME='enable_rasch_analysis'
                ) THEN
                    ALTER TABLE grade_items 
                    ADD COLUMN enable_rasch_analysis BOOLEAN DEFAULT FALSE NOT NULL;
                END IF;
                
                IF NOT EXISTS (
                    SELECT * FROM information_schema.COLUMNS 
                    WHERE TABLE_SCHEMA=DATABASE() 
                    AND TABLE_NAME='grade_items' 
                    AND COLUMN_NAME='rasch_analysis_id'
                ) THEN
                    ALTER TABLE grade_items 
                    ADD COLUMN rasch_analysis_id INT NULL;
                END IF;
                
                IF NOT EXISTS (
                    SELECT * FROM information_schema.COLUMNS 
                    WHERE TABLE_SCHEMA=DATABASE() 
                    AND TABLE_NAME='grade_items' 
                    AND COLUMN_NAME='show_rasch_to_students'
                ) THEN
                    ALTER TABLE grade_items 
                    ADD COLUMN show_rasch_to_students BOOLEAN DEFAULT FALSE NOT NULL;
                END IF;
                
                IF EXISTS (
                    SELECT * FROM information_schema.TABLE_CONSTRAINTS 
                    WHERE TABLE_SCHEMA=DATABASE() 
                    AND TABLE_NAME='grade_items' 
                    AND CONSTRAINT_NAME='fk_grade_item_rasch_analysis'
                ) THEN
                    ALTER TABLE grade_items DROP FOREIGN KEY fk_grade_item_rasch_analysis;
                END IF;
                
                IF EXISTS (
                    SELECT * FROM information_schema.STATISTICS 
                    WHERE TABLE_SCHEMA=DATABASE() 
                    AND TABLE_NAME='grade_items' 
                    AND INDEX_NAME='idx_grade_items_rasch'
                ) THEN
                    DROP INDEX idx_grade_items_rasch ON grade_items;
                END IF;
                
                ALTER TABLE grade_items
                ADD CONSTRAINT fk_grade_item_rasch_analysis 
                    FOREIGN KEY (rasch_analysis_id) REFERENCES rasch_analyses(id) ON DELETE SET NULL;
                
                CREATE INDEX idx_grade_items_rasch ON grade_items(rasch_analysis_id);
            END
            """
            
            cursor.execute(procedure_sql)
            connection.commit()
            print("   ✓ Procedure created")
            
            # Call procedure
            print("   Executing procedure...")
            cursor.execute("CALL add_rasch_columns_to_grade_items()")
            connection.commit()
            print("   ✓ Procedure executed")
            
            # Drop procedure
            cursor.execute("DROP PROCEDURE IF EXISTS add_rasch_columns_to_grade_items")
            connection.commit()
            
            # Now execute remaining SQL (tables)
            print("\n📊 Creating Rasch tables...")
            
            # Remove everything from DELIMITER onwards
            sql_content = re.sub(
                r'DELIMITER.*?CREATE PROCEDURE.*?END.*?DELIMITER.*?;',
                '',
                sql_content,
                flags=re.DOTALL | re.IGNORECASE
            )
            
            # Remove CALL and DROP PROCEDURE statements
            sql_content = re.sub(
                r'CALL add_rasch_columns_to_grade_items\(\)',
                '',
                sql_content,
                flags=re.IGNORECASE
            )
            sql_content = re.sub(
                r'DROP PROCEDURE IF EXISTS add_rasch_columns_to_grade_items',
                '',
                sql_content,
                flags=re.IGNORECASE
            )
            
            # Split by semicolon
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            
            for i, stmt in enumerate(statements, 1):
                if not stmt or stmt.startswith('SET') or not stmt.split():
                    continue
                
                stmt_type = stmt.split()[0].upper()
                
                try:
                    cursor.execute(stmt)
                    connection.commit()
                    print(f"   [{i:3d}/{len(statements)}] ✓ {stmt_type}")
                except Exception as e:
                    error_msg = str(e)
                    
                    if any(x in error_msg.lower() for x in [
                        "already exists", 
                        "duplicate",
                        "doesn't exist",
                        "can't drop"
                    ]):
                        print(f"   [{i:3d}/{len(statements)}] ⚠ {stmt_type} - Skipped")
                    else:
                        print(f"   [{i:3d}/{len(statements)}] ✗ {stmt_type}")
                        print(f"       Error: {error_msg[:150]}")
                        raise
            
            print("\n   Re-enabling foreign key checks...")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            connection.commit()
            
            print("\n✅ Migration berhasil!")
            
            # Verify tables
            print("\n📋 Verifying tables...")
            cursor.execute("SHOW TABLES LIKE 'rasch_%'")
            tables = cursor.fetchall()
            
            print(f"   Ditemukan {len(tables)} tabel Rasch:")
            for table in tables:
                print(f"      - {list(table.values())[0]}")
            
            cursor.execute("SHOW TABLES LIKE 'question_bloom_taxonomy'")
            bloom_tables = cursor.fetchall()
            if bloom_tables:
                print(f"      - question_bloom_taxonomy")
            
            # Verify grade_items columns
            print("\n📋 Verifying grade_items columns...")
            cursor.execute("SHOW COLUMNS FROM grade_items LIKE '%rasch%'")
            columns = cursor.fetchall()
            
            if columns:
                print(f"   Ditemukan {len(columns)} kolom Rasch di grade_items:")
                for col in columns:
                    print(f"      - {col['Field']} ({col['Type']})")
            
            cursor.close()
            connection.close()
            
            return True
            
        except Exception as e:
            print(f"\n❌ Migration gagal: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)
