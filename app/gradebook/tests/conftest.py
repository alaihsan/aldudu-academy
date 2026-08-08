import pytest


@pytest.fixture
def grade_category(app, course):
    """Create a grade category for testing"""
    from app.core.extensions import db
    from app.gradebook.models import GradeCategory, GradeCategoryType

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
    from app.core.extensions import db
    from app.gradebook.models import LearningObjective

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
    from app.core.extensions import db
    from app.gradebook.models import GradeItem

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
    from app.core.extensions import db
    from app.gradebook.models import GradeEntry

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
