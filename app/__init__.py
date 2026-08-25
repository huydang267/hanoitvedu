"""Application factory for HaNoiTVEdu."""

from __future__ import annotations

from flask import Flask, render_template

from config import Config, resolve_config

from .data import content
from .extensions import db
from .security import init_csrf


def create_app(config: type[Config] | str | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)

    if config is None or isinstance(config, str):
        config = resolve_config(config)
    app.config.from_object(config() if isinstance(config, type) else config)

    db.init_app(app)
    init_csrf(app)
    _register_blueprints(app)
    _register_jinja(app)
    _register_errors(app)
    _register_health(app)
    _register_cache_headers(app)

    with app.app_context():
        from . import models  # noqa: F401  (registers the tables)

        db.create_all()
        models.seed_forum(content)

    return app


def _register_blueprints(app: Flask) -> None:
    from .blueprints.forum import bp as forum_bp
    from .blueprints.learn import bp as learn_bp
    from .blueprints.notebook import bp as notebook_bp
    from .blueprints.overview import bp as overview_bp
    from .blueprints.practice import bp as practice_bp

    app.register_blueprint(overview_bp)
    app.register_blueprint(learn_bp, url_prefix="/learn")
    app.register_blueprint(practice_bp, url_prefix="/practice")
    app.register_blueprint(notebook_bp, url_prefix="/notebook")
    app.register_blueprint(forum_bp, url_prefix="/forum")


def _register_jinja(app: Flask) -> None:
    """Expose the content accessors templates need. No copy is defined here."""
    app.jinja_env.globals.update(
        site=content.site,
        nav_items=content.nav_items,
        get_page=content.get_page,
        # The LIVE badge sits on every page (CLAUDE.md 5.6); its wording is
        # authored copy, taken from the screen that spells it out.
        live_badge_label=content.get_page("home")["live_badge_label"],
    )
    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True


def _register_errors(app: Flask) -> None:
    @app.errorhandler(404)
    def not_found(_error):
        return render_template("404.html", active_nav=None), 404

    @app.errorhandler(500)
    def server_error(_error):
        return render_template("500.html", active_nav=None), 500


def _register_health(app: Flask) -> None:
    @app.get("/healthz")
    def healthz():
        return "ok", 200, {"Content-Type": "text/plain; charset=utf-8"}


def _register_cache_headers(app: Flask) -> None:
    max_age = app.config.get("SEND_FILE_MAX_AGE_DEFAULT", 0)

    @app.after_request
    def cache_static(response):
        from flask import request

        if request.path.startswith("/static/") and response.status_code == 200:
            if max_age:
                response.headers["Cache-Control"] = f"public, max-age={int(max_age)}"
            else:
                response.headers["Cache-Control"] = "no-cache"
        return response
