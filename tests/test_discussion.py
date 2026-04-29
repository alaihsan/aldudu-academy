import pytest
from app.models import User, Discussion, Post, UserRole

@pytest.fixture
def other_student(db, active_school):
    user = User(
        name='Other Student',
        email='other-student@test.com',
        role=UserRole.MURID,
        email_verified=True,
        school_id=active_school.id,
    )
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def discussion_post(db, teacher_user, student_user, course):
    discussion = Discussion(title='Test Discussion', course_id=course.id, user_id=teacher_user.id)
    db.session.add(discussion)
    db.session.commit()

    post = Post(content='Test Post', discussion_id=discussion.id, user_id=student_user.id)
    db.session.add(post)
    db.session.commit()
    return post

def test_delete_post_by_teacher(client, discussion_post):
    # Login as teacher
    with client.session_transaction() as sess:
        user = User.query.filter_by(email='teacher@test.com').first()
        sess['_user_id'] = str(user.id)

    post = discussion_post
    resp = client.delete(f'/api/posts/{post.id}')
    assert resp.status_code == 200
    assert Post.query.get(post.id) is None

def test_delete_post_by_discussion_creator(client, discussion_post):
    # Login as discussion creator
    with client.session_transaction() as sess:
        user = User.query.filter_by(email='teacher@test.com').first()
        sess['_user_id'] = str(user.id)

    post = discussion_post
    resp = client.delete(f'/api/posts/{post.id}')
    assert resp.status_code == 200
    assert Post.query.get(post.id) is None

def test_delete_post_by_other_user(client, discussion_post, other_student):
    # Login as another user
    with client.session_transaction() as sess:
        sess['_user_id'] = str(other_student.id)

    post = discussion_post
    resp = client.delete(f'/api/posts/{post.id}')
    assert resp.status_code == 403
    assert Post.query.get(post.id) is not None

def test_edit_post_by_author(client, discussion_post):
    # Login as post author
    with client.session_transaction() as sess:
        user = User.query.filter_by(email='student@test.com').first()
        sess['_user_id'] = str(user.id)

    post = discussion_post
    resp = client.put(f'/api/posts/{post.id}', json={'content': 'Edited Post'})
    assert resp.status_code == 200
    assert Post.query.get(post.id).content == 'Edited Post'

def test_edit_post_by_other_user(client, discussion_post, other_student):
    # Login as another user
    with client.session_transaction() as sess:
        sess['_user_id'] = str(other_student.id)

    post = discussion_post
    original_content = post.content
    resp = client.put(f'/api/posts/{post.id}', json={'content': 'Edited Post'})
    assert resp.status_code == 403
    assert Post.query.get(post.id).content == original_content
