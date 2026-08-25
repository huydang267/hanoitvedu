"""Every route answers, the shell renders, and the quiz keeps its answers."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import create_app  # noqa: E402
from app.data import content  # noqa: E402
from config import TestConfig  # noqa: E402

MODULE = "ai-research-planning"


def all_get_routes() -> list[str]:
    """Every GET route in the page map, built from content.json."""
    routes = [
        "/",
        "/about",
        "/program",
        "/blogs",
        "/me",
        "/learn",
        "/practice",
        "/notebook",
        "/forum",
        "/healthz",
    ]
    routes += [f"/program/{role['slug']}" for role in content.get_page("program")["roles"]]
    for slug in content.module_slugs():
        routes.append(f"/learn/{slug}")
        routes += [f"/learn/{slug}/{step}" for step in content.lesson_slugs(slug)]
        if content.get_practice(slug):
            routes.append(f"/practice/{slug}")
        if content.get_quiz(slug):
            routes.append(f"/practice/{slug}/quiz")
    routes += [f"/forum/{channel['slug']}" for channel in content.forum_channels()]
    return routes


class RouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app(TestConfig)

    def setUp(self):
        self.client = self.app.test_client()

    def _csrf(self) -> str:
        """Fetch a page to seed the session, then read the token out of it."""
        html = self.client.get("/forum").get_data(as_text=True)
        match = re.search(r'name="csrf_token" value="([^"]+)"', html)
        self.assertIsNotNone(match, "no CSRF token rendered into the forum form")
        return match.group(1)

    # -- every route answers 200 ------------------------------------------

    def test_every_get_route_returns_200(self):
        for route in all_get_routes():
            with self.subTest(route=route):
                response = self.client.get(route)
                self.assertEqual(response.status_code, 200, route)

    def test_route_count_covers_the_page_map(self):
        # 16 screens + the 4 awaiting-copy pages + 2 section indexes + healthz.
        self.assertGreaterEqual(len(all_get_routes()), 22)

    # -- the shell renders on every page ----------------------------------

    def test_shell_present_on_every_page(self):
        for route in all_get_routes():
            if route == "/healthz":
                continue
            with self.subTest(route=route):
                html = self.client.get(route).get_data(as_text=True)
                self.assertIn('class="card"', html)
                self.assertIn("bg-bars__bar--red", html)
                self.assertIn("bg-bars__bar--blue", html)
                self.assertIn('class="navbar__pill"', html)
                self.assertIn('class="live-badge"', html)
                self.assertIn("image/logo.png", html)

    def test_all_four_logo_colours_on_every_page(self):
        """Each screen must carry all four logo colours (CLAUDE.md 5.4)."""
        for route in all_get_routes():
            if route == "/healthz":
                continue
            with self.subTest(route=route):
                html = self.client.get(route).get_data(as_text=True)
                for colour in ("red", "blue", "yellow", "green"):
                    self.assertRegex(
                        html,
                        rf'(--c-{colour}\)|data-accent="{colour}"|bar--{colour})',
                        f"{route} is missing {colour}",
                    )

    def test_active_nav_marks_one_item(self):
        for route, key in [
            ("/", "OVERVIEW"),
            ("/learn/%s/01" % MODULE, "LEARN"),
            ("/practice/%s" % MODULE, "PRACTICE"),
            ("/notebook", "NOTEBOOK"),
            ("/forum", "FORUM"),
        ]:
            with self.subTest(route=route):
                html = self.client.get(route).get_data(as_text=True)
                self.assertIn('aria-current="page"', html)
                self.assertRegex(html, rf'navbar__link--active"[^>]*>{key}<')

    # -- errors ------------------------------------------------------------

    def test_unknown_paths_use_the_custom_404(self):
        for route in [
            "/not-a-page",
            "/program/not-a-role",
            f"/learn/{MODULE}/99",
            "/learn/not-a-module",
            f"/practice/not-a-module/quiz",
            "/forum/not-a-channel",
        ]:
            with self.subTest(route=route):
                response = self.client.get(route)
                self.assertEqual(response.status_code, 404)
                self.assertIn("404", response.get_data(as_text=True))
                self.assertIn('class="card"', response.get_data(as_text=True))

    def test_healthz_is_plain_ok(self):
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_data(as_text=True), "ok")

    # -- quiz --------------------------------------------------------------

    def test_quiz_page_never_exposes_the_answer_key(self):
        html = self.client.get(f"/practice/{MODULE}/quiz").get_data(as_text=True)
        self.assertNotIn("quiz-option--correct", html)
        self.assertNotIn('"answer"', html)
        for question_id, answer in content.answer_key(MODULE).items():
            self.assertNotRegex(
                html,
                rf'data-answer="{answer}"',
                f"{question_id} answer leaked into the initial HTML",
            )

    def test_quiz_grades_on_post(self):
        token = self._csrf()
        key = content.answer_key(MODULE)
        response = self.client.post(
            f"/practice/{MODULE}/quiz",
            data={"csrf_token": token, **key},
        )
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("quiz-option--correct", html)
        self.assertIn(f"{len(key)} / {len(key)}", html)

    def test_quiz_check_endpoint_returns_json(self):
        token = self._csrf()
        key = content.answer_key(MODULE)
        wrong = {qid: ("A" if ans != "A" else "B") for qid, ans in key.items()}
        response = self.client.post(
            f"/practice/{MODULE}/quiz/check",
            data={"csrf_token": token, **wrong},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["score"], 0)
        self.assertEqual(payload["total"], len(key))
        for qid in key:
            self.assertFalse(payload["results"][qid]["correct"])

    def test_quiz_attempts_are_recorded(self):
        from app.extensions import db
        from app.models import QuizAttempt

        token = self._csrf()
        key = content.answer_key(MODULE)
        self.client.post(f"/practice/{MODULE}/quiz", data={"csrf_token": token, **key})
        with self.app.app_context():
            count = db.session.query(QuizAttempt).count()
        self.assertGreaterEqual(count, len(key))

    # -- forum -------------------------------------------------------------

    def test_forum_seeded_from_content_json(self):
        html = self.client.get("/forum").get_data(as_text=True)
        for post in content.seed_posts():
            self.assertIn(post["author"], html)

    def test_forum_post_round_trip(self):
        token = self._csrf()
        response = self.client.post(
            "/forum/post",
            data={
                "csrf_token": token,
                "channel": "general",
                "author": "Test Author",
                "body": "A message posted by the route test.",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("A message posted by the route test.", response.get_data(as_text=True))

    def test_forum_escapes_user_input(self):
        token = self._csrf()
        response = self.client.post(
            "/forum/post",
            data={
                "csrf_token": token,
                "channel": "general",
                "author": "XSS",
                "body": "<script>alert(1)</script>",
            },
            follow_redirects=True,
        )
        html = response.get_data(as_text=True)
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_forum_rejects_blank_and_overlong_posts(self):
        token = self._csrf()
        blank = self.client.post(
            "/forum/post",
            data={"csrf_token": token, "channel": "general", "author": " ", "body": " "},
        )
        self.assertEqual(blank.status_code, 400)

        long_post = self.client.post(
            "/forum/post",
            data={
                "csrf_token": token,
                "channel": "general",
                "author": "Test",
                "body": "x" * 2001,
            },
        )
        self.assertEqual(long_post.status_code, 400)

    def test_forum_rejects_unknown_channel(self):
        token = self._csrf()
        response = self.client.post(
            "/forum/post",
            data={
                "csrf_token": token,
                "channel": "nope",
                "author": "Test",
                "body": "Hello",
            },
        )
        self.assertEqual(response.status_code, 404)

    # -- CSRF --------------------------------------------------------------

    def test_post_without_csrf_token_is_rejected(self):
        self.client.get("/forum")  # seed the session
        for path, data in [
            ("/forum/post", {"channel": "general", "author": "A", "body": "B"}),
            (f"/practice/{MODULE}/quiz", {"Q1.": "B"}),
            (f"/practice/{MODULE}/quiz/check", {"Q1.": "B"}),
        ]:
            with self.subTest(path=path):
                self.assertEqual(self.client.post(path, data=data).status_code, 400)

    def test_post_with_wrong_csrf_token_is_rejected(self):
        self._csrf()
        response = self.client.post(
            "/forum/post",
            data={
                "csrf_token": "not-the-right-token",
                "channel": "general",
                "author": "A",
                "body": "B",
            },
        )
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
