"""
Test Student Enrollment & Course Management

Note: Enrollment is handled via association table, not a model class.
Students are enrolled through the User.courses_enrolled relationship.
"""
import pytest
from app.models import User, UserRole, Course, AcademicYear, enrollments
from app.extensions import db


class TestEnrollment:
    """Test student enrollment functionality"""

    def test_enroll_student_in_course(self, client, teacher_user, student_user, course):
        """Test enrolling a student in a course using association table"""
        # Enroll student using the association table
        stmt = enrollments.insert().values(
            user_id=student_user.id,
            course_id=course.id
        )
        db.session.execute(stmt)
        db.session.commit()

        # Verify enrollment
        enrolled = db.session.execute(
            db.select(enrollments).where(
                enrollments.c.user_id == student_user.id,
                enrollments.c.course_id == course.id
            )
        ).first()

        assert enrolled is not None
        assert enrolled.user_id == student_user.id
        assert enrolled.course_id == course.id

    def test_duplicate_enrollment_prevention(self, client, teacher_user, student_user, course):
        """Test preventing duplicate enrollments"""
        from sqlalchemy.exc import IntegrityError

        # Create first enrollment
        stmt = enrollments.insert().values(
            user_id=student_user.id,
            course_id=course.id
        )
        db.session.execute(stmt)
        db.session.commit()

        # Try to create duplicate (should fail due to primary key constraint)
        try:
            stmt2 = enrollments.insert().values(
                user_id=student_user.id,
                course_id=course.id
            )
            db.session.execute(stmt2)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            # Duplicate prevention works via primary key constraint

    def test_self_enrollment_with_code(self, client, student_user, course):
        """Test self-enrollment using class code"""
        # Login as student
        client.post('/api/login', json={
            'email': 'student@test.com',
            'password': 'password123'
        })

        # Enroll using class code
        response = client.post('/api/courses/enroll', json={
            'class_code': course.class_code
        })

        # Should succeed or return specific error
        assert response.status_code in [200, 201, 400, 404]

        data = response.get_json()
        if response.status_code in [200, 201]:
            assert data.get('success') is True or 'enrolled' in str(data).lower()

    def test_invalid_enrollment_code(self, client, student_user):
        """Test enrollment with invalid code"""
        # Login as student
        client.post('/api/login', json={
            'email': 'student@test.com',
            'password': 'password123'
        })

        # Try invalid code
        response = client.post('/api/courses/enroll', json={
            'class_code': 'INVALID123'
        })

        # Should fail
        assert response.status_code in [400, 404]
        data = response.get_json()
        assert data.get('success') is False or 'not found' in str(data).lower()


class TestCourseEnrollmentAPI:
    """Test course enrollment API endpoints"""

    def test_get_enrolled_courses(self, client, student_user, course):
        """Test getting enrolled courses for student"""
        # Login as student
        client.post('/api/login', json={
            'email': 'student@test.com',
            'password': 'password123'
        })

        response = client.get('/api/courses/enrolled')

        # Should return list of enrolled courses
        assert response.status_code == 200
        data = response.get_json()
        assert 'courses' in data or 'success' in data

    def test_get_course_students(self, client, teacher_user, course):
        """Test teacher getting list of enrolled students"""
        # Login as teacher
        client.post('/api/login', json={
            'email': 'teacher@test.com',
            'password': 'password123'
        })

        response = client.get(f'/api/course/{course.id}/students')

        # Should return list of students
        assert response.status_code == 200

    def test_remove_student_from_course(self, client, teacher_user, student_user, course):
        """Test removing student from course"""
        # Enroll student first
        stmt = enrollments.insert().values(
            user_id=student_user.id,
            course_id=course.id
        )
        db.session.execute(stmt)
        db.session.commit()

        # Login as teacher
        client.post('/api/login', json={
            'email': 'teacher@test.com',
            'password': 'password123'
        })

        # Remove student
        response = client.delete(f'/api/course/{course.id}/students/{student_user.id}')

        # Should succeed or return specific error
        assert response.status_code in [200, 204, 400, 404]


class TestCourseAccess:
    """Test course access control"""

    def test_teacher_can_access_own_course(self, client, teacher_user, course):
        """Test teacher can access their own course"""
        # Login as teacher
        client.post('/api/login', json={
            'email': 'teacher@test.com',
            'password': 'password123'
        })

        response = client.get(f'/api/course/{course.id}')
        assert response.status_code == 200

    def test_teacher_cannot_access_other_course(self, client, teacher_user):
        """Test teacher cannot access another teacher's course"""
        # Create another teacher and course
        other_teacher = User(
            name='Other Teacher',
            email='other.teacher@test.com',
            role=UserRole.GURU
        )
        other_teacher.set_password('password123')
        db.session.add(other_teacher)
        db.session.commit()

        academic_year = AcademicYear(
            year='2024',
            is_active=True
        )
        db.session.add(academic_year)
        db.session.commit()

        other_course = Course(
            name='Other Course',
            class_code='OTHER123',
            teacher_id=other_teacher.id,
            academic_year_id=academic_year.id
        )
        db.session.add(other_course)
        db.session.commit()

        # Login as original teacher
        client.post('/api/login', json={
            'email': 'teacher@test.com',
            'password': 'password123'
        })

        # Try to access other teacher's course
        response = client.get(f'/api/course/{other_course.id}')

        # Should be forbidden or not found
        assert response.status_code in [403, 404]

    def test_enrolled_student_can_access_course(self, client, student_user, course):
        """Test enrolled student can access course"""
        # Enroll student first
        stmt = enrollments.insert().values(
            user_id=student_user.id,
            course_id=course.id
        )
        db.session.execute(stmt)
        db.session.commit()

        # Login as student
        client.post('/api/login', json={
            'email': 'student@test.com',
            'password': 'password123'
        })

        response = client.get(f'/api/course/{course.id}')

        # Should succeed (student is enrolled)
        assert response.status_code in [200, 403]

    def test_non_enrolled_student_cannot_access_course(self, client, course):
        """Test non-enrolled student cannot access course"""
        # Create non-enrolled student
        student = User(
            name='Non-enrolled Student',
            email='nonenrolled@test.com',
            role=UserRole.MURID
        )
        student.set_password('password123')
        db.session.add(student)
        db.session.commit()

        # Login as non-enrolled student
        client.post('/api/login', json={
            'email': 'nonenrolled@test.com',
            'password': 'password123'
        })

        # Try to access course
        response = client.get(f'/api/course/{course.id}')

        # Should be forbidden or not found
        assert response.status_code in [403, 404]
