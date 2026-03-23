"""
Tests for Gradebook Feature Integration
"""
import pytest
from flask import url_for
from app.extensions import db
from app.models import User, UserRole, Course, Quiz, QuizSubmission, QuizStatus
from app.models import Assignment, AssignmentSubmission, AssignmentStatus
from app.models.gradebook import GradeCategory, GradeCategoryType, GradeItem, GradeEntry
from app.models.gradebook import LearningObjective, LearningGoal


class TestGradebookIntegration:
    """Test gradebook integration with quiz and assignment"""

    def test_teacher_can_access_gradebook(self, client, teacher_user, course):
        """Test that teacher can access their course gradebook"""
        with client:
            client.post('/login', data={
                'email': teacher_user.email,
                'password': 'password123'
            }, follow_redirects=True)

            response = client.get(f'/gradebook/course/{course.id}')
            assert response.status_code == 200
            assert b'Buku Nilai' in response.data

    def test_student_cannot_access_teacher_gradebook(self, client, student_user, course):
        """Test that student cannot access teacher gradebook view"""
        with client:
            client.post('/login', data={
                'email': student_user.email,
                'password': 'password123'
            }, follow_redirects=True)

            response = client.get(f'/gradebook/course/{course.id}', follow_redirects=True)
            assert response.status_code == 403

    def test_create_grade_category(self, client, teacher_user, course):
        """Test creating a grade category"""
        with client:
            client.post('/login', data={
                'email': teacher_user.email,
                'password': 'password123'
            }, follow_redirects=True)

            response = client.post('/gradebook/api/categories', json={
                'course_id': course.id,
                'name': 'Penilaian Harian',
                'category_type': 'formatif',
                'weight': 30.0
            }, content_type='application/json')

            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert data['category']['name'] == 'Penilaian Harian'

    def test_create_learning_objective(self, client, teacher_user, course):
        """Test creating a learning objective (CP)"""
        with client:
            client.post('/login', data={
                'email': teacher_user.email,
                'password': 'password123'
            }, follow_redirects=True)

            response = client.post('/gradebook/api/learning-objectives', json={
                'course_id': course.id,
                'code': 'CP-1',
                'description': 'Memahami konsep dasar aljabar'
            }, content_type='application/json')

            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert data['learning_objective']['code'] == 'CP-1'

    def test_create_learning_goal(self, client, teacher_user, course, learning_objective):
        """Test creating a learning goal (TP)"""
        with client:
            client.post('/login', data={
                'email': teacher_user.email,
                'password': 'password123'
            }, follow_redirects=True)

            response = client.post('/gradebook/api/learning-goals', json={
                'learning_objective_id': learning_objective.id,
                'code': 'TP-1.1',
                'description': 'Siswa dapat menyelesaikan persamaan linear'
            }, content_type='application/json')

            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert data['learning_goal']['code'] == 'TP-1.1'

    def test_create_grade_item(self, client, teacher_user, course, grade_category):
        """Test creating a grade item"""
        with client:
            client.post('/login', data={
                'email': teacher_user.email,
                'password': 'password123'
            }, follow_redirects=True)

            response = client.post('/gradebook/api/items', json={
                'course_id': course.id,
                'name': 'Tugas 1 - Persamaan Linear',
                'category_id': grade_category.id,
                'max_score': 100.0,
                'weight': 10.0
            }, content_type='application/json')

            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert data['item']['name'] == 'Tugas 1 - Persamaan Linear'

    def test_bulk_save_grades(self, client, teacher_user, course, grade_item, student_user):
        """Test bulk saving grade entries"""
        with client:
            client.post('/login', data={
                'email': teacher_user.email,
                'password': 'password123'
            }, follow_redirects=True)

            response = client.post('/gradebook/api/entries/bulk', json={
                'entries': [
                    {
                        'grade_item_id': grade_item.id,
                        'student_id': student_user.id,
                        'score': 85.0,
                        'feedback': 'Bagus!'
                    }
                ]
            }, content_type='application/json')

            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert data['saved_count'] == 1

    def test_quiz_auto_sync_to_gradebook(self, client, course, teacher_user, student_user, quiz):
        """Test that quiz submission automatically creates grade entry"""
        # Publish quiz first
        quiz.status = QuizStatus.PUBLISHED
        db.session.commit()

        with client:
            client.post('/login', data={
                'email': student_user.email,
                'password': 'password123'
            }, follow_redirects=True)

            # Submit quiz
            response = client.post(f'/quiz/{quiz.id}/submit', json={
                'answers': []
            }, content_type='application/json')

            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True

            # Check if grade entry was created
            grade_item = GradeItem.query.filter_by(quiz_id=quiz.id).first()
            assert grade_item is not None

            grade_entry = GradeEntry.query.filter_by(
                grade_item_id=grade_item.id,
                student_id=student_user.id
            ).first()
            assert grade_entry is not None
            assert grade_entry.score == data['score']

    def test_assignment_grade_sync(self, client, teacher_user, course, student_user, assignment):
        """Test that assignment grading creates grade entry"""
        # Create submission first
        submission = AssignmentSubmission(
            assignment_id=assignment.id,
            student_id=student_user.id,
            content='Jawaban tugas',
            status=AssignmentSubmissionStatus.SUBMITTED
        )
        db.session.add(submission)
        db.session.commit()

        with client:
            client.post('/login', data={
                'email': teacher_user.email,
                'password': 'password123'
            }, follow_redirects=True)

            # Grade assignment
            response = client.post(f'/assignment/{assignment.id}/grade/{submission.id}', data={
                'score': '90',
                'feedback': 'Excellent!'
            }, content_type='multipart/form-data')

            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True

            # Check if grade entry was created
            grade_item = GradeItem.query.filter_by(assignment_id=assignment.id).first()
            assert grade_item is not None

            grade_entry = GradeEntry.query.filter_by(
                grade_item_id=grade_item.id,
                student_id=student_user.id
            ).first()
            assert grade_entry is not None
            assert grade_entry.score == 90.0
            assert grade_entry.feedback == 'Excellent!'

    def test_student_view_grades(self, client, student_user, course, grade_item, grade_entry):
        """Test student can view their own grades"""
        with client:
            client.post('/login', data={
                'email': student_user.email,
                'password': 'password123'
            }, follow_redirects=True)

            response = client.get(f'/gradebook/course/{course.id}/my-grades')
            assert response.status_code == 200
            assert b'Nilai Saya' in response.data

    def test_get_student_grades_summary_api(self, client, teacher_user, course, student_user, grade_item, grade_entry):
        """Test API endpoint for student grades summary"""
        with client:
            client.post('/login', data={
                'email': teacher_user.email,
                'password': 'password123'
            }, follow_redirects=True)

            response = client.get(f'/gradebook/api/student/{student_user.id}/course/{course.id}')
            assert response.status_code == 200

            data = response.get_json()
            assert data['success'] is True
            assert 'summary' in data
            assert 'final_grade' in data['summary']
            assert 'items' in data['summary']

    def test_import_quiz_to_gradebook(self, client, teacher_user, course, quiz, grade_category):
        """Test importing quiz to gradebook"""
        with client:
            client.post('/login', data={
                'email': teacher_user.email,
                'password': 'password123'
            }, follow_redirects=True)

            response = client.post(f'/gradebook/api/quizzes/{quiz.id}/import', json={
                'category_id': grade_category.id
            }, content_type='application/json')

            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert data['item']['quiz_id'] == quiz.id

    def test_sync_quiz_grades(self, client, teacher_user, course, quiz, grade_category, student_user):
        """Test syncing quiz grades to gradebook"""
        # First import the quiz
        grade_item = GradeItem(
            name=f"Quiz: {quiz.name}",
            category_id=grade_category.id,
            max_score=quiz.points,
            course_id=course.id,
            quiz_id=quiz.id
        )
        db.session.add(grade_item)
        db.session.commit()

        # Create a quiz submission
        submission = QuizSubmission(
            quiz_id=quiz.id,
            user_id=student_user.id,
            score=85.0,
            total_points=100
        )
        db.session.add(submission)
        db.session.commit()

        with client:
            client.post('/login', data={
                'email': teacher_user.email,
                'password': 'password123'
            }, follow_redirects=True)

            response = client.post(f'/gradebook/api/quizzes/{quiz.id}/sync', content_type='application/json')
            assert response.status_code == 200

            data = response.get_json()
            assert data['success'] is True
            assert data['updated_count'] >= 0

    def test_course_statistics(self, client, teacher_user, course, grade_item, grade_entry):
        """Test getting course statistics"""
        with client:
            client.post('/login', data={
                'email': teacher_user.email,
                'password': 'password123'
            }, follow_redirects=True)

            response = client.get(f'/gradebook/api/stats/{course.id}')
            assert response.status_code == 200

            data = response.get_json()
            assert data['success'] is True
            assert 'stats' in data
            assert 'average_grade' in data['stats']
            assert 'highest_grade' in data['stats']
            assert 'lowest_grade' in data['stats']


class TestGradebookBugFixes:
    """Test cases for BUG-1, BUG-2, BUG-3 fixes"""
    
    def test_bug1_mixed_weight_items(self, app, course, grade_category, student_user):
        """Test BUG-1 fix: Mixed weight items (some 0, some >0) should all be included"""
        from app.services.gradebook_service import calculate_category_grade
        
        # Create quiz item with weight=100 (imported)
        quiz_item = GradeItem(
            name='Quiz: Test',
            category_id=grade_category.id,
            max_score=100.0,
            weight=100.0,
            course_id=course.id,
        )
        
        # Create manual item with weight=0
        manual_item = GradeItem(
            name='Tugas Manual',
            category_id=grade_category.id,
            max_score=100.0,
            weight=0.0,
            course_id=course.id,
        )
        
        db.session.add_all([quiz_item, manual_item])
        db.session.commit()
        
        # Create entries for both items
        quiz_entry = GradeEntry(
            grade_item_id=quiz_item.id,
            student_id=student_user.id,
            score=80.0,
            percentage=80.0,
        )
        
        manual_entry = GradeEntry(
            grade_item_id=manual_item.id,
            student_id=student_user.id,
            score=90.0,
            percentage=90.0,
        )
        
        db.session.add_all([quiz_entry, manual_entry])
        db.session.commit()
        
        # Calculate category grade - both items should be included
        with app.app_context():
            category_data = calculate_category_grade(student_user.id, grade_category.id)
        
        # Both items should contribute to the score
        # Quiz (80% × 100 weight) + Manual (90% × 100 weight) = 170 / 200 = 85%
        assert category_data['score'] == 85.0, f"Expected 85.0, got {category_data['score']}"

    def test_bug2_unified_final_grade(self, app, course, grade_category, student_user):
        """Test BUG-2 fix: Unified final grade calculation"""
        from app.services.gradebook_service import calculate_final_grade, calculate_category_grade
        
        # Create grade item
        item = GradeItem(
            name='Test Item',
            category_id=grade_category.id,
            max_score=100.0,
            weight=100.0,
            course_id=course.id,
        )
        db.session.add(item)
        db.session.flush()
        
        # Create entry
        entry = GradeEntry(
            grade_item_id=item.id,
            student_id=student_user.id,
            score=85.0,
            percentage=85.0,
        )
        db.session.add(entry)
        db.session.commit()
        
        with app.app_context():
            # Test unified function directly with simple average (student view)
            final_grade_simple = calculate_final_grade(student_user.id, course.id, use_category_weighting=False)
            assert final_grade_simple == 85.0, f"Simple average should be 85.0, got {final_grade_simple}"
            
            # Test with category weighting (teacher view) - category has weight 30%
            # Category score = 85, weight = 30
            # weighted_score = 85 * 30 / 100 = 25.5
            # Final = (25.5 / 30) * 100 = 85.0
            final_grade_weighted = calculate_final_grade(student_user.id, course.id, use_category_weighting=True)
            assert final_grade_weighted == 85.0, f"Weighted average should be 85.0, got {final_grade_weighted}"

    def test_bug3_manual_override_protects_from_sync(self, app, course, quiz, grade_category, student_user):
        """Test BUG-3 fix: Manual override protects grade from auto-sync"""
        from app.services.gradebook_service import sync_quiz_grades
        
        # Create grade item for quiz
        grade_item = GradeItem(
            name=f"Quiz: {quiz.name}",
            category_id=grade_category.id,
            max_score=quiz.points,
            course_id=course.id,
            quiz_id=quiz.id,
        )
        db.session.add(grade_item)
        db.session.flush()  # Get the ID before creating entry
        
        # Create entry with manual override
        original_score = 95.0
        entry = GradeEntry(
            grade_item_id=grade_item.id,
            student_id=student_user.id,
            score=original_score,
            percentage=95.0,
            manual_override=True,  # Teacher manually adjusted this
        )
        db.session.add(entry)
        
        # Create quiz submission with different score
        submission = QuizSubmission(
            quiz_id=quiz.id,
            user_id=student_user.id,
            score=70.0,  # Different from manual override
            total_points=100
        )
        db.session.add(submission)
        db.session.commit()
        
        with app.app_context():
            # Sync quiz grades
            updated_count = sync_quiz_grades(quiz.id)
        
        # Entry should NOT be updated because of manual_override
        db.session.refresh(entry)
        assert entry.score == original_score, \
            f"Manual override failed: expected {original_score}, got {entry.score}"
        assert entry.manual_override == True

    def test_bulk_save_grades_sets_manual_override(self, app, course, grade_category, student_user, teacher_user):
        """Test that bulk_save_grades sets manual_override flag"""
        from app.services.gradebook_service import bulk_save_grades
        
        # Create grade item
        item = GradeItem(
            name='Test Item',
            category_id=grade_category.id,
            max_score=100.0,
            weight=100.0,
            course_id=course.id,
        )
        db.session.add(item)
        db.session.flush()  # Get ID
        item_id = item.id
        
        # Bulk save with manual override - DON'T use app.app_context() here
        # because we're already in the app context from fixture
        entries_data = [{
            'grade_item_id': item_id,
            'student_id': student_user.id,
            'score': 88.0,
            'feedback': 'Good work!'
        }]
        
        saved_count = bulk_save_grades(entries_data, graded_by=teacher_user.id)
        
        assert saved_count == 1
        
        # Verify manual_override is set
        entry = GradeEntry.query.filter_by(
            grade_item_id=item_id,
            student_id=student_user.id
        ).first()
        
        assert entry is not None
        assert entry.score == 88.0
        assert entry.manual_override == True, "Manual override should be True for bulk saved grades"
