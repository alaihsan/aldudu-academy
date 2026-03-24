from flask import Blueprint, render_template, redirect, url_for, abort, send_from_directory, request
import os
from flask_login import login_required, current_user
from app.models import (
    db, Course, Quiz, Question, Option,
    QuestionType, GradeType, UserRole, Link, File,
    QuizSubmission, Answer, Discussion, QuizStatus, ActivityLog
)
from app.helpers import get_jakarta_now
from app.tenant import get_school_id_or_abort, verify_course_in_school

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

@main_bp.route('/kelas/<int:course_id>')
@login_required
def course_detail(course_id):
    from app.models import Course, File, Link, Quiz, QuizStatus, Assignment, AssignmentStatus

    course = db.session.get(Course, course_id)
    if course is None:
        abort(404)

    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)
    is_teacher = (current_user.id == course.teacher_id)

    if is_teacher:
        quizzes = Quiz.query.filter_by(course_id=course.id, is_archived=False).all()
        assignments = Assignment.query.filter_by(course_id=course.id).all()
    else:
        quizzes = Quiz.query.filter_by(course_id=course.id, status=QuizStatus.PUBLISHED).all()
        assignments = Assignment.query.filter_by(course_id=course.id, status=AssignmentStatus.PUBLISHED).all()
    links = Link.query.filter_by(course_id=course.id).all()
    files = File.query.filter_by(course_id=course.id).all()
    discussions = Discussion.query.filter_by(course_id=course.id).all()

    topics = []
    for quiz in quizzes:
        topics.append({
            'id': quiz.id,
            'name': quiz.name,
            'type': 'Kuis',
            'url': url_for('main.quiz_detail', quiz_id=quiz.id),
            'created_at': quiz.created_at,
            'folder_id': quiz.folder_id
        })
    for assignment in assignments:
        topics.append({
            'id': assignment.id,
            'name': assignment.title,
            'type': 'Tugas',
            'url': url_for('assignment.detail', assignment_id=assignment.id),
            'created_at': assignment.created_at,
            'folder_id': assignment.folder_id
        })
    for link in links:
        topics.append({
            'id': link.id,
            'name': link.name,
            'type': 'Link',
            'url': link.url,
            'created_at': link.created_at,
            'folder_id': getattr(link, 'folder_id', None)
        })
    for file in files:
        topics.append({
            'id': file.id,
            'name': file.name,
            'type': 'Berkas',
            'url': url_for('main.serve_file', file_id=file.id),
            'created_at': file.created_at,
            'folder_id': getattr(file, 'folder_id', None)
        })
    for discussion in discussions:
        topics.append({
            'id': discussion.id,
            'name': discussion.title,
            'type': 'Diskusi',
            'url': url_for('main.discussion_detail', course_id=course.id, discussion_id=discussion.id),
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
        'course_detail.html',
        course=course,
        is_teacher=is_teacher,
        topics=topics,
        topics_json=topics_json
    )

@main_bp.route('/quiz/<int:quiz_id>')
@login_required
def quiz_detail(quiz_id):
    quiz = db.session.get(Quiz, quiz_id)
    if quiz is None:
        abort(404)

    course = quiz.course
    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)
    is_teacher = (current_user.id == course.teacher_id)
    is_preview = request.args.get('preview') == 'true'

    if not is_teacher and current_user not in course.students:
        abort(403)

    if not is_teacher and quiz.status != QuizStatus.PUBLISHED:
        abort(403, description='Kuis ini belum tersedia.')

    # For teachers: show editor by default, show preview only when preview=true
    if is_teacher and not is_preview:
        return render_template('quiz_editor.html', quiz=quiz, QuestionType=QuestionType, Question=Question, Option=Option)
    else:
        questions = quiz.questions.order_by(Question.order).all()
        if quiz.shuffle_questions:
            import random
            random.shuffle(questions)
        return render_template(
            'quiz_detail.html',
            quiz=quiz,
            course=course,
            is_teacher=is_teacher,
            is_preview=is_preview,
            questions=questions,
            QuestionType=QuestionType,
            Option=Option
        )

@main_bp.route('/quiz/<int:quiz_id>/saved', methods=['GET'])
@login_required
def quiz_saved(quiz_id):
    quiz = db.session.get(Quiz, quiz_id)
    if quiz is None:
        abort(404)
    course = quiz.course
    return redirect(url_for('main.course_detail', course_id=course.id))

@main_bp.route('/files/<int:file_id>')
@login_required
def serve_file(file_id):
    file = db.session.get(File, file_id)
    if file is None:
        abort(404)

    course = file.course
    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)
    is_teacher = (current_user.id == course.teacher_id)

    if not is_teacher and current_user not in course.students:
        abort(403)
        
    now = get_jakarta_now()
    if file.start_date and now < file.start_date:
        abort(403, description="File is not yet available.")
    if file.end_date and now > file.end_date:
        abort(403, description="File has expired.")

    upload_folder = os.path.join(os.getcwd(), 'instance', 'uploads', str(course.id))
    return send_from_directory(upload_folder, file.filename, as_attachment=False)

@main_bp.route('/uploads/<int:course_id>/<path:filename>')
@login_required
def serve_question_image(course_id, filename):
    course = db.session.get(Course, course_id)
    if course is None:
        abort(404)
    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)
    is_teacher = (current_user.id == course.teacher_id)
    is_student = current_user in course.students
    if not is_teacher and not is_student:
        abort(403)
    upload_folder = os.path.join(os.getcwd(), 'instance', 'uploads', str(course_id))
    return send_from_directory(upload_folder, filename, as_attachment=False)

@main_bp.route('/kelas/<int:course_id>/diskusi')
@login_required
def course_discussions(course_id):
    """Halaman Forum Diskusi per kelas"""
    course = db.session.get(Course, course_id)
    if course is None:
        abort(404)
    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)
    
    is_teacher = (current_user.id == course.teacher_id)
    is_student = current_user in course.students
    if not is_teacher and not is_student:
        abort(403)
    
    return render_template('course_discussions.html', course=course, is_teacher=is_teacher)

@main_bp.route('/kelas/<int:course_id>/diskusi/<int:discussion_id>')
@login_required
def discussion_detail(course_id, discussion_id):
    course = db.session.get(Course, course_id)
    if course is None:
        abort(404)
    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)
    discussion = db.session.get(Discussion, discussion_id)
    if discussion is None or discussion.course_id != course_id:
        abort(404)
    is_teacher = (current_user.id == course.teacher_id)
    if not is_teacher and current_user not in course.students:
        abort(403)
    return render_template('discussion_detail.html', course=course, discussion=discussion, is_teacher=is_teacher)

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

@main_bp.route('/issues')
@login_required
def issues():
    return render_template('issues.html')

@main_bp.route('/api/set-language', methods=['POST'])
@login_required
def set_language():
    """API endpoint untuk mengubah bahasa preferensi user"""
    from flask import jsonify
    data = request.get_json()
    lang_code = data.get('language', 'id')

    # Validasi kode bahasa yang didukung
    supported_languages = ['id', 'en', 'en-US', 'en-GB', 'ar', 'jv', 'jv-YO', 'jv-MA', 'su', 'min', 'ban']
    if lang_code not in supported_languages:
        return jsonify({'success': False, 'message': 'Bahasa tidak didukung'}), 400

    current_user.preferred_language = lang_code
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Bahasa berhasil diubah',
        'language': lang_code
    })


@main_bp.route('/api/courses', methods=['GET'])
@login_required
def api_get_courses():
    """API endpoint untuk mendapatkan daftar kelas user"""
    from flask import jsonify
    from app.models import Course

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


@main_bp.route('/api/courses/<int:course_id>/students', methods=['GET'])
@login_required
def api_get_course_students(course_id):
    """API endpoint untuk mendapatkan daftar siswa dalam course"""
    from flask import jsonify
    from app.models import Course, UserRole

    course = Course.query.get(course_id)
    if not course:
        return jsonify({'success': False, 'message': 'Course not found'}), 404

    # Check permission - only teacher or super admin can access
    if course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    students = course.students.all()
    return jsonify({
        'success': True,
        'students': [{
            'id': s.id,
            'name': s.name,
            'email': s.email,
        } for s in students]
    })


@main_bp.route('/api/quiz/<int:quiz_id>/archive', methods=['POST'])
@login_required
def api_archive_quiz(quiz_id):
    """API endpoint untuk mengarsipkan kuis"""
    from flask import jsonify
    from app.models import Quiz

    quiz = db.session.get(Quiz, quiz_id)
    if not quiz:
        return jsonify({'success': False, 'message': 'Kuis tidak ditemukan'}), 404

    if quiz.course.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'Anda tidak memiliki izin'}), 403

    quiz.is_archived = True
    db.session.commit()

    return jsonify({'success': True, 'message': 'Kuis berhasil diarsipkan'})


@main_bp.route('/api/assignment/<int:assignment_id>/archive', methods=['POST'])
@login_required
def api_archive_assignment(assignment_id):
    """API endpoint untuk mengarsipkan tugas"""
    from flask import jsonify
    from app.models import Assignment, AssignmentStatus

    assignment = db.session.get(Assignment, assignment_id)
    if not assignment:
        return jsonify({'success': False, 'message': 'Tugas tidak ditemukan'}), 404

    if assignment.course.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'Anda tidak memiliki izin'}), 403

    assignment.status = AssignmentStatus.ARCHIVED
    db.session.commit()

    return jsonify({'success': True, 'message': 'Tugas berhasil diarsipkan'})


@main_bp.route('/api/file/<int:file_id>/archive', methods=['POST'])
@login_required
def api_archive_file(file_id):
    """API endpoint untuk mengarsipkan file"""
    from flask import jsonify
    from app.models import File

    file = db.session.get(File, file_id)
    if not file:
        return jsonify({'success': False, 'message': 'File tidak ditemukan'}), 404

    if file.course.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'Anda tidak memiliki izin'}), 403

    file.is_archived = True
    db.session.commit()

    return jsonify({'success': True, 'message': 'File berhasil diarsipkan'})


@main_bp.route('/api/quiz/<int:quiz_id>/restore', methods=['POST'])
@login_required
def api_restore_quiz(quiz_id):
    """API endpoint untuk memulihkan kuis dari arsip"""
    from flask import jsonify
    from app.models import Quiz

    quiz = db.session.get(Quiz, quiz_id)
    if not quiz:
        return jsonify({'success': False, 'message': 'Kuis tidak ditemukan'}), 404

    if quiz.course.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'Anda tidak memiliki izin'}), 403

    quiz.is_archived = False
    db.session.commit()

    return jsonify({'success': True, 'message': 'Kuis berhasil dipulihkan'})


@main_bp.route('/api/assignment/<int:assignment_id>/restore', methods=['POST'])
@login_required
def api_restore_assignment(assignment_id):
    """API endpoint untuk memulihkan tugas dari arsip"""
    from flask import jsonify
    from app.models import Assignment, AssignmentStatus

    assignment = db.session.get(Assignment, assignment_id)
    if not assignment:
        return jsonify({'success': False, 'message': 'Tugas tidak ditemukan'}), 404

    if assignment.course.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'Anda tidak memiliki izin'}), 403

    assignment.status = AssignmentStatus.PUBLISHED
    db.session.commit()

    return jsonify({'success': True, 'message': 'Tugas berhasil dipulihkan'})


@main_bp.route('/api/file/<int:file_id>/restore', methods=['POST'])
@login_required
def api_restore_file(file_id):
    """API endpoint untuk memulihkan file dari arsip"""
    from flask import jsonify
    from app.models import File

    file = db.session.get(File, file_id)
    if not file:
        return jsonify({'success': False, 'message': 'File tidak ditemukan'}), 404

    if file.course.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'Anda tidak memiliki izin'}), 403

    file.is_archived = False
    db.session.commit()

    return jsonify({'success': True, 'message': 'File berhasil dipulihkan'})


@main_bp.route('/api/course/<int:course_id>/theme', methods=['PUT'])
@login_required
def api_update_course_theme(course_id):
    """API endpoint untuk update warna tema kelas"""
    from flask import jsonify, request
    from app.models import Course

    course = db.session.get(Course, course_id)
    if not course:
        return jsonify({'success': False, 'message': 'Kelas tidak ditemukan'}), 404

    if course.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'Anda tidak memiliki izin'}), 403

    data = request.get_json()
    color = data.get('color')

    if not color:
        return jsonify({'success': False, 'message': 'Warna tidak valid'}), 400

    # Validate hex color format
    import re
    if not re.match(r'^#[0-9A-Fa-f]{6}$', color):
        return jsonify({'success': False, 'message': 'Format warna tidak valid'}), 400

    course.color = color
    db.session.commit()

    return jsonify({'success': True, 'message': 'Warna tema berhasil diubah'})


@main_bp.route('/kelas/<int:course_id>/arsip')
@login_required
def course_archives(course_id):
    """Halaman arsip untuk kelas - menampilkan kuis, tugas, dan file yang diarsipkan"""
    from app.models import Course, Quiz, Assignment, File, Link

    course = db.session.get(Course, course_id)
    if course is None:
        abort(404)

    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)

    is_teacher = (current_user.id == course.teacher_id)
    is_student = current_user in course.students
    is_admin = current_user.role.value == 'admin'
    if not (is_teacher or is_student or is_admin):
        abort(403)

    # Get archived items
    archived_quizzes = Quiz.query.filter_by(course_id=course.id, is_archived=True).order_by(Quiz.updated_at.desc()).all()
    archived_assignments = Assignment.query.filter_by(course_id=course.id, status=AssignmentStatus.ARCHIVED).order_by(Assignment.updated_at.desc()).all()
    archived_files = File.query.filter_by(course_id=course.id, is_archived=True).order_by(File.updated_at.desc()).all()
    archived_links = Link.query.filter_by(course_id=course.id, is_archived=True).order_by(Link.updated_at.desc()).all()

    return render_template('course_archives.html',
                          course=course,
                          archived_quizzes=archived_quizzes,
                          archived_assignments=archived_assignments,
                          archived_files=archived_files,
                          archived_links=archived_links,
                          is_teacher=is_teacher)
