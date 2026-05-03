import os
import secrets
from flask import Blueprint, abort, current_app, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user, login_required
from app.extensions import db
from app.models import Quiz, QuizStatus, UserRole

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
@login_required
def index():
    if current_user.role == UserRole.TEACHER:
        quizzes = Quiz.query.filter_by(created_by=current_user.id).order_by(Quiz.updated_at.desc()).all()
    else:
        quizzes = Quiz.query.filter_by(status=QuizStatus.PUBLISHED).order_by(Quiz.updated_at.desc()).all()
    return render_template("index.html", quizzes=quizzes)


@main_bp.route("/quiz/new", methods=["POST"])
@login_required
def create_quiz():
    if not current_user.is_teacher:
        abort(403)
    quiz = Quiz(title=request.form.get("title") or "Kuis Baru", created_by=current_user.id)
    db.session.add(quiz)
    db.session.commit()
    return redirect(url_for("main.quiz_detail", quiz_id=quiz.id))


@main_bp.route("/quiz/<int:quiz_id>")
@login_required
def quiz_detail(quiz_id):
    quiz = db.session.get(Quiz, quiz_id)
    if not quiz:
        abort(404)

    is_owner = quiz.created_by == current_user.id
    preview = request.args.get("preview") == "true"

    if is_owner and not preview:
        return render_template("quiz/editor.html", quiz=quiz)

    if not is_owner and quiz.status != QuizStatus.PUBLISHED:
        abort(403)

    questions = list(quiz.questions)
    if quiz.shuffle_questions:
        secrets.SystemRandom().shuffle(questions)

    attempt_count = 0
    if not preview:
        attempt_count = len([s for s in quiz.submissions if s.user_id == current_user.id])

    return render_template(
        "quiz/take.html",
        quiz=quiz,
        questions=questions,
        is_preview=preview,
        attempt_count=attempt_count,
    )


@main_bp.route("/quiz/<int:quiz_id>/submissions/<int:submission_id>")
@login_required
def submission_detail(quiz_id, submission_id):
    quiz = db.session.get(Quiz, quiz_id)
    if not quiz:
        abort(404)
    submission = next((item for item in quiz.submissions if item.id == submission_id), None)
    if not submission:
        abort(404)
    if quiz.created_by != current_user.id and submission.user_id != current_user.id:
        abort(403)
    return render_template("quiz/submission.html", quiz=quiz, submission=submission)


@main_bp.route("/uploads/<path:filename>")
@login_required
def uploaded_file(filename):
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    return send_from_directory(upload_folder, filename, as_attachment=False)


@main_bp.route("/health")
def health():
    return {"status": "ok"}
