import logging
from flask import Blueprint, request, jsonify, abort
from flask_login import login_required, current_user
from app.models import db, Course, AcademicYear, UserRole, UserCourseOrder
from app.helpers import sanitize_text, is_valid_color, is_valid_class_code, generate_class_code, get_courses_for_user, format_course_data, log_activity
from app.core.authorization import get_school_id_or_abort, verify_course_in_school, verify_academic_year_in_school

logger = logging.getLogger(__name__)

courses_bp = Blueprint('courses', __name__, url_prefix='/api')


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
        return jsonify({'success': False, 'message': 'Hanya guru yang dapat membuat kelas'}), 403
    data = request.get_json() or {}
    name = sanitize_text(data.get('name', ''), max_len=150)
    academic_year_id = data.get('academic_year_id')
    if not name:
        return jsonify({'success': False, 'message': 'Nama kelas wajib diisi'}), 400
    try:
        academic_year_id = int(academic_year_id)
    except (ValueError, TypeError) as e:
        logger.error(f"Invalid academic_year_id: {academic_year_id}, error: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Tahun ajaran tidak valid'}), 400

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
        abort(403, description="Anda tidak memiliki izin untuk mengedit kelas ini.")
    data = request.get_json() or {}
    if 'name' in data:
        name = sanitize_text(data.get('name'), max_len=150)
        if not name:
            return jsonify({'success': False, 'message': 'Nama kelas tidak valid'}), 400
        course.name = name
    if 'color' in data:
        color = data.get('color')
        if not is_valid_color(color):
            return jsonify({'success': False, 'message': 'Warna tidak valid'}), 400
        course.color = color.strip()
    db.session.commit()
    return jsonify({'success': True, 'course': format_course_data(course, current_user)})


@courses_bp.route('/courses/<int:course_id>', methods=['DELETE'])
@login_required
def api_delete_course(course_id):
    course = db.session.get(Course, course_id)
    if not course:
        return jsonify({'success': False, 'message': 'Kelas tidak ditemukan'}), 404

    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)

    if course.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'Anda tidak memiliki izin untuk menghapus kelas ini'}), 403

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

        return jsonify({'success': True, 'message': 'Kelas berhasil dihapus'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to delete course {course_id}: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Gagal menghapus kelas'}), 500


@courses_bp.route('/enroll', methods=['POST'])
@login_required
def api_enroll_in_course():
    if current_user.role != UserRole.MURID:
        return jsonify({'success': False, 'message': 'Hanya murid yang bisa bergabung ke kelas'}), 403
    data = request.get_json() or {}
    code = data.get('class_code', '')
    if not is_valid_class_code(code):
        return jsonify({'success': False, 'message': 'Kode kelas tidak valid'}), 400
    code = code.strip().upper()
    course_to_join = Course.query.filter_by(class_code=code).first()
    if not course_to_join:
        return jsonify({'success': False, 'message': f'Kelas dengan kode "{code}" tidak ditemukan'}), 404

    # Verify course belongs to student's school
    school_id = get_school_id_or_abort()
    verify_course_in_school(course_to_join, school_id)

    if course_to_join in current_user.courses_enrolled:
        return jsonify({'success': False, 'message': 'Anda sudah terdaftar di kelas ini'}), 409
    current_user.courses_enrolled.append(course_to_join)
    db.session.commit()
    return jsonify({'success': True, 'message': f'Anda berhasil bergabung dengan kelas {course_to_join.name}', 'course': format_course_data(course_to_join, current_user)})


@courses_bp.route('/courses/reorder', methods=['POST'])
@login_required
def api_reorder_courses():
    data = request.get_json() or {}
    course_ids = data.get('course_ids', [])

    if not isinstance(course_ids, list):
        return jsonify({'success': False, 'message': 'Format data tidak valid'}), 400

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
        return jsonify({'success': True, 'message': 'Urutan kelas berhasil diperbarui'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to reorder courses for user {current_user.id}: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Gagal memperbarui urutan'}), 500
