import enum
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db
from app.helpers import get_jakarta_now


class SchoolStatus(enum.Enum):
    PENDING = 'pending'
    VERIFIED = 'verified'
    ACTIVE = 'active'
    SUSPENDED = 'suspended'


class School(db.Model):
    __tablename__ = 'schools'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(200), nullable=False)
    slug: Mapped[str] = mapped_column(db.String(100), unique=True, nullable=False, index=True)
    address: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(db.String(20), nullable=True)
    email: Mapped[str] = mapped_column(db.String(100), nullable=False)
    admin_email: Mapped[str] = mapped_column(db.String(100), nullable=False)
    status: Mapped[SchoolStatus] = mapped_column(
        db.Enum(SchoolStatus), nullable=False, default=SchoolStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=get_jakarta_now)
    approved_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)

    # Relationships
    users: Mapped[List['User']] = relationship('User', back_populates='school', lazy='dynamic')
    academic_years: Mapped[List['AcademicYear']] = relationship('AcademicYear', back_populates='school', lazy='dynamic')
    tickets: Mapped[List['Ticket']] = relationship('Ticket', back_populates='school', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'email': self.email,
            'admin_email': self.admin_email,
            'status': self.status.value,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'approved_at': self.approved_at.strftime('%Y-%m-%d %H:%M:%S') if self.approved_at else None,
        }

    def __repr__(self):
        return f'<School {self.name} ({self.slug})>'
