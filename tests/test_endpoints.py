def test_login_bad_email(client):
    resp = client.post('/api/login', json={'email': 'bad', 'password': 'x'})
    assert resp.status_code == 400

def test_create_course_requires_login(client):
    resp = client.post('/api/courses', json={'name': 'Math', 'academic_year_id': 1})
    assert resp.status_code in (401, 302)  # redirect to login or unauthorized
