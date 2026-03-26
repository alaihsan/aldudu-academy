"""
Rasch Analysis API Blueprint

Endpoints untuk:
- Threshold checking & manual trigger
- Status polling
- Results retrieval (person measures, item measures)
- Wright Map visualization
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from app.models import db, Course, UserRole
from app.models.rasch import (
    RaschAnalysis,
    RaschAnalysisStatus,
    RaschPersonMeasure,
    RaschItemMeasure,
    RaschThresholdLog,
)

rasch_bp = Blueprint('rasch', __name__, url_prefix='/api/rasch')


def get_analysis_or_abort(analysis_id, check_permission=True):
    """Get analysis record or abort with 404"""
    analysis = RaschAnalysis.query.get(analysis_id)
    
    if not analysis:
        return jsonify({
            'success': False,
            'message': 'Analisis tidak ditemukan'
        }), 404
    
    if check_permission:
        # Check if user has permission
        if current_user.role == UserRole.SUPER_ADMIN:
            return analysis
        
        # Check if user is teacher of the course
        course = Course.query.get(analysis.course_id)
        if not course or course.teacher_id != current_user.id:
            return jsonify({
                'success': False,
                'message': 'Anda tidak memiliki akses ke analisis ini'
            }), 403
    
    return analysis


# ============================================================
# Threshold & Manual Trigger
# ============================================================

@rasch_bp.route('/quizzes/<int:quiz_id>/threshold-status', methods=['GET'])
@login_required
def api_get_threshold_status(quiz_id):
    """
    Get threshold status untuk quiz.
    
    Response:
    {
        "quiz_id": 123,
        "total_students": 45,
        "submitted": 28,
        "min_required": 30,
        "threshold_met": false,
        "remaining": 2,
        "percentage": 62.2,
        "auto_trigger_enabled": true,
        "status": "waiting",
        "message": "Menunggu 2 siswa lagi untuk memulai analisis Rasch"
    }
    """
    from app.models.quiz import Quiz, QuizSubmission
    from app.models.gradebook import GradeItem
    
    quiz = Quiz.query.get(quiz_id)
    
    if not quiz:
        return jsonify({'success': False, 'message': 'Quiz tidak ditemukan'}), 404
    
    # Check permission
    course = Course.query.get(quiz.course_id)
    if course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        return jsonify({'success': False, 'message': 'Akses ditolak'}), 403
    
    # Count submissions
    submission_count = QuizSubmission.query.filter_by(quiz_id=quiz_id).count()
    
    # Get total students
    total_students = course.students.count()
    
    # Get or check analysis
    grade_item = GradeItem.query.filter_by(quiz_id=quiz_id).first()
    
    if grade_item and grade_item.rasch_analysis_id:
        analysis = RaschAnalysis.query.get(grade_item.rasch_analysis_id)
        min_required = analysis.min_persons if analysis else 30
        auto_trigger = analysis.auto_trigger if analysis else True
        status = analysis.status.value if analysis else 'pending'
    else:
        min_required = 30
        auto_trigger = grade_item.enable_rasch_analysis if grade_item else False
        status = 'pending'
    
    threshold_met = submission_count >= min_required
    remaining = max(0, min_required - submission_count)
    percentage = (submission_count / min_required * 100) if min_required > 0 else 0
    
    if threshold_met:
        message = "Threshold terpenuhi. Analisis siap dijalankan."
    else:
        message = f"Menunggu {remaining} siswa lagi untuk memulai analisis Rasch"
    
    return jsonify({
        'success': True,
        'quiz_id': quiz_id,
        'total_students': total_students,
        'submitted': submission_count,
        'min_required': min_required,
        'threshold_met': threshold_met,
        'remaining': remaining,
        'percentage': round(percentage, 1),
        'auto_trigger_enabled': auto_trigger,
        'status': status,
        'message': message,
    })


@rasch_bp.route('/quizzes/<int:quiz_id>/analyze', methods=['POST'])
@login_required
def api_manual_trigger_analysis(quiz_id):
    """
    Manual trigger Rasch analysis (bypass threshold).
    
    Request:
    {
        "min_persons": 20  // Optional: override default
    }
    """
    from app.models.quiz import Quiz
    from app.services.rasch_threshold_service import RaschThresholdService
    
    quiz = Quiz.query.get(quiz_id)
    
    if not quiz:
        return jsonify({'success': False, 'message': 'Quiz tidak ditemukan'}), 404
    
    # Check permission
    course = Course.query.get(quiz.course_id)
    if course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        return jsonify({'success': False, 'message': 'Akses ditolak'}), 403
    
    # Get override min_persons
    data = request.get_json() or {}
    min_persons = data.get('min_persons')
    
    # Trigger analysis
    service = RaschThresholdService()
    success, message = service.manual_trigger(quiz_id, min_persons)
    
    if success:
        return jsonify({
            'success': True,
            'message': message
        })
    else:
        return jsonify({
            'success': False,
            'message': message
        }), 400


# ============================================================
# Analysis Management
# ============================================================

@rasch_bp.route('/analyses', methods=['GET'])
@login_required
def api_list_analyses():
    """
    List analyses untuk course.
    
    Query params:
    - course_id: Filter by course
    - quiz_id: Filter by quiz
    - status: Filter by status
    """
    course_id = request.args.get('course_id', type=int)
    quiz_id = request.args.get('quiz_id', type=int)
    status = request.args.get('status')
    
    # Permission check
    if course_id:
        course = Course.query.get(course_id)
        if not course:
            return jsonify({'success': False, 'message': 'Course tidak ditemukan'}), 404
        
        if course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
            return jsonify({'success': False, 'message': 'Akses ditolak'}), 403
    
    query = RaschAnalysis.query
    
    if course_id:
        query = query.filter_by(course_id=course_id)
    if quiz_id:
        query = query.filter_by(quiz_id=quiz_id)
    if status:
        query = query.filter_by(status=status)
    
    analyses = query.order_by(RaschAnalysis.created_at.desc()).all()
    
    return jsonify({
        'success': True,
        'analyses': [a.to_dict() for a in analyses]
    })


@rasch_bp.route('/analyses/<int:analysis_id>', methods=['GET'])
@login_required
def api_get_analysis(analysis_id):
    """
    Get analysis detail dengan progress.
    
    Response:
    {
        "id": 1,
        "name": "Quiz 1 Rasch Analysis",
        "status": "processing",
        "progress_percentage": 45.5,
        "status_message": "Calculating item difficulties (iteration 23/100)",
        "num_persons": null,
        "num_items": null,
        "started_at": "2026-03-21T10:30:00",
        "estimated_completion": "2026-03-21T10:35:00"
    }
    """
    analysis = get_analysis_or_abort(analysis_id)
    
    if not isinstance(analysis, RaschAnalysis):
        return analysis  # Return error response
    
    return jsonify({
        'success': True,
        'analysis': analysis.to_dict()
    })


@rasch_bp.route('/analyses/<int:analysis_id>/status', methods=['GET'])
@login_required
def api_get_analysis_status(analysis_id):
    """
    Polling status analysis.
    
    Response:
    {
        "status": "processing",
        "progress_percentage": 45.5,
        "status_message": "Iteration 23/100",
        "is_complete": false,
        "is_failed": false
    }
    """
    analysis = get_analysis_or_abort(analysis_id)
    
    if not isinstance(analysis, RaschAnalysis):
        return analysis
    
    return jsonify({
        'success': True,
        'status': analysis.status,
        'progress_percentage': float(analysis.progress_percentage) if analysis.progress_percentage else 0,
        'status_message': analysis.status_message,
        'is_complete': analysis.status == RaschAnalysisStatus.COMPLETED.value,
        'is_failed': analysis.status == RaschAnalysisStatus.FAILED.value,
        'started_at': analysis.started_at.isoformat() if analysis.started_at else None,
        'completed_at': analysis.completed_at.isoformat() if analysis.completed_at else None,
    })


@rasch_bp.route('/analyses/<int:analysis_id>', methods=['DELETE'])
@login_required
def api_delete_analysis(analysis_id):
    """Delete analysis"""
    analysis = get_analysis_or_abort(analysis_id)
    
    if not isinstance(analysis, RaschAnalysis):
        return analysis
    
    db.session.delete(analysis)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Analisis berhasil dihapus'
    })


# ============================================================
# Results - Person Measures
# ============================================================

@rasch_bp.route('/analyses/<int:analysis_id>/persons', methods=['GET'])
@login_required
def api_get_person_measures(analysis_id):
    """
    Get person measures (ability θ) untuk semua siswa.
    
    Query params:
    - student_id: Filter by specific student
    
    Response:
    {
        "analysis_id": 1,
        "persons": [
            {
                "student_id": 101,
                "student_name": "Ahmad",
                "raw_score": 85,
                "percentage": 85.0,
                "theta": 1.23,
                "theta_se": 0.15,
                "ability_level": "high",
                "ability_percentile": 78.5,
                "fit_status": "well_fitted",
                "outfit_mnsq": 0.95,
                "infit_mnsq": 1.02
            }
        ]
    }
    """
    from app.models.user import User
    
    analysis = get_analysis_or_abort(analysis_id)
    
    if not isinstance(analysis, RaschAnalysis):
        return analysis
    
    student_id = request.args.get('student_id', type=int)
    
    query = RaschPersonMeasure.query.filter_by(rasch_analysis_id=analysis_id)
    
    if student_id:
        query = query.filter_by(student_id=student_id)
    
    measures = query.all()
    
    persons = []
    for m in measures:
        persons.append({
            'student_id': m.student_id,
            'student_name': m.student.name if m.student else 'Unknown',
            'raw_score': m.raw_score,
            'percentage': float(m.percentage) if m.percentage else None,
            'theta': float(m.theta) if m.theta else None,
            'theta_se': float(m.theta_se) if m.theta_se else None,
            'theta_centered': float(m.theta_centered) if m.theta_centered else None,
            'ability_level': m.ability_level,
            'ability_percentile': float(m.ability_percentile) if m.ability_percentile else None,
            'fit_status': m.fit_status,
            'fit_category': m.fit_category,
            'outfit_mnsq': float(m.outfit_mnsq) if m.outfit_mnsq else None,
            'outfit_zstd': float(m.outfit_zstd) if m.outfit_zstd else None,
            'infit_mnsq': float(m.infit_mnsq) if m.infit_mnsq else None,
            'infit_zstd': float(m.infit_zstd) if m.infit_zstd else None,
        })
    
    # Sort by theta descending
    persons.sort(key=lambda x: x['theta'] or 0, reverse=True)
    
    return jsonify({
        'success': True,
        'analysis_id': analysis_id,
        'count': len(persons),
        'persons': persons
    })


# ============================================================
# Results - Item Measures
# ============================================================

@rasch_bp.route('/analyses/<int:analysis_id>/items', methods=['GET'])
@login_required
def api_get_item_measures(analysis_id):
    """
    Get item measures (difficulty δ) untuk semua soal.
    
    Response:
    {
        "analysis_id": 1,
        "items": [
            {
                "question_id": 1,
                "question_text": "Apa ibu kota Indonesia?",
                "delta": -1.5,
                "difficulty_level": "easy",
                "p_value": 0.85,
                "point_biserial": 0.42,
                "bloom_level": "remember",
                "fit_status": "well_fitted"
            }
        ]
    }
    """
    analysis = get_analysis_or_abort(analysis_id)
    
    if not isinstance(analysis, RaschAnalysis):
        return analysis
    
    measures = RaschItemMeasure.query.filter_by(rasch_analysis_id=analysis_id).all()
    
    items = []
    for m in measures:
        items.append({
            'question_id': m.question_id,
            'question_text': (m.question.question_text[:100] + '...') if m.question and m.question.question_text else None,
            'delta': float(m.delta) if m.delta else None,
            'delta_se': float(m.delta_se) if m.delta_se else None,
            'difficulty_level': m.difficulty_level,
            'p_value': float(m.p_value) if m.p_value else None,
            'point_biserial': float(m.point_biserial) if m.point_biserial else None,
            'bloom_level': m.bloom_level,
            'fit_status': m.fit_status,
            'fit_category': m.fit_category,
            'outfit_mnsq': float(m.outfit_mnsq) if m.outfit_mnsq else None,
            'infit_mnsq': float(m.infit_mnsq) if m.infit_mnsq else None,
        })
    
    # Sort by delta (easiest to hardest)
    items.sort(key=lambda x: x['delta'] or 0)
    
    return jsonify({
        'success': True,
        'analysis_id': analysis_id,
        'count': len(items),
        'items': items
    })


# ============================================================
# Wright Map Visualization
# ============================================================

@rasch_bp.route('/analyses/<int:analysis_id>/wright-map', methods=['GET'])
@login_required
def api_get_wright_map(analysis_id):
    """
    Get data untuk Wright Map visualization.
    
    Wright Map menampilkan distribusi person ability dan item difficulty
    dalam satu vertical map.
    
    Response:
    {
        "analysis_id": 1,
        "map_data": {
            "person_distribution": [
                {"theta_range": "-2.0 to -1.5", "count": 5},
                ...
            ],
            "item_distribution": [
                {"delta_range": "-2.0 to -1.5", "count": 3},
                ...
            ],
            "mean_person_theta": 0.5,
            "mean_item_delta": 0.0,
            "sd_person": 1.2,
            "sd_item": 0.8
        }
    }
    """
    import math
    
    analysis = get_analysis_or_abort(analysis_id)
    
    if not isinstance(analysis, RaschAnalysis):
        return analysis
    
    # Get person measures
    person_measures = RaschPersonMeasure.query.filter_by(
        rasch_analysis_id=analysis_id
    ).filter(RaschPersonMeasure.theta.isnot(None)).all()
    
    # Get item measures
    item_measures = RaschItemMeasure.query.filter_by(
        rasch_analysis_id=analysis_id
    ).filter(RaschItemMeasure.delta.isnot(None)).all()
    
    # Calculate distributions
    def get_distribution(measures, value_attr):
        """Group measures into bands"""
        bands = {
            'very_high': {'range': '> 2.0', 'count': 0},
            'high': {'range': '0.5 to 2.0', 'count': 0},
            'average': {'range': '-0.5 to 0.5', 'count': 0},
            'low': {'range': '-2.0 to -0.5', 'count': 0},
            'very_low': {'range': '< -2.0', 'count': 0},
        }
        
        for m in measures:
            value = getattr(m, value_attr)
            if value is None:
                continue
            
            if value > 2.0:
                bands['very_high']['count'] += 1
            elif value > 0.5:
                bands['high']['count'] += 1
            elif value > -0.5:
                bands['average']['count'] += 1
            elif value > -2.0:
                bands['low']['count'] += 1
            else:
                bands['very_low']['count'] += 1
        
        return [
            {'level': level, **data}
            for level, data in bands.items()
        ]
    
    # Calculate statistics
    person_thetas = [m.theta for m in person_measures if m.theta is not None]
    item_deltas = [m.delta for m in item_measures if m.delta is not None]
    
    def calc_stats(values):
        if not values:
            return {'mean': 0, 'sd': 0}
        
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        sd = math.sqrt(variance)
        
        return {'mean': mean, 'sd': sd}
    
    person_stats = calc_stats(person_thetas)
    item_stats = calc_stats(item_deltas)
    
    return jsonify({
        'success': True,
        'analysis_id': analysis_id,
        'map_data': {
            'person_distribution': get_distribution(person_measures, 'theta'),
            'item_distribution': get_distribution(item_measures, 'delta'),
            'mean_person_theta': round(person_stats['mean'], 3),
            'mean_item_delta': round(item_stats['mean'], 3),
            'sd_person': round(person_stats['sd'], 3),
            'sd_item': round(item_stats['sd'], 3),
        },
        'num_persons': len(person_measures),
        'num_items': len(item_measures),
    })


# ============================================================
# Bloom Taxonomy Analysis
# ============================================================

@rasch_bp.route('/quizzes/<int:quiz_id>/bloom-summary', methods=['GET'])
@login_required
def api_get_bloom_summary(quiz_id):
    """
    Get Bloom taxonomy distribution untuk quiz.
    
    Response:
    {
        "quiz_id": 123,
        "total_questions": 30,
        "distribution": {
            "remember": {"count": 5, "percentage": 16.7},
            "understand": {"count": 8, "percentage": 26.7},
            ...
        },
        "cognitive_depth": "moderate"
    }
    """
    from app.models.quiz import Question
    from app.models.rasch import QuestionBloomTaxonomy
    
    quiz = Quiz.query.get(quiz_id)
    
    if not quiz:
        return jsonify({'success': False, 'message': 'Quiz tidak ditemukan'}), 404
    
    # Check permission
    course = Course.query.get(quiz.course_id)
    if course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        return jsonify({'success': False, 'message': 'Akses ditolak'}), 403
    
    # Get questions
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    total = len(questions)

    if total == 0:
        return jsonify({
            'success': True,
            'quiz_id': quiz_id,
            'total_questions': 0,
            'distribution': {},
            'cognitive_depth': 'unknown'
        })

    # Pre-load all Bloom taxonomy classifications in a single query
    question_ids = [q.id for q in questions]
    all_blooms = QuestionBloomTaxonomy.query.filter(
        QuestionBloomTaxonomy.question_id.in_(question_ids)
    ).all()
    
    # Create a lookup dictionary: question_id -> bloom
    blooms_lookup = {b.question_id: b for b in all_blooms}

    # Count Bloom levels
    distribution = {
        'remember': 0,
        'understand': 0,
        'apply': 0,
        'analyze': 0,
        'evaluate': 0,
        'create': 0,
        'unclassified': 0,
    }

    for q in questions:
        bloom = blooms_lookup.get(q.id)

        if bloom:
            level = bloom.bloom_level.value
            if level in distribution:
                distribution[level] += 1
            else:
                distribution['unclassified'] += 1
        else:
            distribution['unclassified'] += 1
    
    # Calculate percentages
    distribution_with_pct = {}
    for level, count in distribution.items():
        distribution_with_pct[level] = {
            'count': count,
            'percentage': round(count / total * 100, 1) if total > 0 else 0
        }
    
    # Determine cognitive depth
    higher_order = distribution['analyze'] + distribution['evaluate'] + distribution['create']
    lower_order = distribution['remember'] + distribution['understand']
    
    if higher_order > lower_order:
        cognitive_depth = 'high'
    elif higher_order < lower_order:
        cognitive_depth = 'low'
    else:
        cognitive_depth = 'moderate'
    
    return jsonify({
        'success': True,
        'quiz_id': quiz_id,
        'total_questions': total,
        'distribution': distribution_with_pct,
        'cognitive_depth': cognitive_depth,
    })


@rasch_bp.route('/course/<int:course_id>/my-ability', methods=['GET'])
@login_required
def api_get_my_ability(course_id):
    """
    Get Rasch ability data untuk siswa yang sedang login.
    
    Response:
    {
        "success": true,
        "ability": {
            "theta": 0.85,
            "ability_level": "high",
            "ability_percentile": 75.5,
            "raw_score": 25,
            "total_items": 30,
            "created_at": "2026-03-23"
        }
    }
    """
    from sqlalchemy import func
    
    # Check if student is enrolled
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'success': False, 'message': 'Kursus tidak ditemukan'}), 404
    
    # Verify student is enrolled
    if current_user.role == UserRole.MURID:
        if current_user.id not in [s.id for s in course.students.all()]:
            return jsonify({'success': False, 'message': 'Anda tidak terdaftar di kursus ini'}), 403
    elif current_user.role == UserRole.GURU:
        # Teachers can view but this endpoint is primarily for students
        pass
    else:
        return jsonify({'success': False, 'message': 'Akses ditolak'}), 403
    
    # Get latest Rasch analysis for this course
    latest_analysis = RaschAnalysis.query.filter_by(
        course_id=course_id
    ).order_by(RaschAnalysis.created_at.desc()).first()
    
    if not latest_analysis:
        return jsonify({
            'success': False,
            'message': 'Belum ada analisis Rasch untuk kursus ini'
        }), 404
    
    # Get student's ability measure
    student_measure = RaschPersonMeasure.query.filter_by(
        analysis_id=latest_analysis.id,
        user_id=current_user.id
    ).first()
    
    if not student_measure:
        return jsonify({
            'success': False,
            'message': 'Anda belum memiliki hasil analisis Rasch'
        }), 404
    
    # Calculate percentile (percentage of students with lower ability)
    lower_students = RaschPersonMeasure.query.filter(
        RaschPersonMeasure.analysis_id == latest_analysis.id,
        RaschPersonMeasure.theta < student_measure.theta
    ).count()
    
    total_students = RaschPersonMeasure.query.filter_by(
        analysis_id=latest_analysis.id
    ).count()
    
    percentile = (lower_students / total_students * 100) if total_students > 0 else 50
    
    return jsonify({
        'success': True,
        'ability': {
            'theta': float(student_measure.theta) if student_measure.theta else 0,
            'ability_level': student_measure.ability_level,
            'ability_percentile': round(percentile, 1),
            'raw_score': student_measure.raw_score,
            'total_items': student_measure.total_items,
            'created_at': student_measure.created_at.strftime('%Y-%m-%d') if student_measure.created_at else None
        }
    })
