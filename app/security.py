"""Session-backed CSRF protection.

Hand-rolled rather than pulled from Flask-WTF so the dependency list stays at the
three packages CLAUDE.md section 2 allows.
"""

from __future__ import annotations

import hmac
import secrets

from flask import abort, request, session

_SESSION_KEY = "_csrf_token"
_FORM_FIELD = "csrf_token"
_HEADER = "X-CSRF-Token"

# Methods that mutate state and therefore require a token.
_PROTECTED = {"POST", "PUT", "PATCH", "DELETE"}


def csrf_token() -> str:
    """Return this session's CSRF token, minting one on first use."""
    token = session.get(_SESSION_KEY)
    if not token:
        token = secrets.token_urlsafe(32)
        session[_SESSION_KEY] = token
    return token


def _submitted_token() -> str:
    return request.form.get(_FORM_FIELD) or request.headers.get(_HEADER) or ""


def validate_csrf() -> None:
    """Abort 400 when a mutating request arrives without a matching token."""
    if request.method not in _PROTECTED:
        return
    expected = session.get(_SESSION_KEY)
    submitted = _submitted_token()
    if not expected or not submitted or not hmac.compare_digest(expected, submitted):
        abort(400)


def init_csrf(app) -> None:
    """Wire the guard and the template helper into an app."""
    app.before_request(validate_csrf)
    app.jinja_env.globals["csrf_token"] = csrf_token
