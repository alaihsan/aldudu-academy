"""
Rasch Analysis API Blueprint

Endpoints untuk:
- Threshold checking & manual trigger
- Status polling
- Results retrieval (person measures, item measures)
- Wright Map visualization
- Simplified metrics for teachers
"""

import math
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


@rasch_bp.route('/quizzes/<int:quiz_id>/process-late-submissions', methods=['POST'])
@login_required
def api_process_late_submissions(quiz_id):
    """
    Process late submissions untuk quiz yang sudah dianalisis.
    
    Menggunakan anchor values untuk menghitung ability siswa baru
    tanpa perlu re-run analisis penuh.
    
    Request (optional):
    {
        "submission_id": 123  // Process specific submission only
    }
    
    Response:
    {
        "success": true,
        "processed": 5,
        "failed": 0,
        "total_late": 5,
        "results": [...]
    }
    """
    from app.models.quiz import Quiz, QuizSubmission
    from app.models.gradebook import GradeItem
    from app.models.rasch import RaschAnalysis, RaschAnalysisStatus
    from app.services.rasch_anchor_service import process_late_submissions, RaschAnchorService

    quiz = Quiz.query.get(quiz_id)

    if not quiz:
        return jsonify({'success': False, 'message': 'Quiz tidak ditemukan'}), 404

    # Check permission
    course = Course.query.get(quiz.course_id)
    if course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        return jsonify({'success': False, 'message': 'Akses ditolak'}), 403

    # Get completed analysis
    grade_item = GradeItem.query.filter_by(quiz_id=quiz_id).first()
    
    if not grade_item or not grade_item.rasch_analysis_id:
        return jsonify({
            'success': False,
            'message': 'Belum ada analisis Rasch untuk quiz ini'
        }), 404
    
    analysis = RaschAnalysis.query.get(grade_item.rasch_analysis_id)
    
    if not analysis or analysis.status != RaschAnalysisStatus.COMPLETED.value:
        return jsonify({
            'success': False,
            'message': 'Analisis belum completed. Tidak ada late submissions untuk diproses.'
        }), 400

    # Check if specific submission requested
    data = request.get_json() or {}
    submission_id = data.get('submission_id', type=int)
    
    if submission_id:
        # Process single submission
        service = RaschAnchorService(analysis_id=analysis.id)
        result = service.calculate_ability_for_submission(submission_id)
        
        if result and result.get('success'):
            return jsonify({
                'success': True,
                'submission_id': submission_id,
                'result': result
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Gagal memproses submission ini'
            }), 400
    else:
        # Process all late submissions
        result = process_late_submissions(quiz_id)
        
        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify({
                'success': False,
                'message': result.get('error', 'Gagal memproses late submissions')
            }), 400


@rasch_bp.route('/analyses/<int:analysis_id>/re-run', methods=['POST'])
@login_required
def api_rerun_analysis(analysis_id):
    """
    Re-run analisis Rasch untuk include late submissions.
    
    Ini akan menghapus person dan item measures lama dan menjalankan
    ulang analisis dengan semua submissions terbaru.
    
    Request (optional):
    {
        "min_late_percentage": 10  // Minimum percentage of late submissions to trigger re-run
    }
    """
    from app.models.rasch import RaschItemMeasure, RaschPersonMeasure
    
    analysis = get_analysis_or_abort(analysis_id)

    if not isinstance(analysis, RaschAnalysis):
        return analysis
    
    # Check if analysis is completed
    if analysis.status != RaschAnalysisStatus.COMPLETED.value:
        return jsonify({
            'success': False,
            'message': 'Hanya analisis completed yang bisa di-re-run'
        }), 400
    
    # Check late submissions
    if analysis.quiz_id:
        submission_count = QuizSubmission.query.filter_by(quiz_id=analysis.quiz_id).count()
        existing_measures = RaschPersonMeasure.query.filter_by(
            rasch_analysis_id=analysis_id
        ).count()
        late_count = submission_count - existing_measures
        
        if late_count <= 0:
            return jsonify({
                'success': False,
                'message': 'Tidak ada late submissions untuk di-re-run'
            }), 400
        
        # Check minimum percentage
        data = request.get_json() or {}
        min_percentage = data.get('min_late_percentage', 0)
        late_percentage = (late_count / submission_count * 100) if submission_count > 0 else 0
        
        if late_percentage < min_percentage:
            return jsonify({
                'success': False,
                'message': f'Late submissions hanya {late_percentage:.1f}% (minimum: {min_percentage}%)'
            }), 400
    
    try:
        # Delete old measures
        RaschPersonMeasure.query.filter_by(rasch_analysis_id=analysis_id).delete()
        RaschItemMeasure.query.filter_by(rasch_analysis_id=analysis_id).delete()
        
        # Reset analysis status
        analysis.status = RaschAnalysisStatus.PENDING.value
        analysis.status_message = "Re-running analysis dengan data terbaru"
        db.session.commit()
        
        # Trigger analysis
        from app.services.rasch_threshold_service import RaschThresholdService
        service = RaschThresholdService()
        service._trigger_analysis(analysis, check_type='manual')
        
        return jsonify({
            'success': True,
            'message': f'Analisis di-re-run dengan {late_count} late submissions',
            'analysis_id': analysis_id,
            'late_count': late_count,
        })
        
    except Exception as e:
        logger.error(f"Error re-running analysis: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


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


# ============================================================
# Simplified Metrics (Teacher-Friendly)
# ============================================================

@rasch_bp.route('/analyses/<int:analysis_id>/persons/simplified', methods=['GET'])
@login_required
def api_get_person_measures_simplified(analysis_id):
    """
    Get person measures dengan metrik yang disederhanakan untuk guru.
    
    Termasuk:
    - Scaled Score (0-100)
    - Warning badges untuk fit issues
    - Actionable insights
    
    Response:
    {
        "success": true,
        "persons": [
            {
                "student_id": 101,
                "student_name": "Ahmad",
                "scaled_score": 72.5,
                "grade": "B",
                "category": "Baik",
                "ability_level": "high",
                "warning": {
                    "level": "none",
                    "label": "VALID",
                    "message": "Pola jawaban konsisten dan valid",
                    "color": "badge-success"
                },
                "insights": [
                    {
                        "type": "strength",
                        "title": "Kemampuan Tinggi",
                        "description": "Siswa menunjukkan pemahaman yang sangat baik...",
                        "priority": 4
                    }
                ],
                "mastery_zone": {
                    "zone": "developing",
                    "label": "Dalam Pengembangan",
                    "mastered_percentage": 65.0,
                    "recommendation": "Fokus pada soal-soal di zona challenge..."
                }
            }
        ]
    }
    """
    from app.services.rasch_ui_helpers import (
        format_scaled_score,
        get_person_fit_warning,
        generate_person_insights,
        get_mastery_zone,
    )
    
    analysis = get_analysis_or_abort(analysis_id)
    
    if not isinstance(analysis, RaschAnalysis):
        return analysis
    
    # Get all person measures
    measures = RaschPersonMeasure.query.filter_by(rasch_analysis_id=analysis_id).all()
    
    # Get all item deltas for mastery zone calculation
    item_measures = RaschItemMeasure.query.filter_by(rasch_analysis_id=analysis_id).all()
    item_deltas = [m.delta for m in item_measures if m.delta is not None]
    
    # Calculate mean and SD for scaling
    person_thetas = [m.theta for m in measures if m.theta is not None]
    mean_theta = sum(person_thetas) / len(person_thetas) if person_thetas else 0
    
    if len(person_thetas) > 1:
        sd_theta = math.sqrt(sum((t - mean_theta) ** 2 for t in person_thetas) / (len(person_thetas) - 1))
    else:
        sd_theta = 1
    
    persons = []
    for m in measures:
        # Scaled score transformation
        score_data = format_scaled_score(m.theta, {'mean_theta': mean_theta, 'sd_theta': sd_theta})
        
        # Warning badge
        warning = get_person_fit_warning(m.outfit_mnsq or 1.0, m.infit_mnsq or 1.0)
        
        # Insights
        insights = generate_person_insights(
            theta=m.theta or 0,
            outfit_mnsq=m.outfit_mnsq or 1.0,
            theta_se=m.theta_se or 0.5,
            percentile=m.ability_percentile or 50,
            ability_level=m.ability_level or 'average'
        )
        
        # Mastery zone
        mastery = get_mastery_zone(m.theta or 0, item_deltas)
        
        persons.append({
            'student_id': m.student_id,
            'student_name': m.student.name if m.student else 'Unknown',
            'scaled_score': score_data['scaled_score'],
            'grade': score_data['grade'],
            'category': score_data['category'],
            'ability_level': m.ability_level,
            'ability_percentile': float(m.ability_percentile) if m.ability_percentile else None,
            'theta': float(m.theta) if m.theta else None,  # Keep for reference
            'warning': {
                'level': warning.level.value,
                'label': warning.label,
                'message': warning.message,
                'color': warning.color,
                'icon': warning.icon,
            },
            'insights': [
                {
                    'type': i.type.value,
                    'title': i.title,
                    'description': i.description,
                    'priority': i.priority,
                }
                for i in insights
            ],
            'mastery_zone': mastery,
        })
    
    # Sort by scaled score descending
    persons.sort(key=lambda x: x['scaled_score'], reverse=True)
    
    return jsonify({
        'success': True,
        'analysis_id': analysis_id,
        'count': len(persons),
        'scaling_info': {
            'mean_theta': round(mean_theta, 3),
            'sd_theta': round(sd_theta, 3),
            'formula': 'Scaled Score = 50 + 10 * ((theta - mean) / SD)',
        },
        'persons': persons,
    })


@rasch_bp.route('/analyses/<int:analysis_id>/items/simplified', methods=['GET'])
@login_required
def api_get_item_measures_simplified(analysis_id):
    """
    Get item measures dengan metrik yang disederhanakan untuk guru.
    
    Termasuk:
    - Difficulty label (Mudah, Sedang, Sulit)
    - Warning badges untuk problematic items
    - Actionable insights
    
    Response:
    {
        "success": true,
        "items": [
            {
                "question_id": 1,
                "question_text": "Apa ibu kota Indonesia?",
                "difficulty_label": "Mudah",
                "difficulty_description": "Lebih dari 80% siswa menjawab benar",
                "p_value": 0.85,
                "delta": -1.5,
                "discrimination": {
                    "label": "Baik",
                    "point_biserial": 0.42
                },
                "warning": {
                    "level": "none",
                    "label": "BAIK",
                    "message": "Soal berfungsi dengan baik",
                    "color": "badge-success"
                },
                "insights": [...],
                "bloom_level": "remember"
            }
        ]
    }
    """
    from app.services.rasch_ui_helpers import (
        format_item_difficulty,
        get_item_fit_warning,
        generate_item_insights,
    )
    
    analysis = get_analysis_or_abort(analysis_id)
    
    if not isinstance(analysis, RaschAnalysis):
        return analysis
    
    # Get all item measures
    measures = RaschItemMeasure.query.filter_by(rasch_analysis_id=analysis_id).all()
    
    items = []
    for m in measures:
        # Difficulty interpretation
        difficulty = format_item_difficulty(m.delta or 0, m.p_value or 0.5)
        
        # Warning badge
        warning = get_item_fit_warning(m.outfit_mnsq or 1.0, m.infit_mnsq or 1.0)
        
        # Insights
        insights = generate_item_insights(
            delta=m.delta or 0,
            p_value=m.p_value or 0.5,
            point_biserial=m.point_biserial or 0,
            outfit_mnsq=m.outfit_mnsq or 1.0,
            bloom_level=m.bloom_level
        )
        
        # Discrimination interpretation
        pb = m.point_biserial or 0
        if pb >= 0.4:
            disc_label = 'Sangat Baik'
            disc_color = 'success'
        elif pb >= 0.3:
            disc_label = 'Baik'
            disc_color = 'info'
        elif pb >= 0.2:
            disc_label = 'Cukup'
            disc_color = 'warning'
        else:
            disc_label = 'Kurang'
            disc_color = 'danger'
        
        items.append({
            'question_id': m.question_id,
            'question_text': (m.question.question_text[:100] + '...') if m.question and m.question.question_text else None,
            'difficulty_label': difficulty['difficulty_label'],
            'difficulty_description': difficulty['difficulty_description'],
            'difficulty_color': difficulty['color_class'],
            'p_value': difficulty['p_value'],
            'delta': difficulty['delta'],
            'discrimination': {
                'label': disc_label,
                'point_biserial': round(pb, 3),
                'color': disc_color,
            },
            'warning': {
                'level': warning.level.value,
                'label': warning.label,
                'message': warning.message,
                'color': warning.color,
                'icon': warning.icon,
            },
            'insights': [
                {
                    'type': i.type.value,
                    'title': i.title,
                    'description': i.description,
                    'priority': i.priority,
                }
                for i in insights
            ],
            'bloom_level': m.bloom_level,
            'fit_status': m.fit_status,
        })
    
    # Sort by p_value (easiest first)
    items.sort(key=lambda x: x['p_value'], reverse=True)
    
    return jsonify({
        'success': True,
        'analysis_id': analysis_id,
        'count': len(items),
        'items': items,
    })


@rasch_bp.route('/analyses/<int:analysis_id>/insights', methods=['GET'])
@login_required
def api_get_analysis_insights(analysis_id):
    """
    Get actionable insights untuk keseluruhan analisis.
    
    Response:
    {
        "success": true,
        "quiz_insights": [...],
        "summary": {
            "reliability": {
                "value": 0.85,
                "label": "Sangat Baik",
                "color": "success"
            },
            "separation": {
                "person": 2.5,
                "item": 3.2,
                "label": "Baik"
            }
        },
        "recommendations": [...]
    }
    """
    from app.services.rasch_ui_helpers import (
        generate_quiz_insights,
        theta_to_scaled_score,
    )
    
    analysis = get_analysis_or_abort(analysis_id)
    
    if not isinstance(analysis, RaschAnalysis):
        return analysis
    
    # Generate quiz insights
    quiz_insights = generate_quiz_insights(
        cronbach_alpha=analysis.cronbach_alpha or 0.7,
        person_separation=analysis.person_separation_index or 1.5,
        item_separation=analysis.item_separation_index or 2.0,
        num_persons=analysis.num_persons or 0,
        num_items=analysis.num_items or 0,
    )
    
    # Reliability summary
    alpha = analysis.cronbach_alpha or 0
    if alpha >= 0.8:
        rel_label = 'Sangat Baik'
        rel_color = 'success'
    elif alpha >= 0.7:
        rel_label = 'Baik'
        rel_color = 'info'
    elif alpha >= 0.6:
        rel_label = 'Cukup'
        rel_color = 'warning'
    else:
        rel_label = 'Kurang'
        rel_color = 'danger'
    
    # Separation summary
    ps = analysis.person_separation_index or 0
    if ps >= 2.0:
        sep_label = 'Baik'
        sep_color = 'success'
    elif ps >= 1.5:
        sep_label = 'Cukup'
        sep_color = 'warning'
    else:
        sep_label = 'Kurang'
        sep_color = 'danger'
    
    return jsonify({
        'success': True,
        'analysis_id': analysis_id,
        'quiz_insights': [
            {
                'type': i.type.value,
                'title': i.title,
                'description': i.description,
                'priority': i.priority,
            }
            for i in quiz_insights
        ],
        'summary': {
            'reliability': {
                'value': round(alpha, 3),
                'label': rel_label,
                'color': rel_color,
                'description': 'Konsistensi internal kuis',
            },
            'separation': {
                'person': round(ps, 2),
                'item': round(analysis.item_separation_index or 0, 2),
                'label': sep_label,
                'color': sep_color,
                'description': 'Kemampuan membedakan level kemampuan',
            },
        },
        'recommendations': [
            {
                'type': i.type.value,
                'title': i.title,
                'description': i.description,
            }
            for i in quiz_insights if i.type.value in ['suggestion', 'weakness']
        ],
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
    
    Response includes UI hints untuk handling unclassified questions.

    Response:
    {
        "quiz_id": 123,
        "total_questions": 30,
        "distribution": {
            "remember": {"count": 5, "percentage": 16.7},
            "understand": {"count": 8, "percentage": 26.7},
            ...
        },
        "cognitive_depth": "moderate",
        "mapping_status": {
            "is_complete": false,
            "mapped_count": 20,
            "unmapped_count": 10,
            "mapped_percentage": 66.7,
            "is_optional_feature": true,
            "ui_message": "10 soal belum diklasifikasikan. Taksonomi Bloom adalah fitur opsional.",
            "recommendation": "Klasifikasikan soal untuk analisis kognitif yang lebih lengkap"
        }
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
            'cognitive_depth': 'unknown',
            'mapping_status': {
                'is_complete': False,
                'mapped_count': 0,
                'unmapped_count': 0,
                'mapped_percentage': 0,
                'is_optional_feature': True,
                'ui_message': 'Quiz ini belum memiliki soal.',
                'recommendation': 'Tambahkan soal terlebih dahulu.'
            }
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

    # Determine cognitive depth (only based on classified questions)
    classified_count = total - distribution['unclassified']
    higher_order = distribution['analyze'] + distribution['evaluate'] + distribution['create']
    lower_order = distribution['remember'] + distribution['understand']

    if classified_count == 0:
        cognitive_depth = 'not_classified'
    elif higher_order > lower_order:
        cognitive_depth = 'high'
    elif higher_order < lower_order:
        cognitive_depth = 'low'
    else:
        cognitive_depth = 'moderate'

    # Build mapping status for UI
    mapped_count = classified_count
    unmapped_count = distribution['unclassified']
    mapped_percentage = round(mapped_count / total * 100, 1) if total > 0 else 0
    is_complete = unmapped_count == 0

    # Generate UI messages based on mapping status
    if unmapped_count == 0:
        ui_message = "Semua soal sudah diklasifikasikan dengan Taksonomi Bloom."
        ui_status = "complete"
        recommendation = None
    elif unmapped_count == total:
        ui_message = "Belum ada soal yang diklasifikasikan. Taksonomi Bloom adalah fitur opsional untuk analisis kognitif."
        ui_status = "not_started"
        recommendation = "Klasifikasikan soal-soal untuk melihat distribusi tingkat kognitif."
    elif mapped_percentage >= 80:
        ui_message = f"{unmapped_count} soal belum diklasifikasikan. Analisis sudah cukup representatif."
        ui_status = "mostly_complete"
        recommendation = None
    else:
        ui_message = f"{unmapped_count} dari {total} soal belum diklasifikasikan. Taksonomi Bloom adalah fitur opsional."
        ui_status = "in_progress"
        recommendation = "Klasifikasikan lebih banyak soal untuk analisis kognitif yang lebih akurat."

    mapping_status = {
        'is_complete': is_complete,
        'mapped_count': mapped_count,
        'unmapped_count': unmapped_count,
        'mapped_percentage': mapped_percentage,
        'is_optional_feature': True,
        'ui_message': ui_message,
        'ui_status': ui_status,
        'recommendation': recommendation,
        'feature_info': {
            'title': 'Taksonomi Bloom (Opsional)',
            'description': 'Klasifikasi tingkat kognitif soal membantu menganalisis kedalaman penilaian.',
            'benefits': [
                'Memahami distribusi tingkat kesulitan kognitif',
                'Memastikan keseimbangan soal lower-order dan higher-order thinking',
                'Analisis korelasi antara cognitive level dan student performance'
            ],
            'skip_message': 'Anda dapat melewati fitur ini dan tetap menggunakan analisis Rasch dasar.'
        }
    }

    return jsonify({
        'success': True,
        'quiz_id': quiz_id,
        'total_questions': total,
        'distribution': distribution_with_pct,
        'cognitive_depth': cognitive_depth,
        'mapping_status': mapping_status,
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


# ============================================================
# Scheduled Batch Processing (Admin Only)
# ============================================================

@rasch_bp.route('/admin/batch/nightly-analysis', methods=['POST'])
@login_required
def api_run_nightly_batch():
    """
    Run nightly batch analysis untuk semua quiz yang eligible.
    
    Hanya untuk super admin.
    
    Request (optional):
    {
        "course_id": 123  // Filter by specific course
    }
    
    Response:
    {
        "success": true,
        "new_analyses": 5,
        "re_analyses": 2,
        "skipped": 10,
        "failed": 0,
        "details": [...]
    }
    """
    from app.models.user import UserRole
    
    # Only super admin
    if current_user.role != UserRole.SUPER_ADMIN:
        return jsonify({
            'success': False,
            'message': 'Akses ditolak. Hanya super admin yang bisa menjalankan batch processing.'
        }), 403
    
    data = request.get_json() or {}
    course_id = data.get('course_id', type=int)
    
    from app.services.rasch_scheduled_service import run_nightly_analysis
    
    result = run_nightly_analysis(course_id)
    
    if result.get('success'):
        return jsonify(result)
    else:
        return jsonify({
            'success': False,
            'message': result.get('error', 'Batch processing failed')
        }), 500


@rasch_bp.route('/admin/batch/late-submissions', methods=['POST'])
@login_required
def api_run_late_submissions_batch():
    """
    Process late submissions untuk semua quiz yang sudah dianalisis.
    
    Hanya untuk super admin.
    
    Request (optional):
    {
        "course_id": 123  // Filter by specific course
    }
    
    Response:
    {
        "success": true,
        "quizzes_processed": 5,
        "students_processed": 15,
        "failed": 0,
        "details": [...]
    }
    """
    from app.models.user import UserRole
    
    # Only super admin
    if current_user.role != UserRole.SUPER_ADMIN:
        return jsonify({
            'success': False,
            'message': 'Akses ditolak. Hanya super admin yang bisa menjalankan batch processing.'
        }), 403
    
    data = request.get_json() or {}
    course_id = data.get('course_id', type=int)
    
    from app.services.rasch_scheduled_service import run_late_submissions_processing
    
    result = run_late_submissions_processing(course_id)
    
    if result.get('success'):
        return jsonify(result)
    else:
        return jsonify({
            'success': False,
            'message': result.get('error', 'Batch processing failed')
        }), 500
