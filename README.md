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

    Antarmuka yang Bersih: Dibuat dengan CSS kustom (tanpa framework) untuk menghasilkan tampilan yang unik, ringan, dan fokus pada pengalaman pengguna.

🛠️ Teknologi yang Digunakan

Proyek ini dibangun menggunakan tumpukan teknologi yang modern dan andal:

    Backend:

        Flask: Framework web Python yang ringan dan fleksibel.

        Flask-SQLAlchemy: Ekstensi untuk integrasi dengan database menggunakan Object-Relational Mapper (ORM).

        Flask-Login: Mengelola sesi login pengguna dengan aman.

    Frontend:

        Jinja2: Template engine yang kuat untuk merender halaman HTML secara dinamis.

        CSS Kustom: Semua gaya ditulis dari nol untuk kontrol penuh atas desain.

        JavaScript (Vanilla JS): Digunakan untuk interaktivitas di sisi klien, seperti memuat data secara dinamis (AJAX/Fetch API) dan mengelola modal.

    Database:

        SQLite: Digunakan sebagai database utama untuk kemudahan pengembangan dan portabilitas.

🚀 Cara Menjalankan Proyek

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

Terima kasih telah melihat proyek ini!
