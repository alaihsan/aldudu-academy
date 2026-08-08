import pytest


@pytest.fixture
def grade_category(app, course):
    """Create a grade category for testing (quiz-grade-sync tests need one)."""
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
def grade_item(app, course, grade_category):
    """Create a grade item for testing (quiz-grade-sync tests need one)."""
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
