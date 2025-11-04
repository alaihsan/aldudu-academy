
import json
import pytest
from app import create_app
from models import db, User, Course, Discussion, Post, UserRole

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
            # Create a teacher, a student, a course, a discussion, and a post
            teacher = User(name='Teacher', email='teacher@test.com', role=UserRole.GURU)
            teacher.set_password('password')
            student = User(name='Student', email='student@test.com', role=UserRole.MURID)
            student.set_password('password')
            db.session.add_all([teacher, student])
            db.session.commit()

            course = Course(name='Test Course', teacher_id=teacher.id, class_code='TEST101', academic_year_id=1)
            db.session.add(course)
            db.session.commit()

            discussion = Discussion(title='Test Discussion', course_id=course.id, user_id=teacher.id)
            db.session.add(discussion)
            db.session.commit()

            post = Post(content='Test Post', discussion_id=discussion.id, user_id=student.id)
            db.session.add(post)
            db.session.commit()

        yield client

def test_delete_post_by_teacher(client):
    # Login as teacher
    with client.session_transaction() as sess:
        user = User.query.filter_by(email='teacher@test.com').first()
        sess['_user_id'] = user.id

    post = Post.query.first()
    resp = client.delete(f'/api/posts/{post.id}')
    assert resp.status_code == 200
    assert Post.query.get(post.id) is None

def test_delete_post_by_discussion_creator(client):
    # Login as discussion creator
    with client.session_transaction() as sess:
        user = User.query.filter_by(email='teacher@test.com').first()
        sess['_user_id'] = user.id

    post = Post.query.first()
    resp = client.delete(f'/api/posts/{post.id}')
    assert resp.status_code == 200
    assert Post.query.get(post.id) is None

def test_delete_post_by_other_user(client):
    # Login as another user
    with client.session_transaction() as sess:
        user = User.query.filter_by(email='student@test.com').first()
        sess['_user_id'] = user.id

    post = Post.query.first()
    resp = client.delete(f'/api/posts/{post.id}')
    assert resp.status_code == 403
    assert Post.query.get(post.id) is not None

def test_edit_post_by_author(client):
    # Login as post author
    with client.session_transaction() as sess:
        user = User.query.filter_by(email='student@test.com').first()
        sess['_user_id'] = user.id

    post = Post.query.first()
    resp = client.put(f'/api/posts/{post.id}', json={'content': 'Edited Post'})
    assert resp.status_code == 200
    assert Post.query.get(post.id).content == 'Edited Post'

def test_edit_post_by_other_user(client):
    # Login as another user
    with client.session_transaction() as sess:
        user = User.query.filter_by(email='teacher@test.com').first()
        sess['_user_id'] = user.id

    post = Post.query.first()
    original_content = post.content
    resp = client.put(f'/api/posts/{post.id}', json={'content': 'Edited Post'})
    assert resp.status_code == 403
    assert Post.query.get(post.id).content == original_content
