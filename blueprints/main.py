from flask import Blueprint, render_template, redirect, url_for, abort
from flask_login import login_required, current_user
from models import db, Course, Quiz


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
    course = db.session.get(Course, course_id)
    if course is None:
        abort(404)
    # --- TAMBAHKAN LOGIKA INI ---
    # Cek apakah pengguna saat ini adalah guru dari mata pelajaran ini
    is_teacher = (current_user.id == course.teacher_id)
    
    # Kirim variabel is_teacher dan semua kuis ke template
    quizzes = course.quizzes.order_by(Quiz.id.desc()).all()
    
    return render_template(
        'course_detail.html', 
        course=course, 
        is_teacher=is_teacher,
        quizzes=quizzes
    )

@main_bp.route('/quiz/<int:quiz_id>')
@login_required
def quiz_detail(quiz_id):
    quiz = db.session.get(Quiz, quiz_id)
    if quiz is None:
        abort(404)

    course = quiz.course # Ambil mata pelajarannya dari kuis

    # Keamanan: Pastikan hanya guru/murid yang terdaftar yang bisa akses
    if current_user.id == course.teacher_id:
        pass # Guru boleh akses
    elif current_user not in course.students:
        abort(403) # Murid yang tidak terdaftar dilarang

    return render_template(
        'quiz_detail.html', 
        quiz=quiz,
        course=course
    )
