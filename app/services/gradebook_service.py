"""
Gradebook Service - Handles grade calculations and data management
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from sqlalchemy import func
from app.extensions import db
from app.models import (
    Course, User, Quiz, QuizSubmission, QuizStatus,
    GradeCategory, GradeCategoryType, LearningObjective, LearningGoal,
    GradeItem, GradeEntry
)
from app.helpers import get_jakarta_now


def calculate_final_grade(student_id: int, course_id: int, use_category_weighting: bool = True) -> float:
    """
    Calculate final grade for a student in a course.
    
    This is the unified function used by both teacher and student views.
    
    Args:
        student_id: Student user ID
        course_id: Course ID
        use_category_weighting: If True, use category weighting. If False, use simple average.
    
    Returns:
        Final grade as a percentage (0-100)
    """
    if use_category_weighting:
        # Use category weighting (teacher view)
        categories = GradeCategory.query.filter_by(course_id=course_id).all()
        
        if not categories:
            # No categories defined, fall back to simple average
            use_category_weighting = False
    
    if not use_category_weighting:
        # Simple average of all graded items (student view fallback)
        all_items = GradeItem.query.filter_by(course_id=course_id).all()
        all_percentages = []
        
        for item in all_items:
            entry = GradeEntry.query.filter_by(
                grade_item_id=item.id,
                student_id=student_id
            ).first()
            if entry and entry.percentage is not None:
                all_percentages.append(entry.percentage)
        
        return round(sum(all_percentages) / len(all_percentages), 2) if all_percentages else 0.0
    
    # Category-weighted calculation
    total_weighted_score = 0.0
    total_weight = 0.0

    for category in categories:
        category_data = calculate_category_grade(student_id, category.id)
        if category_data['weight'] > 0:
            total_weighted_score += category_data['weighted_score']
            total_weight += category_data['weight']

    # Return as percentage (0-100), not ratio (0-1)
    return round((total_weighted_score / total_weight) * 100, 2) if total_weight > 0 else 0.0


def calculate_student_grade(student_id: int, course_id: int) -> Dict:
    """
    Calculate final grade for a student in a course
    Returns dict with category breakdown and final grade
    """
    # Get all grade categories for the course
    categories = GradeCategory.query.filter_by(course_id=course_id).all()

    result = {
        'student_id': student_id,
        'course_id': course_id,
        'categories': {},
        'final_grade': 0.0,
        'total_weight': 0.0,
    }

    total_weighted_score = 0.0
    total_weight = 0.0

    for category in categories:
        category_data = calculate_category_grade(student_id, category.id)
        if category_data['weight'] > 0:
            result['categories'][category.category_type.value] = category_data
            total_weighted_score += category_data['weighted_score']
            total_weight += category_data['weight']

    if total_weight > 0:
        result['final_grade'] = round((total_weighted_score / total_weight) * 100, 2)
        result['total_weight'] = total_weight

    return result


def calculate_category_grade(student_id: int, category_id: int) -> Dict:
    """
    Calculate grade for a specific category
    
    Handles 3 scenarios:
    1. All items weight=0 → simple average (all items count equally)
    2. All items weight>0 → weighted average (items count by their weight)
    3. Mixed (some 0, some >0) → hybrid: items with weight use weight, items without weight use simple average
    """
    category = GradeCategory.query.get(category_id)
    if not category:
        return {'score': 0, 'weight': 0, 'weighted_score': 0}

    # Get all grade items in this category
    grade_items = GradeItem.query.filter_by(category_id=category_id).all()

    total_score = 0.0
    total_max_score = 0.0
    items_count = 0

    # Check weight distribution
    all_zero_weight = all(item.weight == 0 for item in grade_items)
    all_nonzero_weight = all(item.weight > 0 for item in grade_items)
    has_mixed_weights = not all_zero_weight and not all_nonzero_weight

    for item in grade_items:
        entry = GradeEntry.query.filter_by(
            grade_item_id=item.id,
            student_id=student_id
        ).first()

        if entry and entry.score is not None:
            # Normalize to percentage
            percentage = entry.percentage if entry.percentage else (entry.score / item.max_score * 100) if item.max_score > 0 else 0
            
            if all_zero_weight:
                # Scenario 1: Simple average - all items count equally
                total_score += percentage
                total_max_score += 100
            elif all_nonzero_weight:
                # Scenario 2: Weighted average - items count by their weight
                total_score += percentage * (item.weight / 100)
                total_max_score += item.weight
            else:
                # Scenario 3: Mixed - hybrid approach
                # Items with explicit weight use their weight
                # Items without weight (weight=0) are treated as equal-weight items
                if item.weight > 0:
                    total_score += percentage * (item.weight / 100)
                    total_max_score += item.weight
                else:
                    # For mixed scenario, items without weight get equal share of remaining weight
                    # Example: if quiz has weight=100, manual items share the remaining 0
                    # We treat weight=0 items as having equal weight among themselves
                    total_score += percentage
                    total_max_score += 100
            
            items_count += 1

    # Calculate category average
    category_score = (total_score / total_max_score * 100) if total_max_score > 0 else 0

    return {
        'category_id': category_id,
        'category_name': category.name,
        'category_type': category.category_type.value,
        'score': round(category_score, 2),
        'weight': category.weight,
        'weighted_score': round(category_score * category.weight / 100, 2),
        'items_count': items_count,
    }


def calculate_course_statistics(course_id: int) -> Dict:
    """
    Calculate statistics for all students in a course
    """
    course = Course.query.get(course_id)
    if not course:
        return {}
    
    # Get all students enrolled in the course
    students = course.students.all()
    
    stats = {
        'course_id': course_id,
        'course_name': course.name,
        'students_count': len(students),
        'grades': [],
        'average_grade': 0.0,
        'highest_grade': 0.0,
        'lowest_grade': 100.0,
    }
    
    all_grades = []
    
    for student in students:
        final_grade = calculate_final_grade(student.id, course_id, use_category_weighting=True)
        if final_grade > 0:
            all_grades.append(final_grade)
            stats['grades'].append({
                'student_id': student.id,
                'student_name': student.name,
                'final_grade': round(final_grade, 2),
            })
    
    if all_grades:
        stats['average_grade'] = round(sum(all_grades) / len(all_grades), 2)
        stats['highest_grade'] = round(max(all_grades), 2)
        stats['lowest_grade'] = round(min(all_grades), 2)
    
    return stats


def import_quiz_to_gradebook(quiz_id: int, category_id: int, learning_goal_id: Optional[int] = None) -> Tuple[Optional[GradeItem], Optional[str]]:
    """
    Import quiz scores to gradebook
    Creates a GradeItem and GradeEntries from quiz submissions
    """
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return None, 'Quiz tidak ditemukan'
    
    category = GradeCategory.query.get(category_id)
    if not category:
        return None, 'Kategori tidak ditemukan'
    
    # Check if grade item already exists for this quiz
    existing_item = GradeItem.query.filter_by(quiz_id=quiz_id).first()
    if existing_item:
        return None, 'Quiz sudah diimpor ke buku nilai'
    
    # Create grade item
    grade_item = GradeItem(
        name=f"Quiz: {quiz.name}",
        description=quiz.description,
        category_id=category_id,
        learning_goal_id=learning_goal_id,
        max_score=quiz.points,
        weight=100.0,  # Default weight, can be adjusted later
        course_id=quiz.course_id,
        quiz_id=quiz_id,
        due_date=quiz.created_at,
    )
    db.session.add(grade_item)
    db.session.flush()
    
    # Import quiz submissions as grade entries
    submissions = QuizSubmission.query.filter_by(quiz_id=quiz_id).all()
    
    for submission in submissions:
        percentage = (submission.score / submission.total_points * 100) if submission.total_points > 0 else 0
        
        grade_entry = GradeEntry(
            grade_item_id=grade_item.id,
            student_id=submission.user_id,
            score=submission.score,
            percentage=percentage,
            graded_at=submission.submitted_at,
            graded_by=quiz.course.teacher_id,
        )
        db.session.add(grade_entry)
    
    db.session.commit()
    
    return grade_item, None


def sync_quiz_grades(quiz_id: int) -> int:
    """
    Sync quiz submission scores with gradebook.
    Respects manual_override flag - will not overwrite manually adjusted grades.
    
    Returns number of entries updated.
    """
    grade_item = GradeItem.query.filter_by(quiz_id=quiz_id).first()
    if not grade_item:
        return 0

    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return 0

    updated_count = 0
    submissions = QuizSubmission.query.filter_by(quiz_id=quiz_id).all()

    for submission in submissions:
        entry = GradeEntry.query.filter_by(
            grade_item_id=grade_item.id,
            student_id=submission.user_id
        ).first()

        if entry:
            # Skip if this grade was manually overridden by teacher
            if entry.manual_override:
                continue
            
            percentage = (submission.score / submission.total_points * 100) if submission.total_points > 0 else 0
            entry.score = submission.score
            entry.percentage = percentage
            entry.graded_at = submission.submitted_at
            updated_count += 1
        else:
            # Create new entry if doesn't exist
            percentage = (submission.score / submission.total_points * 100) if submission.total_points > 0 else 0
            entry = GradeEntry(
                grade_item_id=grade_item.id,
                student_id=submission.user_id,
                score=submission.score,
                percentage=percentage,
                graded_at=submission.submitted_at,
                graded_by=quiz.course.teacher_id,
                manual_override=False,  # New entries from sync are not overridden
            )
            db.session.add(entry)
            updated_count += 1

    db.session.commit()
    return updated_count


def get_predicate(grade: float) -> Dict:
    """
    Get predicate letter and label based on standard grade intervals.
    A >= 90: Sangat Baik
    B >= 80: Baik
    C >= 70: Cukup
    D < 70: Kurang
    """
    if grade >= 90:
        return {'letter': 'A', 'label': 'Sangat Baik'}
    elif grade >= 80:
        return {'letter': 'B', 'label': 'Baik'}
    elif grade >= 70:
        return {'letter': 'C', 'label': 'Cukup'}
    else:
        return {'letter': 'D', 'label': 'Kurang'}


def get_mastery_status(grade: float) -> str:
    """
    Get mastery status message based on grade predicate.
    """
    if grade >= 90:
        return 'Kamu mampu menguasai materi ini'
    elif grade >= 80:
        return 'Kamu cukup mampu menguasai materi ini'
    elif grade >= 70:
        return 'Kamu cukup untuk menguasai materi ini'
    else:
        return 'Kamu belum menguasai materi ini'


def needs_remedial(grade: float, kkm: float = 70.0) -> bool:
    """
    Check if student needs remedial based on KKM threshold.
    
    Args:
        grade: Student's grade (0-100)
        kkm: Minimum passing grade (default: 70)
    
    Returns:
        True if grade < KKM (needs remedial)
    """
    return grade < kkm


def get_remedial_label(grade: float, kkm: float = 70.0) -> str:
    """
    Get remedial status label.
    
    Args:
        grade: Student's grade (0-100)
        kkm: Minimum passing grade (default: 70)
    
    Returns:
        Label indicating remedial status
    """
    if grade >= kkm:
        return 'Tuntas'
    else:
        return 'Perlu Remedial'


def generate_report_description(student_name: str, course_name: str, final_grade: float, 
                                category_breakdown: Dict = None, strengths: list = None, 
                                improvements: list = None) -> str:
    """
    Generate smart report card description based on student performance.
    
    Args:
        student_name: Student name
        course_name: Course name
        final_grade: Final grade (0-100)
        category_breakdown: Dict with category scores {'formatif': 85, 'sumatif': 90, ...}
        strengths: List of strong areas
        improvements: List of areas needing improvement
    
    Returns:
        Generated description text (Indonesian)
    """
    # Determine performance level
    if final_grade >= 90:
        level = 'excellent'
    elif final_grade >= 80:
        level = 'good'
    elif final_grade >= 70:
        level = 'satisfactory'
    elif final_grade >= 60:
        level = 'developing'
    else:
        level = 'needs_support'
    
    # Templates for each performance level
    templates = {
        'excellent': [
            f"{student_name} menunjukkan performa yang sangat baik dalam {course_name}. "
            "Siswa ini konsisten mencapai hasil terbaik dan memahami konsep dengan mendalam.",
            
            f"Ananda {student_name} meraih pencapaian luar biasa di mata pelajaran {course_name}. "
            "Kemampuan analisis dan pemahaman konsep sangat mengesankan.",
            
            f"{student_name} adalah siswa berprestasi tinggi dalam {course_name}. "
            "Konsistensi dan dedikasi yang ditunjukkan patut menjadi contoh."
        ],
        'good': [
            f"{student_name} menunjukkan performa yang baik dalam {course_name}. "
            "Dengan terus meningkatkan konsistensi, potensi untuk mencapai hasil lebih baik sangat besar.",
            
            f"Ananda {student_name} telah menunjukkan kemajuan yang baik di {course_name}. "
            "Pertahankan semangat belajar dan tingkatkan latihan untuk hasil yang lebih optimal.",
            
            f"{student_name} memiliki pemahaman yang baik terhadap materi {course_name}. "
            "Teruslah berlatih dan jangan ragu untuk bertanya ketika ada kesulitan."
        ],
        'satisfactory': [
            f"{student_name} mencapai hasil yang cukup dalam {course_name}. "
            "Diperlukan peningkatan konsistensi belajar dan lebih banyak latihan untuk memperbaiki pemahaman.",
            
            f"Ananda {student_name} sudah memahami konsep dasar {course_name} dengan cukup baik. "
            "Tingkatkan frekuensi belajar dan manfaatkan waktu untuk latihan tambahan.",
            
            f"{student_name} menunjukkan pemahaman yang memadai dalam {course_name}. "
            "Fokus pada area yang masih sulit dan perbanyak latihan soal akan membantu peningkatan."
        ],
        'developing': [
            f"{student_name} masih dalam tahap pengembangan pemahaman {course_name}. "
            "Diperlukan bimbingan tambahan dan latihan lebih intensif untuk menguasai konsep dasar.",
            
            f"Ananda {student_name} perlu meningkatkan usaha belajar di {course_name}. "
            "Disarankan mengikuti sesi bimbingan dan memperbanyak latihan untuk memperkuat pemahaman.",
            
            f"{student_name} menunjukkan perkembangan yang masih perlu ditingkatkan dalam {course_name}. "
            "Konsistensi belajar dan perhatian lebih pada materi dasar sangat penting."
        ],
        'needs_support': [
            f"{student_name} memerlukan dukungan tambahan dalam {course_name}. "
            "Sangat disarankan untuk mengikuti program remedial dan bimbingan intensif.",
            
            f"Ananda {student_name} perlu perhatian khusus di mata pelajaran {course_name}. "
            "Kolaborasi antara guru, siswa, dan orang tua diperlukan untuk meningkatkan hasil belajar.",
            
            f"{student_name} menghadapi tantangan dalam {course_name}. "
            "Pendekatan belajar yang berbeda dan bimbingan individual akan sangat membantu."
        ]
    }
    
    # Select template based on level
    import random
    base_description = random.choice(templates[level])
    
    # Add specific feedback if category breakdown provided
    specific_feedback = ""
    if category_breakdown:
        formatif = category_breakdown.get('formatif', 0)
        sumatif = category_breakdown.get('sumatif', 0)
        sikap = category_breakdown.get('sikap', 0)
        
        if formatif > 0 and formatif < 70:
            specific_feedback += " Perlu peningkatan pada penilaian formatif."
        if sumatif > 0 and sumatif < 70:
            specific_feedback += " Perlu penguatan pada penilaian sumatif."
        if sikap > 0 and sikap < 70:
            specific_feedback += " Perlu perhatian pada aspek sikap."
    
    # Add strengths if provided
    if strengths:
        strength_text = " Kelebihan: " + ", ".join(strengths[:3]) + "."
        base_description += strength_text
    
    # Add improvements if provided
    if improvements:
        improvement_text = " Area perbaikan: " + ", ".join(improvements[:3]) + "."
        base_description += improvement_text
    
    return base_description + specific_feedback


def get_student_grades_summary(student_id: int, course_id: int) -> Dict:
    """
    Get comprehensive grade summary for a student.
    Uses unified calculate_final_grade() for consistent calculation.
    Includes predicate (A/B/C/D) and mastery status for each learning objective.
    """
    course = Course.query.get(course_id)
    if not course:
        return {}

    # Check if student is enrolled
    students_list = course.students.all() if hasattr(course.students, 'all') else course.students
    if course.teacher_id != student_id and student_id not in [s.id for s in students_list]:
        return {}

    # ── Collect ALL grade items for this course ──────────────────────
    all_items = GradeItem.query.filter_by(course_id=course_id).all()

    items_list = []
    all_percentages = []

    for item in all_items:
        entry = GradeEntry.query.filter_by(
            grade_item_id=item.id,
            student_id=student_id
        ).first()

        item_data = {
            'item_id': item.id,
            'item_name': item.name,
            'score': entry.score if entry else None,
            'max_score': item.max_score,
            'percentage': entry.percentage if entry else None,
            'feedback': entry.feedback if entry else None,
            'graded_at': entry.graded_at.strftime('%Y-%m-%d') if entry and entry.graded_at else None,
            'category_name': item.category.name if item.category else 'Umum',
            'is_quiz': item.quiz_id is not None,
            'is_assignment': item.assignment_id is not None,
        }
        items_list.append(item_data)

        if entry and entry.percentage is not None:
            all_percentages.append(entry.percentage)

    # ── Calculate final grade using unified function ─────────────────
    # Student view uses simple average (no category weighting)
    final_grade = calculate_final_grade(student_id, course_id, use_category_weighting=False)
    predicate = get_predicate(final_grade)

    # ── Learning objectives (Capaian Materi) with mastery status ─────
    learning_objectives = LearningObjective.query.filter_by(
        course_id=course_id
    ).order_by(LearningObjective.order).all()

    lo_list = []
    for lo in learning_objectives:
        lo_data = lo.to_dict()
        lo_data['items'] = []
        lo_percentages = []
        seen_item_ids: set = set()

        # Items linked directly to this CP
        for item in lo.grade_items:
            if item.id in seen_item_ids:
                continue
            seen_item_ids.add(item.id)
            entry = GradeEntry.query.filter_by(
                grade_item_id=item.id,
                student_id=student_id
            ).first()
            if entry and entry.percentage is not None:
                lo_data['items'].append({
                    'item_id': item.id,
                    'item_name': item.name,
                    'score': entry.score,
                    'max_score': item.max_score,
                    'percentage': entry.percentage,
                })
                lo_percentages.append(entry.percentage)

        # Items linked through TPs
        for goal in lo.learning_goals:
            for item in goal.grade_items:
                if item.id in seen_item_ids:
                    continue
                seen_item_ids.add(item.id)
                entry = GradeEntry.query.filter_by(
                    grade_item_id=item.id,
                    student_id=student_id
                ).first()
                if entry and entry.percentage is not None:
                    lo_data['items'].append({
                        'item_id': item.id,
                        'item_name': item.name,
                        'score': entry.score,
                        'max_score': item.max_score,
                        'percentage': entry.percentage,
                        'goal_code': goal.code,
                    })
                    lo_percentages.append(entry.percentage)

        # Calculate average score and mastery status for this CP
        avg_score = round(sum(lo_percentages) / len(lo_percentages), 2) if lo_percentages else 0.0
        lo_data['avg_score'] = avg_score
        lo_data['predicate'] = get_predicate(avg_score)
        lo_data['mastery_status'] = get_mastery_status(avg_score)
        lo_data['needs_remedial'] = needs_remedial(avg_score)
        lo_data['remedial_label'] = get_remedial_label(avg_score)

        lo_list.append(lo_data)

    # ── If no CP defined, create a virtual "overall" entry ───────────
    if not lo_list and all_percentages:
        lo_list.append({
            'id': 0,
            'code': 'Umum',
            'description': course.name,
            'course_id': course_id,
            'order': 0,
            'goals_count': 0,
            'items': [],
            'avg_score': final_grade,
            'predicate': predicate,
            'mastery_status': get_mastery_status(final_grade),
        })

    summary = {
        'course_id': course_id,
        'course_name': course.name,
        'student_id': student_id,
        'items': items_list,
        'learning_objectives': lo_list,
        'final_grade': final_grade,
        'predicate': predicate,
        'mastery_status': get_mastery_status(final_grade),
        'total_items': len(all_items),
        'graded_items': len(all_percentages),
    }

    return summary


def bulk_save_grades(entries_data: List[Dict], graded_by: int, set_manual_override: bool = True) -> int:
    """
    Bulk save grade entries.
    
    Args:
        entries_data: List of dicts with keys: grade_item_id, student_id, score, feedback, manual_override (optional)
        graded_by: Teacher user ID who is grading
        set_manual_override: If True, mark manually entered grades as overridden (protected from auto-sync)
    
    Returns:
        Number of entries saved
    """
    saved_count = 0
    now = get_jakarta_now()

    for entry_data in entries_data:
        grade_item_id = entry_data.get('grade_item_id')
        student_id = entry_data.get('student_id')
        score = entry_data.get('score')
        feedback = entry_data.get('feedback')
        manual_override = entry_data.get('manual_override', set_manual_override)

        if not all([grade_item_id, student_id, score is not None]):
            continue

        # Get grade item to calculate percentage
        grade_item = GradeItem.query.get(grade_item_id)
        if not grade_item:
            continue

        percentage = (score / grade_item.max_score * 100) if grade_item.max_score > 0 else 0

        # Find or create entry
        entry = GradeEntry.query.filter_by(
            grade_item_id=grade_item_id,
            student_id=student_id
        ).first()

        if entry:
            entry.score = score
            entry.percentage = percentage
            entry.feedback = feedback
            entry.graded_at = now
            entry.graded_by = graded_by
            if manual_override:
                entry.manual_override = True
        else:
            entry = GradeEntry(
                grade_item_id=grade_item_id,
                student_id=student_id,
                score=score,
                percentage=percentage,
                feedback=feedback,
                graded_at=now,
                graded_by=graded_by,
                manual_override=manual_override,
            )
            db.session.add(entry)

        saved_count += 1

    db.session.commit()
    return saved_count
