"""Screens 1-4 plus the two landing cards whose copy does not exist yet."""

from __future__ import annotations

from flask import abort, render_template

from ...data import content
from . import bp


@bp.get("/")
def home():
    return render_template(
        "overview/home.html", page=content.get_page("home"), active_nav="overview"
    )


@bp.get("/about")
def about():
    return render_template(
        "overview/about.html", page=content.get_page("about"), active_nav="overview"
    )


@bp.get("/program")
def program():
    return render_template(
        "overview/program.html", page=content.get_page("program"), active_nav="overview"
    )


@bp.get("/program/<role>")
def role(role: str):
    entry = content.role_entry(role)
    if entry is None:
        abort(404)

    page = content.get_page(f"role_{role}")
    if page is None:
        # content.json carries only this role's label, so the screen renders
        # with that label and nothing invented around it (CLAUDE.md 6.4).
        return render_template(
            "overview/awaiting_copy.html", label=entry["label"], active_nav="overview"
        )

    return render_template("overview/role.html", page=page, active_nav="overview")


@bp.get("/blogs")
def blogs():
    card = content.home_card("overview.blogs")
    return render_template(
        "overview/awaiting_copy.html", label=card["label"], active_nav="overview"
    )


@bp.get("/me")
def profile():
    card = content.home_card("overview.profile")
    return render_template(
        "overview/awaiting_copy.html", label=card["label"], active_nav="overview"
    )
