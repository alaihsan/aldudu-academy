import datetime
import enum
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.extensions import db
from app.helpers import get_jakarta_now


class KbmActivityType(enum.Enum):
    TEORI = 'teori'
    PRAKTIKUM = 'praktikum'
    UJIAN = 'ujian'
    TUGAS = 'tugas'
    REVIEW = 'review'
    LAINNYA = 'lainnya'


class KbmNote(db.Model):
    """Catatan Kegiatan Belajar Mengajar (KBM)"""
    __tablename__ = 'kbm_notes'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    course_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('courses.id'), nullable=False, index=True)
    teacher_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    # Activity details
    activity_date: Mapped[datetime.datetime] = mapped_column(db.DateTime, nullable=False)
    start_time: Mapped[Optional[datetime.time]] = mapped_column(db.Time, nullable=True)
    end_time: Mapped[Optional[datetime.time]] = mapped_column(db.Time, nullable=True)
    activity_type: Mapped[KbmActivityType] = mapped_column(db.Enum(KbmActivityType), nullable=False, default=KbmActivityType.TEORI)
    topic: Mapped[str] = mapped_column(db.String(200), nullable=False)  # Materi pokok
    description: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)  # Detail KBM
    notes: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)  # Catatan tambahan (refleksi, dll)

    # Metadata
    created_at: Mapped[datetime.datetime] = mapped_column(db.DateTime, default=get_jakarta_now)
    updated_at: Mapped[datetime.datetime] = mapped_column(db.DateTime, default=get_jakarta_now, onupdate=get_jakarta_now)

    # Relationships
    course = relationship('Course', back_populates='kbm_notes')
    teacher = relationship('User', foreign_keys=[teacher_id])

    def to_dict(self):
        return {
            'id': self.id,
            'course_id': self.course_id,
            'teacher_id': self.teacher_id,
            'activity_date': self.activity_date.strftime('%Y-%m-%d') if self.activity_date else None,
            'start_time': self.start_time.strftime('%H:%M') if self.start_time else None,
            'end_time': self.end_time.strftime('%H:%M') if self.end_time else None,
            'activity_type': self.activity_type.value,
            'topic': self.topic,
            'description': self.description,
            'notes': self.notes,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
        }

    def __repr__(self):
        return f'<KbmNote {self.topic} on {self.activity_date}>'
