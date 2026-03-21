Aldudu Academy - Learning Management System (LMS)

Selamat datang di Aldudu Academy! Ini adalah proyek Learning Management System (LMS) sederhana namun kuat yang dibangun dari awal menggunakan framework Flask. Aplikasi ini dirancang untuk menyediakan platform yang bersih, intuitif, dan efisien bagi guru dan murid untuk mengelola kegiatan belajar-mengajar secara online.
✨ Fitur Utama

Aldudu Academy dilengkapi dengan serangkaian fitur inti yang esensial untuk sebuah LMS:

    Manajemen Tahun Ajaran: Mengorganisir semua kelas dan konten berdasarkan tahun ajaran. Guru dan murid dapat dengan mudah beralih untuk melihat arsip dari tahun-tahun sebelumnya.

    Manajemen Kelas (CRUD):

        Buat Kelas: Guru dapat membuat kelas baru untuk tahun ajaran yang aktif.

        Edit Kelas: Guru bisa mengubah nama kelas dan memilih warna latar kartu yang menarik untuk personalisasi.

        Lihat Kelas: Tampilan dasbor utama dalam bentuk kartu (card) yang visual dan informatif.

    Sistem Pendaftaran Mandiri:

        Kode Kelas Unik: Setiap kelas yang dibuat akan memiliki kode unik yang di-generate secara otomatis.

        Gabung ke Kelas: Murid dapat dengan mudah mendaftarkan diri ke sebuah kelas hanya dengan memasukkan kode kelas yang diberikan oleh guru.

    Peran Pengguna (Guru & Murid): Sistem membedakan antara peran Guru dan Murid, di mana setiap peran memiliki hak akses dan tampilan dasbor yang berbeda.

    Gradebook & Penilaian:
        
        - Buku Nilai Terintegrasi: Sistem gradebook dengan kategori (Formatif, Sumatif, Sikap, Portfolio)
        - Auto-Sync Quiz & Assignment: Nilai dari quiz dan tugas otomatis masuk ke gradebook
        - Teori Klasik & Rasch Model: Dukungan untuk teori pengukuran klasik dan modern
        - Taksonomi Bloom: Mapping level kognitif untuk setiap soal
        - Analitik Lanjutan: Wright Map, fit statistics, reliability indices

    Antarmuka yang Bersih: Dibuat dengan CSS kustom (tanpa framework) untuk menghasilkan tampilan yang unik, ringan, dan fokus pada pengalaman pengguna.

🛠️ Teknologi yang Digunakan

Proyek ini dibangun menggunakan tumpukan teknologi yang modern dan andal:

    Backend:

        Flask: Framework web Python yang ringan dan fleksibel.

        Flask-SQLAlchemy: Ekstensi untuk integrasi dengan database menggunakan Object-Relational Mapper (ORM).

        Flask-Login: Mengelola sesi login pengguna dengan aman.

        Celery: Distributed task queue untuk background processing (Rasch analysis).

        Redis: Message broker untuk Celery.

    Frontend:

        Jinja2: Template engine yang kuat untuk merender halaman HTML secara dinamis.

        CSS Kustom: Semua gaya ditulis dari nol untuk kontrol penuh atas desain.

        JavaScript (Vanilla JS): Digunakan untuk interaktivitas di sisi klien, seperti memuat data secara dinamis (AJAX/Fetch API) dan mengelola modal.

  
IInisialisasi Database:
    Pastikan `DATABASE_URL` Anda sudah di-set di terminal.
    
    1. Terapkan skema database (membuat tabel):
       flask db upgrade
    
    2. Isi database dengan data awal (contoh guru, murid):
       flask init-db

Untuk menjalankan proyek ini di lingkungan lokal Anda, ikuti langkah-langkah berikut:

    Clone Repositori:

    git clone https://github.com/nama-anda/aldudu-academy.git
    cd aldudu-academy

    Buat dan Aktifkan Virtual Environment:

    # Untuk Windows
    python -m venv venv
    .\venv\Scripts\activate

    # Untuk macOS/Linux
    python3 -m venv venv
    source venv/bin/activate

    Install Dependensi:

    pip install -r requirements.txt

    (Catatan: Pastikan Anda sudah membuat file requirements.txt dengan menjalankan pip freeze > requirements.txt)

    Inisialisasi Database:
    Perintah ini akan membuat file aldudu_academy.db dan mengisinya dengan data awal (contoh guru, murid, dan kelas).

    flask init-db

    Jalankan Aplikasi:

    flask run

Aplikasi sekarang akan berjalan di http://127.0.0.1:5000. Anda bisa login menggunakan akun contoh:

    Guru: guru@aldudu.com (password: 123)

    Murid: murid@aldudu.com (password: 123)


Deployment dengan Docker (Production-like Local Setup)

Untuk menjalankan aplikasi menggunakan Docker, yang menyimulasikan lingkungan produksi, ikuti langkah-langkah berikut:

1.  **Prasyarat**: Pastikan Anda telah menginstal Docker Desktop atau Docker Engine.

2.  **Buat File Environment (`.env`)**:
    Konfigurasi aplikasi, seperti koneksi database dan secret key, dikelola melalui environment variables. Salin contoh file environment dan sesuaikan jika perlu.

    ```bash
    cp deploy/.env.example .env
    ```
    *Catatan: Nilai default di `.env` sudah dikonfigurasi untuk berjalan dengan Docker Compose di lingkungan lokal. Anda tidak perlu mengubahnya untuk memulai.*

3.  **Bangun dan Jalankan Kontainer**:
    Perintah ini akan membangun image Docker, membuat ulang kontainer untuk memastikan konfigurasi terbaru diterapkan, dan menjalankannya di latar belakang.

    ```bash
    docker compose -f deploy/docker-compose.prod.yml up -d --build --force-recreate
    ```

4.  **Jalankan Migrasi Database**:
    Setelah kontainer berjalan, terapkan skema database di dalam kontainer `web`.

    ```bash
    docker compose -f deploy/docker-compose.prod.yml exec web flask db upgrade
    ```

5.  **Isi Database dengan Data Awal (Seed)**:
    Jalankan perintah ini untuk mengisi database dengan data contoh, termasuk akun guru dan murid.

    ```bash
    docker compose -f deploy/docker-compose.prod.yml exec web flask init-db
    ```

6.  **Akses Aplikasi**:
    Aplikasi sekarang akan tersedia di browser Anda pada `http://localhost:8000`.

    Anda bisa login menggunakan akun contoh:
    -   **Guru**: `guru@aldudu.com` (password: `123`)
    -   **Murid**: `murid@aldudu.com` (password: `123`)

7.  **Lihat Log Aplikasi (Opsional)**:
    Untuk melihat log dari layanan `web` secara real-time:

    ```bash
    docker compose -f deploy/docker-compose.prod.yml logs -f web
    ```

Keamanan: menyimpan SECRET_KEY
--------------------------------

Untuk mencegah kebocoran kunci rahasia, aplikasi sekarang membaca SECRET_KEY dari:

- Variabel lingkungan `FLASK_SECRET_KEY` (direkomendasikan untuk deployment).
- File `instance/config.py` yang tidak dilacak oleh Git. Salin `instance/config.py.example` menjadi `instance/config.py` dan masukkan kunci yang kuat.

Contoh (macOS/Linux):

```zsh
# export ke session saat deploy
export FLASK_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
FLASK_APP=app .venv/bin/python -m flask run
```

Jangan menyimpan `instance/config.py` atau variabel rahasia ke repositori publik.

---

## 📊 Rasch Model Integration

Aldudu Academy sekarang dilengkapi dengan **Rasch Model** untuk analisis penilaian modern berdasarkan Item Response Theory.

### Fitur Rasch Model

- ✅ **JMLE Algorithm**: Joint Maximum Likelihood Estimation untuk ability (θ) dan difficulty (δ)
- ✅ **Auto-Trigger**: Analisis otomatis saat threshold terpenuhi (≥30 siswa)
- ✅ **Background Processing**: Celery worker untuk analisis async
- ✅ **Fit Statistics**: Infit/Outfit MNSQ untuk validasi kualitas soal
- ✅ **Wright Map**: Visualisasi distribusi ability dan difficulty
- ✅ **Bloom Taxonomy**: Mapping level kognitif soal

### Quick Start - Rasch Model

**1. Install Dependencies:**
```bash
pip install -r requirements.txt
```

**2. Run Migration:**
```bash
python scripts\run_rasch_migration.py
```

**3. Start Redis & Celery:**
```bash
# Terminal 1: Redis
redis-server

# Terminal 2: Celery Worker
python run_worker.py

# Terminal 3: Flask App
python run.py
```

**4. Enable Rasch untuk Quiz:**
```sql
UPDATE grade_items 
SET enable_rasch_analysis = TRUE 
WHERE quiz_id = 123;
```

**5. Monitor Progress:**
```bash
curl http://localhost:5000/api/rasch/quizzes/123/threshold-status
```

### Dokumentasi Lengkap

Untuk panduan lengkap penggunaan Rasch Model, lihat:
- 📖 **[Laporan/RASCH.md](laporan/README_RASCH.md)** - Panduan lengkap instalasi, konfigurasi, dan interpretasi hasil
- 📖 **[RASCH_IMPLEMENTATION.md](RASCH_IMPLEMENTATION.md)** - Technical implementation details

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/rasch/quizzes/:id/threshold-status` | GET | Check threshold progress |
| `/api/rasch/quizzes/:id/analyze` | POST | Manual trigger analysis |
| `/api/rasch/analyses/:id/persons` | GET | Get person measures (ability θ) |
| `/api/rasch/analyses/:id/items` | GET | Get item measures (difficulty δ) |
| `/api/rasch/analyses/:id/wright-map` | GET | Wright Map visualization |

---

Terima kasih telah melihat proyek ini!
