# blueprints/main.py

from flask import Blueprint, render_template, redirect, url_for, abort
from flask_login import login_required, current_user
# --- PERBAIKAN: Tambahkan impor QuestionType dan model lain ---
from models import (
    db, Course, Quiz, Question, Option,
    QuestionType, GradeType, UserRole, Link
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
# ... existing code ...
    course = db.session.get(Course, course_id)
    if course is None:
        abort(404)
    # --- TAMBAHKAN LOGIKA INI ---
    # Cek apakah pengguna saat ini adalah guru dari mata pelajaran ini
    is_teacher = (current_user.id == course.teacher_id)
    
    # Kirim variabel is_teacher dan semua kuis ke template
    quizzes = Quiz.query.filter_by(course_id=course.id).order_by(Quiz.id.desc()).all()
    links = Link.query.filter_by(course_id=course.id).order_by(Link.created_at.desc()).all()
    topics = []
    for quiz in quizzes:
        topics.append({
            'id': quiz.id,
            'name': quiz.name,
            'type': 'Kuis',
            'url': url_for('main.quiz_detail', quiz_id=quiz.id)
        })
    for link in links:
        topics.append({
            'id': link.id,
            'name': link.name,
            'type': 'Link',
            'url': link.url
        })
    
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
        return render_template('quiz_editor.html', quiz=quiz)
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
