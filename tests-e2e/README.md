# Playwright smoke suite

Regression gate for the `app/static/js` modularization refactor — checks
that moved/split JS files still load in the right order, onclick handlers
still fire, and no page throws a console error. It is **not** general
feature-test coverage; it exists to catch the exact failure mode this kind
of refactor risks (a stale path, a broken load order, a name that stopped
being reachable from the global scope).

This is the first Node/npm tooling in this otherwise all-Python repo —
it's isolated to this folder on purpose (separate `package.json`, own
`node_modules/`) so it doesn't touch `requirements.txt`/pytest.

## Setup

```bash
cd tests-e2e
npm install
```

Playwright's browsers are expected to already be installed (`npx playwright
install` if not). The Python side needs the repo's normal
`pip install -r requirements.txt` in whatever interpreter `PYTHON_BIN`
points at (default `python3` on PATH).

## Running

```bash
npm test
```

This lets every request (Tailwind/HTMX/SweetAlert2/SortableJS/DOMPurify/
Google Fonts CDNs) go out over the real network, exactly like production.
Use this by default on a normal dev machine or CI runner with internet
access.

### Offline mode

```bash
E2E_OFFLINE=1 npm test
```

Only needed when the CDNs above aren't reachable (e.g. a sandboxed CI
runner behind an egress allowlist). It fulfills those specific requests
from local npm-vendored copies (`tests/fixtures.js`) instead of hitting
the network, and specs use `Locator.evaluate()`-based clicks/fills instead
of `click()`/`fill()` since there's no real Tailwind CSS to compute layout
from in this mode (see the comments in `tests/fixtures.js` for why).

## What it seeds

`seed.py` drops and recreates a throwaway SQLite DB
(`instance/e2e_test.db`, gitignored) with one school, one teacher, one
student (enrolled), one course, and one published quiz — just enough for
`tests/smoke.spec.js`'s 5 scenarios. `playwright.config.js`'s `webServer`
runs it automatically before every `npm test`.

Seeded emails use `@aldudu-e2e.dev`, not `*.test`/`*.example` — the app's
real login validates emails with `email_validator`, which rejects RFC 2606
reserved domains.
