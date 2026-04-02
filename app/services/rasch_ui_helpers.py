"""
Rasch UI Helpers

Transformasi metrik teknis Rasch (Theta, Delta, MNSQ) menjadi format yang ramah untuk guru dan siswa.
Tidak mengubah database - hanya transformasi di layer presentasi.

Fitur:
1. Scaled Score (0-100) dari Theta
2. Warning System untuk Fit Statistics
3. Actionable Insights dari metrik
4. Simplified Wright Map (Zona Penguasaan)
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class WarningLevel(Enum):
    """Level warning untuk fit statistics"""
    NONE = 'none'  # Tidak ada warning
    LOW = 'low'  # Warning rendah (kuning)
    HIGH = 'high'  # Warning tinggi (merah)


class InsightType(Enum):
    """Tipe insight/rekomendasi"""
    STRENGTH = 'strength'  # Kekuatan
    WEAKNESS = 'weakness'  # Kelemahan
    SUGGESTION = 'suggestion'  # Saran perbaikan


@dataclass
class WarningBadge:
    """Badge warning untuk UI"""
    level: WarningLevel
    label: str
    message: str
    color: str  # CSS color class
    icon: str  # Icon name


@dataclass
class Insight:
    """Insight/rekomendasi untuk user"""
    type: InsightType
    title: str
    description: str
    priority: int  # 1-5, 5 = highest


# ============================================================
# 1. SCALED SCORE TRANSFORMATION (0-100)
# ============================================================

def theta_to_scaled_score(theta: float, mean_theta: float = 0, sd_theta: float = 1) -> float:
    """
    Transform Theta (logit) ke Scaled Score (0-100).
    
    Formula: Scaled_Score = 50 + (10 * (theta - mean_theta) / sd_theta)
    
    Default: mean=0, sd=1 menghasilkan:
    - Theta = -3.0 → Score ≈ 20
    - Theta = 0 → Score = 50
    - Theta = +3.0 → Score ≈ 80
    
    Args:
        theta: Ability dalam logit
        mean_theta: Mean ability untuk centering (default: 0)
        sd_theta: Standard deviation untuk scaling (default: 1)
    
    Returns:
        float: Scaled score 0-100 (clamped)
    """
    # Standardize theta
    z_score = (theta - mean_theta) / sd_theta if sd_theta > 0 else theta
    
    # Transform to 0-100 scale
    # Using formula: Score = 50 + 10 * z_score
    scaled_score = 50 + (10 * z_score)
    
    # Clamp to 0-100
    return max(0, min(100, scaled_score))


def delta_to_difficulty_score(delta: float, mean_delta: float = 0, sd_delta: float = 1) -> float:
    """
    Transform Delta (difficulty logit) ke Difficulty Score (0-100).
    
    Note: Higher delta = lebih sulit, jadi kita invert scale
    - Delta = -3.0 (mudah) → Score ≈ 80
    - Delta = 0 → Score = 50
    - Delta = +3.0 (sulit) → Score ≈ 20
    
    Args:
        delta: Difficulty dalam logit
        mean_delta: Mean difficulty (default: 0)
        sd_delta: Standard deviation (default: 1)
    
    Returns:
        float: Difficulty score 0-100 (clamped)
    """
    z_score = (delta - mean_delta) / sd_delta if sd_delta > 0 else delta
    # Invert: higher delta = lower score (lebih sulit)
    difficulty_score = 50 - (10 * z_score)
    return max(0, min(100, difficulty_score))


def format_scaled_score(theta: float, context: Dict = None) -> Dict:
    """
    Format theta menjadi scaled score dengan interpretasi.
    
    Returns:
        dict: {
            'scaled_score': float,
            'grade': str,
            'category': str,
            'description': str,
            'color_class': str
        }
    """
    if context is None:
        context = {}
    
    mean_theta = context.get('mean_theta', 0)
    sd_theta = context.get('sd_theta', 1)
    
    scaled_score = theta_to_scaled_score(theta, mean_theta, sd_theta)
    scaled_score_rounded = round(scaled_score, 1)
    
    # Determine grade and category
    if scaled_score >= 80:
        grade = 'A'
        category = 'Sangat Baik'
        description = 'Kemampuan sangat tinggi di atas rata-rata'
        color_class = 'success'  # Green
    elif scaled_score >= 70:
        grade = 'B'
        category = 'Baik'
        description = 'Kemampuan di atas rata-rata'
        color_class = 'info'  # Blue
    elif scaled_score >= 60:
        grade = 'C'
        category = 'Cukup'
        description = 'Kemampuan rata-rata'
        color_class = 'warning'  # Yellow
    elif scaled_score >= 50:
        grade = 'D'
        category = 'Kurang'
        description = 'Kemampuan di bawah rata-rata, perlu peningkatan'
        color_class = 'danger'  # Red
    else:
        grade = 'E'
        category = 'Sangat Kurang'
        description = 'Kemampuan sangat rendah, butuh perhatian khusus'
        color_class = 'danger-dark'  # Dark Red
    
    return {
        'scaled_score': scaled_score_rounded,
        'grade': grade,
        'category': category,
        'description': description,
        'color_class': color_class,
        'original_theta': round(theta, 3),
    }


# ============================================================
# 2. WARNING SYSTEM FOR FIT STATISTICS
# ============================================================

def get_person_fit_warning(outfit_mnsq: float, infit_mnsq: float) -> WarningBadge:
    """
    Dapatkan warning badge untuk fit statistics siswa.
    
    Interpretasi:
    - MNSQ > 1.5: UNDERFIT → "Indikasi Menebak / Inkonsisten"
    - MNSQ < 0.5: OVERFIT → "Terlalu Identik / Menghafal"
    - 0.5 <= MNSQ <= 1.5: WELL_FITTED → Tidak ada warning
    
    Args:
        outfit_mnsq: Outfit MNSQ value
        infit_mnsq: Infit MNSQ value
    
    Returns:
        WarningBadge: Badge untuk ditampilkan di UI
    """
    # Use outfit as primary indicator (more sensitive to unexpected responses)
    mnsq = outfit_mnsq
    
    if mnsq > 1.5:
        return WarningBadge(
            level=WarningLevel.HIGH,
            label='UNDERFIT',
            message='Indikasi menebak atau jawaban inkonsisten',
            color='badge-danger',
            icon='alert-triangle'
        )
    elif mnsq < 0.5:
        return WarningBadge(
            level=WarningLevel.LOW,
            label='OVERFIT',
            message='Pola jawaban terlalu identik (menghafal?)',
            color='badge-warning',
            icon='alert-circle'
        )
    else:
        return WarningBadge(
            level=WarningLevel.NONE,
            label='VALID',
            message='Pola jawaban konsisten dan valid',
            color='badge-success',
            icon='check-circle'
        )


def get_item_fit_warning(outfit_mnsq: float, infit_mnsq: float) -> WarningBadge:
    """
    Dapatkan warning badge untuk fit statistics soal.
    
    Interpretasi:
    - MNSQ > 1.5: UNDERFIT → "Soal Ambigu / Menjebak"
    - MNSQ < 0.5: OVERFIT → "Soal Terlalu Mudah Diprediksi"
    - 0.5 <= MNSQ <= 1.5: WELL_FITTED → Soal baik
    
    Args:
        outfit_mnsq: Outfit MNSQ value
        infit_mnsq: Infit MNSQ value
    
    Returns:
        WarningBadge: Badge untuk ditampilkan di UI
    """
    mnsq = outfit_mnsq
    
    if mnsq > 1.5:
        return WarningBadge(
            level=WarningLevel.HIGH,
            label='UNDERFIT',
            message='Soal ambigu atau menjebak - perlu review',
            color='badge-danger',
            icon='alert-triangle'
        )
    elif mnsq < 0.5:
        return WarningBadge(
            level=WarningLevel.LOW,
            label='OVERFIT',
            message='Soal terlalu mudah diprediksi',
            color='badge-warning',
            icon='alert-circle'
        )
    else:
        return WarningBadge(
            level=WarningLevel.NONE,
            label='BAIK',
            message='Soal berfungsi dengan baik',
            color='badge-success',
            icon='check-circle'
        )


def format_item_difficulty(delta: float, p_value: float) -> Dict:
    """
    Format difficulty menjadi interpretasi yang mudah dipahami.
    
    Args:
        delta: Difficulty logit
        p_value: Classical p-value (proportion correct)
    
    Returns:
        dict: {
            'difficulty_label': str,
            'difficulty_description': str,
            'color_class': str,
            'icon': str
        }
    """
    # Use p-value for more intuitive interpretation
    if p_value >= 0.8:
        label = 'Mudah'
        description = 'Lebih dari 80% siswa menjawab benar'
        color = 'success'
        icon = 'arrow-down'
    elif p_value >= 0.6:
        label = 'Sedang'
        description = '60-80% siswa menjawab benar'
        color = 'info'
        icon = 'minus'
    elif p_value >= 0.4:
        label = 'Cukup Sulit'
        description = '40-60% siswa menjawab benar'
        color = 'warning'
        icon = 'arrow-up'
    elif p_value >= 0.2:
        label = 'Sulit'
        description = '20-40% siswa menjawab benar'
        color = 'danger'
        icon = 'arrow-up'
    else:
        label = 'Sangat Sulit'
        description = 'Kurang dari 20% siswa menjawab benar'
        color = 'danger-dark'
        icon = 'arrow-up'
    
    return {
        'difficulty_label': label,
        'difficulty_description': description,
        'color_class': color,
        'icon': icon,
        'p_value': round(p_value, 3),
        'delta': round(delta, 3),
    }


# ============================================================
# 3. ACTIONABLE INSIGHTS GENERATOR
# ============================================================

def generate_person_insights(
    theta: float,
    outfit_mnsq: float,
    theta_se: float,
    percentile: float,
    ability_level: str
) -> List[Insight]:
    """
    Generate insights untuk siswa berdasarkan measure-nya.
    
    Args:
        theta: Ability logit
        outfit_mnsq: Outfit MNSQ
        theta_se: Standard error
        percentile: Percentile rank
        ability_level: Ability level category
    
    Returns:
        List[Insight]: List insights yang actionable
    """
    insights = []
    
    # Insight based on ability level
    if ability_level in ['very_high', 'high']:
        insights.append(Insight(
            type=InsightType.STRENGTH,
            title='Kemampuan Tinggi',
            description='Siswa menunjukkan pemahaman yang sangat baik. Pertimbangkan untuk memberikan tantangan tambahan.',
            priority=4
        ))
    elif ability_level in ['very_low', 'low']:
        insights.append(Insight(
            type=InsightType.WEAKNESS,
            title='Perlu Perhatian',
            description='Siswa membutuhkan bantuan tambahan. Identifikasi topik yang belum dikuasai.',
            priority=5
        ))
    
    # Insight based on fit
    if outfit_mnsq > 1.5:
        insights.append(Insight(
            type=InsightType.SUGGESTION,
            title='Pola Jawaban Tidak Konsisten',
            description='Cek apakah siswa menebak atau ada faktor lain yang mempengaruhi jawaban.',
            priority=4
        ))
    elif outfit_mnsq < 0.5:
        insights.append(Insight(
            type=InsightType.SUGGESTION,
            title='Pola Jawaban Terlalu Terprediksi',
            description='Siswa mungkin menghafal pola jawaban. Pastikan pemahaman konseptual.',
            priority=3
        ))
    
    # Insight based on measurement precision
    if theta_se > 0.5:
        insights.append(Insight(
            type=InsightType.SUGGESTION,
            title='Pengukuran Kurang Presisi',
            description=f'Standard error tinggi ({theta_se:.2f}). Pertimbangkan lebih banyak soal untuk pengukuran yang lebih akurat.',
            priority=2
        ))
    
    # Insight based on percentile
    if percentile < 25:
        insights.append(Insight(
            type=InsightType.SUGGESTION,
            title='Di Bawah Rata-Rata Kelas',
            description=f'Siswa berada di {percentile:.0f}th percentile. Rekomendasi: tutoring atau belajar kelompok.',
            priority=4
        ))
    elif percentile > 75:
        insights.append(Insight(
            type=InsightType.STRENGTH,
            title='Di Atas Rata-Rata Kelas',
            description=f'Siswa berada di {percentile:.0f}th percentile. Dapat menjadi tutor sebaya.',
            priority=3
        ))
    
    # Sort by priority
    insights.sort(key=lambda x: x.priority, reverse=True)
    
    return insights


def generate_item_insights(
    delta: float,
    p_value: float,
    point_biserial: float,
    outfit_mnsq: float,
    bloom_level: Optional[str] = None
) -> List[Insight]:
    """
    Generate insights untuk soal berdasarkan measure-nya.
    
    Args:
        delta: Difficulty logit
        p_value: Classical p-value
        point_biserial: Discrimination index
        outfit_mnsq: Outfit MNSQ
        bloom_level: Bloom taxonomy level
    
    Returns:
        List[Insight]: List insights yang actionable
    """
    insights = []
    
    # Insight based on difficulty
    if p_value < 0.2:
        insights.append(Insight(
            type=InsightType.SUGGESTION,
            title='Soal Sangat Sulit',
            description=f'Hanya {p_value*100:.0f}% siswa yang menjawab benar. Review apakah soal terlalu sulit atau ada kesalahan.',
            priority=4
        ))
    elif p_value > 0.9:
        insights.append(Insight(
            type=InsightType.SUGGESTION,
            title='Soal Sangat Mudah',
            description=f'{p_value*100:.0f}% siswa menjawab benar. Pertimbangkan untuk meningkatkan kesulitan.',
            priority=2
        ))
    
    # Insight based on discrimination
    if point_biserial < 0.2:
        insights.append(Insight(
            type=InsightType.WEAKNESS,
            title='Daya Beda Rendah',
            description=f'Point-biserial {point_biserial:.2f}. Soal ini tidak membedakan siswa pintar dan kurang.',
            priority=4
        ))
    elif point_biserial > 0.4:
        insights.append(Insight(
            type=InsightType.STRENGTH,
            title='Daya Beda Baik',
            description=f'Point-biserial {point_biserial:.2f}. Soal ini efektif membedakan kemampuan siswa.',
            priority=3
        ))
    
    # Insight based on fit
    if outfit_mnsq > 1.5:
        insights.append(Insight(
            type=InsightType.WEAKNESS,
            title='Soal Bermasalah',
            description='Soal tidak fit dengan model Rasch. Mungkin ambigu, menjebak, atau ada kunci jawaban salah.',
            priority=5
        ))
    
    # Insight based on Bloom level
    if bloom_level in ['analyze', 'evaluate', 'create']:
        if p_value < 0.3:
            insights.append(Insight(
                type=InsightType.SUGGESTION,
                title='HOTS Terlalu Sulit',
                description='Soal higher-order thinking ini terlalu sulit. Pertimbangkan scaffolding atau soal perantara.',
                priority=3
            ))
    
    # Sort by priority
    insights.sort(key=lambda x: x.priority, reverse=True)
    
    return insights


def generate_quiz_insights(
    cronbach_alpha: float,
    person_separation: float,
    item_separation: float,
    num_persons: int,
    num_items: int
) -> List[Insight]:
    """
    Generate insights untuk keseluruhan quiz.
    
    Args:
        cronbach_alpha: Reliability index
        person_separation: Person separation index
        item_separation: Item separation index
        num_persons: Number of students
        num_items: Number of items
    
    Returns:
        List[Insight]: List insights untuk quiz
    """
    insights = []
    
    # Reliability insight
    if cronbach_alpha >= 0.8:
        insights.append(Insight(
            type=InsightType.STRENGTH,
            title='Reliabilitas Sangat Baik',
            description=f'Cronbach's alpha {cronbach_alpha:.2f}. Kuis ini konsisten dan dapat diandalkan.',
            priority=4
        ))
    elif cronbach_alpha >= 0.7:
        insights.append(Insight(
            type=InsightType.STRENGTH,
            title='Reliabilitas Baik',
            description=f'Cronbach's alpha {cronbach_alpha:.2f}. Kuis ini cukup andal untuk penilaian.',
            priority=3
        ))
    elif cronbach_alpha >= 0.6:
        insights.append(Insight(
            type=InsightType.WEAKNESS,
            title='Reliabilitas Cukup',
            description=f'Cronbach's alpha {cronbach_alpha:.2f}. Pertimbangkan menambah atau memperbaiki soal.',
            priority=3
        ))
    else:
        insights.append(Insight(
            type=InsightType.WEAKNESS,
            title='Reliabilitas Rendah',
            description=f'Cronbach's alpha {cronbach_alpha:.2f}. Kuis perlu direvisi signifikan.',
            priority=5
        ))
    
    # Person separation insight
    if person_separation >= 2.0:
        insights.append(Insight(
            type=InsightType.STRENGTH,
            title='Daya Beda Siswa Baik',
            description=f'Person separation {person_separation:.2f}. Kuis dapat membedakan level kemampuan siswa dengan baik.',
            priority=3
        ))
    elif person_separation < 1.0:
        insights.append(Insight(
            type=InsightType.SUGGESTION,
            title='Daya Beda Siswa Rendah',
            description=f'Person separation {person_separation:.2f}. Tambah soal dengan variasi kesulitan.',
            priority=4
        ))
    
    # Item separation insight
    if item_separation >= 3.0:
        insights.append(Insight(
            type=InsightType.STRENGTH,
            title='Hierarki Soal Jelas',
            description=f'Item separation {item_separation:.2f}. Urutan kesulitan soal sangat konsisten.',
            priority=3
        ))
    
    # Sample size insight
    if num_persons < 30:
        insights.append(Insight(
            type=InsightType.SUGGESTION,
            title='Sampel Kecil',
            description=f'Hanya {num_persons} siswa. Hasil analisis mungkin kurang stabil. Tunggu lebih banyak submission.',
            priority=3
        ))
    
    # Test length insight
    if num_items < 10:
        insights.append(Insight(
            type=InsightType.SUGGESTION,
            title='Kuis Terlalu Pendek',
            description=f'Hanya {num_items} soal. Pertimbangkan menambah soal untuk pengukuran lebih akurat.',
            priority=3
        ))
    elif num_items > 50:
        insights.append(Insight(
            type=InsightType.SUGGESTION,
            title='Kuis Terlalu Panjang',
            description=f'{num_items} soal mungkin terlalu melelahkan. Pertimbangkan untuk memecah kuis.',
            priority=2
        ))
    
    # Sort by priority
    insights.sort(key=lambda x: x.priority, reverse=True)
    
    return insights


# ============================================================
# 4. SIMPLIFIED WRIGHT MAP (ZONA PENGUASAAN)
# ============================================================

def get_mastery_zone(theta: float, item_deltas: List[float]) -> Dict:
    """
    Tentukan zona penguasaan siswa berdasarkan ability vs difficulty.
    
    Args:
        theta: Student ability
        item_deltas: List of item difficulties
    
    Returns:
        dict: {
            'mastery_zone': str,
            'mastered_count': int,
            'ready_count': int,
            'challenge_count': int,
            'too_hard_count': int,
            'recommendation': str
        }
    """
    if not item_deltas:
        return {
            'mastery_zone': 'unknown',
            'mastered_count': 0,
            'ready_count': 0,
            'challenge_count': 0,
            'too_hard_count': 0,
            'recommendation': 'Tidak ada data soal untuk analisis'
        }
    
    mastered = 0  # theta - delta > 2.0 (prob > 88%)
    ready = 0     # theta - delta 0.5 to 2.0 (prob 62-88%)
    challenge = 0 # theta - delta -0.5 to 0.5 (prob 38-62%)
    too_hard = 0  # theta - delta < -0.5 (prob < 38%)
    
    for delta in item_deltas:
        diff = theta - delta
        
        if diff > 2.0:
            mastered += 1
        elif diff > 0.5:
            ready += 1
        elif diff > -0.5:
            challenge += 1
        else:
            too_hard += 1
    
    total = len(item_deltas)
    mastered_pct = mastered / total * 100
    
    # Determine overall zone
    if mastered_pct >= 80:
        zone = 'mastered'
        zone_label = 'Sudah Dikuasai'
        zone_color = 'success'
        recommendation = 'Siswa siap untuk materi yang lebih menantang.'
    elif mastered_pct >= 50:
        zone = 'developing'
        zone_label = 'Dalam Pengembangan'
        zone_color = 'info'
        recommendation = 'Fokus pada soal-soal di zona challenge untuk peningkatan optimal.'
    elif mastered_pct >= 30:
        zone = 'learning'
        zone_label = 'Sedang Belajar'
        zone_color = 'warning'
        recommendation = 'Perkuat pemahaman konsep dasar sebelum lanjut ke materi sulit.'
    else:
        zone = 'struggling'
        zone_label = 'Membutuhkan Bantuan'
        zone_color = 'danger'
        recommendation = 'Siswa membutuhkan scaffolding dan bantuan intensif.'
    
    return {
        'mastery_zone': zone,
        'mastery_zone_label': zone_label,
        'mastery_zone_color': zone_color,
        'mastered_count': mastered,
        'ready_count': ready,
        'challenge_count': challenge,
        'too_hard_count': too_hard,
        'mastered_percentage': round(mastered_pct, 1),
        'recommendation': recommendation,
    }


def create_simplified_wright_map(
    person_thetas: List[float],
    item_deltas: List[float],
    mean_theta: float = 0,
    sd_theta: float = 1
) -> Dict:
    """
    Buat Wright Map yang disederhanakan menjadi Zona Penguasaan.
    
    Args:
        person_thetas: List of student abilities
        item_deltas: List of item difficulties
        mean_theta: Mean for scaling
        sd_theta: SD for scaling
    
    Returns:
        dict: Simplified Wright Map data
    """
    # Create bands
    bands = {
        'very_high': {'label': 'Sangat Tinggi', 'range': '> 70', 'students': 0, 'items': 0, 'color': 'success'},
        'high': {'label': 'Tinggi', 'range': '60-70', 'students': 0, 'items': 0, 'color': 'info'},
        'medium': {'label': 'Sedang', 'range': '40-60', 'students': 0, 'items': 0, 'color': 'warning'},
        'low': {'label': 'Rendah', 'range': '30-40', 'students': 0, 'items': 0, 'color': 'danger'},
        'very_low': {'label': 'Sangat Rendah', 'range': '< 30', 'students': 0, 'items': 0, 'color': 'danger-dark'},
    }
    
    # Count students
    for theta in person_thetas:
        score = theta_to_scaled_score(theta, mean_theta, sd_theta)
        if score >= 70:
            bands['very_high']['students'] += 1
        elif score >= 60:
            bands['high']['students'] += 1
        elif score >= 40:
            bands['medium']['students'] += 1
        elif score >= 30:
            bands['low']['students'] += 1
        else:
            bands['very_low']['students'] += 1
    
    # Count items
    for delta in item_deltas:
        score = delta_to_difficulty_score(delta, mean_theta, sd_theta)
        if score >= 70:  # Easy items
            bands['very_high']['items'] += 1
        elif score >= 60:
            bands['high']['items'] += 1
        elif score >= 40:
            bands['medium']['items'] += 1
        elif score >= 30:
            bands['low']['items'] += 1
        else:  # Hard items
            bands['very_low']['items'] += 1
    
    # Generate summary
    total_students = len(person_thetas)
    total_items = len(item_deltas)
    
    summary = []
    for key, data in bands.items():
        summary.append({
            'level': key,
            'label': data['label'],
            'range': data['range'],
            'student_count': data['students'],
            'student_percentage': round(data['students'] / total_students * 100, 1) if total_students > 0 else 0,
            'item_count': data['items'],
            'item_percentage': round(data['items'] / total_items * 100, 1) if total_items > 0 else 0,
            'color': data['color'],
        })
    
    return {
        'bands': summary,
        'total_students': total_students,
        'total_items': total_items,
        'mean_scaled_score': round(theta_to_scaled_score(mean_theta, mean_theta, sd_theta), 1),
    }
