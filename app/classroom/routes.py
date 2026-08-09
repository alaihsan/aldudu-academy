"""
Classroom Blueprint - "Ruang Kelas": aggregated pending-work view across
every course a user is enrolled in (student) or teaches (teacher).
"""
from flask import Blueprint, jsonify, render_template, request
from flask_login import login_required, current_user
from app.core.authorization import get_school_id_or_abort
from app.classroom.services import get_pending_items_for_user

classroom_bp = Blueprint('classroom', __name__, url_prefix='/api')

# Separate blueprint (no /api prefix) for the page render, since classroom_bp's
# prefix is fixed to /api for its JSON route.
classroom_pages_bp = Blueprint('classroom_pages', __name__, template_folder='templates')


@classroom_pages_bp.route('/ruang-kelas')
@login_required
def classroom_page():
    return render_template('classroom/classroom.html')


@classroom_bp.route('/classroom/items', methods=['GET'])
@login_required
def api_classroom_items():
    school_id = get_school_id_or_abort()

    item_filter = request.args.get('filter', 'all')
    if item_filter not in ('all', 'assignments', 'quizzes'):
        item_filter = 'all'

    sort_mode = request.args.get('sort', 'due-asc')
    if sort_mode not in ('due-asc', 'due-desc', 'recent'):
        sort_mode = 'due-asc'

    items = get_pending_items_for_user(current_user, school_id, item_filter=item_filter, sort_mode=sort_mode)

    return jsonify({'success': True, 'items': items})
