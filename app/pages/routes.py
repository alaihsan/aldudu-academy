from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from app.core.extensions import db
from app.models import UserRole
from app.core.i18n import t

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')


@main_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('index.html')


@main_bp.route('/settings')
@login_required
def settings():
    return render_template('settings.html')


@main_bp.route('/history')
@login_required
def history():
    is_teacher = current_user.role in (UserRole.GURU, UserRole.ADMIN)
    return render_template('history.html', is_teacher=is_teacher)


@main_bp.route('/privacy-policy')
@login_required
def privacy_policy():
    return render_template('privacy_policy.html')


@main_bp.route('/sponsor')
@login_required
def sponsor():
    return render_template('sponsor.html')


@main_bp.route('/api/set-language', methods=['POST'])
@login_required
def set_language():
    """API endpoint untuk mengubah bahasa preferensi user"""
    data = request.get_json()
    lang_code = data.get('language', 'id')

    # Validasi kode bahasa yang didukung
    from app.core.i18n import SUPPORTED_LANGUAGES
    if lang_code not in SUPPORTED_LANGUAGES:
        return jsonify({'success': False, 'message': t('pages.messages.language_not_supported')}), 400

    current_user.preferred_language = lang_code
    db.session.commit()

    return jsonify({
        'success': True,
        'message': t('pages.messages.language_changed'),
        'language': lang_code
    })


@main_bp.errorhandler(403)
def forbidden(error):
    return {
        'success': False,
        'message': str(error.description) or t('messages.no_permission'),
    }, 403
