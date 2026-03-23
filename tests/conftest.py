import os
import sys
import pytest
from datetime import datetime
from pathlib import Path

# Ensure project root is importable when running tests
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(scope='function')
def app():
    """Create application for testing with MySQL"""
    from app import create_app
    import os
    
    # Use MySQL from environment or .env
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
        from app.extensions import db
        # Drop all tables first to ensure clean state
        db.drop_all()
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def db(app):
    """Create database session for testing"""
    from app.extensions import db
    with app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()


@pytest.fixture
def teacher_user(app):
    """Create a teacher user for testing"""
    from app.extensions import db
    from app.models import User, UserRole
    
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
    from app.extensions import db
    from app.models import User, UserRole
    
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
    from app.extensions import db
    from app.models import Course, AcademicYear, User
    
    # Create academic year first (required foreign key)
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
    
    # Enroll student - use the relationship properly
    student = User.query.filter_by(email='student@test.com').first()
    if student:
        student.courses_enrolled.append(course)
        db.session.commit()
    
    return course


@pytest.fixture
def grade_category(app, course):
    """Create a grade category for testing"""
    from app.extensions import db
    from app.models.gradebook import GradeCategory, GradeCategoryType
    
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
    from app.extensions import db
    from app.models.gradebook import LearningObjective
    
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
    from app.extensions import db
    from app.models.gradebook import GradeItem
    
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
    from app.extensions import db
    from app.models.gradebook import GradeEntry
    
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
    from app.extensions import db
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
    from app.extensions import db
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
