import os
from datetime import datetime, time
from flask import Blueprint, request, jsonify, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy.orm import joinedload, selectinload
from app.models import db, Course, AcademicYear, UserRole, Link, File, Discussion, Post, Like, UserCourseOrder, KbmNote, KbmActivityType, Quiz, GradeType, QuizStatus
from app.helpers import sanitize_text, is_valid_color, is_valid_class_code, generate_class_code, get_courses_for_user, format_course_data, log_activity
from app.tenant import get_school_id_or_abort, verify_course_in_school, verify_academic_year_in_school

courses_bp = Blueprint('courses', __name__, url_prefix='/api')


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
    
    courses_query = get_courses_for_user(current_user, current_year.id)
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
