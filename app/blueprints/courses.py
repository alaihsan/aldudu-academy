import os
import uuid
from datetime import datetime, time
from flask import Blueprint, request, jsonify, abort, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy.orm import joinedload, selectinload
from app.models import db, Course, AcademicYear, UserRole, Link, File, Discussion, Post, Like, UserCourseOrder, KbmNote, KbmActivityType, Quiz, GradeType, QuizStatus, ContentFolder, Assignment
from app.helpers import sanitize_text, is_valid_color, is_valid_class_code, generate_class_code, get_courses_for_user, format_course_data, log_activity
from app.tenant import get_school_id_or_abort, verify_course_in_school, verify_academic_year_in_school

courses_bp = Blueprint('courses', __name__, url_prefix='/api')


def allowed_file(filename, allowed_extensions=None):
    """Check if file extension is allowed"""
    if allowed_extensions is None:
        allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {
            'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
            'png', 'jpg', 'jpeg', 'gif', 'webp',
            'txt', 'rtf', 'zip', 'rar', '7z'
        })
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def get_file_extension(filename):
    """Get file extension from filename"""
    if '.' in filename:
        return filename.rsplit('.', 1)[1].lower()
    return ''


def generate_secure_filename(original_filename):
    """Generate a secure filename with UUID to prevent path traversal"""
    ext = get_file_extension(original_filename)
    unique_id = uuid.uuid4().hex
    return f"{unique_id}.{ext}" if ext else unique_id


@courses_bp.route('/initial-data', methods=['GET'])
@login_required
def api_initial_data():
    school_id = get_school_id_or_abort()
    # Only use the current academic year 2025/2026, scoped to school
    current_year = AcademicYear.query.filter_by(year='2025/2026', school_id=school_id).first()
    if not current_year:
        current_year = AcademicYear(year='2025/2026', is_active=True, school_id=school_id)
        db.session.add(current_year)
        db.session.commit()
    
    print(f"[DEBUG] api_initial_data: user={current_user.id} ({current_user.role.value}), school_id={school_id}, year_id={current_year.id}")

    courses_query = get_courses_for_user(current_user, current_year.id)
    courses = [format_course_data(c, current_user) for c in courses_query]
    
    print(f"[DEBUG] api_initial_data: returning {len(courses)} courses")

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
    except Exception:
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
    except Exception:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Gagal menghapus kelas'}), 500


@courses_bp.route('/courses/<int:course_id>/quizzes', methods=['POST'])
@login_required
def api_create_quiz(course_id):
    if current_user.role != UserRole.GURU:
        return jsonify({'success': False, 'message': 'Hanya guru yang dapat membuat kuis'}), 403

    course = db.session.get(Course, course_id)
    if not course:
        return jsonify({'success': False, 'message': 'Mata pelajaran tidak ditemukan'}), 404

    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)

    if course.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'Anda tidak memiliki izin'}), 403

    data = request.get_json() or {}
    name = sanitize_text(data.get('name', ''), max_len=200) or 'Kuis Tanpa Judul'

    try:
        grade_type = GradeType(data.get('grade_type', 'numeric'))
    except ValueError:
        grade_type = GradeType.NUMERIC

    try:
        points = int(data.get('points', 100))
    except (ValueError, TypeError):
        points = 100

    quiz = Quiz(
        name=name,
        course_id=course_id,
        grade_type=grade_type,
        points=points,
        status=QuizStatus.DRAFT,
    )
    db.session.add(quiz)
    db.session.commit()

    log_activity(current_user.id, f'Membuat kuis: {name}', target_type='Quiz', target_id=quiz.id)

    return jsonify({'success': True, 'quiz': {'id': quiz.id, 'name': quiz.name}}), 201


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

    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)

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

    except Exception:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Terjadi kesalahan server'}), 500


@courses_bp.route('/courses/<int:course_id>/files', methods=['POST'])
@login_required
def api_create_file(course_id):
    if current_user.role != UserRole.GURU:
        return jsonify({'success': False, 'message': 'Hanya guru yang dapat mengunggah file'}), 403

    course = db.session.get(Course, course_id)
    if not course:
        return jsonify({'success': False, 'message': 'Mata pelajaran tidak ditemukan'}), 404

    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)

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

    # Validate file extension
    if not allowed_file(file.filename):
        allowed = current_app.config.get('ALLOWED_EXTENSIONS', [])
        return jsonify({
            'success': False,
            'message': f'Tipe file tidak diizinkan. Hanya file dengan ekstensi: {", ".join(sorted(allowed))}'
        }), 400

    # Validate file size (check Content-Length header)
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Reset to beginning
    
    max_size = current_app.config.get('MAX_CONTENT_LENGTH', 16777216)  # 16MB default
    if file_size > max_size:
        return jsonify({
            'success': False,
            'message': f'Ukuran file terlalu besar. Maksimal: {max_size // (1024 * 1024)}MB'
        }), 400

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
        # Generate secure filename with UUID
        secure_name = generate_secure_filename(file.filename)
        
        # Create upload folder
        upload_folder = os.path.join(os.getcwd(), 'instance', 'uploads', str(course_id))
        os.makedirs(upload_folder, exist_ok=True)
        
        # Save file with secure name
        file_path = os.path.join(upload_folder, secure_name)
        file.save(file_path)

        new_file = File(
            name=name,
            description=description,
            filename=secure_name,
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


@courses_bp.route('/courses/<int:course_id>/discussions', methods=['POST'])
@login_required
def create_discussion(course_id):
    course = db.session.get(Course, course_id)
    if not course:
        return jsonify({'success': False, 'message': 'Mata pelajaran tidak ditemukan'}), 404

    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)

    if current_user.role != UserRole.GURU and current_user not in course.students:
        return jsonify({'success': False, 'message': 'Anda tidak memiliki izin untuk membuat diskusi di kelas ini'}), 403

    data = request.get_json() or {}
    title = sanitize_text(data.get('title', ''), max_len=200)
    content = sanitize_text(data.get('content', ''))

    if not title or not content:
        return jsonify({'success': False, 'message': 'Judul dan isi diskusi wajib diisi'}), 400

    try:
        new_discussion = Discussion(
            title=title,
            course_id=course_id,
            user_id=current_user.id
        )
        db.session.add(new_discussion)
        db.session.commit()

        new_post = Post(
            content=content,
            discussion_id=new_discussion.id,
            user_id=current_user.id
        )
        db.session.add(new_post)
        db.session.commit()

        return jsonify({'success': True, 'discussion': {'id': new_discussion.id, 'title': new_discussion.title}}), 201
    except Exception:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Terjadi kesalahan saat membuat diskusi'}), 500


@courses_bp.route('/courses/<int:course_id>/discussions', methods=['GET'])
@login_required
def get_discussions(course_id):
    course = db.session.get(Course, course_id)
    if not course:
        return jsonify({'success': False, 'message': 'Mata pelajaran tidak ditemukan'}), 404

    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)

    if current_user.role != UserRole.GURU and current_user not in course.students:
        return jsonify({'success': False, 'message': 'Anda tidak memiliki izin untuk melihat diskusi di kelas ini'}), 403

    discussions = Discussion.query.filter_by(course_id=course_id)\
        .options(joinedload(Discussion.user), selectinload(Discussion.posts).joinedload(Post.user))\
        .order_by(Discussion.created_at.desc()).all()
    return jsonify({'success': True, 'discussions': [d.to_dict() for d in discussions]})


@courses_bp.route('/discussions/<int:discussion_id>/posts', methods=['GET'])
@login_required
def get_posts(discussion_id):
    discussion = db.session.get(Discussion, discussion_id)
    if not discussion:
        return jsonify({'success': False, 'message': 'Diskusi tidak ditemukan'}), 404

    if current_user.role != UserRole.GURU and current_user not in discussion.course.students:
        return jsonify({'success': False, 'message': 'Anda tidak memiliki izin untuk melihat diskusi ini'}), 403

    posts = Post.query.filter_by(discussion_id=discussion_id)\
        .options(joinedload(Post.user), selectinload(Post.replies).joinedload(Post.user), selectinload(Post.likes).joinedload(Like.user))\
        .order_by(Post.created_at.asc()).all()
    return jsonify({'success': True, 'posts': [p.to_dict() for p in posts]})


@courses_bp.route('/discussions/<int:discussion_id>/posts', methods=['POST'])
@login_required
def add_post(discussion_id):
    discussion = db.session.get(Discussion, discussion_id)
    if not discussion:
        return jsonify({'success': False, 'message': 'Diskusi tidak ditemukan'}), 404

    if discussion.closed:
        return jsonify({'success': False, 'message': 'Diskusi ini sudah ditutup'}), 403

    data = request.get_json() or {}
    content = sanitize_text(data.get('content', ''))
    parent_id = data.get('parent_id')

    if not content:
        return jsonify({'success': False, 'message': 'Isi respon tidak boleh kosong'}), 400

    new_post = Post(
        content=content,
        discussion_id=discussion_id,
        user_id=current_user.id,
        parent_id=parent_id
    )
    db.session.add(new_post)
    db.session.commit()

    return jsonify({'success': True, 'post': new_post.to_dict()}), 201


@courses_bp.route('/posts/<int:post_id>/like', methods=['POST'])
@login_required
def like_post(post_id):
    post = db.session.get(Post, post_id)
    if not post:
        return jsonify({'success': False, 'message': 'Post tidak ditemukan'}), 404

    like = Like.query.filter_by(post_id=post_id, user_id=current_user.id).first()
    if like:
        db.session.delete(like)
        db.session.commit()
        return jsonify({'success': True, 'action': 'unliked'})
    else:
        new_like = Like(post_id=post_id, user_id=current_user.id)
        db.session.add(new_like)
        db.session.commit()
        return jsonify({'success': True, 'action': 'liked'})


@courses_bp.route('/posts/<int:post_id>', methods=['DELETE'])
@login_required
def delete_post(post_id):
    post = db.session.get(Post, post_id)
    if not post:
        return jsonify({'success': False, 'message': 'Post tidak ditemukan'}), 404

    # Allow deletion if user is the post author or the discussion creator (teacher)
    if current_user.id != post.user_id and current_user.id != post.discussion.user_id:
        return jsonify({'success': False, 'message': 'Anda tidak memiliki izin untuk menghapus post ini'}), 403

    db.session.delete(post)
    db.session.commit()

    return jsonify({'success': True})


@courses_bp.route('/discussions/<int:discussion_id>/close', methods=['POST'])
@login_required
def close_discussion(discussion_id):
    discussion = db.session.get(Discussion, discussion_id)
    if not discussion:
        return jsonify({'success': False, 'message': 'Diskusi tidak ditemukan'}), 404

    if discussion.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Hanya pembuat diskusi yang dapat menutupnya'}), 403

    discussion.closed = True
    db.session.commit()

    return jsonify({'success': True, 'message': 'Diskusi telah ditutup'})


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
    except Exception:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Gagal memperbarui urutan'}), 500



@courses_bp.route('/courses/<int:course_id>/content/reorder', methods=['POST'])
@login_required
def api_reorder_content(course_id):
    if current_user.role != UserRole.GURU:
        return jsonify({'success': False, 'message': 'Hanya guru yang dapat mengatur urutan'}), 403

    course = db.session.get(Course, course_id)
    if not course or course.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'Anda tidak memiliki izin'}), 403

    data = request.get_json() or {}
    items = data.get('items', [])

    try:
        for item in items:
            item_id = item.get('id')
            item_type = item.get('type')
            order = item.get('order', 0)
            folder_id = item.get('folder_id')  # None means root level

            if item_type == 'quiz':
                obj = db.session.get(Quiz, item_id)
            elif item_type == 'assignment':
                obj = db.session.get(Assignment, item_id)
            elif item_type == 'file':
                obj = db.session.get(File, item_id)
            elif item_type == 'link':
                obj = db.session.get(Link, item_id)
            elif item_type == 'folder':
                obj = db.session.get(ContentFolder, item_id)
            else:
                continue

            if obj and hasattr(obj, 'order'):
                obj.order = order
            if obj and item_type != 'folder' and hasattr(obj, 'folder_id'):
                obj.folder_id = folder_id
            if obj and item_type == 'folder' and hasattr(obj, 'parent_folder_id'):
                obj.parent_folder_id = folder_id

        db.session.commit()
        return jsonify({'success': True})
    except Exception:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Gagal menyimpan urutan'}), 500


@courses_bp.route('/courses/<int:course_id>/content/move-to-folder', methods=['POST'])
@login_required
def api_move_to_folder(course_id):
    if current_user.role != UserRole.GURU:
        return jsonify({'success': False, 'message': 'Hanya guru yang dapat memindahkan konten'}), 403

    course = db.session.get(Course, course_id)
    if not course or course.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'Anda tidak memiliki izin'}), 403

    data = request.get_json() or {}
    item_id = data.get('item_id')
    item_type = data.get('item_type')
    folder_id = data.get('folder_id')  # None to move to root

    if folder_id:
        folder = db.session.get(ContentFolder, folder_id)
        if not folder or folder.course_id != course_id:
            return jsonify({'success': False, 'message': 'Folder tidak valid'}), 400

    if item_type == 'quiz':
        obj = db.session.get(Quiz, item_id)
    elif item_type == 'assignment':
        obj = db.session.get(Assignment, item_id)
    elif item_type == 'file':
        obj = db.session.get(File, item_id)
    elif item_type == 'link':
        obj = db.session.get(Link, item_id)
    else:
        return jsonify({'success': False, 'message': 'Tipe konten tidak valid'}), 400

    if not obj:
        return jsonify({'success': False, 'message': 'Konten tidak ditemukan'}), 404

    obj.folder_id = folder_id
    db.session.commit()

    return jsonify({'success': True})


# ─── KBM Notes Routes ───────────────────────────────────────────────────────────

@courses_bp.route('/courses/<int:course_id>/kbm-notes', methods=['GET'])
@login_required
def api_get_kbm_notes(course_id):
    """Get all KBM notes for a course"""
    course = Course.query.get_or_404(course_id)
    
    # Check permission
    if course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    notes = KbmNote.query.filter_by(course_id=course_id).order_by(KbmNote.activity_date.desc()).all()
    return jsonify({'success': True, 'notes': [note.to_dict() for note in notes]})


@courses_bp.route('/courses/<int:course_id>/kbm-notes', methods=['POST'])
@login_required
def api_create_kbm_note(course_id):
    """Create a new KBM note"""
    course = Course.query.get_or_404(course_id)
    
    if course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    data = request.get_json() or {}
    
    # Validate required fields
    topic = data.get('topic', '').strip()
    if not topic:
        return jsonify({'success': False, 'message': 'Topik/materi wajib diisi'}), 400
    
    # Parse date
    activity_date_str = data.get('activity_date')
    if not activity_date_str:
        return jsonify({'success': False, 'message': 'Tanggal wajib diisi'}), 400
    
    try:
        activity_date = datetime.strptime(activity_date_str, '%Y-%m-%d')
    except ValueError:
        return jsonify({'success': False, 'message': 'Format tanggal tidak valid'}), 400
    
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


@courses_bp.route('/kbm-notes/<int:note_id>', methods=['PUT'])
@login_required
def api_update_kbm_note(note_id):
    """Update a KBM note"""
    note = KbmNote.query.get_or_404(note_id)
    course = Course.query.get(note.course_id)
    
    if not course or (course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
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


@courses_bp.route('/kbm-notes/<int:note_id>', methods=['DELETE'])
@login_required
def api_delete_kbm_note(note_id):
    """Delete a KBM note"""
    note = KbmNote.query.get_or_404(note_id)
    course = Course.query.get(note.course_id)
    
    if not course or (course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    db.session.delete(note)
    db.session.commit()

    return jsonify({'success': True})


# ===== Content Folder Management Endpoints =====

@courses_bp.route('/courses/<int:course_id>/folders', methods=['GET'])
@login_required
def api_get_course_folders(course_id):
    """Get all folders in a course with hierarchical structure"""
    course = db.session.get(Course, course_id)
    if not course:
        abort(404)

    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)

    # Get all folders (sorted by order)
    folders = ContentFolder.query.filter_by(course_id=course_id).order_by(ContentFolder.order).all()

    # Build hierarchical structure
    def build_folder_tree(parent_id=None):
        items = []
        for folder in folders:
            if folder.parent_folder_id == parent_id:
                item = folder.to_dict(include_children=False)
                item['children'] = build_folder_tree(folder.id)
                items.append(item)
        return items

    folder_tree = build_folder_tree()

    return jsonify({
        'success': True,
        'folders': folder_tree
    })


@courses_bp.route('/courses/<int:course_id>/folders', methods=['POST'])
@login_required
def api_create_folder(course_id):
    """Create a new folder in a course"""
    course = db.session.get(Course, course_id)
    if not course:
        abort(404)

    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)

    # Only teacher can create folders (not admin or super admin)
    if course.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'Anda tidak memiliki izin untuk membuat folder'}), 403

    data = request.get_json() or {}
    name = sanitize_text(data.get('name', ''), max_len=200).strip()
    parent_folder_id = data.get('parent_folder_id')

    if not name:
        return jsonify({'success': False, 'message': 'Nama folder wajib diisi'}), 400

    # Verify parent folder belongs to same course
    if parent_folder_id:
        parent_folder = ContentFolder.query.get(parent_folder_id)
        if not parent_folder or parent_folder.course_id != course_id:
            return jsonify({'success': False, 'message': 'Parent folder tidak valid'}), 400

    # Get the next order number
    max_order = db.session.query(db.func.max(ContentFolder.order)).filter(
        ContentFolder.course_id == course_id,
        ContentFolder.parent_folder_id == parent_folder_id
    ).scalar() or 0

    folder = ContentFolder(
        name=name,
        course_id=course_id,
        parent_folder_id=parent_folder_id,
        order=max_order + 1
    )

    db.session.add(folder)
    db.session.commit()

    log_activity(current_user.id, f"Created folder: {name} in course {course.name}")

    return jsonify({
        'success': True,
        'folder': folder.to_dict(include_children=True)
    }), 201


@courses_bp.route('/folders/<int:folder_id>', methods=['PUT'])
@login_required
def api_update_folder(folder_id):
    """Update folder (rename, reorder)"""
    folder = ContentFolder.query.get_or_404(folder_id)
    course = Course.query.get(folder.course_id)

    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)

    # Only teacher can update folder
    if course.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    data = request.get_json() or {}

    if 'name' in data:
        name = sanitize_text(data['name'], max_len=200).strip()
        if name:
            folder.name = name

    if 'order' in data:
        try:
            folder.order = int(data['order'])
        except (ValueError, TypeError):
            pass

    db.session.commit()

    return jsonify({
        'success': True,
        'folder': folder.to_dict(include_children=False)
    })


@courses_bp.route('/folders/<int:folder_id>', methods=['DELETE'])
@login_required
def api_delete_folder(folder_id):
    """Delete a folder and move its contents to parent"""
    folder = ContentFolder.query.get_or_404(folder_id)
    course = Course.query.get(folder.course_id)

    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)

    # Only teacher can delete folder
    if course.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    folder_id_val = folder.id
    parent_id = folder.parent_folder_id

    # Move all child folders to parent
    child_folders = ContentFolder.query.filter_by(parent_folder_id=folder_id_val).all()
    for child in child_folders:
        child.parent_folder_id = parent_id

    # Move all materials to parent folder
    Quiz.query.filter_by(folder_id=folder_id_val).update({Quiz.folder_id: parent_id})
    Assignment.query.filter_by(folder_id=folder_id_val).update({Assignment.folder_id: parent_id})
    File.query.filter_by(folder_id=folder_id_val).update({File.folder_id: parent_id})
    Link.query.filter_by(folder_id=folder_id_val).update({Link.folder_id: parent_id})

    db.session.delete(folder)
    db.session.commit()

    log_activity(current_user.id, f"Deleted folder {folder_id_val}")

    return jsonify({'success': True})


@courses_bp.route('/materials/<material_type>/<int:material_id>/move', methods=['POST'])
@login_required
def api_move_material(material_type, material_id):
    """Move a material (quiz, assignment, file, link) to a folder"""
    data = request.get_json() or {}
    folder_id = data.get('folder_id')
    order = data.get('order', 0)

    # Map material types
    material_map = {
        'quiz': Quiz,
        'assignment': Assignment,
        'file': File,
        'link': Link
    }

    if material_type not in material_map:
        return jsonify({'success': False, 'message': 'Tipe material tidak valid'}), 400

    Material = material_map[material_type]
    material = Material.query.get_or_404(material_id)

    # Get course and verify permissions
    course_id = material.course_id
    course = Course.query.get(course_id)

    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)

    if course.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    # Verify folder belongs to same course
    if folder_id:
        target_folder = ContentFolder.query.get(folder_id)
        if not target_folder or target_folder.course_id != course_id:
            return jsonify({'success': False, 'message': 'Target folder tidak valid'}), 400

    # Update material
    material.folder_id = folder_id
    if order >= 0:
        material.order = order

    db.session.commit()

    return jsonify({'success': True})


@courses_bp.route('/courses/<int:course_id>/materials/reorder', methods=['POST'])
@login_required
def api_reorder_materials(course_id):
    """Reorder materials in a course"""
    course = Course.query.get_or_404(course_id)
    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)

    if course.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    data = request.get_json() or {}
    order_list = data.get('order', [])

    for item in order_list:
        material_id = item.get('id')
        material_type = item.get('type')
        order = item.get('order', 0)

        if material_type == 'quiz':
            quiz = Quiz.query.get(material_id)
            if quiz and quiz.course_id == course_id:
                quiz.order = order
        elif material_type == 'assignment':
            assignment = Assignment.query.get(material_id)
            if assignment and assignment.course_id == course_id:
                assignment.order = order
        elif material_type == 'file':
            file = File.query.get(material_id)
            if file and file.course_id == course_id:
                file.order = order
        elif material_type == 'link':
            link = Link.query.get(material_id)
            if link and link.course_id == course_id:
                link.order = order

    db.session.commit()
    return jsonify({'success': True})


@courses_bp.route('/courses/<int:course_id>/folders/reorder', methods=['POST'])
@login_required
def api_reorder_folders(course_id):
    """Reorder folders in a course"""
    course = Course.query.get_or_404(course_id)
    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)

    if course.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    data = request.get_json() or {}
    order_list = data.get('order', [])

    for item in order_list:
        folder_id = item.get('id')
        order = item.get('order', 0)

        folder = ContentFolder.query.get(folder_id)
        if folder and folder.course_id == course_id:
            folder.order = order

    db.session.commit()
    return jsonify({'success': True})


@courses_bp.route('/materials/<int:material_id>/move', methods=['PUT'])
@login_required
def api_move_material_to_folder(material_id):
    """Move a material to a folder"""
    data = request.get_json() or {}
    folder_id = data.get('folder_id')

    # Try to find material in different tables
    material = None
    material_type = None

    for model in [Quiz, Assignment, File, Link]:
        material = model.query.get(material_id)
        if material:
            material_type = model.__tablename__
            course_id = material.course_id
            break

    if not material:
        return jsonify({'success': False, 'message': 'Material not found'}), 404

    course = Course.query.get(course_id)
    if not course:
        return jsonify({'success': False, 'message': 'Course not found'}), 404

    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)

    if course.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    # Update folder_id
    material.folder_id = folder_id
    db.session.commit()

    log_activity(current_user.id, f"Moved {material_type} {material_id} to folder {folder_id}")

    return jsonify({'success': True})


@courses_bp.route('/folders/<int:folder_id>/move', methods=['PUT'])
@login_required
def api_move_folder(folder_id):
    """Move a folder to a parent folder"""
    data = request.get_json() or {}
    new_parent_id = data.get('parent_folder_id')

    folder = ContentFolder.query.get_or_404(folder_id)
    course = Course.query.get(folder.course_id)

    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)

    if course.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    # Prevent moving folder into itself or its descendants
    if new_parent_id:
        child_ids = [f.id for f in ContentFolder.query.filter_by(parent_folder_id=folder_id).all()]
        if new_parent_id in child_ids or new_parent_id == folder_id:
            return jsonify({'success': False, 'message': 'Invalid parent folder'}), 400

    folder.parent_folder_id = new_parent_id
    db.session.commit()

    log_activity(current_user.id, f"Moved folder {folder_id} to parent {new_parent_id}")

    return jsonify({'success': True})


@courses_bp.route('/api/link/<int:link_id>/archive', methods=['POST'])
@login_required
def api_archive_link(link_id):
    """Archive a link"""
    link = Link.query.get_or_404(link_id)
    course = Course.query.get(link.course_id)
    
    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)
    
    if course.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    link.is_archived = True
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Link berhasil diarsipkan'})


@courses_bp.route('/api/link/<int:link_id>/restore', methods=['POST'])
@login_required
def api_restore_link(link_id):
    """Restore an archived link"""
    link = Link.query.get_or_404(link_id)
    course = Course.query.get(link.course_id)

    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)

    if course.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    link.is_archived = False
    db.session.commit()

    return jsonify({'success': True, 'message': 'Link berhasil dipulihkan'})


@courses_bp.route('/api/link/<int:link_id>', methods=['DELETE'])
@login_required
def api_delete_link(link_id):
    """Delete a link permanently from archive"""
    link = Link.query.get_or_404(link_id)
    course = Course.query.get(link.course_id)

    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)

    if course.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    db.session.delete(link)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Link berhasil dihapus permanen'})
