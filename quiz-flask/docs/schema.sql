CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(7) NOT NULL DEFAULT 'STUDENT',
    created_at DATETIME NOT NULL
);

CREATE INDEX ix_users_email ON users (email);

CREATE TABLE quizzes (
    id INTEGER PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(11) NOT NULL DEFAULT 'DRAFT',
    duration_minutes INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 1,
    shuffle_questions BOOLEAN NOT NULL DEFAULT 0,
    questions_per_page INTEGER NOT NULL DEFAULT 0,
    quiz_password VARCHAR(120),
    theme_color VARCHAR(7) NOT NULL DEFAULT '#2563eb',
    theme_font VARCHAR(50) NOT NULL DEFAULT 'Inter',
    theme_text_size VARCHAR(20) NOT NULL DEFAULT 'normal',
    theme_background VARCHAR(30) NOT NULL DEFAULT 'plain',
    theme_background_intensity INTEGER NOT NULL DEFAULT 20,
    theme_form_width VARCHAR(20) NOT NULL DEFAULT 'standard',
    theme_card_radius VARCHAR(20) NOT NULL DEFAULT 'google',
    theme_density VARCHAR(20) NOT NULL DEFAULT 'normal',
    confirmation_message TEXT DEFAULT 'Jawaban Anda telah direkam.',
    default_points INTEGER NOT NULL DEFAULT 10,
    required_by_default BOOLEAN NOT NULL DEFAULT 1,
    created_by INTEGER NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY(created_by) REFERENCES users (id)
);

CREATE INDEX ix_quizzes_created_by ON quizzes (created_by);

CREATE TABLE questions (
    id INTEGER PRIMARY KEY,
    quiz_id INTEGER NOT NULL,
    question_text TEXT NOT NULL DEFAULT '',
    question_type VARCHAR(15) NOT NULL DEFAULT 'MULTIPLE_CHOICE',
    description TEXT,
    image VARCHAR(255),
    "order" INTEGER NOT NULL DEFAULT 1,
    points INTEGER NOT NULL DEFAULT 0,
    is_required BOOLEAN NOT NULL DEFAULT 1,
    max_file_size INTEGER NOT NULL DEFAULT 10,
    allowed_file_types VARCHAR(200) DEFAULT 'pdf,image,document',
    FOREIGN KEY(quiz_id) REFERENCES quizzes (id) ON DELETE CASCADE
);

CREATE INDEX ix_questions_quiz_id ON questions (quiz_id);

CREATE TABLE options (
    id INTEGER PRIMARY KEY,
    question_id INTEGER NOT NULL,
    option_text VARCHAR(500) NOT NULL,
    is_correct BOOLEAN NOT NULL DEFAULT 0,
    "order" INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY(question_id) REFERENCES questions (id) ON DELETE CASCADE
);

CREATE INDEX ix_options_question_id ON options (question_id);

CREATE TABLE quiz_submissions (
    id INTEGER PRIMARY KEY,
    quiz_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    submitted_at DATETIME NOT NULL,
    score FLOAT,
    total_points INTEGER NOT NULL DEFAULT 0,
    earned_points FLOAT NOT NULL DEFAULT 0,
    attempt_number INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY(quiz_id) REFERENCES quizzes (id) ON DELETE CASCADE,
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_quiz_submissions_quiz_id ON quiz_submissions (quiz_id);
CREATE INDEX ix_quiz_submissions_user_id ON quiz_submissions (user_id);
CREATE INDEX ix_quiz_user_submitted ON quiz_submissions (quiz_id, user_id, submitted_at);

CREATE TABLE answers (
    id INTEGER PRIMARY KEY,
    submission_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    answer_text TEXT,
    answer_data JSON,
    selected_option_id INTEGER,
    manual_score FLOAT,
    FOREIGN KEY(submission_id) REFERENCES quiz_submissions (id) ON DELETE CASCADE,
    FOREIGN KEY(question_id) REFERENCES questions (id) ON DELETE CASCADE,
    FOREIGN KEY(selected_option_id) REFERENCES options (id) ON DELETE SET NULL
);

CREATE INDEX ix_answers_submission_id ON answers (submission_id);
CREATE INDEX ix_answers_question_id ON answers (question_id);
