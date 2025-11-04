"""
Database models for Aldudu Academy.

This module defines all SQLAlchemy models used in the application.
"""

import datetime
import enum
from typing import List, Optional

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()

enrollments = db.Table('enrollments',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('course_id', db.Integer, db.ForeignKey('courses.id'), primary_key=True)
)

class UserRole(enum.Enum):
    """User role enumeration."""
    GURU = 'guru'
    MURID = 'murid'
    ADMIN = 'admin'


class QuestionType(enum.Enum):
    """Question type enumeration."""
    MULTIPLE_CHOICE = 'multiple_choice'
    TRUE_FALSE = 'true_false'
    LONG_TEXT = 'long_text'


class GradeType(enum.Enum):
    """Grade type enumeration."""
    NUMERIC = 'numeric'
    LETTER = 'letter'

class User(UserMixin, db.Model):
    """User model representing teachers and students."""
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(100), nullable=False)
    email: Mapped[str] = mapped_column(db.String(100), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(db.String(256), nullable=False)
    role: Mapped[UserRole] = mapped_column(db.Enum(UserRole), nullable=False, default=UserRole.MURID)

    courses_taught: Mapped[List['Course']] = relationship('Course', back_populates='teacher', lazy='dynamic')
    courses_enrolled: Mapped[List['Course']] = relationship('Course', secondary=enrollments, lazy='subquery', back_populates='students')

    def set_password(self, password: str) -> None:
        """Set user password hash."""
        # Use PBKDF2 to avoid dependency on hashlib.scrypt availability on some platforms
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password: str) -> bool:
        """Check if password matches hash."""
        return check_password_hash(self.password_hash, password)

    def __eq__(self, other: object) -> bool:
        """Check equality by ID."""
        if isinstance(other, User):
            return self.id == other.id
        return False

    def __repr__(self) -> str:
        """String representation of User."""
        return f'<User {self.name} ({self.role.value})>'

class AcademicYear(db.Model):
    """Academic year model."""
    __tablename__ = 'academic_years'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    year: Mapped[str] = mapped_column(db.String(20), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)

    courses: Mapped[List['Course']] = relationship('Course', backref='academic_year', lazy='dynamic')

    def __repr__(self) -> str:
        """String representation of AcademicYear."""
        return f'<AcademicYear {self.year}>'

class Course(db.Model):
    """Course model representing class subjects."""
    __tablename__ = 'courses'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(150), nullable=False)
    class_code: Mapped[str] = mapped_column(db.String(8), unique=True, nullable=False, index=True)
    color: Mapped[str] = mapped_column(db.String(7), nullable=False, default='#0282c6')  # Default blue color

    academic_year_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('academic_years.id'), nullable=False)
    teacher_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    teacher: Mapped[User] = relationship('User', back_populates='courses_taught')
    students: Mapped[List[User]] = relationship('User', secondary=enrollments, lazy='subquery', back_populates='courses_enrolled')

    quizzes: Mapped[List['Quiz']] = relationship('Quiz', back_populates='course', lazy='dynamic', cascade='all, delete-orphan')
    links: Mapped[List['Link']] = relationship('Link', back_populates='course', lazy='dynamic', cascade='all, delete-orphan')
    files: Mapped[List['File']] = relationship('File', back_populates='course', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self) -> str:
        """String representation of Course."""
        return f'<Course {self.name}>'
    
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
    points: Mapped[int] = mapped_column(db.Integer, default=100)
    created_at: Mapped[datetime.datetime] = mapped_column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime.datetime] = mapped_column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    course: Mapped[Course] = relationship('Course', back_populates='quizzes')
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

class Link(db.Model):
    """Link model for course resources."""
    __tablename__ = 'links'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(200), nullable=False)
    url: Mapped[str] = mapped_column(db.String(500), nullable=False)
    course_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('courses.id'), nullable=False, index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(db.DateTime, default=datetime.datetime.utcnow)

    course: Mapped[Course] = relationship('Course', back_populates='links')

    def __repr__(self) -> str:
        """String representation of Link."""
        return f'<Link {self.name}>'


class File(db.Model):
    """File model for course resources."""
    __tablename__ = 'files'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    filename: Mapped[str] = mapped_column(db.String(200), nullable=False)
    course_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('courses.id'), nullable=False, index=True)
    start_date: Mapped[Optional[datetime.datetime]] = mapped_column(db.DateTime, nullable=True)
    end_date: Mapped[Optional[datetime.datetime]] = mapped_column(db.DateTime, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(db.DateTime, default=datetime.datetime.utcnow)

    course: Mapped[Course] = relationship('Course', back_populates='files')

    def __repr__(self) -> str:
        """String representation of File."""
        return f'<File {self.name}>'

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
    user: Mapped[User] = relationship('User', backref='quiz_submissions')
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
