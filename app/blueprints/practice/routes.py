"""Screens 13-14: the practice screen and the three-question quick check.

The answer key never reaches the browser before a submission. Templates receive
the quiz through content.get_quiz(), which strips every `answer` key; only the
grading paths below ask for it.
"""

from __future__ import annotations

from flask import abort, jsonify, render_template, request

from ...data import content
from ...extensions import db
from ...models import QuizAttempt
from . import bp


def _grade(module: str, form) -> tuple[dict[str, dict], int]:
    """Score a submission. Returns ({question id: result}, correct count)."""
    key = content.answer_key(module)
    results: dict[str, dict] = {}
    score = 0

    for question_id, expected in key.items():
        chosen = (form.get(question_id) or "").strip()
        if not chosen:
            continue
        correct = chosen == expected
        score += 1 if correct else 0
        results[question_id] = {
            "chosen": chosen,
            "correct": correct,
            "answer": expected,
        }
        db.session.add(
            QuizAttempt(
                module=module,
                question_id=question_id,
                chosen=chosen,
                correct=correct,
            )
        )

    if results:
        db.session.commit()
    return results, score


@bp.route("/", methods=["GET"], strict_slashes=False)
def index():
    modules = [
        (slug, module)
        for slug, module in content.all_modules()
        if module.get("practice")
    ]
    return render_template(
        "practice/index.html", modules=modules, active_nav="practice"
    )


@bp.get("/<module>")
def practice(module: str):
    practice_data = content.get_practice(module)
    if practice_data is None:
        abort(404)
    return render_template(
        "practice/practice.html",
        slug=module,
        module=content.get_module(module),
        practice=practice_data,
        has_quiz=content.get_quiz(module) is not None,
        active_nav="practice",
    )


@bp.route("/<module>/quiz", methods=["GET", "POST"])
def quiz(module: str):
    quiz_data = content.get_quiz(module)  # answers stripped
    if quiz_data is None:
        abort(404)

    results: dict[str, dict] = {}
    score = None
    if request.method == "POST":
        results, score = _grade(module, request.form)

    return render_template(
        "practice/quiz.html",
        slug=module,
        module=content.get_module(module),
        quiz=quiz_data,
        results=results,
        score=score,
        total=len(quiz_data["questions"]),
        active_nav="practice",
    )


@bp.post("/<module>/quiz/check")
def quiz_check(module: str):
    """JSON grading endpoint for the progressive-enhancement path."""
    if content.get_quiz(module) is None:
        abort(404)
    results, score = _grade(module, request.form)
    return jsonify(
        {
            "results": results,
            "score": score,
            "total": len(content.answer_key(module)),
        }
    )
