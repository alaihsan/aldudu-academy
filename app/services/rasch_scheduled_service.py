"""
Rasch Scheduled Batch Service

Service untuk menjalankan analisis Rasch secara terjadwal (misal: tengah malam)
setelah threshold tercapai. Ini menangani kasus dimana banyak siswa submit
di luar jam kerja atau analisis perlu diulang dengan data terbaru.

Usage:
    - Dipanggil via cron job atau scheduled task
    - Jalankan setiap malam untuk memproses quiz yang mencapai threshold
    - Optional: Re-run analisis yang sudah ada untuk include late submissions
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from app import db
from app.models.rasch import (
    RaschAnalysis,
    RaschAnalysisStatus,
    RaschAnalysisType,
    RaschPersonMeasure,
)
from app.models.quiz import Quiz, QuizSubmission
from app.models.gradebook import GradeItem

logger = logging.getLogger(__name__)


class RaschScheduledBatchService:
    """
    Service untuk scheduled/periodic Rasch analysis.
    
    Fitur:
    - Process quizzes yang mencapai threshold hari ini
    - Re-run analisis yang sudah ada untuk include late submissions
    - Skip quizzes yang sudah dianalisis dengan data lengkap
    """
    
    def __init__(self):
        self.default_min_persons = 30
        self.late_submission_threshold = 5  # Min late submissions untuk re-run
        
    def run_nightly_batch(self, course_id: Optional[int] = None) -> dict:
        """
        Run nightly batch processing untuk semua quiz yang eligible.
        
        Args:
            course_id: Optional - filter untuk course tertentu
            
        Returns:
            dict: Summary hasil processing
        """
        logger.info("Starting nightly Rasch batch processing...")
        
        results = {
            'started_at': datetime.utcnow().isoformat(),
            'new_analyses': 0,
            're_analyses': 0,
            'skipped': 0,
            'failed': 0,
            'details': [],
        }
        
        try:
            # Get all quizzes with Rasch enabled
            query = GradeItem.query.filter_by(enable_rasch_analysis=True)
            
            if course_id:
                # Filter by course via quiz relationship
                grade_items = query.all()
                grade_items = [gi for gi in grade_items if gi.quiz and gi.quiz.course_id == course_id]
            else:
                grade_items = query.all()
            
            logger.info(f"Found {len(grade_items)} quizzes with Rasch enabled")
            
            for grade_item in grade_items:
                if not grade_item.quiz:
                    continue
                
                result = self._process_quiz(grade_item)
                results['details'].append(result)
                
                if result['action'] == 'new_analysis':
                    results['new_analyses'] += 1
                elif result['action'] == 're_analysis':
                    results['re_analyses'] += 1
                elif result['action'] == 'skipped':
                    results['skipped'] += 1
                elif result['action'] == 'failed':
                    results['failed'] += 1
            
            results['completed_at'] = datetime.utcnow().isoformat()
            results['success'] = True
            
            logger.info(
                f"Nightly batch completed: {results['new_analyses']} new, "
                f"{results['re_analyses']} re-analyses, {results['skipped']} skipped, "
                f"{results['failed']} failed"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Nightly batch failed: {e}", exc_info=True)
            results['success'] = False
            results['error'] = str(e)
            return results
    
    def _process_quiz(self, grade_item: GradeItem) -> dict:
        """
        Process single quiz for batch analysis.
        
        Args:
            grade_item: GradeItem record
            
        Returns:
            dict: Processing result
        """
        quiz = grade_item.quiz
        
        if not quiz:
            return {
                'quiz_id': grade_item.quiz_id,
                'action': 'skipped',
                'reason': 'Quiz not found',
            }
        
        # Count submissions
        submission_count = QuizSubmission.query.filter_by(quiz_id=quiz.id).count()
        
        if submission_count == 0:
            return {
                'quiz_id': quiz.id,
                'action': 'skipped',
                'reason': 'No submissions',
            }
        
        # Check existing analysis
        existing_analysis = None
        if grade_item.rasch_analysis_id:
            existing_analysis = RaschAnalysis.query.get(grade_item.rasch_analysis_id)
        
        # Determine action
        if existing_analysis and existing_analysis.status == RaschAnalysisStatus.COMPLETED.value:
            # Check if we should re-run
            return self._handle_completed_analysis(grade_item, existing_analysis, submission_count)
        elif existing_analysis and existing_analysis.status in [
            RaschAnalysisStatus.PROCESSING.value,
            RaschAnalysisStatus.QUEUED.value,
        ]:
            return {
                'quiz_id': quiz.id,
                'action': 'skipped',
                'reason': f'Analysis already {existing_analysis.status}',
            }
        else:
            # New analysis
            return self._handle_new_analysis(grade_item, submission_count)
    
    def _handle_completed_analysis(
        self, 
        grade_item: GradeItem, 
        analysis: RaschAnalysis,
        submission_count: int
    ) -> dict:
        """
        Handle quiz yang sudah memiliki analisis completed.
        
        Decide apakah perlu re-run berdasarkan jumlah late submissions.
        """
        # Count how many students already have measures
        existing_measures = RaschPersonMeasure.query.filter_by(
            rasch_analysis_id=analysis.id
        ).count()
        
        # Calculate late submissions
        late_count = submission_count - existing_measures
        
        if late_count < self.late_submission_threshold:
            logger.info(
                f"Quiz {grade_item.quiz_id}: Skipping re-analysis "
                f"(only {late_count} late submissions, threshold={self.late_submission_threshold})"
            )
            return {
                'quiz_id': grade_item.quiz_id,
                'quiz_name': grade_item.quiz.name,
                'action': 'skipped',
                'reason': f'Only {late_count} late submissions (threshold={self.late_submission_threshold})',
                'submission_count': submission_count,
                'existing_measures': existing_measures,
                'late_count': late_count,
            }
        
        # Check if significant portion of new submissions
        late_percentage = (late_count / submission_count * 100) if submission_count > 0 else 0
        
        if late_percentage < 10:  # Less than 10% new submissions
            logger.info(
                f"Quiz {grade_item.quiz_id}: Skipping re-analysis "
                f"(late submissions only {late_percentage}%)"
            )
            return {
                'quiz_id': grade_item.quiz_id,
                'quiz_name': grade_item.quiz.name,
                'action': 'skipped',
                'reason': f'Late submissions only {late_percentage:.1f}%',
                'submission_count': submission_count,
                'existing_measures': existing_measures,
                'late_count': late_count,
            }
        
        # Re-run analysis
        logger.info(
            f"Quiz {grade_item.quiz_id}: Re-running analysis with {late_count} late submissions"
        )
        
        try:
            # Delete old person and item measures (keep analysis record)
            RaschPersonMeasure.query.filter_by(rasch_analysis_id=analysis.id).delete()
            
            from app.models.rasch import RaschItemMeasure
            RaschItemMeasure.query.filter_by(rasch_analysis_id=analysis.id).delete()
            
            # Reset analysis status
            analysis.status = RaschAnalysisStatus.PENDING.value
            analysis.num_persons = submission_count
            analysis.status_message = f"Re-running analysis with {late_count} new submissions"
            db.session.commit()
            
            # Trigger analysis
            self._trigger_analysis(analysis.id)
            
            return {
                'quiz_id': grade_item.quiz_id,
                'quiz_name': grade_item.quiz.name,
                'action': 're_analysis',
                'reason': f'{late_count} late submissions ({late_percentage:.1f}%)',
                'submission_count': submission_count,
                'existing_measures': existing_measures,
                'late_count': late_count,
                'analysis_id': analysis.id,
            }
            
        except Exception as e:
            logger.error(f"Error re-running analysis for quiz {grade_item.quiz_id}: {e}")
            db.session.rollback()
            return {
                'quiz_id': grade_item.quiz_id,
                'action': 'failed',
                'reason': str(e),
            }
    
    def _handle_new_analysis(self, grade_item: GradeItem, submission_count: int) -> dict:
        """
        Handle quiz yang belum memiliki analisis.
        """
        min_persons = grade_item.rasch_analysis.min_persons if grade_item.rasch_analysis else self.default_min_persons
        
        if submission_count < min_persons:
            remaining = min_persons - submission_count
            logger.info(
                f"Quiz {grade_item.quiz_id}: Skipping (need {remaining} more submissions)"
            )
            return {
                'quiz_id': grade_item.quiz_id,
                'quiz_name': grade_item.quiz.name if grade_item.quiz else None,
                'action': 'skipped',
                'reason': f'Need {remaining} more submissions to reach threshold',
                'submission_count': submission_count,
                'min_required': min_persons,
            }
        
        # Create and trigger new analysis
        logger.info(
            f"Quiz {grade_item.quiz_id}: Creating new analysis with {submission_count} submissions"
        )
        
        try:
            from app.models.rasch import RaschAnalysis, RaschAnalysisType, RaschAnalysisStatus
            from app.models.user import User
            
            # Create analysis record
            quiz = grade_item.quiz
            analysis = RaschAnalysis(
                name=f"Rasch Analysis - {quiz.name}",
                course_id=quiz.course_id,
                quiz_id=quiz.id,
                analysis_type=RaschAnalysisType.QUIZ,
                status=RaschAnalysisStatus.PENDING,
                min_persons=min_persons,
                auto_trigger=True,
                num_persons=submission_count,
                created_by=quiz.teacher_id,
            )
            
            db.session.add(analysis)
            db.session.commit()
            
            # Link to grade_item
            grade_item.rasch_analysis_id = analysis.id
            db.session.commit()
            
            # Trigger analysis
            self._trigger_analysis(analysis.id)
            
            return {
                'quiz_id': grade_item.quiz_id,
                'quiz_name': quiz.name,
                'action': 'new_analysis',
                'reason': f'Threshold met ({submission_count} >= {min_persons})',
                'submission_count': submission_count,
                'min_required': min_persons,
                'analysis_id': analysis.id,
            }
            
        except Exception as e:
            logger.error(f"Error creating new analysis for quiz {grade_item.quiz_id}: {e}")
            db.session.rollback()
            return {
                'quiz_id': grade_item.quiz_id,
                'action': 'failed',
                'reason': str(e),
            }
    
    def _trigger_analysis(self, analysis_id: int):
        """Trigger Celery worker untuk analisis"""
        try:
            from app.workers.rasch_worker import rasch_analysis
            
            if rasch_analysis:
                rasch_analysis.delay(analysis_id=analysis_id)
                logger.info(f"Enqueued analysis {analysis_id} to Celery")
                return
        except Exception as e:
            logger.warning(f"Celery not available, running sync: {e}")
        
        # Fallback: run synchronously
        self._run_analysis_sync(analysis_id)
    
    def _run_analysis_sync(self, analysis_id: int):
        """Run analysis synchronously (fallback)"""
        from app.services.rasch_analysis_service import RaschAnalysisService
        
        try:
            service = RaschAnalysisService(analysis_id=analysis_id)
            service.run_analysis()
            logger.info(f"Sync analysis {analysis_id} completed")
        except Exception as e:
            logger.error(f"Sync analysis failed: {e}")
            raise
    
    def process_late_submissions_batch(self, course_id: Optional[int] = None) -> dict:
        """
        Process late submissions untuk semua quiz yang sudah dianalisis.
        
        Menggunakan anchor values untuk menghitung ability siswa baru
        tanpa perlu re-run analisis penuh.
        
        Args:
            course_id: Optional - filter untuk course tertentu
            
        Returns:
            dict: Summary hasil processing
        """
        logger.info("Starting late submissions batch processing...")
        
        results = {
            'started_at': datetime.utcnow().isoformat(),
            'quizzes_processed': 0,
            'students_processed': 0,
            'failed': 0,
            'details': [],
        }
        
        try:
            # Get all completed analyses
            query = RaschAnalysis.query.filter_by(
                status=RaschAnalysisStatus.COMPLETED.value,
                analysis_type=RaschAnalysisType.QUIZ.value,
            )
            
            if course_id:
                query = query.filter_by(course_id=course_id)
            
            analyses = query.all()
            
            for analysis in analyses:
                if not analysis.quiz_id:
                    continue
                
                result = self._process_late_for_quiz(analysis)
                results['details'].append(result)
                
                if result.get('success'):
                    results['quizzes_processed'] += 1
                    results['students_processed'] += result.get('processed', 0)
                else:
                    results['failed'] += 1
            
            results['completed_at'] = datetime.utcnow().isoformat()
            results['success'] = True
            
            logger.info(
                f"Late submissions batch completed: {results['quizzes_processed']} quizzes, "
                f"{results['students_processed']} students processed"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Late submissions batch failed: {e}", exc_info=True)
            results['success'] = False
            results['error'] = str(e)
            return results
    
    def _process_late_for_quiz(self, analysis: RaschAnalysis) -> dict:
        """
        Process late submissions untuk quiz tertentu.
        """
        from app.services.rasch_anchor_service import process_late_submissions
        
        quiz_id = analysis.quiz_id
        
        result = process_late_submissions(quiz_id)
        
        return {
            'quiz_id': quiz_id,
            'quiz_name': analysis.quiz.name if analysis.quiz else None,
            'analysis_id': analysis.id,
            'success': result.get('success', False),
            'processed': result.get('processed', 0),
            'failed': result.get('failed', 0),
            'total_late': result.get('total_late', 0),
        }


# Convenience functions untuk cron/scheduler
def run_nightly_analysis(course_id: Optional[int] = None) -> dict:
    """
    Run nightly batch analysis.
    
    Dipanggil dari cron job atau scheduled task.
    
    Usage (cron):
        0 2 * * * cd /path/to/app && python -c "from app.services.rasch_scheduled_service import run_nightly_analysis; run_nightly_analysis()"
    """
    service = RaschScheduledBatchService()
    return service.run_nightly_batch(course_id)


def run_late_submissions_processing(course_id: Optional[int] = None) -> dict:
    """
    Process late submissions using anchor values.
    
    Dipanggil lebih sering (misal setiap jam) untuk update siswa baru.
    
    Usage (cron):
        0 * * * * cd /path/to/app && python -c "from app.services.rasch_scheduled_service import run_late_submissions_processing; run_late_submissions_processing()"
    """
    service = RaschScheduledBatchService()
    return service.process_late_submissions_batch(course_id)
