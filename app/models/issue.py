from datetime import datetime
import enum
from . import db
from app.helpers import get_jakarta_now

class IssueStatus(enum.Enum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    CLOSED = "Closed"

class IssuePriority(enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    URGENT = "Urgent"

class Issue(db.Model):
    __tablename__ = 'issues'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.Enum(IssueStatus), default=IssueStatus.OPEN)
    priority = db.Column(db.Enum(IssuePriority), default=IssuePriority.MEDIUM)
    
    # Relationships
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('issues', lazy=True))
    
    created_at = db.Column(db.DateTime, default=get_jakarta_now)
    updated_at = db.Column(db.DateTime, default=get_jakarta_now, onupdate=get_jakarta_now)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status.value,
            'priority': self.priority.value,
            'user_id': self.user_id,
            'user_name': self.user.name,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }
