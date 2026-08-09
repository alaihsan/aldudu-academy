"""
Ruang Kelas (Classroom) — aggregates assignments and quizzes across every
course a user is enrolled in (student) or teaches (teacher) into one list,
so they don't have to open each course individually to see what's pending.

Quizzes have no due-date field in the schema (only `duration`, the time
limit once started) — only Assignment.due_date is a real deadline, so
"tenggat terdekat/terjauh" sorting only ever orders assignments; quizzes
always sort to the end of a due-date sort, ordered by recency instead.
"""
from app.core.extensions import db
from app.helpers import get_courses_for_user
from app.models import (
    AcademicYear, UserRole, Quiz, QuizStatus, QuizSubmission,
    Assignment, AssignmentStatus, AssignmentSubmission, AssignmentSubmissionStatus,
)

TEACHER_ROLES = (UserRole.GURU, UserRole.ADMIN, UserRole.SUPER_ADMIN)


def _resolve_year_id(user, school_id):
    """Mirror courses.api_initial_data's active-year resolution so the
    course set here matches what the dashboard shows (app/courses/routes.py).
    """
    if user.role in TEACHER_ROLES:
        return -1
    current_year = AcademicYear.query.filter_by(school_id=school_id, is_active=True).first()
    return current_year.id if current_year else -1


def _assignment_item(assignment, course, pending_count=None):
    item = {
        'type': 'assignment',
        'id': assignment.id,
        'title': assignment.title,
        'course_id': course.id,
        'course_name': course.name,
        'due_date': assignment.due_date.isoformat() if assignment.due_date else None,
        'created_at': assignment.created_at.isoformat(),
        'url': f'/assignment/{assignment.id}',
    }
    if pending_count is not None:
        item['pending_count'] = pending_count
    return item


def _quiz_item(quiz, course, pending_count=None):
    item = {
        'type': 'quiz',
        'id': quiz.id,
        'title': quiz.name,
        'course_id': course.id,
        'course_name': course.name,
        'due_date': None,
        'created_at': quiz.created_at.isoformat(),
        'url': f'/quiz/{quiz.id}',
    }
    if pending_count is not None:
        item['pending_count'] = pending_count
    return item


def _collect_items(user, courses):
    is_teacher = user.role in TEACHER_ROLES
    items = []

    for course in courses:
        for assignment in course.assignments:
            if assignment.is_trashed or assignment.status != AssignmentStatus.PUBLISHED:
                continue
            if is_teacher:
                pending = assignment.submissions.filter_by(
                    status=AssignmentSubmissionStatus.SUBMITTED
                ).count()
                if pending == 0:
                    continue
                items.append(_assignment_item(assignment, course, pending_count=pending))
            else:
                already_submitted = db.session.query(AssignmentSubmission.id).filter_by(
                    assignment_id=assignment.id, student_id=user.id
                ).first()
                if already_submitted:
                    continue
                items.append(_assignment_item(assignment, course))

        for quiz in course.quizzes:
            if quiz.is_trashed or quiz.is_archived or quiz.status != QuizStatus.PUBLISHED:
                continue
            if is_teacher:
                pending = len(quiz.submissions)
                if pending == 0:
                    continue
                items.append(_quiz_item(quiz, course, pending_count=pending))
            else:
                already_done = db.session.query(QuizSubmission.id).filter_by(
                    quiz_id=quiz.id, user_id=user.id
                ).first()
                if already_done:
                    continue
                items.append(_quiz_item(quiz, course))

    return items


def _apply_filter(items, item_filter):
    if item_filter == 'assignments':
        return [i for i in items if i['type'] == 'assignment']
    if item_filter == 'quizzes':
        return [i for i in items if i['type'] == 'quiz']
    return items


def _apply_sort(items, sort_mode):
    if sort_mode == 'recent':
        return sorted(items, key=lambda i: i['created_at'], reverse=True)

    with_due = [i for i in items if i['due_date']]
    without_due = sorted([i for i in items if not i['due_date']], key=lambda i: i['created_at'], reverse=True)
    with_due.sort(key=lambda i: i['due_date'], reverse=(sort_mode == 'due-desc'))
    return with_due + without_due


def get_pending_items_for_user(user, school_id, item_filter='all', sort_mode='due-asc'):
    year_id = _resolve_year_id(user, school_id)
    courses = get_courses_for_user(user, year_id)
    items = _collect_items(user, courses)
    items = _apply_filter(items, item_filter)
    return _apply_sort(items, sort_mode)
