from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db
from app.helpers import get_jakarta_now


class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action: Mapped[str] = mapped_column(db.String(200), nullable=False)
    target_type: Mapped[Optional[str]] = mapped_column(db.String(50), nullable=True)
    target_id: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    details: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(db.String(45), nullable=True)
    school_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey('schools.id'), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=get_jakarta_now)

    # Relationships
    user = relationship('User', backref=db.backref('activity_logs', lazy=True))
    school = relationship('School', backref=db.backref('activity_logs', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'user_name': self.user.name,
            'user_role': self.user.role.value,
            'action': self.action,
            'details': self.details,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
