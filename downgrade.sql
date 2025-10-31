DATABASE_URL: postgresql://myuser:secret@db:5432/aldudu_prod
BEGIN;

-- Running downgrade 5ff97e5caa64 -> 1f2b7825d481

ALTER TABLE questions DROP COLUMN "order";

ALTER TABLE options DROP COLUMN "order";

UPDATE alembic_version SET version_num='1f2b7825d481' WHERE alembic_version.version_num = '5ff97e5caa64';

-- Running downgrade 1f2b7825d481 -> 5f51342ac48d

ALTER TABLE quizzes DROP COLUMN grade_type;

ALTER TABLE quizzes DROP COLUMN grading_category;

ALTER TABLE quizzes DROP COLUMN points;

ALTER TABLE quizzes DROP COLUMN end_date;

ALTER TABLE quizzes DROP COLUMN start_date;

UPDATE alembic_version SET version_num='5f51342ac48d' WHERE alembic_version.version_num = '1f2b7825d481';

COMMIT;

