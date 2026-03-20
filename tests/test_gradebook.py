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
def student_user(app):
    """Create a student user for testing"""
    user = User(
        name='Test Student',
        email='student@test.com',
        role=UserRole.MURID
    )
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def course(app, teacher_user):
    """Create a course for testing"""
    course = Course(
        name='Test Course',
        description='Test Description',
        teacher_id=teacher_user.id,
        class_code='TEST123'
    )
    db.session.add(course)
    db.session.commit()
    # Enroll student
    course.students.append(User.query.filter_by(email='student@test.com').first())
    db.session.commit()
    return course


@pytest.fixture
def grade_category(app, course):
    """Create a grade category for testing"""
    category = GradeCategory(
        name='Penilaian Harian',
        category_type=GradeCategoryType.FORMATIF,
        weight=30.0,
        course_id=course.id
    )
    db.session.add(category)
    db.session.commit()
    return category


@pytest.fixture
def learning_objective(app, course):
    """Create a learning objective for testing"""
    lo = LearningObjective(
        code='CP-1',
        description='Test Learning Objective',
        course_id=course.id
    )
    db.session.add(lo)
    db.session.commit()
    return lo


@pytest.fixture
def grade_item(app, course, grade_category):
    """Create a grade item for testing"""
    item = GradeItem(
        name='Test Grade Item',
        category_id=grade_category.id,
        max_score=100.0,
        weight=10.0,
        course_id=course.id
    )
    db.session.add(item)
    db.session.commit()
    return item


@pytest.fixture
def grade_entry(app, grade_item, student_user):
    """Create a grade entry for testing"""
    entry = GradeEntry(
        grade_item_id=grade_item.id,
        student_id=student_user.id,
        score=85.0,
        percentage=85.0,
        feedback='Good job!'
    )
    db.session.add(entry)
    db.session.commit()
    return entry


@pytest.fixture
def quiz(app, course):
    """Create a quiz for testing"""
    quiz = Quiz(
        name='Test Quiz',
        description='Test Description',
        course_id=course.id,
        points=100,
        status=QuizStatus.DRAFT
    )
    db.session.add(quiz)
    db.session.commit()
    return quiz


@pytest.fixture
def assignment(app, course):
    """Create an assignment for testing"""
    assignment = Assignment(
        title='Test Assignment',
        description='Test Description',
        course_id=course.id,
        max_score=100.0,
        status=AssignmentStatus.PUBLISHED
    )
    db.session.add(assignment)
    db.session.commit()
    return assignment
