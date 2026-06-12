import pytest
from app.models import Course, Quiz, Question, Option, Assignment, File, Link
from app.extensions import db

def test_course_import_feature(client, teacher_user, course):
    # Log in as teacher
    client.post('/api/login', json={
        'email': 'teacher@test.com',
        'password': 'password123'
    })

    # Create destination course
    from datetime import datetime
    from app.models import AcademicYear
    
    ay = AcademicYear.query.first()
    dest_course = Course(
        name='Destination Course',
        class_code='DEST456',
        teacher_id=teacher_user.id,
        academic_year_id=ay.id
    )
    db.session.add(dest_course)
    db.session.commit()

    # Create materials in source course (default 'course')
    quiz = Quiz(name='Source Quiz', points=100, course_id=course.id)
    db.session.add(quiz)
    db.session.commit()

    q = Question(question_text='Q1', quiz_id=quiz.id)
    db.session.add(q)
    db.session.commit()

    opt = Option(option_text='O1', is_correct=True, question_id=q.id)
    db.session.add(opt)

    assignment = Assignment(title='Source Assignment', max_score=100, course_id=course.id)
    db.session.add(assignment)

    file_item = File(name='Source File', filename='doc.pdf', course_id=course.id)
    db.session.add(file_item)

    link = Link(name='Source Link', url='https://google.com', course_id=course.id)
    db.session.add(link)
    db.session.commit()

    # Import payload
    payload = {
        'source_course_id': course.id,
        'items': [
            {'type': 'quiz', 'id': quiz.id},
            {'type': 'assignment', 'id': assignment.id},
            {'type': 'file', 'id': file_item.id},
            {'type': 'link', 'id': link.id}
        ]
    }

    # Call import API
    response = client.post(
        f'/api/courses/{dest_course.id}/import',
        json=payload
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'Berhasil mengimpor 4 materi' in data['message']

    # Verify Quiz duplication
    imported_quiz = Quiz.query.filter_by(course_id=dest_course.id).first()
    assert imported_quiz is not None
    assert imported_quiz.name == 'Source Quiz'
    assert imported_quiz.id != quiz.id

    # Verify Question duplication
    imported_q = Question.query.filter_by(quiz_id=imported_quiz.id).first()
    assert imported_q is not None
    assert imported_q.question_text == 'Q1'

    # Verify Option duplication
    imported_opt = Option.query.filter_by(question_id=imported_q.id).first()
    assert imported_opt is not None
    assert imported_opt.option_text == 'O1'
    assert imported_opt.is_correct is True

    # Verify Assignment duplication
    imported_assign = Assignment.query.filter_by(course_id=dest_course.id).first()
    assert imported_assign is not None
    assert imported_assign.title == 'Source Assignment'

    # Verify File duplication
    imported_file = File.query.filter_by(course_id=dest_course.id).first()
    assert imported_file is not None
    assert imported_file.name == 'Source File'

    # Verify Link duplication
    imported_link = Link.query.filter_by(course_id=dest_course.id).first()
    assert imported_link is not None
    assert imported_link.name == 'Source Link'
    assert imported_link.url == 'https://google.com'
