"""
Rasch Anchor Values Service

Menghitung ability untuk siswa yang submit terlambat (setelah analisis berjalan)
menggunakan Anchor Items (nilai difficulty yang sudah dikalibrasi).

Pendekatan:
- Gunakan item difficulties dari analisis terakhir sebagai anchor values
- Hitung ability siswa baru menggunakan fixed item difficulties
- Tidak perlu menjalankan ulang JMLE penuh

Formula:
    theta_new = ln(P / (1-P)) + mean(delta_anchored)
    
dimana P adalah proportion correct siswa baru terhadap soal yang sudah dikalibrasi.
"""

import math
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from app import db
from app.models.rasch import (
    RaschAnalysis,
    RaschAnalysisStatus,
    RaschPersonMeasure,
    RaschItemMeasure,
    AbilityLevel,
    FitStatus,
    FitCategory,
)
from app.models.quiz import QuizSubmission, Answer, Question
from app.models.user import User

logger = logging.getLogger(__name__)


class RaschAnchorService:
    """
    Service untuk menghitung ability siswa baru menggunakan anchor values.
    
    Usage:
        service = RaschAnchorService(analysis_id=1)
        result = service.calculate_ability_for_submission(submission_id=123)
    """
    
    def __init__(self, analysis_id: int):
        self.analysis_id = analysis_id
        self.analysis: Optional[RaschAnalysis] = None
        
        # Anchor values (item difficulties dari analisis sebelumnya)
        self.anchor_difficulties: Dict[int, float] = {}
        
        # Data untuk siswa baru
        self.student_id: Optional[int] = None
        self.responses: Dict[int, int] = {}  # question_id -> 1/0
        
    def load_anchor_values(self) -> bool:
        """
        Load anchor values (item difficulties) dari analisis yang sudah ada.
        
        Returns:
            bool: True jika anchor values berhasil dimuat
        """
        try:
            self.analysis = RaschAnalysis.query.get(self.analysis_id)
            
            if not self.analysis:
                logger.error(f"Analysis {self.analysis_id} not found")
                return False
            
            # Check if analysis is completed
            if self.analysis.status != RaschAnalysisStatus.COMPLETED.value:
                logger.error(f"Analysis {self.analysis_id} is not completed (status: {self.analysis.status})")
                return False
            
            # Load item measures as anchor values
            item_measures = RaschItemMeasure.query.filter_by(
                rasch_analysis_id=self.analysis_id
            ).all()
            
            if not item_measures:
                logger.error(f"No item measures found for analysis {self.analysis_id}")
                return False
            
            for item in item_measures:
                if item.delta is not None:
                    self.anchor_difficulties[item.question_id] = item.delta
            
            logger.info(f"Loaded {len(self.anchor_difficulties)} anchor values from analysis {self.analysis_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading anchor values: {e}", exc_info=True)
            return False
    
    def load_student_responses(self, submission_id: int) -> bool:
        """
        Load responses untuk siswa baru dari submission.
        
        Args:
            submission_id: ID quiz submission siswa
            
        Returns:
            bool: True jika responses berhasil dimuat
        """
        try:
            submission = QuizSubmission.query.get(submission_id)
            
            if not submission:
                logger.error(f"Submission {submission_id} not found")
                return False
            
            self.student_id = submission.user_id
            
            # Get all answers for this submission
            answers = Answer.query.filter_by(submission_id=submission_id).all()
            
            for answer in answers:
                question_id = answer.question_id
                # Check if this question has anchor value
                if question_id in self.anchor_difficulties:
                    # Determine if correct (1) or incorrect (0)
                    is_correct = self._is_answer_correct(answer)
                    self.responses[question_id] = 1 if is_correct else 0
            
            if not self.responses:
                logger.warning(f"No matching responses found for submission {submission_id}")
                return False
            
            logger.info(f"Loaded {len(self.responses)} responses for student {self.student_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading student responses: {e}", exc_info=True)
            return False
    
    def _is_answer_correct(self, answer: Answer) -> bool:
        """Check apakah jawaban benar"""
        question = answer.question
        
        if question.question_type in ['multiple_choice', 'true_false', 'dropdown']:
            if answer.selected_option_id:
                from app.models.quiz import Option
                option = Option.query.get(answer.selected_option_id)
                return option.is_correct if option else False
        elif question.question_type == 'checkbox':
            return answer.manual_score > 0 if answer.manual_score else False
        elif question.question_type in ['long_text', 'upload']:
            return answer.manual_score > 0 if answer.manual_score else False
        
        return False
    
    def calculate_ability(self) -> Optional[float]:
        """
        Calculate ability untuk siswa baru menggunakan anchor values.
        
        Menggunakan iterative procedure untuk menemukan theta yang memaksimalkan
        likelihood diberikan fixed item difficulties.
        
        Returns:
            float: Estimated ability (theta), atau None jika gagal
        """
        if not self.responses:
            return None
        
        # Calculate raw score
        raw_score = sum(self.responses.values())
        total_items = len(self.responses)
        
        # Handle extreme scores
        if raw_score == 0:
            # Score 0: extrapolate low
            logger.info(f"Student {self.student_id} has extreme low score (0/{total_items})")
            return self._extrapolate_extreme_low()
        elif raw_score == total_items:
            # Perfect score: extrapolate high
            logger.info(f"Student {self.student_id} has perfect score ({total_items}/{total_items})")
            return self._extrapolate_extreme_high()
        
        # Initial estimate using simple logit
        p = raw_score / total_items
        theta = math.log(p / (1 - p)) if 0 < p < 1 else 0
        
        # Iterative refinement using Newton-Raphson
        for _ in range(20):  # Max 20 iterations
            sum_expected = 0
            sum_variance = 0
            sum_observed = raw_score
            
            for question_id, response in self.responses.items():
                delta = self.anchor_difficulties.get(question_id)
                if delta is None:
                    continue
                
                p_correct = self._probability(theta, delta)
                sum_expected += p_correct
                sum_variance += p_correct * (1 - p_correct)
            
            # Update theta
            if sum_variance > 0.0001:
                theta_new = theta + (sum_observed - sum_expected) / sum_variance
                
                # Check convergence
                if abs(theta_new - theta) < 0.001:
                    theta = theta_new
                    break
                
                theta = theta_new
            else:
                break
        
        logger.info(f"Calculated ability theta={theta:.3f} for student {self.student_id}")
        return theta
    
    def _extrapolate_extreme_high(self) -> float:
        """
        Extrapolate ability untuk siswa dengan perfect score.
        
        Menggunakan mean + 2*SD dari ability distribution yang ada.
        """
        # Get existing person measures from this analysis
        existing_measures = RaschPersonMeasure.query.filter_by(
            rasch_analysis_id=self.analysis_id
        ).filter(RaschPersonMeasure.theta.isnot(None)).all()
        
        if not existing_measures:
            # Fallback: use default high value
            return 4.0
        
        # Calculate mean and SD
        thetas = [m.theta for m in existing_measures]
        mean_theta = sum(thetas) / len(thetas)
        
        if len(thetas) > 1:
            variance = sum((t - mean_theta) ** 2 for t in thetas) / (len(thetas) - 1)
            std_dev = math.sqrt(variance) if variance > 0 else 1.0
        else:
            std_dev = 1.0
        
        # Extrapolate: mean + 2*SD
        extreme_theta = mean_theta + (2.0 * std_dev)
        logger.info(f"Extrapolated extreme-high theta={extreme_theta:.3f} for student {self.student_id}")
        return extreme_theta
    
    def _extrapolate_extreme_low(self) -> float:
        """
        Extrapolate ability untuk siswa dengan zero score.
        
        Menggunakan mean - 2*SD dari ability distribution yang ada.
        """
        # Get existing person measures from this analysis
        existing_measures = RaschPersonMeasure.query.filter_by(
            rasch_analysis_id=self.analysis_id
        ).filter(RaschPersonMeasure.theta.isnot(None)).all()
        
        if not existing_measures:
            # Fallback: use default low value
            return -4.0
        
        # Calculate mean and SD
        thetas = [m.theta for m in existing_measures]
        mean_theta = sum(thetas) / len(thetas)
        
        if len(thetas) > 1:
            variance = sum((t - mean_theta) ** 2 for t in thetas) / (len(thetas) - 1)
            std_dev = math.sqrt(variance) if variance > 0 else 1.0
        else:
            std_dev = 1.0
        
        # Extrapolate: mean - 2*SD
        extreme_theta = mean_theta - (2.0 * std_dev)
        logger.info(f"Extrapolated extreme-low theta={extreme_theta:.3f} for student {self.student_id}")
        return extreme_theta
    
    def _probability(self, theta: float, delta: float) -> float:
        """
        Calculate probability of correct response.
        
        Rasch formula: P(X=1) = exp(theta - delta) / (1 + exp(theta - delta))
        """
        logit = theta - delta
        
        # Avoid overflow
        if logit > 20:
            return 1.0
        elif logit < -20:
            return 0.0
        
        exp_logit = math.exp(logit)
        return exp_logit / (1 + exp_logit)
    
    def calculate_fit_statistics(self, theta: float) -> dict:
        """
        Calculate fit statistics untuk siswa baru.
        
        Args:
            theta: Ability estimate
            
        Returns:
            dict: Fit statistics
        """
        sum_squared_residual = 0
        sum_variance = 0
        sum_standardized_sq = 0
        sum_information = 0
        n_items = 0
        
        for question_id, observed in self.responses.items():
            delta = self.anchor_difficulties.get(question_id)
            if delta is None:
                continue
            
            p = self._probability(theta, delta)
            residual = observed - p
            variance = p * (1 - p)
            sum_information += variance
            
            if variance > 0.0001:
                sum_squared_residual += residual ** 2
                sum_variance += variance
                sum_standardized_sq += (residual ** 2) / variance
            
            n_items += 1
        
        # Fit statistics
        infit_mnsq = sum_squared_residual / sum_variance if sum_variance > 0 else 1.0
        outfit_mnsq = sum_standardized_sq / n_items if n_items > 0 else 1.0
        
        # Z-standardized
        infit_zstd = self._wilson_hilferty_zstd(infit_mnsq, n_items)
        outfit_zstd = self._wilson_hilferty_zstd(outfit_mnsq, n_items)
        
        # Interpretations
        fit_status = self._interpret_fit_status(outfit_mnsq)
        fit_category = self._interpret_fit_category(outfit_mnsq)
        ability_level = self._interpret_ability_level(theta)
        
        # Standard error
        theta_se = 1 / math.sqrt(sum_information) if sum_information > 0 else 1.0
        
        return {
            'theta': theta,
            'theta_se': theta_se,
            'outfit_mnsq': outfit_mnsq,
            'outfit_zstd': outfit_zstd,
            'infit_mnsq': infit_mnsq,
            'infit_zstd': infit_zstd,
            'fit_status': fit_status,
            'fit_category': fit_category,
            'ability_level': ability_level,
        }
    
    def _wilson_hilferty_zstd(self, mnsq: float, n: int) -> float:
        """Wilson-Hilferty transformation"""
        if n <= 0 or mnsq <= 0:
            return 0.0
        q = 6.0 / n
        try:
            zstd = (mnsq ** (1.0 / 3) - 1) * (3 / math.sqrt(q)) + math.sqrt(q) / 3
        except (ValueError, ZeroDivisionError):
            zstd = 0.0
        return zstd
    
    def _interpret_fit_status(self, mnsq: float) -> str:
        """Interpret fit status"""
        if 0.5 <= mnsq <= 1.5:
            return FitStatus.WELL_FITTED.value
        elif mnsq > 1.5:
            return FitStatus.UNDERFIT.value
        else:
            return FitStatus.OVERFIT.value
    
    def _interpret_fit_category(self, mnsq: float) -> str:
        """Interpret fit category"""
        if 0.8 <= mnsq <= 1.2:
            return FitCategory.EXCELLENT.value
        elif (0.6 <= mnsq < 0.8) or (1.2 < mnsq <= 1.4):
            return FitCategory.GOOD.value
        elif (0.5 <= mnsq < 0.6) or (1.4 < mnsq <= 1.5):
            return FitCategory.MARGINAL.value
        else:
            return FitCategory.POOR.value
    
    def _interpret_ability_level(self, theta: float) -> str:
        """Interpret ability level"""
        if theta < -2.0:
            return AbilityLevel.VERY_LOW.value
        elif theta < -0.5:
            return AbilityLevel.LOW.value
        elif theta <= 0.5:
            return AbilityLevel.AVERAGE.value
        elif theta <= 2.0:
            return AbilityLevel.HIGH.value
        else:
            return AbilityLevel.VERY_HIGH.value
    
    def save_person_measure(self, theta: float, fit_stats: dict, submission_id: int) -> Optional[RaschPersonMeasure]:
        """
        Save person measure ke database.
        
        Args:
            theta: Ability estimate
            fit_stats: Fit statistics
            submission_id: Quiz submission ID
            
        Returns:
            RaschPersonMeasure: Saved record, atau None jika gagal
        """
        try:
            # Check if already exists
            existing = RaschPersonMeasure.query.filter_by(
                rasch_analysis_id=self.analysis_id,
                student_id=self.student_id
            ).first()
            
            if existing:
                logger.info(f"Updating existing person measure for student {self.student_id}")
                person = existing
            else:
                person = RaschPersonMeasure(
                    rasch_analysis_id=self.analysis_id,
                    student_id=self.student_id,
                    quiz_submission_id=submission_id,
                )
            
            # Calculate raw score
            raw_score = sum(self.responses.values())
            total_possible = len(self.responses)
            percentage = (raw_score / total_possible * 100) if total_possible > 0 else 0
            
            # Calculate percentile
            all_thetas = RaschPersonMeasure.query.filter_by(
                rasch_analysis_id=self.analysis_id
            ).filter(RaschPersonMeasure.theta.isnot(None)).all()
            
            theta_values = [m.theta for m in all_thetas]
            percentile = sum(1 for t in theta_values if t < theta) / len(theta_values) * 100 if theta_values else 50
            
            # Update fields
            person.raw_score = raw_score
            person.total_possible = total_possible
            person.percentage = percentage
            person.theta = theta
            person.theta_se = fit_stats['theta_se']
            person.theta_centered = theta - (sum(theta_values) / len(theta_values)) if theta_values else 0
            person.outfit_mnsq = fit_stats['outfit_mnsq']
            person.outfit_zstd = fit_stats['outfit_zstd']
            person.infit_mnsq = fit_stats['infit_mnsq']
            person.infit_zstd = fit_stats['infit_zstd']
            person.fit_status = fit_stats['fit_status']
            person.fit_category = fit_stats['fit_category']
            person.ability_level = fit_stats['ability_level']
            person.ability_percentile = percentile
            
            db.session.add(person)
            db.session.commit()
            
            logger.info(f"Saved person measure for student {self.student_id} with theta={theta:.3f}")
            return person
            
        except Exception as e:
            logger.error(f"Error saving person measure: {e}", exc_info=True)
            db.session.rollback()
            return None
    
    def calculate_ability_for_submission(self, submission_id: int) -> Optional[dict]:
        """
        Main method: Calculate ability untuk submission baru.
        
        Args:
            submission_id: ID quiz submission
            
        Returns:
            dict: Result dengan ability dan fit statistics, atau None jika gagal
        """
        try:
            # Step 1: Load anchor values
            if not self.load_anchor_values():
                return None
            
            # Step 2: Load student responses
            if not self.load_student_responses(submission_id):
                return None
            
            # Step 3: Calculate ability
            theta = self.calculate_ability()
            
            if theta is None:
                logger.error("Failed to calculate ability")
                return None
            
            # Step 4: Calculate fit statistics
            fit_stats = self.calculate_fit_statistics(theta)
            
            # Step 5: Save to database
            submission = QuizSubmission.query.get(submission_id)
            person = self.save_person_measure(theta, fit_stats, submission_id)
            
            if person is None:
                return None
            
            # Update analysis num_persons
            if self.analysis:
                self.analysis.num_persons = RaschPersonMeasure.query.filter_by(
                    rasch_analysis_id=self.analysis_id
                ).count()
                db.session.commit()
            
            logger.info(f"Successfully calculated ability for student {self.student_id}: theta={theta:.3f}")
            
            return {
                'success': True,
                'student_id': self.student_id,
                'submission_id': submission_id,
                'theta': theta,
                'theta_se': fit_stats['theta_se'],
                'ability_level': fit_stats['ability_level'],
                'fit_status': fit_stats['fit_status'],
                'raw_score': sum(self.responses.values()),
                'total_items': len(self.responses),
            }
            
        except Exception as e:
            logger.error(f"Error in calculate_ability_for_submission: {e}", exc_info=True)
            return None


def process_late_submissions(quiz_id: int) -> dict:
    """
    Process late submissions untuk quiz yang sudah dianalisis.
    
    Fungsi ini akan:
    1. Cari analisis yang sudah completed untuk quiz ini
    2. Cari submissions yang belum ada di person_measures
    3. Hitung ability untuk setiap submission baru menggunakan anchor values
    
    Args:
        quiz_id: ID quiz
        
    Returns:
        dict: Summary hasil processing
    """
    from app.models.gradebook import GradeItem
    
    try:
        # Get completed analysis for this quiz
        grade_item = GradeItem.query.filter_by(quiz_id=quiz_id).first()
        
        if not grade_item or not grade_item.rasch_analysis_id:
            logger.warning(f"No Rasch analysis found for quiz {quiz_id}")
            return {'success': False, 'message': 'No completed analysis found'}
        
        analysis_id = grade_item.rasch_analysis_id
        analysis = RaschAnalysis.query.get(analysis_id)
        
        if not analysis or analysis.status != RaschAnalysisStatus.COMPLETED.value:
            logger.warning(f"Analysis {analysis_id} is not completed")
            return {'success': False, 'message': 'Analysis not completed'}
        
        # Get all submissions
        all_submissions = QuizSubmission.query.filter_by(quiz_id=quiz_id).all()
        
        # Get submissions that already have person measures
        existing_student_ids = db.session.query(RaschPersonMeasure.student_id).filter_by(
            rasch_analysis_id=analysis_id
        ).distinct().all()
        existing_student_ids = set([s[0] for s in existing_student_ids])
        
        # Find late submissions
        late_submissions = [
            s for s in all_submissions 
            if s.user_id not in existing_student_ids
        ]
        
        if not late_submissions:
            logger.info(f"No late submissions found for quiz {quiz_id}")
            return {'success': True, 'processed': 0, 'message': 'No late submissions'}
        
        # Process each late submission
        service = RaschAnchorService(analysis_id)
        processed = 0
        failed = 0
        
        for submission in late_submissions:
            result = service.calculate_ability_for_submission(submission.id)
            
            if result and result.get('success'):
                processed += 1
                logger.info(f"Processed late submission {submission.id} for student {submission.user_id}")
            else:
                failed += 1
                logger.warning(f"Failed to process late submission {submission.id}")
        
        logger.info(f"Processed {processed} late submissions, {failed} failed")
        
        return {
            'success': True,
            'processed': processed,
            'failed': failed,
            'total_late': len(late_submissions),
        }
        
    except Exception as e:
        logger.error(f"Error processing late submissions: {e}", exc_info=True)
        return {'success': False, 'error': str(e)}
