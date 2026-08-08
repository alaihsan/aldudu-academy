"""
Shared pytest fixtures for tests colocated under app/<feature>/tests/.

Several features share a fixture chain rooted in `course` (which itself
depends on `active_school`/`teacher_user`) — e.g. gradebook, quiz, and
assignment tests all build on the same test course. Keeping those shared
fixtures here (an ancestor directory of every app/<feature>/tests/ package)
lets pytest's conftest discovery make them available everywhere under
app/, without duplicating them per feature.

tests/conftest.py (repo root) still holds its own copy for the test
files that haven't been colocated into app/<feature>/tests/ yet, since
that directory isn't a descendant of this one.
"""
import os
import sys
import pytest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(scope='function')
def app():
    """Create application for testing with MySQL"""
    from app import create_app

    database_url = os.environ.get('TEST_DATABASE_URL',
                   os.environ.get('DATABASE_URL',
                   'mysql+pymysql://root:@localhost:3306/aldudu_academy_test'))

    app = create_app(test_config={
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': database_url,
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'WTF_CSRF_ENABLED': False,
    })

    with app.app_context():
        from app.core.extensions import db
        db.drop_all()
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def db(app):
    """Create database session for testing"""
    from app.core.extensions import db
    with app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()


@pytest.fixture
def active_school(app):
    """Create an active school for authenticated user tests"""
    from app.core.extensions import db
    from app.models import School, SchoolStatus

    school = School(
        name='Test School',
        slug='test-school',
        email='school@test.com',
        admin_email='admin@test.com',
        status=SchoolStatus.ACTIVE,
    )
    db.session.add(school)
    db.session.commit()
    return school


@pytest.fixture
def teacher_user(app, active_school):
    """Create a teacher user for testing"""
    from app.core.extensions import db
    from app.models import User, UserRole

    user = User(
        name='Test Teacher',
        email='teacher@test.com',
        role=UserRole.GURU,
        email_verified=True,
        school_id=active_school.id,
    )
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def student_user(app, active_school):
    """Create a student user for testing"""
    from app.core.extensions import db
    from app.models import User, UserRole

    user = User(
        name='Test Student',
        email='student@test.com',
        role=UserRole.MURID,
        email_verified=True,
        school_id=active_school.id,
    )
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def course(app, teacher_user, active_school):
    """Create a course for testing"""
    from app.core.extensions import db
    from app.models import Course, AcademicYear

    academic_year = AcademicYear(
        year=str(datetime.now().year),
        is_active=True,
        school_id=active_school.id,
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
    from app.core.extensions import db
    from app.models import Quiz, QuizStatus

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
    from app.core.extensions import db
    from app.models import Assignment, AssignmentStatus

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


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()
