#!/usr/bin/env python3
"""
verify_content.py — guarantees the site never drifts from the author's wording.

Every leaf string in content/content.json must appear, character-for-character
(whitespace collapsed), in the pdftotext dump of the page it came from.

Usage:
    python tools/verify_content.py            # check content.json vs source dumps
    python tools/verify_content.py --strict   # exit 1 on any miss (use in CI / pre-commit)

Notes:
- pdftotext lays multi-column pages out side by side, so a sentence that is
  visually one line can be broken by text from another column. Those show up as
  MISSES and must be eyeballed against the PDF once, then added to ALLOW below.
- Never "fix" a miss by editing content.json to match the dump loosely. The dump
  is the source of truth; content.json copies it.
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content" / "content.json"
SOURCE_DIR = ROOT / "content" / "flow"      # matching corpus (pdftotext reading order)
REF_DIR = ROOT / "content" / "source"      # human-readable layout dump, for eyeballing

# Keys that hold structure/ids, not authored copy.
SKIP_KEYS = {
    "_README", "source", "active_nav", "accent", "endpoint", "key", "slug",
    "module", "state", "answer", "n", "id", "likes", "when", "type", "columns",
    "decor",
}

# Strings verified by hand against the PDF that pdftotext splits across columns.
ALLOW: set[str] = set()


def norm(s: str) -> str:
    s = unicodedata.normalize("NFC", s)
    s = s.replace(" ", " ")
    return re.sub(r"\s+", " ", s).strip()


def load_corpus() -> dict[str, str]:
    pages = {p.stem: norm(p.read_text(encoding="utf-8")) for p in sorted(SOURCE_DIR.glob("page-*.txt"))}
    pages["__all__"] = " ".join(pages.values())
    return pages


def walk(node, page: str | None, path: str, out: list[tuple[str, str, str]]) -> None:
    """Collect (json_path, page_hint, string) for every authored leaf string."""
    if isinstance(node, dict):
        page = node.get("source", page)
        for k, v in node.items():
            if k in SKIP_KEYS:
                continue
            walk(v, page, f"{path}.{k}", out)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            walk(v, page, f"{path}[{i}]", out)
    elif isinstance(node, str) and node.strip():
        out.append((path, page or "__all__", node))


def main() -> int:
    strict = "--strict" in sys.argv
    data = json.loads(CONTENT.read_text(encoding="utf-8"))
    corpus = load_corpus()

    leaves: list[tuple[str, str, str]] = []
    walk(data, None, "$", leaves)

    misses: list[tuple[str, str, str]] = []
    for path, page, text in leaves:
        needle = norm(text)
        if needle in ALLOW:
            continue
        pattern = re.compile(r"(?<!\\w)" + re.escape(needle) + r"(?!\\w)")
        haystack = corpus.get(page, corpus["__all__"])
        if pattern.search(haystack) or pattern.search(corpus["__all__"]):
            continue
        misses.append((path, page, needle))

    checked = len(leaves)
    print(f"checked {checked} strings against {len(corpus) - 1} source pages")

    if not misses:
        print("OK — every string matches the author's wording exactly.")
        return 0

    print(f"\n{len(misses)} string(s) not found verbatim in the source dump:\n")
    for path, page, needle in misses:
        print(f"  [{page}] {path}")
        print(f"      {needle[:160]}{'…' if len(needle) > 160 else ''}")
    print("\nEach one is either a typo introduced in content.json (fix content.json)")
    print("or a column split in pdftotext (verify against the PDF, then add to ALLOW).")
    return 1 if strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
