import enum
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db
from app.helpers import get_jakarta_now


class TicketCategory(enum.Enum):
    TECHNICAL = 'technical'
    ACCOUNT = 'account'
    COURSE = 'course'
    QUIZ = 'quiz'
    GENERAL = 'general'


class TicketStatus(enum.Enum):
    OPEN = 'open'
    IN_QUEUE = 'in_queue'
    IN_PROGRESS = 'in_progress'
    WAITING_USER = 'waiting_user'
    RESOLVED = 'resolved'
    CLOSED = 'closed'


class TicketPriority(enum.Enum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    URGENT = 'urgent'


class Ticket(db.Model):
    __tablename__ = 'tickets'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    ticket_number: Mapped[str] = mapped_column(db.String(20), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(db.String(200), nullable=False)
    description: Mapped[str] = mapped_column(db.Text, nullable=False)
    category: Mapped[TicketCategory] = mapped_column(
        db.Enum(TicketCategory), nullable=False, default=TicketCategory.GENERAL
    )
    status: Mapped[TicketStatus] = mapped_column(
        db.Enum(TicketStatus), nullable=False, default=TicketStatus.OPEN
    )
    priority: Mapped[TicketPriority] = mapped_column(
        db.Enum(TicketPriority), nullable=False, default=TicketPriority.MEDIUM
    )
    school_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey('schools.id'), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey('users.id'), nullable=False
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=get_jakarta_now)
    updated_at: Mapped[datetime] = mapped_column(db.DateTime, default=get_jakarta_now, onupdate=get_jakarta_now)

    # Relationships
    school = relationship('School', back_populates='tickets')
    user = relationship('User', backref=db.backref('tickets', lazy='dynamic'))
    messages: Mapped[List['TicketMessage']] = relationship(
        'TicketMessage', back_populates='ticket', lazy='dynamic',
        cascade='all, delete-orphan', order_by='TicketMessage.created_at'
    )

    def to_dict(self, include_messages=False):
        data = {
            'id': self.id,
            'ticket_number': self.ticket_number,
            'title': self.title,
            'description': self.description,
            'category': self.category.value,
            'status': self.status.value,
            'priority': self.priority.value,
            'school_id': self.school_id,
            'school_name': self.school.name if self.school else None,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else None,
            'resolved_at': self.resolved_at.strftime('%Y-%m-%d %H:%M:%S') if self.resolved_at else None,
            'closed_at': self.closed_at.strftime('%Y-%m-%d %H:%M:%S') if self.closed_at else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        }
        if include_messages:
            data['messages'] = [m.to_dict() for m in self.messages.all()]
        return data

    def __repr__(self):
        return f'<Ticket {self.ticket_number}>'


class TicketMessage(db.Model):
    __tablename__ = 'ticket_messages'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    ticket_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey('tickets.id'), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey('users.id'), nullable=False
    )
    content: Mapped[str] = mapped_column(db.Text, nullable=False)
    is_internal: Mapped[bool] = mapped_column(db.Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=get_jakarta_now)

    # Relationships
    ticket = relationship('Ticket', back_populates='messages')
    user = relationship('User', backref=db.backref('ticket_messages', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'ticket_id': self.ticket_id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else None,
            'user_role': self.user.role.value if self.user else None,
            'content': self.content,
            'is_internal': self.is_internal,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        }

    def __repr__(self):
        return f'<TicketMessage #{self.id} on Ticket #{self.ticket_id}>'
