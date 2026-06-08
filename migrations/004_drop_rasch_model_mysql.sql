-- ============================================================
-- Drop Rasch Model Migration for Aldudu Academy (MySQL Version)
-- ============================================================
-- Menghapus seluruh skema fitur Rasch Model dari database.
-- Bloom Taxonomy (question_bloom_taxonomy) DIPERTAHANKAN.
--
-- Membatalkan: 002_rasch_model_mysql.sql
-- Database: MySQL 8.0+
-- Created: 2026-06-08
-- ============================================================

SET FOREIGN_KEY_CHECKS = 0;

-- ============================================================
-- 1. Lepas integrasi Rasch dari tabel grade_items
-- ============================================================

-- Drop foreign key (jika ada)
SET @fk_exists = (
    SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'grade_items'
      AND CONSTRAINT_NAME = 'fk_grade_item_rasch_analysis'
);
SET @sql = IF(@fk_exists > 0,
    'ALTER TABLE grade_items DROP FOREIGN KEY fk_grade_item_rasch_analysis;',
    'SELECT 1;');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Drop index (jika ada)
SET @idx_exists = (
    SELECT COUNT(*) FROM information_schema.STATISTICS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'grade_items'
      AND INDEX_NAME = 'idx_grade_items_rasch'
);
SET @sql = IF(@idx_exists > 0,
    'DROP INDEX idx_grade_items_rasch ON grade_items;',
    'SELECT 1;');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Drop kolom Rasch
ALTER TABLE grade_items
    DROP COLUMN enable_rasch_analysis,
    DROP COLUMN rasch_analysis_id,
    DROP COLUMN show_rasch_to_students;

-- ============================================================
-- 2. Drop tabel Rasch (urut sesuai dependensi foreign key)
-- ============================================================

DROP TABLE IF EXISTS rasch_threshold_logs;
DROP TABLE IF EXISTS rasch_rating_scales;
DROP TABLE IF EXISTS rasch_item_measures;
DROP TABLE IF EXISTS rasch_person_measures;
DROP TABLE IF EXISTS rasch_analyses;

-- CATATAN: question_bloom_taxonomy SENGAJA TIDAK di-drop (masih dipakai).

SET FOREIGN_KEY_CHECKS = 1;
