import enum
from typing import List, Optional
from flask_login import UserMixin
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash
from app.extensions import db


class UserRole(enum.Enum):
    SUPER_ADMIN = 'super_admin'
    ADMIN = 'admin'
    GURU = 'guru'
    MURID = 'murid'


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(100), nullable=False)
    email: Mapped[str] = mapped_column(db.String(100), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(db.String(256), nullable=False)
    role: Mapped[UserRole] = mapped_column(db.Enum(UserRole), nullable=False, default=UserRole.MURID)
    is_active: Mapped[bool] = mapped_column(db.Boolean, nullable=False, default=True)
    email_verified: Mapped[bool] = mapped_column(db.Boolean, nullable=False, default=False)
    school_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey('schools.id'), nullable=True, index=True
    )

    # Relationships
    school = relationship('School', back_populates='users')
    courses_taught: Mapped[List['Course']] = relationship('Course', back_populates='teacher', lazy='dynamic')
    courses_enrolled: Mapped[List['Course']] = relationship(
        'Course', secondary='enrollments', lazy='subquery', back_populates='students'
    )

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'role': self.role.value,
            'school_id': self.school_id,
        }

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, User):
            return self.id == other.id
        return False

    def __repr__(self) -> str:
        return f'<User {self.name} ({self.role.value})>'
