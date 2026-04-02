"""
Rasch Threshold Checker

Mekanisme untuk auto-trigger Rasch analysis saat threshold terpenuhi.
Dipanggil setiap kali ada siswa submit quiz.
"""

import logging
from datetime import datetime
from typing import Optional, Tuple

from app import db
from app.models.rasch import (
    RaschAnalysis,
    RaschAnalysisStatus,
    RaschAnalysisType,
    RaschThresholdLog,
    ThresholdCheckType,
    ThresholdAction,
)
from app.models.quiz import Quiz, QuizSubmission

logger = logging.getLogger(__name__)


def check_and_trigger_rasch_analysis(
    quiz_id: int,
    submission_id: Optional[int] = None,
    check_type: str = 'auto'
) -> Tuple[bool, str]:
    """
    Check threshold dan trigger Rasch analysis jika terpenuhi.
    
    Dipanggil otomatis saat ada siswa submit quiz.
    
    Args:
        quiz_id: ID quiz yang di-submit
        submission_id: ID submission (optional, untuk logging)
        check_type: 'auto' atau 'manual'
        
    Returns:
        Tuple[bool, str]: (threshold_met, message)
    """
    from app.services.rasch_threshold_service import RaschThresholdService
    
    service = RaschThresholdService()
    return service.check_and_trigger(quiz_id, submission_id, check_type)


class RaschThresholdService:
    """
    Service untuk threshold checking dan auto-trigger Rasch analysis.
    """
    
    def __init__(self):
        self.default_min_persons = 30  # Default threshold
    
    def check_and_trigger(
        self,
        quiz_id: int,
        submission_id: Optional[int] = None,
        check_type: str = 'auto'
    ) -> Tuple[bool, str]:
        """
        Check threshold dan trigger analysis.
        
        Returns:
            Tuple[bool, str]: (threshold_met, message)
        """
        try:
            # Get quiz
            quiz = Quiz.query.get(quiz_id)
            
            if not quiz:
                return False, "Quiz not found"
            
            # Check if quiz has grade_item with Rasch enabled
            from app.models.gradebook import GradeItem
            grade_item = GradeItem.query.filter_by(quiz_id=quiz_id).first()
            
            if not grade_item or not grade_item.enable_rasch_analysis:
                logger.debug(f"Quiz {quiz_id} does not have Rasch analysis enabled")
                return False, "Rasch analysis not enabled for this quiz"

            # Count submissions
            submission_count = QuizSubmission.query.filter_by(quiz_id=quiz_id).count()

            # Get or create analysis record
            analysis = self._get_or_create_analysis(quiz_id, grade_item)

            # Check if analysis should be skipped (already completed/processing/queued)
            if getattr(analysis, '_skip_trigger', False):
                # Analysis is already completed/processing - check for late submission
                if analysis.status == RaschAnalysisStatus.COMPLETED.value:
                    # Process late submission using anchor values
                    return self._process_late_submission(analysis, submission_id)
                logger.info(f"Skipping threshold check for quiz {quiz_id} - analysis already active")
                return False, "Analisis Rasch sedang berjalan atau sudah selesai"

            # Get threshold from analysis
            min_persons = analysis.min_persons or self.default_min_persons

            # Check threshold
            threshold_met = submission_count >= min_persons

            # Log threshold check
            self._log_threshold_check(
                analysis_id=analysis.id,
                check_type=check_type,
                num_submissions=submission_count,
                min_required=min_persons,
                threshold_met=threshold_met
            )

            if threshold_met:
                # Trigger analysis
                return self._trigger_analysis(analysis, check_type)
            else:
                # Update status to waiting
                remaining = min_persons - submission_count
                analysis.status = RaschAnalysisStatus.WAITING.value
                analysis.status_message = f"Menunggu {remaining} siswa lagi untuk memulai analisis"
                analysis.progress_percentage = (submission_count / min_persons) * 100
                db.session.commit()

                logger.info(f"Threshold not met for quiz {quiz_id}: {submission_count}/{min_persons}")
                return False, f"Menunggu {remaining} siswa lagi untuk memulai analisis Rasch"

        except Exception as e:
            logger.error(f"Error in threshold check: {e}", exc_info=True)
            return False, f"Error: {str(e)}"
    
    def _get_or_create_analysis(self, quiz_id: int, grade_item) -> RaschAnalysis:
        """Get existing analysis or create new one"""
        from app.models.user import User

        # Check if analysis already exists
        existing = RaschAnalysis.query.filter_by(
            quiz_id=quiz_id,
            analysis_type=RaschAnalysisType.QUIZ.value
        ).first()

        if existing:
            # Check if analysis is already in a terminal or active state
            # If so, don't allow re-triggering
            if existing.status in [
                RaschAnalysisStatus.COMPLETED.value,
                RaschAnalysisStatus.PROCESSING.value,
                RaschAnalysisStatus.QUEUED.value,
            ]:
                logger.info(
                    f"Analysis {existing.id} for quiz {quiz_id} is in status {existing.status}, skipping trigger"
                )
                # Return a mock object with is_active flag to signal caller to skip
                existing._skip_trigger = True
                return existing
            
            logger.debug(f"Found existing analysis {existing.id} for quiz {quiz_id}")
            return existing
        
        # Create new analysis
        quiz = Quiz.query.get(quiz_id)
        
        analysis = RaschAnalysis(
            name=f"Rasch Analysis - {quiz.name}",
            course_id=quiz.course_id,
            quiz_id=quiz_id,
            analysis_type=RaschAnalysisType.QUIZ,
            status=RaschAnalysisStatus.PENDING,
            min_persons=30,  # Default
            auto_trigger=True,
            created_by=quiz.teacher_id,  # Assuming teacher_id is the creator
        )
        
        db.session.add(analysis)
        db.session.commit()
        
        # Link to grade_item
        grade_item.rasch_analysis_id = analysis.id
        db.session.commit()
        
        logger.info(f"Created new Rasch analysis {analysis.id} for quiz {quiz_id}")
        return analysis
    
    def _trigger_analysis(self, analysis: RaschAnalysis, check_type: str) -> Tuple[bool, str]:
        """Trigger Rasch analysis"""
        try:
            # Update status
            analysis.status = RaschAnalysisStatus.QUEUED.value
            analysis.status_message = "Analysis queued for processing"
            db.session.commit()
            
            # Log action
            self._log_threshold_check(
                analysis_id=analysis.id,
                check_type=check_type,
                num_submissions=analysis.num_persons or 0,
                min_required=analysis.min_persons,
                threshold_met=True,
                action_taken='queued'
            )
            
            # Trigger Celery task
            self._enqueue_analysis(analysis.id)
            
            logger.info(f"Triggered Rasch analysis {analysis.id}")
            return True, "Rasch analysis started"
            
        except Exception as e:
            logger.error(f"Error triggering analysis: {e}")
            analysis.status = RaschAnalysisStatus.FAILED.value
            analysis.error_message = str(e)
            db.session.commit()
            return False, f"Error triggering analysis: {str(e)}"
    
    def _enqueue_analysis(self, analysis_id: int):
        """Enqueue analysis to Celery worker"""
        try:
            # Try to use Celery
            from app.workers.rasch_worker import rasch_analysis
            
            # Check if Celery is available
            if rasch_analysis:
                rasch_analysis.delay(analysis_id=analysis_id)
                logger.info(f"Enqueued Rasch analysis {analysis_id} to Celery")
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
            logger.info(f"Sync Rasch analysis {analysis_id} completed")
        except Exception as e:
            logger.error(f"Sync analysis failed: {e}")

    def _process_late_submission(self, analysis: RaschAnalysis, submission_id: Optional[int]) -> Tuple[bool, str]:
        """
        Process late submission using anchor values.
        
        Args:
            analysis: Completed Rasch analysis record
            submission_id: ID of the new submission
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        if not submission_id:
            return False, "Submission ID required for late processing"
        
        try:
            from app.services.rasch_anchor_service import RaschAnchorService
            
            service = RaschAnchorService(analysis_id=analysis.id)
            result = service.calculate_ability_for_submission(submission_id)
            
            if result and result.get('success'):
                theta = result.get('theta', 0)
                ability_level = result.get('ability_level', 'unknown')
                logger.info(
                    f"Late submission {submission_id} processed: theta={theta:.3f}, level={ability_level}"
                )
                return True, f"Nilai ability berhasil dihitung: θ={theta:.3f} ({ability_level})"
            else:
                logger.warning(f"Failed to process late submission {submission_id}")
                return False, "Gagal menghitung nilai ability untuk submission ini"
                
        except Exception as e:
            logger.error(f"Error processing late submission: {e}", exc_info=True)
            return False, f"Error: {str(e)}"

    def _log_threshold_check(
        self,
        analysis_id: int,
        check_type: str,
        num_submissions: int,
        min_required: int,
        threshold_met: bool,
        action_taken: Optional[str] = None,
        reason: Optional[str] = None
    ):
        """Log threshold check to database"""
        try:
            log = RaschThresholdLog(
                rasch_analysis_id=analysis_id,
                check_type=check_type,
                num_submissions=num_submissions,
                min_required=min_required,
                threshold_met=threshold_met,
                action_taken=action_taken,
                reason=reason,
            )
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error logging threshold check: {e}")
            db.session.rollback()
    
    def manual_trigger(self, quiz_id: int, min_persons: Optional[int] = None) -> Tuple[bool, str]:
        """
        Manual trigger Rasch analysis (bypass threshold).
        
        Args:
            quiz_id: ID quiz
            min_persons: Override minimum persons threshold
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Get quiz
            quiz = Quiz.query.get(quiz_id)
            
            if not quiz:
                return False, "Quiz not found"
            
            # Get grade_item
            from app.models.gradebook import GradeItem
            grade_item = GradeItem.query.filter_by(quiz_id=quiz_id).first()
            
            if not grade_item or not grade_item.enable_rasch_analysis:
                return False, "Rasch analysis not enabled for this quiz"
            
            # Get or create analysis
            analysis = self._get_or_create_analysis(quiz_id, grade_item)
            
            # Override min_persons if specified
            if min_persons:
                analysis.min_persons = min_persons
            
            # Count current submissions
            submission_count = QuizSubmission.query.filter_by(quiz_id=quiz_id).count()
            analysis.num_persons = submission_count
            
            # Trigger analysis regardless of threshold
            logger.info(f"Manual trigger for Rasch analysis {analysis.id} with {submission_count} submissions")
            
            return self._trigger_analysis(analysis, check_type='manual')
            
        except Exception as e:
            logger.error(f"Error in manual trigger: {e}", exc_info=True)
            return False, f"Error: {str(e)}"
