import secrets
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db
from app.helpers import get_jakarta_now


class EmailVerificationToken(db.Model):
    __tablename__ = 'email_verification_tokens'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    token: Mapped[str] = mapped_column(db.String(64), unique=True, nullable=False, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    school_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('schools.id'), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(db.DateTime, nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=get_jakarta_now)

    user = relationship('User', backref=db.backref('verification_tokens', lazy=True))
    school = relationship('School', backref=db.backref('verification_tokens', lazy=True))

    @staticmethod
    def generate(user_id=None, school_id=None, expires_hours=24):
        token = EmailVerificationToken(
            token=secrets.token_urlsafe(48),
            user_id=user_id,
            school_id=school_id,
            expires_at=get_jakarta_now() + timedelta(hours=expires_hours),
        )
        return token

    @property
    def is_expired(self):
        return get_jakarta_now() > self.expires_at

    @property
    def is_used(self):
        return self.used_at is not None

    @property
    def is_valid(self):
        return not self.is_expired and not self.is_used

    def __repr__(self):
        return f'<EmailVerificationToken {self.token[:8]}...>'


class PasswordResetToken(db.Model):
    __tablename__ = 'password_reset_tokens'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    token: Mapped[str] = mapped_column(db.String(64), unique=True, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(db.DateTime, nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=get_jakarta_now)

    user = relationship('User', backref=db.backref('password_reset_tokens', lazy=True))

    @staticmethod
    def generate(user_id, expires_hours=1):
        token = PasswordResetToken(
            token=secrets.token_urlsafe(48),
            user_id=user_id,
            expires_at=get_jakarta_now() + timedelta(hours=expires_hours),
        )
        return token

    @property
    def is_expired(self):
        return get_jakarta_now() > self.expires_at

    @property
    def is_used(self):
        return self.used_at is not None

    @property
    def is_valid(self):
        return not self.is_expired and not self.is_used

    def __repr__(self):
        return f'<PasswordResetToken {self.token[:8]}...>'
