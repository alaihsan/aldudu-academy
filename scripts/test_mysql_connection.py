"""
Test script untuk simulasi koneksi MySQL dengan password
"""

import os
import pymysql
from dotenv import load_dotenv

# Load .env if exists
load_dotenv()

# Get config from env or defaults
db_url = os.environ.get('DATABASE_URL', '')
if db_url.startswith('mysql+pymysql://'):
    # Parse URL
    db_url = db_url.replace('mysql+pymysql://', '')
    parts = db_url.split('/')
    database = parts[1] if len(parts) > 1 else 'aldudu_academy'
    auth_host = parts[0].split('@')
    host_port = auth_host[1].split(':') if len(auth_host) > 1 else ['localhost', '3306']
    host = host_port[0]
    user_pass = auth_host[0].split(':')
    user = user_pass[0]
    password = user_pass[1] if len(user_pass) > 1 else ''
else:
    host = os.environ.get('MYSQL_HOST', 'localhost')
    user = os.environ.get('MYSQL_USER', 'root')
    password = os.environ.get('MYSQL_PASSWORD', 'passwd')
    database = os.environ.get('MYSQL_DATABASE', 'aldudu_academy')

print("Testing MySQL connection...")
print(f"Host: {host}")
print(f"User: {user}")
print(f"Password: {'*' * len(password)}")
print(f"Database: {database}")
print()

try:
    connection = pymysql.connect(
        host=host,
        user=user,
        password=password,
        database=database,
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
