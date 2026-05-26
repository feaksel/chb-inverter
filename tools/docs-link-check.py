"""Crawl the built MkDocs site and report broken internal links.

Run from the repo root after a `mkdocs build`:

    py -3.12 tools/docs-link-check.py

Exits non-zero if any internal link is broken. External http(s) links are
reported but not failed on (network flakes shouldn't break CI).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import urldefrag, urlparse


SITE_DIR = Path(__file__).resolve().parent.parent / "site"
HREF_RE = re.compile(r'href="([^"]+)"')


def is_external(href: str) -> bool:
    return urlparse(href).scheme in {"http", "https", "mailto", "tel"}


def main() -> int:
    if not SITE_DIR.is_dir():
        print(f"error: {SITE_DIR} does not exist — run `mkdocs build` first.", file=sys.stderr)
        return 2

    html_files = sorted(SITE_DIR.rglob("*.html"))
    if not html_files:
        print(f"error: no HTML files under {SITE_DIR}.", file=sys.stderr)
        return 2

    broken: list[tuple[Path, str]] = []
    external_count = 0

    for html in html_files:
        text = html.read_text(encoding="utf-8", errors="ignore")
        for href in HREF_RE.findall(text):
            if not href or href.startswith("#"):
                continue
            if is_external(href):
                external_count += 1
                continue

            target, _frag = urldefrag(href)
            if not target:
                continue
            target_path = (html.parent / target).resolve()
            if target_path.is_dir():
                target_path = target_path / "index.html"
            if not target_path.exists():
                broken.append((html.relative_to(SITE_DIR), href))

    print(f"checked {len(html_files)} HTML pages, {external_count} external links skipped")

    if broken:
        print(f"\n{len(broken)} broken internal link(s):", file=sys.stderr)
        for src, href in broken:
            print(f"  {src} -> {href}", file=sys.stderr)
        return 1

    print("all internal links resolve")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
