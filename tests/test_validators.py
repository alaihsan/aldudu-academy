import pytest
from app import sanitize_text, is_valid_email, is_valid_color, is_valid_class_code

def test_sanitize_text_basic():
    assert sanitize_text('<b>Hello</b>') == 'Hello'
    assert sanitize_text('   trim  ') == 'trim'
    long = 'a' * 300
    assert len(sanitize_text(long, max_len=50)) == 50

def test_email_validator():
    assert is_valid_email('test@example.com')
    assert not is_valid_email('not-an-email')

def test_color_validator():
    assert is_valid_color('#ff00aa')
    assert not is_valid_color('red')

def test_class_code():
    assert is_valid_class_code('AB12')
    assert not is_valid_class_code('too-long-code-123')
