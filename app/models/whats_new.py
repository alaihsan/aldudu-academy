from app.extensions import db
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Mapped, mapped_column


class WhatsNew(db.Model):
    """Model untuk pengumuman/platform updates dari Super Admin."""
    
    __tablename__ = 'whats_new'
    
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    title: Mapped[str] = mapped_column(db.String(200), nullable=False)
    content: Mapped[str] = mapped_column(db.Text, nullable=False)  # Markdown content
    author_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_published: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        db.DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        nullable=False
    )
    
    # Relationships
    author = db.relationship('User', backref=db.backref('whats_new_posts', lazy='dynamic'))
    
    def to_dict(self, include_author=False):
        """Convert to dictionary."""
        data = {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'is_published': self.is_published,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_author and self.author:
            data['author'] = {
                'id': self.author.id,
                'name': self.author.name,
                'role': self.author.role.value,
            }
        return data
    
    def __repr__(self):
        return f'<WhatsNew {self.title}>'
