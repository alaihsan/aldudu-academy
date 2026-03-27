from flask import Blueprint, render_template, request, jsonify, abort
import re
import logging
from flask_login import login_required, current_user
from app.models import db, User, UserRole, ActivityLog, Course, AcademicYear, QuizSubmission, Quiz
from app.helpers import log_activity, sanitize_text, is_valid_email, generate_random_password
from sqlalchemy import func
from app.tenant import get_school_id_or_abort

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


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

@admin_bp.before_request
@login_required
def admin_required():
    if current_user.role != UserRole.ADMIN:
        abort(403)
    if not current_user.school_id:
        abort(403, description='Akun admin tidak terhubung ke sekolah')

@admin_bp.route('/dashboard')
def dashboard():
    school_id = current_user.school_id
    # Statistics - filtered by school
    stats = {
        'total_guru': User.query.filter_by(role=UserRole.GURU, school_id=school_id).count(),
        'total_murid': User.query.filter_by(role=UserRole.MURID, school_id=school_id).count(),
        'total_courses': Course.query.join(AcademicYear).filter(AcademicYear.school_id == school_id).count(),
        'total_submissions': QuizSubmission.query.join(Quiz).join(Course).join(AcademicYear).filter(AcademicYear.school_id == school_id).count()
    }

    # Recent Activities - filtered by school
    recent_logs = ActivityLog.query.filter_by(school_id=school_id).order_by(ActivityLog.created_at.desc()).limit(20).all()

    return render_template('admin_dashboard.html', stats=stats, recent_logs=recent_logs)

@admin_bp.route('/users')
def user_management():
    school_id = current_user.school_id
    gurus = User.query.filter_by(role=UserRole.GURU, school_id=school_id).order_by(User.name).all()
    murids = User.query.filter_by(role=UserRole.MURID, school_id=school_id).order_by(User.name).all()
    return render_template('admin_users.html', gurus=gurus, murids=murids)


@admin_bp.route('/api/users', methods=['GET'])
def api_get_users():
    """Get list of users (guru and murid) with pagination."""
    role_filter = request.args.get('role')  # 'guru', 'murid', or None for all
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    per_page = min(per_page, 100)

    school_id = current_user.school_id
    query = User.query.filter_by(school_id=school_id)

    if role_filter:
        try:
            role = UserRole(role_filter)
            query = query.filter_by(role=role)
        except ValueError:
            pass

    # Order by role (guru first) then by name
    pagination = query.order_by(User.role.desc(), User.name).paginate(
        page=page, per_page=per_page, error_out=False
    )

    result = []
    for user in pagination.items:
        result.append({
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role.value,
            'is_active': user.is_active,
            'email_verified': user.email_verified,
        })

    return jsonify({
        'success': True,
        'users': result,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
    })

@admin_bp.route('/api/users/bulk-import', methods=['POST'])
def bulk_import_users():
    data = request.get_json() or {}
    raw_text = data.get('raw_data', '')
    role_str = data.get('role', 'murid').lower()
    
    if not raw_text:
        return jsonify({'success': False, 'message': 'Data tidak boleh kosong'}), 400
        
    try:
        role = UserRole(role_str)
    except ValueError:
        return jsonify({'success': False, 'message': 'Role tidak valid'}), 400

    lines = raw_text.strip().split('\n')
    
    # Pre-parse lines to get all emails for a single batch query
    parsed_entries = []
    emails_to_check = set()
    
    for line in lines:
        line = line.strip()
        if not line: continue
        
        parts = re.split(r'\t+| {2,}|[|;,]', line)
        parts = [p.strip() for p in parts if p.strip()]
        
        if len(parts) < 2:
            if ' ' in line and is_valid_email(line.split(' ')[-1]):
                temp_parts = line.split(' ')
                email = temp_parts[-1].lower()
                name = " ".join(temp_parts[:-1])
            else: continue
        else:
            email = parts[-1].lower()
            name = " ".join(parts[:-1])
            
        if is_valid_email(email):
            parsed_entries.append({'name': sanitize_text(name, 100), 'email': email})
            emails_to_check.add(email)

    if not parsed_entries:
        return jsonify({'success': False, 'message': 'Tidak ada data valid yang ditemukan'}), 400

    try:
        # Optimization: Fetch all existing users in this list at once
        existing_users = User.query.filter(User.email.in_(list(emails_to_check))).all()
        existing_emails = {u.email for u in existing_users}
        
        imported_count = 0
        results = []

        for entry in parsed_entries:
            if entry['email'] in existing_emails:
                continue
            
            password = generate_random_password(4)
            user = User(name=entry['name'], email=entry['email'], role=role, school_id=current_user.school_id)
            user.set_password(password)
            db.session.add(user)
            
            # Avoid duplicate in same batch
            existing_emails.add(entry['email'])
            
            results.append({'name': entry['name'], 'email': entry['email'], 'password': password})
            imported_count += 1

        db.session.commit()
        log_activity(current_user.id, f"Impor massal {imported_count} {role.value}", details=f"Mendaftarkan {imported_count} user baru.")

        return jsonify({'success': True, 'count': imported_count, 'results': results})
    except Exception as e:
        db.session.rollback()
        logger.error(f"IMPORT ERROR: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': f'Gagal menyimpan ke database: {str(e)}'}), 500

@admin_bp.route('/api/users/<int:user_id>/reset-password', methods=['POST'])
def reset_password(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User tidak ditemukan'}), 404

    if user.school_id != current_user.school_id:
        return jsonify({'success': False, 'message': 'Tidak memiliki izin'}), 403

    data = request.get_json() or {}
    new_password = data.get('password', '').strip()

    is_valid, error_msg = validate_password(new_password)
    if not is_valid:
        return jsonify({'success': False, 'message': error_msg}), 400
        
    user.set_password(new_password)
    db.session.commit()
    
    log_activity(current_user.id, f"Reset password user: {user.email}", target_id=user.id)
    return jsonify({'success': True, 'message': 'Password berhasil diubah'})

@admin_bp.route('/api/users/<int:user_id>/toggle-status', methods=['POST'])
def toggle_user_status(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User tidak ditemukan'}), 404

    if user.school_id != current_user.school_id:
        return jsonify({'success': False, 'message': 'Tidak memiliki izin'}), 403

    if user.id == current_user.id:
        return jsonify({'success': False, 'message': 'Anda tidak dapat menonaktifkan akun sendiri'}), 400
        
    user.is_active = not user.is_active
    db.session.commit()
    
    action = "Mengaktifkan" if user.is_active else "Menonaktifkan"
    log_activity(current_user.id, f"{action} akun: {user.email}", target_type="User", target_id=user.id)

    return jsonify({'success': True, 'is_active': user.is_active})

@admin_bp.route('/api/users/<int:user_id>/rename', methods=['PATCH'])
def rename_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User tidak ditemukan'}), 404

    if user.school_id != current_user.school_id:
        return jsonify({'success': False, 'message': 'Tidak memiliki izin'}), 403

    if user.role not in (UserRole.GURU, UserRole.MURID):
        return jsonify({'success': False, 'message': 'Hanya guru dan murid yang bisa direname'}), 403

    data = request.get_json() or {}
    new_name = sanitize_text(data.get('name', '').strip(), 100)
    if len(new_name) < 2:
        return jsonify({'success': False, 'message': 'Nama minimal 2 karakter'}), 400

    old_name = user.name
    user.name = new_name
    db.session.commit()

    log_activity(current_user.id, f"Rename user: {old_name} -> {new_name}", target_type="User", target_id=user.id)
    return jsonify({'success': True, 'name': user.name})
