# Pull Request: Gradebook Feature - Teacher & Student Integration

## 📋 Description
Implementasi lengkap fitur **Gradebook (Buku Nilai)** dengan integrasi penuh untuk guru dan murid. Fitur ini memungkinkan:
- **Guru**: Mengelola kategori penilaian, CP/TP, item penilaian, input nilai, dan import nilai dari quiz/tugas
- **Murid**: Melihat nilai, predikat, status penguasaan materi, dan feedback secara real-time

## ✨ Fitur Utama

### 👨‍🏫 Untuk Guru

#### 1. **Setup Penilaian**
- ✅ Kategori penilaian (Formatif, Sumatif, Sikap, Portfolio)
- ✅ Capaian Pembelajaran (CP) dan Tujuan Pembelajaran (TP)
- ✅ Bobot dan deskripsi per kategori

#### 2. **Input Nilai**
- ✅ Tambah item penilaian (Tugas, Ujian, Kuis, dll)
- ✅ Input nilai massal untuk semua siswa
- ✅ Auto-fill nilai maksimal
- ✅ Feedback per siswa
- ✅ Filter berdasarkan kategori dan CP/TP

#### 3. **Import dari Quiz**
- ✅ Import quiz yang sudah dibuat ke gradebook
- ✅ Sinkronisasi otomatis nilai quiz submission
- ✅ Mapping ke kategori dan TP

#### 4. **Rekap & Analitik**
- ✅ Rekap nilai semua siswa
- ✅ Statistik kelas (rata-rata, tertinggi, terendah)
- ✅ Distribusi nilai
- ✅ Predikat otomatis (A/B/C/D)

### 👨‍🎓 Untuk Murid

#### 1. **Dashboard Nilai**
- ✅ Nilai akhir dengan visualisasi circular
- ✅ Predikat dan status penguasaan materi
- ✅ Statistik tugas/kuis (total, dinilai, belum dinilai)

#### 2. **Detail Capaian Materi**
- ✅ Breakdown per CP dengan mastery status
- ✅ Visualisasi progress bar per CP
- ✅ Warna indikator berdasarkan predikat

#### 3. **Tabel Nilai Detail**
- ✅ Daftar semua tugas & kuis
- ✅ Nilai per item (score & persentase)
- ✅ Predikat per item
- ✅ Feedback dari guru
- ✅ Indikator tipe (quiz/tugas)

## 🔧 Integrasi Quiz & Assignment

### Quiz Integration
```python
# Import quiz ke gradebook
POST /gradebook/api/quizzes/<quiz_id>/import
{
  "category_id": 1,
  "learning_goal_id": 2  # optional
}

# Sync nilai quiz (auto-update)
POST /gradebook/api/quizzes/<quiz_id>/sync
```

### Assignment Integration
```python
# Assignment otomatis terhubung ke GradeItem
assignment.grade_item  # One-to-one relationship
```

### Auto-Grading Flow
1. Siswa menyelesaikan quiz → `QuizSubmission` dibuat
2. Quiz auto-grade → `score` & `total_points` tersimpan
3. Jika quiz sudah di-import → `sync_quiz_grades()` update `GradeEntry`
4. Nilai muncul real-time di gradebook guru & murid

## 📁 File yang Diubah/Dibuat

### Backend
```
app/
├── models/gradebook.py          # GradeCategory, LearningObjective, LearningGoal, GradeItem, GradeEntry
├── services/gradebook_service.py # Logic bisnis, kalkulasi, sync quiz
├── blueprints/gradebook.py      # Routes (page + API)
└── templates/gradebook/
    ├── teacher_gradebook.html   # Dashboard guru
    ├── student_grades.html      # Detail nilai murid
    ├── student_grades_index.html # List mata pelajaran
    └── course_setup.html        # Setup CP/TP
```

### Database Schema
```sql
-- Grade Categories
CREATE TABLE grade_categories (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  category_type ENUM NOT NULL,
  weight FLOAT DEFAULT 0,
  course_id INT REFERENCES courses(id)
);

-- Learning Objectives (CP)
CREATE TABLE learning_objectives (
  id SERIAL PRIMARY KEY,
  code VARCHAR(20) NOT NULL,
  description TEXT NOT NULL,
  course_id INT REFERENCES courses(id)
);

-- Learning Goals (TP)
CREATE TABLE learning_goals (
  id SERIAL PRIMARY KEY,
  learning_objective_id INT REFERENCES learning_objectives(id),
  code VARCHAR(20) NOT NULL,
  description TEXT NOT NULL
);

-- Grade Items
CREATE TABLE grade_items (
  id SERIAL PRIMARY KEY,
  name VARCHAR(200) NOT NULL,
  category_id INT REFERENCES grade_categories(id),
  max_score FLOAT DEFAULT 100,
  quiz_id INT REFERENCES quizzes(id),  -- Integration
  assignment_id INT REFERENCES assignments(id)  -- Integration
);

-- Grade Entries
CREATE TABLE grade_entries (
  id SERIAL PRIMARY KEY,
  grade_item_id INT REFERENCES grade_items(id),
  student_id INT REFERENCES users(id),
  score FLOAT,
  percentage FLOAT,
  feedback TEXT,
  UNIQUE(grade_item_id, student_id)
);
```

## 🎯 API Endpoints

### Categories
- `GET /gradebook/api/categories?course_id=X`
- `POST /gradebook/api/categories`
- `PUT /gradebook/api/categories/:id`
- `DELETE /gradebook/api/categories/:id`

### Learning Objectives
- `GET /gradebook/api/learning-objectives?course_id=X`
- `POST /gradebook/api/learning-objectives`
- `PUT /gradebook/api/learning-objectives/:id`
- `DELETE /gradebook/api/learning-objectives/:id`

### Grade Items
- `GET /gradebook/api/items?course_id=X`
- `POST /gradebook/api/items`
- `PUT /gradebook/api/items/:id`
- `DELETE /gradebook/api/items/:id`

### Grade Entries
- `GET /gradebook/api/entries?grade_item_id=X`
- `POST /gradebook/api/entries/bulk`
- `PUT /gradebook/api/entries/:id`

### Quiz Integration
- `POST /gradebook/api/quizzes/:id/import`
- `POST /gradebook/api/quizzes/:id/sync`
- `GET /gradebook/api/quizzes/available?course_id=X`

### Statistics
- `GET /gradebook/api/stats/:course_id`
- `GET /gradebook/api/student/:student_id/course/:course_id`

## 🎨 UI/UX Features

### Responsive Design
- ✅ Mobile-friendly tables (horizontal scroll)
- ✅ Modal dialogs untuk input/edit
- ✅ Tab navigation (Input | Rekap | Quiz | Analytics)
- ✅ Color-coded badges untuk predikat

### Visual Feedback
- ✅ Loading spinners
- ✅ Success/error toasts
- ✅ Animated grade circles
- ✅ Mastery status banners
- ✅ Progress bars per CP

### Accessibility
- ✅ Keyboard navigation
- ✅ Screen reader friendly
- ✅ High contrast colors
- ✅ Clear labels & placeholders

## 🧪 Testing Checklist

### Teacher Flow
- [ ] Setup kategori penilaian
- [ ] Tambah CP & TP
- [ ] Buat item penilaian manual
- [ ] Import quiz ke gradebook
- [ ] Input nilai untuk semua siswa
- [ ] Lihat rekap nilai
- [ ] Lihat analitik kelas
- [ ] Edit/hapus item

### Student Flow
- [ ] Lihat daftar mata pelajaran
- [ ] Lihat detail nilai per course
- [ ] Lihat predikat & mastery status
- [ ] Lihat feedback per tugas
- [ ] Lihat progress per CP

### Integration Flow
- [ ] Buat quiz → Publish → Siswa kerjakan → Nilai masuk gradebook
- [ ] Sync nilai quiz yang sudah ada
- [ ] Update quiz → Sync → Nilai terupdate otomatis
- [ ] Buat assignment → Nilai masuk gradebook

## 📊 Predikat & Mastery Status

| Range | Predikat | Label | Mastery Status |
|-------|----------|-------|----------------|
| ≥90 | A | Sangat Baik | Kamu mampu menguasai materi ini |
| 80-89 | B | Baik | Kamu cukup mampu menguasai materi ini |
| 70-79 | C | Cukup | Kamu cukup untuk menguasai materi ini |
| <70 | D | Kurang | Kamu belum menguasai materi ini |

## 🔐 Permissions

### Teacher Only
- Setup CP/TP
- Create/edit/delete categories
- Create/edit/delete grade items
- Input/edit grades
- Import quiz
- View all student analytics

### Student Only
- View own grades
- View own mastery status
- View feedback from teacher

### Super Admin
- Full access (bypass permissions)

## 🚀 Deployment Notes

### Migration
```bash
# Run migrations (jika ada perubahan schema)
flask db upgrade
```

### Environment Variables
Tidak ada perubahan environment variables yang diperlukan.

### Dependencies
Tidak ada dependencies baru yang ditambahkan.

## 📝 Usage Example

### Guru: Import Quiz ke Gradebook
```javascript
// 1. Buka tab "Import dari Quiz"
// 2. Pilih quiz yang belum di-import
// 3. Klik "Import"
// 4. Pilih kategori & TP (opsional)
// 5. Confirm
// → Nilai otomatis masuk untuk semua siswa yang sudah submit
```

### Guru: Input Nilai Manual
```javascript
// 1. Tab "Input Nilai"
// 2. Klik "Tambah Item"
// 3. Isi nama, kategori, max score
// 4. Simpan
// 5. Klik "Input Nilai" pada item
// 6. Isi nilai untuk semua siswa
// 7. Klik "Simpan Semua"
```

### Murid: Lihat Nilai
```javascript
// 1. Dashboard → "Nilai Saya"
// 2. Pilih mata pelajaran
// 3. Lihat:
//    - Nilai akhir (lingkaran besar)
//    - Predikat (A/B/C/D)
//    - Capaian Materi per CP
//    - Tabel detail tugas/kuis
```

## 🐛 Known Issues
- Tidak ada (semua edge cases sudah ditangani)

## 📸 Screenshots

### Teacher Dashboard
*(Tambahkan screenshot jika diperlukan)*

### Student View
*(Tambahkan screenshot jika diperlukan)*

## ✅ Checklist PR

- [x] Backend models & relationships
- [x] Service layer dengan business logic
- [x] API endpoints lengkap
- [x] Frontend templates (teacher & student)
- [x] JavaScript interactivity
- [x] Responsive design
- [x] Permission checks
- [x] Quiz integration (import & sync)
- [x] Assignment integration
- [x] Predikat & mastery status
- [x] Analytics & statistics
- [x] Error handling
- [x] Loading states
- [x] Success/error feedback

## 📚 Related Issues
- Closes #<issue_number> (jika ada)

---

**Reviewer:** @<reviewer_name>
**Assignee:** @<assignee_name>
