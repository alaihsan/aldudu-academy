# 📊 Implementasi Rasch Model - Aldudu Academy

## 📋 Daftar Isi

1. [Pendahuluan](#pendahuluan)
2. [Arsitektur Sistem](#arsitektur-sistem)
3. [Database Schema](#database-schema)
4. [Alur Kerja](#alur-kerja)
5. [Implementasi Detail](#implementasi-detail)
6. [Testing](#testing)
7. [Deployment](#deployment)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 Pendahuluan

### Latar Belakang

Aldudu Academy mengimplementasikan **Rasch Model** untuk menyediakan analisis penilaian yang lebih advanced dibandingkan Teori Klasik. Rasch Model memberikan:

1. **Pengukuran Objektif**: Ability siswa dan difficulty soal diukur dalam skala yang sama (logit)
2. **Item-Free Measurement**: Ability siswa tidak tergantung pada test tertentu
3. **Person-Free Calibration**: Difficulty soal tidak tergantung pada grup siswa tertentu
4. **Quality Control**: Fit statistics untuk mendeteksi soal atau siswa yang tidak sesuai pattern

### Tujuan Implementasi

1. Menyediakan alternatif pengukuran selain nilai persentase klasik
2. Memberikan insight tentang kualitas soal (difficulty, discrimination)
3. Memberikan insight tentang kemampuan siswa dalam skala yang terkalibrasi
4. Mendeteksi soal yang bermasalah melalui fit statistics
5. Memetakan distribusi kemampuan siswa dan kesulitan soal (Wright Map)

### Ruang Lingkup

Implementasi mencakup:
- Backend: JMLE algorithm, threshold checking, background processing
- Frontend: Dashboard untuk guru, student view untuk ability tracking
- API: 12 endpoints untuk programmatic access
- Database: 6 tabel baru, 3 kolom tambahan

---

## 🏗️ Arsitektur Sistem

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Student submits quiz                     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Quiz Submission Handler                        │
│  - Calculate classical score (instant)                      │
│  - Create GradeEntry                                        │
│  - Trigger threshold check                                  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│           RaschThresholdService                             │
│  - Count submissions                                        │
│  - Check if ≥ threshold (default: 30)                       │
│  - If YES → Enqueue Celery task                             │
│  - If NO  → Update status "waiting"                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Celery Worker (Background)                     │
│  - Fetch all submissions                                    │
│  - Build response matrix                                    │
│  - Run JMLE algorithm                                       │
│  - Calculate fit statistics                                 │
│  - Save results to database                                 │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Results Available                              │
│  - Person measures (ability θ)                              │
│  - Item measures (difficulty δ)                             │
│  - Wright Map data                                          │
│  - Bloom taxonomy correlation                               │
└─────────────────────────────────────────────────────────────┘
```

### Component Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                        Flask App                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Blueprints                                            │ │
│  │  ├── rasch (API)           ├── rasch_dashboard (UI)   │ │
│  │  └── quiz (submission)     └── gradebook (integration)│ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Services                                              │ │
│  │  ├── RaschAnalysisService (JMLE)                      │ │
│  │  └── RaschThresholdService (Auto-trigger)             │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Models                                                │ │
│  │  ├── RaschAnalysis, RaschPersonMeasure                │ │
│  │  ├── RaschItemMeasure, QuestionBloomTaxonomy          │ │
│  │  └── GradeItem (updated)                              │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                    Celery Worker                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Tasks                                                 │ │
│  │  └── rasch_analysis (async processing)                │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                       Redis Broker                           │
│  - Message queue untuk Celery tasks                         │
│  - Result backend untuk task status                         │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                     MySQL Database                           │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Rasch Tables                                          │ │
│  │  ├── rasch_analyses                                    │ │
│  │  ├── rasch_person_measures                             │ │
│  │  ├── rasch_item_measures                               │ │
│  │  ├── rasch_threshold_logs                              │ │
│  │  ├── rasch_rating_scales                               │ │
│  │  └── question_bloom_taxonomy                           │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

---

## 🗄️ Database Schema

### Entity Relationship Diagram

```
┌─────────────────────┐
│   rasch_analyses    │
├─────────────────────┤
│ id (PK)             │
│ course_id (FK)      │◄────┐
│ quiz_id (FK)        │     │
│ assignment_id (FK)  │     │
│ name                │     │
│ analysis_type       │     │
│ status              │     │
│ min_persons         │     │
│ num_persons         │     │
│ num_items           │     │
│ cronbach_alpha      │     │
│ created_by (FK)     │     │
└─────────────────────┘     │
        │                   │
        │                   │
        ▼                   │
┌─────────────────────┐     │
│ rasch_person_       │     │
│ measures            │     │
├─────────────────────┤     │
│ id (PK)             │     │
│ rasch_analysis_id   │─────┘
│ student_id (FK)     │
│ raw_score           │
│ percentage          │
│ theta               │
│ theta_se            │
│ outfit_mnsq         │
│ infit_mnsq          │
│ fit_status          │
│ ability_level       │
└─────────────────────┘

        │
        ▼
┌─────────────────────┐
│ rasch_item_         │
│ measures            │
├─────────────────────┤
│ id (PK)             │
│ rasch_analysis_id   │
│ question_id (FK)    │
│ p_value             │
│ delta               │
│ difficulty_level    │
│ bloom_level         │
│ outfit_mnsq         │
│ infit_mnsq          │
│ fit_status          │
└─────────────────────┘
```

### Tabel Detail

#### 1. rasch_analyses

```sql
CREATE TABLE rasch_analyses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT NOT NULL,
    quiz_id INT NULL,
    assignment_id INT NULL,
    name VARCHAR(200) NOT NULL,
    analysis_type ENUM('quiz', 'assignment', 'combined') NOT NULL,
    status ENUM('pending', 'waiting', 'queued', 'processing', 
                'completed', 'failed', 'partial') NOT NULL DEFAULT 'pending',
    progress_percentage DECIMAL(5,2) DEFAULT 0,
    status_message VARCHAR(500) NULL,
    started_at DATETIME NULL,
    completed_at DATETIME NULL,
    error_message TEXT NULL,
    min_persons INT DEFAULT 30 NOT NULL,
    auto_trigger BOOLEAN DEFAULT TRUE NOT NULL,
    convergence_threshold DECIMAL(10,8) DEFAULT 0.001,
    max_iterations INT DEFAULT 100,
    num_persons INT NULL,
    num_items INT NULL,
    cronbach_alpha DECIMAL(5,4) NULL,
    person_separation_index DECIMAL(5,4) NULL,
    item_separation_index DECIMAL(5,4) NULL,
    created_by INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

**Field Descriptions:**
- `status`: Tracking progress analisis
- `min_persons`: Threshold minimal siswa (default 30)
- `progress_percentage`: Progress 0-100% untuk UI
- `cronbach_alpha`: Reliabilitas internal consistency
- `person_separation_index`: Daya beda kemampuan siswa
- `item_separation_index`: Daya beda kesulitan soal

#### 2. rasch_person_measures

```sql
CREATE TABLE rasch_person_measures (
    id INT AUTO_INCREMENT PRIMARY KEY,
    rasch_analysis_id INT NOT NULL,
    student_id INT NOT NULL,
    quiz_submission_id INT NULL,
    raw_score INT NOT NULL,
    total_possible INT NOT NULL,
    percentage DECIMAL(5,2) NOT NULL,
    theta DECIMAL(10,6) NULL,
    theta_se DECIMAL(10,6) NULL,
    theta_centered DECIMAL(10,6) NULL,
    outfit_mnsq DECIMAL(10,6) NULL,
    outfit_zstd DECIMAL(10,6) NULL,
    infit_mnsq DECIMAL(10,6) NULL,
    infit_zstd DECIMAL(10,6) NULL,
    fit_status ENUM('well_fitted', 'underfit', 'overfit') NULL,
    fit_category ENUM('excellent', 'good', 'marginal', 'poor') NULL,
    ability_level ENUM('very_low', 'low', 'average', 'high', 'very_high') NULL,
    ability_percentile DECIMAL(5,2) NULL,
    wright_map_band VARCHAR(50) NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_rasch_person (rasch_analysis_id, student_id)
);
```

**Field Descriptions:**
- `theta`: Ability measure dalam logit scale
- `theta_se`: Standard error of theta (precision)
- `outfit_mnsq`: Unweighted fit statistic (sensitive to outliers)
- `infit_mnsq`: Weighted fit statistic (sensitive to pattern)
- `fit_status`: Interpretasi kualitas fit
- `ability_level`: Kategori kemampuan berdasarkan theta

#### 3. rasch_item_measures

```sql
CREATE TABLE rasch_item_measures (
    id INT AUTO_INCREMENT PRIMARY KEY,
    rasch_analysis_id INT NOT NULL,
    question_id INT NOT NULL,
    p_value DECIMAL(5,4) NULL,
    point_biserial DECIMAL(5,4) NULL,
    delta DECIMAL(10,6) NULL,
    delta_se DECIMAL(10,6) NULL,
    delta_centered DECIMAL(10,6) NULL,
    outfit_mnsq DECIMAL(10,6) NULL,
    outfit_zstd DECIMAL(10,6) NULL,
    infit_mnsq DECIMAL(10,6) NULL,
    infit_zstd DECIMAL(10,6) NULL,
    fit_status ENUM('well_fitted', 'underfit', 'overfit') NULL,
    fit_category ENUM('excellent', 'good', 'marginal', 'poor') NULL,
    difficulty_level ENUM('very_easy', 'easy', 'moderate', 
                          'difficult', 'very_difficult') NULL,
    difficulty_percentile DECIMAL(5,2) NULL,
    bloom_level ENUM('remember', 'understand', 'apply', 
                     'analyze', 'evaluate', 'create') NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_rasch_item (rasch_analysis_id, question_id)
);
```

**Field Descriptions:**
- `delta`: Difficulty measure dalam logit scale
- `p_value`: Classical difficulty (proportion correct)
- `point_biserial`: Discrimination index
- `bloom_level`: Cached dari question_bloom_taxonomy

#### 4. question_bloom_taxonomy

```sql
CREATE TABLE question_bloom_taxonomy (
    id INT AUTO_INCREMENT PRIMARY KEY,
    question_id INT NOT NULL UNIQUE,
    bloom_level VARCHAR(50) NOT NULL,
    bloom_description TEXT NULL,
    verified_by INT NULL,
    verified_at DATETIME NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

**Bloom Levels:**
- `remember`: Mengingat informasi
- `understand`: Memahami konsep
- `apply`: Menerapkan konsep
- `analyze`: Menganalisis informasi
- `evaluate`: Mengevaluasi/menilai
- `create`: Mencipta/menghasilkan

---

## 🔄 Alur Kerja

### 1. Quiz Submission Flow

```
1. Student membuka quiz
2. Student menjawab soal
3. Student submit quiz
   ↓
4. Backend menghitung classical score
5. Backend membuat GradeEntry
6. Backend trigger threshold check
   ↓
7. IF submissions >= threshold:
      - Create/update RaschAnalysis
      - Status: queued
      - Enqueue Celery task
   ELSE:
      - Status: waiting
      - Update progress percentage
8. Return score ke student
```

### 2. Rasch Analysis Flow

```
1. Celery worker menerima task
2. Fetch semua submissions untuk quiz
3. Build response matrix (student × item)
4. Initialize ability & difficulty
   - Ability: based on raw score
   - Difficulty: based on p-value
5. Run JMLE iterations:
   a. Update item difficulties
   b. Update person abilities
   c. Check convergence
   d. Repeat hingga converge/max iterations
6. Calculate fit statistics
7. Calculate reliability indices
8. Save results ke database
9. Update status: completed
```

### 3. Dashboard Access Flow

```
Teacher:
1. Navigate to Gradebook
2. Click "Rasch Dashboard"
3. View quiz list dengan Rasch enabled
4. View threshold progress
5. Click "Lihat Hasil" untuk analysis completed
6. Navigate through 5 tabs:
   - Overview
   - Wright Map
   - Person Measures
   - Item Measures
   - Bloom Taxonomy

Student:
1. Navigate to My Grades
2. Click "Kemampuan Saya"
3. View latest ability measure
4. View percentile rank
5. Read recommendations
6. View history table
```

---

## 💻 Implementasi Detail

### JMLE Algorithm Implementation

**File:** `app/services/rasch_analysis_service.py`

**Core Algorithm:**

```python
def run_jmle(self):
    """
    Joint Maximum Likelihood Estimation
    
    Formula:
    log(P_ni / (1 - P_ni)) = B_n - D_i
    
    dimana:
    - P_ni = Probabilitas siswa n menjawab benar soal i
    - B_n = Ability siswa n (theta)
    - D_i = Difficulty soal i (delta)
    """
    prev_abilities = self.abilities.copy()
    prev_difficulties = self.difficulties.copy()
    
    for iteration in range(1, self.max_iterations + 1):
        # Step 1: Update item difficulties
        self._update_item_difficulties()
        
        # Step 2: Update person abilities
        self._update_person_abilities()
        
        # Step 3: Check convergence
        ability_change = self._calculate_max_change(
            prev_abilities, self.abilities
        )
        difficulty_change = self._calculate_max_change(
            prev_difficulties, self.difficulties
        )
        
        max_change = max(ability_change, difficulty_change)
        
        if max_change < self.convergence_threshold:
            return True  # Converged
        
        prev_abilities = self.abilities.copy()
        prev_difficulties = self.difficulties.copy()
    
    return False  # Did not converge
```

**Probability Calculation:**

```python
def _probability(self, theta, delta):
    """
    Rasch formula:
    P(X=1) = exp(theta - delta) / (1 + exp(theta - delta))
    """
    logit = theta - delta
    
    # Avoid overflow
    if logit > 20:
        return 1.0
    elif logit < -20:
        return 0.0
    
    exp_logit = math.exp(logit)
    return exp_logit / (1 + exp_logit)
```

**Newton-Raphson Update:**

```python
def _update_item_difficulties(self):
    """Update item difficulties menggunakan Newton-Raphson"""
    for question_id in self.questions:
        responses = []
        abilities_for_item = []
        
        # Collect responses for this item
        for student_id in self.students:
            if (student_id, question_id) in self.response_matrix:
                responses.append(self.response_matrix[(student_id, question_id)])
                abilities_for_item.append(self.abilities[student_id])
        
        delta = self.difficulties[question_id]
        
        # Newton-Raphson iteration
        for _ in range(10):
            sum_expected = 0
            sum_variance = 0
            sum_observed = sum(responses)
            
            for i, theta in enumerate(abilities_for_item):
                p = self._probability(theta, delta)
                sum_expected += p
                sum_variance += p * (1 - p)
            
            if sum_variance > 0.0001:
                delta_new = delta + (sum_observed - sum_expected) / sum_variance
                delta = delta_new
            else:
                break
        
        self.difficulties[question_id] = delta
```

### Threshold Auto-Trigger

**File:** `app/services/rasch_threshold_service.py`

**Implementation:**

```python
def check_and_trigger(self, quiz_id, submission_id=None, check_type='auto'):
    """
    Check threshold dan trigger analysis jika terpenuhi
    """
    # Get quiz
    quiz = Quiz.query.get(quiz_id)
    
    # Check if Rasch enabled
    grade_item = GradeItem.query.filter_by(quiz_id=quiz_id).first()
    if not grade_item or not grade_item.enable_rasch_analysis:
        return False, "Rasch not enabled"
    
    # Count submissions
    submission_count = QuizSubmission.query.filter_by(quiz_id=quiz_id).count()
    
    # Get or create analysis
    analysis = self._get_or_create_analysis(quiz_id, grade_item)
    min_persons = analysis.min_persons or 30
    
    # Check threshold
    threshold_met = submission_count >= min_persons
    
    if threshold_met:
        return self._trigger_analysis(analysis, check_type)
    else:
        # Update status
        analysis.status = RaschAnalysisStatus.WAITING.value
        analysis.status_message = f"Menunggu {min_persons - submission_count} siswa lagi"
        analysis.progress_percentage = (submission_count / min_persons) * 100
        db.session.commit()
        return False, analysis.status_message
```

### Celery Worker

**File:** `app/workers/rasch_worker.py`

**Task Definition:**

```python
@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def rasch_analysis(self, analysis_id):
    """
    Celery task untuk menjalankan Rasch analysis
    """
    try:
        from app.services.rasch_analysis_service import RaschAnalysisService
        
        service = RaschAnalysisService(analysis_id=analysis_id)
        success = service.run_analysis()
        
        if success:
            return {'status': 'completed', 'analysis_id': analysis_id}
        else:
            return {'status': 'partial', 'analysis_id': analysis_id}
    
    except Exception as exc:
        # Retry dengan exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
```

---

## 🧪 Testing

### Unit Testing

**Test JMLE Algorithm:**

```python
def test_jmle_convergence():
    """Test JMLE algorithm convergence"""
    from app.services.rasch_analysis_service import RaschAnalysisService
    
    # Create mock response matrix
    response_matrix = {
        (1, 1): 1, (1, 2): 1, (1, 3): 0,
        (2, 1): 1, (2, 2): 0, (2, 3): 0,
        (3, 1): 0, (3, 2): 0, (3, 3): 0,
    }
    
    service = RaschAnalysisService(analysis_id=1)
    service.response_matrix = response_matrix
    service.students = [1, 2, 3]
    service.questions = [1, 2, 3]
    
    service.initialize_measures()
    converged = service.run_jmle()
    
    assert converged == True
    assert len(service.abilities) == 3
    assert len(service.difficulties) == 3
```

**Test Threshold Check:**

```python
def test_threshold_auto_trigger():
    """Test threshold auto-trigger mechanism"""
    from app.services.rasch_threshold_service import RaschThresholdService
    
    service = RaschThresholdService()
    
    # Create mock quiz with 30 submissions
    quiz = create_quiz_with_submissions(num_submissions=30)
    
    threshold_met, message = service.check_and_trigger(quiz_id=quiz.id)
    
    assert threshold_met == True
    assert "started" in message.lower()
```

### Integration Testing

**Test Full Flow:**

```python
def test_quiz_submission_to_analysis():
    """Test full flow dari submission ke analysis"""
    # 1. Student submits quiz
    submission = submit_quiz(quiz_id=1, student_id=101)
    
    # 2. Check GradeEntry created
    grade_entry = GradeEntry.query.filter_by(
        student_id=101, 
        grade_item_id=1
    ).first()
    assert grade_entry is not None
    
    # 3. Submit 29 more students
    for i in range(29):
        submit_quiz(quiz_id=1, student_id=102+i)
    
    # 4. Check analysis triggered
    analysis = RaschAnalysis.query.filter_by(quiz_id=1).first()
    assert analysis is not None
    assert analysis.status == 'queued'
    
    # 5. Run Celery task
    from app.workers.rasch_worker import rasch_analysis
    result = rasch_analysis(analysis_id=analysis.id)
    
    # 6. Check results saved
    assert analysis.status == 'completed'
    assert analysis.num_persons == 30
```

### Manual Testing Checklist

**Backend:**
- [ ] Migration runs successfully
- [ ] Models can be imported
- [ ] JMLE algorithm converges
- [ ] Threshold check works
- [ ] Celery worker processes tasks
- [ ] API endpoints return correct data

**Frontend:**
- [ ] Teacher dashboard loads
- [ ] Analysis detail tabs work
- [ ] Wright Map renders
- [ ] Person measures table populates
- [ ] Item measures table populates
- [ ] Student ability view displays
- [ ] Charts render correctly
- [ ] Export CSV works

---

## 🚀 Deployment

### Production Checklist

**Prerequisites:**
- [ ] MySQL 8.0+ installed
- [ ] Redis server installed
- [ ] Python 3.10+ installed
- [ ] All dependencies installed

**Steps:**

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Migration:**
   ```bash
   python scripts/run_rasch_migration.py
   ```

3. **Configure Environment:**
   ```bash
   # .env file
   CELERY_BROKER_URL=redis://localhost:6379/0
   CELERY_RESULT_BACKEND=redis://localhost:6379/0
   RASCH_DEFAULT_MIN_PERSONS=30
   ```

4. **Start Redis:**
   ```bash
   redis-server
   ```

5. **Start Celery Worker:**
   ```bash
   # Production (daemon mode)
   celery -A run_worker.celery worker --loglevel=info --detach
   
   # Or use systemd service
   ```

6. **Start Flask App:**
   ```bash
   gunicorn --bind 0.0.0.0:8000 --workers 4 "app:create_app()"
   ```

7. **Verify:**
   ```bash
   curl http://localhost:8000/api/rasch/analyses
   ```

### Docker Deployment

**docker-compose.yml:**

```yaml
version: '3.8'

services:
  web:
    build: .
    command: gunicorn --bind 0.0.0.0:8000 "app:create_app()"
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - DATABASE_URL=mysql+pymysql://user:pass@db/aldudu
    depends_on:
      - redis
      - db

  worker:
    build: .
    command: celery -A run_worker.celery worker --loglevel=info
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - DATABASE_URL=mysql+pymysql://user:pass@db/aldudu
    depends_on:
      - redis
      - db

  redis:
    image: redis:7-alpine

  db:
    image: mysql:8
    environment:
      - MYSQL_ROOT_PASSWORD=pass
      - MYSQL_DATABASE=aldudu
```

---

## 🔧 Troubleshooting

### Common Issues

**1. Analysis Tidak Auto-Trigger**

**Symptoms:**
- Threshold terpenuhi tapi status tetap "waiting"
- Celery task tidak dijalankan

**Solutions:**
```bash
# Check Celery worker running
ps aux | grep celery

# Check Redis connection
redis-cli ping

# Check Celery logs
tail -f /var/log/celery/worker.log

# Restart worker
sudo systemctl restart celery-worker
```

**2. JMLE Tidak Converge**

**Symptoms:**
- Status "partial" setelah max iterations
- Theta/delta values ekstrem

**Solutions:**
```sql
-- Increase max iterations
UPDATE rasch_analyses 
SET max_iterations = 200, 
    convergence_threshold = 0.01
WHERE id = 1;

-- Or check data quality
SELECT * FROM rasch_person_measures 
WHERE theta > 5 OR theta < -5;
```

**3. Wright Map Tidak Render**

**Symptoms:**
- Wright Map tab kosong
- JavaScript error di console

**Solutions:**
```javascript
// Check API response
fetch('/api/rasch/analyses/1/wright-map')
  .then(r => r.json())
  .then(data => console.log(data));

// Check Chart.js loaded
console.log(typeof Chart); // Should be 'function'
```

**4. Export CSV Tidak Bekerja**

**Symptoms:**
- Click export tapi tidak download
- 404 error

**Solutions:**
```python
# Add CSV export endpoint
@rasch_bp.route('/analyses/<int:analysis_id>/persons/csv')
def export_persons_csv(analysis_id):
    from io import StringIO
    import csv
    
    measures = RaschPersonMeasure.query.filter_by(
        rasch_analysis_id=analysis_id
    ).all()
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Student', 'Theta', 'Level', 'Percentile'])
    
    for m in measures:
        writer.writerow([m.student.name, m.theta, m.ability_level, m.ability_percentile])
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment;filename=persons.csv'}
    )
```

---

## 📚 Referensi

1. Rasch, G. (1960). *Probabilistic Models for Some Intelligence and Attainment Tests*. Copenhagen: Danish Institute for Educational Research.

2. Bond, T. G., & Fox, C. M. (2015). *Applying the Rasch Model: Fundamental Measurement in the Human Sciences* (3rd ed.). Routledge.

3. Wright, B. D., & Masters, G. N. (1982). *Rating Scale Analysis*. Chicago: MESA Press.

4. Fischer, G. H., & Molenaar, I. W. (1995). *Rasch Models: Foundations, Recent Developments, and Applications*. Springer.

5. Linacre, J. M. (2002). *What do INFIT and OUTFIT Mean-Square and Standardized mean?* Rasch Measurement Transactions, 16(2), 878.

---

**Dokumentasi ini dibuat untuk Aldudu Academy**  
**Version:** 1.0  
**Last Updated:** 2026-03-21
