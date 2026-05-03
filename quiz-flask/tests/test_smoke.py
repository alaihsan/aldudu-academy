from io import BytesIO

from app import create_app
from app.extensions import db
from app.models import Option, Question, QuestionType, Quiz, QuizStatus, User, UserRole
from app.services.quiz_docx_import_service import create_sample_docx_bytes


class TestConfig:
    SECRET_KEY = "test"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = "instance/test_uploads"
    TESTING = True


def make_app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
    return app


def register(client, name, email, role):
    return client.post(
        "/auth/register",
        data={"name": name, "email": email, "password": "secret1", "role": role},
        follow_redirects=True,
    )


def test_teacher_can_create_quiz():
    app = make_app()
    client = app.test_client()
    register(client, "Guru", "guru@example.com", "teacher")
    response = client.post("/quiz/new", data={"title": "Kuis Demo"})
    assert response.status_code == 302
    with app.app_context():
        assert Quiz.query.filter_by(title="Kuis Demo").count() == 1


def test_student_submission_is_graded():
    app = make_app()
    with app.app_context():
        teacher = User(name="Guru", email="guru@example.com", role=UserRole.TEACHER)
        teacher.set_password("secret1")
        student = User(name="Murid", email="murid@example.com", role=UserRole.STUDENT)
        student.set_password("secret1")
        db.session.add_all([teacher, student])
        db.session.flush()
        quiz = Quiz(title="Kuis", created_by=teacher.id, status=QuizStatus.PUBLISHED)
        db.session.add(quiz)
        db.session.flush()
        question = Question(quiz_id=quiz.id, question_text="2+2?", question_type=QuestionType.MULTIPLE_CHOICE, points=10)
        db.session.add(question)
        db.session.flush()
        correct = Option(question_id=question.id, option_text="4", is_correct=True, order=1)
        wrong = Option(question_id=question.id, option_text="5", is_correct=False, order=2)
        db.session.add_all([correct, wrong])
        db.session.commit()
        quiz_id = quiz.id
        correct_id = correct.id

    client = app.test_client()
    client.post("/auth/login", data={"email": "murid@example.com", "password": "secret1"})
    response = client.post(
        f"/api/quizzes/{quiz_id}/submit",
        json={"answers": [{"question_id": 1, "selected_option_id": correct_id}]},
    )
    assert response.status_code == 200
    response_json = response.get_json()
    assert response_json["score"] == 100
    assert response_json["completion_url"].endswith(f"/quiz/{quiz_id}/completed/1")

    client.post("/auth/logout")
    client.post("/auth/login", data={"email": "guru@example.com", "password": "secret1"})
    stats = client.get(f"/api/quizzes/{quiz_id}/stats")
    assert stats.status_code == 200
    stats_json = stats.get_json()
    assert stats_json["sheet"]["headers"][-1] == "1. 2+2?"
    assert stats_json["sheet"]["rows"][0][-1] == "4"

    xlsx = client.get(f"/api/quizzes/{quiz_id}/responses.xlsx")
    assert xlsx.status_code == 200
    assert xlsx.data.startswith(b"PK")


def test_student_can_submit_likert_scale():
    app = make_app()
    with app.app_context():
        teacher = User(name="Guru", email="guru2@example.com", role=UserRole.TEACHER)
        teacher.set_password("secret1")
        student = User(name="Murid", email="murid2@example.com", role=UserRole.STUDENT)
        student.set_password("secret1")
        db.session.add_all([teacher, student])
        db.session.flush()
        quiz = Quiz(title="Survei", created_by=teacher.id, status=QuizStatus.PUBLISHED)
        db.session.add(quiz)
        db.session.flush()
        question = Question(quiz_id=quiz.id, question_text="Seberapa setuju?", question_type=QuestionType.LIKERT_SCALE, points=10)
        db.session.add(question)
        db.session.flush()
        selected = Option(question_id=question.id, option_text="Setuju", order=4)
        db.session.add(selected)
        db.session.commit()
        quiz_id = quiz.id
        question_id = question.id
        selected_id = selected.id

    client = app.test_client()
    client.post("/auth/login", data={"email": "murid2@example.com", "password": "secret1"})
    response = client.post(
        f"/api/quizzes/{quiz_id}/submit",
        json={"answers": [{"question_id": question_id, "selected_option_id": selected_id}]},
    )
    assert response.status_code == 200
    assert response.get_json()["score"] == 0


def test_upload_question_rejects_wrong_type_and_oversize():
    app = make_app()
    with app.app_context():
        teacher = User(name="Guru", email="guru3@example.com", role=UserRole.TEACHER)
        teacher.set_password("secret1")
        student = User(name="Murid", email="murid3@example.com", role=UserRole.STUDENT)
        student.set_password("secret1")
        db.session.add_all([teacher, student])
        db.session.flush()
        quiz = Quiz(title="Upload", created_by=teacher.id, status=QuizStatus.PUBLISHED)
        db.session.add(quiz)
        db.session.flush()
        question = Question(
            quiz_id=quiz.id,
            question_text="Upload dokumen",
            question_type=QuestionType.UPLOAD,
            max_file_size=1,
            allowed_file_types="document",
        )
        db.session.add(question)
        db.session.commit()
        quiz_id = quiz.id
        question_id = question.id

    client = app.test_client()
    client.post("/auth/login", data={"email": "murid3@example.com", "password": "secret1"})

    wrong_type = client.post(
        f"/api/quizzes/{quiz_id}/submit",
        data={
            "answers": f'[{{"question_id": {question_id}}}]',
            f"file_{question_id}": (BytesIO(b"not a document"), "jawaban.png"),
        },
        content_type="multipart/form-data",
    )
    assert wrong_type.status_code == 400

    oversize = client.post(
        f"/api/quizzes/{quiz_id}/submit",
        data={
            "answers": f'[{{"question_id": {question_id}}}]',
            f"file_{question_id}": (BytesIO(b"x" * (1024 * 1024 + 1)), "jawaban.pdf"),
        },
        content_type="multipart/form-data",
    )
    assert oversize.status_code == 400


def test_upload_question_rejects_too_many_files():
    app = make_app()
    with app.app_context():
        teacher = User(name="Guru", email="guru4@example.com", role=UserRole.TEACHER)
        teacher.set_password("secret1")
        student = User(name="Murid", email="murid4@example.com", role=UserRole.STUDENT)
        student.set_password("secret1")
        db.session.add_all([teacher, student])
        db.session.flush()
        quiz = Quiz(title="Upload Banyak", created_by=teacher.id, status=QuizStatus.PUBLISHED)
        db.session.add(quiz)
        db.session.flush()
        question = Question(
            quiz_id=quiz.id,
            question_text="Upload maksimal satu",
            question_type=QuestionType.UPLOAD,
            max_file_size=1,
            allowed_file_types="document;max_files=1",
        )
        db.session.add(question)
        db.session.commit()
        quiz_id = quiz.id
        question_id = question.id

    client = app.test_client()
    client.post("/auth/login", data={"email": "murid4@example.com", "password": "secret1"})
    response = client.post(
        f"/api/quizzes/{quiz_id}/submit",
        data={
            "answers": f'[{{"question_id": {question_id}}}]',
            f"file_{question_id}": [
                (BytesIO(b"one"), "satu.pdf"),
                (BytesIO(b"two"), "dua.pdf"),
            ],
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 400


def test_teacher_can_import_quiz_from_docx():
    app = make_app()
    with app.app_context():
        teacher = User(name="Guru", email="guru5@example.com", role=UserRole.TEACHER)
        teacher.set_password("secret1")
        db.session.add(teacher)
        db.session.flush()
        quiz = Quiz(title="Import DOCX", created_by=teacher.id)
        db.session.add(quiz)
        db.session.commit()
        quiz_id = quiz.id

    client = app.test_client()
    client.post("/auth/login", data={"email": "guru5@example.com", "password": "secret1"})
    response = client.post(
        f"/api/quizzes/{quiz_id}/import-docx",
        data={"file": (BytesIO(create_sample_docx_bytes()), "contoh.docx")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    assert response.get_json()["imported_count"] == 5

    with app.app_context():
        imported = Question.query.filter_by(quiz_id=quiz_id).order_by(Question.order).all()
        assert imported[0].question_type == QuestionType.MULTIPLE_CHOICE
        assert imported[0].options[0].is_correct is True
        assert imported[1].question_type == QuestionType.CHECKBOX
        assert imported[2].question_type == QuestionType.LIKERT_SCALE
