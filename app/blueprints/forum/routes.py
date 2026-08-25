"""Screen 16: the AI Work Forum, backed by SQLite.

Submissions are CSRF-checked by the app-wide guard in app/security.py and
length-checked here. Output is escaped by Jinja autoescape; nothing user-typed
is ever marked safe.
"""

from __future__ import annotations

from flask import abort, current_app, redirect, render_template, request, url_for

from ...data import content
from ...extensions import db
from ...models import ForumPost
from . import bp

# Accent names a post may carry, kept to the palette the design uses.
_ACCENTS = ("red", "blue", "green", "yellow")


def _render(channel_slug: str, error: str | None = None, status: int = 200):
    channel = content.channel_by_slug(channel_slug)
    if channel is None:
        abort(404)

    posts = (
        ForumPost.query.filter_by(channel=channel_slug)
        .order_by(ForumPost.created_at.asc(), ForumPost.id.asc())
        .all()
    )
    html = render_template(
        "forum/index.html",
        page=content.get_page("forum"),
        channels=content.forum_channels(),
        current_channel=channel,
        posts=posts,
        error=error,
        active_nav="forum",
    )
    return html, status


@bp.route("/", methods=["GET"], strict_slashes=False)
def index():
    return _render(content.default_channel_slug())


@bp.get("/<channel>")
def channel(channel: str):
    return _render(channel)


@bp.post("/post")
def post():
    author = (request.form.get("author") or "").strip()
    body = (request.form.get("body") or "").strip()
    accent = (request.form.get("accent") or "blue").strip()
    channel_slug = (request.form.get("channel") or "").strip()

    if content.channel_by_slug(channel_slug) is None:
        abort(404)
    if accent not in _ACCENTS:
        accent = "blue"

    author_max = current_app.config["FORUM_AUTHOR_MAX"]
    body_max = current_app.config["FORUM_BODY_MAX"]

    if not author or not body:
        return _render(channel_slug, error="empty", status=400)
    if len(author) > author_max or len(body) > body_max:
        return _render(channel_slug, error="too_long", status=400)

    db.session.add(
        ForumPost(author=author, accent=accent, channel=channel_slug, body=body)
    )
    db.session.commit()
    return redirect(url_for("forum.channel", channel=channel_slug))
