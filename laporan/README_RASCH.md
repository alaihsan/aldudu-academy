# 📊 Panduan Lengkap Rasch Model - Aldudu Academy

## 📋 Daftar Isi

1. [Pendahuluan](#pendahuluan)
2. [Konsep Dasar](#konsep-dasar)
3. [Instalasi & Konfigurasi](#instalasi--konfigurasi)
4. [Cara Menggunakan](#cara-menggunakan)
5. [API Reference](#api-reference)
6. [Interpretasi Hasil](#interpretasi-hasil)
7. [Troubleshooting](#troubleshooting)
8. [FAQ](#faq)

---

## 🎯 Pendahuluan

### Apa itu Rasch Model?

**Rasch Model** adalah teori pengukuran modern yang dikembangkan oleh Georg Rasch (1960) untuk mengukur kemampuan person dan kesulitan item dalam skala yang sama (logit scale).

Berbeda dengan **Teori Klasik** yang menghasilkan nilai persentase (0-100), Rasch Model menghasilkan:
- **Ability (θ)**: Kemampuan siswa dalam skala logit
- **Difficulty (δ)**: Tingkat kesulitan soal dalam skala logit

### Mengapa Rasch Model?

| Aspek | Teori Klasik | Rasch Model |
|-------|--------------|-------------|
| **Skor** | Persentase (0-100) | Ability (θ) dalam logit |
| **Sulit soal** | P-value (% benar) | Difficulty (δ) dalam logit |
| **Sample dependent** | ✅ Ya | ❌ Tidak (item-free) |
| **Test dependent** | ✅ Ya | ❌ Tidak (person-free) |
| **Minimum siswa** | 1 | 30 (recommended) |
| **Processing** | Instant | Batch (background) |

### Kapan Menggunakan Rasch?

**Gunakan Rasch Model untuk:**
- ✅ Ujian tengah semester (banyak siswa)
- ✅ Ujian akhir semester
- ✅ Quiz dengan ≥30 siswa
- ✅ Analisis kualitas soal
- ✅ Validasi instrumen penilaian

**Tidak perlu Rasch untuk:**
- ❌ Quiz harian dengan <10 siswa
- ❌ Tugas individu
- ❌ Penilaian formatif cepat

---

## 📚 Konsep Dasar

### 1. Rasch Model Formula

```
log(P_ni / (1 - P_ni)) = B_n - D_i

dimana:
- P_ni = Probabilitas siswa n menjawab benar soal i
- B_n = Ability siswa n (theta, θ)
- D_i = Difficulty soal i (delta, δ)
```

### 2. Logit Scale

```
-3    -2    -1     0     1     2     3
|-----|-----|-----|-----|-----|-----|
Very  Low        Avg       High Very
Low                          High

θ > 0  = Siswa di atas rata-rata
θ < 0  = Siswa di bawah rata-rata
δ > 0  = Soal di atas rata-rata (sulit)
δ < 0  = Soal di bawah rata-rata (mudah)
```

### 3. Fit Statistics

| Statistic | Range Ideal | Interpretasi |
|-----------|-------------|--------------|
| **Outfit MNSQ** | 0.8 - 1.2 | Respons unexpected (outlier) |
| **Infit MNSQ** | 0.8 - 1.2 | Respons expected (pattern) |
| **ZSTD** | -2.0 to +2.0 | Signifikansi statistik |

### 4. Wright Map

Visualisasi distribusi person ability dan item difficulty dalam satu peta vertikal:

```
Logit
  2.0 |           ● S1 (Very High)
  1.5 |        ● S2
  1.0 |     ● S3      ■ Q5 (Difficult)
  0.5 |  ● S4    ■ Q4
  0.0 |────────────■ Q3 (Average)───────── Mean
 -0.5 |     ■ Q2
 -1.0 |  ● S5   ■ Q1 (Easy)
 -1.5 | ● S6
 -2.0 | ● S7 (Very Low)

● = Student ability
■ = Item difficulty
```

---

## ⚙️ Instalasi & Konfigurasi

### 1. Install Dependencies

```bash
# Install semua requirements
pip install -r requirements.txt

# Atau install manual
pip install celery==5.6.2 redis==7.3.0
```

### 2. Run Migration

```bash
# Run migration database
python scripts\run_rasch_migration.py
```

### 3. Setup Redis (Untuk Celery)

**Windows:**
```bash
# Download Redis untuk Windows dari:
# https://github.com/microsoftarchive/redis/releases

# Atau gunakan Docker
docker run -d -p 6379:6379 redis:latest
```

**Linux/Mac:**
```bash
# Install
sudo apt-get install redis-server  # Ubuntu/Debian
brew install redis  # macOS

# Start
redis-server
```

### 4. Konfigurasi Environment

Tambahkan ke `.env`:

```bash
# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Rasch Default Settings
RASCH_DEFAULT_MIN_PERSONS=30
RASCH_DEFAULT_CONVERGENCE=0.001
RASCH_DEFAULT_MAX_ITERATIONS=100
```

### 5. Start Services

```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start Celery Worker
python run_worker.py

# Terminal 3: Start Flask App
python run.py
```

---

## 🚀 Cara Menggunakan

### Step 1: Enable Rasch Analysis

**Melalui Database:**
```sql
UPDATE grade_items 
SET enable_rasch_analysis = TRUE 
WHERE quiz_id = 123;
```

**Melalui Code (saat membuat GradeItem):**
```python
from app.models.gradebook import GradeItem

grade_item = GradeItem(
    name="Mid Term Exam",
    category_id=1,
    max_score=100,
    course_id=1,
    quiz_id=123,
    enable_rasch_analysis=True,  # Enable Rasch
    show_rasch_to_students=True  # Optional: show to students
)
db.session.add(grade_item)
db.session.commit()
```

### Step 2: Students Take Quiz

Siswa mengerjakan quiz seperti biasa. Setiap submission akan:
1. Auto-sync ke Gradebook (Teori Klasik - instant)
2. Auto-trigger threshold check untuk Rasch

```python
# Di quiz.py - auto-trigger setelah submit
from app.services.rasch_threshold_service import RaschThresholdService

threshold_service = RaschThresholdService()
threshold_met, message = threshold_service.check_and_trigger(
    quiz_id=quiz.id,
    submission_id=submission.id,
    check_type='auto'
)
```

### Step 3: Monitor Threshold Progress

**API:**
```bash
curl http://localhost:5000/api/rasch/quizzes/123/threshold-status
```

**Response:**
```json
{
  "success": true,
  "quiz_id": 123,
  "total_students": 45,
  "submitted": 28,
  "min_required": 30,
  "threshold_met": false,
  "remaining": 2,
  "percentage": 93.3,
  "status": "waiting",
  "message": "Menunggu 2 siswa lagi untuk memulai analisis Rasch"
}
```

### Step 4: Analysis Auto-Trigger

Saat threshold terpenuhi (≥30 submissions):
- Status berubah: `waiting` → `queued` → `processing` → `completed`
- Celery worker menjalankan JMLE algorithm
- Hasil disimpan ke database

### Step 5: Manual Trigger (Optional)

Jika ingin analisis sebelum threshold:

```bash
curl -X POST http://localhost:5000/api/rasch/quizzes/123/analyze \
  -H "Content-Type: application/json" \
  -d '{"min_persons": 20}'
```

### Step 6: View Results

**Person Measures (Ability θ):**
```bash
curl http://localhost:5000/api/rasch/analyses/1/persons
```

**Item Measures (Difficulty δ):**
```bash
curl http://localhost:5000/api/rasch/analyses/1/items
```

**Wright Map Data:**
```bash
curl http://localhost:5000/api/rasch/analyses/1/wright-map
```

---

## 📡 API Reference

### Base URL
```
/api/rasch
```

### Threshold & Trigger

#### GET `/quizzes/:id/threshold-status`
Check threshold progress.

**Response:**
```json
{
  "success": true,
  "submitted": 28,
  "min_required": 30,
  "threshold_met": false,
  "remaining": 2,
  "percentage": 93.3,
  "status": "waiting"
}
```

#### POST `/quizzes/:id/analyze`
Manual trigger analysis.

**Request:**
```json
{
  "min_persons": 20
}
```

### Analysis Management

#### GET `/analyses`
List analyses.

**Query Params:**
- `course_id`: Filter by course
- `quiz_id`: Filter by quiz
- `status`: Filter by status (pending, processing, completed, failed)

#### GET `/analyses/:id`
Get analysis detail.

**Response:**
```json
{
  "success": true,
  "analysis": {
    "id": 1,
    "name": "Mid Term Exam Analysis",
    "status": "completed",
    "progress_percentage": 100,
    "num_persons": 45,
    "num_items": 30,
    "cronbach_alpha": 0.87,
    "completed_at": "2026-03-21T10:35:00"
  }
}
```

#### GET `/analyses/:id/status`
Poll analysis status.

**Response:**
```json
{
  "success": true,
  "status": "processing",
  "progress_percentage": 45.5,
  "status_message": "Iteration 23/100",
  "is_complete": false
}
```

### Results

#### GET `/analyses/:id/persons`
Get person measures.

**Response:**
```json
{
  "success": true,
  "persons": [
    {
      "student_id": 101,
      "student_name": "Ahmad",
      "raw_score": 85,
      "percentage": 85.0,
      "theta": 1.23,
      "theta_se": 0.15,
      "ability_level": "high",
      "ability_percentile": 78.5,
      "fit_status": "well_fitted",
      "outfit_mnsq": 0.95,
      "infit_mnsq": 1.02
    }
  ]
}
```

#### GET `/analyses/:id/items`
Get item measures.

**Response:**
```json
{
  "success": true,
  "items": [
    {
      "question_id": 1,
      "question_text": "Apa ibu kota Indonesia?",
      "delta": -1.5,
      "difficulty_level": "easy",
      "p_value": 0.85,
      "point_biserial": 0.42,
      "bloom_level": "remember",
      "fit_status": "well_fitted"
    }
  ]
}
```

#### GET `/analyses/:id/wright-map`
Get Wright Map visualization data.

**Response:**
```json
{
  "success": true,
  "map_data": {
    "person_distribution": [
      {"level": "very_high", "range": "> 2.0", "count": 5},
      {"level": "high", "range": "0.5 to 2.0", "count": 10},
      {"level": "average", "range": "-0.5 to 0.5", "count": 20},
      {"level": "low", "range": "-2.0 to -0.5", "count": 8},
      {"level": "very_low", "range": "< -2.0", "count": 2}
    ],
    "mean_person_theta": 0.25,
    "sd_person": 1.2
  }
}
```

#### GET `/quizzes/:id/bloom-summary`
Get Bloom taxonomy distribution.

**Response:**
```json
{
  "success": true,
  "distribution": {
    "remember": {"count": 5, "percentage": 16.7},
    "understand": {"count": 8, "percentage": 26.7},
    "apply": {"count": 10, "percentage": 33.3},
    "analyze": {"count": 5, "percentage": 16.7},
    "evaluate": {"count": 2, "percentage": 6.7}
  },
  "cognitive_depth": "moderate"
}
```

---

## 📊 Interpretasi Hasil

### 1. Ability Level (θ)

| Theta Range | Level | Label | Interpretasi |
|-------------|-------|-------|--------------|
| θ > 2.0 | Very High | Sangat Tinggi | Top 5% performers |
| 0.5 < θ ≤ 2.0 | High | Tinggi | Above average |
| -0.5 ≤ θ ≤ 0.5 | Average | Sedang | Typical performance |
| -2.0 ≤ θ < -0.5 | Low | Rendah | Below average |
| θ < -2.0 | Very Low | Sangat Rendah | Needs intervention |

### 2. Difficulty Level (δ)

| Delta Range | Level | Label | P-Value |
|-------------|-------|-------|---------|
| δ < -2.0 | Very Easy | Sangat Mudah | > 0.90 |
| -2.0 ≤ δ < -0.5 | Easy | Mudah | 0.70 - 0.90 |
| -0.5 ≤ δ ≤ 0.5 | Moderate | Sedang | 0.30 - 0.70 |
| 0.5 < δ ≤ 2.0 | Difficult | Sulit | 0.10 - 0.30 |
| δ > 2.0 | Very Difficult | Sangat Sulit | < 0.10 |

### 3. Fit Statistics

#### Outfit MNSQ (Unweighted)
- Sensitif terhadap unexpected responses (outliers)
- Deteksi siswa yang menjawab benar soal sulit tapi salah soal mudah

#### Infit MNSQ (Weighted)
- Sensitif terhadap pattern respons
- Deteksi respons yang terlalu predictable (cheating?)

#### Interpretasi MNSQ

| MNSQ Range | Category | Action |
|------------|----------|--------|
| 0.8 - 1.2 | Excellent | Keep item/person |
| 0.6 - 0.8 | Good | Review item |
| 1.2 - 1.4 | Marginal | Consider revision |
| < 0.5 or > 1.5 | Poor | Remove/revise item |

### 4. Reliability Indices

#### Cronbach's Alpha
| Alpha | Reliability |
|-------|-------------|
| ≥ 0.9 | Excellent |
| 0.8 - 0.9 | Good |
| 0.7 - 0.8 | Acceptable |
| 0.6 - 0.7 | Questionable |
| < 0.6 | Poor |

#### Person Separation Index (PSI)
- ≥ 2.0: Good separation (distinguish 3 levels)
- ≥ 3.0: Excellent separation (distinguish 4+ levels)

### 5. Point-Biserial

| Range | Discrimination |
|-------|----------------|
| ≥ 0.40 | Very good |
| 0.30 - 0.39 | Reasonably good |
| 0.20 - 0.29 | Marginal |
| < 0.20 | Poor (consider removing) |

---

## 🔧 Troubleshooting

### 1. Analysis Tidak Auto-Trigger

**Problem:** Threshold terpenuhi tapi analisis tidak mulai.

**Check:**
```bash
# Check Celery worker running
python run_worker.py

# Check Redis running
redis-cli ping  # Should return: PONG

# Check logs
tail -f logs/celery.log
```

**Solution:**
```bash
# Restart Celery
# Ctrl+C to stop
python run_worker.py
```

### 2. Analysis Failed

**Problem:** Status = `failed`

**Check:**
```bash
curl http://localhost:5000/api/rasch/analyses/1/status
```

**Response:**
```json
{
  "status": "failed",
  "error_message": "No submissions found"
}
```

**Solution:**
- Pastikan ada submissions untuk quiz
- Check `min_persons` tidak terlalu tinggi

### 3. Convergence Tidak Tercapai

**Problem:** Status = `partial` setelah max iterations

**Causes:**
- Data terlalu sedikit (<10 students)
- Response pattern ekstrem (semua benar/salah)
- Item terlalu mudah/sulit

**Solution:**
```sql
-- Increase max iterations
UPDATE rasch_analyses 
SET max_iterations = 200 
WHERE id = 1;

-- Or relax convergence threshold
UPDATE rasch_analyses 
SET convergence_threshold = 0.01 
WHERE id = 1;
```

### 4. Redis Connection Error

**Problem:** `redis.exceptions.ConnectionError`

**Solution:**
```bash
# Check Redis running
redis-cli ping

# Start Redis
redis-server

# Or use Docker
docker run -d -p 6379:6379 redis:latest
```

### 5. Celery Task Stuck

**Problem:** Task status `queued` tapi tidak `processing`

**Solution:**
```bash
# Check worker logs
# Ctrl+C worker, then restart
python run_worker.py

# Purge stuck tasks (in Python shell)
from app import create_app
app = create_app()
with app.app_context():
    from app.celery_app import make_celery
    celery = make_celery(app)
    celery.control.purge()
```

---

## ❓ FAQ

### Q: Berapa minimal siswa untuk Rasch?
**A:** Minimal 30 siswa untuk hasil yang reliable. Bisa lebih rendah (20) untuk kelas kecil, tapi interpretasi harus lebih hati-hati.

### Q: Apakah Rasch wajib untuk semua quiz?
**A:** Tidak. Gunakan untuk quiz penting (mid term, final exam). Quiz harian tidak perlu Rasch.

### Q: Berapa lama proses analisis?
**A:** Tergantung jumlah siswa dan soal:
- 30 students × 20 questions: ~1-2 menit
- 100 students × 50 questions: ~5-10 menit

### Q: Apakah siswa bisa lihat hasil Rasch?
**A:** Tergantung setting `show_rasch_to_students`. Jika TRUE, siswa bisa lihat ability level dan percentile.

### Q: Apa bedanya Outfit dan Infit?
**A:** 
- **Outfit**: Deteksi unexpected responses (outlier)
- **Infit**: Deteksi pattern respons (cheating detection)

### Q: Bagaimana jika item misfit?
**A:** Review item tersebut:
- MNSQ > 1.5: Item ambigu, pertimbangkan revisi
- MNSQ < 0.5: Item terlalu predictable, pertimbangkan remove

### Q: Apakah Rasch bisa untuk tugas (assignment)?
**A:** Ya, menggunakan **Partial Credit Model** untuk rubric-based grading. (Coming soon)

### Q: Bagaimana cara export hasil Rasch?
**A:** Gunakan API endpoints untuk export ke Excel/PDF:
```python
import requests
import pandas as pd

# Get person measures
response = requests.get('http://localhost:5000/api/rasch/analyses/1/persons')
data = response.json()

# Export to Excel
df = pd.DataFrame(data['persons'])
df.to_excel('rasch_results.xlsx', index=False)
```

---

## 📚 Referensi

1. Rasch, G. (1960). *Probabilistic Models for Some Intelligence and Attainment Tests*. Copenhagen: Danish Institute for Educational Research.
2. Bond, T. G., & Fox, C. M. (2015). *Applying the Rasch Model: Fundamental Measurement in the Human Sciences* (3rd ed.). Routledge.
3. Wright, B. D., & Masters, G. N. (1982). *Rating Scale Analysis*. Chicago: MESA Press.
4. Fischer, G. H., & Molenaar, I. W. (1995). *Rasch Models: Foundations, Recent Developments, and Applications*. Springer.

---

**Dokumentasi ini dibuat untuk Aldudu Academy**  
**Version:** 1.0  
**Last Updated:** 2026-03-21
