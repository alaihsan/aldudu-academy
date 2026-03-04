import datetime
import enum
from typing import List, Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from . import db

class QuestionType(enum.Enum):
    MULTIPLE_CHOICE = 'multiple_choice'
    TRUE_FALSE = 'true_false'
    DROPDOWN = 'dropdown'
    CHECKBOX = 'checkbox'
    LONG_TEXT = 'long_text'
    UPLOAD = 'upload'

class QuizStatus(enum.Enum):
    DRAFT = 'draft'
    PUBLISHED = 'published'
    UNPUBLISHED = 'unpublished'

class GradeType(enum.Enum):
    NUMERIC = 'numeric'
    LETTER = 'letter'

class Quiz(db.Model):
    __tablename__ = 'quizzes'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    
    # Theme & Style Settings
    theme_color: Mapped[str] = mapped_column(db.String(7), default='#673ab7')
    bg_pattern: Mapped[str] = mapped_column(db.String(50), default='none')
    font_question: Mapped[str] = mapped_column(db.String(50), default='Inter')
    font_answer: Mapped[str] = mapped_column(db.String(50), default='Inter')

    course_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    grade_type: Mapped[GradeType] = mapped_column(db.Enum(GradeType), nullable=False, default=GradeType.NUMERIC)
    
    # Status Management
    status: Mapped[QuizStatus] = mapped_column(db.Enum(QuizStatus), default=QuizStatus.DRAFT, nullable=False)
    
    points: Mapped[int] = mapped_column(db.Integer, default=100)
    is_published: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False) # Legacy, keeping for migration safety
    
    created_at: Mapped[datetime.datetime] = mapped_column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime.datetime] = mapped_column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    course: Mapped['Course'] = relationship('Course', back_populates='quizzes')
    questions: Mapped[List['Question']] = relationship('Question', back_populates='quiz', lazy='dynamic', cascade="all, delete-orphan")

class Question(db.Model):
    __tablename__ = 'questions'
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    question_text: Mapped[str] = mapped_column(db.Text, nullable=False)
    question_type: Mapped[QuestionType] = mapped_column(db.Enum(QuestionType), nullable=False, default=QuestionType.MULTIPLE_CHOICE)
    quiz_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False, index=True)
    order: Mapped[int] = mapped_column(db.Integer, nullable=False, default=1)
    description: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    is_required: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)
    points: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)
    max_file_size: Mapped[int] = mapped_column(db.Integer, default=10, nullable=False)
    allowed_file_types: Mapped[Optional[str]] = mapped_column(db.String(200), default='document')

    quiz: Mapped[Quiz] = relationship('Quiz', back_populates='questions')
    options: Mapped[List['Option']] = relationship('Option', back_populates='question', lazy='dynamic', cascade='all, delete-orphan')

class Option(db.Model):
    __tablename__ = 'options'
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    option_text: Mapped[str] = mapped_column(db.String(500), nullable=False)
    is_correct: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    question_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('questions.id'), nullable=False, index=True)
    order: Mapped[int] = mapped_column(db.Integer, nullable=False, default=1)
    question: Mapped[Question] = relationship('Question', back_populates='options')

class QuizSubmission(db.Model):
    __tablename__ = 'quiz_submissions'
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    quiz_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    submitted_at: Mapped[datetime.datetime] = mapped_column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)
    score: Mapped[Optional[float]] = mapped_column(db.Float, nullable=True)
    total_points: Mapped[int] = mapped_column(db.Integer, nullable=False)
    quiz: Mapped[Quiz] = relationship('Quiz', backref='submissions')
    user: Mapped['User'] = relationship('User', backref='quiz_submissions')
    answers: Mapped[List['Answer']] = relationship('Answer', back_populates='submission', lazy='dynamic', cascade='all, delete-orphan')

class Answer(db.Model):
    __tablename__ = 'answers'
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    submission_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('quiz_submissions.id'), nullable=False, index=True)
    question_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('questions.id'), nullable=False, index=True)
    answer_text: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    selected_option_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('options.id'), nullable=True)
    submission: Mapped[QuizSubmission] = relationship('QuizSubmission', back_populates='answers')
    question: Mapped[Question] = relationship('Question', backref='answers')
    selected_option: Mapped[Optional[Option]] = relationship('Option', backref='answers')
