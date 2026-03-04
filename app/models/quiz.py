import datetime
import enum
from typing import List, Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from . import db

class QuestionType(enum.Enum):
    """Question type enumeration."""
    MULTIPLE_CHOICE = 'multiple_choice'
    TRUE_FALSE = 'true_false'
    DROPDOWN = 'dropdown'
    LONG_TEXT = 'long_text'


class GradeType(enum.Enum):
    """Grade type enumeration."""
    NUMERIC = 'numeric'
    LETTER = 'letter'

class Quiz(db.Model):
    """Quiz model representing assessments."""
    __tablename__ = 'quizzes'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(200), nullable=False)
    course_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    grade_type: Mapped[GradeType] = mapped_column(db.Enum(GradeType), nullable=False, default=GradeType.NUMERIC)
    grading_category: Mapped[Optional[str]] = mapped_column(db.String(100))
    start_date: Mapped[Optional[datetime.datetime]] = mapped_column(db.DateTime, nullable=True)
    end_date: Mapped[Optional[datetime.datetime]] = mapped_column(db.DateTime, nullable=True)
    points: Mapped[int] = mapped_column(db.Integer, default=100) # Total points
    is_published: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    allow_responses: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)
    shuffle_questions: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime.datetime] = mapped_column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    course: Mapped['Course'] = relationship('Course', back_populates='quizzes')
    questions: Mapped[List['Question']] = relationship('Question', back_populates='quiz', lazy='dynamic', cascade="all, delete-orphan")

class Question(db.Model):
    """Question model for quiz questions."""
    __tablename__ = 'questions'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    question_text: Mapped[str] = mapped_column(db.Text, nullable=False)
    question_type: Mapped[QuestionType] = mapped_column(db.Enum(QuestionType), nullable=False, default=QuestionType.MULTIPLE_CHOICE)
    image_path: Mapped[Optional[str]] = mapped_column(db.String(500), nullable=True)  # Path to image file
    quiz_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False, index=True)
    order: Mapped[int] = mapped_column(db.Integer, nullable=False, default=1)
    description: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)  # For LONG_TEXT questions
    is_required: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)
    points: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)
    explanation: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)

    quiz: Mapped[Quiz] = relationship('Quiz', back_populates='questions')
    options: Mapped[List['Option']] = relationship('Option', back_populates='question', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self) -> str:
        """String representation of Question."""
        return f'<Question {self.question_text[:50]}>'

class Option(db.Model):
    """Option model for multiple choice answers."""
    __tablename__ = 'options'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    option_text: Mapped[str] = mapped_column(db.String(500), nullable=False)
    is_correct: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    question_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('questions.id'), nullable=False, index=True)
    order: Mapped[int] = mapped_column(db.Integer, nullable=False, default=1)

    question: Mapped[Question] = relationship('Question', back_populates='options')

    def __repr__(self) -> str:
        """String representation of Option."""
        return f'<Option {self.option_text}>'

class QuizSubmission(db.Model):
    """Quiz submission model for student answers."""
    __tablename__ = 'quiz_submissions'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    quiz_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    submitted_at: Mapped[datetime.datetime] = mapped_column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)
    score: Mapped[Optional[float]] = mapped_column(db.Float, nullable=True)  # Calculated score
    total_points: Mapped[int] = mapped_column(db.Integer, nullable=False)

    quiz: Mapped[Quiz] = relationship('Quiz', backref='submissions')
    user: Mapped['User'] = relationship('User', backref='quiz_submissions')
    answers: Mapped[List['Answer']] = relationship('Answer', back_populates='submission', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self) -> str:
        """String representation of QuizSubmission."""
        return f'<QuizSubmission quiz={self.quiz_id} user={self.user_id} score={self.score}>'


class Answer(db.Model):
    """Answer model for quiz submissions."""
    __tablename__ = 'answers'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    submission_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('quiz_submissions.id'), nullable=False, index=True)
    question_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('questions.id'), nullable=False, index=True)
    answer_text: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)  # For long text answers
    selected_option_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('options.id'), nullable=True)  # For multiple choice

    submission: Mapped[QuizSubmission] = relationship('QuizSubmission', back_populates='answers')
    question: Mapped[Question] = relationship('Question', backref='answers')
    selected_option: Mapped[Optional[Option]] = relationship('Option', backref='answers')

    def __repr__(self) -> str:
        """String representation of Answer."""
        return f'<Answer question={self.question_id} text={self.answer_text[:50] if self.answer_text else None}>'
