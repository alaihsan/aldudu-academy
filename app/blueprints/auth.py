import re
from flask import Blueprint, request, jsonify, render_template, redirect
from flask_login import login_user, logout_user, current_user, login_required
from app.models import User, UserRole, SchoolStatus, PasswordResetToken, School
from app.helpers import is_valid_email, log_activity
from app.extensions import limiter, db
from app.services.auth_service import (
    register_school, verify_email_token,
    request_password_reset, reset_password, register_user,
)

auth_bp = Blueprint('auth', __name__)


def validate_password(password):
    """
    Validate password strength.
    Returns (is_valid, error_message)
    Requirements:
    - Minimum 6 characters
    - At least 1 uppercase letter
    - At least 1 number
    - At least 1 symbol
    """
    if len(password) < 6:
        return False, 'Password minimal 6 karakter'
    if not re.search(r'[A-Z]', password):
        return False, 'Password harus mengandung minimal 1 huruf kapital'
    if not re.search(r'\d', password):
        return False, 'Password harus mengandung minimal 1 angka'
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, 'Password harus mengandung minimal 1 simbol (!@#$%^&*(),.?":{}|<>)'
    return True, None


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
@limiter.limit("20 per minute")
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
@limiter.limit("10 per minute; 50 per hour")
def api_login():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')

    if not email or not password or not is_valid_email(email):
        return jsonify({'success': False, 'message': 'Email atau password tidak valid'}), 400

    user = User.query.filter_by(email=email.strip()).first()
    if not user:
        return jsonify({'success': False, 'message': 'Email tidak terdaftar', 'field': 'email'}), 401
    if not user.check_password(password):
        return jsonify({'success': False, 'message': 'Password salah', 'field': 'password'}), 401

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
    elif user.role == UserRole.ADMIN and user.school:
        response_data['redirect'] = '/admin/dashboard'
    elif user.school:
        response_data['redirect'] = '/dashboard'

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
@limiter.limit("5 per hour")
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

    is_valid, error_msg = validate_password(password)
    if not is_valid:
        return jsonify({'success': False, 'message': error_msg}), 400

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
@limiter.limit("5 per hour")
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


@auth_bp.route('/api/schools', methods=['GET'])
def api_get_schools():
    """Get list of active schools for registration dropdown"""
    schools = School.query.filter_by(status=SchoolStatus.ACTIVE).order_by(School.name).all()
    result = [
        {
            'id': school.id,
            'name': school.name,
            'slug': school.slug,
        }
        for school in schools
    ]
    return jsonify({'success': True, 'schools': result})


@auth_bp.route('/api/register-user', methods=['POST'])
@limiter.limit("5 per hour")
def api_register_user():
    """Register a new user (murid/guru) and enroll to selected school"""
    data = request.get_json() or {}

    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    role = data.get('role', '').lower()
    school_id = data.get('school_id')

    # Validate required fields
    if not all([name, email, password, role, school_id]):
        return jsonify({'success': False, 'message': 'Semua field wajib diisi'}), 400

    # Validate role
    if role not in ['murid', 'guru']:
        return jsonify({'success': False, 'message': 'Role harus murid atau guru'}), 400

    # Validate email format
    if not is_valid_email(email):
        return jsonify({'success': False, 'message': 'Format email tidak valid'}), 400

    # Validate password strength
    is_valid, error_msg = validate_password(password)
    if not is_valid:
        return jsonify({'success': False, 'message': error_msg}), 400

    # Check if email already exists
    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': 'Email sudah terdaftar'}), 400

    # Check if school exists and is active
    school = School.query.filter_by(id=school_id, status=SchoolStatus.ACTIVE).first()
    if not school:
        return jsonify({'success': False, 'message': 'Sekolah tidak ditemukan atau belum aktif'}), 404

    # Register user
    user, error = register_user(
        name=name,
        email=email,
        password=password,
        role=role,
        school_id=school_id,
    )

    if error:
        return jsonify({'success': False, 'message': error}), 400

    return jsonify({'success': True, 'message': 'Registrasi berhasil. Cek email untuk verifikasi.'}), 201


@auth_bp.route('/api/profile', methods=['PUT'])
@login_required
def api_update_profile():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    if not name or len(name) < 2:
        return jsonify({'success': False, 'message': 'Nama minimal 2 karakter'}), 400
    if len(name) > 100:
        return jsonify({'success': False, 'message': 'Nama maksimal 100 karakter'}), 400
    current_user.name = name
    db.session.commit()
    return jsonify({'success': True, 'message': 'Profil berhasil diperbarui'})


@auth_bp.route('/api/change-password', methods=['PUT'])
@login_required
def api_change_password():
    data = request.get_json() or {}
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')

    if not old_password or not new_password:
        return jsonify({'success': False, 'message': 'Semua field wajib diisi'}), 400
    if not current_user.check_password(old_password):
        return jsonify({'success': False, 'message': 'Password lama salah'}), 401
    
    is_valid, error_msg = validate_password(new_password)
    if not is_valid:
        return jsonify({'success': False, 'message': error_msg}), 400

    current_user.set_password(new_password)
    db.session.commit()
    log_activity(current_user.id, "Ganti password")
    return jsonify({'success': True, 'message': 'Password berhasil diubah'})


@auth_bp.route('/api/activity-logs', methods=['GET'])
@login_required
def api_activity_logs():
    from app.models import ActivityLog
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    per_page = min(per_page, 100)

    is_teacher = current_user.role in (UserRole.GURU, UserRole.ADMIN)

    if is_teacher and current_user.school_id:
        query = ActivityLog.query.filter_by(school_id=current_user.school_id)
    else:
        query = ActivityLog.query.filter_by(user_id=current_user.id)

    query = query.order_by(ActivityLog.created_at.desc())
    total = query.count()
    logs = query.offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        'success': True,
        'logs': [log.to_dict() for log in logs],
        'has_more': (page * per_page) < total
    })


def _redirect_after_login(user):
    if user.role == UserRole.SUPER_ADMIN:
        return redirect('/superadmin/dashboard')
    if user.role == UserRole.ADMIN and user.school:
        return redirect('/admin/dashboard')
    if user.school:
        return redirect('/dashboard')
    return redirect('/')
