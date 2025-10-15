from flask import Blueprint, render_template, redirect, url_for, abort
from flask_login import login_required, current_user
from models import db, Course

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
    return render_template('course_detail.html', course=course)
