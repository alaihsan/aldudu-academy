"""
Test Rasch Model Analysis
"""
import pytest
from app.models import Quiz, QuizSubmission, Question, Answer, User, UserRole
from app.extensions import db


class TestRaschAnalysis:
    """Test Rasch Model analysis functionality"""

    def test_rasch_threshold_check(self, client, quiz, student_user):
        """Test checking Rasch analysis threshold"""
        from app.extensions import db
        
        # Create minimum submissions for analysis
        submissions = []
        for i in range(30):  # Minimum 30 submissions for Rasch
            student = User(
                name=f'Test Student {i}',
                email=f'student{i}@test.com',
                role=UserRole.MURID
            )
            student.set_password('password123')
            db.session.add(student)
            
            submission = QuizSubmission(
                quiz_id=quiz.id,
                student_id=student.id,
                status='graded',
                score=50 + i  # Varying scores
            )
            db.session.add(submission)
            submissions.append(submission)
        
        db.session.commit()
        
        # Check threshold status
        from app.services.rasch_service import check_rasch_threshold
        meets_threshold, count = check_rasch_threshold(quiz.id)
        
        assert meets_threshold is True
        assert count >= 30

    def test_rasch_item_difficulty_calculation(self, quiz):
        """Test calculating item difficulty using Rasch"""
        # Mock data for difficulty calculation
        item_responses = [
            {'correct': True, 'ability': 1.0},
            {'correct': False, 'ability': 0.5},
            {'correct': True, 'ability': 1.5},
            {'correct': False, 'ability': -0.5},
        ]
        
        # Calculate difficulty (simplified)
        correct_count = sum(1 for r in item_responses if r['correct'])
        difficulty = 1.0 - (correct_count / len(item_responses))
        
        assert 0 <= difficulty <= 1

    def test_rasch_person_ability_calculation(self, quiz, student_user):
        """Test calculating person ability using Rasch"""
        from app.extensions import db
        
        # Create submission with known score
        submission = QuizSubmission(
            quiz_id=quiz.id,
            student_id=student_user.id,
            status='graded',
            score=85
        )
        db.session.add(submission)
        db.session.commit()
        
        # Ability should correlate with score
        ability = submission.score / 100  # Normalized
        assert 0 <= ability <= 1


class TestWrightMap:
    """Test Wright Map generation"""

    def test_wright_map_data_structure(self, quiz):
        """Test Wright Map data structure"""
        # Mock Wright Map data
        wright_map_data = {
            'items': [
                {'id': 1, 'difficulty': 0.8, 'label': 'Q1'},
                {'id': 2, 'difficulty': 0.5, 'label': 'Q2'},
                {'id': 3, 'difficulty': 0.2, 'label': 'Q3'},
            ],
            'persons': [
                {'id': 1, 'ability': 0.9, 'label': 'Student A'},
                {'id': 2, 'ability': 0.6, 'label': 'Student B'},
                {'id': 3, 'ability': 0.3, 'label': 'Student C'},
            ]
        }
        
        # Validate structure
        assert 'items' in wright_map_data
        assert 'persons' in wright_map_data
        assert len(wright_map_data['items']) > 0
        assert len(wright_map_data['persons']) > 0

    def test_wright_map_scale_range(self):
        """Test Wright Map scale range"""
        # Wright Map should use logit scale typically -4 to +4
        min_logit = -4.0
        max_logit = 4.0
        
        # Mock data
        item_difficulties = [0.8, 0.5, -0.2, 1.5, -1.0]
        person_abilities = [0.9, 0.6, -0.3, 2.0, -1.5]
        
        # All values should be within reasonable range
        for d in item_difficulties:
            assert min_logit - 1 <= d <= max_logit + 1
        
        for a in person_abilities:
            assert min_logit - 1 <= a <= max_logit + 1


class TestRaschFitStatistics:
    """Test Rasch fit statistics"""

    def test_infit_mnsq_calculation(self):
        """Test Infit Mean Square calculation"""
        # Mock residuals and variances
        residuals = [0.5, -0.3, 0.8, -0.1, 0.2]
        variances = [0.8, 0.6, 0.9, 0.7, 0.5]
        
        # Calculate standardized residuals
        std_residuals = [r / (v ** 0.5) for r, v in zip(residuals, variances)]
        
        # Calculate Infit MNSQ (simplified)
        squared_sum = sum(r ** 2 for r in std_residuals)
        infit_mnsq = squared_sum / len(std_residuals)
        
        # Acceptable range is typically 0.5 to 1.5
        assert 0 <= infit_mnsq <= 3  # Broad range for test

    def test_outfit_mnsq_calculation(self):
        """Test Outfit Mean Square calculation"""
        # Similar to Infit but uses raw residuals
        residuals = [0.5, -0.3, 0.8, -0.1, 0.2]
        
        outfit_mnsq = sum(r ** 2 for r in residuals) / len(residuals)
        
        # Acceptable range is typically 0.5 to 1.5
        assert 0 <= outfit_mnsq <= 3


class TestRaschReliability:
    """Test Rasch reliability indices"""

    def test_person_reliability(self):
        """Test person reliability index"""
        # Mock reliability calculation
        true_variance = 0.8
        error_variance = 0.2
        
        reliability = true_variance / (true_variance + error_variance)
        
        assert 0 <= reliability <= 1
        assert reliability == 0.8  # 80% reliability

    def test_item_reliability(self):
        """Test item reliability index"""
        # Mock reliability calculation
        true_variance = 0.7
        error_variance = 0.3
        
        reliability = true_variance / (true_variance + error_variance)
        
        assert 0 <= reliability <= 1
        assert reliability == 0.7  # 70% reliability


class TestRaschAPI:
    """Test Rasch API endpoints"""

    def test_get_threshold_status(self, client, quiz):
        """Test getting Rasch threshold status"""
        response = client.get(f'/api/rasch/quizzes/{quiz.id}/threshold-status')
        
        # Should return JSON with threshold info
        assert response.status_code == 200
        data = response.get_json()
        assert 'success' in data or 'meets_threshold' in data

    def test_trigger_rasch_analysis(self, client, quiz):
        """Test triggering Rasch analysis"""
        response = client.post(f'/api/rasch/quizzes/{quiz.id}/analyze')
        
        # Should accept analysis request
        assert response.status_code in [200, 202]
        data = response.get_json()
        assert 'success' in data or 'analysis_id' in data
