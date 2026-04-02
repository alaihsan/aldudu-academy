"""
Evaluation Tes Blueprint

Routes untuk dashboard Evaluasi Tes - khusus untuk guru
Mengaggregasi quiz, assignment, dan Rasch analysis dalam satu tempat
"""
from flask import Blueprint, render_template, request, jsonify, abort
from flask_login import login_required, current_user
from app.models import Course, UserRole
from app.services.evaluation_tes_service import EvaluationTesService

evaluation_bp = Blueprint('evaluation', __name__, url_prefix='/evaluasi-tes')


@evaluation_bp.route('/')
@login_required
def dashboard():
    """
    Dashboard Evaluasi Tes - Halaman utama untuk guru
    
    Menampilkan:
    - Ringkasan statistik evaluasi
    - Daftar tes & tugas
    - Analisis Rasch
    - Kemampuan siswa
    """
    # Only for teachers and admins
    if current_user.role not in [UserRole.GURU, UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        abort(403, "Akses ditolak. Hanya guru yang dapat mengakses halaman ini.")
    
    # Get all courses taught by teacher
    if current_user.role == UserRole.SUPER_ADMIN:
        courses = Course.query.all()
    else:
        courses = current_user.courses_taught.all()
    
    return render_template('evaluation/dashboard.html', courses=courses)


@evaluation_bp.route('/course/<int:course_id>')
@login_required
def course_detail(course_id):
    """
    Detail evaluasi untuk course tertentu
    
    Tab 1: Ringkasan
    """
    course = Course.query.get_or_404(course_id)
    
    # Check permission
    if course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        abort(403)
    
    # Initialize service
    service = EvaluationTesService(course_id, current_user.id)
    
    # Get dashboard summary
    summary = service.get_dashboard_summary()
    
    # Get score distribution
    score_dist = service.get_score_distribution('all')
    
    # Get comparison chart data
    comparison_data = service.get_comparison_chart_data()
    
    # Get recent evaluations
    recent_evaluations = service.get_recent_evaluations(limit=5)
    
    return render_template('evaluation/course_detail.html',
                         course=course,
                         summary=summary,
                         score_distribution=score_dist,
                         comparison_data=comparison_data,
                         recent_evaluations=recent_evaluations)


@evaluation_bp.route('/course/<int:course_id>/evaluations')
@login_required
def evaluations_list(course_id):
    """
    Tab 2: Daftar Tes & Tugas
    
    Returns:
        Template dengan list semua evaluasi
    """
    course = Course.query.get_or_404(course_id)
    
    if course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        abort(403)
    
    # Get all quizzes
    from app.models import Quiz, QuizStatus
    quizzes = Quiz.query.filter_by(course_id=course_id).all()
    
    # Get all assignments (via grade_items)
    from app.models.gradebook import GradeItem
    grade_items = GradeItem.query.filter_by(course_id=course_id).all()
    assignment_items = [gi for gi in grade_items if gi.assignment_id]
    
    # Get filter params
    eval_type = request.args.get('type', 'all')  # all, quiz, assignment
    status_filter = request.args.get('status', 'all')  # all, published, draft
    needs_analysis = request.args.get('needs_analysis', 'false')  # true/false
    
    # Apply filters
    filtered_quizzes = quizzes
    filtered_assignments = assignment_items
    
    if eval_type == 'quiz':
        filtered_assignments = []
    elif eval_type == 'assignment':
        filtered_quizzes = []
    
    if status_filter == 'published':
        filtered_quizzes = [q for q in filtered_quizzes if q.status == QuizStatus.PUBLISHED]
    elif status_filter == 'draft':
        filtered_quizzes = [q for q in filtered_quizzes if q.status in [QuizStatus.DRAFT, QuizStatus.UNPUBLISHED]]
    
    if needs_analysis == 'true':
        from app.models.rasch import RaschAnalysis
        quizzes_with_analysis = set()
        for q in quizzes:
            has_analysis = RaschAnalysis.query.filter_by(quiz_id=q.id).count() > 0
            if has_analysis:
                quizzes_with_analysis.add(q.id)
        
        filtered_quizzes = [q for q in filtered_quizzes if q.id not in quizzes_with_analysis]
        filtered_assignments = [a for a in filtered_assignments if not a.rasch_analysis_id]
    
    return render_template('evaluation/evaluations_list.html',
                         course=course,
                         quizzes=filtered_quizzes,
                         assignments=filtered_assignments,
                         current_type=eval_type,
                         current_status=status_filter,
                         current_needs_analysis=needs_analysis)


@evaluation_bp.route('/course/<int:course_id>/analysis')
@login_required
def rasch_analysis(course_id):
    """
    Tab 3: Analisis Kualitas Soal (Rasch)
    
    Menampilkan:
    - Reliabilitas tes
    - Wright Map
    - Item analysis
    - Fit statistics
    """
    course = Course.query.get_or_404(course_id)
    
    if course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        abort(403)
    
    # Get Rasch analyses
    from app.models.rasch import RaschAnalysis, RaschAnalysisStatus
    analyses = RaschAnalysis.query.filter_by(course_id=course_id)\
        .order_by(RaschAnalysis.created_at.desc()).all()
    
    return render_template('evaluation/rasch_analysis.html',
                         course=course,
                         analyses=analyses,
                         RaschAnalysisStatus=RaschAnalysisStatus)


@evaluation_bp.route('/course/<int:course_id>/students')
@login_required
def student_abilities(course_id):
    """
    Tab 4: Kemampuan Siswa
    
    Menampilkan:
    - Tabel ranking siswa
    - Grafik perkembangan
    - Distribusi kemampuan
    """
    course = Course.query.get_or_404(course_id)
    
    if course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        abort(403)
    
    # Initialize service
    service = EvaluationTesService(course_id, current_user.id)
    
    # Get student ability data
    student_data = service.get_student_ability_data()
    
    return render_template('evaluation/student_abilities.html',
                         course=course,
                         student_data=student_data)


@evaluation_bp.route('/course/<int:course_id>/settings')
@login_required
def settings(course_id):
    """
    Tab 5: Pengaturan
    
    Konfigurasi evaluasi dan Rasch analysis
    """
    course = Course.query.get_or_404(course_id)
    
    if course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        abort(403)
    
    return render_template('evaluation/settings.html', course=course)


# ─── API ENDPOINTS ─────────────────────────────────────────────────────────────

@evaluation_bp.route('/api/<int:course_id>/summary')
@login_required
def api_summary(course_id):
    """API: Ringkasan dashboard"""
    print(f"[EVALUATION API] Getting summary for course {course_id}")
    
    course = Course.query.get_or_404(course_id)

    if course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        print(f"[EVALUATION API] Unauthorized: user {current_user.id} not teacher of course {course_id}")
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    print(f"[EVALUATION API] Creating service for course {course_id}")
    service = EvaluationTesService(course_id, current_user.id)
    
    print(f"[EVALUATION API] Getting dashboard summary")
    summary = service.get_dashboard_summary()
    
    print(f"[EVALUATION API] Summary: {summary}")

    return jsonify({'success': True, 'summary': summary})


@evaluation_bp.route('/api/<int:course_id>/score-distribution')
@login_required
def api_score_distribution(course_id):
    """API: Distribusi nilai"""
    course = Course.query.get_or_404(course_id)
    
    if course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    eval_type = request.args.get('type', 'all')
    service = EvaluationTesService(course_id, current_user.id)
    data = service.get_score_distribution(eval_type)
    
    return jsonify({'success': True, 'data': data})


@evaluation_bp.route('/api/<int:course_id>/evaluation/<int:eval_id>/stats')
@login_required
def api_evaluation_stats(course_id, eval_id):
    """API: Statistik evaluasi detail"""
    course = Course.query.get_or_404(course_id)
    
    if course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    eval_type = request.args.get('type', 'quiz')
    service = EvaluationTesService(course_id, current_user.id)
    
    try:
        stats = service.get_evaluation_statistics(eval_id, eval_type)
        return jsonify({'success': True, 'stats': stats})
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@evaluation_bp.route('/api/<int:course_id>/rasch-summary')
@login_required
def api_rasch_summary(course_id):
    """API: Ringkasan Rasch analyses"""
    course = Course.query.get_or_404(course_id)
    
    if course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    service = EvaluationTesService(course_id, current_user.id)
    summary = service.get_rasch_summary()
    
    return jsonify({'success': True, 'summary': summary})


@evaluation_bp.route('/api/<int:course_id>/comparison-chart')
@login_required
def api_comparison_chart(course_id):
    """API: Data chart perbandingan"""
    course = Course.query.get_or_404(course_id)
    
    if course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    service = EvaluationTesService(course_id, current_user.id)
    data = service.get_comparison_chart_data()
    
    return jsonify({'success': True, 'data': data})


@evaluation_bp.route('/api/<int:course_id>/item-analysis/<int:quiz_id>')
@login_required
def api_item_analysis(course_id, quiz_id):
    """API: Item analysis chart"""
    course = Course.query.get_or_404(course_id)
    
    if course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    service = EvaluationTesService(course_id, current_user.id)
    data = service.get_item_analysis_chart(quiz_id)
    
    return jsonify({'success': True, 'data': data})


@evaluation_bp.route('/api/<int:course_id>/time-series/<int:quiz_id>')
@login_required
def api_time_series(course_id, quiz_id):
    """API: Time series submissions"""
    course = Course.query.get_or_404(course_id)
    
    if course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    service = EvaluationTesService(course_id, current_user.id)
    data = service.get_time_series_submissions(quiz_id)
    
    return jsonify({'success': True, 'data': data})


@evaluation_bp.route('/api/<int:course_id>/wright-map/<int:analysis_id>')
@login_required
def api_wright_map(course_id, analysis_id):
    """API: Wright Map data"""
    course = Course.query.get_or_404(course_id)
    
    if course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    service = EvaluationTesService(course_id, current_user.id)
    data = service.get_wright_map_data(analysis_id)
    
    return jsonify({'success': True, 'data': data})


@evaluation_bp.route('/api/<int:course_id>/student-abilities')
@login_required
def api_student_abilities(course_id):
    """API: Data kemampuan siswa"""
    course = Course.query.get_or_404(course_id)
    
    if course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    service = EvaluationTesService(course_id, current_user.id)
    data = service.get_student_ability_data()
    
    return jsonify({'success': True, 'data': data})
