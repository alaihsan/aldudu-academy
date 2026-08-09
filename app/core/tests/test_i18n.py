import pytest
from app.core.i18n import t, resolve_lang, SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE


def _login(client, user):
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)


def test_supported_languages_have_seven_codes():
    assert set(SUPPORTED_LANGUAGES) == {'id', 'en', 'jv', 'su', 'ban', 'min', 'ar'}


def test_t_returns_indonesian_by_default(app):
    with app.test_request_context('/'):
        assert t('common.language', lang='id') == 'Bahasa'


def test_t_returns_translation_for_other_languages(app):
    with app.test_request_context('/'):
        assert t('common.language', lang='en') == 'Language'
        assert t('common.language', lang='ar') != 'Bahasa'


def test_t_falls_back_to_default_language_for_missing_key(app):
    with app.test_request_context('/'):
        # A key that doesn't exist anywhere falls back to the raw key itself.
        assert t('nonexistent.key.xyz', lang='en') == 'nonexistent.key.xyz'


def test_t_supports_positional_format_args(app):
    with app.test_request_context('/'):
        raw = t('time.minutes_ago', 'id')
        result = t('time.minutes_ago', 'id', None, 5)
        assert result == raw.format(5)


def test_t_falls_back_gracefully_on_missing_positional_arg(app):
    with app.test_request_context('/'):
        # No args supplied for a template with a '{0}' placeholder should
        # not raise — falls back to the raw (unformatted) template string.
        raw = t('time.minutes_ago', 'id')
        assert t('time.minutes_ago', 'id') == raw


def test_resolve_lang_uses_authenticated_user_preference(app, db, teacher_user):
    teacher_user.preferred_language = 'en'
    db.session.commit()

    with app.test_request_context('/'):
        from flask_login import login_user
        login_user(teacher_user)
        assert resolve_lang() == 'en'


def test_resolve_lang_falls_back_to_default_for_guest(app):
    with app.test_request_context('/'):
        assert resolve_lang() == DEFAULT_LANGUAGE


def test_resolve_lang_uses_accept_language_header_for_guest(app):
    with app.test_request_context('/', headers={'Accept-Language': 'en-US,en;q=0.9'}):
        assert resolve_lang() == 'en'


def test_set_language_endpoint_persists_preference(client, db, teacher_user):
    _login(client, teacher_user)
    resp = client.post('/api/set-language', json={'language': 'jv'})
    assert resp.status_code == 200
    assert resp.get_json()['success'] is True

    from app.core.extensions import db as _db
    _db.session.refresh(teacher_user)
    assert teacher_user.preferred_language == 'jv'


def test_set_language_endpoint_rejects_unsupported_code(client, db, teacher_user):
    _login(client, teacher_user)
    resp = client.post('/api/set-language', json={'language': 'xx-not-real'})
    assert resp.status_code == 400
    assert resp.get_json()['success'] is False


def test_html_lang_attribute_matches_preferred_language(client, db, teacher_user):
    teacher_user.preferred_language = 'ar'
    db.session.commit()
    _login(client, teacher_user)

    resp = client.get('/dashboard')
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert '<html lang="ar" dir="rtl">' in body
