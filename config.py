"""Configuration objects for the HaNoiTVEdu app factory."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent
INSTANCE = ROOT / "instance"

# Sentinel so ProdConfig can refuse to boot on the development secret.
DEV_SECRET = "dev-only-not-for-production"


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if url:
        # Heroku-style postgres:// prefixes are not understood by SQLAlchemy 2.
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url
    INSTANCE.mkdir(exist_ok=True)
    return f"sqlite:///{INSTANCE / 'hanoitvedu.sqlite'}"


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or DEV_SECRET
    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Longest accepted forum submissions, enforced server-side.
    FORUM_AUTHOR_MAX = 60
    FORUM_BODY_MAX = 2000


class DevConfig(Config):
    DEBUG = True
    TEMPLATES_AUTO_RELOAD = True
    SEND_FILE_MAX_AGE_DEFAULT = 0


class ProdConfig(Config):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    PREFERRED_URL_SCHEME = "https"
    # One year; static filenames are stable and cache-busted by ?v= on change.
    SEND_FILE_MAX_AGE_DEFAULT = 31_536_000

    def __init__(self) -> None:
        if self.SECRET_KEY == DEV_SECRET:
            raise RuntimeError(
                "SECRET_KEY must be set in the environment before running in production."
            )


class TestConfig(Config):
    TESTING = True
    DEBUG = False
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite://"  # in-memory, per test run


CONFIGS = {
    "development": DevConfig,
    "production": ProdConfig,
    "testing": TestConfig,
}


def resolve_config(name: str | None = None) -> type[Config]:
    """Pick a config class by name, falling back to FLASK_ENV then development."""
    key = (name or os.environ.get("FLASK_ENV") or "development").lower()
    return CONFIGS.get(key, DevConfig)
