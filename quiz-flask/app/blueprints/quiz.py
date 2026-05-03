import json
import os
from flask import Blueprint, abort, current_app, jsonify, request, url_for
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from app.extensions import db
from app.helpers import matching_pair, sanitize_rich_text, sanitize_text
from app.models import Answer, Option, Question, QuestionType, Quiz, QuizStatus, QuizSubmission
from app.services.grading_service import grade_answer, total_possible_points

quiz_bp = Blueprint("quiz", __name__)


def require_owner(quiz_id):
    quiz = db.session.get(Quiz, quiz_id)
    if not quiz:
        abort(404)
    if quiz.created_by != current_user.id:
        abort(403)
    return quiz


def serialize_option(option, include_correct=True):
    data = {"id": option.id, "text": option.option_text, "order": option.order}
    if include_correct:
        data["is_correct"] = option.is_correct
    return data


def serialize_question(question, include_correct=True):
    return {
        "id": question.id,
        "quiz_id": question.quiz_id,
        "text": question.question_text,
        "type": question.question_type.name,
        "description": question.description,
        "image": question.image,
        "image_url": url_for("main.uploaded_file", filename=question.image) if question.image else None,
        "order": question.order,
        "points": question.points,
        "is_required": question.is_required,
        "max_file_size": question.max_file_size,
        "allowed_file_types": question.allowed_file_types,
        "options": [serialize_option(option, include_correct) for option in question.options],
    }


def serialize_theme(quiz):
    return {
        "theme_color": quiz.theme_color,
        "theme_font": getattr(quiz, "theme_font", "Inter"),
        "theme_text_size": getattr(quiz, "theme_text_size", "normal"),
        "theme_background": getattr(quiz, "theme_background", "plain"),
        "theme_background_intensity": getattr(quiz, "theme_background_intensity", 20),
        "theme_form_width": getattr(quiz, "theme_form_width", "standard"),
        "theme_card_radius": getattr(quiz, "theme_card_radius", "google"),
        "theme_density": getattr(quiz, "theme_density", "normal"),
    }


def apply_theme_payload(quiz, data):
    if "theme_color" in data and str(data.get("theme_color", "")).startswith("#"):
        quiz.theme_color = data["theme_color"][:7]

    choices = {
        "theme_font": {"Inter", "Roboto", "Poppins", "Merriweather"},
        "theme_text_size": {"compact", "normal", "large"},
        "theme_background": {"plain", "grid", "wave", "topography", "confetti"},
        "theme_form_width": {"narrow", "standard", "wide"},
        "theme_card_radius": {"google", "sharp", "soft"},
        "theme_density": {"spacious", "normal", "compact"},
    }
    for field, allowed in choices.items():
        if field in data and data[field] in allowed:
            setattr(quiz, field, data[field])

    if "theme_background_intensity" in data:
        try:
            quiz.theme_background_intensity = min(100, max(0, int(data.get("theme_background_intensity") or 0)))
        except (TypeError, ValueError):
            pass


def apply_question_payload(question, payload):
    if "text" in payload:
        question.question_text = sanitize_rich_text(payload.get("text", ""))
    if "type" in payload:
        question.question_type = QuestionType[payload["type"]]
    if "description" in payload:
        question.description = sanitize_rich_text(payload.get("description", ""))
    if "points" in payload:
        question.points = max(0, int(payload.get("points") or 0))
    if "is_required" in payload:
        question.is_required = bool(payload.get("is_required"))
    if "max_file_size" in payload:
        question.max_file_size = max(1, int(payload.get("max_file_size") or 10))
    if "allowed_file_types" in payload:
        question.allowed_file_types = sanitize_text(payload.get("allowed_file_types", ""), 200)

    if "options" in payload:
        existing = {option.id: option for option in question.options}
        seen_ids = set()
        for index, item in enumerate(payload.get("options") or [], start=1):
            option_id = item.get("id")
            option = existing.get(option_id) if option_id else None
            if option is None:
                option = Option(question=question)
                db.session.add(option)
            option.option_text = sanitize_rich_text(item.get("text", ""), 500) or f"Opsi {index}"
            option.is_correct = bool(item.get("is_correct"))
            option.order = int(item.get("order") or index)
            if option.id:
                seen_ids.add(option.id)
        for option_id, option in existing.items():
            if option_id not in seen_ids and not any((item.get("id") == option_id) for item in payload.get("options") or []):
                db.session.delete(option)


@quiz_bp.route("/quizzes/<int:quiz_id>")
@login_required
def get_quiz(quiz_id):
    quiz = require_owner(quiz_id)
    return jsonify(
        {
            "id": quiz.id,
            "title": quiz.title,
            "description": quiz.description,
            "status": quiz.status.value,
            "duration_minutes": quiz.duration_minutes,
            "max_attempts": quiz.max_attempts,
            "shuffle_questions": quiz.shuffle_questions,
            "questions_per_page": quiz.questions_per_page,
            "quiz_password": quiz.quiz_password or "",
            **serialize_theme(quiz),
            "confirmation_message": quiz.confirmation_message,
            "default_points": quiz.default_points,
            "required_by_default": quiz.required_by_default,
            "questions": [serialize_question(question) for question in quiz.questions],
        }
    )


@quiz_bp.route("/quizzes/<int:quiz_id>", methods=["PUT"])
@login_required
def update_quiz(quiz_id):
    quiz = require_owner(quiz_id)
    data = request.get_json() or {}
    if "title" in data:
        quiz.title = sanitize_text(data.get("title"), 200) or quiz.title
    if "description" in data:
        quiz.description = sanitize_rich_text(data.get("description"))
    for field in ("duration_minutes", "max_attempts", "questions_per_page", "default_points"):
        if field in data:
            setattr(quiz, field, max(0, int(data.get(field) or 0)))
    for field in ("shuffle_questions", "required_by_default"):
        if field in data:
            setattr(quiz, field, bool(data.get(field)))
    if "quiz_password" in data:
        quiz.quiz_password = sanitize_text(data.get("quiz_password"), 120) or None
    apply_theme_payload(quiz, data)
    if "confirmation_message" in data:
        quiz.confirmation_message = sanitize_text(data.get("confirmation_message"), 500)
    db.session.commit()
    return jsonify({"success": True})


@quiz_bp.route("/quizzes/<int:quiz_id>/status", methods=["POST"])
@login_required
def set_status(quiz_id):
    quiz = require_owner(quiz_id)
    status = (request.get_json() or {}).get("status", "draft")
    quiz.status = QuizStatus(status)
    db.session.commit()
    return jsonify({"success": True, "status": quiz.status.value})


@quiz_bp.route("/quizzes/<int:quiz_id>/questions", methods=["POST"])
@login_required
def add_question(quiz_id):
    quiz = require_owner(quiz_id)
    qtype = QuestionType[(request.get_json() or {}).get("type", "MULTIPLE_CHOICE")]
    question = Question(
        quiz=quiz,
        question_text="",
        question_type=qtype,
        order=(len(quiz.questions) + 1),
        points=quiz.default_points,
        is_required=quiz.required_by_default,
    )
    if qtype in (QuestionType.MULTIPLE_CHOICE, QuestionType.DROPDOWN, QuestionType.CHECKBOX):
        question.options.append(Option(option_text="Opsi 1", order=1))
    elif qtype == QuestionType.TRUE_FALSE:
        question.options.extend([Option(option_text="Benar", order=1), Option(option_text="Salah", order=2)])
    elif qtype == QuestionType.MATCHING:
        question.options.append(Option(option_text="Istilah = Pasangan", order=1, is_correct=True))
    db.session.add(question)
    db.session.commit()
    return jsonify({"success": True, "question": serialize_question(question)})


@quiz_bp.route("/questions/<int:question_id>", methods=["PUT"])
@login_required
def update_question(question_id):
    question = db.session.get(Question, question_id)
    if not question:
        abort(404)
    require_owner(question.quiz_id)
    apply_question_payload(question, request.get_json() or {})
    db.session.commit()
    return jsonify({"success": True, "question": serialize_question(question)})


@quiz_bp.route("/questions/<int:question_id>", methods=["DELETE"])
@login_required
def delete_question(question_id):
    question = db.session.get(Question, question_id)
    if not question:
        return jsonify({"success": True})
    quiz = require_owner(question.quiz_id)
    db.session.delete(question)
    db.session.flush()
    for index, item in enumerate(quiz.questions, start=1):
        item.order = index
    db.session.commit()
    return jsonify({"success": True})


@quiz_bp.route("/questions/<int:question_id>/duplicate", methods=["POST"])
@login_required
def duplicate_question(question_id):
    original = db.session.get(Question, question_id)
    if not original:
        abort(404)
    require_owner(original.quiz_id)
    clone = Question(
        quiz_id=original.quiz_id,
        question_text=f"{original.question_text} (Salinan)",
        question_type=original.question_type,
        description=original.description,
        order=original.order + 1,
        points=original.points,
        is_required=original.is_required,
        max_file_size=original.max_file_size,
        allowed_file_types=original.allowed_file_types,
    )
    db.session.add(clone)
    db.session.flush()
    for option in original.options:
        db.session.add(Option(question_id=clone.id, option_text=option.option_text, is_correct=option.is_correct, order=option.order))
    db.session.commit()
    return jsonify({"success": True, "question": serialize_question(clone)})


@quiz_bp.route("/quizzes/<int:quiz_id>/questions/reorder", methods=["POST"])
@login_required
def reorder_questions(quiz_id):
    quiz = require_owner(quiz_id)
    order_map = {int(item["id"]): int(item["order"]) for item in (request.get_json() or {}).get("order", [])}
    for question in quiz.questions:
        if question.id in order_map:
            question.order = order_map[question.id]
    db.session.commit()
    return jsonify({"success": True})


@quiz_bp.route("/questions/<int:question_id>/upload-image", methods=["POST"])
@login_required
def upload_question_image(question_id):
    question = db.session.get(Question, question_id)
    if not question:
        abort(404)
    require_owner(question.quiz_id)
    file = request.files.get("image")
    if not file or not file.filename:
        return jsonify({"success": False, "message": "File wajib dipilih."}), 400
    filename = secure_filename(f"q{question.id}_{file.filename}")
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    file.save(path)
    question.image = filename
    db.session.commit()
    return jsonify({"success": True, "question": serialize_question(question)})


@quiz_bp.route("/quizzes/<int:quiz_id>/verify-password", methods=["POST"])
@login_required
def verify_password(quiz_id):
    quiz = db.session.get(Quiz, quiz_id)
    if not quiz:
        abort(404)
    entered = str((request.get_json() or {}).get("password", "")).strip()
    return jsonify({"success": not quiz.quiz_password or entered == quiz.quiz_password})


@quiz_bp.route("/quizzes/<int:quiz_id>/submit", methods=["POST"])
@login_required
def submit_quiz(quiz_id):
    quiz = db.session.get(Quiz, quiz_id)
    if not quiz:
        abort(404)
    if quiz.status != QuizStatus.PUBLISHED:
        return jsonify({"success": False, "message": "Kuis belum dipublikasikan."}), 403
    if quiz.max_attempts > 0:
        count = QuizSubmission.query.filter_by(quiz_id=quiz.id, user_id=current_user.id).count()
        if count >= quiz.max_attempts:
            return jsonify({"success": False, "message": "Batas pengerjaan sudah tercapai."}), 409

    answers_payload = json.loads(request.form.get("answers", "[]")) if not request.is_json else (request.get_json() or {}).get("answers", [])
    questions = list(quiz.questions)
    total_points = total_possible_points(questions)
    earned = 0.0
    submission = QuizSubmission(
        quiz=quiz,
        user_id=current_user.id,
        total_points=int(total_points),
        attempt_number=QuizSubmission.query.filter_by(quiz_id=quiz.id, user_id=current_user.id).count() + 1,
    )
    db.session.add(submission)
    db.session.flush()

    question_lookup = {question.id: question for question in questions}
    for item in answers_payload:
        question = question_lookup.get(int(item.get("question_id") or 0))
        if not question:
            continue
        answer = Answer(submission=submission, question=question, answer_data=item)
        db.session.add(answer)
        if question.question_type in (QuestionType.MULTIPLE_CHOICE, QuestionType.TRUE_FALSE, QuestionType.DROPDOWN):
            answer.selected_option_id = item.get("selected_option_id")
        elif question.question_type == QuestionType.LONG_TEXT:
            answer.answer_text = item.get("answer_text")
        elif question.question_type in (QuestionType.CHECKBOX, QuestionType.MATCHING):
            answer.answer_text = json.dumps(item, ensure_ascii=True)
        elif question.question_type == QuestionType.UPLOAD:
            file = request.files.get(f"file_{question.id}")
            if file and file.filename:
                filename = secure_filename(f"sub{submission.id}_q{question.id}_{file.filename}")
                file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
                answer.answer_text = filename
                item["filename"] = filename
        earned += grade_answer(question, item)

    submission.earned_points = earned
    submission.score = (earned / total_points * 100) if total_points else 0
    db.session.commit()
    return jsonify({"success": True, "score": submission.score, "submission_id": submission.id})


@quiz_bp.route("/quizzes/<int:quiz_id>/stats")
@login_required
def stats(quiz_id):
    quiz = require_owner(quiz_id)
    submissions = sorted(quiz.submissions, key=lambda item: item.submitted_at, reverse=True)
    scores = [item.score or 0 for item in submissions]
    return jsonify(
        {
            "success": True,
            "total_submissions": len(submissions),
            "average_score": round(sum(scores) / len(scores), 1) if scores else 0,
            "max_score": round(max(scores), 1) if scores else 0,
            "min_score": round(min(scores), 1) if scores else 0,
            "submissions": [
                {
                    "id": item.id,
                    "student_name": item.user.name,
                    "score": round(item.score or 0, 1),
                    "submitted_at": item.submitted_at.strftime("%Y-%m-%d %H:%M"),
                }
                for item in submissions
            ],
        }
    )
