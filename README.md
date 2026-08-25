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

Verified on Python 3.10 and 3.14 with the pinned `requirements.txt`; `.python-version`
asks build packs for 3.12.

### Any platform

Two environment variables, one process command.

| Variable | Value |
|---|---|
| `SECRET_KEY` | **required** — `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `FLASK_ENV` | `production` |
| `DATABASE_URL` | optional; defaults to SQLite in `instance/` |

```
web: gunicorn "app:create_app()" -b 0.0.0.0:$PORT
```

That line is already in the `Procfile`. To run it by hand:

```bash
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
export FLASK_ENV=production
gunicorn "app:create_app()" -b 0.0.0.0:8000
```

`ProdConfig` refuses to start on the development secret, disables debug, sets
`SESSION_COOKIE_SECURE` / `HTTPONLY` / `SAMESITE=Lax`, and serves static assets with a
one-year `Cache-Control`. `GET /healthz` returns `200 ok` for load-balancer probes.

### Serve it over HTTPS

`ProdConfig` marks the session cookie `Secure`, so browsers will not store it over plain
HTTP. Without the session there is no CSRF token, and **every forum post and quiz
submission returns 400**. Managed platforms terminate TLS for you and this is a non-issue;
on a bare VPS, put the app behind nginx or Caddy with a certificate before going live.

### What happens to the database

The forum and quiz tables live in `instance/hanoitvedu.sqlite`. Most platforms give a
container an ephemeral filesystem, so on every deploy and restart:

- posts and quiz attempts written by visitors are lost;
- the forum reseeds itself from `content/content.json`, so the six sample posts always
  come back and the page is never empty.

For a demo or a review link that is fine. To keep what visitors write, either attach a
persistent disk and point `DATABASE_URL` at a file on it:

```
DATABASE_URL=sqlite:////data/hanoitvedu.sqlite     # note the four slashes: absolute path
```

or move to Postgres — `config.py` already rewrites a `postgres://` URL to `postgresql://`,
but the driver is not installed, so add `psycopg[binary]` to `requirements.txt` first.

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
