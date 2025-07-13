# app.py
from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, AcademicYear, Course, UserRole
import string
import random

# --- FUNGSI HELPER ---
def generate_class_code(length=6):
    """Generate kode kelas alfanumerik yang unik."""
    characters = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(random.choices(characters, k=length))
        if not Course.query.filter_by(class_code=code).first():
            return code

def get_courses_for_user(user, year_id):
    """Helper untuk mengambil kelas berdasarkan peran user dan tahun ajaran."""
    if not year_id:
        return []
    if user.role == UserRole.GURU:
        return Course.query.filter_by(teacher_id=user.id, academic_year_id=year_id).order_by(Course.name).all()
    else: # MURID
        return Course.query.join(User.courses_enrolled).filter(
            User.id == user.id, 
            Course.academic_year_id == year_id
        ).order_by(Course.name).all()

def format_course_data(course, user):
    """Helper untuk memformat data kelas menjadi dictionary."""
    return {
        'id': course.id,
        'name': course.name,
        'teacher': course.teacher.name,
        'studentCount': len(course.students),
        'class_code': course.class_code,
        'is_teacher': course.teacher_id == user.id 
    }

# --- KONFIGURASI APLIKASI ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'kunci-rahasia-yang-sangat-aman-dan-sulit-ditebak-sekali'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///aldudu_academy.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- INISIALISASI EXTENSIONS ---
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'index'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- RUTE HALAMAN (HTML) ---
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('index.html')

@app.route('/kelas/<int:course_id>')
@login_required
def course_detail(course_id):
    course = Course.query.get_or_404(course_id)
    return render_template('course_detail.html', course=course)

# --- API ENDPOINTS (JSON) ---
@app.route('/api/session', methods=['GET'])
def api_session():
    if current_user.is_authenticated:
        return jsonify({'isAuthenticated': True, 'user': {'name': current_user.name, 'role': current_user.role.value}})
    return jsonify({'isAuthenticated': False})

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    user = User.query.filter_by(email=data.get('email')).first()
    if user and user.check_password(data.get('password')):
        login_user(user)
        return jsonify({'success': True, 'user': {'name': user.name, 'role': user.role.value}})
    return jsonify({'success': False, 'message': 'Email atau password salah'}), 401

@app.route('/api/logout', methods=['POST'])
@login_required
def api_logout():
    logout_user()
    return jsonify({'success': True})

@app.route('/api/initial-data', methods=['GET'])
@login_required
def api_initial_data():
    academic_years_query = AcademicYear.query.order_by(AcademicYear.year.desc()).all()
    academic_years = [{'id': ay.id, 'year': ay.year} for ay in academic_years_query]
    active_year_id = academic_years[0]['id'] if academic_years else None
    courses_query = get_courses_for_user(current_user, active_year_id)
    courses = [format_course_data(c, current_user) for c in courses_query]
    return jsonify({'academicYears': academic_years, 'courses': courses})

@app.route('/api/courses/year/<int:year_id>', methods=['GET'])
@login_required
def api_get_courses_by_year(year_id):
    courses_query = get_courses_for_user(current_user, year_id)
    courses = [format_course_data(c, current_user) for c in courses_query]
    return jsonify({'courses': courses})

@app.route('/api/courses', methods=['POST'])
@login_required
def api_create_course():
    if current_user.role != UserRole.GURU:
        return jsonify({'success': False, 'message': 'Hanya guru yang dapat membuat kelas'}), 403
    data = request.get_json()
    new_course = Course(
        name=data.get('name'),
        academic_year_id=data.get('academic_year_id'),
        teacher_id=current_user.id,
        class_code=generate_class_code()
    )
    db.session.add(new_course)
    db.session.commit()
    return jsonify({
        'success': True,
        'course': format_course_data(new_course, current_user)
    }), 201

@app.route('/api/enroll', methods=['POST'])
@login_required
def api_enroll_in_course():
    if current_user.role != UserRole.MURID:
        return jsonify({'success': False, 'message': 'Hanya murid yang bisa bergabung ke kelas'}), 403
    code = request.json.get('class_code', '').upper()
    if not code:
        return jsonify({'success': False, 'message': 'Kode kelas dibutuhkan'}), 400
    course_to_join = Course.query.filter_by(class_code=code).first()
    if not course_to_join:
        return jsonify({'success': False, 'message': f'Kelas dengan kode "{code}" tidak ditemukan'}), 404
    if course_to_join in current_user.courses_enrolled:
        return jsonify({'success': False, 'message': 'Anda sudah terdaftar di kelas ini'}), 409
    current_user.courses_enrolled.append(course_to_join)
    db.session.commit()
    return jsonify({
        'success': True, 
        'message': f'Anda berhasil bergabung dengan kelas {course_to_join.name}',
        'course': format_course_data(course_to_join, current_user)
    })

# --- Perintah CLI ---
@app.cli.command("init-db")
def init_db_command():
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("Membuat data awal...")
        guru = User(name="Bapak Budi", email="guru@aldudu.com", role=UserRole.GURU)
        guru.set_password("123")
        murid = User(name="Siti Murid", email="murid@aldudu.com", role=UserRole.MURID)
        murid.set_password("123")
        ay1 = AcademicYear(year="2024/2025", is_active=True)
        ay2 = AcademicYear(year="2023/2024")
        db.session.add_all([guru, murid, ay1, ay2])
        db.session.commit()
        course1 = Course(name="Matematika XI-A", academic_year_id=ay1.id, teacher_id=guru.id, class_code=generate_class_code())
        course2 = Course(name="Biologi XI-A", academic_year_id=ay1.id, teacher_id=guru.id, class_code=generate_class_code())
        course3 = Course(name="Sejarah X-B", academic_year_id=ay2.id, teacher_id=guru.id, class_code=generate_class_code())
        db.session.add_all([course1, course2, course3])
        murid.courses_enrolled.append(course3)
        db.session.commit()
        print("Database berhasil diinisialisasi.")

if __name__ == '__main__':
    app.run(debug=True)
