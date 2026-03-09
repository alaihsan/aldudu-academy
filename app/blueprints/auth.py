from flask import Blueprint, request, jsonify, render_template, redirect
from flask_login import login_user, logout_user, current_user
from app.models import User, UserRole, SchoolStatus, PasswordResetToken
from app.helpers import is_valid_email, log_activity
from app.services.auth_service import (
    register_school, verify_email_token,
    request_password_reset, reset_password,
)

auth_bp = Blueprint('auth', __name__)


# ─── Page Routes ────────────────────────────────────

@auth_bp.route('/login')
def login_page():
    if current_user.is_authenticated:
        return _redirect_after_login(current_user)
    return render_template('index.html')


@auth_bp.route('/register')
def register_page():
    if current_user.is_authenticated:
        return _redirect_after_login(current_user)
    return render_template('auth/register.html')


@auth_bp.route('/verify-email/<token>')
def verify_email_page(token):
    success, message = verify_email_token(token)
    return render_template('auth/verify_email.html', success=success, message=message)


@auth_bp.route('/forgot-password')
def forgot_password_page():
    return render_template('auth/forgot_password.html')


@auth_bp.route('/reset-password/<token>')
def reset_password_page(token):
    token_obj = PasswordResetToken.query.filter_by(token=token).first()
    valid = token_obj is not None and token_obj.is_valid
    return render_template('auth/reset_password.html', valid=valid, token=token)


# ─── API Routes ─────────────────────────────────────

@auth_bp.route('/api/session', methods=['GET'])
def api_session():
    if current_user.is_authenticated:
        if not current_user.is_active:
            logout_user()
            return jsonify({'isAuthenticated': False})

        user_data = {
            'id': current_user.id,
            'name': current_user.name,
            'role': current_user.role.value,
            'school_id': current_user.school_id,
        }

        if current_user.school:
            user_data['school_slug'] = current_user.school.slug

        return jsonify({'isAuthenticated': True, 'user': user_data})
    return jsonify({'isAuthenticated': False})


@auth_bp.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')

    if not email or not password or not is_valid_email(email):
        return jsonify({'success': False, 'message': 'Email atau password tidak valid'}), 400

    user = User.query.filter_by(email=email.strip()).first()
    if not user or not user.check_password(password):
        return jsonify({'success': False, 'message': 'Email atau password salah'}), 401

    if not user.is_active:
        return jsonify({'success': False, 'message': 'Akun Anda telah dinonaktifkan. Hubungi admin.'}), 403

    if not user.email_verified and user.role != UserRole.SUPER_ADMIN:
        return jsonify({'success': False, 'message': 'Email belum diverifikasi. Cek inbox Anda.'}), 403

    if user.role != UserRole.SUPER_ADMIN:
        if not user.school:
            return jsonify({'success': False, 'message': 'Akun tidak terhubung ke sekolah manapun'}), 403
        if user.school.status != SchoolStatus.ACTIVE:
            return jsonify({'success': False, 'message': 'Sekolah Anda belum aktif atau telah disuspend'}), 403

    login_user(user)
    log_activity(user.id, "Login")

    response_data = {
        'success': True,
        'user': {
            'id': user.id,
            'name': user.name,
            'role': user.role.value,
        }
    }

    if user.role == UserRole.SUPER_ADMIN:
        response_data['redirect'] = '/superadmin/dashboard'
    elif user.school:
        response_data['redirect'] = f'/s/{user.school.slug}/dashboard'

    return jsonify(response_data)


@auth_bp.route('/api/logout', methods=['POST'])
def api_logout():
    if current_user.is_authenticated:
        user_id = current_user.id
        logout_user()
        log_activity(user_id, "Logout")
        return jsonify({'success': True})
    return jsonify({'success': False}), 401


@auth_bp.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json() or {}

    school_name = data.get('school_name', '').strip()
    slug = data.get('slug', '').strip().lower()
    school_email = data.get('school_email', '').strip()
    admin_name = data.get('admin_name', '').strip()
    admin_email = data.get('admin_email', '').strip()
    password = data.get('password', '')

    if not all([school_name, slug, school_email, admin_name, admin_email, password]):
        return jsonify({'success': False, 'message': 'Semua field wajib diisi'}), 400

    if not is_valid_email(school_email) or not is_valid_email(admin_email):
        return jsonify({'success': False, 'message': 'Format email tidak valid'}), 400

    if len(password) < 6:
        return jsonify({'success': False, 'message': 'Password minimal 6 karakter'}), 400

    school, error = register_school(
        name=school_name,
        slug=slug,
        email=school_email,
        admin_name=admin_name,
        admin_email=admin_email,
        admin_password=password,
    )

    if error:
        return jsonify({'success': False, 'message': error}), 400

    return jsonify({'success': True, 'message': 'Registrasi berhasil. Cek email untuk verifikasi.'}), 201


@auth_bp.route('/api/forgot-password', methods=['POST'])
def api_forgot_password():
    data = request.get_json() or {}
    email = data.get('email', '').strip()

    if not email or not is_valid_email(email):
        return jsonify({'success': True})

    request_password_reset(email)
    return jsonify({'success': True})


@auth_bp.route('/api/reset-password/<token>', methods=['POST'])
def api_reset_password(token):
    data = request.get_json() or {}
    password = data.get('password', '')

    success, message = reset_password(token, password)
    if not success:
        return jsonify({'success': False, 'message': message}), 400

    return jsonify({'success': True, 'message': message})


def _redirect_after_login(user):
    if user.role == UserRole.SUPER_ADMIN:
        return redirect('/superadmin/dashboard')
    if user.school:
        return redirect(f'/s/{user.school.slug}/dashboard')
    return redirect('/')
