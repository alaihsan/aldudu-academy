import json
import os
import zipfile
from io import BytesIO
from xml.sax.saxutils import escape as xml_escape
from flask import Blueprint, abort, current_app, jsonify, request, url_for
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from app.extensions import db
from app.helpers import matching_pair, plain_text, sanitize_rich_text, sanitize_text
from app.models import Answer, Option, Question, QuestionType, Quiz, QuizStatus, QuizSubmission
from app.services.grading_service import grade_answer, total_possible_points
from app.services.quiz_docx_import_service import create_sample_docx_bytes, import_questions_from_docx

quiz_bp = Blueprint("quiz", __name__)

LIKERT_DEFAULT_LABELS = ["Sangat tidak setuju", "Tidak setuju", "Netral", "Setuju", "Sangat setuju"]
UPLOAD_FILE_CATEGORIES = {
    "document": {"pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt"},
    "image": {"jpg", "jpeg", "png", "heic", "heif"},
    "video": {"mp4", "avi", "mov", "hevc", "h265"},
}
QUESTION_VIDEO_EXTENSIONS = {"mp4", "avi", "mov", "hevc", "h265"}


def normalize_upload_categories(value):
    raw_items = [item.strip().lower() for item in str(value or "").replace(";", ",").split(",")]
    aliases = {
        "dokumen": "document",
        "document": "document",
        "documents": "document",
        "pdf": "document",
        "doc": "document",
        "xls": "document",
        "ppt": "document",
        "txt": "document",
        "gambar": "image",
        "image": "image",
        "images": "image",
        "jpg": "image",
        "jpeg": "image",
        "png": "image",
        "heic": "image",
        "heif": "image",
        "video": "video",
        "videos": "video",
        "mp4": "video",
        "avi": "video",
        "mov": "video",
        "hevc": "video",
        "h.265": "video",
        "h265": "video",
    }
    categories = []
    for item in raw_items:
        category = aliases.get(item)
        if category and category not in categories:
            categories.append(category)
    return categories or ["document"]


def upload_extensions_for_categories(value):
    extensions = set()
    for category in normalize_upload_categories(value):
        extensions.update(UPLOAD_FILE_CATEGORIES[category])
    return extensions


def upload_max_files_from_value(value):
    for part in str(value or "").replace(";", ",").split(","):
        key, _, raw_value = part.strip().partition("=")
        if key.strip().lower() in {"max_files", "max-file", "maxfile", "jumlah_file"}:
            try:
                return min(10, max(1, int(raw_value or 1)))
            except (TypeError, ValueError):
                return 1
    return 1


def upload_file_error(question, file):
    max_bytes = int(question.max_file_size or 10) * 1024 * 1024
    file.stream.seek(0, os.SEEK_END)
    size = file.stream.tell()
    file.stream.seek(0)
    if size > max_bytes:
        return f"File untuk pertanyaan {question.order} melebihi batas {question.max_file_size} MB."

    filename = (file.filename or "").lower()
    extension = "h265" if filename.endswith(".h.265") else os.path.splitext(filename)[1].lstrip(".")
    if extension == "h.265":
        extension = "h265"
    if extension not in upload_extensions_for_categories(question.allowed_file_types):
        return f"Tipe file untuk pertanyaan {question.order} tidak sesuai ketentuan."
    return None


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
    media_extension = os.path.splitext(question.image or "")[1].lower().lstrip(".")
    if (question.image or "").lower().endswith(".h.265"):
        media_extension = "h265"
    return {
        "id": question.id,
        "quiz_id": question.quiz_id,
        "text": question.question_text,
        "type": question.question_type.name,
        "description": question.description,
        "image": question.image,
        "image_url": url_for("main.uploaded_file", filename=question.image) if question.image else None,
        "media_type": "video" if media_extension in QUESTION_VIDEO_EXTENSIONS else "image",
        "order": question.order,
        "points": question.points,
        "is_required": question.is_required,
        "max_file_size": question.max_file_size,
        "allowed_file_types": question.allowed_file_types,
        "options": [serialize_option(option, include_correct) for option in question.options],
    }


def answer_display_text(answer):
    question = answer.question
    payload = answer.answer_data or {}
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except (TypeError, ValueError):
            payload = {}

    if question.question_type in (QuestionType.MULTIPLE_CHOICE, QuestionType.TRUE_FALSE, QuestionType.DROPDOWN, QuestionType.LIKERT_SCALE):
        option_id = payload.get("selected_option_id") or answer.selected_option_id
        option = next((item for item in question.options if item.id == option_id), None)
        return plain_text(option.option_text) if option else ""

    if question.question_type == QuestionType.CHECKBOX:
        selected_ids = set(payload.get("selected_option_ids") or [])
        return ", ".join(plain_text(option.option_text) for option in question.options if option.id in selected_ids)

    if question.question_type == QuestionType.MATCHING:
        pairs = payload.get("matching_answers") or {}
        return "; ".join(f"{plain_text(left)} = {plain_text(right)}" for left, right in pairs.items())

    if question.question_type == QuestionType.LONG_TEXT:
        return plain_text(payload.get("answer_text") or answer.answer_text or "")

    if question.question_type == QuestionType.UPLOAD:
        filenames = payload.get("filenames")
        if not filenames and answer.answer_text:
            try:
                filenames = json.loads(answer.answer_text)
            except (TypeError, ValueError):
                filenames = [answer.answer_text]
        return ", ".join(filenames or [])

    return plain_text(answer.answer_text or "")


def answer_attachments(answer):
    if answer.question.question_type != QuestionType.UPLOAD:
        return []
    payload = answer.answer_data or {}
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except (TypeError, ValueError):
            payload = {}
    filenames = payload.get("filenames")
    if not filenames and answer.answer_text:
        try:
            filenames = json.loads(answer.answer_text)
        except (TypeError, ValueError):
            filenames = [answer.answer_text]
    return [
        {
            "name": filename,
            "url": url_for("main.uploaded_file", filename=filename),
            "download_url": url_for("main.uploaded_file", filename=filename, download="true"),
        }
        for filename in (filenames or [])
    ]


def response_sheet_rows(quiz):
    questions = list(quiz.questions)
    headers = ["Waktu Submit", "Nama Murid", "Email", "Skor (%)"] + [
        f"{index}. {plain_text(question.question_text) or 'Pertanyaan'}"
        for index, question in enumerate(questions, start=1)
    ]
    rows = []
    submissions = sorted(quiz.submissions, key=lambda item: item.submitted_at, reverse=True)
    for submission in submissions:
        answer_lookup = {answer.question_id: answer for answer in submission.answers}
        rows.append([
            submission.submitted_at.strftime("%Y-%m-%d %H:%M"),
            submission.user.name,
            submission.user.email,
            round(submission.score or 0, 1),
            *[answer_display_text(answer_lookup[question.id]) if question.id in answer_lookup else "" for question in questions],
        ])
    return headers, rows


def build_xlsx(headers, rows):
    sheet_rows = [headers, *rows]

    def cell_ref(row_index, col_index):
        letters = ""
        value = col_index
        while value:
            value, remainder = divmod(value - 1, 26)
            letters = chr(65 + remainder) + letters
        return f"{letters}{row_index}"

    row_xml = []
    for row_index, row in enumerate(sheet_rows, start=1):
        cells = []
        for col_index, value in enumerate(row, start=1):
            text = xml_escape(str(value if value is not None else ""))
            cells.append(f'<c r="{cell_ref(row_index, col_index)}" t="inlineStr"><is><t>{text}</t></is></c>')
        row_xml.append(f'<row r="{row_index}">{"".join(cells)}</row>')

    sheet_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData>{"".join(row_xml)}</sheetData>
</worksheet>'''
    workbook_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets><sheet name="Jawaban" sheetId="1" r:id="rId1"/></sheets>
</workbook>'''
    rels_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>'''
    workbook_rels_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>'''
    content_types_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>'''
    output = BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types_xml)
        archive.writestr("_rels/.rels", rels_xml)
        archive.writestr("xl/workbook.xml", workbook_xml)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels_xml)
        archive.writestr("xl/worksheets/sheet1.xml", sheet_xml)
    output.seek(0)
    return output.getvalue()


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
        raw_file_types = payload.get("allowed_file_types", "")
        question.allowed_file_types = ",".join(normalize_upload_categories(raw_file_types))
        question.allowed_file_types += f";max_files={upload_max_files_from_value(raw_file_types)}"

    if "options" in payload:
        option_payload = payload.get("options") or []
        if question.question_type == QuestionType.LIKERT_SCALE:
            option_payload = option_payload[:5]
        existing = {option.id: option for option in question.options}
        seen_ids = set()
        for index, item in enumerate(option_payload, start=1):
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
            if option_id not in seen_ids and not any((item.get("id") == option_id) for item in option_payload):
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
    elif qtype == QuestionType.LIKERT_SCALE:
        question.points = 0
        question.options.extend([Option(option_text=label, order=index) for index, label in enumerate(LIKERT_DEFAULT_LABELS, start=1)])
    db.session.add(question)
    db.session.commit()
    return jsonify({"success": True, "question": serialize_question(question)})


@quiz_bp.route("/quizzes/import-sample-format")
@login_required
def download_quiz_import_sample():
    return current_app.response_class(
        create_sample_docx_bytes(),
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": 'attachment; filename="contoh-format-import-soal.docx"'},
    )


@quiz_bp.route("/quizzes/<int:quiz_id>/import-docx", methods=["POST"])
@login_required
def import_quiz_docx(quiz_id):
    quiz = require_owner(quiz_id)
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"success": False, "message": "File Word wajib dipilih."}), 400
    if not file.filename.lower().endswith(".docx"):
        return jsonify({"success": False, "message": "Gunakan file Word berformat .docx."}), 400
    try:
        result = import_questions_from_docx(file, quiz)
    except zipfile.BadZipFile:
        return jsonify({"success": False, "message": "File .docx tidak valid atau rusak."}), 400
    except Exception as exc:
        db.session.rollback()
        current_app.logger.error("Failed importing quiz docx: %s", exc, exc_info=True)
        return jsonify({"success": False, "message": "Gagal mengimpor file Word."}), 500
    return jsonify(result), 200 if result.get("success") else 400


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


@quiz_bp.route("/questions/<int:question_id>/upload-video", methods=["POST"])
@login_required
def upload_question_video(question_id):
    question = db.session.get(Question, question_id)
    if not question:
        abort(404)
    require_owner(question.quiz_id)
    file = request.files.get("video")
    if not file or not file.filename:
        return jsonify({"success": False, "message": "File video wajib dipilih."}), 400
    filename_lower = file.filename.lower()
    extension = "h265" if filename_lower.endswith(".h.265") else os.path.splitext(filename_lower)[1].lstrip(".")
    if extension not in QUESTION_VIDEO_EXTENSIONS:
        return jsonify({"success": False, "message": "Gunakan video MP4, AVI, MOV, HEVC, atau H.265."}), 400
    filename = secure_filename(f"q{question.id}_{file.filename}")
    file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
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
        if question.question_type in (QuestionType.MULTIPLE_CHOICE, QuestionType.TRUE_FALSE, QuestionType.DROPDOWN, QuestionType.LIKERT_SCALE):
            answer.selected_option_id = item.get("selected_option_id")
        elif question.question_type == QuestionType.LONG_TEXT:
            answer.answer_text = item.get("answer_text")
        elif question.question_type in (QuestionType.CHECKBOX, QuestionType.MATCHING):
            answer.answer_text = json.dumps(item, ensure_ascii=True)
        elif question.question_type == QuestionType.UPLOAD:
            files = [file for file in request.files.getlist(f"file_{question.id}") if file and file.filename]
            max_files = upload_max_files_from_value(question.allowed_file_types)
            if len(files) > max_files:
                return jsonify({"success": False, "message": f"Pertanyaan {question.order} maksimal menerima {max_files} file."}), 400
            saved_files = []
            for file_index, file in enumerate(files, start=1):
                error = upload_file_error(question, file)
                if error:
                    return jsonify({"success": False, "message": error}), 400
                filename = secure_filename(f"sub{submission.id}_q{question.id}_{file_index}_{file.filename}")
                file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
                saved_files.append(filename)
            if saved_files:
                answer.answer_text = json.dumps(saved_files, ensure_ascii=True)
                item["filenames"] = saved_files
        earned += grade_answer(question, item)

    submission.earned_points = earned
    submission.score = (earned / total_points * 100) if total_points else 0
    db.session.commit()
    return jsonify({
        "success": True,
        "score": submission.score,
        "submission_id": submission.id,
        "completion_url": url_for("main.quiz_completed", quiz_id=quiz.id, submission_id=submission.id),
    })


@quiz_bp.route("/quizzes/<int:quiz_id>/stats")
@login_required
def stats(quiz_id):
    quiz = require_owner(quiz_id)
    submissions = sorted(quiz.submissions, key=lambda item: item.submitted_at, reverse=True)
    scores = [item.score or 0 for item in submissions]
    sheet_headers, sheet_rows = response_sheet_rows(quiz)
    answer_counts = {question.id: 0 for question in quiz.questions}
    for submission in submissions:
        for answer in submission.answers:
            if answer.question_id in answer_counts and answer_display_text(answer):
                answer_counts[answer.question_id] += 1
    return jsonify(
        {
            "success": True,
            "total_submissions": len(submissions),
            "average_score": round(sum(scores) / len(scores), 1) if scores else 0,
            "max_score": round(max(scores), 1) if scores else 0,
            "min_score": round(min(scores), 1) if scores else 0,
            "download_url": url_for("quiz.download_responses_xlsx", quiz_id=quiz.id),
            "questions": [
                {
                    "id": question.id,
                    "text": plain_text(question.question_text) or f"Pertanyaan {index}",
                    "type": question.question_type.name,
                    "answered": answer_counts.get(question.id, 0),
                }
                for index, question in enumerate(quiz.questions, start=1)
            ],
            "sheet": {"headers": sheet_headers, "rows": sheet_rows},
            "submissions": [
                {
                    "id": item.id,
                    "student_name": item.user.name,
                    "student_email": item.user.email,
                    "score": round(item.score or 0, 1),
                    "submitted_at": item.submitted_at.strftime("%Y-%m-%d %H:%M"),
                    "answers": [
                        {
                            "question_id": answer.question_id,
                            "question": plain_text(answer.question.question_text) or "Pertanyaan",
                            "answer": answer_display_text(answer),
                            "attachments": answer_attachments(answer),
                        }
                        for answer in sorted(item.answers, key=lambda answer: answer.question.order)
                    ],
                }
                for item in submissions
            ],
        }
    )


@quiz_bp.route("/quizzes/<int:quiz_id>/responses.xlsx")
@login_required
def download_responses_xlsx(quiz_id):
    quiz = require_owner(quiz_id)
    headers, rows = response_sheet_rows(quiz)
    content = build_xlsx(headers, rows)
    filename = secure_filename(f"{quiz.title or 'quiz'}-jawaban.xlsx") or "jawaban.xlsx"
    return current_app.response_class(
        content,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
