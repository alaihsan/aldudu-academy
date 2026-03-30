"""
Evaluation Tes Service Layer

Service untuk aggregasi data evaluasi tes (quiz & assignment) dengan analisis statistik
dan visualisasi untuk dashboard guru.
"""
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy import func, case, cast, Numeric
from sqlalchemy.orm import joinedload
from collections import defaultdict
from app.models import (
    db, Course, Quiz, QuizStatus, QuizSubmission, Question, QuestionType,
    Answer, User, UserRole, Assignment, AssignmentSubmission, Option
)
from app.models.gradebook import GradeItem, GradeEntry, GradeCategory, GradeCategoryType
from app.models.rasch import RaschAnalysis, RaschAnalysisStatus, RaschPersonMeasure, RaschItemMeasure
from app.helpers import get_jakarta_now


class EvaluationTesService:
    """
    Service layer untuk Evaluasi Tes
    
    Menyediakan metode untuk:
    - Aggregasi statistik tes (quiz & assignment)
    - Analisis distribusi nilai
    - Item analysis (difficulty, discrimination)
    - Visualisasi data untuk Chart.js
    """
    
    def __init__(self, course_id: int, teacher_id: int):
        self.course_id = course_id
        self.teacher_id = teacher_id
        self._validate_permission()
    
    def _validate_permission(self):
        """Validasi bahwa user adalah guru dari course ini"""
        course = Course.query.get(self.course_id)
        if not course:
            raise ValueError("Course tidak ditemukan")
        
        if course.teacher_id != self.teacher_id:
            # Check if super_admin
            user = User.query.get(self.teacher_id)
            if not user or user.role != UserRole.SUPER_ADMIN:
                raise PermissionError("Tidak memiliki akses ke course ini")
    
    def get_dashboard_summary(self) -> Dict[str, Any]:
        """
        Ringkasan dashboard evaluasi tes
        
        Returns:
            Dict dengan statistik agregat
        """
        # Get all quizzes
        quizzes = Quiz.query.filter_by(course_id=self.course_id).all()
        quiz_ids = [q.id for q in quizzes]
        
        # Get all grade items (assignments & quizzes)
        grade_items = GradeItem.query.filter_by(course_id=self.course_id).all()
        assignment_items = [gi for gi in grade_items if gi.assignment_id]
        
        # Count published
        published_quizzes = Quiz.query.filter(
            Quiz.course_id == self.course_id,
            Quiz.status == QuizStatus.PUBLISHED
        ).count()
        
        # Total submissions
        total_quiz_submissions = 0
        if quiz_ids:
            total_quiz_submissions = db.session.query(func.count(QuizSubmission.id)).filter(
                QuizSubmission.quiz_id.in_(quiz_ids)
            ).scalar() or 0
        
        # Assignment submissions
        total_assignment_submissions = 0
        if assignment_items:
            assignment_ids = [gi.assignment_id for gi in assignment_items]
            total_assignment_submissions = db.session.query(func.count(AssignmentSubmission.id)).filter(
                AssignmentSubmission.assignment_id.in_(assignment_ids)
            ).scalar() or 0
        
        # Average scores from grade entries
        avg_score_result = db.session.query(
            func.avg(GradeEntry.percentage)
        ).join(GradeItem).filter(
            GradeItem.course_id == self.course_id
        ).scalar() or 0.0
        
        # Rasch analyses count
        rasch_count = RaschAnalysis.query.filter_by(course_id=self.course_id).count()
        
        # Count items needing attention
        items_needing_attention = self._count_items_needing_attention()
        
        return {
            'total_evaluations': len(quizzes) + len(assignment_items),
            'published_evaluations': published_quizzes + len([gi for gi in assignment_items if gi.quiz_id]),
            'total_submissions': total_quiz_submissions + total_assignment_submissions,
            'average_score': round(avg_score_result, 2),
            'evaluations_with_rasch': rasch_count,
            'total_quizzes': len(quizzes),
            'total_assignments': len(assignment_items),
            'items_needing_attention': items_needing_attention
        }
    
    def _count_items_needing_attention(self) -> Dict[str, int]:
        """Hitung soal yang perlu perhatian (terlalu mudah/sulit/daya beda rendah)"""
        quizzes = Quiz.query.filter_by(course_id=self.course_id).all()
        
        too_easy = 0
        too_hard = 0
        low_discrimination = 0
        
        for quiz in quizzes:
            questions = quiz.questions.all()
            for q in questions:
                total_answers = Answer.query.filter_by(question_id=q.id).count()
                if total_answers == 0:
                    continue
                
                correct_answers = 0
                if q.question_type in [QuestionType.MULTIPLE_CHOICE, QuestionType.TRUE_FALSE, QuestionType.DROPDOWN]:
                    correct_answers = db.session.query(func.count(Answer.id)).join(
                        Option, Answer.selected_option_id == Option.id
                    ).filter(
                        Answer.question_id == q.id,
                        Option.is_correct == True
                    ).scalar() or 0
                
                difficulty = (correct_answers / total_answers * 100) if total_answers > 0 else 50
                
                if difficulty > 90:
                    too_easy += 1
                elif difficulty < 20:
                    too_hard += 1
        
        return {
            'too_easy': too_easy,
            'too_hard': too_hard,
            'low_discrimination': low_discrimination,
            'total': too_easy + too_hard + low_discrimination
        }
    
    def get_score_distribution(self, evaluation_type: str = 'all') -> Dict[str, List]:
        """
        Distribusi nilai untuk visualisasi histogram
        
        Args:
            evaluation_type: 'quiz', 'assignment', atau 'all'
        
        Returns:
            Dict dengan labels, data, colors
        """
        # Define score ranges
        ranges = [
            (0, 10), (11, 20), (21, 30), (31, 40), (41, 50),
            (51, 60), (61, 70), (71, 80), (81, 90), (91, 100)
        ]
        
        labels = [f"{low}-{high}" for low, high in ranges]
        data = [0] * len(ranges)
        
        # Get grade items based on type
        query = GradeItem.query.filter_by(course_id=self.course_id)
        
        if evaluation_type == 'quiz':
            query = query.filter(GradeItem.quiz_id.isnot(None))
        elif evaluation_type == 'assignment':
            query = query.filter(GradeItem.assignment_id.isnot(None))
        
        grade_items = query.all()
        grade_item_ids = [gi.id for gi in grade_items]
        
        if not grade_item_ids:
            return {'labels': labels, 'data': data, 'colors': self._get_chart_colors(len(labels))}
        
        # Count students per range
        for i, (low, high) in enumerate(ranges):
            count = db.session.query(func.count(GradeEntry.id)).filter(
                GradeEntry.grade_item_id.in_(grade_item_ids),
                GradeEntry.percentage >= low,
                GradeEntry.percentage <= high
            ).scalar() or 0
            data[i] = count
        
        return {
            'labels': labels,
            'data': data,
            'colors': self._get_chart_colors(len(labels))
        }
    
    def get_evaluation_statistics(self, evaluation_id: int, evaluation_type: str) -> Dict[str, Any]:
        """
        Statistik detail untuk satu evaluasi
        """
        if evaluation_type == 'quiz':
            return self._get_quiz_statistics(evaluation_id)
        elif evaluation_type == 'assignment':
            return self._get_assignment_statistics(evaluation_id)
        else:
            raise ValueError("Invalid evaluation_type. Use 'quiz' or 'assignment'")
    
    def _get_quiz_statistics(self, quiz_id: int) -> Dict[str, Any]:
        """Statistik detail untuk quiz"""
        quiz = Quiz.query.get(quiz_id)
        if not quiz or quiz.course_id != self.course_id:
            raise ValueError("Quiz tidak ditemukan")
        
        submissions = QuizSubmission.query.filter_by(quiz_id=quiz_id).all()
        
        if not submissions:
            return self._empty_quiz_stats(quiz)
        
        # Calculate statistics
        scores = [s.score for s in submissions if s.score is not None]
        
        if not scores:
            return self._empty_quiz_stats(quiz)
        
        # Basic stats
        avg_score = sum(scores) / len(scores)
        max_score = max(scores)
        min_score = min(scores)
        
        # Median
        sorted_scores = sorted(scores)
        n = len(sorted_scores)
        median_score = sorted_scores[n // 2] if n % 2 == 1 else (sorted_scores[n // 2 - 1] + sorted_scores[n // 2]) / 2
        
        # Standard deviation
        variance = sum((x - avg_score) ** 2 for x in scores) / len(scores)
        std_deviation = variance ** 0.5
        
        # Completion rate
        course = Course.query.get(self.course_id)
        total_students = course.students.count() if course else 0
        completion_rate = (len(submissions) / total_students * 100) if total_students > 0 else 0
        
        # Question-level analysis
        questions = quiz.questions.order_by(Question.order).all()
        question_stats = []
        
        for q in questions:
            total_answers = Answer.query.filter_by(question_id=q.id).count()
            correct_answers = 0
            
            if q.question_type in [QuestionType.MULTIPLE_CHOICE, QuestionType.TRUE_FALSE, QuestionType.DROPDOWN]:
                correct_answers = db.session.query(func.count(Answer.id)).join(
                    Option, Answer.selected_option_id == Option.id
                ).filter(
                    Answer.question_id == q.id,
                    Option.is_correct == True
                ).scalar() or 0
            elif q.question_type == QuestionType.LONG_TEXT:
                correct_answers = db.session.query(func.count(Answer.id)).filter(
                    Answer.question_id == q.id,
                    Answer.manual_score != None
                ).scalar() or 0
            
            difficulty_index = (correct_answers / total_answers * 100) if total_answers > 0 else 0
            
            question_stats.append({
                'question_id': q.id,
                'question_text': q.question_text[:50] + '...' if len(q.question_text) > 50 else q.question_text,
                'question_type': q.question_type.value,
                'total_answers': total_answers,
                'correct_answers': correct_answers,
                'difficulty_index': round(difficulty_index, 2),
                'points': q.points,
                'difficulty_label': self._get_difficulty_label(difficulty_index)
            })
        
        # Score distribution for chart
        score_ranges = [(0, 59), (60, 69), (70, 79), (80, 89), (90, 100)]
        dist_labels = ['< 60', '60-69', '70-79', '80-89', '90-100']
        dist_data = [len([s for s in scores if low <= s <= high]) for low, high in score_ranges]
        
        return {
            'quiz': {'id': quiz.id, 'name': quiz.name, 'description': quiz.description},
            'total_submissions': len(submissions),
            'average_score': round(avg_score, 2),
            'max_score': round(max_score, 2),
            'min_score': round(min_score, 2),
            'median_score': round(median_score, 2),
            'std_deviation': round(std_deviation, 2),
            'completion_rate': round(completion_rate, 2),
            'question_stats': question_stats,
            'score_distribution': {
                'labels': dist_labels,
                'data': dist_data
            }
        }
    
    def _empty_quiz_stats(self, quiz) -> Dict[str, Any]:
        """Return empty stats for quiz with no submissions"""
        return {
            'quiz': {'id': quiz.id, 'name': quiz.name, 'description': quiz.description} if quiz else None,
            'total_submissions': 0,
            'average_score': 0,
            'max_score': 0,
            'min_score': 0,
            'median_score': 0,
            'std_deviation': 0,
            'completion_rate': 0,
            'question_stats': [],
            'score_distribution': {'labels': [], 'data': []}
        }
    
    def _get_difficulty_label(self, difficulty: float) -> str:
        """Label kesulitan untuk guru"""
        if difficulty > 80:
            return 'Mudah'
        elif difficulty > 40:
            return 'Sedang'
        else:
            return 'Sulit'
    
    def _get_assignment_statistics(self, grade_item_id: int) -> Dict[str, Any]:
        """Statistik detail untuk assignment"""
        grade_item = GradeItem.query.get(grade_item_id)
        if not grade_item or grade_item.course_id != self.course_id or not grade_item.assignment_id:
            raise ValueError("Assignment tidak ditemukan")
        
        assignment = Assignment.query.get(grade_item.assignment_id)
        entries = GradeEntry.query.filter_by(grade_item_id=grade_item_id).all()
        
        if not entries:
            return self._empty_assignment_stats(assignment, grade_item)
        
        scores = [e.score for e in entries if e.score is not None]
        
        if not scores:
            return self._empty_assignment_stats(assignment, grade_item)
        
        avg_score = sum(scores) / len(scores)
        max_score = max(scores)
        min_score = min(scores)
        
        graded_count = len([e for e in entries if e.score is not None])
        pending_count = len(entries) - graded_count
        
        # Score distribution
        score_ranges = [(0, 59), (60, 69), (70, 79), (80, 89), (90, 100)]
        dist_labels = ['< 60', '60-69', '70-79', '80-89', '90-100']
        dist_data = [len([s for s in scores if low <= s <= high]) for low, high in score_ranges]
        
        return {
            'assignment': {'id': assignment.id, 'name': assignment.name} if assignment else None,
            'grade_item': grade_item.to_dict(),
            'total_submissions': len(entries),
            'average_score': round(avg_score, 2),
            'max_score': round(max_score, 2),
            'min_score': round(min_score, 2),
            'graded_count': graded_count,
            'pending_count': pending_count,
            'score_distribution': {
                'labels': dist_labels,
                'data': dist_data
            }
        }
    
    def _empty_assignment_stats(self, assignment, grade_item) -> Dict[str, Any]:
        """Return empty stats for assignment with no submissions"""
        return {
            'assignment': {'id': assignment.id, 'name': assignment.name} if assignment else None,
            'grade_item': grade_item.to_dict(),
            'total_submissions': 0,
            'average_score': 0,
            'max_score': 0,
            'min_score': 0,
            'graded_count': 0,
            'pending_count': 0,
            'score_distribution': {'labels': [], 'data': []}
        }
    
    def get_rasch_summary(self) -> List[Dict[str, Any]]:
        """Ringkasan Rasch analyses untuk course ini"""
        analyses = RaschAnalysis.query.filter_by(course_id=self.course_id)\
            .order_by(RaschAnalysis.created_at.desc()).all()
        
        result = []
        for analysis in analyses:
            quiz = Quiz.query.get(analysis.quiz_id) if analysis.quiz_id else None
            person_count = RaschPersonMeasure.query.filter_by(rasch_analysis_id=analysis.id).count()
            item_count = RaschItemMeasure.query.filter_by(rasch_analysis_id=analysis.id).count()
            
            result.append({
                'analysis_id': analysis.id,
                'quiz_id': analysis.quiz_id,
                'quiz_name': quiz.name if quiz else 'N/A',
                'status': analysis.status.value,
                'person_reliability': float(analysis.person_reliability) if analysis.person_reliability else None,
                'item_reliability': float(analysis.item_reliability) if analysis.item_reliability else None,
                'person_count': person_count,
                'item_count': item_count,
                'created_at': analysis.created_at.strftime('%Y-%m-%d %H:%M'),
                'reliability_label': self._get_reliability_label(analysis.person_reliability)
            })
        
        return result
    
    def _get_reliability_label(self, reliability: Optional[float]) -> str:
        """Label reliabilitas untuk guru"""
        if reliability is None:
            return 'Belum dianalisis'
        elif reliability < 0.5:
            return '⚠️ Rendah'
        elif reliability < 0.7:
            return '🟡 Cukup'
        else:
            return '✅ Tinggi'
    
    def get_recent_evaluations(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Evaluasi terbaru"""
        quizzes = Quiz.query.filter_by(course_id=self.course_id)\
            .order_by(Quiz.updated_at.desc()).limit(limit).all()
        
        result = []
        for q in quizzes:
            submission_count = QuizSubmission.query.filter_by(quiz_id=q.id).count()
            result.append({
                'id': q.id,
                'type': 'quiz',
                'name': q.name,
                'status': q.status.value,
                'submissions': submission_count,
                'updated_at': q.updated_at.strftime('%Y-%m-%d %H:%M')
            })
        
        return result
    
    def get_comparison_chart_data(self) -> Dict[str, Any]:
        """Data untuk chart perbandingan kelas"""
        quizzes = Quiz.query.filter_by(course_id=self.course_id).all()
        
        labels = [q.name[:20] + '...' if len(q.name) > 20 else q.name for q in quizzes[:10]]
        avg_scores = []
        submission_counts = []
        
        for q in quizzes[:10]:
            submissions = QuizSubmission.query.filter_by(quiz_id=q.id).all()
            scores = [s.score for s in submissions if s.score is not None]
            avg_scores.append(round(sum(scores) / len(scores), 2) if scores else 0)
            submission_counts.append(len(submissions))
        
        return {
            'labels': labels,
            'datasets': [
                {
                    'label': 'Rata-rata Nilai',
                    'data': avg_scores,
                    'backgroundColor': 'rgba(99, 102, 241, 0.6)',
                    'borderColor': 'rgba(99, 102, 241, 1)',
                    'borderWidth': 2,
                    'yAxisID': 'y'
                },
                {
                    'label': 'Jumlah Pengerjaan',
                    'data': submission_counts,
                    'backgroundColor': 'rgba(168, 85, 247, 0.6)',
                    'borderColor': 'rgba(168, 85, 247, 1)',
                    'borderWidth': 2,
                    'yAxisID': 'y1'
                }
            ]
        }
    
    def _get_chart_colors(self, count: int, base_color: str = 'primary') -> List[str]:
        """Generate warna untuk chart"""
        primary_colors = [
            'rgba(99, 102, 241, 0.8)',
            'rgba(129, 140, 248, 0.8)',
            'rgba(167, 139, 250, 0.8)',
            'rgba(192, 132, 252, 0.8)',
            'rgba(216, 180, 254, 0.8)',
            'rgba(232, 221, 255, 0.8)',
            'rgba(79, 70, 229, 0.8)',
            'rgba(67, 56, 202, 0.8)',
            'rgba(55, 48, 163, 0.8)',
            'rgba(49, 46, 129, 0.8)'
        ]
        return primary_colors[:count]
    
    def get_item_analysis_chart(self, quiz_id: int) -> Dict[str, Any]:
        """Data untuk chart item analysis (difficulty vs discrimination)"""
        quiz = Quiz.query.get(quiz_id)
        if not quiz:
            return {'labels': [], 'datasets': []}
        
        questions = quiz.questions.order_by(Question.order).all()
        
        labels = []
        difficulty_data = []
        discrimination_data = []
        
        for i, q in enumerate(questions):
            labels.append(f"Q{i+1}")
            
            total_answers = Answer.query.filter_by(question_id=q.id).count()
            correct_answers = 0
            
            if q.question_type in [QuestionType.MULTIPLE_CHOICE, QuestionType.TRUE_FALSE, QuestionType.DROPDOWN]:
                correct_answers = db.session.query(func.count(Answer.id)).join(
                    Option, Answer.selected_option_id == Option.id
                ).filter(
                    Answer.question_id == q.id,
                    Option.is_correct == True
                ).scalar() or 0
            
            difficulty = (correct_answers / total_answers * 100) if total_answers > 0 else 50
            discrimination = 0.5  # Simplified placeholder
            
            difficulty_data.append(round(100 - difficulty, 2))
            discrimination_data.append(discrimination)
        
        return {
            'labels': labels,
            'datasets': [{
                'label': 'Soal',
                'data': [
                    {'x': difficulty_data[i], 'y': discrimination_data[i]}
                    for i in range(len(questions))
                ],
                'backgroundColor': 'rgba(99, 102, 241, 0.6)',
                'borderColor': 'rgba(99, 102, 241, 1)',
                'pointRadius': 6,
                'pointHoverRadius': 8
            }]
        }
    
    def get_time_series_submissions(self, quiz_id: int) -> Dict[str, Any]:
        """Data untuk chart time series submissions"""
        quiz = Quiz.query.get(quiz_id)
        if not quiz:
            return {'labels': [], 'datasets': []}
        
        submissions = QuizSubmission.query.filter_by(quiz_id=quiz_id)\
            .order_by(QuizSubmission.submitted_at).all()
        
        if not submissions:
            return {'labels': [], 'datasets': []}
        
        daily_counts = defaultdict(int)
        for sub in submissions:
            date_str = sub.submitted_at.strftime('%Y-%m-%d')
            daily_counts[date_str] += 1
        
        labels = sorted(daily_counts.keys())
        data = [daily_counts[date] for date in labels]
        
        return {
            'labels': labels,
            'datasets': [{
                'label': 'Submissions per Hari',
                'data': data,
                'backgroundColor': 'rgba(99, 102, 241, 0.2)',
                'borderColor': 'rgba(99, 102, 241, 1)',
                'borderWidth': 2,
                'fill': True,
                'tension': 0.4
            }]
        }
    
    def get_wright_map_data(self, analysis_id: int) -> Dict[str, Any]:
        """Data untuk Wright Map visualization"""
        analysis = RaschAnalysis.query.get(analysis_id)
        if not analysis:
            return {'person_measures': [], 'item_measures': [], 'scale_range': [0, 100]}
        
        # Get person measures
        person_measures = RaschPersonMeasure.query.filter_by(rasch_analysis_id=analysis_id).all()
        item_measures = RaschItemMeasure.query.filter_by(rasch_analysis_id=analysis_id).all()
        
        # Format for chart
        persons_data = [
            {
                'student_name': pm.student.name,
                'ability': float(pm.measure) if pm.measure else 0,
                'error': float(pm.error) if pm.error else 0,
                'percentile': pm.percentile_rank
            }
            for pm in person_measures[:50]  # Limit untuk performa
        ]
        
        items_data = [
            {
                'item_text': im.item_text[:30] + '...' if len(im.item_text) > 30 else im.item_text,
                'difficulty': float(im.measure) if im.measure else 0,
                'error': float(im.error) if im.error else 0
            }
            for im in item_measures
        ]
        
        # Calculate scale range
        all_measures = [float(pm.measure) for pm in person_measures if pm.measure] + \
                      [float(im.measure) for im in item_measures if im.measure]
        
        if all_measures:
            min_scale = min(all_measures) - 1
            max_scale = max(all_measures) + 1
        else:
            min_scale, max_scale = 0, 100
        
        return {
            'person_measures': persons_data,
            'item_measures': items_data,
            'scale_range': [min_scale, max_scale],
            'analysis_name': analysis.quiz.name if analysis.quiz else 'N/A'
        }
    
    def get_student_ability_data(self) -> List[Dict[str, Any]]:
        """Data kemampuan siswa untuk tabel"""
        # Get latest Rasch analysis
        latest_analysis = RaschAnalysis.query.filter_by(course_id=self.course_id, status='completed')\
            .order_by(RaschAnalysis.created_at.desc()).first()
        
        if not latest_analysis:
            return []
        
        person_measures = RaschPersonMeasure.query.filter_by(rasch_analysis_id=latest_analysis.id)\
            .join(User).all()
        
        result = []
        for pm in person_measures:
            result.append({
                'student_id': pm.student_id,
                'student_name': pm.student.name,
                'ability_measure': float(pm.measure) if pm.measure else 0,
                'error': float(pm.error) if pm.error else 0,
                'percentile_rank': pm.percentile_rank,
                'ability_label': self._get_ability_label(pm.measure),
                'recommendation': self._get_student_recommendation(pm.measure, pm.percentile_rank)
            })
        
        # Sort by ability descending
        result.sort(key=lambda x: x['ability_measure'], reverse=True)
        
        # Add rank
        for i, item in enumerate(result):
            item['rank'] = i + 1
        
        return result
    
    def _get_ability_label(self, measure: Optional[float]) -> str:
        """Label kemampuan untuk guru"""
        if measure is None:
            return 'Belum diukur'
        elif measure > 70:
            return '🌟 Sangat Tinggi'
        elif measure > 55:
            return '✅ Tinggi'
        elif measure > 40:
            return '🟡 Sedang'
        elif measure > 25:
            return '⚠️ Rendah'
        else:
            return '🔴 Sangat Rendah'
    
    def _get_student_recommendation(self, measure: Optional[float], percentile: Optional[float]) -> str:
        """Rekomendasi tindak lanjut untuk siswa"""
        if measure is None or percentile is None:
            return 'Perlu analisis'
        elif percentile >= 80:
            return 'Berikan pengayaan'
        elif percentile >= 50:
            return 'Pertahankan'
        elif percentile >= 30:
            return 'Perlu latihan tambahan'
        else:
            return 'Perlu remedial'
