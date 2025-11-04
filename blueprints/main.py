# blueprints/main.py

from flask import Blueprint, render_template, redirect, url_for, abort, send_from_directory
import os
from datetime import datetime
from flask_login import login_required, current_user
# --- PERBAIKAN: Tambahkan impor QuestionType dan model lain ---
from models import (
    db, Course, Quiz, Question, Option,
    QuestionType, GradeType, UserRole, Link, File,
    QuizSubmission, Answer, Discussion
)


main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
# ... existing code ...
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')


@main_bp.route('/dashboard')
@login_required
def dashboard():
# ... existing code ...
    return render_template('index.html')


@main_bp.route('/kelas/<int:course_id>')
@login_required
def course_detail(course_id):
    course = db.session.get(Course, course_id)
    if course is None:
        abort(404)
    # Cek apakah pengguna saat ini adalah guru dari mata pelajaran ini
    is_teacher = (current_user.id == course.teacher_id)
    
    # Kirim variabel is_teacher dan semua kuis ke template
    quizzes = Quiz.query.filter_by(course_id=course.id).all()
    links = Link.query.filter_by(course_id=course.id).all()
    files = File.query.filter_by(course_id=course.id).all()
    
    topics = []
    for quiz in quizzes:
        topics.append({
            'id': quiz.id,
            'name': quiz.name,
            'type': 'Kuis',
            'url': url_for('main.quiz_detail', quiz_id=quiz.id),
            'created_at': quiz.created_at
        })
    for link in links:
        topics.append({
            'id': link.id,
            'name': link.name,
            'type': 'Link',
            'url': link.url,
            'created_at': link.created_at
        })
    for file in files:
        topics.append({
            'id': file.id,
            'name': file.name,
            'type': 'Berkas',
            'url': url_for('main.serve_file', file_id=file.id),
            'created_at': file.created_at
        })
    
    # Sort topics by creation date, newest first
    topics.sort(key=lambda x: x['created_at'], reverse=True)
    
    return render_template(
        'course_detail.html', 
        course=course, 
        is_teacher=is_teacher,
        topics=topics
    )

@main_bp.route('/quiz/<int:quiz_id>')
@login_required
def quiz_detail(quiz_id):
    quiz = db.session.get(Quiz, quiz_id)
    if quiz is None:
        abort(404)

    course = quiz.course
    is_teacher = (current_user.id == course.teacher_id)

    if not is_teacher and current_user not in course.students:
        abort(403)

    if is_teacher:
        # For teachers, render the editor
        return render_template('quiz_editor.html', quiz=quiz, QuestionType=QuestionType)
    else:
        # For students, render the detail/view page
        questions = quiz.questions.order_by(Question.order).all()
        return render_template(
            'quiz_detail.html',
            quiz=quiz,
            course=course,
            is_teacher=is_teacher,
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
    is_teacher = (current_user.id == course.teacher_id)

    if not is_teacher:
        abort(403)

    # Redirect back to the course page
    return redirect(url_for('main.course_detail', course_id=course.id))


@main_bp.route('/files/<int:file_id>')
@login_required
def serve_file(file_id):
    file = db.session.get(File, file_id)
    if file is None:
        abort(404)

    course = file.course
    is_teacher = (current_user.id == course.teacher_id)

    if not is_teacher and current_user not in course.students:
        abort(403)
        
    # Check if file is within start_date and end_date
    now = datetime.utcnow()
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

    is_teacher = (current_user.id == course.teacher_id)
    is_student = current_user in course.students

    if not is_teacher and not is_student:
        abort(403)

    upload_folder = os.path.join(os.getcwd(), 'instance', 'uploads', str(course_id))
    return send_from_directory(upload_folder, filename, as_attachment=False)


@main_bp.route('/kelas/<int:course_id>/diskusi/<int:discussion_id>')
@login_required
def discussion_detail(course_id, discussion_id):
    course = db.session.get(Course, course_id)
    if course is None:
        abort(404)

    discussion = db.session.get(Discussion, discussion_id)
    if discussion is None or discussion.course_id != course_id:
        abort(404)

    is_teacher = (current_user.id == course.teacher_id)
    if not is_teacher and current_user not in course.students:
        abort(403)

    return render_template('discussion_detail.html', course=course, discussion=discussion, is_teacher=is_teacher)
