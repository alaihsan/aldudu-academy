import enum
from app.extensions import db
from app.helpers import now_jakarta


class QuestionType(enum.Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    DROPDOWN = "dropdown"
    CHECKBOX = "checkbox"
    LONG_TEXT = "long_text"
    UPLOAD = "upload"
    MATCHING = "matching"
    LIKERT_SCALE = "likert_scale"


class QuizStatus(enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    UNPUBLISHED = "unpublished"


class Quiz(db.Model):
    __tablename__ = "quizzes"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.Enum(QuizStatus), nullable=False, default=QuizStatus.DRAFT)
    duration_minutes = db.Column(db.Integer, nullable=False, default=0)
    max_attempts = db.Column(db.Integer, nullable=False, default=1)
    shuffle_questions = db.Column(db.Boolean, nullable=False, default=False)
    questions_per_page = db.Column(db.Integer, nullable=False, default=0)
    quiz_password = db.Column(db.String(120))
    theme_color = db.Column(db.String(7), nullable=False, default="#2563eb")
    theme_font = db.Column(db.String(50), nullable=False, default="Inter")
    theme_text_size = db.Column(db.String(20), nullable=False, default="normal")
    theme_background = db.Column(db.String(30), nullable=False, default="plain")
    theme_background_intensity = db.Column(db.Integer, nullable=False, default=20)
    theme_form_width = db.Column(db.String(20), nullable=False, default="standard")
    theme_card_radius = db.Column(db.String(20), nullable=False, default="google")
    theme_density = db.Column(db.String(20), nullable=False, default="normal")
    confirmation_message = db.Column(db.Text, default="Jawaban Anda telah direkam.")
    default_points = db.Column(db.Integer, nullable=False, default=10)
    required_by_default = db.Column(db.Boolean, nullable=False, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_jakarta)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_jakarta, onupdate=now_jakarta)

    creator = db.relationship("User", back_populates="quizzes")
    questions = db.relationship("Question", back_populates="quiz", order_by="Question.order", cascade="all, delete-orphan")
    submissions = db.relationship("QuizSubmission", back_populates="quiz", cascade="all, delete-orphan")


class Question(db.Model):
    __tablename__ = "questions"

    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
    question_text = db.Column(db.Text, nullable=False, default="")
    question_type = db.Column(db.Enum(QuestionType), nullable=False, default=QuestionType.MULTIPLE_CHOICE)
    description = db.Column(db.Text)
    image = db.Column(db.String(255))
    order = db.Column(db.Integer, nullable=False, default=1)
    points = db.Column(db.Integer, nullable=False, default=0)
    is_required = db.Column(db.Boolean, nullable=False, default=True)
    max_file_size = db.Column(db.Integer, nullable=False, default=10)
    allowed_file_types = db.Column(db.String(200), default="pdf,image,document")

    quiz = db.relationship("Quiz", back_populates="questions")
    options = db.relationship("Option", back_populates="question", order_by="Option.order", cascade="all, delete-orphan")
    answers = db.relationship("Answer", back_populates="question")


class Option(db.Model):
    __tablename__ = "options"

    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    option_text = db.Column(db.String(500), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False, default=False)
    order = db.Column(db.Integer, nullable=False, default=1)

    question = db.relationship("Question", back_populates="options")
    answers = db.relationship("Answer", back_populates="selected_option")


class QuizSubmission(db.Model):
    __tablename__ = "quiz_submissions"
    __table_args__ = (db.Index("ix_quiz_user_submitted", "quiz_id", "user_id", "submitted_at"),)

    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    submitted_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_jakarta)
    score = db.Column(db.Float)
    total_points = db.Column(db.Integer, nullable=False, default=0)
    earned_points = db.Column(db.Float, nullable=False, default=0)
    attempt_number = db.Column(db.Integer, nullable=False, default=1)

    quiz = db.relationship("Quiz", back_populates="submissions")
    user = db.relationship("User", back_populates="submissions")
    answers = db.relationship("Answer", back_populates="submission", cascade="all, delete-orphan")


class Answer(db.Model):
    __tablename__ = "answers"

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey("quiz_submissions.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    answer_text = db.Column(db.Text)
    answer_data = db.Column(db.JSON)
    selected_option_id = db.Column(db.Integer, db.ForeignKey("options.id", ondelete="SET NULL"))
    manual_score = db.Column(db.Float)

    submission = db.relationship("QuizSubmission", back_populates="answers")
    question = db.relationship("Question", back_populates="answers")
    selected_option = db.relationship("Option", back_populates="answers")
