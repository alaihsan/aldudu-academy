"""
Verifies that every translation file under app/static/translations/*.json
has exactly the same set of dotted keys as the others.

The 7 languages are meant to be a single source of truth shared by both
the client (language.js fetches these files directly) and the server
(app/core/i18n.py's t() helper) — if one file falls behind, that language
silently shows raw key strings (client) or crashes/falls back oddly
(server). Run this after editing any translation file; exits non-zero on
mismatch so it can be wired into CI later.
"""
import json
import sys
from pathlib import Path

TRANSLATIONS_DIR = Path(__file__).resolve().parents[1] / 'app' / 'static' / 'translations'


def flatten_keys(d, prefix=''):
    keys = set()
    for k, v in d.items():
        full_key = f'{prefix}.{k}' if prefix else k
        if isinstance(v, dict):
            keys |= flatten_keys(v, full_key)
        else:
            keys.add(full_key)
    return keys


def main():
    files = sorted(TRANSLATIONS_DIR.glob('*.json'))
    if not files:
        print(f'No translation files found in {TRANSLATIONS_DIR}')
        return 1

    key_sets = {}
    for path in files:
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        # 'meta' legitimately varies per language (own-language name, flag,
        # optional 'rtl' flag only Arabic needs) — not a content key set.
        data.pop('meta', None)
        key_sets[path.stem] = flatten_keys(data)

    reference_lang = 'id' if 'id' in key_sets else next(iter(key_sets))
    reference_keys = key_sets[reference_lang]

    ok = True
    for lang, keys in key_sets.items():
        if lang == reference_lang:
            continue
        missing = reference_keys - keys
        extra = keys - reference_keys
        if missing or extra:
            ok = False
            print(f'[{lang}] out of sync with [{reference_lang}]:')
            if missing:
                print(f'  missing: {sorted(missing)}')
            if extra:
                print(f'  extra:   {sorted(extra)}')

    if ok:
        print(f'OK: all {len(files)} translation files share {len(reference_keys)} keys.')
        return 0
    return 1


if __name__ == '__main__':
    sys.exit(main())
