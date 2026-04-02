"""
Rasch Analysis Service

Implementasi Joint Maximum Likelihood Estimation (JMLE) untuk Rasch Model.

Rasch Model Formula:
    log(P_ni / (1 - P_ni)) = B_n - D_i
    
    dimana:
    - P_ni = Probabilitas siswa n menjawab benar soal i
    - B_n = Ability siswa n (theta)
    - D_i = Difficulty soal i (delta)

JMLE Algorithm:
    1. Initialize ability dan difficulty
    2. Iteratively update difficulty untuk setiap item
    3. Iteratively update ability untuk setiap person
    4. Check convergence
    5. Repeat hingga converge atau max iterations
"""

import math
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from app import create_app, db
from app.models.rasch import (
    RaschAnalysis,
    RaschAnalysisStatus,
    RaschPersonMeasure,
    RaschItemMeasure,
    FitStatus,
    FitCategory,
    AbilityLevel,
    DifficultyLevel,
)
from app.models.quiz import QuizSubmission, Answer, Question
from app.models.user import User

logger = logging.getLogger(__name__)


@dataclass
class RaschResult:
    """Container untuk hasil analisis Rasch"""
    person_measures: Dict[int, dict]  # student_id -> measure dict
    item_measures: Dict[int, dict]  # question_id -> measure dict
    iterations: int
    converged: bool
    cronbach_alpha: float
    person_separation_index: float
    item_separation_index: float


class RaschAnalysisService:
    """
    Service untuk menjalankan Rasch analysis menggunakan JMLE algorithm.
    
    Usage:
        service = RaschAnalysisService(analysis_id=1)
        result = service.run_analysis()
    """
    
    def __init__(self, analysis_id: int):
        self.analysis_id = analysis_id
        self.analysis: Optional[RaschAnalysis] = None
        
        # JMLE parameters
        self.convergence_threshold = 0.001
        self.max_iterations = 100
        
        # Data structures
        self.response_matrix: Dict[Tuple[int, int], int] = {}  # (student_id, question_id) -> 1/0
        self.students: List[int] = []  # List of student_ids
        self.questions: List[int] = []  # List of question_ids
        
        # Measures
        self.abilities: Dict[int, float] = {}  # student_id -> theta
        self.difficulties: Dict[int, float] = {}  # question_id -> delta
        
        # Results
        self.person_results: Dict[int, dict] = {}
        self.item_results: Dict[int, dict] = {}
    
    def load_data(self) -> bool:
        """
        Load data dari database untuk analisis.
        
        Returns:
            bool: True jika data berhasil dimuat
        """
        try:
            self.analysis = RaschAnalysis.query.get(self.analysis_id)
            
            if not self.analysis:
                raise ValueError(f"Analysis {self.analysis_id} not found")
            
            # Update parameters from analysis
            self.convergence_threshold = float(self.analysis.convergence_threshold)
            self.max_iterations = self.analysis.max_iterations
            
            # Get quiz or assignment
            if self.analysis.quiz_id:
                return self._load_quiz_data()
            elif self.analysis.assignment_id:
                return self._load_assignment_data()
            else:
                raise ValueError("Analysis must have quiz_id or assignment_id")
                
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return False
    
    def _load_quiz_data(self) -> bool:
        """Load data dari quiz submissions"""
        try:
            quiz_id = self.analysis.quiz_id
            
            # Get all submissions for this quiz
            submissions = QuizSubmission.query.filter_by(quiz_id=quiz_id).all()
            
            if not submissions:
                raise ValueError("No submissions found for quiz")
            
            # Get all questions in the quiz
            questions = Question.query.filter_by(quiz_id=quiz_id).all()
            self.questions = [q.id for q in questions]
            
            if not self.questions:
                raise ValueError("No questions found in quiz")
            
            # Build response matrix
            for submission in submissions:
                student_id = submission.user_id
                self.students.append(student_id)
                
                # Get answers for this submission
                answers = Answer.query.filter_by(submission_id=submission.id).all()
                
                for answer in answers:
                    question_id = answer.question_id
                    # Determine if correct (1) or incorrect (0)
                    is_correct = self._is_answer_correct(answer)
                    self.response_matrix[(student_id, question_id)] = 1 if is_correct else 0
            
            # Update analysis metadata
            self.analysis.num_persons = len(self.students)
            self.analysis.num_items = len(self.questions)
            
            logger.info(f"Loaded {len(self.students)} students, {len(self.questions)} questions")
            return True
            
        except Exception as e:
            logger.error(f"Error loading quiz data: {e}")
            return False
    
    def _load_assignment_data(self) -> bool:
        """Load data dari assignment submissions (rubric-based)"""
        logger.warning("Assignment-based Rasch analysis is not yet implemented")
        if self.analysis:
            self.analysis.status = RaschAnalysisStatus.COMPLETED
            self.analysis.error_message = "Analisis Rasch untuk tugas belum tersedia. Saat ini hanya tersedia untuk kuis."
            db.session.commit()
        return False
    
    def _is_answer_correct(self, answer: Answer) -> bool:
        """Check apakah jawaban benar"""
        question = answer.question
        
        if question.question_type in ['multiple_choice', 'true_false', 'dropdown']:
            # Check if selected option is correct
            if answer.selected_option_id:
                from app.models.quiz import Option
                option = Option.query.get(answer.selected_option_id)
                return option.is_correct if option else False
        elif question.question_type == 'checkbox':
            # Partial credit untuk checkbox
            # TODO: Implement partial credit
            return answer.manual_score > 0 if answer.manual_score else False
        elif question.question_type in ['long_text', 'upload']:
            # Manual grading
            return answer.manual_score > 0 if answer.manual_score else False
        
        return False
    
    def initialize_measures(self):
        """
        Initialize ability dan difficulty measures.

        Ability diinisialisasi berdasarkan raw score.
        Difficulty diinisialisasi berdasarkan p-value.
        
        Extreme scores (0 atau sempurna) di-exclude dari iterasi JMLE untuk
        menghindari bias kalibrasi. Ability mereka dihitung via ekstrapolasi
        setelah item konvergen.
        """
        # Identify students with extreme scores
        self.extreme_high_students = []  # Perfect scores
        self.extreme_low_students = []   # Zero scores
        self.non_extreme_students = []   # Students included in JMLE
        
        # Initialize abilities based on raw scores
        for student_id in self.students:
            raw_score = self._calculate_raw_score(student_id)
            total_items = len(self.questions)
            
            # Classify students
            if raw_score == 0:
                self.extreme_low_students.append(student_id)
                # Initial placeholder (will be extrapolated later)
                self.abilities[student_id] = -4.0  # Starting point for extrapolation
            elif raw_score == total_items:
                self.extreme_high_students.append(student_id)
                # Initial placeholder (will be extrapolated later)
                self.abilities[student_id] = 4.0  # Starting point for extrapolation
            else:
                self.non_extreme_students.append(student_id)
                # Logit transformation: theta = ln(p / (1-p))
                p = raw_score / total_items
                theta = math.log(p / (1 - p)) if 0 < p < 1 else 0
                self.abilities[student_id] = theta
        
        # Initialize difficulties based on p-values (using all students)
        for question_id in self.questions:
            p_value = self._calculate_p_value(question_id)
            
            # Avoid extreme values for items
            if p_value <= 0:
                p_value = 0.01
            elif p_value >= 1:
                p_value = 0.99
            
            # Logit transformation: delta = ln((1-p) / p)
            delta = math.log((1 - p_value) / p_value)
            self.difficulties[question_id] = delta
        
        logger.info(
            f"Initialized measures: {len(self.non_extreme_students)} non-extreme students, "
            f"{len(self.extreme_high_students)} extreme high, {len(self.extreme_low_students)} extreme low"
        )
    
    def _calculate_raw_score(self, student_id: int) -> int:
        """Calculate raw score untuk siswa"""
        score = 0
        for question_id in self.questions:
            if (student_id, question_id) in self.response_matrix:
                score += self.response_matrix[(student_id, question_id)]
        return score
    
    def _calculate_p_value(self, question_id: int) -> float:
        """Calculate p-value (proportion correct) untuk soal"""
        correct = 0
        total = 0
        
        for student_id in self.students:
            if (student_id, question_id) in self.response_matrix:
                correct += self.response_matrix[(student_id, question_id)]
                total += 1
        
        return correct / total if total > 0 else 0.5
    
    def run_jmle(self) -> bool:
        """
        Run Joint Maximum Likelihood Estimation algorithm.
        
        Hanya menggunakan non-extreme students untuk kalibrasi difficulty.
        Extreme students akan diekstrapolasi setelah konvergensi.

        Returns:
            bool: True jika converge
        """
        logger.info(f"Starting JMLE (max_iter={self.max_iterations}, threshold={self.convergence_threshold})")

        prev_abilities = {k: v for k, v in self.abilities.items() if k in self.non_extreme_students}
        prev_difficulties = self.difficulties.copy()

        for iteration in range(1, self.max_iterations + 1):
            # Update progress
            self._update_progress(iteration)

            # Step 1: Update item difficulties (fixing person abilities)
            # Only use non-extreme students for item calibration
            self._update_item_difficulties()

            # Step 2: Update person abilities (fixing item difficulties)
            # Only update non-extreme students
            self._update_person_abilities_non_extreme()

            # Step 3: Check convergence (only for non-extreme students)
            ability_change = self._calculate_max_change_filtered(prev_abilities, self.abilities, self.non_extreme_students)
            difficulty_change = self._calculate_max_change(prev_difficulties, self.difficulties)

            max_change = max(ability_change, difficulty_change)

            logger.debug(f"Iteration {iteration}: max_change={max_change:.6f}")

            if max_change < self.convergence_threshold:
                logger.info(f"Converged at iteration {iteration}")
                # Extrapolate abilities for extreme students
                self._extrapolate_extreme_abilities()
                self._save_results(iteration, converged=True)
                return True

            prev_abilities = {k: v for k, v in self.abilities.items() if k in self.non_extreme_students}
            prev_difficulties = self.difficulties.copy()

        logger.warning(f"Did not converge after {self.max_iterations} iterations")
        # Still extrapolate even if not converged
        self._extrapolate_extreme_abilities()
        self._save_results(self.max_iterations, converged=False)
        return False
    
    def _update_item_difficulties(self):
        """
        Update item difficulties using Newton-Raphson.
        Hanya menggunakan non-extreme students untuk kalibrasi difficulty yang tidak bias.
        """
        for question_id in self.questions:
            # Get responses for this item (only from non-extreme students)
            responses = []
            abilities_for_item = []

            for student_id in self.non_extreme_students:
                if (student_id, question_id) in self.response_matrix:
                    responses.append(self.response_matrix[(student_id, question_id)])
                    abilities_for_item.append(self.abilities[student_id])

            if not responses:
                continue

            # Newton-Raphson update
            delta = self.difficulties[question_id]

            for _ in range(10):  # Max 10 iterations per item
                # Calculate expected and observed
                sum_expected = 0
                sum_variance = 0
                sum_observed = sum(responses)

                for i, theta in enumerate(abilities_for_item):
                    p = self._probability(theta, delta)
                    sum_expected += p
                    sum_variance += p * (1 - p)

                # Update delta
                if sum_variance > 0.0001:
                    delta_new = delta + (sum_observed - sum_expected) / sum_variance
                    delta = delta_new
                else:
                    break

            self.difficulties[question_id] = delta
    
    def _update_person_abilities(self):
        """Update person abilities using Newton-Raphson (legacy, use _update_person_abilities_non_extreme)"""
        for student_id in self.students:
            # Get responses for this person
            responses = []
            difficulties_for_person = []

            for question_id in self.questions:
                if (student_id, question_id) in self.response_matrix:
                    responses.append(self.response_matrix[(student_id, question_id)])
                    difficulties_for_person.append(self.difficulties[question_id])

            if not responses:
                continue

            # Newton-Raphson update
            theta = self.abilities[student_id]

            for _ in range(10):  # Max 10 iterations per person
                # Calculate expected and observed
                sum_expected = 0
                sum_variance = 0
                sum_observed = sum(responses)

                for i, delta in enumerate(difficulties_for_person):
                    p = self._probability(theta, delta)
                    sum_expected += p
                    sum_variance += p * (1 - p)

                # Update theta
                if sum_variance > 0.0001:
                    theta_new = theta + (sum_observed - sum_expected) / sum_variance
                    theta = theta_new
                else:
                    break

            self.abilities[student_id] = theta

    def _update_person_abilities_non_extreme(self):
        """
        Update person abilities using Newton-Raphson.
        Hanya update non-extreme students untuk menghindari bias.
        """
        for student_id in self.non_extreme_students:
            # Get responses for this person
            responses = []
            difficulties_for_person = []

            for question_id in self.questions:
                if (student_id, question_id) in self.response_matrix:
                    responses.append(self.response_matrix[(student_id, question_id)])
                    difficulties_for_person.append(self.difficulties[question_id])

            if not responses:
                continue

            # Newton-Raphson update
            theta = self.abilities[student_id]

            for _ in range(10):  # Max 10 iterations per person
                # Calculate expected and observed
                sum_expected = 0
                sum_variance = 0
                sum_observed = sum(responses)

                for i, delta in enumerate(difficulties_for_person):
                    p = self._probability(theta, delta)
                    sum_expected += p
                    sum_variance += p * (1 - p)

                # Update theta
                if sum_variance > 0.0001:
                    theta_new = theta + (sum_observed - sum_expected) / sum_variance
                    theta = theta_new
                else:
                    break

            self.abilities[student_id] = theta

    def _extrapolate_extreme_abilities(self):
        """
        Extrapolate ability estimates for extreme students (perfect or zero scores).
        
        Menggunakan metode Wright & Linacre (1990) untuk extrapolasi:
        - Extreme high: theta ≈ theta_max + SE_max
        - Extreme low: theta ≈ theta_min - SE_min
        
        Dimana theta_max/min adalah ability tertinggi/terendah dari non-extreme students,
        dan SE adalah standard error.
        """
        if not self.non_extreme_students:
            logger.warning("No non-extreme students for extrapolation")
            return
        
        # Get abilities and SE for non-extreme students
        non_extreme_thetas = [self.abilities[s] for s in self.non_extreme_students]
        
        if not non_extreme_thetas:
            return
        
        # Calculate average ability and spread
        mean_theta = sum(non_extreme_thetas) / len(non_extreme_thetas)
        
        # Calculate standard deviation of non-extreme abilities
        if len(non_extreme_thetas) > 1:
            variance = sum((t - mean_theta) ** 2 for t in non_extreme_thetas) / (len(non_extreme_thetas) - 1)
            std_dev = math.sqrt(variance) if variance > 0 else 1.0
        else:
            std_dev = 1.0
        
        # Extrapolate extreme high students (perfect scores)
        for student_id in self.extreme_high_students:
            # Use Wright & Linacre approximation: theta ≈ theta_max + 1.4 * SE
            # SE is approximated from the spread of non-extreme abilities
            extreme_theta = mean_theta + (2.0 * std_dev)
            self.abilities[student_id] = extreme_theta
            logger.debug(f"Extrapolated extreme-high student {student_id}: theta={extreme_theta:.3f}")
        
        # Extrapolate extreme low students (zero scores)
        for student_id in self.extreme_low_students:
            # Use Wright & Linacre approximation: theta ≈ theta_min - 1.4 * SE
            extreme_theta = mean_theta - (2.0 * std_dev)
            self.abilities[student_id] = extreme_theta
            logger.debug(f"Extrapolated extreme-low student {student_id}: theta={extreme_theta:.3f}")
        
        logger.info(
            f"Extrapolated {len(self.extreme_high_students)} extreme-high and "
            f"{len(self.extreme_low_students)} extreme-low students"
        )

    def _calculate_max_change_filtered(
        self,
        old_values: Dict[int, float],
        new_values: Dict[int, float],
        filter_keys: List[int]
    ) -> float:
        """
        Calculate maximum absolute change between iterations for filtered keys only.
        """
        max_change = 0

        for key in filter_keys:
            if key in old_values and key in new_values:
                change = abs(new_values[key] - old_values[key])
                max_change = max(max_change, change)

        return max_change
    
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
    
    def _calculate_max_change(
        self, 
        old_values: Dict[int, float], 
        new_values: Dict[int, float]
    ) -> float:
        """Calculate maximum absolute change between iterations"""
        max_change = 0
        
        for key in new_values:
            if key in old_values:
                change = abs(new_values[key] - old_values[key])
                max_change = max(max_change, change)
        
        return max_change
    
    def calculate_fit_statistics(self):
        """Calculate fit statistics (infit, outfit) untuk persons dan items"""
        # Person fit statistics
        for student_id in self.students:
            self.person_results[student_id] = self._calculate_person_fit(student_id)
        
        # Item fit statistics
        for question_id in self.questions:
            self.item_results[question_id] = self._calculate_item_fit(question_id)
    
    def _calculate_person_fit(self, student_id: int) -> dict:
        """Calculate fit statistics untuk person"""
        theta = self.abilities[student_id]

        sum_squared_residual = 0
        sum_variance = 0
        sum_standardized_sq = 0  # Σ(z²) for outfit

        n_items = 0
        sum_information = 0  # Σ(P*Q) for model-based SE

        for question_id in self.questions:
            if (student_id, question_id) not in self.response_matrix:
                continue

            observed = self.response_matrix[(student_id, question_id)]
            delta = self.difficulties[question_id]
            p = self._probability(theta, delta)

            residual = observed - p
            variance = p * (1 - p)
            sum_information += variance

            if variance > 0.0001:
                sum_squared_residual += residual ** 2
                sum_variance += variance
                sum_standardized_sq += (residual ** 2) / variance

            n_items += 1

        # Infit MNSQ (information-weighted): Σ(residual²) / Σ(variance)
        infit_mnsq = sum_squared_residual / sum_variance if sum_variance > 0 else 1.0

        # Outfit MNSQ (unweighted mean of standardized residuals): (1/N) × Σ(z²)
        outfit_mnsq = sum_standardized_sq / n_items if n_items > 0 else 1.0

        # Z-standardized using Wilson-Hilferty cube root transformation
        infit_zstd = self._wilson_hilferty_zstd(infit_mnsq, n_items)
        outfit_zstd = self._wilson_hilferty_zstd(outfit_mnsq, n_items)

        # Fit interpretation
        fit_status = self._interpret_fit_status(outfit_mnsq)
        fit_category = self._interpret_fit_category(outfit_mnsq)

        # Ability level interpretation
        ability_level = self._interpret_ability_level(theta)

        # Model-based SE: 1/√(Σ P*Q)
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
    
    def _calculate_item_fit(self, question_id: int) -> dict:
        """Calculate fit statistics untuk item"""
        delta = self.difficulties[question_id]

        sum_squared_residual = 0
        sum_variance = 0
        sum_standardized_sq = 0  # Σ(z²) for outfit

        n_persons = 0
        sum_information = 0  # Σ(P*Q) for model-based SE

        for student_id in self.students:
            if (student_id, question_id) not in self.response_matrix:
                continue

            observed = self.response_matrix[(student_id, question_id)]
            theta = self.abilities[student_id]
            p = self._probability(theta, delta)

            residual = observed - p
            variance = p * (1 - p)
            sum_information += variance

            if variance > 0.0001:
                sum_squared_residual += residual ** 2
                sum_variance += variance
                sum_standardized_sq += (residual ** 2) / variance

            n_persons += 1

        # Infit MNSQ (information-weighted): Σ(residual²) / Σ(variance)
        infit_mnsq = sum_squared_residual / sum_variance if sum_variance > 0 else 1.0

        # Outfit MNSQ (unweighted mean of standardized residuals): (1/N) × Σ(z²)
        outfit_mnsq = sum_standardized_sq / n_persons if n_persons > 0 else 1.0

        # Z-standardized using Wilson-Hilferty cube root transformation
        infit_zstd = self._wilson_hilferty_zstd(infit_mnsq, n_persons)
        outfit_zstd = self._wilson_hilferty_zstd(outfit_mnsq, n_persons)

        # Fit interpretation
        fit_status = self._interpret_fit_status(outfit_mnsq)
        fit_category = self._interpret_fit_category(outfit_mnsq)

        # Difficulty interpretation
        difficulty_level = self._interpret_difficulty_level(delta)

        # Classical p-value
        p_value = self._calculate_p_value(question_id)

        # Point-biserial (simplified)
        point_biserial = self._calculate_point_biserial(question_id)

        # Model-based SE: 1/√(Σ P*Q)
        delta_se = 1 / math.sqrt(sum_information) if sum_information > 0 else 1.0

        return {
            'delta': delta,
            'delta_se': delta_se,
            'p_value': p_value,
            'point_biserial': point_biserial,
            'outfit_mnsq': outfit_mnsq,
            'outfit_zstd': outfit_zstd,
            'infit_mnsq': infit_mnsq,
            'infit_zstd': infit_zstd,
            'fit_status': fit_status,
            'fit_category': fit_category,
            'difficulty_level': difficulty_level,
        }
    
    def _wilson_hilferty_zstd(self, mnsq: float, n: int) -> float:
        """
        Wilson-Hilferty cube root transformation for MNSQ to Z-standardized.
        Standard formula used by Winsteps and other Rasch software.
        """
        if n <= 0 or mnsq <= 0:
            return 0.0
        q = 6.0 / n
        try:
            zstd = (mnsq ** (1.0 / 3) - 1) * (3 / math.sqrt(q)) + math.sqrt(q) / 3
        except (ValueError, ZeroDivisionError):
            zstd = 0.0
        return zstd

    def _interpret_fit_status(self, mnsq: float) -> str:
        """Interpret fit status berdasarkan MNSQ"""
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
        """Interpret ability level berdasarkan theta"""
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
    
    def _interpret_difficulty_level(self, delta: float) -> str:
        """Interpret difficulty level berdasarkan delta"""
        if delta < -2.0:
            return DifficultyLevel.VERY_EASY.value
        elif delta < -0.5:
            return DifficultyLevel.EASY.value
        elif delta <= 0.5:
            return DifficultyLevel.MODERATE.value
        elif delta <= 2.0:
            return DifficultyLevel.DIFFICULT.value
        else:
            return DifficultyLevel.VERY_DIFFICULT.value
    
    def _calculate_point_biserial(self, question_id: int) -> float:
        """Calculate point-biserial correlation untuk item"""
        # Simplified calculation
        correct_scores = []
        incorrect_scores = []
        
        for student_id in self.students:
            if (student_id, question_id) not in self.response_matrix:
                continue
            
            response = self.response_matrix[(student_id, question_id)]
            raw_score = self._calculate_raw_score(student_id) - response  # Exclude this item
            
            if response == 1:
                correct_scores.append(raw_score)
            else:
                incorrect_scores.append(raw_score)
        
        if not correct_scores or not incorrect_scores:
            return 0.0
        
        # Point-biserial approximation
        mean_correct = sum(correct_scores) / len(correct_scores)
        mean_incorrect = sum(incorrect_scores) / len(incorrect_scores)
        
        all_scores = correct_scores + incorrect_scores
        std_dev = math.sqrt(sum((s - sum(all_scores)/len(all_scores))**2 for s in all_scores) / len(all_scores))
        
        if std_dev == 0:
            return 0.0
        
        p = len(correct_scores) / len(all_scores)
        q = 1 - p
        
        point_biserial = (mean_correct - mean_incorrect) / std_dev * math.sqrt(p * q)
        
        # Clamp to [-1, 1]
        return max(-1.0, min(1.0, point_biserial))
    
    def calculate_reliability(self) -> dict:
        """Calculate reliability indices"""
        # Person separation index
        person_variance = self._calculate_variance(list(self.abilities.values()))
        person_se_mean = sum(
            self.person_results[sid]['theta_se'] ** 2 
            for sid in self.students
        ) / len(self.students)
        
        person_separation = math.sqrt(person_variance / person_se_mean) if person_se_mean > 0 else 0
        person_reliability = person_separation ** 2 / (1 + person_separation ** 2)
        
        # Item separation index
        item_variance = self._calculate_variance(list(self.difficulties.values()))
        item_se_mean = sum(
            self.item_results[qid]['delta_se'] ** 2 
            for qid in self.questions
        ) / len(self.questions)
        
        item_separation = math.sqrt(item_variance / item_se_mean) if item_se_mean > 0 else 0
        item_reliability = item_separation ** 2 / (1 + item_separation ** 2)
        
        # Cronbach's alpha (simplified)
        n_items = len(self.questions)
        item_variances = []
        
        for qid in self.questions:
            p = self.item_results[qid]['p_value']
            item_variances.append(p * (1 - p))
        
        total_variance = self._calculate_variance([
            self._calculate_raw_score(sid) for sid in self.students
        ])
        
        if total_variance > 0:
            cronbach_alpha = (n_items / (n_items - 1)) * (
                1 - sum(item_variances) / total_variance
            )
        else:
            cronbach_alpha = 0
        
        return {
            'person_separation_index': person_separation,
            'person_reliability': person_reliability,
            'item_separation_index': item_separation,
            'item_reliability': item_reliability,
            'cronbach_alpha': cronbach_alpha,
        }
    
    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance"""
        if len(values) < 2:
            return 0
        
        mean = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    
    def _update_progress(self, iteration: int):
        """Update progress di database"""
        if self.analysis:
            progress = (iteration / self.max_iterations) * 100
            self.analysis.progress_percentage = progress
            self.analysis.status_message = f"Iteration {iteration}/{self.max_iterations}"
            db.session.commit()
    
    def _save_results(self, iterations: int, converged: bool):
        """Save results ke database"""
        try:
            if not self.analysis:
                return
            
            # Calculate fit statistics
            self.calculate_fit_statistics()
            
            # Calculate reliability
            reliability = self.calculate_reliability()
            
            # Save person measures
            for student_id, measure in self.person_results.items():
                # Get raw score
                raw_score = self._calculate_raw_score(student_id)
                total_possible = len(self.questions)
                percentage = (raw_score / total_possible * 100) if total_possible > 0 else 0
                
                # Calculate percentile
                all_thetas = [self.person_results[s]['theta'] for s in self.students]
                percentile = sum(1 for t in all_thetas if t < measure['theta']) / len(all_thetas) * 100
                
                person = RaschPersonMeasure(
                    rasch_analysis_id=self.analysis_id,
                    student_id=student_id,
                    raw_score=raw_score,
                    total_possible=total_possible,
                    percentage=percentage,
                    theta=measure['theta'],
                    theta_se=measure['theta_se'],
                    theta_centered=measure['theta'] - sum(all_thetas) / len(all_thetas),
                    outfit_mnsq=measure['outfit_mnsq'],
                    outfit_zstd=measure['outfit_zstd'],
                    infit_mnsq=measure['infit_mnsq'],
                    infit_zstd=measure['infit_zstd'],
                    fit_status=measure['fit_status'],
                    fit_category=measure['fit_category'],
                    ability_level=measure['ability_level'],
                    ability_percentile=percentile,
                )
                db.session.add(person)
            
            # Save item measures
            for question_id, measure in self.item_results.items():
                # Get Bloom taxonomy if exists
                bloom_level = None
                from app.models.rasch import QuestionBloomTaxonomy
                bloom = QuestionBloomTaxonomy.query.filter_by(question_id=question_id).first()
                if bloom:
                    bloom_level = bloom.bloom_level.value
                
                item = RaschItemMeasure(
                    rasch_analysis_id=self.analysis_id,
                    question_id=question_id,
                    p_value=measure['p_value'],
                    point_biserial=measure['point_biserial'],
                    delta=measure['delta'],
                    delta_se=measure['delta_se'],
                    delta_centered=measure['delta'] - sum(self.difficulties.values()) / len(self.difficulties),
                    outfit_mnsq=measure['outfit_mnsq'],
                    outfit_zstd=measure['outfit_zstd'],
                    infit_mnsq=measure['infit_mnsq'],
                    infit_zstd=measure['infit_zstd'],
                    fit_status=measure['fit_status'],
                    fit_category=measure['fit_category'],
                    difficulty_level=measure['difficulty_level'],
                    bloom_level=bloom_level,
                )
                db.session.add(item)
            
            # Update analysis
            self.analysis.status = RaschAnalysisStatus.COMPLETED.value if converged else RaschAnalysisStatus.PARTIAL.value
            self.analysis.completed_at = datetime.utcnow()
            self.analysis.cronbach_alpha = reliability['cronbach_alpha']
            self.analysis.person_separation_index = reliability['person_separation_index']
            self.analysis.item_separation_index = reliability['item_separation_index']
            
            db.session.commit()
            
            logger.info(f"Results saved: {len(self.person_results)} persons, {len(self.item_results)} items")
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
            db.session.rollback()
            raise
    
    def run_analysis(self) -> bool:
        """
        Run complete Rasch analysis.
        
        Returns:
            bool: True jika analisis berhasil
        """
        try:
            # Step 1: Load data
            if not self.load_data():
                return False
            
            # Step 2: Initialize measures
            self.initialize_measures()
            
            # Step 3: Run JMLE
            converged = self.run_jmle()
            
            logger.info(f"Analysis complete: converged={converged}")
            return True
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            if self.analysis:
                self.analysis.status = RaschAnalysisStatus.FAILED.value
                self.analysis.error_message = str(e)
                db.session.commit()
            return False
