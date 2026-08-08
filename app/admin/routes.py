from flask import Blueprint, render_template, request, jsonify, abort
import re
import logging
from flask_login import login_required, current_user
from app.models import db, User, UserRole, ActivityLog, Course, AcademicYear, QuizSubmission, Quiz, School
from app.helpers import log_activity, sanitize_text, is_valid_email, generate_random_password, validate_password, generate_class_code
from sqlalchemy import func
from app.core.authorization import get_school_id_or_abort

logger = logging.getLogger(__name__)

# Password default untuk siswa hasil import
DEFAULT_STUDENT_PASSWORD = 'passwd'

admin_bp = Blueprint('admin', __name__, url_prefix='/admin', template_folder='templates')


@admin_bp.before_request
@login_required
def admin_required():
    if current_user.role.value not in ['admin', 'super_admin']:
        abort(403)
    # Only regular admin must have a school_id; superadmin can access all
    if current_user.role == UserRole.ADMIN and not current_user.school_id:
        abort(403, description='Akun admin tidak terhubung ke sekolah')

@admin_bp.route('/dashboard')
def dashboard():
    school_id = current_user.school_id
    # Statistics - filtered by school
    stats = {
        'total_guru': User.query.filter_by(role=UserRole.GURU, school_id=school_id).count(),
        'total_murid': User.query.filter_by(role=UserRole.MURID, school_id=school_id).count(),
        'total_courses': Course.query.join(AcademicYear).filter(AcademicYear.school_id == school_id).count(),
        'total_submissions': QuizSubmission.query.join(Quiz).join(Course).join(AcademicYear).filter(AcademicYear.school_id == school_id).count()
    }

    # Recent Activities - filtered by school
    recent_logs = ActivityLog.query.filter_by(school_id=school_id).order_by(ActivityLog.created_at.desc()).limit(20).all()

    return render_template('admin/admin_dashboard.html', stats=stats, recent_logs=recent_logs)

@admin_bp.route('/users')
def user_management():
    school_id = current_user.school_id
    gurus = User.query.filter_by(role=UserRole.GURU, school_id=school_id).order_by(User.name).all()
    murids = User.query.filter_by(role=UserRole.MURID, school_id=school_id).order_by(User.name).all()
    courses = (Course.query.join(AcademicYear)
               .filter(AcademicYear.school_id == school_id)
               .order_by(Course.name).all())
    return render_template('admin/admin_users.html', gurus=gurus, murids=murids, courses=courses)


@admin_bp.route('/api/users', methods=['GET'])
def api_get_users():
    """Get list of users (guru and murid) with pagination."""
    role_filter = request.args.get('role')  # 'guru', 'murid', or None for all
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    per_page = min(per_page, 100)

    school_id = current_user.school_id
    query = User.query.filter_by(school_id=school_id)

    if role_filter:
        try:
            role = UserRole(role_filter)
            query = query.filter_by(role=role)
        except ValueError:
            pass

    # Order by role (guru first) then by name
    pagination = query.order_by(User.role.desc(), User.name).paginate(
        page=page, per_page=per_page, error_out=False
    )

    result = []
    for user in pagination.items:
        result.append({
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role.value,
            'is_active': user.is_active,
            'email_verified': user.email_verified,
        })

    return jsonify({
        'success': True,
        'users': result,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
    })

@admin_bp.route('/api/users/bulk-import', methods=['POST'])
def bulk_import_users():
    data = request.get_json() or {}
    raw_text = data.get('raw_data', '')
    role_str = data.get('role', 'murid').lower()
    
    if not raw_text:
        return jsonify({'success': False, 'message': 'Data tidak boleh kosong'}), 400
        
    try:
        role = UserRole(role_str)
    except ValueError:
        return jsonify({'success': False, 'message': 'Role tidak valid'}), 400

    lines = raw_text.strip().split('\n')
    
    # Pre-parse lines to get all emails for a single batch query
    parsed_entries = []
    emails_to_check = set()
    
    for line in lines:
        line = line.strip()
        if not line: continue
        
        parts = re.split(r'\t+| {2,}|[|;,]', line)
        parts = [p.strip() for p in parts if p.strip()]
        
        if len(parts) < 2:
            if ' ' in line and is_valid_email(line.split(' ')[-1]):
                temp_parts = line.split(' ')
                email = temp_parts[-1].lower()
                name = " ".join(temp_parts[:-1])
            else: continue
        else:
            email = parts[-1].lower()
            name = " ".join(parts[:-1])
            
        if is_valid_email(email):
            parsed_entries.append({'name': sanitize_text(name, 100), 'email': email})
            emails_to_check.add(email)

    if not parsed_entries:
        return jsonify({'success': False, 'message': 'Tidak ada data valid yang ditemukan'}), 400

    try:
        # Optimization: Fetch all existing users in this list at once
        existing_users = User.query.filter(User.email.in_(list(emails_to_check))).all()
        existing_emails = {u.email for u in existing_users}
        
        imported_count = 0
        results = []

        for entry in parsed_entries:
            if entry['email'] in existing_emails:
                continue
            
            password = generate_random_password(4)
            user = User(name=entry['name'], email=entry['email'], role=role, school_id=current_user.school_id)
            user.set_password(password)
            db.session.add(user)
            
            # Avoid duplicate in same batch
            existing_emails.add(entry['email'])
            
            results.append({'name': entry['name'], 'email': entry['email'], 'password': password})
            imported_count += 1

        db.session.commit()
        log_activity(current_user.id, f"Impor massal {imported_count} {role.value}", details=f"Mendaftarkan {imported_count} user baru.")

        return jsonify({'success': True, 'count': imported_count, 'results': results})
    except Exception as e:
        db.session.rollback()
        logger.error(f"IMPORT ERROR: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': f'Gagal menyimpan ke database: {str(e)}'}), 500

@admin_bp.route('/api/users/<int:user_id>/reset-password', methods=['POST'])
def reset_password(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User tidak ditemukan'}), 404

    if user.school_id != current_user.school_id:
        return jsonify({'success': False, 'message': 'Tidak memiliki izin'}), 403

    data = request.get_json() or {}
    new_password = data.get('password', '').strip()

    is_valid, error_msg = validate_password(new_password)
    if not is_valid:
        return jsonify({'success': False, 'message': error_msg}), 400
        
    user.set_password(new_password)
    db.session.commit()
    
    log_activity(current_user.id, f"Reset password user: {user.email}", target_id=user.id)
    return jsonify({'success': True, 'message': 'Password berhasil diubah'})

@admin_bp.route('/api/users/<int:user_id>/toggle-status', methods=['POST'])
def toggle_user_status(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User tidak ditemukan'}), 404

    if user.school_id != current_user.school_id:
        return jsonify({'success': False, 'message': 'Tidak memiliki izin'}), 403

    if user.id == current_user.id:
        return jsonify({'success': False, 'message': 'Anda tidak dapat menonaktifkan akun sendiri'}), 400
        
    user.is_active = not user.is_active
    db.session.commit()
    
    action = "Mengaktifkan" if user.is_active else "Menonaktifkan"
    log_activity(current_user.id, f"{action} akun: {user.email}", target_type="User", target_id=user.id)

    return jsonify({'success': True, 'is_active': user.is_active})

@admin_bp.route('/api/users/<int:user_id>/rename', methods=['PATCH'])
def rename_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User tidak ditemukan'}), 404

    if user.school_id != current_user.school_id:
        return jsonify({'success': False, 'message': 'Tidak memiliki izin'}), 403

    if user.role not in (UserRole.GURU, UserRole.MURID):
        return jsonify({'success': False, 'message': 'Hanya guru dan murid yang bisa direname'}), 403

    data = request.get_json() or {}
    new_name = sanitize_text(data.get('name', '').strip(), 100)
    if len(new_name) < 2:
        return jsonify({'success': False, 'message': 'Nama minimal 2 karakter'}), 400

    old_name = user.name
    user.name = new_name
    db.session.commit()

    log_activity(current_user.id, f"Rename user: {old_name} -> {new_name}", target_type="User", target_id=user.id)
    return jsonify({'success': True, 'name': user.name})


# ─── Kelas & Import Siswa ────────────────────────────────────────────────────

def _student_email_from_nis(nis, school):
    """Email sintetis dari NIS (siswa login pakai NIS, email hanya kunci unik internal)."""
    slug = (school.slug if school and school.slug else f'sekolah{school.id if school else 0}')
    return f"{nis}@{slug}.siswa.id"


def _normalize_gender(value):
    """Normalisasi jenis kelamin ke 'L' / 'P' (atau None)."""
    v = (value or '').strip().lower()
    if not v:
        return None
    if v[0] == 'l':  # Laki-laki / L
        return 'L'
    if v[0] == 'p':  # Perempuan / P
        return 'P'
    return None


def _active_academic_year(school_id):
    """Ambil tahun ajaran aktif sekolah; buat default bila belum ada."""
    year = AcademicYear.query.filter_by(school_id=school_id, is_active=True).first()
    if not year:
        year = AcademicYear.query.filter_by(year='2025/2026', school_id=school_id).first()
    if not year:
        year = AcademicYear(year='2025/2026', is_active=True, school_id=school_id)
        db.session.add(year)
        db.session.flush()
    return year


def _get_or_create_class(name, school_id, teacher_id, year):
    """Cari kelas berdasarkan nama (dalam sekolah); buat baru bila tidak ada.

    Returns: (course, created_bool)
    """
    existing = (Course.query.join(AcademicYear)
                .filter(AcademicYear.school_id == school_id,
                        func.lower(Course.name) == name.lower())
                .first())
    if existing:
        return existing, False
    course = Course(
        name=name,
        class_code=generate_class_code(),
        academic_year_id=year.id,
        teacher_id=teacher_id,
    )
    db.session.add(course)
    db.session.flush()
    return course, True


def _school_courses(school_id):
    """Daftar kelas/course satu sekolah (urut nama)."""
    return (Course.query.join(AcademicYear)
            .filter(AcademicYear.school_id == school_id)
            .order_by(Course.name).all())


def _parse_student_line(line):
    """Parse satu baris: NIS, Nama Lengkap, Jenis Kelamin[, Kelas].

    Kolom "Kelas" opsional — bila tidak ada, dipakai kelas tujuan dari dropdown.
    """
    raw = line.rstrip('\n').rstrip('\r')
    if '\t' in raw:
        # Format Excel: jangan buang kolom kosong agar posisi tetap
        parts = [p.strip() for p in raw.split('\t')]
    else:
        parts = [p.strip() for p in re.split(r' {2,}|[|;]', raw) if p.strip()]
    if len(parts) < 3:
        return None
    nis = parts[0].strip()
    name = sanitize_text(parts[1], 100)
    gender = _normalize_gender(parts[2])
    kelas = sanitize_text(parts[3], 150) if len(parts) >= 4 and parts[3] else None
    if not nis or not name:
        return None
    return {'nis': nis, 'name': name, 'gender': gender, 'kelas': kelas}


@admin_bp.route('/api/classes', methods=['POST'])
def create_class():
    """Buat kelas baru untuk sekolah admin. Admin menjadi pengampu kelas."""
    data = request.get_json() or {}
    name = sanitize_text((data.get('name') or '').strip(), 150)
    if len(name) < 2:
        return jsonify({'success': False, 'message': 'Nama kelas minimal 2 karakter'}), 400

    try:
        year = _active_academic_year(current_user.school_id)
        course, created = _get_or_create_class(name, current_user.school_id, current_user.id, year)
        if not created:
            return jsonify({'success': False, 'message': f'Kelas "{name}" sudah ada'}), 409
        db.session.commit()
        log_activity(current_user.id, f"Membuat kelas: {course.name}",
                     target_type="Course", target_id=course.id)
        return jsonify({'success': True, 'class': {
            'id': course.id, 'name': course.name, 'class_code': course.class_code,
        }})
    except Exception as e:
        db.session.rollback()
        logger.error(f"CREATE CLASS ERROR: {e}", exc_info=True)
        return jsonify({'success': False, 'message': f'Gagal membuat kelas: {e}'}), 500


@admin_bp.route('/api/students/bulk-import', methods=['POST'])
def bulk_import_students():
    """Import siswa via paste Excel: NIS, Nama Lengkap, Jenis Kelamin, Kelas.

    Tiap baris didaftarkan ke kelas pada kolom "Kelas" (dibuat otomatis bila belum ada).
    """
    data = request.get_json() or {}
    raw_text = data.get('raw_data', '')
    target_course_id = data.get('course_id')  # kelas tujuan default (opsional)

    if not raw_text or not raw_text.strip():
        return jsonify({'success': False, 'message': 'Data siswa tidak boleh kosong'}), 400

    # Kelas tujuan default dari dropdown (bila dipilih)
    target_course = db.session.get(Course, target_course_id) if target_course_id else None
    if target_course and target_course.academic_year.school_id != current_user.school_id:
        return jsonify({'success': False, 'message': 'Kelas tujuan tidak valid'}), 400

    # Parse semua baris (lewati baris header bila ada)
    parsed = []
    seen_nis = set()
    for line in raw_text.strip().split('\n'):
        if not line.strip():
            continue
        row = _parse_student_line(line)
        if not row:
            continue
        # Lewati baris header (mis. "NIS  Nama Lengkap ...")
        if not any(ch.isdigit() for ch in row['nis']):
            continue
        # Tentukan kelas: kolom "Kelas" di baris, atau kelas tujuan dropdown
        if not row['kelas']:
            if not target_course:
                continue  # tak ada kelas untuk baris ini
            row['kelas'] = target_course.name
        if row['nis'] in seen_nis:
            continue
        seen_nis.add(row['nis'])
        parsed.append(row)

    if not parsed:
        return jsonify({'success': False,
                        'message': 'Tidak ada data valid. Pilih kelas tujuan atau sertakan kolom Kelas. Format: NIS, Nama Lengkap, Jenis Kelamin, Kelas'}), 400

    try:
        school = db.session.get(School, current_user.school_id)
        year = _active_academic_year(current_user.school_id)

        existing = {u.nis: u for u in User.query.filter(User.nis.in_(list(seen_nis))).all()}
        class_cache = {}          # nama-kelas(lower) -> Course
        enrolled_cache = {}       # course.id -> set(user_id)
        created_students = 0
        created_classes = []
        enrolled = 0
        results = []

        for row in parsed:
            nis, name, gender, kelas = row['nis'], row['name'], row['gender'], row['kelas']

            # Kelas (get-or-create, di-cache)
            key = kelas.lower()
            course = class_cache.get(key)
            if course is None:
                course, was_created = _get_or_create_class(kelas, current_user.school_id, current_user.id, year)
                class_cache[key] = course
                enrolled_cache[course.id] = {s.id for s in course.students}
                if was_created:
                    created_classes.append(course.name)

            # Siswa (get-or-create berdasarkan NIS)
            user = existing.get(nis)
            if user is None:
                user = User(
                    name=name,
                    nis=nis,
                    gender=gender,
                    email=_student_email_from_nis(nis, school),
                    role=UserRole.MURID,
                    school_id=current_user.school_id,
                    is_active=True,
                    email_verified=True,
                )
                user.set_password(DEFAULT_STUDENT_PASSWORD)
                db.session.add(user)
                db.session.flush()
                existing[nis] = user
                created_students += 1
                status = 'baru'
            else:
                if gender and not user.gender:
                    user.gender = gender
                status = 'sudah ada'

            # Enroll ke kelas baris ini
            if user.id not in enrolled_cache[course.id]:
                course.students.append(user)
                enrolled_cache[course.id].add(user.id)
                enrolled += 1

            results.append({'nis': nis, 'name': name, 'kelas': course.name, 'status': status})

        db.session.commit()
        log_activity(
            current_user.id,
            f"Import {created_students} siswa baru",
            details=f"{created_students} siswa dibuat, {enrolled} enrollment, {len(created_classes)} kelas baru.",
        )
        return jsonify({
            'success': True,
            'created_students': created_students,
            'enrolled': enrolled,
            'created_classes': created_classes,
            'default_password': DEFAULT_STUDENT_PASSWORD,
            'results': results,
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"IMPORT SISWA ERROR: {e}", exc_info=True)
        return jsonify({'success': False, 'message': f'Gagal menyimpan: {e}'}), 500


# ─── Manajemen Kelas ─────────────────────────────────────────────────────────

def _verify_class_in_school(course):
    """Pastikan kelas milik sekolah admin; abort 403/404 bila tidak."""
    if not course:
        abort(404)
    if course.academic_year.school_id != current_user.school_id:
        abort(403)


@admin_bp.route('/classes')
def classes_management():
    """Halaman Manajemen Kelas — daftar semua kelas sekolah."""
    courses = _school_courses(current_user.school_id)
    return render_template('admin/admin_classes.html', courses=courses)


@admin_bp.route('/classes/<int:course_id>')
def class_detail(course_id):
    """Detail kelas — daftar siswa, edit nama, mutasi, impor."""
    course = db.session.get(Course, course_id)
    _verify_class_in_school(course)
    students = sorted(course.students, key=lambda s: (s.name or '').lower())
    other_classes = [c for c in _school_courses(current_user.school_id) if c.id != course.id]
    return render_template('admin/admin_class_detail.html',
                           course=course, students=students, other_classes=other_classes)


@admin_bp.route('/api/classes/<int:course_id>', methods=['PATCH'])
def rename_class(course_id):
    """Ubah nama kelas."""
    course = db.session.get(Course, course_id)
    _verify_class_in_school(course)
    data = request.get_json() or {}
    new_name = sanitize_text((data.get('name') or '').strip(), 150)
    if len(new_name) < 2:
        return jsonify({'success': False, 'message': 'Nama kelas minimal 2 karakter'}), 400

    # Cegah duplikat nama dalam sekolah
    dup = (Course.query.join(AcademicYear)
           .filter(AcademicYear.school_id == current_user.school_id,
                   func.lower(Course.name) == new_name.lower(),
                   Course.id != course.id).first())
    if dup:
        return jsonify({'success': False, 'message': f'Kelas "{new_name}" sudah ada'}), 409

    old = course.name
    course.name = new_name
    db.session.commit()
    log_activity(current_user.id, f"Ubah nama kelas: {old} -> {new_name}",
                 target_type="Course", target_id=course.id)
    return jsonify({'success': True, 'name': course.name})


@admin_bp.route('/api/students/<int:student_id>/transfer', methods=['POST'])
def transfer_student(student_id):
    """Mutasi siswa: pindah dari satu kelas ke kelas lain (dalam sekolah)."""
    student = db.session.get(User, student_id)
    if not student or student.school_id != current_user.school_id or student.role != UserRole.MURID:
        return jsonify({'success': False, 'message': 'Siswa tidak valid'}), 400

    data = request.get_json() or {}
    from_course = db.session.get(Course, data.get('from_course_id')) if data.get('from_course_id') else None
    to_course = db.session.get(Course, data.get('to_course_id'))

    _verify_class_in_school(to_course)
    if from_course:
        _verify_class_in_school(from_course)

    try:
        if from_course and student in from_course.students:
            from_course.students.remove(student)
        if student not in to_course.students:
            to_course.students.append(student)
        db.session.commit()
        log_activity(current_user.id,
                     f"Mutasi siswa {student.name} ke kelas {to_course.name}",
                     target_type="User", target_id=student.id)
        return jsonify({'success': True, 'to_class': to_course.name})
    except Exception as e:
        db.session.rollback()
        logger.error(f"TRANSFER STUDENT ERROR: {e}", exc_info=True)
        return jsonify({'success': False, 'message': f'Gagal mutasi: {e}'}), 500
