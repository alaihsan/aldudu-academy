from flask import abort
from flask_login import current_user
from app.models import UserRole


def get_school_id_or_abort():
    """Get the current user's school_id, or abort 403 if not set.
    
    Superadmin users are exempt and can access all resources.
    """
    # Superadmin can access everything without school_id
    if current_user.role == UserRole.SUPER_ADMIN:
        return None
    
    school_id = current_user.school_id
    if not school_id:
        abort(403, description='Akun tidak terhubung ke sekolah manapun')
    return school_id


def verify_user_in_school(user, school_id):
    """Verify that a given user belongs to the specified school."""
    if user.school_id != school_id:
        abort(403, description='Tidak memiliki izin untuk mengakses user ini')


def verify_course_in_school(course, school_id):
    """Verify that a course belongs to the specified school via its academic year."""
    if not course.academic_year or course.academic_year.school_id != school_id:
        abort(403, description='Kelas tidak ditemukan di sekolah ini')


def verify_academic_year_in_school(year_id, school_id):
    """Verify an academic year belongs to the school."""
    from app.models import AcademicYear
    from app.extensions import db
    year = db.session.get(AcademicYear, year_id)
    if not year or year.school_id != school_id:
        abort(400, description='Tahun ajaran tidak valid untuk sekolah ini')
    return year
