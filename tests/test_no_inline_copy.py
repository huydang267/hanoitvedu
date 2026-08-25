"""No template contains a sentence of site copy.

Copy belongs to content/content.json and reaches the page as a rendered value
(CLAUDE.md section 6). This test pulls the authored strings straight out of the
JSON and fails if any of them appears literally inside a template.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

TEMPLATES = ROOT / "app" / "templates"
CONTENT = ROOT / "content" / "content.json"

# Keys that hold structure, not authored copy. Mirrors tools/verify_content.py.
SKIP_KEYS = {
    "_README", "source", "active_nav", "accent", "endpoint", "key", "slug",
    "module", "state", "answer", "n", "id", "likes", "when", "type", "columns",
    "decor",
}

# Single words that are also legitimate code identifiers or CSS/HTML fragments.
# Only strings long enough to be unmistakably copy are checked.
MIN_LENGTH = 12


def authored_strings() -> list[str]:
    data = json.loads(CONTENT.read_text(encoding="utf-8"))
    out: list[str] = []

    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key not in SKIP_KEYS:
                    walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)
        elif isinstance(node, str) and len(node.strip()) >= MIN_LENGTH:
            out.append(node.strip())

    walk(data)
    return out


class InlineCopyTests(unittest.TestCase):
    def test_templates_exist(self):
        self.assertTrue(list(TEMPLATES.rglob("*.html")), "no templates found")

    def test_no_authored_sentence_appears_inline(self):
        strings = authored_strings()
        self.assertGreater(len(strings), 100, "content.json looks unexpectedly small")

        offenders: list[tuple[str, str]] = []
        for template in sorted(TEMPLATES.rglob("*.html")):
            source = template.read_text(encoding="utf-8")
            for text in strings:
                if text in source:
                    offenders.append((str(template.relative_to(ROOT)), text[:70]))

        self.assertEqual(
            offenders,
            [],
            "site copy hard-coded in templates:\n"
            + "\n".join(f"  {path}: {text!r}" for path, text in offenders),
        )

    def test_no_authored_sentence_appears_in_python_or_css_or_js(self):
        """Copy must not leak into the data layer, the views, the CSS or the JS."""
        strings = authored_strings()
        roots = [
            ROOT / "app",
            ROOT / "config.py",
            ROOT / "run.py",
        ]
        files: list[Path] = []
        for root in roots:
            if root.is_file():
                files.append(root)
            else:
                for suffix in ("*.py", "*.css", "*.js"):
                    files.extend(root.rglob(suffix))

        offenders: list[tuple[str, str]] = []
        for path in sorted(set(files)):
            if "__pycache__" in path.parts:
                continue
            source = path.read_text(encoding="utf-8")
            for text in strings:
                if text in source:
                    offenders.append((str(path.relative_to(ROOT)), text[:70]))

        self.assertEqual(
            offenders,
            [],
            "site copy hard-coded outside content.json:\n"
            + "\n".join(f"  {path}: {text!r}" for path, text in offenders),
        )


if __name__ == "__main__":
    unittest.main()
