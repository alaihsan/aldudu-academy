# 📊 Rancangan Sistem Rasch Model untuk Gradebook

## 🎯 Prinsip Dasar

### Teori Klasik vs Rasch Model

| Aspek | Teori Klasik | Rasch Model |
|-------|--------------|-------------|
| **Kapan dihitung** | Instant (saat submit) | Batch (setelah threshold) |
| **Valid untuk** | 1 siswa | Minimal 30 siswa |
| **Output** | Score, Percentage | Ability (θ), Difficulty (δ) |
| **Visibilitas** | Langsung | Setelah analisis selesai |
| **Dependency** | Individual | Cohort-based |

---

## 🔄 Alur Kerja Hybrid

```
┌─────────────────────────────────────────────────────────────┐
│                    SISWA KERJAKAN QUIZ                      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  SISWA SUBMIT                                               │
│  ✅ Hitung score (Teori Klasik)                             │
│  ✅ Create GradeEntry (score, percentage)                   │
│  ✅ Update QuizSubmission                                   │
│  ✅ Notify guru & siswa                                     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  CHECK THRESHOLD FOR RASCH                                  │
│  ─────────────────────────────────────                      │
│  Cek apakah:                                                │
│  1. Jumlah siswa yang sudah submit ≥ 30?                   │
│  2. ATAU quiz sudah expired?                                │
│  3. ATAU guru manual trigger?                               │
│                                                             │
│  Jika BELUM → Tunggu (status: waiting)                     │
│  Jika SUDAH → Enqueue Rasch Analysis                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  BACKGROUND WORKER (Celery/RQ)                              │
│  ─────────────────────────────────────                      │
│  1. Update status: processing                               │
│  2. Fetch all submissions untuk quiz ini                    │
│  3. Build Person-Item Response Matrix                       │
│  4. Run JMLE Algorithm                                      │
│  5. Calculate:                                              │
│     - Person measures (θ) + SE + fit stats                  │
│     - Item measures (δ) + SE + fit stats                    │
│  6. Save to rasch_person_measures & rasch_item_measures    │
│  7. Update status: completed                                │
│  8. Notify guru: "Rasch analysis ready"                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 🗄️ Database Schema

### 1. Tabel `rasch_analyses`

```sql
CREATE TABLE rasch_analyses (
    id SERIAL PRIMARY KEY,
    course_id INTEGER NOT NULL REFERENCES courses(id),
    quiz_id INTEGER REFERENCES quizzes(id),  -- Nullable: bisa untuk multiple quiz
    assignment_id INTEGER REFERENCES assignments(id),
    
    -- Identification
    name VARCHAR(200) NOT NULL,
    analysis_type VARCHAR(50) NOT NULL,  -- 'quiz', 'assignment', 'combined'
    
    -- Status tracking
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
        -- pending: menunggu threshold
        -- waiting: menunggu siswa lain
        -- queued: masuk antrian worker
        -- processing: sedang dianalisis
        -- completed: selesai
        -- failed: gagal (lihat error_message)
        -- partial: sebagian selesai (misal: hanya item analysis)
    
    progress_percentage FLOAT DEFAULT 0,
    status_message VARCHAR(500),  -- Update progress real-time
    
    -- Timing
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    
    -- Threshold configuration
    min_persons INTEGER DEFAULT 30,  -- Minimal siswa untuk valid analysis
    auto_trigger BOOLEAN DEFAULT TRUE,  -- Auto-trigger saat threshold tercapai
    
    -- Rasch parameters
    convergence_threshold FLOAT DEFAULT 0.001,
    max_iterations INTEGER DEFAULT 100,
    
    -- Results summary
    num_persons INTEGER,
    num_items INTEGER,
    cronbach_alpha FLOAT,
    person_separation_index FLOAT,
    item_separation_index FLOAT,
    
    -- Metadata
    created_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_rasch_analyses_status ON rasch_analyses(status);
CREATE INDEX idx_rasch_analyses_quiz ON rasch_analyses(quiz_id);
CREATE INDEX idx_rasch_analyses_course ON rasch_analyses(course_id);
```

### 2. Tabel `rasch_person_measures`

```sql
CREATE TABLE rasch_person_measures (
    id SERIAL PRIMARY KEY,
    rasch_analysis_id INTEGER NOT NULL REFERENCES rasch_analyses(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES users(id),
    quiz_submission_id INTEGER REFERENCES quiz_submissions(id),
    
    -- Classical scores (untuk comparability)
    raw_score INTEGER NOT NULL,
    total_possible INTEGER NOT NULL,
    percentage FLOAT NOT NULL,
    
    -- Rasch ability measure
    theta FLOAT,              -- Ability (logit scale)
    theta_se FLOAT,           -- Standard error of theta
    theta_centered FLOAT,     -- Theta centered at 0 (untuk reporting)
    
    -- Fit statistics
    outfit_mnsq FLOAT,        -- Outfit mean square (expected ~1.0)
    outfit_zstd FLOAT,        -- Outfit z-standardized (-2 to +2 acceptable)
    infit_mnsq FLOAT,         -- Infit mean square
    infit_zstd FLOAT,         -- Infit z-standardized
    
    -- Fit interpretation
    fit_status VARCHAR(50),   -- 'well_fitted', 'underfit', 'overfit'
    fit_category VARCHAR(50), -- 'excellent', 'good', 'marginal', 'poor'
    
    -- Ability level interpretation
    ability_level VARCHAR(50), -- 'very_low', 'low', 'average', 'high', 'very_high'
    ability_percentile FLOAT,  -- Percentile rank among cohort
    
    -- Wright Map position
    wright_map_band VARCHAR(50),  -- For visualization grouping
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(rasch_analysis_id, student_id)
);

CREATE INDEX idx_rasch_person_student ON rasch_person_measures(student_id);
CREATE INDEX idx_rasch_person_theta ON rasch_person_measures(theta);
```

### 3. Tabel `rasch_item_measures`

```sql
CREATE TABLE rasch_item_measures (
    id SERIAL PRIMARY KEY,
    rasch_analysis_id INTEGER NOT NULL REFERENCES rasch_analyses(id) ON DELETE CASCADE,
    question_id INTEGER NOT NULL REFERENCES questions(id),
    
    -- Classical indices
    p_value FLOAT,            -- Difficulty index (proportion correct, 0-1)
    point_biserial FLOAT,     -- Discrimination index (-1 to +1)
    
    -- Rasch difficulty measure
    delta FLOAT,              -- Difficulty (logit scale)
    delta_se FLOAT,           -- Standard error of delta
    delta_centered FLOAT,     -- Delta centered at mean item difficulty
    
    -- Fit statistics
    outfit_mnsq FLOAT,
    outfit_zstd FLOAT,
    infit_mnsq FLOAT,
    infit_zstd FLOAT,
    
    -- Fit interpretation
    fit_status VARCHAR(50),
    fit_category VARCHAR(50),
    
    -- Difficulty interpretation
    difficulty_level VARCHAR(50),  -- 'very_easy', 'easy', 'moderate', 'difficult', 'very_difficult'
    difficulty_percentile FLOAT,
    
    -- Bloom Taxonomy integration
    bloom_level VARCHAR(50),  -- Cached from question_bloom_taxonomy
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(rasch_analysis_id, question_id)
);

CREATE INDEX idx_rasch_item_question ON rasch_item_measures(question_id);
CREATE INDEX idx_rasch_item_delta ON rasch_item_measures(delta);
```

### 4. Tabel `question_bloom_taxonomy`

```sql
CREATE TABLE question_bloom_taxonomy (
    id SERIAL PRIMARY KEY,
    question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    
    -- Bloom's Revised Taxonomy
    bloom_level VARCHAR(50) NOT NULL,
        -- 'remember': Mengingat informasi
        -- 'understand': Memahami konsep
        -- 'apply': Menerapkan konsep
        -- 'analyze': Menganalisis informasi
        -- 'evaluate': Mengevaluasi/menilai
        -- 'create': Mencipta/menghasilkan
    
    bloom_description TEXT,  -- Justifikasi pemilihan level
    verified_by INTEGER REFERENCES users(id),  -- Guru yang verifikasi
    verified_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(question_id)
);

COMMENT ON TABLE question_bloom_taxonomy IS 'Mapping taksonomi Bloom untuk setiap soal';
```

### 5. Tabel `rasch_threshold_logs`

```sql
CREATE TABLE rasch_threshold_logs (
    id SERIAL PRIMARY KEY,
    rasch_analysis_id INTEGER NOT NULL REFERENCES rasch_analyses(id),
    
    -- Threshold check
    check_type VARCHAR(50) NOT NULL,  -- 'auto', 'manual'
    num_submissions INTEGER NOT NULL,
    min_required INTEGER NOT NULL,
    threshold_met BOOLEAN NOT NULL,
    
    -- Decision
    action_taken VARCHAR(50),  -- 'queued', 'waiting', 'ignored'
    reason TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🔧 Modifikasi Model yang Sudah Ada

### `app/models/gradebook.py`

```python
class GradeItem(db.Model):
    # ... existing fields ...
    
    # Rasch integration
    enable_rasch_analysis: Mapped[bool] = mapped_column(
        db.Boolean, default=False, nullable=False
    )
    # Jika TRUE: quiz/assignment ini akan dianalisis dengan Rasch
    
    rasch_analysis_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey('rasch_analyses.id'), 
        nullable=True, index=True
    )
    # Link ke hasil Rasch analysis terbaru
    
    show_rasch_to_students: Mapped[bool] = mapped_column(
        db.Boolean, default=False, nullable=False
    )
    # Kontrol visibilitas: apakah siswa bisa lihat Rasch measures?
```

### `app/models/quiz.py`

```python
class Question(db.Model):
    # ... existing fields ...
    
    # Bloom Taxonomy relationship
    bloom_taxonomy: Mapped[Optional['QuestionBloomTaxonomy']] = relationship(
        'QuestionBloomTaxonomy', 
        back_populates='question', 
        uselist=False, 
        cascade='all, delete-orphan'
    )
```

---

## ⚙️ Background Worker Architecture

### `app/services/rasch_analysis_service.py`

```python
class RaschAnalysisService:
    """
    Service untuk menjalankan Rasch analysis
    """
    
    def __init__(self, analysis_id: int):
        self.analysis = RaschAnalysis.query.get(analysis_id)
    
    def check_threshold(self) -> bool:
        """
        Cek apakah threshold untuk Rasch analysis sudah terpenuhi
        """
        num_submissions = self.get_submission_count()
        min_required = self.analysis.min_persons
        
        # Log threshold check
        self.log_threshold_check(num_submissions, min_required)
        
        if num_submissions >= min_required:
            return True
        
        # Cek apakah quiz sudah expired
        if self.is_quiz_expired():
            return True
        
        return False
    
    def run_analysis(self):
        """
        Jalankan Rasch analysis (JMLE algorithm)
        """
        try:
            self.update_status('processing')
            
            # Step 1: Fetch data
            response_matrix = self.build_response_matrix()
            
            # Step 2: Initial estimates
            person_abilities, item_difficulties = self.initial_estimates(response_matrix)
            
            # Step 3: JMLE iterations
            for iteration in range(self.analysis.max_iterations):
                # Update item difficulties
                item_difficulties = self.estimate_item_difficulties(
                    response_matrix, person_abilities
                )
                
                # Update person abilities
                person_abilities = self.estimate_person_abilities(
                    response_matrix, item_difficulties
                )
                
                # Check convergence
                if self.check_convergence(person_abilities, item_difficulties):
                    break
            
            # Step 4: Calculate fit statistics
            fit_stats = self.calculate_fit_statistics(
                response_matrix, person_abilities, item_difficulties
            )
            
            # Step 5: Save results
            self.save_person_measures(person_abilities, fit_stats['persons'])
            self.save_item_measures(item_difficulties, fit_stats['items'])
            
            # Step 6: Update analysis summary
            self.update_analysis_summary()
            
            self.update_status('completed')
            
        except Exception as e:
            self.update_status('failed', str(e))
            raise
```

### `app/workers/rasch_worker.py`

```python
from celery import Celery
from app.services.rasch_analysis_service import RaschAnalysisService

celery = Celery('rasch_worker', broker='redis://localhost:6379/0')

@celery.task(bind=True, max_retries=3)
def run_rasch_analysis(self, analysis_id: int):
    """
    Celery task untuk menjalankan Rasch analysis
    """
    try:
        service = RaschAnalysisService(analysis_id)
        service.run_analysis()
        return {'status': 'completed', 'analysis_id': analysis_id}
    
    except Exception as e:
        # Retry dengan exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
```

---

## 📡 API Endpoints

### Threshold & Status

```python
# Cek status threshold untuk quiz
GET /api/quizzes/:id/rasch/threshold-status
Response:
{
  "quiz_id": 123,
  "total_students": 45,
  "submitted": 28,
  "min_required": 30,
  "threshold_met": false,
  "remaining": 2,
  "percentage": 62.2,
  "auto_trigger_enabled": true,
  "status": "waiting",
  "message": "Menunggu 2 siswa lagi untuk memulai analisis Rasch"
}

# Manual trigger Rasch analysis (bypass threshold)
POST /api/quizzes/:id/rasch/analyze
{
  "min_persons": 20  // Override default
}
```

### Analysis Management

```python
# List analyses untuk course
GET /api/courses/:id/rasch/analyses

# Get analysis detail dengan progress
GET /api/rasch/analyses/:id
Response:
{
  "id": 1,
  "name": "Quiz 1 Rasch Analysis",
  "status": "processing",
  "progress_percentage": 45.5,
  "status_message": "Calculating item difficulties (iteration 23/100)",
  "num_persons": null,
  "num_items": null,
  "started_at": "2026-03-21T10:30:00",
  "estimated_completion": "2026-03-21T10:35:00"
}

# Polling status
GET /api/rasch/analyses/:id/status
```

### Results

```python
# Person measures (ability)
GET /api/rasch/analyses/:id/persons
Response:
{
  "analysis_id": 1,
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

# Item measures (difficulty)
GET /api/rasch/analyses/:id/items
Response:
{
  "analysis_id": 1,
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

# Wright Map visualization data
GET /api/rasch/analyses/:id/wright-map
```

### Bloom Taxonomy

```python
# Set Bloom level untuk soal
POST /api/questions/:id/bloom
{
  "bloom_level": "analyze",
  "bloom_description": "Soal ini meminta siswa menganalisis hubungan sebab-akibat"
}

# Get Bloom distribution untuk quiz
GET /api/quizzes/:id/bloom-summary
Response:
{
  "quiz_id": 123,
  "total_questions": 30,
  "distribution": {
    "remember": {"count": 5, "percentage": 16.7},
    "understand": {"count": 8, "percentage": 26.7},
    "apply": {"count": 10, "percentage": 33.3},
    "analyze": {"count": 5, "percentage": 16.7},
    "evaluate": {"count": 2, "percentage": 6.7},
    "create": {"count": 0, "percentage": 0}
  },
  "cognitive_depth": "moderate"  # based on distribution
}
```

---

## 🎨 UI/UX Considerations

### Teacher Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│  Quiz: Mid Term Exam                                        │
│  ─────────────────────────────────────                      │
│  📊 Submissions: 28/45 (62%)                                │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Rasch Analysis Status                               │   │
│  │  ───────────────────────────────────────────────     │   │
│  │  ⏳ Waiting for 2 more students...                    │   │
│  │  ████████████████████░░░░░░░░ 62%                    │   │
│  │                                                       │   │
│  │  [Analyze Now] [Configure Threshold]                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Setelah selesai:                                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  ✅ Analysis Completed (Mar 21, 10:35)               │   │
│  │  ───────────────────────────────────────────────     │   │
│  │  • 45 students analyzed                              │   │
│  │  • 30 questions calibrated                            │   │
│  │  • Cronbach's α = 0.87 (Good reliability)            │   │
│  │                                                       │   │
│  │  [View Report] [Download PDF] [Export CSV]           │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Student View

```
┌─────────────────────────────────────────────────────────────┐
│  Hasil Quiz: Mid Term Exam                                  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Nilai Kamu: 85/100 (B - Baik)                      │   │
│  │  ───────────────────────────────────────────────     │   │
│  │                                                       │   │
│  │  📈 Kemampuan Kamu (Rasch Analysis)                  │   │
│  │  Level: HIGH (Top 22% di kelas)                      │   │
│  │  ───────────────────────────────────────────────     │   │
│  │                                                       │   │
│  │  Soal yang sulit untukmu:                            │   │
│  │  • Q15 (Analyze) - Difficulty: High                  │   │
│  │  • Q22 (Evaluate) - Difficulty: Very High            │   │
│  │                                                       │   │
│  │  Rekomendasi:                                        │   │
│  │  Fokus pada level kognitif 'analyze' dan 'evaluate'  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧪 Testing Strategy

### Unit Tests

```python
def test_rasch_threshold_check():
    """Test threshold logic"""
    analysis = create_analysis(min_persons=30)
    add_submissions(25)
    assert analysis.check_threshold() == False
    
    add_submissions(5)
    assert analysis.check_threshold() == True

def test_rasch_single_student_invalid():
    """Rasch should not run with single student"""
    analysis = create_analysis(min_persons=30)
    add_submissions(1)
    
    with pytest.raises(RaschValidationError):
        analysis.run_analysis()

def test_jMLE_convergence():
    """Test JMLE algorithm convergence"""
    response_matrix = create_response_matrix(50, 30)
    service = RaschAnalysisService()
    
    theta, delta = service.run_jmle(response_matrix)
    
    assert len(theta) == 50
    assert len(delta) == 30
    assert service.convergence_achieved == True
```

### Integration Tests

```python
def test_quiz_submission_triggers_rasch():
    """Full flow: submission → threshold check → Rasch analysis"""
    quiz = create_quiz(enable_rasch=True)
    
    # Submit 30 students
    for student in students[:30]:
        submit_quiz(quiz, student)
    
    # Should auto-trigger Rasch
    analysis = RaschAnalysis.query.filter_by(quiz_id=quiz.id).first()
    assert analysis is not None
    assert analysis.status == 'completed'
```

---

## 📋 Checklist Implementasi

### Phase 1: Core Infrastructure
- [ ] Buat migration SQL untuk semua tabel
- [ ] Buat SQLAlchemy models
- [ ] Setup Celery worker
- [ ] Implementasi threshold checking logic

### Phase 2: Rasch Algorithm
- [ ] Implementasi JMLE algorithm
- [ ] Implementasi fit statistics (infit/outfit)
- [ ] Implementasi ability/difficulty estimation
- [ ] Save results ke database

### Phase 3: Integration
- [ ] Hook ke quiz submission flow
- [ ] Auto-trigger mechanism
- [ ] Manual trigger API
- [ ] Status polling endpoint

### Phase 4: Bloom Taxonomy
- [ ] UI untuk set Bloom level
- [ ] Bloom distribution analysis
- [ ] Correlation: Bloom vs Difficulty

### Phase 5: Reporting
- [ ] Teacher dashboard
- [ ] Student view
- [ ] Wright Map visualization
- [ ] PDF export

---

## 🎯 Kesimpulan

### Jawaban untuk Pertanyaan Anda:

**Q: Apakah valid menilai satu anak saja dengan Rasch Model?**

**A: TIDAK VALID.** Rasch Model membutuhkan minimal **30 siswa** untuk estimasi yang reliable.

**Solusi yang saya tawarkan:**

1. **Teori Klasik**: Instant, untuk 1 siswa → Langsung masuk gradebook
2. **Rasch Model**: Batch, tunggu threshold → Analisis terpisah di background

**Keuntungan:**
- ✅ Siswa dapat nilai langsung (teori klasik)
- ✅ Guru dapat insight mendalam (Rasch) setelah threshold
- ✅ Validitas pengukuran terjaga
- ✅ Flexibility: guru bisa manual trigger jika butuh cepat

---

Apakah Anda ingin saya mulai implementasikan:
1. **Migration SQL** untuk tabel-tabel baru?
2. **SQLAlchemy models**?
3. **Rasch algorithm** (JMLE) dari scratch atau pakai library existing (misal: `pyrasch`)?
