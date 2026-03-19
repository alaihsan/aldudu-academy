import string
import random
import re
import html
from datetime import datetime, timedelta, timezone
from flask import request
from sqlalchemy import func
from sqlalchemy.orm import joinedload

def get_jakarta_now():
    """Returns current time in Jakarta (WIB, UTC+7)."""
    return datetime.now(timezone(timedelta(hours=7)))

def log_activity(user_id, action, target_type=None, target_id=None, details=None, school_id=None):
    """Logs user activity in the database."""
    from app.models import db, ActivityLog
    try:
        # Auto-detect school_id from user if not provided
        if school_id is None:
            from app.models import User
            user = db.session.get(User, user_id)
            if user:
                school_id = user.school_id

        log = ActivityLog(
            user_id=user_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details,
            ip_address=request.remote_addr if request else '127.0.0.1',
            school_id=school_id
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Failed to log activity: {e}")

def generate_random_password(length=4):
    """Generates a random 4-character password with lowercase, number, and symbol."""
    lower = string.ascii_lowercase
    digits = string.digits
    symbols = "!@#$%^&*"
    all_chars = lower + digits + symbols
    
    password = [
        random.choice(lower),
        random.choice(digits),
        random.choice(symbols),
        random.choice(all_chars)
    ]
    random.shuffle(password)
    return ''.join(password[:length])

def generate_class_code(length=6):
    from app.models import Course
    characters = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(random.choices(characters, k=length))
        if not Course.query.filter_by(class_code=code).first():
            return code

def get_courses_for_user(user, year_id):
    from app.models import Course, User, UserRole, UserCourseOrder
    if not year_id:
        return []
    
    query = Course.query.options(joinedload(Course.teacher))
    
    # Outer join with UserCourseOrder for the current user
    query = query.outerjoin(
        UserCourseOrder, 
        (UserCourseOrder.course_id == Course.id) & (UserCourseOrder.user_id == user.id)
    )
    
    if user.role == UserRole.GURU:
        query = query.filter(Course.teacher_id == user.id, Course.academic_year_id == year_id)
    else:
        query = query.join(Course.students).filter(User.id == user.id, Course.academic_year_id == year_id)
        
    # Order by manual_order first (coalesce NULL to 0), then by name
    return query.order_by(func.coalesce(UserCourseOrder.manual_order, 0), Course.name).all()

def format_course_data(course, user):
    return {
        'id': course.id,
        'name': course.name,
        'teacher': {
            'name': course.teacher.name
        },
        'studentCount': len(course.students),
        'classCode': course.class_code,
        'color': course.color,
        'is_teacher': course.teacher_id == user.id,
    }

def sanitize_text(value: str, max_len: int = 150) -> str:
    if value is None:
        return ''
    s = value.strip()
    s = re.sub(r'<[^>]*?>', '', s)
    s = html.escape(s)
    if len(s) > max_len:
        s = s[:max_len]
    return s

def sanitize_rich_text(value: str, max_len: int = 5000) -> str:
    """Sanitize rich text HTML, allowing only safe formatting tags."""
    if value is None:
        return ''
    s = value.strip()
    allowed_tags = {'b', 'i', 'u', 'strong', 'em', 'ol', 'ul', 'li', 'br', 'p', 'div'}
    def replace_tag(match):
        tag_content = match.group(1)
        tag_name = re.match(r'/?(\w+)', tag_content)
        if tag_name and tag_name.group(1).lower() in allowed_tags:
            return match.group(0)
        return ''
    s = re.sub(r'<([^>]*?)>', replace_tag, s)
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
