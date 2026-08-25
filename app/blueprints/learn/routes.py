"""Screens 5-12: the module overview and its data-driven lesson pages."""

from __future__ import annotations

from flask import abort, render_template

from ...data import content
from . import bp


@bp.route("/", methods=["GET"], strict_slashes=False)
def index():
    return render_template(
        "learn/index.html", modules=content.all_modules(), active_nav="learn"
    )


@bp.get("/<module>")
def module(module: str):
    mod = content.get_module(module)
    if mod is None:
        abort(404)
    return render_template(
        "learn/module.html",
        slug=module,
        module=mod,
        lessons=content.lessons_in_order(module),
        # Screen 5 sits under OVERVIEW in the page map.
        active_nav="overview",
    )


@bp.get("/<module>/<step>")
def lesson(module: str, step: str):
    lesson_data = content.get_lesson(module, step)
    if lesson_data is None:
        abort(404)
    previous, following = content.lesson_neighbours(module, step)
    return render_template(
        "learn/lesson.html",
        slug=module,
        module=content.get_module(module),
        lesson=lesson_data,
        previous=previous,
        following=following,
        active_nav="learn",
    )
