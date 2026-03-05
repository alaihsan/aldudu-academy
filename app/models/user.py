import enum
from typing import List
from flask_login import UserMixin
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash
from . import db

class UserRole(enum.Enum):
    """User role enumeration."""
    GURU = 'guru'
    MURID = 'murid'
    ADMIN = 'admin'

class User(UserMixin, db.Model):
    """User model representing teachers and students."""
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(100), nullable=False)
    email: Mapped[str] = mapped_column(db.String(100), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(db.String(256), nullable=False)
    role: Mapped[UserRole] = mapped_column(db.Enum(UserRole), nullable=False, default=UserRole.MURID)
    is_active: Mapped[bool] = mapped_column(db.Boolean, nullable=False, default=True)

    courses_taught: Mapped[List['Course']] = relationship('Course', back_populates='teacher', lazy='dynamic')
    courses_enrolled: Mapped[List['Course']] = relationship('Course', secondary='enrollments', lazy='subquery', back_populates='students')

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'role': self.role.value
        }

    def set_password(self, password: str) -> None:
        """Set user password hash."""
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
