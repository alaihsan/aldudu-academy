from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from . import db

class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action: Mapped[str] = mapped_column(db.String(200), nullable=False) # e.g., "Create Course", "Login"
    target_type: Mapped[str] = mapped_column(db.String(50), nullable=True) # e.g., "Course", "Quiz"
    target_id: Mapped[int] = mapped_column(db.Integer, nullable=True)
    details: Mapped[str] = mapped_column(db.Text, nullable=True) # JSON or descriptive string
    ip_address: Mapped[str] = mapped_column(db.String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship('User', backref=db.backref('activity_logs', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'user_name': self.user.name,
            'user_role': self.user.role.value,
            'action': self.action,
            'details': self.details,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
