-- ============================================================
-- Add is_archived field to quizzes table
-- ============================================================
-- Migration untuk menambahkan field is_archived pada tabel quizzes
-- Digunakan untuk mengarsipkan kuis tanpa menghapus data nilai siswa
--
-- Created: 2026-03-22
-- ============================================================

-- Add is_archived column to quizzes table
ALTER TABLE quizzes 
ADD COLUMN is_archived BOOLEAN NOT NULL DEFAULT FALSE;

-- Add index for better query performance
CREATE INDEX IF NOT EXISTS idx_quizzes_is_archived ON quizzes(is_archived);

-- Add index for combined course_id and is_archived queries
CREATE INDEX IF NOT EXISTS idx_quizzes_course_archived ON quizzes(course_id, is_archived);

-- ============================================================
-- Rollback (downgrade)
-- ============================================================
-- Untuk rollback, jalankan perintah berikut:
-- 
-- DROP INDEX IF EXISTS idx_quizzes_course_archived;
-- DROP INDEX IF EXISTS idx_quizzes_is_archived;
-- ALTER TABLE quizzes DROP COLUMN is_archived;
-- ============================================================
