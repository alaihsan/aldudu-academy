import re
from app.extensions import db
from app.models import (
    User, UserRole, School, SchoolStatus,
    EmailVerificationToken, PasswordResetToken
)
from app.services.email_service import (
    send_verification_email, send_password_reset_email,
    send_superadmin_new_school_notification
)


def is_valid_slug(slug):
    return bool(re.match(r'^[a-z0-9][a-z0-9-]{2,98}[a-z0-9]$', slug))


def register_school(name, slug, email, admin_name, admin_email, admin_password):
    if School.query.filter_by(slug=slug).first():
        return None, 'Slug sudah digunakan oleh sekolah lain'

    if User.query.filter_by(email=admin_email).first():
        return None, 'Email admin sudah terdaftar'

    if not is_valid_slug(slug):
        return None, 'Slug hanya boleh huruf kecil, angka, dan strip (min 4 karakter)'

    # Create school
    school = School(
        name=name,
        slug=slug,
        email=email,
        admin_email=admin_email,
        status=SchoolStatus.PENDING,
    )
    db.session.add(school)
    db.session.flush()

    # Create admin user
    admin_user = User(
        name=admin_name,
        email=admin_email,
        role=UserRole.ADMIN,
        is_active=True,
        email_verified=False,
        school_id=school.id,
    )
    admin_user.set_password(admin_password)
    db.session.add(admin_user)
    db.session.flush()

    # Generate verification token
    token = EmailVerificationToken.generate(user_id=admin_user.id, school_id=school.id)
    db.session.add(token)
    db.session.commit()

    # Send verification email
    send_verification_email(admin_user, school, token)

    return school, None


def verify_email_token(token_str):
    token = EmailVerificationToken.query.filter_by(token=token_str).first()
    if not token or not token.is_valid:
        return False, 'Token tidak valid atau sudah kadaluarsa'

    from app.helpers import get_jakarta_now
    token.used_at = get_jakarta_now().replace(tzinfo=None)

    if token.user_id:
        user = db.session.get(User, token.user_id)
        if user:
            user.email_verified = True

    if token.school_id:
        school = db.session.get(School, token.school_id)
        if school and school.status == SchoolStatus.PENDING:
            school.status = SchoolStatus.VERIFIED
            # Notify super admin
            send_superadmin_new_school_notification(school)

    db.session.commit()
    return True, 'Email berhasil diverifikasi'


def request_password_reset(email):
    user = User.query.filter_by(email=email).first()
    if not user:
        # Don't reveal whether email exists
        return True

    token = PasswordResetToken.generate(user_id=user.id)
    db.session.add(token)
    db.session.commit()

    send_password_reset_email(user, token)
    return True


def reset_password(token_str, new_password):
    token = PasswordResetToken.query.filter_by(token=token_str).first()
    if not token or not token.is_valid:
        return False, 'Token tidak valid atau sudah kadaluarsa'

    if len(new_password) < 6:
        return False, 'Password minimal 6 karakter'

    from app.helpers import get_jakarta_now
    token.used_at = get_jakarta_now().replace(tzinfo=None)

    user = db.session.get(User, token.user_id)
    if user:
        user.set_password(new_password)

    db.session.commit()
    return True, 'Password berhasil direset'
