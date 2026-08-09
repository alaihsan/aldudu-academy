import logging
from flask import Blueprint, request, jsonify, abort, render_template, url_for
from flask_login import login_required, current_user
from app.core.extensions import db
from app.models import UserRole, Quiz, Assignment, AssignmentStatus
from app.content.models import File, Link
from app.courses.models import Course, AcademicYear, UserCourseOrder
from app.helpers import sanitize_text, is_valid_color, is_valid_class_code, generate_class_code, get_courses_for_user, format_course_data, log_activity
from app.core.authorization import get_school_id_or_abort, verify_course_in_school, verify_academic_year_in_school
from app.core.i18n import t

logger = logging.getLogger(__name__)

courses_bp = Blueprint('courses', __name__, url_prefix='/api')

# Separate blueprint (no /api prefix) for page renders, since courses_bp's
# prefix is fixed to /api for its JSON routes.
courses_pages_bp = Blueprint('courses_pages', __name__, template_folder='templates')


@courses_pages_bp.route('/kelas/<int:course_id>')
@login_required
def course_detail(course_id):
    from sqlalchemy.orm import selectinload
    from app.models import QuizStatus

    # Optimize with selectinload for all related content
    course = db.session.query(Course).options(
        selectinload(Course.quizzes),
        selectinload(Course.assignments),
        selectinload(Course.files),
        selectinload(Course.links),
        selectinload(Course.discussions)
    ).filter(Course.id == course_id).first()

    if course is None:
        abort(404)

    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)
    is_teacher = (current_user.id == course.teacher_id)
    is_student = current_user in course.students
    is_admin = current_user.role in (UserRole.ADMIN, UserRole.SUPER_ADMIN)

    if not (is_teacher or is_student or is_admin):
        abort(403, description=t('course.messages.no_access_to_class'))

    # Filter: arsip + Ruang TPS dikeluarkan dari daftar materi utama
    def _live(x):
        return (not getattr(x, 'is_archived', False)) and (not getattr(x, 'is_trashed', False))

    if is_teacher:
        quizzes = [q for q in course.quizzes if _live(q)]
        assignments = [a for a in course.assignments if _live(a)]
    else:
        quizzes = [q for q in course.quizzes if q.status == QuizStatus.PUBLISHED and _live(q)]
        assignments = [a for a in course.assignments if a.status == AssignmentStatus.PUBLISHED and _live(a)]

    links = [l for l in course.links if _live(l)]
    files = [f for f in course.files if _live(f)]
    discussions = course.discussions

    topics = []
    for quiz in quizzes:
        topics.append({
            'id': quiz.id,
            'name': quiz.name,
            'type': 'Kuis',
            'url': url_for('quiz_pages.quiz_detail', quiz_id=quiz.id),
            'created_at': quiz.created_at,
            'folder_id': quiz.folder_id
        })
    # ... (rest of the processing logic remains the same)
    for assignment in assignments:
        topics.append({
            'id': assignment.id,
            'name': assignment.title,
            'type': 'Tugas',
            'url': url_for('assignment.detail', assignment_id=assignment.id),
            'description': assignment.description or '',
            'created_at': assignment.created_at,
            'folder_id': assignment.folder_id
        })
    for link in links:
        topics.append({
            'id': link.id,
            'name': link.name,
            'type': 'Link',
            'url': link.url,
            'description': link.description or '',
            'created_at': link.created_at,
            'folder_id': getattr(link, 'folder_id', None)
        })
    for file in files:
        topics.append({
            'id': file.id,
            'name': file.name,
            'type': 'Berkas',
            'url': url_for('content_files.serve_file', file_id=file.id),
            'filename': file.filename,
            'description': file.description or '',
            'created_at': file.created_at,
            'folder_id': getattr(file, 'folder_id', None)
        })
    for discussion in discussions:
        topics.append({
            'id': discussion.id,
            'name': discussion.title,
            'type': 'Diskusi',
            'url': url_for('discussion_pages.discussion_detail', course_id=course.id, discussion_id=discussion.id),
            'created_at': discussion.created_at,
            'folder_id': None
        })

    from datetime import datetime
    epoch = datetime(1970, 1, 1)
    topics.sort(key=lambda x: x['created_at'] or epoch, reverse=True)

    # JSON-safe version for JavaScript (datetime → isoformat string)
    topics_json = [
        {**t, 'created_at': t['created_at'].isoformat() if t['created_at'] else None}
        for t in topics
    ]

    return render_template(
        'courses/course_detail.html',
        course=course,
        is_teacher=is_teacher,
        topics=topics,
        topics_json=topics_json
    )


@courses_pages_bp.route('/kelas/<int:course_id>/arsip')
@login_required
def course_archives(course_id):
    """Halaman arsip untuk kelas - menampilkan kuis, tugas, dan file yang diarsipkan"""
    course = db.session.get(Course, course_id)
    if course is None:
        abort(404, description=t('course.messages.class_not_found'))

    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)

    # Teacher, admin, and enrolled students can access archives
    is_teacher = (current_user.id == course.teacher_id)
    is_student = current_user in course.students
    is_admin = (current_user.role == UserRole.ADMIN)
    if not (is_teacher or is_student or is_admin):
        abort(403, description=t('course.messages.no_access_to_archive'))

    # Get archived items (kecualikan yang sudah masuk Ruang TPS)
    archived_quizzes = Quiz.query.filter_by(course_id=course.id, is_archived=True, is_trashed=False).order_by(Quiz.updated_at.desc()).all()
    archived_assignments = Assignment.query.filter_by(course_id=course.id, status=AssignmentStatus.ARCHIVED, is_trashed=False).order_by(Assignment.updated_at.desc()).all()
    archived_files = File.query.filter_by(course_id=course.id, is_archived=True, is_trashed=False).order_by(File.created_at.desc()).all()
    archived_links = Link.query.filter_by(course_id=course.id, is_archived=True, is_trashed=False).order_by(Link.created_at.desc()).all()

    return render_template('courses/course_archives.html',
                          course=course,
                          archived_quizzes=archived_quizzes,
                          archived_assignments=archived_assignments,
                          archived_files=archived_files,
                          archived_links=archived_links,
                          is_teacher=is_teacher or is_admin)


@courses_pages_bp.route('/kelas/<int:course_id>/impor')
@login_required
def course_import(course_id):
    """Halaman Impor Konten dari kelas lain"""
    course = db.session.get(Course, course_id)
    if course is None:
        abort(404, description=t('course.messages.class_not_found'))

    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)

    # Only teacher of the class can import content
    is_teacher = (current_user.id == course.teacher_id)
    if not is_teacher:
        abort(403, description=t('course.messages.teacher_only_menu'))

    # Get all OTHER courses taught by this teacher (to import FROM)
    other_courses = Course.query.filter(Course.teacher_id == current_user.id, Course.id != course_id).all()

    return render_template('courses/course_import.html',
                           course=course,
                           other_courses=other_courses,
                           is_teacher=is_teacher)


@courses_bp.route('/courses', methods=['GET'])
@login_required
def api_get_courses():
    """API endpoint untuk mendapatkan daftar kelas user"""
    # Get all courses where user is teacher or student
    if current_user.role.value == 'guru':
        courses = Course.query.filter_by(teacher_id=current_user.id).all()
    elif current_user.role.value == 'murid':
        courses = Course.query.filter(Course.students.contains(current_user)).all()
    else:
        # Admin and super admin see all courses
        courses = Course.query.all()

    return jsonify({
        'success': True,
        'courses': [{
            'id': c.id,
            'name': c.name,
            'color': c.color,
            'teacher_name': c.teacher.name if c.teacher else '-',
            'class_code': c.class_code
        } for c in courses]
    })


@courses_bp.route('/courses/<int:course_id>/students', methods=['GET'])
@login_required
def api_get_course_students(course_id):
    """API endpoint untuk mendapatkan daftar siswa dalam course"""
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'success': False, 'message': t('messages.course_not_found')}), 404

    # Check permission - only teacher or super admin can access
    if course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        return jsonify({'success': False, 'message': t('messages.unauthorized')}), 403

    students = sorted(course.students, key=lambda s: (s.name or '').lower())
    return jsonify({
        'success': True,
        'students': [{
            'id': s.id,
            'name': s.name,
            'email': s.email,
            'nis': s.nis,
            'gender': s.gender,
        } for s in students]
    })


@courses_bp.route('/course/<int:course_id>/theme', methods=['PUT'])
@login_required
def api_update_course_theme(course_id):
    """API endpoint untuk update warna tema kelas"""
    import re

    course = db.session.get(Course, course_id)
    if not course:
        return jsonify({'success': False, 'message': t('course.messages.class_not_found')}), 404

    if course.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': t('messages.no_permission')}), 403

    data = request.get_json()
    color = data.get('color')

    if not color:
        return jsonify({'success': False, 'message': t('course.messages.invalid_color')}), 400

    # Validate hex color format
    if not re.match(r'^#[0-9A-Fa-f]{6}$', color):
        return jsonify({'success': False, 'message': t('course.messages.invalid_color_format')}), 400

    course.color = color
    db.session.commit()

    return jsonify({'success': True, 'message': t('course.messages.theme_color_updated')})


@courses_bp.route('/initial-data', methods=['GET'])
@login_required
def api_initial_data():
    school_id = get_school_id_or_abort()

    # Pre-fetch active year to avoid redundant queries
    current_year = AcademicYear.query.filter_by(school_id=school_id, is_active=True).first()

    if not current_year:
        # Check if 2025/2026 exists even if not active, or create it
        current_year = AcademicYear.query.filter_by(year='2025/2026', school_id=school_id).first()
        if not current_year:
            current_year = AcademicYear(year='2025/2026', is_active=True, school_id=school_id)
            db.session.add(current_year)
            db.session.commit()
        else:
            current_year.is_active = True
            db.session.commit()

    # For teachers: use -1 to show all their courses (no year filter)
    # For teachers & admins: use -1 to show all classes (no year filter)
    # For students: use active academic year
    year_id = -1 if current_user.role in (UserRole.GURU, UserRole.ADMIN, UserRole.SUPER_ADMIN) else current_year.id

    # get_courses_for_user already has some optimization, but we can ensure teacher is loaded
    courses_query = get_courses_for_user(current_user, year_id)
    courses = [format_course_data(c, current_user) for c in courses_query]

    return jsonify({
        'academicYears': [{'id': current_year.id, 'year': current_year.year}],
        'courses': courses,
        'currentYearId': current_year.id
    })


@courses_bp.route('/courses/year/<int:year_id>', methods=['GET'])
@login_required
def api_get_courses_by_year(year_id):
    school_id = get_school_id_or_abort()
    verify_academic_year_in_school(year_id, school_id)
    courses_query = get_courses_for_user(current_user, year_id)
    courses = [format_course_data(c, current_user) for c in courses_query]
    return jsonify({'courses': courses})


@courses_bp.route('/courses', methods=['POST'])
@login_required
def api_create_course():
    if current_user.role != UserRole.GURU:
        return jsonify({'success': False, 'message': t('course.messages.teacher_only_create_class')}), 403
    data = request.get_json() or {}
    name = sanitize_text(data.get('name', ''), max_len=150)
    academic_year_id = data.get('academic_year_id')
    if not name:
        return jsonify({'success': False, 'message': t('course.messages.class_name_required')}), 400
    try:
        academic_year_id = int(academic_year_id)
    except (ValueError, TypeError) as e:
        logger.error(f"Invalid academic_year_id: {academic_year_id}, error: {e}", exc_info=True)
        return jsonify({'success': False, 'message': t('course.messages.invalid_academic_year')}), 400

    school_id = get_school_id_or_abort()
    verify_academic_year_in_school(academic_year_id, school_id)

    new_course = Course(
        name=name,
        academic_year_id=academic_year_id,
        teacher_id=current_user.id,
        class_code=generate_class_code(),
        color=data.get('color', '#0282c6')
    )
    db.session.add(new_course)
    db.session.commit()
    return jsonify({'success': True, 'course': format_course_data(new_course, current_user)}), 201


@courses_bp.route('/courses/<int:course_id>', methods=['PUT'])
@login_required
def update_course(course_id):
    course = db.session.get(Course, course_id)
    if course is None:
        abort(404)
    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)
    if course.teacher_id != current_user.id:
        abort(403, description=t('course.messages.no_permission_edit_class'))
    data = request.get_json() or {}
    if 'name' in data:
        name = sanitize_text(data.get('name'), max_len=150)
        if not name:
            return jsonify({'success': False, 'message': t('course.messages.invalid_class_name')}), 400
        course.name = name
    if 'color' in data:
        color = data.get('color')
        if not is_valid_color(color):
            return jsonify({'success': False, 'message': t('course.messages.invalid_color')}), 400
        course.color = color.strip()
    db.session.commit()
    return jsonify({'success': True, 'course': format_course_data(course, current_user)})


@courses_bp.route('/courses/<int:course_id>', methods=['DELETE'])
@login_required
def api_delete_course(course_id):
    course = db.session.get(Course, course_id)
    if not course:
        return jsonify({'success': False, 'message': t('course.messages.class_not_found')}), 404

    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)

    if course.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': t('course.messages.no_permission_delete_class')}), 403

    course_name = course.name
    teacher_name = current_user.name

    try:
        db.session.delete(course)
        db.session.commit()

        # Log the activity
        log_activity(
            user_id=current_user.id,
            action='DELETE_COURSE',
            target_type='Course',
            target_id=course_id,
            details=f'Guru "{teacher_name}" menghapus kelas "{course_name}"'
        )

        return jsonify({'success': True, 'message': t('course.messages.class_deleted')})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to delete course {course_id}: {e}", exc_info=True)
        return jsonify({'success': False, 'message': t('course.messages.failed_delete_class')}), 500


@courses_bp.route('/enroll', methods=['POST'])
@login_required
def api_enroll_in_course():
    if current_user.role != UserRole.MURID:
        return jsonify({'success': False, 'message': t('course.messages.student_only_join_class')}), 403
    data = request.get_json() or {}
    code = data.get('class_code', '')
    if not is_valid_class_code(code):
        return jsonify({'success': False, 'message': t('course.messages.invalid_class_code')}), 400
    code = code.strip().upper()
    course_to_join = Course.query.filter_by(class_code=code).first()
    if not course_to_join:
        return jsonify({'success': False, 'message': t('course.messages.class_code_not_found', code)}), 404

    # Verify course belongs to student's school
    school_id = get_school_id_or_abort()
    verify_course_in_school(course_to_join, school_id)

    if course_to_join in current_user.courses_enrolled:
        return jsonify({'success': False, 'message': t('course.messages.already_enrolled')}), 409
    current_user.courses_enrolled.append(course_to_join)
    db.session.commit()
    return jsonify({'success': True, 'message': t('course.messages.joined_class', course_to_join.name), 'course': format_course_data(course_to_join, current_user)})


@courses_bp.route('/courses/reorder', methods=['POST'])
@login_required
def api_reorder_courses():
    data = request.get_json() or {}
    course_ids = data.get('course_ids', [])

    if not isinstance(course_ids, list):
        return jsonify({'success': False, 'message': t('messages.invalid_data_format')}), 400

    try:
        # Delete existing orders for this user
        UserCourseOrder.query.filter_by(user_id=current_user.id).delete()

        # Add new orders
        for index, course_id in enumerate(course_ids):
            new_order = UserCourseOrder(
                user_id=current_user.id,
                course_id=course_id,
                manual_order=index + 1  # Start from 1
            )
            db.session.add(new_order)

        db.session.commit()
        return jsonify({'success': True, 'message': t('course.messages.class_order_updated')})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to reorder courses for user {current_user.id}: {e}", exc_info=True)
        return jsonify({'success': False, 'message': t('course.messages.failed_update_order')}), 500
