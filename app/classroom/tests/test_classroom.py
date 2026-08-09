import pytest
from app.models import (
    User, UserRole, School, SchoolStatus, AcademicYear,
    AssignmentSubmission, AssignmentSubmissionStatus, QuizSubmission, QuizStatus,
)


def _login(client, user):
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)


@pytest.fixture
def enrolled_student(db, course, student_user):
    course.students.append(student_user)
    db.session.commit()
    return student_user


def test_student_sees_pending_assignment_and_quiz(client, db, course, assignment, quiz, enrolled_student):
    quiz.status = QuizStatus.PUBLISHED
    db.session.commit()

    _login(client, enrolled_student)

    resp = client.get('/api/classroom/items')
    assert resp.status_code == 200

    data = resp.get_json()
    assert data['success'] is True
    types = {item['type'] for item in data['items']}
    assert types == {'assignment', 'quiz'}


def test_student_does_not_see_submitted_assignment(client, db, course, assignment, enrolled_student):
    submission = AssignmentSubmission(
        assignment_id=assignment.id,
        student_id=enrolled_student.id,
        status=AssignmentSubmissionStatus.SUBMITTED,
    )
    db.session.add(submission)
    db.session.commit()

    _login(client, enrolled_student)
    resp = client.get('/api/classroom/items')
    data = resp.get_json()

    assert all(item['id'] != assignment.id or item['type'] != 'assignment' for item in data['items'])


def test_student_does_not_see_completed_quiz(client, db, course, quiz, enrolled_student):
    quiz.status = QuizStatus.PUBLISHED
    db.session.commit()

    submission = QuizSubmission(quiz_id=quiz.id, user_id=enrolled_student.id, total_points=100)
    db.session.add(submission)
    db.session.commit()

    _login(client, enrolled_student)
    resp = client.get('/api/classroom/items')
    data = resp.get_json()

    assert all(item['id'] != quiz.id or item['type'] != 'quiz' for item in data['items'])


def test_teacher_sees_only_items_needing_review(client, db, course, assignment, quiz, teacher_user, enrolled_student):
    # No submissions yet: teacher should see nothing to review.
    _login(client, teacher_user)
    resp = client.get('/api/classroom/items')
    data = resp.get_json()
    assert data['items'] == []

    # Once a student submits, the teacher should see it as pending review.
    submission = AssignmentSubmission(
        assignment_id=assignment.id,
        student_id=enrolled_student.id,
        status=AssignmentSubmissionStatus.SUBMITTED,
    )
    db.session.add(submission)
    db.session.commit()

    resp = client.get('/api/classroom/items')
    data = resp.get_json()
    assignment_items = [i for i in data['items'] if i['type'] == 'assignment']
    assert len(assignment_items) == 1
    assert assignment_items[0]['pending_count'] == 1


def test_teacher_does_not_see_graded_assignment(client, db, course, assignment, teacher_user, enrolled_student):
    submission = AssignmentSubmission(
        assignment_id=assignment.id,
        student_id=enrolled_student.id,
        status=AssignmentSubmissionStatus.GRADED,
    )
    db.session.add(submission)
    db.session.commit()

    _login(client, teacher_user)
    resp = client.get('/api/classroom/items')
    data = resp.get_json()
    assert all(item['type'] != 'assignment' for item in data['items'])


def test_filter_assignments_only(client, db, course, assignment, quiz, enrolled_student):
    _login(client, enrolled_student)
    resp = client.get('/api/classroom/items?filter=assignments')
    data = resp.get_json()
    assert all(item['type'] == 'assignment' for item in data['items'])


def test_tenant_isolation_other_school_student_sees_nothing(client, db, course, assignment, quiz):
    other_school = School(
        name='Other School', slug='other-school',
        email='other@test.com', admin_email='other-admin@test.com',
        status=SchoolStatus.ACTIVE,
    )
    db.session.add(other_school)
    db.session.commit()

    other_year = AcademicYear(year='2099', is_active=True, school_id=other_school.id)
    db.session.add(other_year)
    db.session.commit()

    other_student = User(
        name='Other School Student', email='other-student@test.com',
        role=UserRole.MURID, email_verified=True, school_id=other_school.id,
    )
    other_student.set_password('password123')
    db.session.add(other_student)
    db.session.commit()

    _login(client, other_student)
    resp = client.get('/api/classroom/items')
    data = resp.get_json()
    assert data['items'] == []


def test_requires_login(client):
    resp = client.get('/api/classroom/items')
    assert resp.status_code in (302, 401)


def test_classroom_page_renders(client, enrolled_student):
    _login(client, enrolled_student)
    resp = client.get('/ruang-kelas')
    assert resp.status_code == 200
