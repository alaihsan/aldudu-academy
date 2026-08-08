import pytest
from app.models import Link
from app.core.extensions import db

def test_create_link_normalization(client, teacher_user, course):
    # Log in as teacher
    client.post('/api/login', json={
        'email': 'teacher@test.com',
        'password': 'password123'
    })
    
    # 1. Create link with protocol
    response = client.post(
        f'/api/courses/{course.id}/links',
        json={'name': 'Google with https', 'url': 'https://google.com'}
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data['success'] is True
    assert data['link']['url'] == 'https://google.com'
    
    # Verify in DB
    link_id = data['link']['id']
    link = db.session.get(Link, link_id)
    assert link.url == 'https://google.com'
    
    # 2. Create link without protocol
    response2 = client.post(
        f'/api/courses/{course.id}/links',
        json={'name': 'Google without protocol', 'url': 'google.com'}
    )
    assert response2.status_code == 201
    data2 = response2.get_json()
    assert data2['success'] is True
    assert data2['link']['url'] == 'https://google.com'
    
    # Verify in DB
    link_id2 = data2['link']['id']
    link2 = db.session.get(Link, link_id2)
    assert link2.url == 'https://google.com'


def test_update_link_normalization(client, teacher_user, course):
    # Log in as teacher
    client.post('/api/login', json={
        'email': 'teacher@test.com',
        'password': 'password123'
    })
    
    # Create initial link
    new_link = Link(name='Initial Link', url='https://initial.com', course_id=course.id)
    db.session.add(new_link)
    db.session.commit()
    
    # Update link with protocol
    response = client.put(
        f'/api/link/{new_link.id}',
        json={'name': 'Updated Protocol', 'url': 'http://yahoo.com'}
    )
    assert response.status_code == 200
    db.session.refresh(new_link)
    assert new_link.url == 'http://yahoo.com'
    
    # Update link without protocol
    response2 = client.put(
        f'/api/link/{new_link.id}',
        json={'name': 'Updated No Protocol', 'url': 'yahoo.com'}
    )
    assert response2.status_code == 200
    db.session.refresh(new_link)
    assert new_link.url == 'https://yahoo.com'
