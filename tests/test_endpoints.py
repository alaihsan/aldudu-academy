import json
import pytest
from app import create_app
from models import db


@pytest.fixture
def client(tmp_path):
    app = create_app()
    # use a temporary DB for tests
    db_fd = tmp_path / "test.db"
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_fd}'
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            db.drop_all()
            db.create_all()
        yield client

def test_login_bad_email(client):
    resp = client.post('/api/login', json={'email': 'bad', 'password': 'x'})
    assert resp.status_code == 400

def test_create_course_requires_login(client):
    resp = client.post('/api/courses', json={'name': 'Math', 'academic_year_id': 1})
    assert resp.status_code in (401, 302)  # redirect to login or unauthorized
