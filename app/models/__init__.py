from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user import User, UserRole
from .course import Course, AcademicYear, Link, File, enrollments
from .quiz import Quiz, Question, Option, QuizSubmission, Answer, QuestionType, GradeType, QuizStatus
from .discussion import Discussion, Post, Like
