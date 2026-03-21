"""
Rasch Dashboard Blueprint

Routes untuk menampilkan dashboard Rasch Model untuk guru.
"""

from flask import Blueprint, render_template, request, jsonify, abort
from flask_login import login_required, current_user
from app.models import Course, UserRole
from app.models.rasch import RaschAnalysis, RaschAnalysisStatus

rasch_dashboard_bp = Blueprint('rasch_dashboard', __name__, url_prefix='/rasch')


@rasch_dashboard_bp.context_processor
def utility_processor():
    """Add utility functions to template context"""
    def get_ability_label(level):
        labels = {
            'very_high': 'Very High',
            'high': 'High',
            'average': 'Average',
            'low': 'Low',
            'very_low': 'Very Low'
        }
        return labels.get(level, 'Unknown')
    
    def get_percentile_class(percentile):
        if percentile is None:
            return 'mid'
        if percentile >= 75:
            return 'high'
        if percentile >= 50:
            return 'mid'
        return 'low'
    
    return {
        'get_ability_label': get_ability_label,
        'get_percentile_class': get_percentile_class
    }


@rasch_dashboard_bp.route('/course/<int:course_id>')
@login_required
def teacher_dashboard(course_id):
    """
    Teacher dashboard untuk melihat Rasch analyses dari sebuah course.
    
    Menampilkan:
    - List quiz dengan Rasch enabled
    - Threshold progress untuk setiap quiz
    - Status analyses (pending, processing, completed)
    - Quick actions (analyze, view results)
    """
    course = Course.query.get(course_id)
    
    if not course:
        abort(404)
    
    # Check permission
    if course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        abort(403)
    
    # Get all quizzes in course
    from app.models.quiz import Quiz
    quizzes = Quiz.query.filter_by(course_id=course_id).all()
    
    # Get grade_items with Rasch enabled
    from app.models.gradebook import GradeItem
    grade_items = GradeItem.query.filter_by(course_id=course_id, enable_rasch_analysis=True).all()
    
    # Get analyses for this course
    analyses = RaschAnalysis.query.filter_by(course_id=course_id)\
        .order_by(RaschAnalysis.created_at.desc()).all()
    
    return render_template('rasch/teacher_dashboard.html',
                         course=course,
                         quizzes=quizzes,
                         grade_items=grade_items,
                         analyses=analyses,
                         RaschAnalysisStatus=RaschAnalysisStatus)


@rasch_dashboard_bp.route('/analysis/<int:analysis_id>')
@login_required
def analysis_detail(analysis_id):
    """
    Detail page untuk Rasch analysis.
    
    Menampilkan:
    - Analysis info & status
    - Wright Map visualization
    - Person measures table
    - Item measures table
    - Fit statistics
    - Bloom taxonomy correlation
    """
    analysis = RaschAnalysis.query.get(analysis_id)
    
    if not analysis:
        abort(404)
    
    # Check permission
    course = Course.query.get(analysis.course_id)
    if not course or (course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN):
        abort(403)
    
    return render_template('rasch/analysis_detail.html',
                         analysis=analysis,
                         course=course)


@rasch_dashboard_bp.route('/course/<int:course_id>/my-ability')
@login_required
def student_ability(course_id):
    """
    Student view untuk melihat ability measure mereka sendiri.
    
    Menampilkan:
    - Ability measure (theta) untuk setiap quiz
    - Percentile rank di kelas
    - Rekomendasi berdasarkan Bloom level
    """
    course = Course.query.get(course_id)
    
    if not course:
        abort(404)
    
    # Check if user is student in this course
    if current_user not in course.students and current_user.role != UserRole.SUPER_ADMIN:
        abort(403)
    
    # Get all analyses for this course
    analyses = RaschAnalysis.query.filter_by(course_id=course_id, status='completed').all()
    
    # Get student's person measures
    from app.models.rasch import RaschPersonMeasure
    person_measures = RaschPersonMeasure.query.filter_by(student_id=current_user.id).all()
    
    # Filter measures for this course's analyses
    student_measures = [m for m in person_measures if m.rasch_analysis_id in [a.id for a in analyses]]
    
    return render_template('rasch/student_ability.html',
                         course=course,
                         analyses=analyses,
                         student_measures=student_measures)
