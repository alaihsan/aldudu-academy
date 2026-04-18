"""
Test Quiz Submission & Grading
"""
import pytest
from datetime import datetime
from app.models import Quiz, QuizSubmission, QuizStatus, Question, Answer, User
from app.extensions import db


class TestQuizSubmission:
    """Test quiz submission functionality"""

    def test_create_quiz_submission(self, client, quiz, student_user):
        """Test creating a quiz submission"""
        from app.extensions import db
        
        submission = QuizSubmission(
            quiz_id=quiz.id,
            student_id=student_user.id,
            status='submitted',
            score=0
        )
        db.session.add(submission)
        db.session.commit()
        
        assert submission.id is not None
        assert submission.quiz_id == quiz.id
        assert submission.student_id == student_user.id

    def test_quiz_submission_auto_grade(self, client, quiz, student_user):
        """Test automatic grading of quiz submission"""
        from app.extensions import db
        
        # Create a question
        question = Question(
            quiz_id=quiz.id,
            question_text='What is 2+2?',
            question_type='multiple_choice',
            options=['3', '4', '5', '6'],
            correct_answer='4',
            points=10
        )
        db.session.add(question)
        db.session.commit()
        
        # Create submission
        submission = QuizSubmission(
            quiz_id=quiz.id,
            student_id=student_user.id,
            status='submitted',
            score=0
        )
        db.session.add(submission)
        db.session.commit()
        
        # Create answer
        answer = SubmissionAnswer(
            submission_id=submission.id,
            question_id=question.id,
            student_answer='4'
        )
        db.session.add(answer)
        db.session.commit()
        
        # Auto-grade
        submission.auto_grade()
        db.session.commit()
        
        assert submission.score == 10
        assert submission.status == 'graded'

    def test_quiz_submission_status_transitions(self, quiz, student_user):
        """Test quiz submission status transitions"""
        from app.extensions import db
        
        submission = QuizSubmission(
            quiz_id=quiz.id,
            student_id=student_user.id,
            status='in_progress'
        )
        db.session.add(submission)
        db.session.commit()
        
        # Transition to submitted
        submission.status = 'submitted'
        db.session.commit()
        assert submission.status == 'submitted'
        
        # Transition to graded
        submission.status = 'graded'
        db.session.commit()
        assert submission.status == 'graded'

    def test_quiz_submission_duplicate_prevention(self, client, quiz, student_user):
        """Test preventing duplicate quiz submissions"""
        from app.extensions import db
        
        # Create first submission
        submission1 = QuizSubmission(
            quiz_id=quiz.id,
            student_id=student_user.id,
            status='submitted'
        )
        db.session.add(submission1)
        db.session.commit()
        
        # Try to create duplicate (should be handled by business logic)
        existing = QuizSubmission.query.filter_by(
            quiz_id=quiz.id,
            student_id=student_user.id,
            status='submitted'
        ).first()
        
        assert existing is not None


class TestQuizGradeCalculation:
    """Test quiz grade calculation"""

    def test_calculate_quiz_percentage(self, quiz, student_user):
        """Test calculating quiz percentage"""
        from app.extensions import db
        
        submission = QuizSubmission(
            quiz_id=quiz.id,
            student_id=student_user.id,
            score=85,
            status='graded'
        )
        db.session.add(submission)
        db.session.commit()
        
        # Calculate percentage
        percentage = (submission.score / quiz.points) * 100 if quiz.points > 0 else 0
        assert percentage == 85.0

    def test_quiz_grade_sync_to_gradebook(self, client, quiz, student_user, grade_item):
        """Test syncing quiz grade to gradebook"""
        from app.extensions import db
        from app.models.gradebook import GradeEntry
        
        # Create submission
        submission = QuizSubmission(
            quiz_id=quiz.id,
            student_id=student_user.id,
            score=90,
            status='graded'
        )
        db.session.add(submission)
        db.session.commit()
        
        # Create grade entry
        entry = GradeEntry(
            grade_item_id=grade_item.id,
            student_id=student_user.id,
            score=90,
            percentage=90.0
        )
        db.session.add(entry)
        db.session.commit()
        
        assert entry.score == 90
        assert entry.percentage == 90.0


class TestQuizAPI:
    """Test quiz API endpoints"""

    def test_get_quiz_unauthorized(self, client, quiz):
        """Test accessing quiz without authorization"""
        response = client.get(f'/api/quiz/{quiz.id}')
        assert response.status_code in [302, 401]

    def test_submit_quiz(self, client, quiz, student_user):
        """Test submitting quiz answers"""
        from app.extensions import db
        
        # Login as student
        client.post('/api/login', json={
            'email': 'student@test.com',
            'password': 'password123'
        })
        
        # Create submission first
        submission = QuizSubmission(
            quiz_id=quiz.id,
            student_id=student_user.id,
            status='in_progress'
        )
        db.session.add(submission)
        db.session.commit()
        
        # Submit quiz
        response = client.post(f'/api/quiz/{quiz.id}/submit', json={
            'submission_id': submission.id,
            'answers': []
        })
        
        # Should update submission status
        db.session.refresh(submission)
        assert submission.status in ['submitted', 'graded']
