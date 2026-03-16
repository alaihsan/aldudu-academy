import enum
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db
from app.helpers import get_jakarta_now


class GradeCategoryType(enum.Enum):
    FORMATIF = 'formatif'
    SUMATIF = 'sumatif'
    SIKAP = 'sikap'
    PORTFOLIO = 'portfolio'


class GradeCategory(db.Model):
    """Kategori Penilaian (Formatif, Sumatif, Sikap, Portfolio)"""
    __tablename__ = 'grade_categories'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(100), nullable=False)
    category_type: Mapped[GradeCategoryType] = mapped_column(
        db.Enum(GradeCategoryType), nullable=False, default=GradeCategoryType.FORMATIF
    )
    weight: Mapped[float] = mapped_column(db.Float, nullable=False, default=0.0)  # Bobot dalam persen
    description: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    course_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('courses.id'), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=get_jakarta_now)

    # Relationships
    course = relationship('Course', back_populates='grade_categories')
    grade_items: Mapped[List['GradeItem']] = relationship('GradeItem', back_populates='category', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category_type': self.category_type.value,
            'weight': self.weight,
            'description': self.description,
            'course_id': self.course_id,
        }

    def __repr__(self):
        return f'<GradeCategory {self.name} ({self.category_type.value})>'


class LearningObjective(db.Model):
    """Capaian Pembelajaran (CP)"""
    __tablename__ = 'learning_objectives'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    code: Mapped[str] = mapped_column(db.String(20), nullable=False)  # e.g., "CP-1"
    description: Mapped[str] = mapped_column(db.Text, nullable=False)
    course_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('courses.id'), nullable=False, index=True)
    order: Mapped[int] = mapped_column(db.Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=get_jakarta_now)

    # Relationships
    course = relationship('Course', back_populates='learning_objectives')
    learning_goals: Mapped[List['LearningGoal']] = relationship('LearningGoal', back_populates='learning_objective', lazy='dynamic', cascade='all, delete-orphan')
    grade_items: Mapped[List['GradeItem']] = relationship('GradeItem', back_populates='learning_objective', lazy='dynamic')

    __table_args__ = (
        db.UniqueConstraint('code', 'course_id', name='uq_cp_code_course'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'description': self.description,
            'course_id': self.course_id,
            'order': self.order,
            'goals_count': self.learning_goals.count(),
        }

    def __repr__(self):
        return f'<LearningObjective {self.code}>'


class LearningGoal(db.Model):
    """Tujuan Pembelajaran (TP)"""
    __tablename__ = 'learning_goals'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    learning_objective_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('learning_objectives.id'), nullable=False, index=True)
    code: Mapped[str] = mapped_column(db.String(20), nullable=False)  # e.g., "TP-1.1"
    description: Mapped[str] = mapped_column(db.Text, nullable=False)
    order: Mapped[int] = mapped_column(db.Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=get_jakarta_now)

    # Relationships
    learning_objective = relationship('LearningObjective', back_populates='learning_goals')
    grade_items: Mapped[List['GradeItem']] = relationship('GradeItem', back_populates='learning_goal', lazy='dynamic')

    __table_args__ = (
        db.UniqueConstraint('code', 'learning_objective_id', name='uq_tp_code_lo'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'description': self.description,
            'learning_objective_id': self.learning_objective_id,
            'order': self.order,
        }

    def __repr__(self):
        return f'<LearningGoal {self.code}>'


class GradeItem(db.Model):
    """Item Penilaian (Tugas, Ujian, Kuis, dll)"""
    __tablename__ = 'grade_items'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    
    # Category & Learning Objectives
    category_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('grade_categories.id'), nullable=False, index=True)
    learning_objective_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('learning_objectives.id'), nullable=True, index=True)
    learning_goal_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('learning_goals.id'), nullable=True, index=True)
    
    # Scoring
    max_score: Mapped[float] = mapped_column(db.Float, nullable=False, default=100.0)
    weight: Mapped[float] = mapped_column(db.Float, nullable=False, default=0.0)  # Bobot dalam kategori (%)
    
    # Timing
    due_date: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    course_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('courses.id'), nullable=False, index=True)
    
    # Quiz Integration
    quiz_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('quizzes.id'), nullable=True, index=True)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=get_jakarta_now)
    updated_at: Mapped[datetime] = mapped_column(db.DateTime, default=get_jakarta_now, onupdate=get_jakarta_now)

    # Relationships
    category = relationship('GradeCategory', back_populates='grade_items')
    learning_objective = relationship('LearningObjective', back_populates='grade_items')
    learning_goal = relationship('LearningGoal', back_populates='grade_items')
    course = relationship('Course', back_populates='grade_items')
    quiz = relationship('Quiz', backref='grade_item')
    grade_entries: Mapped[List['GradeEntry']] = relationship('GradeEntry', back_populates='grade_item', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category_id': self.category_id,
            'learning_objective_id': self.learning_objective_id,
            'learning_goal_id': self.learning_goal_id,
            'max_score': self.max_score,
            'weight': self.weight,
            'due_date': self.due_date.strftime('%Y-%m-%d') if self.due_date else None,
            'course_id': self.course_id,
            'quiz_id': self.quiz_id,
            'entries_count': self.grade_entries.count(),
        }

    def __repr__(self):
        return f'<GradeItem {self.name}>'


class GradeEntry(db.Model):
    """Nilai Siswa per Item Penilaian"""
    __tablename__ = 'grade_entries'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    grade_item_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('grade_items.id'), nullable=False, index=True)
    student_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    score: Mapped[Optional[float]] = mapped_column(db.Float, nullable=True)
    percentage: Mapped[Optional[float]] = mapped_column(db.Float, nullable=True)  # Score normalized to 0-100
    feedback: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    graded_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    graded_by: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=get_jakarta_now)
    updated_at: Mapped[datetime] = mapped_column(db.DateTime, default=get_jakarta_now, onupdate=get_jakarta_now)

    # Relationships
    grade_item = relationship('GradeItem', back_populates='grade_entries')
    student = relationship('User', foreign_keys=[student_id], backref='grade_entries')
    grader = relationship('User', foreign_keys=[graded_by])

    __table_args__ = (
        db.UniqueConstraint('grade_item_id', 'student_id', name='uq_grade_item_student'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'grade_item_id': self.grade_item_id,
            'student_id': self.student_id,
            'score': self.score,
            'percentage': self.percentage,
            'feedback': self.feedback,
            'graded_at': self.graded_at.strftime('%Y-%m-%d %H:%M:%S') if self.graded_at else None,
            'graded_by': self.graded_by,
        }

    def __repr__(self):
        return f'<GradeEntry Student:{self.student_id} Item:{self.grade_item_id} Score:{self.score}>'
