"""
Seeds a throwaway SQLite database with fixtures for the Playwright smoke
suite: one school, one teacher, one student (enrolled), one course, and
one published quiz with a single question so the "take quiz" flow has
something real to click through.

Not a general-purpose demo/seed script — only creates what smoke.spec.js
needs. Re-run freely; it drops and recreates all tables each time.
"""
import os
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DB_PATH = ROOT / 'instance' / 'e2e_test.db'
os.environ.setdefault('SECRET_KEY', 'e2e-smoke-test-secret-key-not-for-prod-32chars')
os.environ.setdefault('DATABASE_URL', f'sqlite:///{DB_PATH}')

from app import create_app  # noqa: E402
from app.core.extensions import db  # noqa: E402
from app.models import School, SchoolStatus, User, UserRole  # noqa: E402
from app.courses.models import Course, AcademicYear  # noqa: E402
from app.quiz.models import Quiz, QuizStatus, Question, QuestionType, Option  # noqa: E402

# NOT *.test/*.example/*.invalid — email_validator (used by the real login
# API) rejects those as RFC 2606 reserved domains, which would make every
# login in this suite fail with a spurious "not registered" error.
TEACHER_EMAIL = 'teacher@aldudu-e2e.dev'
STUDENT_EMAIL = 'student@aldudu-e2e.dev'
PASSWORD = 'Password123!'

app = create_app(test_config={
    'SQLALCHEMY_DATABASE_URI': os.environ['DATABASE_URL'],
    'WTF_CSRF_ENABLED': False,
})

with app.app_context():
    db.drop_all()
    db.create_all()

    school = School(
        name='E2E School', slug='e2e-school', email='school@aldudu-e2e.dev',
        admin_email='admin@aldudu-e2e.dev', status=SchoolStatus.ACTIVE,
    )
    db.session.add(school)
    db.session.commit()

    teacher = User(name='E2E Teacher', email=TEACHER_EMAIL, role=UserRole.GURU,
                    email_verified=True, school_id=school.id)
    teacher.set_password(PASSWORD)
    student = User(name='E2E Student', email=STUDENT_EMAIL, role=UserRole.MURID,
                    email_verified=True, school_id=school.id)
    student.set_password(PASSWORD)
    db.session.add_all([teacher, student])
    db.session.commit()

    year = AcademicYear(year=str(datetime.now().year), is_active=True, school_id=school.id)
    db.session.add(year)
    db.session.commit()

    course = Course(name='E2E Course', class_code='E2E1234', teacher_id=teacher.id,
                     academic_year_id=year.id)
    db.session.add(course)
    db.session.commit()
    course.students.append(student)
    db.session.commit()

    quiz = Quiz(name='E2E Quiz', description='Smoke test quiz', course_id=course.id,
                points=100, status=QuizStatus.PUBLISHED, duration=0, max_attempts=0)
    db.session.add(quiz)
    db.session.commit()

    question = Question(question_text='2 + 2 = ?', question_type=QuestionType.MULTIPLE_CHOICE,
                         quiz_id=quiz.id, order=1, points=10)
    db.session.add(question)
    db.session.commit()
    db.session.add_all([
        Option(option_text='4', is_correct=True, question_id=question.id, order=1),
        Option(option_text='5', is_correct=False, question_id=question.id, order=2),
    ])
    db.session.commit()

    print('SEED_OK course_id=%d quiz_id=%d' % (course.id, quiz.id))
