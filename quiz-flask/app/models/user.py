import enum
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from app.extensions import db
from app.helpers import now_jakarta


class UserRole(enum.Enum):
    TEACHER = "teacher"
    STUDENT = "student"


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.STUDENT)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_jakarta)

    quizzes = db.relationship("Quiz", back_populates="creator", cascade="all, delete-orphan")
    submissions = db.relationship("QuizSubmission", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_teacher(self):
        return self.role == UserRole.TEACHER
