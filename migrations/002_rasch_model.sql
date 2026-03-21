-- ============================================================
-- Rasch Model Migration for Aldudu Academy
-- ============================================================
-- Migration untuk mendukung analisis Rasch Model pada sistem gradebook
-- 
-- Teori Klasik: Instant (saat submit quiz)
-- Rasch Model: Batch processing (setelah threshold terpenuhi)
--
-- Created: 2026-03-21
-- ============================================================

-- ============================================================
-- 1. Tabel: question_bloom_taxonomy
-- ============================================================
-- Mapping taksonomi Bloom untuk setiap soal
-- Digunakan untuk analisis korelasi difficulty vs cognitive level

CREATE TABLE IF NOT EXISTS question_bloom_taxonomy (
    id SERIAL PRIMARY KEY,
    question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    
    -- Bloom's Revised Taxonomy levels
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
    
    CONSTRAINT uq_question_bloom UNIQUE(question_id)
);

CREATE INDEX idx_bloom_taxonomy_level ON question_bloom_taxonomy(bloom_level);

COMMENT ON TABLE question_bloom_taxonomy IS 'Mapping taksonomi Bloom untuk setiap soal';
COMMENT ON COLUMN question_bloom_taxonomy.bloom_level IS 'Level kognitif berdasarkan Bloom Revised Taxonomy';


-- ============================================================
-- 2. Tabel: rasch_analyses
-- ============================================================
-- Tabel utama untuk tracking analisis Rasch

CREATE TABLE IF NOT EXISTS rasch_analyses (
    id SERIAL PRIMARY KEY,
    course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    quiz_id INTEGER REFERENCES quizzes(id) ON DELETE SET NULL,
    assignment_id INTEGER REFERENCES assignments(id) ON DELETE SET NULL,
    
    -- Identification
    name VARCHAR(200) NOT NULL,
    analysis_type VARCHAR(50) NOT NULL,
        -- 'quiz': Analisis untuk satu quiz
        -- 'assignment': Analisis untuk tugas (rubric-based)
        -- 'combined': Analisis gabungan multiple assessments
    
    -- Status tracking
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
        -- 'pending': Menunggu threshold
        -- 'waiting': Menunggu siswa lain submit
        -- 'queued': Masuk antrian worker
        -- 'processing': Sedang dianalisis
        -- 'completed': Selesai
        -- 'failed': Gagal (lihat error_message)
        -- 'partial': Sebagian selesai
    
    progress_percentage NUMERIC(5,2) DEFAULT 0,
    status_message VARCHAR(500),  -- Update progress real-time
    
    -- Timing
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    
    -- Threshold configuration
    min_persons INTEGER DEFAULT 30,  -- Minimal siswa untuk valid analysis
    auto_trigger BOOLEAN DEFAULT TRUE,  -- Auto-trigger saat threshold tercapai
    
    -- Rasch parameters
    convergence_threshold NUMERIC(10,8) DEFAULT 0.001,
    max_iterations INTEGER DEFAULT 100,
    
    -- Results summary
    num_persons INTEGER,
    num_items INTEGER,
    cronbach_alpha NUMERIC(5,4),  -- Reliabilitas (0-1)
    person_separation_index NUMERIC(5,4),  -- Daya beda orang
    item_separation_index NUMERIC(5,4),  -- Daya beda item
    
    -- Metadata
    created_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_rasch_analysis_type CHECK (analysis_type IN ('quiz', 'assignment', 'combined')),
    CONSTRAINT chk_rasch_status CHECK (status IN (
        'pending', 'waiting', 'queued', 'processing', 'completed', 'failed', 'partial'
    )),
    CONSTRAINT chk_rasch_min_persons CHECK (min_persons >= 5)
);

CREATE INDEX idx_rasch_analyses_status ON rasch_analyses(status);
CREATE INDEX idx_rasch_analyses_quiz ON rasch_analyses(quiz_id);
CREATE INDEX idx_rasch_analyses_course ON rasch_analyses(course_id);
CREATE INDEX idx_rasch_analyses_assignment ON rasch_analyses(assignment_id);
CREATE INDEX idx_rasch_analyses_created_at ON rasch_analyses(created_at DESC);

COMMENT ON TABLE rasch_analyses IS 'Tracking analisis Rasch Model untuk quiz dan assignment';
COMMENT ON COLUMN rasch_analyses.status IS 'Status progress analisis';
COMMENT ON COLUMN rasch_analyses.min_persons IS 'Minimal siswa untuk validitas Rasch (rekomendasi: 30)';
COMMENT ON COLUMN rasch_analyses.cronbach_alpha IS 'Reliabilitas internal consistency';


-- ============================================================
-- 3. Tabel: rasch_person_measures
-- ============================================================
-- Ability parameter (θ) untuk setiap siswa

CREATE TABLE IF NOT EXISTS rasch_person_measures (
    id SERIAL PRIMARY KEY,
    rasch_analysis_id INTEGER NOT NULL REFERENCES rasch_analyses(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    quiz_submission_id INTEGER REFERENCES quiz_submissions(id) ON DELETE SET NULL,
    
    -- Classical scores (untuk comparability dengan teori klasik)
    raw_score INTEGER NOT NULL,
    total_possible INTEGER NOT NULL,
    percentage NUMERIC(5,2) NOT NULL,
    
    -- Rasch ability measure (logit scale)
    theta NUMERIC(10,6),              -- Ability measure
    theta_se NUMERIC(10,6),           -- Standard error of theta
    theta_centered NUMERIC(10,6),     -- Theta centered at 0 untuk reporting
    
    -- Fit statistics
    outfit_mnsq NUMERIC(10,6),        -- Outfit mean square (expected ~1.0)
    outfit_zstd NUMERIC(10,6),        -- Outfit z-standardized (-2 to +2 acceptable)
    infit_mnsq NUMERIC(10,6),         -- Infit mean square
    infit_zstd NUMERIC(10,6),         -- Infit z-standardized
    
    -- Fit interpretation
    fit_status VARCHAR(50),
        -- 'well_fitted': 0.5 <= MNSQ <= 1.5
        -- 'underfit': MNSQ > 1.5 (unpredictable)
        -- 'overfit': MNSQ < 0.5 (too predictable)
    
    fit_category VARCHAR(50),
        -- 'excellent': 0.8 <= MNSQ <= 1.2
        -- 'good': 0.6 <= MNSQ < 0.8 or 1.2 < MNSQ <= 1.4
        -- 'marginal': 0.5 <= MNSQ < 0.6 or 1.4 < MNSQ <= 1.5
        -- 'poor': MNSQ < 0.5 or MNSQ > 1.5
    
    -- Ability level interpretation
    ability_level VARCHAR(50),
        -- 'very_low': θ < -2.0
        -- 'low': -2.0 <= θ < -0.5
        -- 'average': -0.5 <= θ <= 0.5
        -- 'high': 0.5 < θ <= 2.0
        -- 'very_high': θ > 2.0
    
    ability_percentile NUMERIC(5,2),  -- Percentile rank among cohort
    
    -- Wright Map position (untuk visualization grouping)
    wright_map_band VARCHAR(50),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uq_rasch_person UNIQUE(rasch_analysis_id, student_id),
    CONSTRAINT chk_person_fit_status CHECK (fit_status IN (
        'well_fitted', 'underfit', 'overfit', NULL
    )),
    CONSTRAINT chk_person_fit_category CHECK (fit_category IN (
        'excellent', 'good', 'marginal', 'poor', NULL
    )),
    CONSTRAINT chk_person_ability_level CHECK (ability_level IN (
        'very_low', 'low', 'average', 'high', 'very_high', NULL
    ))
);

CREATE INDEX idx_rasch_person_student ON rasch_person_measures(student_id);
CREATE INDEX idx_rasch_person_theta ON rasch_person_measures(theta);
CREATE INDEX idx_rasch_person_fit ON rasch_person_measures(fit_status);
CREATE INDEX idx_rasch_person_analysis ON rasch_person_measures(rasch_analysis_id);

COMMENT ON TABLE rasch_person_measures IS 'Ability parameter (θ) untuk setiap siswa dalam analisis Rasch';
COMMENT ON COLUMN rasch_person_measures.theta IS 'Kemampuan siswa dalam logit scale';
COMMENT ON COLUMN rasch_person_measures.outfit_mnsq IS 'Fit statistic untuk respons unexpected';
COMMENT ON COLUMN rasch_person_measures.infit_mnsq IS 'Fit statistic untuk respons expected';


-- ============================================================
-- 4. Tabel: rasch_item_measures
-- ============================================================
-- Difficulty parameter (δ) untuk setiap soal

CREATE TABLE IF NOT EXISTS rasch_item_measures (
    id SERIAL PRIMARY KEY,
    rasch_analysis_id INTEGER NOT NULL REFERENCES rasch_analyses(id) ON DELETE CASCADE,
    question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    
    -- Classical indices
    p_value NUMERIC(5,4),             -- Difficulty index (proportion correct, 0-1)
    point_biserial NUMERIC(5,4),      -- Discrimination index (-1 to +1)
    
    -- Rasch difficulty measure (logit scale)
    delta NUMERIC(10,6),              -- Difficulty measure
    delta_se NUMERIC(10,6),           -- Standard error of delta
    delta_centered NUMERIC(10,6),     -- Delta centered at mean item difficulty
    
    -- Fit statistics
    outfit_mnsq NUMERIC(10,6),
    outfit_zstd NUMERIC(10,6),
    infit_mnsq NUMERIC(10,6),
    infit_zstd NUMERIC(10,6),
    
    -- Fit interpretation
    fit_status VARCHAR(50),
    fit_category VARCHAR(50),
    
    -- Difficulty interpretation
    difficulty_level VARCHAR(50),
        -- 'very_easy': δ < -2.0 (p > 0.90)
        -- 'easy': -2.0 <= δ < -0.5 (p: 0.70-0.90)
        -- 'moderate': -0.5 <= δ <= 0.5 (p: 0.30-0.70)
        -- 'difficult': 0.5 < δ <= 2.0 (p: 0.10-0.30)
        -- 'very_difficult': δ > 2.0 (p < 0.10)
    
    difficulty_percentile NUMERIC(5,2),
    
    -- Bloom Taxonomy integration (cached dari question_bloom_taxonomy)
    bloom_level VARCHAR(50),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uq_rasch_item UNIQUE(rasch_analysis_id, question_id),
    CONSTRAINT chk_item_fit_status CHECK (fit_status IN (
        'well_fitted', 'underfit', 'overfit', NULL
    )),
    CONSTRAINT chk_item_difficulty_level CHECK (difficulty_level IN (
        'very_easy', 'easy', 'moderate', 'difficult', 'very_difficult', NULL
    ))
);

CREATE INDEX idx_rasch_item_question ON rasch_item_measures(question_id);
CREATE INDEX idx_rasch_item_delta ON rasch_item_measures(delta);
CREATE INDEX idx_rasch_item_fit ON rasch_item_measures(fit_status);
CREATE INDEX idx_rasch_item_bloom ON rasch_item_measures(bloom_level);
CREATE INDEX idx_rasch_item_analysis ON rasch_item_measures(rasch_analysis_id);

COMMENT ON TABLE rasch_item_measures IS 'Difficulty parameter (δ) untuk setiap soal dalam analisis Rasch';
COMMENT ON COLUMN rasch_item_measures.p_value IS 'Classical difficulty: proporsi siswa yang menjawab benar';
COMMENT ON COLUMN rasch_item_measures.point_biserial IS 'Daya beda soal: korelasi soal dengan total score';
COMMENT ON COLUMN rasch_item_measures.delta IS 'Kesulitan soal dalam logit scale (positif = sulit)';


-- ============================================================
-- 5. Tabel: rasch_threshold_logs
-- ============================================================
-- Log untuk tracking threshold checking

CREATE TABLE IF NOT EXISTS rasch_threshold_logs (
    id SERIAL PRIMARY KEY,
    rasch_analysis_id INTEGER NOT NULL REFERENCES rasch_analyses(id) ON DELETE CASCADE,
    
    -- Threshold check
    check_type VARCHAR(50) NOT NULL,
        -- 'auto': Automatic check saat submission
        -- 'manual': Manual trigger oleh guru
    
    num_submissions INTEGER NOT NULL,
    min_required INTEGER NOT NULL,
    threshold_met BOOLEAN NOT NULL,
    
    -- Decision
    action_taken VARCHAR(50),
        -- 'queued': Masuk antrian analisis
        -- 'waiting': Masih menunggu
        -- 'ignored': Diabaikan (misal: analysis sudah ada)
    
    reason TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_threshold_check_type CHECK (check_type IN ('auto', 'manual')),
    CONSTRAINT chk_threshold_action CHECK (action_taken IN (
        'queued', 'waiting', 'ignored', NULL
    ))
);

CREATE INDEX idx_rasch_threshold_analysis ON rasch_threshold_logs(rasch_analysis_id);
CREATE INDEX idx_rasch_threshold_created ON rasch_threshold_logs(created_at DESC);

COMMENT ON TABLE rasch_threshold_logs IS 'Log tracking untuk threshold checking Rasch analysis';


-- ============================================================
-- 6. Tabel: rasch_rating_scales (Optional - untuk Rating Scale Model)
-- ============================================================
-- Untuk analisis tugas dengan rubric (Partial Credit Model)

CREATE TABLE IF NOT EXISTS rasch_rating_scales (
    id SERIAL PRIMARY KEY,
    rasch_analysis_id INTEGER NOT NULL REFERENCES rasch_analyses(id) ON DELETE CASCADE,
    scale_name VARCHAR(100) NOT NULL,
    
    -- Scale structure
    num_categories INTEGER NOT NULL CHECK (num_categories >= 2),
    thresholds JSONB,  -- Array of threshold parameters (tau)
        -- Example: [-1.5, -0.5, 0.5, 1.5] untuk skala 5 kategori
    
    -- Scale statistics
    category_observations JSONB,  -- Count per kategori
    category_averages JSONB,      -- Average ability per kategori
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_rating_categories CHECK (num_categories >= 2)
);

CREATE INDEX idx_rasch_rating_scales_analysis ON rasch_rating_scales(rasch_analysis_id);

COMMENT ON TABLE rasch_rating_scales IS 'Rating scale parameters untuk Partial Credit Model (tugas dengan rubric)';


-- ============================================================
-- 7. Modifikasi Tabel grade_items
-- ============================================================
-- Menambahkan kolom untuk Rasch integration

ALTER TABLE grade_items
ADD COLUMN IF NOT EXISTS enable_rasch_analysis BOOLEAN DEFAULT FALSE NOT NULL,
ADD COLUMN IF NOT EXISTS rasch_analysis_id INTEGER REFERENCES rasch_analyses(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS show_rasch_to_students BOOLEAN DEFAULT FALSE NOT NULL;

CREATE INDEX IF NOT EXISTS idx_grade_items_rasch ON grade_items(rasch_analysis_id);

COMMENT ON COLUMN grade_items.enable_rasch_analysis IS 'Flag untuk mengaktifkan Rasch analysis';
COMMENT ON COLUMN grade_items.rasch_analysis_id IS 'Link ke hasil Rasch analysis terbaru';
COMMENT ON COLUMN grade_items.show_rasch_to_students IS 'Kontrol visibilitas Rasch measures untuk siswa';


-- ============================================================
-- 8. Data Seed: Default Values
-- ============================================================

-- Insert sample Bloom taxonomy mapping untuk quiz yang sudah ada
-- (Optional - bisa dihapus jika tidak diperlukan)

INSERT INTO question_bloom_taxonomy (question_id, bloom_level, bloom_description)
SELECT 
    q.id,
    CASE 
        WHEN q.question_type = 'multiple_choice' AND q.points <= 5 THEN 'remember'
        WHEN q.question_type = 'true_false' THEN 'understand'
        WHEN q.question_type = 'long_text' AND q.points > 20 THEN 'analyze'
        ELSE 'understand'
    END as bloom_level,
    'Auto-generated based on question type and points' as bloom_description
FROM questions q
LEFT JOIN question_bloom_taxonomy b ON q.id = b.question_id
WHERE b.id IS NULL
LIMIT 100;  -- Batch insert untuk testing


-- ============================================================
-- 9. Views untuk Reporting (Optional)
-- ============================================================

-- View: Ringkasan analisis Rasch per course
CREATE OR REPLACE VIEW v_rasch_analysis_summary AS
SELECT 
    ra.id,
    ra.name,
    ra.course_id,
    c.name as course_name,
    ra.quiz_id,
    q.name as quiz_name,
    ra.assignment_id,
    a.title as assignment_title,
    ra.analysis_type,
    ra.status,
    ra.progress_percentage,
    ra.num_persons,
    ra.num_items,
    ra.cronbach_alpha,
    ra.started_at,
    ra.completed_at,
    ra.created_at,
    u.name as created_by_name
FROM rasch_analyses ra
LEFT JOIN courses c ON ra.course_id = c.id
LEFT JOIN quizzes q ON ra.quiz_id = q.id
LEFT JOIN assignments a ON ra.assignment_id = a.id
LEFT JOIN users u ON ra.created_by = u.id;

-- View: Person measures dengan student info
CREATE OR REPLACE VIEW v_rasch_person_summary AS
SELECT 
    rpm.id,
    rpm.rasch_analysis_id,
    rpm.student_id,
    s.name as student_name,
    s.email as student_email,
    rpm.raw_score,
    rpm.percentage,
    rpm.theta,
    rpm.theta_se,
    rpm.ability_level,
    rpm.ability_percentile,
    rpm.fit_status,
    rpm.outfit_mnsq,
    rpm.infit_mnsq,
    rpm.created_at
FROM rasch_person_measures rpm
LEFT JOIN users s ON rpm.student_id = s.id;

-- View: Item measures dengan question info
CREATE OR REPLACE VIEW v_rasch_item_summary AS
SELECT 
    rim.id,
    rim.rasch_analysis_id,
    rim.question_id,
    q.question_text,
    q.question_type,
    q.points,
    rim.p_value,
    rim.point_biserial,
    rim.delta,
    rim.difficulty_level,
    rim.bloom_level,
    rim.fit_status,
    rim.outfit_mnsq,
    rim.infit_mnsq,
    rim.created_at
FROM rasch_item_measures rim
LEFT JOIN questions q ON rim.question_id = q.id;


-- ============================================================
-- Migration Complete
-- ============================================================
-- 
-- Next steps:
-- 1. Run migration: psql -d aldudu_academy -f migrations/002_rasch_model.sql
-- 2. Verify tables: \dt rasch_*
-- 3. Test with sample data
--
-- Rollback (jika diperlukan):
-- DROP VIEW IF EXISTS v_rasch_item_summary;
-- DROP VIEW IF EXISTS v_rasch_person_summary;
-- DROP VIEW IF EXISTS v_rasch_analysis_summary;
-- DROP TABLE IF EXISTS rasch_rating_scales CASCADE;
-- DROP TABLE IF EXISTS rasch_threshold_logs CASCADE;
-- DROP TABLE IF EXISTS rasch_item_measures CASCADE;
-- DROP TABLE IF EXISTS rasch_person_measures CASCADE;
-- DROP TABLE IF EXISTS rasch_analyses CASCADE;
-- DROP TABLE IF EXISTS question_bloom_taxonomy CASCADE;
-- 
-- ALTER TABLE grade_items 
-- DROP COLUMN IF EXISTS show_rasch_to_students,
-- DROP COLUMN IF EXISTS rasch_analysis_id,
-- DROP COLUMN IF EXISTS enable_rasch_analysis;
-- ============================================================
