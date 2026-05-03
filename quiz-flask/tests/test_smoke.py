from app import create_app
from app.extensions import db
from app.models import Option, Question, QuestionType, Quiz, QuizStatus, User, UserRole


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
    assert response.get_json()["score"] == 100
