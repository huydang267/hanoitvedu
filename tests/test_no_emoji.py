"""No emoji anywhere in the app or in what it renders (CLAUDE.md section 5.8).

Scope note: this checks for *emoji*. It deliberately does not flag the dingbats
and punctuation the author uses in her own copy — the check and cross in
"✕ INSTEAD OF:" / "✓ TRY:", the arrows in "AI plans → You search → You verify",
the heart on a forum post, the bullet in the LIVE badge. Those are verified
authored strings or typographic marks, not emoji, and the verbatim rule forbids
altering them.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import create_app  # noqa: E402
from tests.test_routes import all_get_routes  # noqa: E402
from config import TestConfig  # noqa: E402

# Unicode blocks that contain emoji proper. Ranges are (first, last) inclusive.
EMOJI_RANGES = [
    (0x1F300, 0x1F5FF),  # symbols and pictographs
    (0x1F600, 0x1F64F),  # emoticons
    (0x1F680, 0x1F6FF),  # transport and map
    (0x1F700, 0x1F77F),  # alchemical
    (0x1F900, 0x1F9FF),  # supplemental symbols and pictographs
    (0x1FA70, 0x1FAFF),  # extended-A
    (0x2600, 0x26FF),    # miscellaneous symbols
    (0x1F1E6, 0x1F1FF),  # regional indicators (flags)
]

# Codepoints that only count as emoji when followed by U+FE0F.
VARIATION_SELECTOR = "️"


def emoji_in(text: str) -> list[str]:
    found = []
    for index, char in enumerate(text):
        point = ord(char)
        if any(low <= point <= high for low, high in EMOJI_RANGES):
            found.append(char)
        elif text[index + 1 : index + 2] == VARIATION_SELECTOR and point > 0x2000:
            found.append(char + VARIATION_SELECTOR)
    return found


class EmojiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app(TestConfig)

    def test_no_emoji_in_source_files(self):
        offenders = []
        for suffix in ("*.html", "*.css", "*.js", "*.py"):
            for path in (ROOT / "app").rglob(suffix):
                if "__pycache__" in path.parts:
                    continue
                found = emoji_in(path.read_text(encoding="utf-8"))
                if found:
                    offenders.append((str(path.relative_to(ROOT)), found))
        self.assertEqual(offenders, [], f"emoji found in app/: {offenders}")

    def test_no_emoji_in_content_json(self):
        text = (ROOT / "content" / "content.json").read_text(encoding="utf-8")
        self.assertEqual(emoji_in(text), [], "emoji found in content.json")

    def test_no_emoji_in_rendered_output(self):
        client = self.app.test_client()
        offenders = []
        for route in all_get_routes():
            found = emoji_in(client.get(route).get_data(as_text=True))
            if found:
                offenders.append((route, found))
        self.assertEqual(offenders, [], f"emoji rendered on: {offenders}")

    def test_authored_dingbats_survive(self):
        """The author's own marks are rendered, not stripped or substituted."""
        client = self.app.test_client()
        html = client.get("/learn/ai-research-planning/01").get_data(as_text=True)
        self.assertIn("✕", html)  # the cross in "✕ INSTEAD OF:"
        self.assertIn("✓", html)  # the check in "✓ TRY:"


if __name__ == "__main__":
    unittest.main()
