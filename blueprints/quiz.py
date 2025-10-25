# blueprints/quiz.py

from flask import (
    Blueprint, request, jsonify, abort, 
    render_template, make_response
)
from flask_login import login_required, current_user
# --- Impor model yang diperlukan ---
from models import (
    db, Course, Quiz, UserRole, GradeType, 
    Question, Option, QuestionType
)
from helpers import sanitize_text
import datetime

quiz_bp = Blueprint('quiz', __name__, url_prefix='/api')


# --- Fungsi Helper Validasi ---

def get_quiz_or_abort(quiz_id, check_teacher=True):
    """Helper untuk mengambil kuis dan memvalidasi izin guru."""
    quiz = db.session.get(Quiz, quiz_id)
    if not quiz:
        abort(404, description="Kuis tidak ditemukan.")
    
    if check_teacher and quiz.course.teacher_id != current_user.id:
        abort(403, description="Anda tidak memiliki izin untuk mengedit kuis ini.")
    
    # Keamanan tambahan: Cek jika murid mencoba mengakses
    if current_user.role == UserRole.MURID:
         if current_user not in quiz.course.students:
             abort(403, description="Anda tidak terdaftar di kelas ini.")
             
    return quiz

def get_question_or_abort(question_id, check_teacher=True):
    """Helper untuk mengambil pertanyaan dan memvalidasi izin."""
    question = db.session.get(Question, question_id)
    if not question:
        abort(404, description="Pertanyaan tidak ditemukan.")
    
    if check_teacher and question.quiz.course.teacher_id != current_user.id:
        abort(403, description="Anda tidak memiliki izin untuk mengedit pertanyaan ini.")
        
    return question

def get_option_or_abort(option_id, check_teacher=True):
    """Helper untuk mengambil opsi dan memvalidasi izin."""
    option = db.session.get(Option, option_id)
    if not option:
        abort(404, description="Opsi tidak ditemukan.")
    
    if check_teacher and option.question.quiz.course.teacher_id != current_user.id:
        abort(403, description="Anda tidak memiliki izin untuk mengedit opsi ini.")
        
    return option


# --- Rute API Asli (Membuat Kuis) ---

@quiz_bp.route('/courses/<int:course_id>/quizzes', methods=['POST'])
@login_required
def api_create_quiz(course_id):
    """
    Membuat kuis baru untuk sebuah mata pelajaran.
    Hanya guru yang mengajar mata pelajaran tersebut yang bisa mengakses.
    """
    
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
    
    points = data.get('points', 100)
    category = sanitize_text(data.get('category', ''), max_len=100)
    grade_type_str = data.get('grade_type', 'numeric')
    
    try:
        grade_type = GradeType(grade_type_str)
    except ValueError:
        grade_type = GradeType.NUMERIC # Default

    def parse_datetime(dt_str):
        if not dt_str:
            return None
        try:
            return datetime.datetime.fromisoformat(dt_str)
        except (ValueError, TypeError):
            return None

    start_date = parse_datetime(data.get('start_date'))
    end_date = parse_datetime(data.get('end_date'))

    # 5. Buat kuis di database
    try:
        new_quiz = Quiz(
            name=name,
            course_id=course_id,
            start_date=start_date,
            end_date=end_date,
            points=points,
            grading_category=category if category else None, 
            grade_type=grade_type
        )
        db.session.add(new_quiz)
        db.session.commit()
        
        # 6. Kembalikan data kuis yang baru dibuat
        return jsonify({
            'success': True,
            'quiz': {
                'id': new_quiz.id,
                'name': new_quiz.name,
                'course_id': new_quiz.course_id
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Terjadi kesalahan server: {e}'}), 500


# ---
# RUTE-RUTE BARU UNTUK HTMX QUIZ BUILDER
# ---

@quiz_bp.route('/quiz/<int:quiz_id>/question/add', methods=['POST'])
@login_required
def api_add_question(quiz_id):
    """HTMX: Membuat pertanyaan baru dan mengembalikan HTML-nya."""
    quiz = get_quiz_or_abort(quiz_id) # Memvalidasi izin guru
    
    # Tentukan urutan untuk pertanyaan baru
    last_question = quiz.questions.order_by(Question.order.desc()).first()
    new_order = (last_question.order + 1) if last_question else 1
    
    new_question = Question(
        quiz_id=quiz.id,
        question_text=f"Pertanyaan Baru {new_order}",
        question_type=QuestionType.MULTIPLE_CHOICE,
        order=new_order
    )
    db.session.add(new_question)
    
    # Buat 4 opsi default untuk Tipe Pilihan Ganda
    default_options = [
        Option(question_id=new_question.id, option_text="Opsi A", order=1),
        Option(question_id=new_question.id, option_text="Opsi B", order=2),
        Option(question_id=new_question.id, option_text="Opsi C", order=3),
        Option(question_id=new_question.id, option_text="Opsi D", order=4),
    ]
    db.session.add_all(default_options)
    db.session.commit()

    # --- PERBAIKAN PENTING ---
    # Refresh objek 'new_question' agar ia tahu tentang opsi-opsi 
    # yang baru saja kita simpan di database.
    db.session.refresh(new_question)
    
    # Render *hanya* partial HTML untuk pertanyaan baru
    return render_template(
        '_question_form.html', 
        question=new_question, 
        QuestionType=QuestionType
    )

@quiz_bp.route('/question/<int:question_id>/update', methods=['PUT'])
@login_required
def api_update_question(question_id):
    """HTMX: Autosave untuk teks pertanyaan (dipicu oleh hx-trigger='blur')."""
    question = get_question_or_abort(question_id)
    
    # 'request.form' digunakan karena HTMX mengirim sebagai form data
    new_text = request.form.get('question_text', '').strip()
    
    if not new_text:
        new_text = "Pertanyaan tidak boleh kosong"
        
    question.question_text = sanitize_text(new_text, max_len=5000)
    db.session.commit()
    
    # Kirim kembali nilai yang sudah bersih untuk disinkronkan ke input
    return f'<input type="text" name="question_text" class="question-title-input" value="{question.question_text}" hx-put="/api/question/{question.id}/update" hx-trigger="blur" hx-swap="outerHTML" />'

@quiz_bp.route('/question/<int:question_id>/change-type', methods=['POST'])
@login_required
def api_change_question_type(question_id):
    """HTMX: Mengubah tipe pertanyaan (PG <-> B/S)."""
    question = get_question_or_abort(question_id)
    new_type_str = request.form.get('question_type')
    
    try:
        new_type = QuestionType(new_type_str)
    except ValueError:
        return "Tipe tidak valid", 400

    question.question_type = new_type
    
    # Hapus semua opsi jawaban yang ada
    Option.query.filter_by(question_id=question.id).delete()
    
    # Jika tipenya Benar/Salah, buat opsi B/S yang baru
    if new_type == QuestionType.TRUE_FALSE:
        true_opt = Option(question_id=question.id, option_text="Benar", order=1, is_correct=False)
        false_opt = Option(question_id=question.id, option_text="Salah", order=2, is_correct=False)
        db.session.add_all([true_opt, false_opt])
    
    # Jika tipenya Pilihan Ganda, buat 1 opsi kosong
    elif new_type == QuestionType.MULTIPLE_CHOICE:
        empty_opt = Option(question_id=question.id, option_text="Opsi 1", order=1, is_correct=False)
        db.session.add(empty_opt)
        
    db.session.commit()
    db.session.refresh(question) # Refresh untuk memuat opsi baru

    # Render ulang *hanya* bagian <div id="answer-options-...">
    return render_template('_answer_options.html', question=question)

@quiz_bp.route('/question/<int:question_id>/delete', methods=['DELETE'])
@login_required
def api_delete_question(question_id):
    """HTMX: Menghapus pertanyaan (dan mengembalikan respons kosong)."""
    question = get_question_or_abort(question_id)
    
    # cascade='all, delete-orphan' di model akan menghapus semua opsi
    db.session.delete(question)
    db.session.commit()
    
    # Mengembalikan respons 200 OK tanpa konten
    # HTMX akan otomatis menghapus elemen dari DOM
    return "", 200

@quiz_bp.route('/question/<int:question_id>/set-correct', methods=['POST'])
@login_required
def api_question_set_correct_option(question_id):
    """HTMX: Autosave untuk KUNCI JAWABAN (radio button)."""
    question = get_question_or_abort(question_id)
    
    # Ambil ID opsi yang dipilih dari form
    selected_option_id = request.form.get(f'correct_option_q{question.id}')
    
    if not selected_option_id:
        return "Opsi ID tidak ditemukan", 400
        
    try:
        selected_option_id = int(selected_option_id)
    except ValueError:
        return "Opsi ID tidak valid", 400

    # 1. Set semua opsi untuk pertanyaan ini menjadi 'is_correct = False'
    for opt in question.options:
        opt.is_correct = False
        
    # 2. Set hanya opsi yang dipilih menjadi 'is_correct = True'
    option_to_set = next((opt for opt in question.options if opt.id == selected_option_id), None)
    
    if option_to_set:
        option_to_set.is_correct = True
    else:
        # Keamanan: Pastikan opsi itu milik pertanyaan ini
        return "Opsi tidak valid untuk pertanyaan ini", 403
        
    db.session.commit()
    
    # Tidak perlu mengembalikan HTML, 
    # karena HTMX hanya memicu 'POST' dan tidak perlu menukar apa pun.
    # Kita bisa mengembalikan header 'HX-Trigger' jika ingin memicu event lain.
    response = make_response("", 204) # 204 No Content
    response.headers['HX-Trigger'] = f'answerKeyUpdated{question.id}'
    return response


# --- Rute API untuk Opsi Jawaban (Pilihan Ganda) ---

@quiz_bp.route('/question/<int:question_id>/option/add', methods=['POST'])
@login_required
def api_add_option(question_id):
    """HTMX: Menambah opsi baru (Pilihan Ganda) ke pertanyaan."""
    question = get_question_or_abort(question_id)
    
    if question.question_type != QuestionType.MULTIPLE_CHOICE:
        return "Hanya pertanyaan Pilihan Ganda yang bisa ditambah opsi", 400

    last_option = question.options.order_by(Option.order.desc()).first()
    new_order = (last_option.order + 1) if last_option else 1
    
    new_option = Option(
        question_id=question.id,
        option_text=f"Opsi {new_order}",
        order=new_order
    )
    db.session.add(new_option)
    db.session.commit()
    
    # Render *hanya* partial HTML untuk opsi baru
    return render_template(
        '_option_form.html', 
        option=new_option, 
        question=question
    )

@quiz_bp.route('/option/<int:option_id>/update', methods=['PUT'])
@login_required
def api_update_option(option_id):
    """HTMX: Autosave untuk teks opsi (Pilihan Ganda)."""
    option = get_option_or_abort(option_id)
    
    new_text = request.form.get('option_text', '').strip()
    if not new_text:
        new_text = "Opsi tidak boleh kosong"
        
    option.option_text = sanitize_text(new_text, max_len=1000)
    db.session.commit()
    
    # Kirim kembali input yang sudah bersih
    return f'<input type="text" name="option_text" class="option-text-input" value="{option.option_text}" hx-put="/api/option/{option.id}/update" hx-trigger="blur" hx-swap="outerHTML" />'

@quiz_bp.route('/option/<int:option_id>/delete', methods=['DELETE'])
@login_required
def api_delete_option(option_id):
    """HTMX: Menghapus opsi (Pilihan Ganda)."""
    option = get_option_or_abort(option_id)
    
    # Jangan biarkan pengguna menghapus opsi terakhir
    if option.question.options.count() <= 1:
        # Mengembalikan 400 Bad Request dengan pesan
        response = make_response("Tidak dapat menghapus opsi terakhir.", 400)
        # Mengirim header HTMX untuk menampilkan pesan alert (jika Anda mau)
        # response.headers['HX-Trigger'] = '{"showAlert": "Tidak dapat menghapus opsi terakhir."}'
        return response
        
    db.session.delete(option)
    db.session.commit()
    
    return "", 200

