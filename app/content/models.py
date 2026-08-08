import datetime
from typing import List, Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.extensions import db
from app.helpers import get_jakarta_now


class ContentFolder(db.Model):
    """Folder untuk mengorganisir konten/material dalam course"""
    __tablename__ = 'content_folders'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(200), nullable=False)
    course_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('courses.id'), nullable=False, index=True)
    parent_folder_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('content_folders.id'), nullable=True, index=True)

    # Manual ordering within course/folder
    order: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)

    created_at: Mapped[datetime.datetime] = mapped_column(db.DateTime, default=get_jakarta_now, nullable=False)
    updated_at: Mapped[datetime.datetime] = mapped_column(db.DateTime, default=get_jakarta_now, onupdate=get_jakarta_now, nullable=False)

    # Relationships
    course = relationship('Course', back_populates='content_folders')
    parent_folder = relationship('ContentFolder', remote_side=[id], back_populates='child_folders')
    child_folders: Mapped[List['ContentFolder']] = relationship('ContentFolder', remote_side=[parent_folder_id], back_populates='parent_folder', cascade='all, delete-orphan')

    # Materials in this folder
    quizzes: Mapped[List['Quiz']] = relationship('Quiz', back_populates='folder', foreign_keys='Quiz.folder_id')
    assignments: Mapped[List['Assignment']] = relationship('Assignment', back_populates='folder', foreign_keys='Assignment.folder_id')
    files: Mapped[List['File']] = relationship('File', back_populates='folder', foreign_keys='File.folder_id')
    links: Mapped[List['Link']] = relationship('Link', back_populates='folder', foreign_keys='Link.folder_id')

    def __repr__(self) -> str:
        return f'<ContentFolder {self.name} in Course:{self.course_id}>'

    def to_dict(self, include_children=False):
        """Convert to dictionary representation"""
        data = {
            'id': self.id,
            'name': self.name,
            'course_id': self.course_id,
            'parent_folder_id': self.parent_folder_id,
            'order': self.order,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

        if include_children:
            data['child_folders'] = [child.to_dict(include_children=True) for child in self.child_folders]
            data['quizzes'] = len(self.quizzes)
            data['assignments'] = len(self.assignments)
            data['files'] = len(self.files)
            data['links'] = len(self.links)
            data['total_items'] = data['quizzes'] + data['assignments'] + data['files'] + data['links']

        return data


class Link(db.Model):
    __tablename__ = 'links'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(200), nullable=False)
    url: Mapped[str] = mapped_column(db.String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    course_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('courses.id'), nullable=False, index=True)

    # Folder organization
    folder_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('content_folders.id'), nullable=True, index=True)
    order: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)

    # Archive status
    is_archived: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False, index=True)

    # Trash (Ruang TPS)
    is_trashed: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False, index=True)
    trashed_at: Mapped[Optional[datetime.datetime]] = mapped_column(db.DateTime, nullable=True)

    created_at: Mapped[datetime.datetime] = mapped_column(db.DateTime, default=get_jakarta_now)

    course: Mapped['Course'] = relationship('Course', back_populates='links')
    folder = relationship('ContentFolder', back_populates='links', foreign_keys=[folder_id])

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

    # Archive status
    is_archived: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False, index=True)

    # Trash (Ruang TPS)
    is_trashed: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False, index=True)
    trashed_at: Mapped[Optional[datetime.datetime]] = mapped_column(db.DateTime, nullable=True)

    # Folder organization
    folder_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('content_folders.id'), nullable=True, index=True)
    order: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)

    created_at: Mapped[datetime.datetime] = mapped_column(db.DateTime, default=get_jakarta_now)

    course: Mapped['Course'] = relationship('Course', back_populates='files')
    folder = relationship('ContentFolder', back_populates='files', foreign_keys=[folder_id])

    def __repr__(self) -> str:
        return f'<File {self.name}>'
