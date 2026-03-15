from flask import current_app, render_template
from flask_mail import Message
from app.extensions import mail


def send_email(subject, recipients, html_body, text_body=None):
    try:
        msg = Message(subject=subject, recipients=recipients)
        msg.html = html_body
        if text_body:
            msg.body = text_body
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send email to {recipients}: {e}")
        return False


def send_verification_email(user, school, token):
    app_url = current_app.config.get('APP_URL', 'http://localhost:5000')
    verify_url = f"{app_url}/verify-email/{token.token}"

    html = render_template('emails/verify_email.html',
        user_name=user.name,
        school_name=school.name,
        verify_url=verify_url,
    )
    return send_email(
        subject=f'Verifikasi Email - {school.name} | Aldudu Academy',
        recipients=[user.email],
        html_body=html,
    )


def send_password_reset_email(user, token):
    app_url = current_app.config.get('APP_URL', 'http://localhost:5000')
    reset_url = f"{app_url}/reset-password/{token.token}"

    html = render_template('emails/reset_password.html',
        user_name=user.name,
        reset_url=reset_url,
    )
    return send_email(
        subject='Reset Password - Aldudu Academy',
        recipients=[user.email],
        html_body=html,
    )


def send_school_approved_email(admin_user, school):
    app_url = current_app.config.get('APP_URL', 'http://localhost:5000')
    login_url = f"{app_url}/login"

    html = render_template('emails/school_approved.html',
        admin_name=admin_user.name,
        school_name=school.name,
        school_slug=school.slug,
        login_url=login_url,
    )
    return send_email(
        subject=f'Sekolah Disetujui - {school.name} | Aldudu Academy',
        recipients=[admin_user.email],
        html_body=html,
    )


def send_ticket_update_email(ticket, message_content, is_resolved=False):
    html = render_template('emails/ticket_update.html',
        ticket_number=ticket.ticket_number,
        ticket_title=ticket.title,
        message_content=message_content,
        is_resolved=is_resolved,
    )
    return send_email(
        subject=f'Update Ticket {ticket.ticket_number} - Aldudu Academy',
        recipients=[ticket.user.email],
        html_body=html,
    )


def send_superadmin_new_school_notification(school):
    from app.models import User, UserRole
    superadmin = User.query.filter_by(role=UserRole.SUPER_ADMIN).first()
    if not superadmin:
        return False

    app_url = current_app.config.get('APP_URL', 'http://localhost:5000')
    html = render_template('emails/new_school_notification.html',
        school_name=school.name,
        school_slug=school.slug,
        school_admin_email=school.admin_email,
        registered_at=school.created_at.strftime('%d %B %Y, %H:%M WIB') if school.created_at else '-',
        dashboard_url=f"{app_url}/superadmin/schools",
    )
    return send_email(
        subject=f'[Pendaftaran Baru] {school.name} Menunggu Approval',
        recipients=[superadmin.email],
        html_body=html,
    )
