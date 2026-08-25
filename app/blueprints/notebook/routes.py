"""Screen 15: the prompt library."""

from __future__ import annotations

from flask import render_template

from ...data import content
from . import bp


@bp.route("/", methods=["GET"], strict_slashes=False)
def index():
    return render_template(
        "notebook/index.html", page=content.get_page("notebook"), active_nav="notebook"
    )
