# Quiz Flask

Repo Flask mandiri untuk fitur quiz yang dipisah dari Aldudu Academy. Scope awal dibuat ramping: autentikasi guru/murid, CRUD quiz, editor soal, halaman pengerjaan, submit jawaban, auto grading, statistik, password quiz, dan upload gambar/file.

## Fitur

- Login dan register guru/murid.
- Guru dapat membuat quiz, mengubah status draft/published/unpublished, durasi, batas attempt, password, tema, dan shuffle.
- Tipe soal: pilihan ganda, benar/salah, dropdown, checkbox, jawaban panjang, upload file, dan matching.
- Auto grading untuk pilihan ganda, benar/salah, dropdown, checkbox, dan matching.
- Jawaban panjang dan upload file tersimpan untuk penilaian manual lanjutan.
- Statistik submission: total, rata-rata, tertinggi, terendah, dan daftar nilai murid.

## Setup

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
$env:FLASK_APP="run.py"
flask init-db
flask run
```

Untuk akses dari device lain di jaringan lokal, jalankan server dengan host `0.0.0.0`:

```powershell
$env:FLASK_RUN_HOST="0.0.0.0"
$env:FLASK_RUN_PORT="5001"
flask run
```

Lalu buka `http://IP-KOMPUTER:5001` dari device lain yang tersambung ke intranet yang sama.

Default database memakai MySQL:

```text
mysql+pymysql://root:passwd@127.0.0.1:3306/db_alsenform?charset=utf8mb4
```

Konfigurasi bisa diubah lewat `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`, dan `MYSQL_CHARSET` di `.env`. Jika perlu koneksi penuh yang berbeda, set `QUIZ_DATABASE_URL`.

## Skema Database

Skema SQL referensi ada di `docs/schema.sql`. Model SQLAlchemy ada di:

- `app/models/user.py`
- `app/models/quiz.py`

Entitas utama:

- `users`
- `quizzes`
- `questions`
- `options`
- `quiz_submissions`
- `answers`

Kolom `answers.answer_data` memakai JSON supaya tipe jawaban kompleks seperti checkbox dan matching tidak dipaksa menjadi string rapuh.

## Catatan Scope

Yang sengaja tidak dibawa dari Aldudu Academy tahap pertama:

- Course/classroom.
- Gradebook.
- Rasch analysis.
- Multi-tenant school.
- Import DOCX.

Fitur itu bisa ditambahkan lagi setelah basis quiz mandiri ini stabil.
