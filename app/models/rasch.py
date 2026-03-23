"""
Rasch Model Models for Aldudu Academy

Models untuk mendukung analisis Rasch Model pada sistem gradebook.
Rasch Model digunakan untuk mengukur:
- Ability (θ): Kemampuan siswa
- Difficulty (δ): Tingkat kesulitan soal

Teori Klasik: Instant (saat submit quiz)
Rasch Model: Batch processing (setelah threshold ≥30 siswa)
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import CheckConstraint, UniqueConstraint, Index, JSON
from enum import Enum

from app.extensions import db
from app.helpers import get_jakarta_now


# ============================================================
# Enums
# ============================================================

class RaschAnalysisStatus(Enum):
    """Status untuk Rasch Analysis"""
    PENDING = 'pending'  # Menunggu threshold
    WAITING = 'waiting'  # Menunggu siswa lain submit
    QUEUED = 'queued'  # Masuk antrian worker
    PROCESSING = 'processing'  # Sedang dianalisis
    COMPLETED = 'completed'  # Selesai
    FAILED = 'failed'  # Gagal
    PARTIAL = 'partial'  # Sebagian selesai


class RaschAnalysisType(Enum):
    """Tipe analisis Rasch"""
    QUIZ = 'quiz'
    ASSIGNMENT = 'assignment'
    COMBINED = 'combined'


class BloomLevel(Enum):
    """Bloom's Revised Taxonomy Levels"""
    REMEMBER = 'remember'  # Mengingat informasi
    UNDERSTAND = 'understand'  # Memahami konsep
    APPLY = 'apply'  # Menerapkan konsep
    ANALYZE = 'analyze'  # Menganalisis informasi
    EVALUATE = 'evaluate'  # Mengevaluasi/menilai
    CREATE = 'create'  # Mencipta/menghasilkan


class FitStatus(Enum):
    """Status fit statistic untuk Rasch"""
    WELL_FITTED = 'well_fitted'  # 0.5 <= MNSQ <= 1.5
    UNDERFIT = 'underfit'  # MNSQ > 1.5 (unpredictable)
    OVERFIT = 'overfit'  # MNSQ < 0.5 (too predictable)


class FitCategory(Enum):
    """Kategori fit quality"""
    EXCELLENT = 'excellent'  # 0.8 <= MNSQ <= 1.2
    GOOD = 'good'  # 0.6 <= MNSQ < 0.8 or 1.2 < MNSQ <= 1.4
    MARGINAL = 'marginal'  # 0.5 <= MNSQ < 0.6 or 1.4 < MNSQ <= 1.5
    POOR = 'poor'  # MNSQ < 0.5 or MNSQ > 1.5


class AbilityLevel(Enum):
    """Level kemampuan siswa berdasarkan theta"""
    VERY_LOW = 'very_low'  # θ < -2.0
    LOW = 'low'  # -2.0 <= θ < -0.5
    AVERAGE = 'average'  # -0.5 <= θ <= 0.5
    HIGH = 'high'  # 0.5 < θ <= 2.0
    VERY_HIGH = 'very_high'  # θ > 2.0


class DifficultyLevel(Enum):
    """Level kesulitan soal berdasarkan delta"""
    VERY_EASY = 'very_easy'  # δ < -2.0 (p > 0.90)
    EASY = 'easy'  # -2.0 <= δ < -0.5 (p: 0.70-0.90)
    MODERATE = 'moderate'  # -0.5 <= δ <= 0.5 (p: 0.30-0.70)
    DIFFICULT = 'difficult'  # 0.5 < δ <= 2.0 (p: 0.10-0.30)
    VERY_DIFFICULT = 'very_difficult'  # δ > 2.0 (p < 0.10)


class ThresholdCheckType(Enum):
    """Tipe threshold check"""
    AUTO = 'auto'  # Automatic check saat submission
    MANUAL = 'manual'  # Manual trigger oleh guru


class ThresholdAction(Enum):
    """Action yang diambil setelah threshold check"""
    QUEUED = 'queued'  # Masuk antrian analisis
    WAITING = 'waiting'  # Masih menunggu
    IGNORED = 'ignored'  # Diabaikan


# ============================================================
# Models
# ============================================================

class QuestionBloomTaxonomy(db.Model):
    """
    Mapping taksonomi Bloom untuk setiap soal.
    
    Digunakan untuk:
    - Analisis korelasi difficulty vs cognitive level
    - Validitas konstruk: memastikan quiz mengukur berbagai level kognitif
    - Reporting: distribusi soal per level Bloom
    """
    __tablename__ = 'question_bloom_taxonomy'
    
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    question_id: Mapped[int] = mapped_column(
        db.Integer, 
        db.ForeignKey('questions.id', ondelete='CASCADE'), 
        nullable=False,
        unique=True
    )
    
    # Bloom's Revised Taxonomy
    bloom_level: Mapped[str] = mapped_column(
        db.Enum(BloomLevel), 
        nullable=False
    )
    bloom_description: Mapped[Optional[str]] = mapped_column(
        db.Text, 
        nullable=True
    )
    
    # Verification
    verified_by: Mapped[Optional[int]] = mapped_column(
        db.Integer, 
        db.ForeignKey('users.id'), 
        nullable=True
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(
        db.DateTime, 
        nullable=True
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime, 
        default=get_jakarta_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        db.DateTime, 
        default=get_jakarta_now, 
        onupdate=get_jakarta_now
    )
    
    # Relationships
    question = relationship('Question', back_populates='bloom_taxonomy')
    verifier = relationship('User', foreign_keys=[verified_by])
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'question_id': self.question_id,
            'bloom_level': self.bloom_level.value,
            'bloom_description': self.bloom_description,
            'verified_by': self.verified_by,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
        }
    
    def __repr__(self) -> str:
        return f'<QuestionBloomTaxonomy Q{self.question_id}: {self.bloom_level.value}>'


class RaschAnalysis(db.Model):
    """
    Tabel utama untuk tracking analisis Rasch.
    
    Setiap quiz/assignment yang enable_rasch_analysis=True akan memiliki
    record di tabel ini saat threshold terpenuhi.
    """
    __tablename__ = 'rasch_analyses'
    
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    course_id: Mapped[int] = mapped_column(
        db.Integer, 
        db.ForeignKey('courses.id', ondelete='CASCADE'), 
        nullable=False,
        index=True
    )
    
    # Source assessment (nullable untuk combined analysis)
    quiz_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, 
        db.ForeignKey('quizzes.id', ondelete='SET NULL'), 
        nullable=True,
        index=True
    )
    assignment_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, 
        db.ForeignKey('assignments.id', ondelete='SET NULL'), 
        nullable=True,
        index=True
    )
    
    # Identification
    name: Mapped[str] = mapped_column(db.String(200), nullable=False)
    analysis_type: Mapped[str] = mapped_column(
        db.Enum(RaschAnalysisType), 
        nullable=False
    )
    
    # Status tracking
    status: Mapped[str] = mapped_column(
        db.Enum(RaschAnalysisStatus), 
        nullable=False, 
        default=RaschAnalysisStatus.PENDING,
        index=True
    )
    progress_percentage: Mapped[float] = mapped_column(
        db.Numeric(5, 2), 
        default=0
    )
    status_message: Mapped[Optional[str]] = mapped_column(db.String(500))
    
    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime)
    error_message: Mapped[Optional[str]] = mapped_column(db.Text)
    
    # Threshold configuration
    min_persons: Mapped[int] = mapped_column(
        db.Integer, 
        default=30,
        nullable=False
    )
    auto_trigger: Mapped[bool] = mapped_column(
        db.Boolean, 
        default=True
    )
    
    # Rasch parameters
    convergence_threshold: Mapped[float] = mapped_column(
        db.Numeric(10, 8), 
        default=0.001
    )
    max_iterations: Mapped[int] = mapped_column(
        db.Integer, 
        default=100
    )
    
    # Results summary
    num_persons: Mapped[Optional[int]] = mapped_column(db.Integer)
    num_items: Mapped[Optional[int]] = mapped_column(db.Integer)
    cronbach_alpha: Mapped[Optional[float]] = mapped_column(db.Numeric(5, 4))
    person_separation_index: Mapped[Optional[float]] = mapped_column(db.Numeric(5, 4))
    item_separation_index: Mapped[Optional[float]] = mapped_column(db.Numeric(5, 4))
    
    # Metadata
    created_by: Mapped[int] = mapped_column(
        db.Integer, 
        db.ForeignKey('users.id'), 
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime, 
        default=get_jakarta_now,
        index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        db.DateTime, 
        default=get_jakarta_now, 
        onupdate=get_jakarta_now
    )
    
    # Relationships
    course = relationship('Course', back_populates='rasch_analyses')
    quiz = relationship('Quiz', back_populates='rasch_analyses')
    assignment = relationship('Assignment', back_populates='rasch_analyses')
    creator = relationship('User', foreign_keys=[created_by])
    grade_item = relationship('GradeItem', back_populates='rasch_analysis')
    
    person_measures: Mapped[List['RaschPersonMeasure']] = relationship(
        'RaschPersonMeasure', 
        back_populates='analysis', 
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    item_measures: Mapped[List['RaschItemMeasure']] = relationship(
        'RaschItemMeasure', 
        back_populates='analysis', 
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    threshold_logs: Mapped[List['RaschThresholdLog']] = relationship(
        'RaschThresholdLog', 
        back_populates='analysis', 
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    rating_scales: Mapped[List['RaschRatingScale']] = relationship(
        'RaschRatingScale', 
        back_populates='analysis', 
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    
    # Check constraints
    __table_args__ = (
        CheckConstraint(
            'min_persons >= 5',
            name='chk_rasch_min_persons'
        ),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'course_id': self.course_id,
            'quiz_id': self.quiz_id,
            'assignment_id': self.assignment_id,
            'name': self.name,
            'analysis_type': self.analysis_type.value,
            'status': self.status.value,
            'progress_percentage': float(self.progress_percentage) if self.progress_percentage else 0,
            'status_message': self.status_message,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message,
            'min_persons': self.min_persons,
            'auto_trigger': self.auto_trigger,
            'num_persons': self.num_persons,
            'num_items': self.num_items,
            'cronbach_alpha': float(self.cronbach_alpha) if self.cronbach_alpha else None,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    @property
    def is_complete(self) -> bool:
        return self.status == RaschAnalysisStatus.COMPLETED
    
    @property
    def is_failed(self) -> bool:
        return self.status == RaschAnalysisStatus.FAILED
    
    @property
    def is_processing(self) -> bool:
        return self.status in [
            RaschAnalysisStatus.PENDING,
            RaschAnalysisStatus.WAITING,
            RaschAnalysisStatus.QUEUED,
            RaschAnalysisStatus.PROCESSING
        ]
    
    def __repr__(self) -> str:
        return f'<RaschAnalysis {self.name} ({self.status.value})>'


class RaschPersonMeasure(db.Model):
    """
    Ability parameter (θ) untuk setiap siswa dalam analisis Rasch.
    
    Menyimpan:
    - Classical scores (raw_score, percentage) untuk comparability
    - Rasch ability (theta) dalam logit scale
    - Fit statistics (infit, outfit)
    - Interpretation (ability_level, fit_category)
    """
    __tablename__ = 'rasch_person_measures'
    
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    rasch_analysis_id: Mapped[int] = mapped_column(
        db.Integer, 
        db.ForeignKey('rasch_analyses.id', ondelete='CASCADE'), 
        nullable=False,
        index=True
    )
    student_id: Mapped[int] = mapped_column(
        db.Integer, 
        db.ForeignKey('users.id', ondelete='CASCADE'), 
        nullable=False,
        index=True
    )
    quiz_submission_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, 
        db.ForeignKey('quiz_submissions.id', ondelete='SET NULL'), 
        nullable=True
    )
    
    # Classical scores
    raw_score: Mapped[int] = mapped_column(db.Integer, nullable=False)
    total_possible: Mapped[int] = mapped_column(db.Integer, nullable=False)
    percentage: Mapped[float] = mapped_column(db.Numeric(5, 2), nullable=False)
    
    # Rasch ability measure (logit scale)
    theta: Mapped[Optional[float]] = mapped_column(db.Numeric(10, 6))
    theta_se: Mapped[Optional[float]] = mapped_column(db.Numeric(10, 6))
    theta_centered: Mapped[Optional[float]] = mapped_column(db.Numeric(10, 6))
    
    # Fit statistics
    outfit_mnsq: Mapped[Optional[float]] = mapped_column(db.Numeric(10, 6))
    outfit_zstd: Mapped[Optional[float]] = mapped_column(db.Numeric(10, 6))
    infit_mnsq: Mapped[Optional[float]] = mapped_column(db.Numeric(10, 6))
    infit_zstd: Mapped[Optional[float]] = mapped_column(db.Numeric(10, 6))
    
    # Fit interpretation
    fit_status: Mapped[Optional[str]] = mapped_column(
        db.Enum(FitStatus)
    )
    fit_category: Mapped[Optional[str]] = mapped_column(
        db.Enum(FitCategory)
    )
    
    # Ability level interpretation
    ability_level: Mapped[Optional[str]] = mapped_column(
        db.Enum(AbilityLevel)
    )
    ability_percentile: Mapped[Optional[float]] = mapped_column(db.Numeric(5, 2))
    
    # Wright Map position
    wright_map_band: Mapped[Optional[str]] = mapped_column(db.String(50))
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime, 
        default=get_jakarta_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        db.DateTime, 
        default=get_jakarta_now, 
        onupdate=get_jakarta_now
    )
    
    # Relationships
    analysis = relationship('RaschAnalysis', back_populates='person_measures')
    student = relationship('User', foreign_keys=[student_id])
    quiz_submission = relationship('QuizSubmission')
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('rasch_analysis_id', 'student_id', 
                        name='uq_rasch_person'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'rasch_analysis_id': self.rasch_analysis_id,
            'student_id': self.student_id,
            'student_name': self.student.name if self.student else None,
            'raw_score': self.raw_score,
            'total_possible': self.total_possible,
            'percentage': float(self.percentage) if self.percentage else None,
            'theta': float(self.theta) if self.theta else None,
            'theta_se': float(self.theta_se) if self.theta_se else None,
            'theta_centered': float(self.theta_centered) if self.theta_centered else None,
            'outfit_mnsq': float(self.outfit_mnsq) if self.outfit_mnsq else None,
            'outfit_zstd': float(self.outfit_zstd) if self.outfit_zstd else None,
            'infit_mnsq': float(self.infit_mnsq) if self.infit_mnsq else None,
            'infit_zstd': float(self.infit_zstd) if self.infit_zstd else None,
            'fit_status': self.fit_status.value if self.fit_status else None,
            'fit_category': self.fit_category.value if self.fit_category else None,
            'ability_level': self.ability_level.value if self.ability_level else None,
            'ability_percentile': float(self.ability_percentile) if self.ability_percentile else None,
        }
    
    def __repr__(self) -> str:
        return f'<RaschPersonMeasure Student:{self.student_id} θ={self.theta}>'


class RaschItemMeasure(db.Model):
    """
    Difficulty parameter (δ) untuk setiap soal dalam analisis Rasch.
    
    Menyimpan:
    - Classical indices (p_value, point_biserial)
    - Rasch difficulty (delta) dalam logit scale
    - Fit statistics
    - Bloom taxonomy level (cached)
    """
    __tablename__ = 'rasch_item_measures'
    
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    rasch_analysis_id: Mapped[int] = mapped_column(
        db.Integer, 
        db.ForeignKey('rasch_analyses.id', ondelete='CASCADE'), 
        nullable=False,
        index=True
    )
    question_id: Mapped[int] = mapped_column(
        db.Integer, 
        db.ForeignKey('questions.id', ondelete='CASCADE'), 
        nullable=False,
        index=True
    )
    
    # Classical indices
    p_value: Mapped[Optional[float]] = mapped_column(db.Numeric(5, 4))
    point_biserial: Mapped[Optional[float]] = mapped_column(db.Numeric(5, 4))
    
    # Rasch difficulty measure
    delta: Mapped[Optional[float]] = mapped_column(db.Numeric(10, 6))
    delta_se: Mapped[Optional[float]] = mapped_column(db.Numeric(10, 6))
    delta_centered: Mapped[Optional[float]] = mapped_column(db.Numeric(10, 6))
    
    # Fit statistics
    outfit_mnsq: Mapped[Optional[float]] = mapped_column(db.Numeric(10, 6))
    outfit_zstd: Mapped[Optional[float]] = mapped_column(db.Numeric(10, 6))
    infit_mnsq: Mapped[Optional[float]] = mapped_column(db.Numeric(10, 6))
    infit_zstd: Mapped[Optional[float]] = mapped_column(db.Numeric(10, 6))
    
    # Fit interpretation
    fit_status: Mapped[Optional[str]] = mapped_column(
        db.Enum(FitStatus)
    )
    fit_category: Mapped[Optional[str]] = mapped_column(
        db.Enum(FitCategory)
    )
    
    # Difficulty interpretation
    difficulty_level: Mapped[Optional[str]] = mapped_column(
        db.Enum(DifficultyLevel)
    )
    difficulty_percentile: Mapped[Optional[float]] = mapped_column(db.Numeric(5, 2))
    
    # Bloom Taxonomy (cached)
    bloom_level: Mapped[Optional[str]] = mapped_column(
        db.Enum(BloomLevel)
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime, 
        default=get_jakarta_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        db.DateTime, 
        default=get_jakarta_now, 
        onupdate=get_jakarta_now
    )
    
    # Relationships
    analysis = relationship('RaschAnalysis', back_populates='item_measures')
    question = relationship('Question')
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('rasch_analysis_id', 'question_id', 
                        name='uq_rasch_item'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'rasch_analysis_id': self.rasch_analysis_id,
            'question_id': self.question_id,
            'question_text': (self.question.question_text[:100] + '...') 
                           if self.question and self.question.question_text 
                           else None,
            'p_value': float(self.p_value) if self.p_value else None,
            'point_biserial': float(self.point_biserial) if self.point_biserial else None,
            'delta': float(self.delta) if self.delta else None,
            'delta_se': float(self.delta_se) if self.delta_se else None,
            'difficulty_level': self.difficulty_level.value if self.difficulty_level else None,
            'difficulty_percentile': float(self.difficulty_percentile) if self.difficulty_percentile else None,
            'bloom_level': self.bloom_level.value if self.bloom_level else None,
            'outfit_mnsq': float(self.outfit_mnsq) if self.outfit_mnsq else None,
            'infit_mnsq': float(self.infit_mnsq) if self.infit_mnsq else None,
            'fit_status': self.fit_status.value if self.fit_status else None,
        }
    
    def __repr__(self) -> str:
        return f'<RaschItemMeasure Q{self.question_id} δ={self.delta}>'


class RaschThresholdLog(db.Model):
    """
    Log untuk tracking threshold checking.
    
    Setiap kali ada siswa submit quiz, sistem akan check threshold
    dan mencatatnya di tabel ini.
    """
    __tablename__ = 'rasch_threshold_logs'
    
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    rasch_analysis_id: Mapped[int] = mapped_column(
        db.Integer, 
        db.ForeignKey('rasch_analyses.id', ondelete='CASCADE'), 
        nullable=False,
        index=True
    )
    
    # Threshold check
    check_type: Mapped[str] = mapped_column(
        db.Enum(ThresholdCheckType), 
        nullable=False
    )
    num_submissions: Mapped[int] = mapped_column(db.Integer, nullable=False)
    min_required: Mapped[int] = mapped_column(db.Integer, nullable=False)
    threshold_met: Mapped[bool] = mapped_column(db.Boolean, nullable=False)
    
    # Decision
    action_taken: Mapped[Optional[str]] = mapped_column(
        db.Enum(ThresholdAction)
    )
    reason: Mapped[Optional[str]] = mapped_column(db.Text)
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime, 
        default=get_jakarta_now,
        index=True
    )
    
    # Relationships
    analysis = relationship('RaschAnalysis', back_populates='threshold_logs')
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'rasch_analysis_id': self.rasch_analysis_id,
            'check_type': self.check_type.value,
            'num_submissions': self.num_submissions,
            'min_required': self.min_required,
            'threshold_met': self.threshold_met,
            'action_taken': self.action_taken.value if self.action_taken else None,
            'reason': self.reason,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    def __repr__(self) -> str:
        return f'<RaschThresholdLog Analysis:{self.rasch_analysis_id} {self.action_taken}>'


class RaschRatingScale(db.Model):
    """
    Rating scale parameters untuk Partial Credit Model.
    
    Digunakan untuk analisis tugas dengan rubric (multiple criteria).
    Menyimpan threshold parameters (tau) untuk setiap kategori rating.
    """
    __tablename__ = 'rasch_rating_scales'
    
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    rasch_analysis_id: Mapped[int] = mapped_column(
        db.Integer, 
        db.ForeignKey('rasch_analyses.id', ondelete='CASCADE'), 
        nullable=False,
        index=True
    )
    scale_name: Mapped[str] = mapped_column(db.String(100), nullable=False)
    
    # Scale structure
    num_categories: Mapped[int] = mapped_column(
        db.Integer,
        nullable=False
    )
    thresholds: Mapped[Optional[List[float]]] = mapped_column(
        JSON,
        nullable=True
    )

    # Scale statistics
    category_observations: Mapped[Optional[Dict[str, int]]] = mapped_column(
        JSON,
        nullable=True
    )
    category_averages: Mapped[Optional[Dict[str, float]]] = mapped_column(
        JSON,
        nullable=True
    )
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime, 
        default=get_jakarta_now
    )
    
    # Relationships
    analysis = relationship('RaschAnalysis', back_populates='rating_scales')
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            'num_categories >= 2',
            name='chk_rating_categories'
        ),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'rasch_analysis_id': self.rasch_analysis_id,
            'scale_name': self.scale_name,
            'num_categories': self.num_categories,
            'thresholds': self.thresholds,
            'category_observations': self.category_observations,
            'category_averages': self.category_averages,
        }
    
    def __repr__(self) -> str:
        return f'<RaschRatingScale {self.scale_name} ({self.num_categories} categories)>'
