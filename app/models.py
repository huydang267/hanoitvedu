"""Database models.

Only genuinely dynamic data lives here. Modules, lessons and prompts are content
and stay in content/content.json (CLAUDE.md section 2).
"""

from __future__ import annotations

from datetime import datetime, timezone

from .extensions import db


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ForumPost(db.Model):
    __tablename__ = "forum_post"

    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(60), nullable=False)
    accent = db.Column(db.String(16), nullable=False, default="blue")
    channel = db.Column(db.String(64), nullable=False, index=True)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow, index=True)
    likes = db.Column(db.Integer, nullable=False, default=0)
    # Present only on seeded rows, which carry the relative time shown in the design.
    when_label = db.Column(db.String(32), nullable=True)

    def __repr__(self) -> str:
        return f"<ForumPost {self.id} {self.author!r} #{self.channel}>"


class QuizAttempt(db.Model):
    __tablename__ = "quiz_attempt"

    id = db.Column(db.Integer, primary_key=True)
    module = db.Column(db.String(64), nullable=False, index=True)
    question_id = db.Column(db.String(16), nullable=False)
    chosen = db.Column(db.String(8), nullable=False)
    correct = db.Column(db.Boolean, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow, index=True)

    def __repr__(self) -> str:
        return f"<QuizAttempt {self.module} {self.question_id} {self.chosen}>"


class UserProfile(db.Model):
    __tablename__ = "user_profile"

    id = db.Column(db.Integer, primary_key=True)
    display_name = db.Column(db.String(60), nullable=False)
    role = db.Column(db.String(32), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow)

    def __repr__(self) -> str:
        return f"<UserProfile {self.display_name!r}>"


def seed_forum(content) -> int:
    """Insert the design's sample posts once, on an empty table.

    Post bodies are authored copy from content.json; the channel assignment is
    structure, so the seeds land in the first channel, which is the view the
    design shows.
    """
    if db.session.query(ForumPost.id).first() is not None:
        return 0

    channel = content.default_channel_slug()
    rows = [
        ForumPost(
            author=post["author"],
            accent=post["accent"],
            channel=channel,
            body=post["body"],
            likes=post["likes"],
            when_label=post["when"],
        )
        for post in content.seed_posts()
    ]
    db.session.add_all(rows)
    db.session.commit()
    return len(rows)
