"""Loader and accessors for content/content.json.

This module is the only bridge between the author's copy and the views. It holds
no site copy of its own: every string a visitor reads comes out of the JSON. See
CLAUDE.md section 6 for the verbatim rule.
"""

from __future__ import annotations

import copy
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONTENT_FILE = ROOT / "content" / "content.json"

# Loaded once at import; treated as immutable, so every accessor that hands a
# mutable structure to a caller deep-copies it first.
_DATA: dict[str, Any] = json.loads(CONTENT_FILE.read_text(encoding="utf-8"))

# Lesson reading order for the module, matching the screen order in CLAUDE.md
# section 4: the mistakes screen sits between step 04 and step 05.
_LESSON_ORDER = ["01", "02", "03", "04", "mistakes", "05", "06"]


# --------------------------------------------------------------------------- site


def site() -> dict[str, Any]:
    """Wordmark, tagline and logo caption."""
    return _DATA["site"]


def nav_items() -> list[dict[str, Any]]:
    """The five navbar entries, in order."""
    return _DATA["nav"]


# -------------------------------------------------------------------------- pages


def get_page(name: str) -> dict[str, Any] | None:
    """One non-lesson screen (home, about, program, role_editorial, ...)."""
    return _DATA["pages"].get(name)


def role_entry(slug: str) -> dict[str, Any] | None:
    """The role card for a slug, from the Our Program screen."""
    for role in get_page("program")["roles"]:
        if role["slug"] == slug:
            return role
    return None


def home_card(endpoint: str) -> dict[str, Any] | None:
    """The landing-page entry card that points at an endpoint."""
    for card in get_page("home")["cards"]:
        if card["endpoint"] == endpoint:
            return card
    return None


# ------------------------------------------------------------------------ modules


def module_slugs() -> list[str]:
    return list(_DATA["modules"].keys())


def get_module(slug: str) -> dict[str, Any] | None:
    return _DATA["modules"].get(slug)


def all_modules() -> list[tuple[str, dict[str, Any]]]:
    """(slug, module) pairs for index pages."""
    return list(_DATA["modules"].items())


def lesson_slugs(module: str) -> list[str]:
    """Lesson slugs in reading order, restricted to those the module defines."""
    mod = get_module(module)
    if not mod:
        return []
    present = {lesson["slug"] for lesson in mod["lessons"]}
    ordered = [slug for slug in _LESSON_ORDER if slug in present]
    # Anything the module adds beyond the known order still gets a page.
    ordered += [s for s in (l["slug"] for l in mod["lessons"]) if s not in _LESSON_ORDER]
    return ordered


def lessons_in_order(module: str) -> list[dict[str, Any]]:
    return [get_lesson(module, slug) for slug in lesson_slugs(module)]


def get_lesson(module: str, step: str) -> dict[str, Any] | None:
    mod = get_module(module)
    if not mod:
        return None
    for lesson in mod["lessons"]:
        if lesson["slug"] == step:
            return lesson
    return None


def lesson_neighbours(
    module: str, step: str
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """(previous, next) lesson dicts, either of which may be None at the ends."""
    order = lesson_slugs(module)
    if step not in order:
        return None, None
    i = order.index(step)
    prev = get_lesson(module, order[i - 1]) if i > 0 else None
    nxt = get_lesson(module, order[i + 1]) if i + 1 < len(order) else None
    return prev, nxt


# --------------------------------------------------------------- practice and quiz


def get_practice(module: str) -> dict[str, Any] | None:
    mod = get_module(module)
    return mod.get("practice") if mod else None


def get_quiz(module: str, *, with_answers: bool = False) -> dict[str, Any] | None:
    """The quiz for a module.

    The answer key is stripped unless explicitly requested, so a template can
    never leak it into the initial HTML. Only the grading view asks for it.
    """
    mod = get_module(module)
    if not mod or "quiz" not in mod:
        return None
    quiz = copy.deepcopy(mod["quiz"])
    if not with_answers:
        for question in quiz["questions"]:
            question.pop("answer", None)
    return quiz


def answer_key(module: str) -> dict[str, str]:
    """{question id: correct option key}. Server-side grading only."""
    quiz = get_quiz(module, with_answers=True)
    if not quiz:
        return {}
    return {q["id"]: q["answer"] for q in quiz["questions"]}


# -------------------------------------------------------------------------- forum


def slugify(label: str) -> str:
    """Turn a channel label into a URL slug: strips '#', folds '&' and spaces
    to hyphens, lowercases. The slug is structure; the label stays authored."""
    text = unicodedata.normalize("NFKD", label)
    text = text.replace("&", " ").replace("#", " ")
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    return re.sub(r"[\s_-]+", "-", text).strip("-").lower()


def forum_channels() -> list[dict[str, str]]:
    """[{'slug': ..., 'label': ...}] for each channel named in content.json."""
    return [
        {"slug": slugify(label), "label": label}
        for label in get_page("forum")["channels"]
    ]


def default_channel_slug() -> str:
    return forum_channels()[0]["slug"]


def channel_by_slug(slug: str) -> dict[str, str] | None:
    for channel in forum_channels():
        if channel["slug"] == slug:
            return channel
    return None


def seed_posts() -> list[dict[str, Any]]:
    return copy.deepcopy(get_page("forum")["seed_posts"])
