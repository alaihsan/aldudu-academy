import datetime
from typing import List, Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from . import db

class Discussion(db.Model):
    """Discussion model for course topics."""
    __tablename__ = 'discussions'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    title: Mapped[str] = mapped_column(db.String(200), nullable=False)
    course_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('courses.id'), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(db.DateTime, default=datetime.datetime.utcnow)
    closed: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)

    course: Mapped['Course'] = relationship('Course', backref='discussions')
    user: Mapped['User'] = relationship('User', backref='discussions')
    posts: Mapped[List['Post']] = relationship('Post', back_populates='discussion', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'title': self.title,
            'created_at': self.created_at.isoformat(),
            'closed': self.closed,
            'user': self.user.to_dict(),
            'posts': [p.to_dict() for p in self.posts]
        }

    def __repr__(self) -> str:
        return f'<Discussion {self.title}>'


class Post(db.Model):
    """Post model for discussion messages."""
    __tablename__ = 'posts'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    content: Mapped[str] = mapped_column(db.Text, nullable=False)
    discussion_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('discussions.id'), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    parent_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('posts.id'), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(db.DateTime, default=datetime.datetime.utcnow)

    discussion: Mapped['Discussion'] = relationship('Discussion', back_populates='posts')
    user: Mapped['User'] = relationship('User', backref='posts')
    parent: Mapped[Optional['Post']] = relationship('Post', remote_side=[id], backref='replies')
    likes: Mapped[List['Like']] = relationship('Like', back_populates='post', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'content': self.content,
            'created_at': self.created_at.isoformat(),
            'user': self.user.to_dict(),
            'parent_id': self.parent_id,
            'replies': [r.to_dict() for r in self.replies],
            'likes': [l.to_dict() for l in self.likes]
        }

    def __repr__(self) -> str:
        return f'<Post {self.id}>'


class Like(db.Model):
    """Like model for posts."""
    __tablename__ = 'likes'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    post_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('posts.id'), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    post: Mapped['Post'] = relationship('Post', back_populates='likes')
    user: Mapped['User'] = relationship('User', backref='likes')

    __table_args__ = (db.UniqueConstraint('post_id', 'user_id', name='_post_user_uc'),)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'user': self.user.to_dict()
        }

    def __repr__(self) -> str:
        """String representation of Like."""
        return f'<Like post={self.post_id} user={self.user_id}>'
