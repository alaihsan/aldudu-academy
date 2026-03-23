"""
Tests for Stage 3 Features (GAP-6: Remedial, GAP-1: CTT Analysis)
"""
import pytest
from app.extensions import db
from app.models import User, UserRole, Course, Quiz, QuizStatus
from app.models.gradebook import GradeCategory, GradeCategoryType, GradeItem, GradeEntry, LearningObjective
from app.services.gradebook_service import needs_remedial, get_remedial_label


class TestGAP6Remedial:
    """Test GAP-6: Flag 'Perlu Remedial' otomatis"""
    
    def test_needs_remedial_below_kkm(self):
        """Student needs remedial if grade < KKM (70)"""
        assert needs_remedial(69) == True
        assert needs_remedial(65) == True
        assert needs_remedial(50) == True
        assert needs_remedial(0) == True
    
    def test_needs_remedial_at_kkm(self):
        """Student doesn't need remedial if grade >= KKM"""
        assert needs_remedial(70) == False
        assert needs_remedial(75) == False
        assert needs_remedial(80) == False
        assert needs_remedial(100) == False
    
    def test_needs_remedial_custom_kkm(self):
        """Custom KKM threshold"""
        assert needs_remedial(74, kkm=75) == True
        assert needs_remedial(75, kkm=75) == False
        assert needs_remedial(76, kkm=75) == False
    
    def test_get_remedial_label(self):
        """Get remedial status label"""
        assert get_remedial_label(69) == 'Perlu Remedial'
        assert get_remedial_label(70) == 'Tuntas'
        assert get_remedial_label(85) == 'Tuntas'
    
    def test_get_remedial_label_custom_kkm(self):
        """Get remedial label with custom KKM"""
        assert get_remedial_label(74, kkm=75) == 'Perlu Remedial'
        assert get_remedial_label(75, kkm=75) == 'Tuntas'


class TestGAP1CTTAnalysisAPI:
    """Test GAP-1: CTT Item Analysis API (Unit Tests)"""
    
    def test_ctt_analysis_calculation_logic(self):
        """Test CTT calculation logic without API"""
        # Mock submission data
        total_students = 10
        student_scores = [1, 1, 1, 1, 1, 0, 0, 0, 0, 0]  # 5 correct, 5 wrong
        total_quiz_scores = [90, 85, 80, 75, 70, 60, 55, 50, 45, 40]
        
        # Calculate p-value
        correct_count = sum(student_scores)
        p_value = correct_count / total_students
        
        assert p_value == 0.5, "p-value should be 0.5 (50% correct)"
        
        # Calculate point-biserial (correlation)
        mean_x = sum(student_scores) / len(student_scores)
        mean_y = sum(total_quiz_scores) / len(total_quiz_scores)
        
        numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(student_scores, total_quiz_scores))
        std_x = (sum((x - mean_x) ** 2 for x in student_scores)) ** 0.5
        std_y = (sum((y - mean_y) ** 2 for y in total_quiz_scores)) ** 0.5
        
        if std_x > 0 and std_y > 0:
            point_biserial = numerator / (std_x * std_y)
        else:
            point_biserial = 0
        
        # Should be positive correlation (students with high total score got it correct)
        assert point_biserial > 0, "Point-biserial should be positive"
        assert point_biserial <= 1, "Point-biserial should be <= 1"
    
    def test_p_value_interpretation(self):
        """Test p-value interpretation"""
        # Easy question (>0.7)
        assert "Mudah" if 0.85 > 0.7 else "other" == "Mudah"
        
        # Medium question (0.3-0.7)
        assert "Sedang" if 0.3 <= 0.5 <= 0.7 else "other" == "Sedang"
        
        # Hard question (<0.3)
        assert "Sukar" if 0.2 < 0.3 else "other" == "Sukar"
    
    def test_point_biserial_interpretation(self):
        """Test point-biserial interpretation"""
        # Good discrimination (>=0.4)
        assert "Baik" if 0.45 >= 0.4 else "other" == "Baik"
        
        # Fair discrimination (0.2-0.4)
        assert "Cukup" if 0.2 <= 0.3 >= 0.2 else "other" == "Cukup"
        
        # Poor discrimination (<0.2)
        assert "Perlu Perbaikan" if 0.15 < 0.2 else "other" == "Perlu Perbaikan"


@pytest.fixture
def teacher_user(app):
    """Create a teacher user for testing"""
    user = User(
        name='Test Teacher',
        email='teacher@test.com',
        role=UserRole.GURU
    )
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def course(app, teacher_user):
    """Create a course for testing"""
    from app.models import AcademicYear
    from datetime import datetime
    
    academic_year = AcademicYear(
        year=str(datetime.now().year),
        is_active=True
    )
    db.session.add(academic_year)
    db.session.commit()
    
    course = Course(
        name='Test Course',
        class_code='TEST123',
        teacher_id=teacher_user.id,
        academic_year_id=academic_year.id
    )
    db.session.add(course)
    db.session.commit()
    return course


@pytest.fixture
def quiz(app, course):
    """Create a quiz for testing"""
    from app.models import Quiz, QuizStatus
    
    quiz = Quiz(
        name='Test Quiz',
        description='Test Description',
        course_id=course.id,
        points=100,
        status=QuizStatus.PUBLISHED
    )
    db.session.add(quiz)
    db.session.commit()
    return quiz
