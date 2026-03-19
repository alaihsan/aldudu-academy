from flask import (
    Blueprint, request, jsonify, abort,
    render_template, make_response, url_for
)
from flask_login import login_required, current_user
from app.models import (
    db, Course, Quiz, UserRole, GradeType, QuizStatus,
    Question, Option, QuestionType,
    QuizSubmission, Answer
)
from app.helpers import sanitize_text, sanitize_rich_text
import datetime
import os
from werkzeug.utils import secure_filename

quiz_bp = Blueprint('quiz', __name__, url_prefix='/api')

# --- Helper Functions ---

def get_quiz_or_abort(quiz_id, check_teacher=True):
    from app.tenant import get_school_id_or_abort, verify_course_in_school
    quiz = db.session.get(Quiz, quiz_id)
    if not quiz: abort(404, description="Kuis tidak ditemukan.")
    school_id = get_school_id_or_abort()
    verify_course_in_school(quiz.course, school_id)
    if check_teacher and quiz.course.teacher_id != current_user.id:
        abort(403, description="Anda tidak memiliki akses ke kuis ini.")
    return quiz

def get_question_or_abort(question_id, check_teacher=True):
    from app.tenant import get_school_id_or_abort, verify_course_in_school
    question = db.session.get(Question, question_id)
    if not question: abort(404, description="Pertanyaan tidak ditemukan.")
    school_id = get_school_id_or_abort()
    verify_course_in_school(question.quiz.course, school_id)
    if check_teacher and question.quiz.course.teacher_id != current_user.id:
        abort(403, description="Anda tidak memiliki akses ke pertanyaan ini.")
    return question

# --- Routes ---

@quiz_bp.route('/quiz/<int:quiz_id>/question/add', methods=['POST'])
@login_required
def api_add_question(quiz_id):
    quiz = get_quiz_or_abort(quiz_id)
    try:
        q_type_str = request.form.get('question_type', 'MULTIPLE_CHOICE')
        q_type = QuestionType[q_type_str]
    except KeyError:
        q_type = QuestionType.MULTIPLE_CHOICE

    last_q = quiz.questions.order_by(Question.order.desc()).first()
    new_order = (last_q.order + 1) if last_q else 1

    question = Question(
        quiz_id=quiz.id,
        question_text="",
        question_type=q_type,
        order=new_order,
        points=quiz.default_points,
        is_required=quiz.required_by_default
    )
    
    if q_type in [QuestionType.MULTIPLE_CHOICE, QuestionType.DROPDOWN, QuestionType.CHECKBOX]:
        question.options.append(Option(option_text="Opsi 1", order=1))
    elif q_type == QuestionType.TRUE_FALSE:
        question.options.extend([Option(option_text="Benar", order=1), Option(option_text="Salah", order=2)])

    db.session.add(question)
    db.session.commit()
    db.session.refresh(question)
    return render_template('_question_form.html', question=question, QuestionType=QuestionType, Option=Option, Question=Question)

@quiz_bp.route('/question/<int:question_id>/change-type', methods=['POST'])
@login_required
def api_change_question_type(question_id):
    question = get_question_or_abort(question_id)
    try:
        new_type = QuestionType[request.form.get('question_type')]
    except (KeyError, TypeError): return "Invalid type", 400

    current_text = request.form.get('question_text')
    if current_text is not None:
        question.question_text = sanitize_text(current_text)

    if question.question_type != new_type:
        old_type = question.question_type
        question.question_type = new_type
        
        option_types = [QuestionType.MULTIPLE_CHOICE, QuestionType.DROPDOWN, QuestionType.CHECKBOX]
        
        # Only clear options if switching from/to types that are incompatible
        if (old_type in option_types and new_type not in option_types) or \
           (old_type not in option_types and new_type in option_types) or \
           (new_type == QuestionType.TRUE_FALSE):
            
            # --- FIX: Handle existing answers before deleting options ---
            # Set selected_option_id to NULL for all answers pointing to options of this question
            options_ids = [o.id for o in question.options]
            if options_ids:
                Answer.query.filter(Answer.selected_option_id.in_(options_ids)).update({Answer.selected_option_id: None}, synchronize_session=False)
            
            # Now safe to delete options
            Option.query.filter_by(question_id=question.id).delete()
            # ------------------------------------------------------------
            
            if new_type in option_types:
                db.session.add(Option(question_id=question.id, option_text="Opsi 1", order=1))
            elif new_type == QuestionType.TRUE_FALSE:
                db.session.add_all([Option(question_id=question.id, option_text="Benar", order=1), Option(question_id=question.id, option_text="Salah", order=2)])

    # Initialize default upload settings if UPLOAD
    if question.question_type == QuestionType.UPLOAD:
        if not question.max_file_size:
            question.max_file_size = 10
        if not question.allowed_file_types:
            question.allowed_file_types = "pdf,image,document"

    db.session.commit()
    db.session.refresh(question)
    return render_template('_question_form.html', question=question, QuestionType=QuestionType, Option=Option, Question=Question)

@quiz_bp.route('/question/<int:question_id>/duplicate', methods=['POST'])
@login_required
def api_duplicate_question(question_id):
    original_q = get_question_or_abort(question_id)
    
    # Create new question based on original
    new_q = Question(
        quiz_id=original_q.quiz_id,
        question_text=f"{original_q.question_text} (Salinan)",
        question_type=original_q.question_type,
        points=original_q.points,
        is_required=original_q.is_required,
        order=original_q.order + 1
    )
    
    # Shift orders of subsequent questions
    Question.query.filter(Question.quiz_id == original_q.quiz_id, Question.order > original_q.order).update({Question.order: Question.order + 1})
    
    db.session.add(new_q)
    db.session.flush() # Get new_q.id
    
    # Copy options
    for opt in original_q.options:
        new_opt = Option(
            question_id=new_q.id,
            option_text=opt.option_text,
            is_correct=opt.is_correct,
            order=opt.order
        )
        db.session.add(new_opt)
    
    db.session.commit()
    db.session.refresh(new_q)
    
    return render_template('_question_form.html', question=new_q, QuestionType=QuestionType, Option=Option, Question=Question)

@quiz_bp.route('/question/<int:question_id>/update', methods=['PUT'])
@login_required
def api_update_question(question_id):
    question = get_question_or_abort(question_id)
    # Use sanitize_rich_text for potential HTML content from contenteditable
    question.question_text = sanitize_rich_text(request.form.get('question_text', ''))
    db.session.commit()
    # Return contenteditable div with current text
    return f'<div contenteditable="true" class="question-title-input font-bold text-xl w-full border-none focus:ring-0 bg-transparent p-0 placeholder-gray-300 resize-none overflow-hidden min-h-[40px]" data-placeholder="Pertanyaan Tanpa Judul" hx-put="/api/question/{question.id}/update" hx-trigger="blur" hx-ext="editable-submit" name="question_text" onmouseup="checkSelection(event)" onkeyup="checkSelection(event)" style="font-family: var(--font-q);">{question.question_text}</div>'

@quiz_bp.route('/question/<int:question_id>/update-points', methods=['PUT'])
@login_required
def api_update_question_points(question_id):
    question = get_question_or_abort(question_id)
    try:
        question.points = int(request.form.get('points', 0))
        db.session.commit()
    except (ValueError, TypeError):
        pass
    return ""

@quiz_bp.route('/question/<int:question_id>/toggle-required', methods=['POST'])
@login_required
def api_toggle_question_required(question_id):
    question = get_question_or_abort(question_id)
    question.is_required = not question.is_required
    db.session.commit()
    return render_template('_question_form.html', question=question, QuestionType=QuestionType, Option=Option, Question=Question)

@quiz_bp.route('/question/<int:question_id>/set-correct', methods=['POST'])
@login_required
def api_set_correct(question_id):
    question = get_question_or_abort(question_id)
    if question.question_type == QuestionType.CHECKBOX:
        selected_ids = [int(sid) for sid in request.form.getlist(f'correct_option_q{question.id}')]
        for opt in question.options: opt.is_correct = (opt.id in selected_ids)
    else:
        selected_id = int(request.form.get(f'correct_option_q{question.id}', 0))
        for opt in question.options: opt.is_correct = (opt.id == selected_id)
    db.session.commit()
    return ""

@quiz_bp.route('/question/<int:question_id>/option/add', methods=['POST'])
@login_required
def api_add_option(question_id):
    question = get_question_or_abort(question_id)
    last_opt = question.options.order_by(Option.order.desc()).first()
    new_order = (last_opt.order + 1) if last_opt else 1
    new_opt = Option(question_id=question.id, option_text=f"Opsi {new_order}", order=new_order)
    db.session.add(new_opt)
    db.session.commit()
    return render_template('_option_form.html', option=new_opt, question=question, Option=Option)

@quiz_bp.route('/option/<int:option_id>/update', methods=['PUT'])
@login_required
def api_update_option(option_id):
    from app.tenant import get_school_id_or_abort, verify_course_in_school
    option = db.session.get(Option, option_id)
    if not option: abort(404)
    school_id = get_school_id_or_abort()
    verify_course_in_school(option.question.quiz.course, school_id)
    if option.question.quiz.course.teacher_id != current_user.id:
        abort(403)
    option.option_text = sanitize_text(request.form.get('option_text', ''))
    db.session.commit()
    return f'<input type="text" class="option-input" value="{option.option_text}" name="option_text" hx-put="/api/option/{option.id}/update" hx-trigger="blur" hx-swap="outerHTML" placeholder="Opsi {option.order}" />'

@quiz_bp.route('/option/<int:option_id>/delete', methods=['DELETE'])
@login_required
def api_delete_option(option_id):
    from app.tenant import get_school_id_or_abort, verify_course_in_school
    option = db.session.get(Option, option_id)
    if not option: return "", 200
    school_id = get_school_id_or_abort()
    verify_course_in_school(option.question.quiz.course, school_id)
    if option.question.quiz.course.teacher_id != current_user.id:
        abort(403)
    if option.question.options.count() > 1:
        db.session.delete(option)
        db.session.commit()
    return "", 200

@quiz_bp.route('/question/<int:question_id>/delete', methods=['DELETE'])
@login_required
def api_delete_question(question_id):
    db.session.delete(get_question_or_abort(question_id))
    db.session.commit()
    return "", 200

@quiz_bp.route('/quiz/<int:quiz_id>/status', methods=['POST'])
@login_required
def api_set_quiz_status(quiz_id):
    quiz = get_quiz_or_abort(quiz_id)
    data = request.get_json()
    status_str = data.get('status', 'draft')
    try:
        quiz.status = QuizStatus(status_str)
        db.session.commit()
        return jsonify({'success': True, 'status': quiz.status.value})
    except (ValueError, KeyError):
        return jsonify({'success': False}), 400

@quiz_bp.route('/submission/<int:submission_id>')
@login_required
def api_get_submission(submission_id):
    from app.tenant import get_school_id_or_abort, verify_course_in_school
    submission = db.session.get(QuizSubmission, submission_id)
    if not submission:
        abort(404)

    school_id = get_school_id_or_abort()
    verify_course_in_school(submission.quiz.course, school_id)

    is_teacher = submission.quiz.course.teacher_id == current_user.id
    if not is_teacher and submission.user_id != current_user.id:
        abort(403)
        
    return render_template('quiz_submission_detail.html', submission=submission, is_teacher=is_teacher)

@quiz_bp.route('/submission/<int:submission_id>/update-score', methods=['POST'])
@login_required
def api_update_submission_score(submission_id):
    from app.tenant import get_school_id_or_abort, verify_course_in_school
    submission = db.session.get(QuizSubmission, submission_id)
    if not submission:
        abort(404)
    school_id = get_school_id_or_abort()
    verify_course_in_school(submission.quiz.course, school_id)
    if submission.quiz.course.teacher_id != current_user.id:
        abort(403)
    
    data = request.get_json()
    new_score = data.get('score')
    if new_score is not None:
        try:
            submission.score = float(new_score)
            db.session.commit()
            return jsonify({'success': True})
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid score format'}), 400
    
    return jsonify({'success': False, 'message': 'Score is required'}), 400

@quiz_bp.route('/quiz/<int:quiz_id>/stats', methods=['GET'])
@login_required
def api_get_quiz_stats(quiz_id):
    quiz = get_quiz_or_abort(quiz_id)
    submissions = QuizSubmission.query.filter_by(quiz_id=quiz_id).all()
    total_submissions = len(submissions)
    if total_submissions == 0: return jsonify({'success': True, 'total_submissions': 0})
    
    questions_stats = []
    for q in quiz.questions.order_by(Question.order).all():
        correct_count = 0
        incorrect_count = 0
        for sub in submissions:
            ans = Answer.query.filter_by(submission_id=sub.id, question_id=q.id).first()
            if ans:
                if q.question_type in [QuestionType.MULTIPLE_CHOICE, QuestionType.DROPDOWN, QuestionType.TRUE_FALSE]:
                    if ans.selected_option and ans.selected_option.is_correct: correct_count += 1
                    else: incorrect_count += 1
                elif ans.answer_text: correct_count += 1
        questions_stats.append({'question_text': q.question_text, 'type': q.question_type.name, 'correct': correct_count, 'incorrect': incorrect_count, 'total': correct_count + incorrect_count})

    scores = [s.score for s in submissions if s.score is not None]
    avg_score = sum(scores) / total_submissions if total_submissions > 0 else 0
    return jsonify({
        'success': True, 
        'total_submissions': total_submissions, 
        'average_score': round(avg_score, 1), 
        'max_score': round(max(scores) if scores else 0, 1), 
        'min_score': round(min(scores) if scores else 0, 1), 
        'questions_stats': questions_stats, 
        'submissions': [
            {
                'id': s.id,
                'student_name': s.user.name, 
                'score': round(s.score, 1) if s.score is not None else 0, 
                'submitted_at': s.submitted_at.strftime('%Y-%m-%d %H:%M')
            } for s in submissions
        ]
    })

@quiz_bp.route('/quiz/<int:quiz_id>/update-meta', methods=['PUT'])
@login_required
def api_update_quiz_meta(quiz_id):
    quiz = get_quiz_or_abort(quiz_id)
    quiz.name = sanitize_text(request.form.get('name', quiz.name))
    quiz.description = sanitize_rich_text(request.form.get('description', ''))
    db.session.commit()
    return "", 204

@quiz_bp.route('/quiz/<int:quiz_id>/update-theme', methods=['PUT'])
@login_required
def api_update_quiz_theme(quiz_id):
    quiz = get_quiz_or_abort(quiz_id)
    data = request.get_json() or {}
    quiz.theme_color = data.get('theme_color', quiz.theme_color)
    quiz.font_question = data.get('font_question', quiz.font_question)
    quiz.font_answer = data.get('font_answer', quiz.font_answer)
    quiz.bg_pattern = data.get('bg_pattern', quiz.bg_pattern)
    try:
        quiz.bg_opacity = int(data.get('bg_opacity', quiz.bg_opacity))
    except (ValueError, TypeError):
        pass
    db.session.commit()
    return jsonify({'success': True})


@quiz_bp.route('/quiz/<int:quiz_id>/update-duration', methods=['PUT'])
@login_required
def api_update_quiz_duration(quiz_id):
    quiz = get_quiz_or_abort(quiz_id)
    data = request.get_json() or {}
    try:
        quiz.duration = int(data.get('duration', 0))
        db.session.commit()
        return jsonify({'success': True})
    except (ValueError, TypeError):
        return jsonify({'success': False}), 400


@quiz_bp.route('/quiz/<int:quiz_id>/update-max-attempts', methods=['PUT'])
@login_required
def api_update_quiz_max_attempts(quiz_id):
    quiz = get_quiz_or_abort(quiz_id)
    data = request.get_json() or {}
    try:
        quiz.max_attempts = int(data.get('max_attempts', 1))
        db.session.commit()
        return jsonify({'success': True})
    except (ValueError, TypeError):
        return jsonify({'success': False}), 400


@quiz_bp.route('/quiz/<int:quiz_id>/update-settings', methods=['PUT'])
@login_required
def api_update_quiz_settings(quiz_id):
    quiz = get_quiz_or_abort(quiz_id)
    data = request.get_json() or {}
    field = data.get('field')
    value = data.get('value')

    if field == 'is_quiz':
        quiz.is_quiz = bool(value)
    elif field == 'collect_email':
        if value in ('none', 'verified'):
            quiz.collect_email = value
    elif field == 'shuffle_questions':
        quiz.shuffle_questions = bool(value)
    elif field == 'confirmation_message':
        quiz.confirmation_message = sanitize_text(str(value or ''), max_len=500)
    elif field == 'default_points':
        try:
            quiz.default_points = max(0, int(value))
        except (ValueError, TypeError):
            return jsonify({'success': False}), 400
    elif field == 'required_by_default':
        quiz.required_by_default = bool(value)
    elif field == 'quiz_password':
        val = str(value or '').strip()
        quiz.quiz_password = val if val else None
    else:
        return jsonify({'success': False, 'message': 'Unknown field'}), 400

    db.session.commit()
    return jsonify({'success': True})


@quiz_bp.route('/quiz/<int:quiz_id>/verify-password', methods=['POST'])
@login_required
def api_verify_quiz_password(quiz_id):
    from app.tenant import get_school_id_or_abort, verify_course_in_school
    quiz = db.session.get(Quiz, quiz_id)
    if not quiz:
        abort(404)
    school_id = get_school_id_or_abort()
    verify_course_in_school(quiz.course, school_id)
    data = request.get_json() or {}
    entered = str(data.get('password', '')).strip()
    if quiz.quiz_password and entered != quiz.quiz_password:
        return jsonify({'success': False, 'message': 'Password salah'}), 403
    return jsonify({'success': True})


@quiz_bp.route('/quiz/<int:quiz_id>/questions/reorder', methods=['POST'])
@login_required
def api_reorder_questions(quiz_id):
    quiz = get_quiz_or_abort(quiz_id)
    data = request.get_json()
    if not data or 'order' not in data:
        abort(400)
    
    for item in data['order']:
        question = Question.query.filter_by(id=item['id'], quiz_id=quiz.id).first()
        if question:
            question.order = item['order']
            
    db.session.commit()
    return jsonify({'success': True})

@quiz_bp.route('/question/<int:question_id>/update-upload-settings', methods=['PUT'])
@login_required
def api_update_upload_settings(question_id):
    question = get_question_or_abort(question_id)
    try:
        max_size = request.form.get('max_file_size')
        if max_size:
            question.max_file_size = int(max_size)
            
        allowed_types = request.form.getlist('allowed_types')
        if allowed_types:
            question.allowed_file_types = ",".join(allowed_types)
        else:
            question.allowed_file_types = ""
            
        db.session.commit()
    except (ValueError, TypeError):
        pass
    return render_template('_question_form.html', question=question, QuestionType=QuestionType, Option=Option, Question=Question)

@quiz_bp.route('/question/<int:question_id>/upload-image', methods=['POST'])
@login_required
def api_upload_question_image(question_id):
    question = get_question_or_abort(question_id)
    if 'image' not in request.files:
        return jsonify({'success': False, 'message': 'Tidak ada file'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'Tidak ada file dipilih'}), 400
    
    if file:
        filename = secure_filename(f"q_{question.id}_{file.filename}")
        upload_folder = os.path.join(os.getcwd(), 'instance', 'uploads', str(question.quiz.course_id))
        os.makedirs(upload_folder, exist_ok=True)
        file.save(os.path.join(upload_folder, filename))
        
        # Delete old image if exists
        if question.image:
            old_path = os.path.join(upload_folder, question.image)
            if os.path.exists(old_path):
                try: os.remove(old_path)
                except OSError: pass
        
        question.image = filename
        db.session.commit()
        
        return render_template('_question_form.html', question=question, QuestionType=QuestionType, Option=Option, Question=Question)

@quiz_bp.route('/question/<int:question_id>/remove-image', methods=['DELETE'])
@login_required
def api_remove_question_image(question_id):
    question = get_question_or_abort(question_id)
    if question.image:
        upload_folder = os.path.join(os.getcwd(), 'instance', 'uploads', str(question.quiz.course_id))
        path = os.path.join(upload_folder, question.image)
        if os.path.exists(path):
            try: os.remove(path)
            except OSError: pass
        question.image = None
        db.session.commit()
    
    return render_template('_question_form.html', question=question, QuestionType=QuestionType, Option=Option, Question=Question)

@quiz_bp.route('/quiz/<int:quiz_id>/submit', methods=['POST'])
@login_required
def api_submit_quiz(quiz_id):
    from app.tenant import get_school_id_or_abort, verify_course_in_school
    quiz = db.session.get(Quiz, quiz_id)
    if not quiz:
        abort(404, description="Kuis tidak ditemukan.")

    school_id = get_school_id_or_abort()
    verify_course_in_school(quiz.course, school_id)

    if quiz.status != QuizStatus.PUBLISHED:
        return jsonify({'success': False, 'message': 'Kuis ini belum dipublikasikan.'}), 403

    # Check max attempts
    if quiz.max_attempts > 0:
        attempt_count = QuizSubmission.query.filter_by(quiz_id=quiz.id, user_id=current_user.id).count()
        if attempt_count >= quiz.max_attempts:
            return jsonify({'success': False, 'message': f'Batas pengerjaan ({quiz.max_attempts}x) telah tercapai.'}), 409

    # Handle both JSON and FormData
    if request.is_json:
        data = request.get_json()
        answers_list = data.get('answers', [])
    else:
        import json
        answers_list = json.loads(request.form.get('answers', '[]'))

    # Create submission
    submission = QuizSubmission(
        quiz_id=quiz.id,
        user_id=current_user.id,
        total_points=0 
    )
    db.session.add(submission)
    db.session.flush()

    total_possible_points = 0
    earned_points = 0
    
    for ans_data in answers_list:
        question_id = ans_data.get('question_id')
        question = db.session.get(Question, question_id)
        if not question or question.quiz_id != quiz.id:
            continue
        
        total_possible_points += question.points
        answer = Answer(submission_id=submission.id, question_id=question.id)

        if question.question_type in [QuestionType.MULTIPLE_CHOICE, QuestionType.TRUE_FALSE, QuestionType.DROPDOWN]:
            opt_id = ans_data.get('selected_option_id')
            answer.selected_option_id = opt_id
            selected_opt = db.session.get(Option, opt_id)
            if selected_opt and selected_opt.is_correct:
                earned_points += question.points
        
        elif question.question_type == QuestionType.LONG_TEXT:
            answer.answer_text = ans_data.get('answer_text')
            
        elif question.question_type == QuestionType.CHECKBOX:
            opt_ids = ans_data.get('selected_option_ids', [])
            answer.answer_text = ",".join(map(str, opt_ids))
            correct_opts = [o.id for o in question.options if o.is_correct]
            if set(opt_ids) == set(correct_opts):
                earned_points += question.points

        elif question.question_type == QuestionType.UPLOAD:
            file = request.files.get(f'file_{question.id}')
            if file and file.filename:
                upload_folder = os.path.join(os.getcwd(), 'instance', 'uploads', str(quiz.course_id))
                os.makedirs(upload_folder, exist_ok=True)
                filename = secure_filename(f"sub_{submission.id}_q{question.id}_{file.filename}")
                file.save(os.path.join(upload_folder, filename))
                answer.answer_text = filename
        
        db.session.add(answer)

    submission.total_points = total_possible_points
    submission.score = (earned_points / total_possible_points * 100) if total_possible_points > 0 else 0

    # ── Auto-sync quiz score to gradebook ──────────────────────────────
    try:
        from app.models.gradebook import GradeItem, GradeEntry, GradeCategory, GradeCategoryType
        from app.helpers import get_jakarta_now

        grade_item = GradeItem.query.filter_by(quiz_id=quiz.id).first()
        if not grade_item:
            # Find or create a category for quizzes
            category = GradeCategory.query.filter_by(course_id=quiz.course_id).first()
            if not category:
                category = GradeCategory(
                    name="Kuis",
                    course_id=quiz.course_id,
                    category_type=GradeCategoryType.FORMATIF,
                    weight=100.0
                )
                db.session.add(category)
                db.session.flush()

            grade_item = GradeItem(
                name=f"Kuis: {quiz.name}",
                description=quiz.description,
                category_id=category.id,
                max_score=float(total_possible_points) if total_possible_points > 0 else float(quiz.points),
                course_id=quiz.course_id,
                quiz_id=quiz.id,
            )
            db.session.add(grade_item)
            db.session.flush()

        # Create or update GradeEntry for this student
        grade_entry = GradeEntry.query.filter_by(
            grade_item_id=grade_item.id,
            student_id=current_user.id
        ).first()

        if not grade_entry:
            grade_entry = GradeEntry(
                grade_item_id=grade_item.id,
                student_id=current_user.id
            )
            db.session.add(grade_entry)

        grade_entry.score = submission.score
        grade_entry.percentage = submission.score  # score is already percentage
        grade_entry.graded_at = get_jakarta_now()
        grade_entry.graded_by = quiz.course.teacher_id
    except Exception:
        pass  # Don't fail quiz submission if gradebook sync fails
    # ───────────────────────────────────────────────────────────────────

    db.session.commit()

    return jsonify({'success': True, 'score': submission.score, 'message': 'Kuis berhasil dikirim.'})
