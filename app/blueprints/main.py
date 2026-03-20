from flask import Blueprint, render_template, redirect, url_for, abort, send_from_directory, request
import os
from flask_login import login_required, current_user
from app.models import (
    db, Course, Quiz, Question, Option,
    QuestionType, GradeType, UserRole, Link, File,
    QuizSubmission, Answer, Discussion, QuizStatus, ActivityLog, ContentFolder
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
        quizzes = Quiz.query.filter_by(course_id=course.id).all()
        assignments = Assignment.query.filter_by(course_id=course.id).all()
    else:
        quizzes = Quiz.query.filter_by(course_id=course.id, status=QuizStatus.PUBLISHED).all()
        assignments = Assignment.query.filter_by(course_id=course.id, status=AssignmentStatus.PUBLISHED).all()
    links = Link.query.filter_by(course_id=course.id).all()
    files = File.query.filter_by(course_id=course.id).all()

    folders = ContentFolder.query.filter_by(course_id=course.id).order_by(ContentFolder.order).all()

    topics = []
    for quiz in quizzes:
        topics.append({
            'id': quiz.id,
            'name': quiz.name,
            'type': 'Kuis',
            'url': url_for('main.quiz_detail', quiz_id=quiz.id),
            'created_at': quiz.created_at,
            'folder_id': quiz.folder_id,
            'order': quiz.order,
        })
    for assignment in assignments:
        topics.append({
            'id': assignment.id,
            'name': assignment.title,
            'type': 'Tugas',
            'url': url_for('assignment.detail', assignment_id=assignment.id),
            'created_at': assignment.created_at,
            'folder_id': assignment.folder_id,
            'order': assignment.order,
        })
    for link in links:
        topics.append({
            'id': link.id,
            'name': link.name,
            'type': 'Link',
            'url': link.url,
            'created_at': link.created_at,
            'folder_id': link.folder_id,
            'order': link.order,
        })
    for file in files:
        topics.append({
            'id': file.id,
            'name': file.name,
            'type': 'Berkas',
            'url': url_for('main.serve_file', file_id=file.id),
            'created_at': file.created_at,
            'folder_id': file.folder_id,
            'order': file.order,
        })

    topics.sort(key=lambda x: x['created_at'], reverse=True)

    folders_data = [f.to_dict() for f in folders]

    return render_template(
        'course_detail.html',
        course=course,
        is_teacher=is_teacher,
        topics=topics,
        folders=folders_data,
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
    from flask import jsonify
    data = request.get_json() or {}
    lang = data.get('language', 'id')
    supported = ['id', 'en', 'ar', 'jv', 'su', 'ban', 'min']
    if lang not in supported:
        return jsonify({'success': False, 'message': 'Bahasa tidak didukung'}), 400
    current_user.preferred_language = lang
    db.session.commit()
    return jsonify({'success': True, 'language': lang})
