import datetime
from typing import List, Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db
from app.helpers import get_jakarta_now

enrollments = db.Table('enrollments',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('course_id', db.Integer, db.ForeignKey('courses.id'), primary_key=True)
)


class AcademicYear(db.Model):
    __tablename__ = 'academic_years'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    year: Mapped[str] = mapped_column(db.String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    school_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey('schools.id'), nullable=True, index=True
    )

    __table_args__ = (
        db.UniqueConstraint('year', 'school_id', name='uq_academic_year_school'),
    )

    courses: Mapped[List['Course']] = relationship('Course', backref='academic_year', lazy='dynamic')
    school = relationship('School', back_populates='academic_years')

    def __repr__(self) -> str:
        return f'<AcademicYear {self.year}>'


class Course(db.Model):
    __tablename__ = 'courses'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(150), nullable=False)
    class_code: Mapped[str] = mapped_column(db.String(8), nullable=False, index=True)
    color: Mapped[str] = mapped_column(db.String(7), nullable=False, default='#0282c6')

    academic_year_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('academic_years.id'), nullable=False)
    teacher_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    teacher: Mapped['User'] = relationship('User', back_populates='courses_taught')
    students: Mapped[List['User']] = relationship('User', secondary=enrollments, lazy='subquery', back_populates='courses_enrolled')

    quizzes: Mapped[List['Quiz']] = relationship('Quiz', back_populates='course', lazy='dynamic', cascade='all, delete-orphan')
    links: Mapped[List['Link']] = relationship('Link', back_populates='course', lazy='dynamic', cascade='all, delete-orphan')
    files: Mapped[List['File']] = relationship('File', back_populates='course', lazy='dynamic', cascade='all, delete-orphan')
    discussions: Mapped[List['Discussion']] = relationship('Discussion', back_populates='course', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self) -> str:
        return f'<Course {self.name}>'


class UserCourseOrder(db.Model):
    __tablename__ = 'user_course_orders'

    user_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    course_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('courses.id'), primary_key=True)
    manual_order: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return f'<UserCourseOrder User:{self.user_id} Course:{self.course_id} Order:{self.manual_order}>'


class Link(db.Model):
    __tablename__ = 'links'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(200), nullable=False)
    url: Mapped[str] = mapped_column(db.String(500), nullable=False)
    course_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('courses.id'), nullable=False, index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(db.DateTime, default=get_jakarta_now)

    course: Mapped[Course] = relationship('Course', back_populates='links')

    def __repr__(self) -> str:
        return f'<Link {self.name}>'


class File(db.Model):
    __tablename__ = 'files'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    filename: Mapped[str] = mapped_column(db.String(200), nullable=False)
    course_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('courses.id'), nullable=False, index=True)
    start_date: Mapped[Optional[datetime.datetime]] = mapped_column(db.DateTime, nullable=True)
    end_date: Mapped[Optional[datetime.datetime]] = mapped_column(db.DateTime, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(db.DateTime, default=get_jakarta_now)

    course: Mapped['Course'] = relationship('Course', back_populates='files')

    def __repr__(self) -> str:
        return f'<File {self.name}>'
