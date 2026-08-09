"""
Server-side i18n helper.

Reads the same JSON files language.js fetches client-side
(app/static/translations/<code>.json) so both sides always agree on
copy — there is no separate .po/.mo toolchain. Used for:
  - SSR initial <html lang>/dir + window.INITIAL_LANG (this module's
    resolve_lang(), avoids a "flash" of the wrong language on deep links)
  - Translating jsonify/abort messages server-side (t(), see
    app/core/authorization.py and route modules)
"""
import json
import os
from pathlib import Path

from flask import current_app, request
from flask_login import current_user

SUPPORTED_LANGUAGES = ['id', 'en', 'jv', 'su', 'ban', 'min', 'ar']
RTL_LANGUAGES = {'ar'}
DEFAULT_LANGUAGE = 'id'

_translations_cache = {}


def _translations_dir():
    return Path(current_app.static_folder) / 'translations'


def load_translations(lang):
    """Load and cache one language's translation dict. Falls back to an
    empty dict (never raises) so a missing/corrupt file degrades to raw
    key strings instead of a 500."""
    if lang in _translations_cache:
        return _translations_cache[lang]

    path = _translations_dir() / f'{lang}.json'
    try:
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}

    if not current_app.debug:
        _translations_cache[lang] = data
    return data


def resolve_lang():
    """Determine the language to render for the current request:
    logged-in user's saved preference, else best Accept-Language match,
    else the default. Mirrors language.js's own precedence (saved choice
    wins over browser default) so SSR and client agree on first paint."""
    if current_user.is_authenticated and current_user.preferred_language in SUPPORTED_LANGUAGES:
        return current_user.preferred_language

    if request:
        best = request.accept_languages.best_match(SUPPORTED_LANGUAGES)
        if best:
            return best

    return DEFAULT_LANGUAGE


def t(key, lang=None, default=None, *args, **kwargs):
    """Translate a dotted key (e.g. 'messages.not_found') using the
    'messages' section (and any other section) of the JSON files. Falls
    back to the same key in DEFAULT_LANGUAGE, then to `default` or the
    raw key itself, so a missing translation never crashes a request.

    Positional *args fill '{0}', '{1}', ... placeholders (the convention
    already used by time.minutes_ago etc. in the JSON files); **kwargs
    fill named placeholders for newer keys. A malformed placeholder falls
    back to the unformatted string instead of raising mid-request."""
    lang = lang or resolve_lang()

    for candidate in (lang, DEFAULT_LANGUAGE):
        data = load_translations(candidate)
        value = data
        for part in key.split('.'):
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                value = None
                break
        if isinstance(value, str):
            if not args and not kwargs:
                return value
            try:
                return value.format(*args, **kwargs)
            except (IndexError, KeyError):
                return value

    return default if default is not None else key
