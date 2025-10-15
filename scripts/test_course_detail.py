#!/usr/bin/env python3
"""Test script to verify course detail page rendering as authenticated user."""
import requests
import sys
from pprint import pprint

BASE_URL = 'http://127.0.0.1:8000'
LOGIN_DATA = {
    'email': 'guru@aldudu.com',
    'password': '123'  # from templates/index.html login form default
}

def test_course_detail():
    # Create a session to maintain cookies
    s = requests.Session()
    
    # Step 1: Get CSRF token if needed (visit login page)
    r = s.get(f'{BASE_URL}/')
    print(f'GET / status: {r.status_code}')
    
    # Step 2: Login via API endpoint
    r = s.post(
        f'{BASE_URL}/api/login',
        json=LOGIN_DATA,
        headers={'Content-Type': 'application/json'}
    )
    print('\nPOST /api/login response:')
    pprint(r.json())
    
    if not r.ok:
        print('Login failed!')
        sys.exit(1)
    
    # Step 3: Get course detail page
    course_id = 2
    r = s.get(f'{BASE_URL}/kelas/{course_id}')
    print(f'\nGET /kelas/{course_id} status: {r.status_code}')
    
    if r.ok:
        # Check if we got HTML (not a redirect to login)
        if 'text/html' in r.headers.get('Content-Type', ''):
            print('Success: Got course detail page HTML')
            # Print title or some other content to verify
            if 'Aldudu Academy' in r.text:
                print('Page contains "Aldudu Academy"')
    else:
        print('Failed to get course page')
        print('Response:', r.text)

if __name__ == '__main__':
    test_course_detail()