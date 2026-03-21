-- ============================================================
-- Rasch Model Migration for Aldudu Academy (MySQL Version)
-- ============================================================
-- Migration untuk mendukung analisis Rasch Model pada sistem gradebook
-- 
-- Teori Klasik: Instant (saat submit quiz)
-- Rasch Model: Batch processing (setelah threshold terpenuhi)
--
-- Database: MySQL 8.0+
-- Created: 2026-03-21
-- ============================================================

SET FOREIGN_KEY_CHECKS = 0;

-- ============================================================
-- 1. Tabel: question_bloom_taxonomy
-- ============================================================

CREATE TABLE IF NOT EXISTS question_bloom_taxonomy (
    id INT AUTO_INCREMENT PRIMARY KEY,
    question_id INT NOT NULL,
    
    -- Bloom's Revised Taxonomy levels
    bloom_level VARCHAR(50) NOT NULL
        COMMENT 'Level kognitif: remember, understand, apply, analyze, evaluate, create',
    
    bloom_description TEXT NULL
        COMMENT 'Justifikasi pemilihan level',
    
    verified_by INT NULL,
    verified_at DATETIME NULL,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    CONSTRAINT uq_question_bloom UNIQUE(question_id),
    CONSTRAINT fk_bloom_question FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
    CONSTRAINT fk_bloom_verified_by FOREIGN KEY (verified_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Mapping taksonomi Bloom untuk setiap soal';

CREATE INDEX idx_bloom_taxonomy_level ON question_bloom_taxonomy(bloom_level);


-- ============================================================
-- 2. Tabel: rasch_analyses
-- ============================================================

CREATE TABLE IF NOT EXISTS rasch_analyses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT NOT NULL,
    quiz_id INT NULL,
    assignment_id INT NULL,
    
    -- Identification
    name VARCHAR(200) NOT NULL,
    analysis_type ENUM('quiz', 'assignment', 'combined') NOT NULL,
    
    -- Status tracking
    status ENUM('pending', 'waiting', 'queued', 'processing', 'completed', 'failed', 'partial') 
        NOT NULL DEFAULT 'pending',
    
    progress_percentage DECIMAL(5,2) DEFAULT 0,
    status_message VARCHAR(500) NULL,
    
    -- Timing
    started_at DATETIME NULL,
    completed_at DATETIME NULL,
    error_message TEXT NULL,
    
    -- Threshold configuration
    min_persons INT DEFAULT 30 NOT NULL,
    auto_trigger BOOLEAN DEFAULT TRUE NOT NULL,
    
    -- Rasch parameters
    convergence_threshold DECIMAL(10,8) DEFAULT 0.001,
    max_iterations INT DEFAULT 100,
    
    -- Results summary
    num_persons INT NULL,
    num_items INT NULL,
    cronbach_alpha DECIMAL(5,4) NULL,
    person_separation_index DECIMAL(5,4) NULL,
    item_separation_index DECIMAL(5,4) NULL,
    
    -- Metadata
    created_by INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_rasch_analysis_type CHECK (analysis_type IN ('quiz', 'assignment', 'combined')),
    CONSTRAINT chk_rasch_status CHECK (status IN ('pending', 'waiting', 'queued', 'processing', 'completed', 'failed', 'partial')),
    CONSTRAINT chk_rasch_min_persons CHECK (min_persons >= 5),
    
    CONSTRAINT fk_rasch_course FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    CONSTRAINT fk_rasch_quiz FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE SET NULL,
    CONSTRAINT fk_rasch_assignment FOREIGN KEY (assignment_id) REFERENCES assignments(id) ON DELETE SET NULL,
    CONSTRAINT fk_rasch_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Tracking analisis Rasch Model untuk quiz dan assignment';

CREATE INDEX idx_rasch_analyses_status ON rasch_analyses(status);
CREATE INDEX idx_rasch_analyses_quiz ON rasch_analyses(quiz_id);
CREATE INDEX idx_rasch_analyses_course ON rasch_analyses(course_id);
CREATE INDEX idx_rasch_analyses_assignment ON rasch_analyses(assignment_id);
CREATE INDEX idx_rasch_analyses_created_at ON rasch_analyses(created_at DESC);


-- ============================================================
-- 3. Tabel: rasch_person_measures
-- ============================================================

CREATE TABLE IF NOT EXISTS rasch_person_measures (
    id INT AUTO_INCREMENT PRIMARY KEY,
    rasch_analysis_id INT NOT NULL,
    student_id INT NOT NULL,
    quiz_submission_id INT NULL,
    
    -- Classical scores
    raw_score INT NOT NULL,
    total_possible INT NOT NULL,
    percentage DECIMAL(5,2) NOT NULL,
    
    -- Rasch ability measure (logit scale)
    theta DECIMAL(10,6) NULL,
    theta_se DECIMAL(10,6) NULL,
    theta_centered DECIMAL(10,6) NULL,
    
    -- Fit statistics
    outfit_mnsq DECIMAL(10,6) NULL,
    outfit_zstd DECIMAL(10,6) NULL,
    infit_mnsq DECIMAL(10,6) NULL,
    infit_zstd DECIMAL(10,6) NULL,
    
    -- Fit interpretation
    fit_status ENUM('well_fitted', 'underfit', 'overfit') NULL,
    fit_category ENUM('excellent', 'good', 'marginal', 'poor') NULL,
    
    -- Ability level interpretation
    ability_level ENUM('very_low', 'low', 'average', 'high', 'very_high') NULL,
    ability_percentile DECIMAL(5,2) NULL,
    
    -- Wright Map position
    wright_map_band VARCHAR(50) NULL,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    CONSTRAINT uq_rasch_person UNIQUE(rasch_analysis_id, student_id),
    CONSTRAINT fk_rasch_person_analysis FOREIGN KEY (rasch_analysis_id) REFERENCES rasch_analyses(id) ON DELETE CASCADE,
    CONSTRAINT fk_rasch_person_student FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_rasch_person_submission FOREIGN KEY (quiz_submission_id) REFERENCES quiz_submissions(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Ability parameter (θ) untuk setiap siswa dalam analisis Rasch';

CREATE INDEX idx_rasch_person_student ON rasch_person_measures(student_id);
CREATE INDEX idx_rasch_person_theta ON rasch_person_measures(theta);
CREATE INDEX idx_rasch_person_fit ON rasch_person_measures(fit_status);
CREATE INDEX idx_rasch_person_analysis ON rasch_person_measures(rasch_analysis_id);


-- ============================================================
-- 4. Tabel: rasch_item_measures
-- ============================================================

CREATE TABLE IF NOT EXISTS rasch_item_measures (
    id INT AUTO_INCREMENT PRIMARY KEY,
    rasch_analysis_id INT NOT NULL,
    question_id INT NOT NULL,
    
    -- Classical indices
    p_value DECIMAL(5,4) NULL,
    point_biserial DECIMAL(5,4) NULL,
    
    -- Rasch difficulty measure
    delta DECIMAL(10,6) NULL,
    delta_se DECIMAL(10,6) NULL,
    delta_centered DECIMAL(10,6) NULL,
    
    -- Fit statistics
    outfit_mnsq DECIMAL(10,6) NULL,
    outfit_zstd DECIMAL(10,6) NULL,
    infit_mnsq DECIMAL(10,6) NULL,
    infit_zstd DECIMAL(10,6) NULL,
    
    -- Fit interpretation
    fit_status ENUM('well_fitted', 'underfit', 'overfit') NULL,
    fit_category ENUM('excellent', 'good', 'marginal', 'poor') NULL,
    
    -- Difficulty interpretation
    difficulty_level ENUM('very_easy', 'easy', 'moderate', 'difficult', 'very_difficult') NULL,
    difficulty_percentile DECIMAL(5,2) NULL,
    
    -- Bloom Taxonomy (cached)
    bloom_level ENUM('remember', 'understand', 'apply', 'analyze', 'evaluate', 'create') NULL,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    CONSTRAINT uq_rasch_item UNIQUE(rasch_analysis_id, question_id),
    CONSTRAINT fk_rasch_item_analysis FOREIGN KEY (rasch_analysis_id) REFERENCES rasch_analyses(id) ON DELETE CASCADE,
    CONSTRAINT fk_rasch_item_question FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Difficulty parameter (δ) untuk setiap soal dalam analisis Rasch';

CREATE INDEX idx_rasch_item_question ON rasch_item_measures(question_id);
CREATE INDEX idx_rasch_item_delta ON rasch_item_measures(delta);
CREATE INDEX idx_rasch_item_fit ON rasch_item_measures(fit_status);
CREATE INDEX idx_rasch_item_bloom ON rasch_item_measures(bloom_level);
CREATE INDEX idx_rasch_item_analysis ON rasch_item_measures(rasch_analysis_id);


-- ============================================================
-- 5. Tabel: rasch_threshold_logs
-- ============================================================

CREATE TABLE IF NOT EXISTS rasch_threshold_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    rasch_analysis_id INT NOT NULL,
    
    -- Threshold check
    check_type ENUM('auto', 'manual') NOT NULL,
    num_submissions INT NOT NULL,
    min_required INT NOT NULL,
    threshold_met BOOLEAN NOT NULL,
    
    -- Decision
    action_taken ENUM('queued', 'waiting', 'ignored') NULL,
    reason TEXT NULL,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_threshold_check_type CHECK (check_type IN ('auto', 'manual')),
    CONSTRAINT chk_threshold_action CHECK (action_taken IN ('queued', 'waiting', 'ignored')),
    CONSTRAINT fk_rasch_threshold_analysis FOREIGN KEY (rasch_analysis_id) REFERENCES rasch_analyses(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Log tracking untuk threshold checking Rasch analysis';

CREATE INDEX idx_rasch_threshold_analysis ON rasch_threshold_logs(rasch_analysis_id);
CREATE INDEX idx_rasch_threshold_created ON rasch_threshold_logs(created_at DESC);


-- ============================================================
-- 6. Tabel: rasch_rating_scales (Optional - untuk Rating Scale Model)
-- ============================================================

CREATE TABLE IF NOT EXISTS rasch_rating_scales (
    id INT AUTO_INCREMENT PRIMARY KEY,
    rasch_analysis_id INT NOT NULL,
    scale_name VARCHAR(100) NOT NULL,
    
    -- Scale structure
    num_categories INT NOT NULL,
    thresholds JSON NULL,
    
    -- Scale statistics
    category_observations JSON NULL,
    category_averages JSON NULL,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_rating_categories CHECK (num_categories >= 2),
    CONSTRAINT fk_rasch_rating_analysis FOREIGN KEY (rasch_analysis_id) REFERENCES rasch_analyses(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Rating scale parameters untuk Partial Credit Model (tugas dengan rubric)';

CREATE INDEX idx_rasch_rating_scales_analysis ON rasch_rating_scales(rasch_analysis_id);


-- ============================================================
-- 7. Modifikasi Tabel grade_items
-- ============================================================

-- Tambahkan kolom untuk Rasch integration
-- Menggunakan procedure untuk handle "IF NOT EXISTS"

DROP PROCEDURE IF EXISTS add_rasch_columns_to_grade_items;

DELIMITER $$

CREATE PROCEDURE add_rasch_columns_to_grade_items()
BEGIN
    -- Add enable_rasch_analysis
    IF NOT EXISTS (
        SELECT * FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA=DATABASE() 
        AND TABLE_NAME='grade_items' 
        AND COLUMN_NAME='enable_rasch_analysis'
    ) THEN
        ALTER TABLE grade_items 
        ADD COLUMN enable_rasch_analysis BOOLEAN DEFAULT FALSE NOT NULL
            COMMENT 'Flag untuk mengaktifkan Rasch analysis';
    END IF;
    
    -- Add rasch_analysis_id
    IF NOT EXISTS (
        SELECT * FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA=DATABASE() 
        AND TABLE_NAME='grade_items' 
        AND COLUMN_NAME='rasch_analysis_id'
    ) THEN
        ALTER TABLE grade_items 
        ADD COLUMN rasch_analysis_id INT NULL
            COMMENT 'Link ke hasil Rasch analysis terbaru';
    END IF;
    
    -- Add show_rasch_to_students
    IF NOT EXISTS (
        SELECT * FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA=DATABASE() 
        AND TABLE_NAME='grade_items' 
        AND COLUMN_NAME='show_rasch_to_students'
    ) THEN
        ALTER TABLE grade_items 
        ADD COLUMN show_rasch_to_students BOOLEAN DEFAULT FALSE NOT NULL
            COMMENT 'Kontrol visibilitas Rasch measures untuk siswa';
    END IF;
    
    -- Drop existing foreign key if exists
    IF EXISTS (
        SELECT * FROM information_schema.TABLE_CONSTRAINTS 
        WHERE TABLE_SCHEMA=DATABASE() 
        AND TABLE_NAME='grade_items' 
        AND CONSTRAINT_NAME='fk_grade_item_rasch_analysis'
    ) THEN
        ALTER TABLE grade_items DROP FOREIGN KEY fk_grade_item_rasch_analysis;
    END IF;
    
    -- Drop existing index if exists
    IF EXISTS (
        SELECT * FROM information_schema.STATISTICS 
        WHERE TABLE_SCHEMA=DATABASE() 
        AND TABLE_NAME='grade_items' 
        AND INDEX_NAME='idx_grade_items_rasch'
    ) THEN
        DROP INDEX idx_grade_items_rasch ON grade_items;
    END IF;
    
    -- Add foreign key
    ALTER TABLE grade_items
    ADD CONSTRAINT fk_grade_item_rasch_analysis 
        FOREIGN KEY (rasch_analysis_id) REFERENCES rasch_analyses(id) ON DELETE SET NULL;
    
    -- Create index
    CREATE INDEX idx_grade_items_rasch ON grade_items(rasch_analysis_id);
END$$

DELIMITER ;

-- Execute procedure
CALL add_rasch_columns_to_grade_items();

-- Drop procedure
DROP PROCEDURE IF EXISTS add_rasch_columns_to_grade_items;


-- ============================================================
-- 8. Data Seed: Default Values (Optional)
-- ============================================================

-- Insert sample Bloom taxonomy mapping untuk quiz yang sudah ada
-- (Optional - bisa dihapus jika tidak diperlukan)

INSERT IGNORE INTO question_bloom_taxonomy (question_id, bloom_level, bloom_description)
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
LIMIT 100;


-- ============================================================
-- Migration Complete
-- ============================================================
-- 
-- Next steps:
-- 1. Verify tables: SHOW TABLES LIKE 'rasch_%';
-- 2. Check structure: DESCRIBE rasch_analyses;
--
-- Rollback (jika diperlukan):
-- SET FOREIGN_KEY_CHECKS = 0;
-- DROP TABLE IF EXISTS rasch_rating_scales;
-- DROP TABLE IF EXISTS rasch_threshold_logs;
-- DROP TABLE IF EXISTS rasch_item_measures;
-- DROP TABLE IF EXISTS rasch_person_measures;
-- DROP TABLE IF EXISTS rasch_analyses;
-- DROP TABLE IF EXISTS question_bloom_taxonomy;
-- 
-- ALTER TABLE grade_items 
-- DROP FOREIGN KEY fk_grade_item_rasch_analysis,
-- DROP COLUMN IF EXISTS show_rasch_to_students,
-- DROP COLUMN IF EXISTS rasch_analysis_id,
-- DROP COLUMN IF EXISTS enable_rasch_analysis;
-- SET FOREIGN_KEY_CHECKS = 1;
-- ============================================================

SET FOREIGN_KEY_CHECKS = 1;
