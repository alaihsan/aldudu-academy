from flask import Blueprint, render_template, request, jsonify, abort
import re
from flask_login import login_required, current_user
from app.models import db, User, UserRole, ActivityLog, Course, QuizSubmission
from app.helpers import log_activity, sanitize_text, is_valid_email, generate_random_password
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.before_request
@login_required
def admin_required():
    if current_user.role != UserRole.ADMIN:
        abort(403)

@admin_bp.route('/dashboard')
def dashboard():
    # Statistics
    stats = {
        'total_guru': User.query.filter_by(role=UserRole.GURU).count(),
        'total_murid': User.query.filter_by(role=UserRole.MURID).count(),
        'total_courses': Course.query.count(),
        'total_submissions': QuizSubmission.query.count()
    }
    
    # Recent Activities
    recent_logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(20).all()
    
    return render_template('admin_dashboard.html', stats=stats, recent_logs=recent_logs)

@admin_bp.route('/users')
def user_management():
    gurus = User.query.filter_by(role=UserRole.GURU).order_by(User.name).all()
    murids = User.query.filter_by(role=UserRole.MURID).order_by(User.name).all()
    return render_template('admin_users.html', gurus=gurus, murids=murids)

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

    # Parse raw_text (Nama \t Email)
    lines = raw_text.strip().split('\n')
    imported_count = 0
    results = []

    try:
        for line in lines:
            line = line.strip()
            if not line: continue
            
            # Split by: 1+ Tabs, 2+ Spaces, Comma, Semicolon, or Pipe
            # This avoids splitting "Muhamad Ikhsan" if separated by a single space
            parts = re.split(r'\t+| {2,}|[|;,]', line)
            parts = [p.strip() for p in parts if p.strip()]
            
            if len(parts) < 2:
                # Fallback: if only 1 space exists, try splitting by that single space
                # but only if it looks like "Name email@domain.com"
                if ' ' in line and is_valid_email(line.split(' ')[-1]):
                    temp_parts = line.split(' ')
                    email = temp_parts[-1].lower()
                    name = " ".join(temp_parts[:-1])
                else:
                    continue
            else:
                email = parts[-1].lower()
                name = " ".join(parts[:-1])
            
            name = sanitize_text(name, max_len=100)
            
            if not is_valid_email(email): continue
            if User.query.filter_by(email=email).first(): continue
            
            # Auto generate 4 char password
            password = generate_random_password(4)
            
            user = User(name=name, email=email, role=role)
            user.set_password(password)
            db.session.add(user)
            
            results.append({'name': name, 'email': email, 'password': password})
            imported_count += 1

        db.session.commit()
        log_activity(current_user.id, f"Impor massal {imported_count} {role.value}", details=f"Mendaftarkan {imported_count} user.")
        
        return jsonify({'success': True, 'count': imported_count, 'results': results})
    except Exception as e:
        db.session.rollback()
        # Log error to console for debugging
        print(f"IMPORT ERROR: {str(e)}")
        return jsonify({'success': False, 'message': f'Gagal menyimpan ke database: {str(e)}'}), 500

@admin_bp.route('/api/users/<int:user_id>/reset-password', methods=['POST'])
def reset_password(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User tidak ditemukan'}), 404
        
    data = request.get_json() or {}
    new_password = data.get('password', '').strip()
    
    if len(new_password) < 6:
        return jsonify({'success': False, 'message': 'Password minimal 6 digit'}), 400
        
    user.set_password(new_password)
    db.session.commit()
    
    log_activity(current_user.id, f"Reset password user: {user.email}", target_id=user.id)
    return jsonify({'success': True, 'message': 'Password berhasil diubah'})

@admin_bp.route('/api/users/<int:user_id>/toggle-status', methods=['POST'])
def toggle_user_status(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User tidak ditemukan'}), 404
        
    if user.id == current_user.id:
        return jsonify({'success': False, 'message': 'Anda tidak dapat menonaktifkan akun sendiri'}), 400
        
    user.is_active = not user.is_active
    db.session.commit()
    
    action = "Mengaktifkan" if user.is_active else "Menonaktifkan"
    log_activity(current_user.id, f"{action} akun: {user.email}", target_type="User", target_id=user.id)
    
    return jsonify({'success': True, 'is_active': user.is_active})
