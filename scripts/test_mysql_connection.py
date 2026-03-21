"""
Test script untuk simulasi koneksi MySQL dengan password
"""

import pymysql

# Test dengan password yang Anda berikan
print("Testing MySQL connection...")
print("Host: localhost")
print("User: root")
print("Password: passwd")
print("Database: aldudu_academy")
print()

try:
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='passwd',  # Password yang Anda berikan
        database='aldudu_academy',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False
    )
    
    print("✅ KONEKSI BERHASIL!")
    print()
    
    # Test query
    cursor = connection.cursor()
    cursor.execute("SELECT DATABASE() as current_db")
    result = cursor.fetchone()
    print(f"Current database: {result['current_db']}")
    
    cursor.execute("SELECT VERSION() as mysql_version")
    result = cursor.fetchone()
    print(f"MySQL version: {result['mysql_version']}")
    
    cursor.execute("SHOW TABLES LIKE 'rasch_%'")
    tables = cursor.fetchall()
    print(f"\nRasch tables found: {len(tables)}")
    for table in tables:
        print(f"  - {table['Tables_in_aldudu_academy (rasch_%)']}")
    
    cursor.execute("SHOW COLUMNS FROM grade_items LIKE '%rasch%'")
    columns = cursor.fetchall()
    print(f"\nGrade items Rasch columns: {len(columns)}")
    for col in columns:
        print(f"  - {col['Field']} ({col['Type']})")
    
    cursor.close()
    connection.close()
    
except Exception as e:
    print(f"❌ KONEKSI GAGAL!")
    print(f"Error: {e}")
    print()
    print("Kemungkinan penyebab:")
    print("1. Password salah")
    print("2. User 'root' tidak memiliki akses dari localhost")
    print("3. MySQL service tidak running")
    print()
    print("Solusi:")
    print("1. Cek password di file konfigurasi Anda")
    print("2. Jalankan: mysql -u root -p (masuk manual untuk cek password)")
    print("3. Restart MySQL service")
