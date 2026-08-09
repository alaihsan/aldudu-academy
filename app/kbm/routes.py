"""
KBM (Kegiatan Belajar Mengajar) Notes Blueprint
"""
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.core.extensions import db
from app.models import Course, UserRole
from app.kbm.models import KbmNote, KbmActivityType
from app.helpers import log_activity
from app.core.i18n import t

kbm_bp = Blueprint('kbm', __name__, url_prefix='/api')


@kbm_bp.route('/courses/<int:course_id>/kbm-notes', methods=['GET'])
@login_required
def api_get_kbm_notes(course_id):
    """Get all KBM notes for a course"""
    course = Course.query.get_or_404(course_id)

    # Check permission
    if course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        return jsonify({'success': False, 'message': t('messages.unauthorized')}), 403

    notes = KbmNote.query.filter_by(course_id=course_id).order_by(KbmNote.activity_date.desc()).all()
    return jsonify({'success': True, 'notes': [note.to_dict() for note in notes]})


@kbm_bp.route('/courses/<int:course_id>/kbm-notes', methods=['POST'])
@login_required
def api_create_kbm_note(course_id):
    """Create a new KBM note"""
    course = Course.query.get_or_404(course_id)

    if course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        return jsonify({'success': False, 'message': t('messages.unauthorized')}), 403

    data = request.get_json() or {}

    # Validate required fields
    topic = data.get('topic', '').strip()
    if not topic:
        return jsonify({'success': False, 'message': t('kbm.messages.topic_required')}), 400

    # Parse date
    activity_date_str = data.get('activity_date')
    if not activity_date_str:
        return jsonify({'success': False, 'message': t('kbm.messages.date_required')}), 400

    try:
        activity_date = datetime.strptime(activity_date_str, '%Y-%m-%d')
    except ValueError:
        return jsonify({'success': False, 'message': t('kbm.messages.invalid_date_format')}), 400

    # Parse time (optional)
    start_time = None
    end_time = None
    if data.get('start_time'):
        try:
            start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        except ValueError:
            pass
    if data.get('end_time'):
        try:
            end_time = datetime.strptime(data['end_time'], '%H:%M').time()
        except ValueError:
            pass

    # Get activity type
    activity_type_str = data.get('activity_type', 'teori').lower()
    try:
        activity_type = KbmActivityType(activity_type_str)
    except ValueError:
        activity_type = KbmActivityType.LAINNYA

    # Create note
    note = KbmNote(
        course_id=course_id,
        teacher_id=current_user.id,
        activity_date=activity_date,
        start_time=start_time,
        end_time=end_time,
        activity_type=activity_type,
        topic=topic,
        description=data.get('description', '').strip(),
        notes=data.get('notes', '').strip(),
    )
    db.session.add(note)
    db.session.commit()

    log_activity(current_user.id, f"Added KBM note: {topic}")

    return jsonify({'success': True, 'note': note.to_dict()})


@kbm_bp.route('/kbm-notes/<int:note_id>', methods=['PUT'])
@login_required
def api_update_kbm_note(note_id):
    """Update a KBM note"""
    note = KbmNote.query.get_or_404(note_id)
    course = Course.query.get(note.course_id)

    if not course or (course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN):
        return jsonify({'success': False, 'message': t('messages.unauthorized')}), 403

    data = request.get_json() or {}

    if 'topic' in data:
        note.topic = data['topic'].strip()
    if 'activity_date' in data:
        try:
            note.activity_date = datetime.strptime(data['activity_date'], '%Y-%m-%d')
        except ValueError:
            pass
    if 'start_time' in data and data['start_time']:
        try:
            note.start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        except ValueError:
            pass
    if 'end_time' in data and data['end_time']:
        try:
            note.end_time = datetime.strptime(data['end_time'], '%H:%M').time()
        except ValueError:
            pass
    if 'activity_type' in data:
        try:
            note.activity_type = KbmActivityType(data['activity_type'].lower())
        except ValueError:
            pass
    if 'description' in data:
        note.description = data['description'].strip()
    if 'notes' in data:
        note.notes = data['notes'].strip()

    db.session.commit()

    return jsonify({'success': True, 'note': note.to_dict()})


@kbm_bp.route('/kbm-notes/<int:note_id>', methods=['DELETE'])
@login_required
def api_delete_kbm_note(note_id):
    """Delete a KBM note"""
    note = KbmNote.query.get_or_404(note_id)
    course = Course.query.get(note.course_id)

    if not course or (course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN):
        return jsonify({'success': False, 'message': t('messages.unauthorized')}), 403

    db.session.delete(note)
    db.session.commit()

    return jsonify({'success': True})
