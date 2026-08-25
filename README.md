# HaNoiTVEdu

A workplace learning platform for Hanoi TV employees: short, role-based modules that teach
practical AI skills for editorial, admin and content work.

**LEARN AI. SHARPEN YOUR STORY**

The app renders the 16 screens designed in `HRD A2.pdf` as responsive server-rendered HTML.
Flask + Jinja + hand-written CSS + vanilla ES6. No CSS framework, no JS framework, no build step.

---

## Run it locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # optional for development
python run.py                 # http://127.0.0.1:5000
```

The SQLite database is created in `instance/` on first run and seeded with the forum's
sample posts.

## Tests

```bash
python -m unittest discover -s tests -t .
```

| Suite | What it guards |
|---|---|
| `tests/test_routes.py` | every route answers 200, the shell renders, all four logo colours appear on every screen, the quiz never exposes its answer key, CSRF is enforced, forum input is validated and escaped |
| `tests/test_no_inline_copy.py` | no sentence of site copy is hard-coded in a template, view, stylesheet or script |
| `tests/test_no_emoji.py` | no emoji in `app/`, in `content.json`, or in any rendered page |

## Content

All user-facing copy lives in `content/content.json` and is verified character-for-character
against the pdftotext dumps of the source PDF:

```bash
python tools/verify_content.py            # report
python tools/verify_content.py --strict   # exit 1 on any miss — use in CI
```

Run this after any change to `content/` or `app/data/`. See `CLAUDE.md` section 6 for the
pipeline and the verbatim rule.

## Deploy

```bash
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
export FLASK_ENV=production
export DATABASE_URL=...        # optional; defaults to SQLite in instance/
gunicorn "app:create_app()" -b 0.0.0.0:8000
```

A `Procfile` is included for platforms that read one:

```
web: gunicorn "app:create_app()" -b 0.0.0.0:$PORT
```

`ProdConfig` refuses to start on the development secret, disables debug, sets
`SESSION_COOKIE_SECURE` / `HTTPONLY` / `SAMESITE=Lax`, and serves static assets with a
one-year `Cache-Control`. `GET /healthz` returns `200 ok` for load-balancer probes.

## Layout

```
run.py  config.py  requirements.txt  Procfile  .env.example
app/
  __init__.py      create_app(), blueprints, jinja globals, error handlers, /healthz
  extensions.py    db singleton
  models.py        ForumPost, QuizAttempt, UserProfile
  security.py      session CSRF token, issue and constant-time verify
  data/content.py  loads content.json once; typed accessors
  blueprints/      overview, learn, practice, notebook, forum
  templates/       base.html, macros/{icons,boxes,blocks}.html, one folder per section
  static/          css/{tokens,layout,components}.css, js/main.js, image/logo.png
content/           content.json + the source and flow PDF dumps
tools/             verify_content.py
tests/
```

`app/static/css/tokens.css` is the single source of truth for colour, type, spacing and
radii, and the only stylesheet permitted to contain a literal hex value.
