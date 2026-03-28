"""
Test Authentication & Authorization
"""
import pytest
from flask import url_for
from app.models import User, UserRole


class TestPasswordValidation:
    """Test password validation in registration"""

    def test_password_too_short(self, client, app):
        """Test password less than 6 characters is rejected"""
        from app.extensions import db
        
        response = client.post('/api/register', json={
            'school_name': 'Test School',
            'slug': 'testschool',
            'school_email': 'school@test.com',
            'admin_name': 'Test Admin',
            'admin_email': 'admin@test.com',
            'password': 'abc'  # Too short
        })
        
        data = response.get_json()
        assert response.status_code == 400
        assert 'minimal 6 karakter' in data['message']

    def test_password_missing_uppercase(self, client, app):
        """Test password without uppercase is rejected"""
        response = client.post('/api/register', json={
            'school_name': 'Test School',
            'slug': 'testschool2',
            'school_email': 'school2@test.com',
            'admin_name': 'Test Admin',
            'admin_email': 'admin2@test.com',
            'password': 'password1!'  # No uppercase
        })
        
        data = response.get_json()
        assert response.status_code == 400
        assert 'huruf kapital' in data['message']

    def test_password_missing_number(self, client, app):
        """Test password without number is rejected"""
        response = client.post('/api/register', json={
            'school_name': 'Test School',
            'slug': 'testschool3',
            'school_email': 'school3@test.com',
            'admin_name': 'Test Admin',
            'admin_email': 'admin3@test.com',
            'password': 'Password!'  # No number
        })
        
        data = response.get_json()
        assert response.status_code == 400
        assert '1 angka' in data['message']

    def test_password_missing_symbol(self, client, app):
        """Test password without symbol is rejected"""
        response = client.post('/api/register', json={
            'school_name': 'Test School',
            'slug': 'testschool4',
            'school_email': 'school4@test.com',
            'admin_name': 'Test Admin',
            'admin_email': 'admin4@test.com',
            'password': 'Password1'  # No symbol
        })
        
        data = response.get_json()
        assert response.status_code == 400
        assert '1 simbol' in data['message']

    def test_password_valid(self, client, app):
        """Test valid password passes validation"""
        response = client.post('/api/register', json={
            'school_name': 'Test School Valid',
            'slug': 'testschoolvalid',
            'school_email': 'schoolvalid@test.com',
            'admin_name': 'Test Admin',
            'admin_email': 'adminvalid@test.com',
            'password': 'Password1!'  # Valid
        })
        
        # Should not fail password validation (may fail for other reasons like duplicate email)
        data = response.get_json()
        assert response.status_code in [201, 400]
        if response.status_code == 400:
            assert 'minimal 6 karakter' not in data['message']
            assert 'huruf kapital' not in data['message']
            assert '1 angka' not in data['message']
            assert '1 simbol' not in data['message']


class TestLogin:
    """Test login functionality"""

    def test_login_invalid_email(self, client, app):
        """Test login with invalid email format"""
        response = client.post('/api/login', json={
            'email': 'invalid-email',
            'password': 'Password1!'
        })
        
        data = response.get_json()
        assert response.status_code == 400
        assert 'tidak valid' in data['message']

    def test_login_nonexistent_email(self, client, app):
        """Test login with non-existent email"""
        response = client.post('/api/login', json={
            'email': 'nonexistent@test.com',
            'password': 'Password1!'
        })
        
        data = response.get_json()
        assert response.status_code == 401
        assert 'tidak terdaftar' in data['message']

    def test_login_wrong_password(self, client, teacher_user):
        """Test login with wrong password"""
        response = client.post('/api/login', json={
            'email': 'teacher@test.com',
            'password': 'wrongpassword'
        })
        
        data = response.get_json()
        assert response.status_code == 401
        assert 'Password salah' in data['message']

    def test_login_success(self, client, teacher_user):
        """Test successful login"""
        response = client.post('/api/login', json={
            'email': 'teacher@test.com',
            'password': 'password123'
        })
        
        data = response.get_json()
        assert response.status_code == 200
        assert data['success'] is True
        assert 'user' in data


class TestAuthorization:
    """Test authorization and role-based access"""

    def test_unauthorized_access(self, client, app):
        """Test accessing protected endpoint without login"""
        response = client.get('/api/profile')
        assert response.status_code in [302, 401]

    def test_teacher_access_gradebook(self, client, teacher_user, course):
        """Test teacher can access their course gradebook"""
        # Login first
        client.post('/api/login', json={
            'email': 'teacher@test.com',
            'password': 'password123'
        })
        
        response = client.get(f'/gradebook/course/{course.id}')
        assert response.status_code == 200

    def test_student_cannot_access_teacher_gradebook(self, client, student_user, course):
        """Test student cannot access teacher gradebook"""
        # Login as student
        client.post('/api/login', json={
            'email': 'student@test.com',
            'password': 'password123'
        })
        
        response = client.get(f'/gradebook/course/{course.id}')
        # Should redirect or show forbidden
        assert response.status_code in [302, 403]


class TestSession:
    """Test session management"""

    def test_get_session_unauthenticated(self, client):
        """Test getting session when not logged in"""
        response = client.get('/api/session')
        data = response.get_json()
        assert data['isAuthenticated'] is False

    def test_get_session_authenticated(self, client, teacher_user):
        """Test getting session when logged in"""
        # Login
        client.post('/api/login', json={
            'email': 'teacher@test.com',
            'password': 'password123'
        })
        
        response = client.get('/api/session')
        data = response.get_json()
        assert data['isAuthenticated'] is True
        assert 'user' in data
        assert data['user']['email'] == 'teacher@test.com'
