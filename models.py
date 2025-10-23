# models.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import enum

db = SQLAlchemy()

enrollments = db.Table('enrollments',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('course_id', db.Integer, db.ForeignKey('courses.id'), primary_key=True)
)

class UserRole(enum.Enum):
    GURU = 'guru'
    MURID = 'murid'
    ADMIN = 'admin'

class QuestionType(enum.Enum):
    MULTIPLE_CHOICE = 'multiple_choice'
    TRUE_FALSE = 'true_false'

# --- TAMBAHAN BARU ---
class GradeType(enum.Enum):
    NUMERIC = 'numeric'
    LETTER = 'letter'
# --- AKHIR TAMBAHAN ---

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.MURID)
    
    courses_taught = db.relationship('Course', back_populates='teacher', lazy='dynamic')
    courses_enrolled = db.relationship('Course', secondary=enrollments, lazy='subquery', back_populates='students')

    def set_password(self, password):
        # Use PBKDF2 to avoid dependency on hashlib.scrypt availability on some platforms
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.name} ({self.role.value})>'

class AcademicYear(db.Model):
    __tablename__ = 'academic_years'

    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.String(20), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=False, nullable=False)
    
    courses = db.relationship('Course', backref='academic_year', lazy='dynamic')

    def __repr__(self):
        return f'<AcademicYear {self.year}>'

class Course(db.Model):
    __tablename__ = 'courses'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    class_code = db.Column(db.String(8), unique=True, nullable=False, index=True)
    
    # Kolom baru untuk warna kartu
    color = db.Column(db.String(7), nullable=False, default='#0282c6') # Default warna biru
    
    academic_year_id = db.Column(db.Integer, db.ForeignKey('academic_years.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    teacher = db.relationship('User', back_populates='courses_taught')
    students = db.relationship('User', secondary=enrollments, lazy='subquery', back_populates='courses_enrolled')

    quizzes = db.relationship('Quiz', back_populates='course', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Course {self.name}>'
    
class Quiz(db.Model):
    __tablename__ = 'quizzes'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False, index=True)

    # --- KOLOM BARU YANG DITAMBAHKAN ---
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)
    points = db.Column(db.Integer, nullable=False, default=100)
    grading_category = db.Column(db.String(100), nullable=True)
    grade_type = db.Column(db.Enum(GradeType), nullable=False, default=GradeType.NUMERIC)
    # --- AKHIR KOLOM BARU ---

    # Relasi ke Course
    course = db.relationship('Course', back_populates='quizzes')
    # Relasi ke Questions
    questions = db.relationship('Question', back_populates='quiz', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Quiz {self.name}>'

class Question(db.Model):
    __tablename__ = 'questions'

    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.Enum(QuestionType), nullable=False, default=QuestionType.MULTIPLE_CHOICE)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False, index=True)

    # Relasi ke Quiz
    quiz = db.relationship('Quiz', back_populates='questions')
    # Relasi ke Options
    options = db.relationship('Option', back_populates='question', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Question {self.question_text[:50]}>'

class Option(db.Model):
    __tablename__ = 'options'

    id = db.Column(db.Integer, primary_key=True)
    option_text = db.Column(db.String(500), nullable=False)
    is_correct = db.Column(db.Boolean, default=False, nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False, index=True)

    # Relasi ke Question
    question = db.relationship('Question', back_populates='options')

    def __repr__(self):
        return f'<Option {self.option_text}>'