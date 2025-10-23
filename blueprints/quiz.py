# blueprints/quiz.py

from flask import Blueprint, request, jsonify, abort
from flask_login import login_required, current_user
# PASTIKAN models.py diimpor dengan benar (termasuk GradeType jika ada)
from models import db, Course, Quiz, UserRole, GradeType 
from helpers import sanitize_text
import datetime

quiz_bp = Blueprint('quiz', __name__, url_prefix='/api')


@quiz_bp.route('/courses/<int:course_id>/quizzes', methods=['POST'])
@login_required
def api_create_quiz(course_id):
    """
    Membuat kuis baru untuk sebuah mata pelajaran.
    Hanya guru yang mengajar mata pelajaran tersebut yang bisa mengakses.
    """
    
    # ... (Validasi 1, 2, 3 tetap sama) ...
    # 1. Validasi: Hanya guru yang bisa membuat kuis
    if current_user.role != UserRole.GURU:
        return jsonify({'success': False, 'message': 'Hanya guru yang dapat membuat kuis'}), 403

    # 2. Validasi: Temukan mata pelajarannya
    course = db.session.get(Course, course_id)
    if not course:
        return jsonify({'success': False, 'message': 'Mata pelajaran tidak ditemukan'}), 404

    # 3. Validasi Keamanan: Pastikan guru ini adalah pemilik mata pelajaran
    if course.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'Anda tidak memiliki izin untuk menambah kuis di mata pelajaran ini'}), 403

    # 4. Ambil dan bersihkan data input
    data = request.get_json() or {}
    name = sanitize_text(data.get('name', ''), max_len=200)
    
    if not name:
        return jsonify({'success': False, 'message': 'Nama kuis wajib diisi'}), 400
    
    # --- AMBIL DATA BARU ---
    points = data.get('points', 100)
    category = sanitize_text(data.get('category', ''), max_len=100)
    grade_type_str = data.get('grade_type', 'numeric')
    
    try:
        grade_type = GradeType(grade_type_str)
    except ValueError:
        grade_type = GradeType.NUMERIC # Default

    # Konversi tanggal (handle string kosong atau None)
    def parse_datetime(dt_str):
        if not dt_str:
            return None
        try:
            # Format 'YYYY-MM-DDTHH:MM'
            return datetime.datetime.fromisoformat(dt_str)
        except (ValueError, TypeError):
            return None

    start_date = parse_datetime(data.get('start_date'))
    end_date = parse_datetime(data.get('end_date'))
    # --- AKHIR PENGAMBILAN DATA ---

    # 5. Buat kuis di database
    try:
        new_quiz = Quiz(
            name=name,
            course_id=course_id,
            # --- SIMPAN DATA BARU ---
            start_date=start_date,
            end_date=end_date,
            points=points,
            grading_category=category if category else None, # Simpan None jika string kosong
            grade_type=grade_type
        )
        db.session.add(new_quiz)
        db.session.commit()
        
        # 6. Kembalikan data kuis yang baru dibuat
        return jsonify({
            'success': True,
            # Anda bisa menambahkan data baru di sini jika diperlukan oleh JS
            'quiz': {
                'id': new_quiz.id,
                'name': new_quiz.name,
                'course_id': new_quiz.course_id
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Terjadi kesalahan server: {e}'}), 500