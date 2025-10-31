import os
from datetime import datetime
from flask import Blueprint, request, jsonify, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, Course, AcademicYear, UserRole, Link, File
from helpers import sanitize_text, is_valid_color, is_valid_class_code, generate_class_code, get_courses_for_user, format_course_data

courses_bp = Blueprint('courses', __name__, url_prefix='/api')


@courses_bp.route('/initial-data', methods=['GET'])
@login_required
def api_initial_data():
    academic_years_query = AcademicYear.query.order_by(AcademicYear.year.desc()).all()
    academic_years = [{'id': ay.id, 'year': ay.year} for ay in academic_years_query]
    active_year_id = academic_years[0]['id'] if academic_years else None
    courses_query = get_courses_for_user(current_user, active_year_id)
    courses = [format_course_data(c, current_user) for c in courses_query]
    return jsonify({'academicYears': academic_years, 'courses': courses})


@courses_bp.route('/courses/year/<int:year_id>', methods=['GET'])
@login_required
def api_get_courses_by_year(year_id):
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
    except Exception:
        return jsonify({'success': False, 'message': 'Tahun ajaran tidak valid'}), 400

    new_course = Course(
        name=name,
        academic_year_id=academic_year_id,
        teacher_id=current_user.id,
        class_code=generate_class_code()
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
    if course_to_join in current_user.courses_enrolled:
        return jsonify({'success': False, 'message': 'Anda sudah terdaftar di kelas ini'}), 409
    current_user.courses_enrolled.append(course_to_join)
    db.session.commit()
    return jsonify({'success': True, 'message': f'Anda berhasil bergabung dengan kelas {course_to_join.name}', 'course': format_course_data(course_to_join, current_user)})


@courses_bp.route('/courses/<int:course_id>/links', methods=['POST'])
@login_required
def api_create_link(course_id):
    """
    Membuat link baru untuk sebuah mata pelajaran.
    Hanya guru yang mengajar mata pelajaran tersebut yang bisa mengakses.
    """

    # 1. Validasi: Hanya guru yang bisa membuat link
    if current_user.role != UserRole.GURU:
        return jsonify({'success': False, 'message': 'Hanya guru yang dapat membuat link'}), 403

    # 2. Validasi: Temukan mata pelajarannya
    course = db.session.get(Course, course_id)
    if not course:
        return jsonify({'success': False, 'message': 'Mata pelajaran tidak ditemukan'}), 404

    # 3. Validasi Keamanan: Pastikan guru ini adalah pemilik mata pelajaran
    if course.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'Anda tidak memiliki izin untuk menambah link di mata pelajaran ini'}), 403

    # 4. Ambil dan bersihkan data input
    data = request.get_json() or {}
    name = sanitize_text(data.get('name', ''), max_len=200)
    url = data.get('url', '').strip()

    if not name:
        return jsonify({'success': False, 'message': 'Nama link wajib diisi'}), 400

    if not url:
        return jsonify({'success': False, 'message': 'URL link wajib diisi'}), 400

    # Basic URL validation
    if not url.startswith(('http://', 'https://')):
        return jsonify({'success': False, 'message': 'URL harus dimulai dengan http:// atau https://'}), 400

    # 5. Buat link di database
    try:
        new_link = Link(
            name=name,
            url=url,
            course_id=course_id
        )
        db.session.add(new_link)
        db.session.commit()

        # 6. Kembalikan data link yang baru dibuat
        return jsonify({
            'success': True,
            'link': {
                'id': new_link.id,
                'name': new_link.name,
                'url': new_link.url,
                'course_id': new_link.course_id
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Terjadi kesalahan server: {e}'}), 500


@courses_bp.route('/courses/<int:course_id>/files', methods=['POST'])
@login_required
def api_create_file(course_id):
    if current_user.role != UserRole.GURU:
        return jsonify({'success': False, 'message': 'Hanya guru yang dapat mengunggah file'}), 403

    course = db.session.get(Course, course_id)
    if not course:
        return jsonify({'success': False, 'message': 'Mata pelajaran tidak ditemukan'}), 404

    if course.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'Anda tidak memiliki izin untuk mengunggah file di mata pelajaran ini'}), 403

    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'Tidak ada file yang diunggah'}), 400

    file = request.files['file']
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    start_date_str = request.form.get('start_date')
    end_date_str = request.form.get('end_date')

    if not name:
        return jsonify({'success': False, 'message': 'Nama file wajib diisi'}), 400
    
    if file.filename == '':
        return jsonify({'success': False, 'message': 'Tidak ada file yang dipilih'}), 400

    start_date = None
    if start_date_str:
        try:
            start_date = datetime.fromisoformat(start_date_str)
        except ValueError:
            return jsonify({'success': False, 'message': 'Format tanggal mulai tidak valid'}), 400

    end_date = None
    if end_date_str:
        try:
            end_date = datetime.fromisoformat(end_date_str)
        except ValueError:
            return jsonify({'success': False, 'message': 'Format tanggal selesai tidak valid'}), 400

    if file:
        filename = secure_filename(file.filename)
        upload_folder = os.path.join(os.getcwd(), 'instance', 'uploads', str(course_id))
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)

        new_file = File(
            name=name,
            description=description,
            filename=filename,
            course_id=course_id,
            start_date=start_date,
            end_date=end_date
        )
        db.session.add(new_file)
        db.session.commit()

        return jsonify({
            'success': True,
            'file': {
                'id': new_file.id,
                'name': new_file.name,
                'description': new_file.description,
                'filename': new_file.filename,
                'course_id': new_file.course_id,
                'start_date': new_file.start_date.isoformat() if new_file.start_date else None,
                'end_date': new_file.end_date.isoformat() if new_file.end_date else None,
            }
        }), 201

    return jsonify({'success': False, 'message': 'Terjadi kesalahan saat mengunggah file'}), 500
