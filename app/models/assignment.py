from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db
from app.helpers import get_jakarta_now
import enum

class AssignmentStatus(enum.Enum):
    PUBLISHED = 'published'
    DRAFT = 'draft'
    ARCHIVED = 'archived'

class AssignmentSubmissionStatus(enum.Enum):
    SUBMITTED = 'submitted'
    GRADED = 'graded'

class Assignment(db.Model):
    __tablename__ = 'assignments'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    title: Mapped[str] = mapped_column(db.String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    course_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('courses.id'), nullable=False, index=True)
    due_date: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    max_score: Mapped[float] = mapped_column(db.Float, nullable=False, default=100.0)
    status: Mapped[AssignmentStatus] = mapped_column(db.Enum(AssignmentStatus), nullable=False, default=AssignmentStatus.PUBLISHED)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=get_jakarta_now)
    updated_at: Mapped[datetime] = mapped_column(db.DateTime, default=get_jakarta_now, onupdate=get_jakarta_now)

    course = relationship('Course', back_populates='assignments')
    submissions: Mapped[List['AssignmentSubmission']] = relationship('AssignmentSubmission', back_populates='assignment', lazy='dynamic', cascade='all, delete-orphan')
    grade_item = relationship('GradeItem', back_populates='assignment', uselist=False, cascade='all, delete-orphan')

    def __repr__(self) -> str:
        return f'<Assignment {self.title}>'

class AssignmentSubmission(db.Model):
    __tablename__ = 'assignment_submissions'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    assignment_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('assignments.id'), nullable=False, index=True)
    student_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    content: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    file_path: Mapped[Optional[str]] = mapped_column(db.String(500), nullable=True)
    status: Mapped[AssignmentSubmissionStatus] = mapped_column(db.Enum(AssignmentSubmissionStatus), nullable=False, default=AssignmentSubmissionStatus.SUBMITTED)
    submitted_at: Mapped[datetime] = mapped_column(db.DateTime, default=get_jakarta_now)
    updated_at: Mapped[datetime] = mapped_column(db.DateTime, default=get_jakarta_now, onupdate=get_jakarta_now)

    assignment = relationship('Assignment', back_populates='submissions')
    student = relationship('User', foreign_keys=[student_id])

    __table_args__ = (
        db.UniqueConstraint('assignment_id', 'student_id', name='uq_assignment_student'),
    )

    def __repr__(self) -> str:
        return f'<AssignmentSubmission Assignment:{self.assignment_id} Student:{self.student_id}>'
