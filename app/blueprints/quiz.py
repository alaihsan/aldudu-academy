from flask import (
    Blueprint, request, jsonify, abort,
    render_template, make_response, url_for
)
from flask_login import login_required, current_user
from app.models import (
    db, Course, Quiz, UserRole, GradeType,
    Question, Option, QuestionType,
    QuizSubmission, Answer
)
from app.helpers import sanitize_text
import datetime
import os
from werkzeug.utils import secure_filename

quiz_bp = Blueprint('quiz', __name__, url_prefix='/api')

# --- Helper Functions ---

def get_quiz_or_abort(quiz_id, check_teacher=True):
    quiz = db.session.get(Quiz, quiz_id)
    if not quiz: abort(404, description="Kuis tidak ditemukan.")
    if check_teacher and quiz.course.teacher_id != current_user.id:
        abort(403, description="Anda tidak memiliki akses ke kuis ini.")
    return quiz

def get_question_or_abort(question_id, check_teacher=True):
    question = db.session.get(Question, question_id)
    if not question: abort(404, description="Pertanyaan tidak ditemukan.")
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
        points=10 # Default points per question
    )
    
    if q_type in [QuestionType.MULTIPLE_CHOICE, QuestionType.DROPDOWN, QuestionType.CHECKBOX]:
        question.options.append(Option(option_text="Opsi 1", order=1))
    elif q_type == QuestionType.TRUE_FALSE:
        question.options.extend([
            Option(option_text="Benar", order=1), 
            Option(option_text="Salah", order=2)
        ])

    db.session.add(question)
    db.session.commit()
    db.session.refresh(question)
    return render_template('_question_form.html', question=question, QuestionType=QuestionType, Option=Option, Question=Question)

@quiz_bp.route('/question/<int:question_id>/change-type', methods=['POST'])
@login_required
def api_change_question_type(question_id):
    question = get_question_or_abort(question_id)
    try:
        new_type_str = request.form.get('question_type')
        new_type = QuestionType[new_type_str]
    except (KeyError, TypeError):
        return "Invalid type", 400

    current_text = request.form.get('question_text')
    if current_text is not None:
        question.question_text = sanitize_text(current_text)

    if question.question_type != new_type:
        question.question_type = new_type
        # Efficiently clear old options
        Option.query.filter_by(question_id=question.id).delete()
        
        if new_type in [QuestionType.MULTIPLE_CHOICE, QuestionType.DROPDOWN, QuestionType.CHECKBOX]:
            db.session.add(Option(question_id=question.id, option_text="Opsi 1", order=1))
        elif new_type == QuestionType.TRUE_FALSE:
            db.session.add_all([
                Option(question_id=question.id, option_text="Benar", order=1),
                Option(question_id=question.id, option_text="Salah", order=2)
            ])

    db.session.commit()
    db.session.refresh(question)
    return render_template('_question_form.html', question=question, QuestionType=QuestionType, Option=Option, Question=Question)

@quiz_bp.route('/question/<int:question_id>/update', methods=['PUT'])
@login_required
def api_update_question(question_id):
    question = get_question_or_abort(question_id)
    question.question_text = sanitize_text(request.form.get('question_text', ''))
    db.session.commit()
    return f'<input type="text" name="question_text" class="question-title-input" value="{question.question_text}" hx-put="/api/question/{question.id}/update" hx-trigger="blur" hx-swap="outerHTML" placeholder="Pertanyaan Tanpa Judul" />'

@quiz_bp.route('/question/<int:question_id>/update-points', methods=['PUT'])
@login_required
def api_update_question_points(question_id):
    question = get_question_or_abort(question_id)
    try:
        question.points = int(request.form.get('points', 0))
        db.session.commit()
    except: pass
    return render_template('_question_form.html', question=question, QuestionType=QuestionType, Option=Option, Question=Question)

@quiz_bp.route('/question/<int:question_id>/toggle-required', methods=['POST'])
@login_required
def api_toggle_question_required(question_id):
    question = get_question_or_abort(question_id)
    question.is_required = not question.is_required
    db.session.commit()
    return render_template('_question_form.html', question=question, QuestionType=QuestionType, Option=Option, Question=Question)

@quiz_bp.route('/question/<int:question_id>/update-upload-settings', methods=['PUT'])
@login_required
def api_update_upload_settings(question_id):
    question = get_question_or_abort(question_id)
    try:
        question.max_file_size = int(request.form.get('max_file_size', 10))
        allowed = request.form.getlist('allowed_types')
        question.allowed_file_types = ",".join(allowed) if allowed else "document"
        db.session.commit()
    except: pass
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
    return render_template('_question_form.html', question=question, QuestionType=QuestionType, Option=Option, Question=Question)

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
    option = db.session.get(Option, option_id)
    if not option: abort(404)
    option.option_text = sanitize_text(request.form.get('option_text', ''))
    db.session.commit()
    return f'<input type="text" class="option-input" value="{option.option_text}" name="option_text" hx-put="/api/option/{option.id}/update" hx-trigger="blur" hx-swap="outerHTML" placeholder="Opsi {option.order}" />'

@quiz_bp.route('/option/<int:option_id>/delete', methods=['DELETE'])
@login_required
def api_delete_option(option_id):
    option = db.session.get(Option, option_id)
    if option and option.question.options.count() > 1:
        db.session.delete(option)
        db.session.commit()
    return "", 200

@quiz_bp.route('/question/<int:question_id>/delete', methods=['DELETE'])
@login_required
def api_delete_question(question_id):
    db.session.delete(get_question_or_abort(question_id))
    db.session.commit()
    return "", 200

@quiz_bp.route('/quiz/<int:quiz_id>/stats', methods=['GET'])
@login_required
def api_get_quiz_stats(quiz_id):
    quiz = get_quiz_or_abort(quiz_id)
    
    # Get all submissions
    submissions = QuizSubmission.query.filter_by(quiz_id=quiz_id).all()
    total_submissions = len(submissions)
    
    if total_submissions == 0:
        return jsonify({
            'success': True,
            'total_submissions': 0,
            'questions_stats': []
        })

    # Stats per question
    questions_stats = []
    for q in quiz.questions.order_by(Question.order).all():
        correct_count = 0
        incorrect_count = 0
        
        # Count for each question
        for sub in submissions:
            # Find answer for this specific question in this submission
            ans = Answer.query.filter_by(submission_id=sub.id, question_id=q.id).first()
            if ans:
                if q.question_type in [QuestionType.MULTIPLE_CHOICE, QuestionType.DROPDOWN, QuestionType.TRUE_FALSE]:
                    if ans.selected_option and ans.selected_option.is_correct:
                        correct_count += 1
                    else:
                        incorrect_count += 1
                # For Long Text/Upload, we count as "answered" for now
                elif ans.answer_text:
                    correct_count += 1
        
        questions_stats.append({
            'question_text': q.question_text,
            'type': q.question_type.name,
            'correct': correct_count,
            'incorrect': incorrect_count,
            'total': correct_count + incorrect_count
        })

    # Calculate stats
    scores = [s.score for s in submissions if s.score is not None]
    avg_score = sum(scores) / total_submissions if total_submissions > 0 else 0
    max_score = max(scores) if scores else 0
    min_score = min(scores) if scores else 0

    return jsonify({
        'success': True,
        'total_submissions': total_submissions,
        'average_score': round(avg_score, 1),
        'max_score': round(max_score, 1),
        'min_score': round(min_score, 1),
        'questions_stats': questions_stats,
        'submissions': [
            {
                'student_name': s.user.name,
                'score': s.score,
                'submitted_at': s.submitted_at.strftime('%Y-%m-%d %H:%M')
            } for s in submissions
        ]
    })

@quiz_bp.route('/quiz/<int:quiz_id>/update-meta', methods=['PUT'])
@login_required
def api_update_quiz_meta(quiz_id):
    quiz = get_quiz_or_abort(quiz_id)
    quiz.name = sanitize_text(request.form.get('name', quiz.name))
    quiz.description = sanitize_text(request.form.get('description', ''))
    db.session.commit()
    # Return minimal response or nothing
    return "", 204

@quiz_bp.route('/quiz/<int:quiz_id>/update-theme', methods=['PUT'])
@login_required
def api_update_quiz_theme(quiz_id):
    quiz = get_quiz_or_abort(quiz_id)
    data = request.get_json() or {}
    
    quiz.theme_color = data.get('theme_color', quiz.theme_color)
    quiz.bg_pattern = data.get('bg_pattern', quiz.bg_pattern)
    quiz.font_question = data.get('font_question', quiz.font_question)
    quiz.font_answer = data.get('font_answer', quiz.font_answer)
    
    db.session.commit()
    return jsonify({'success': True})

@quiz_bp.route('/quiz/<int:quiz_id>/submit', methods=['POST'])
@login_required
def api_submit_quiz(quiz_id):
    quiz = db.session.get(Quiz, quiz_id)
    if not quiz: return jsonify({'success': False}), 404
    data = request.get_json()
    submission = QuizSubmission(quiz_id=quiz_id, user_id=current_user.id, total_points=quiz.points)
    db.session.add(submission)
    db.session.flush()
    total_score = 0
    for ans_data in data.get('answers', []):
        q = db.session.get(Question, ans_data['question_id'])
        if not q: continue
        ans = Answer(submission_id=submission.id, question_id=q.id)
        if q.question_type in [QuestionType.MULTIPLE_CHOICE, QuestionType.DROPDOWN, QuestionType.TRUE_FALSE]:
            ans.selected_option_id = ans_data.get('selected_option_id')
            opt = db.session.get(Option, ans.selected_option_id)
            if opt and opt.is_correct: total_score += q.points
        else:
            ans.answer_text = ans_data.get('answer_text')
        db.session.add(ans)
    submission.score = total_score
    db.session.commit()
    return jsonify({'success': True, 'score': total_score})
