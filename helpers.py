import string
import random
import re
import html
from models import Course, User, UserRole


def generate_class_code(length=6):
    characters = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(random.choices(characters, k=length))
        if not Course.query.filter_by(class_code=code).first():
            return code


def get_courses_for_user(user, year_id):
    if not year_id:
        return []
    if user.role == UserRole.GURU:
        return Course.query.filter_by(teacher_id=user.id, academic_year_id=year_id).order_by(Course.name).all()
    else:
        return Course.query.join(User.courses_enrolled).filter(User.id == user.id, Course.academic_year_id == year_id).order_by(Course.name).all()


def format_course_data(course, user):
    return {
        'id': course.id,
        'name': course.name,
        'teacher': course.teacher.name,
        'studentCount': len(course.students),
        'class_code': course.class_code,
        'color': course.color,
        'is_teacher': course.teacher_id == user.id,
    }


# ----------------------
# Input validation helpers
# ----------------------
def _strip_tags(value: str) -> str:
    if not isinstance(value, str):
        return ''
    return re.sub(r'<[^>]*?>', '', value)


def sanitize_text(value: str, max_len: int = 150) -> str:
    if value is None:
        return ''
    s = value.strip()
    s = _strip_tags(s)
    s = html.escape(s)
    if len(s) > max_len:
        s = s[:max_len]
    return s


def is_valid_email(email: str) -> bool:
    from email_validator import validate_email, EmailNotValidError
    if not isinstance(email, str):
        return False
    try:
        validate_email(email, check_deliverability=False)
        return True
    except EmailNotValidError:
        return False


def is_valid_color(color: str) -> bool:
    if not isinstance(color, str):
        return False
    return re.match(r'^#[0-9a-fA-F]{6}$', color.strip()) is not None


def is_valid_class_code(code: str) -> bool:
    if not isinstance(code, str):
        return False
    c = code.strip().upper()
    return re.match(r'^[A-Z0-9]{4,8}$', c) is not None
