"""Build the handbook web page from HANDBOOK.md.

    python3 scripts/handbook_page/build.py            # writes build/handbook.html

The page embeds the Markdown and renders it in the browser (marked + mermaid
from cdnjs), so HANDBOOK.md stays the only source. Links to repo files become
GitHub links, because the page is hosted outside the repo.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = "https://github.com/GetVizzyWithIt/Saxscribe/blob/main/"
TEMPLATE = Path(__file__).with_name("template.html")


def github_links(md: str) -> str:
    """Point relative links (docs/..., CLAUDE.md) at the file on GitHub; keep #anchors and full URLs."""
    def fix(m: re.Match) -> str:
        text, target = m.group(1), m.group(2)
        if re.match(r"^(https?:|#|mailto:)", target):
            return m.group(0)
        return f"[{text}]({REPO}{target})"
    return re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", fix, md)


def build(out: Path | None = None) -> Path:
    md = github_links((ROOT / "HANDBOOK.md").read_text())
    md = re.sub(r"<!-- /?auto:[a-z-]+ -->\n?", "", md)
    html = TEMPLATE.read_text().replace("__HANDBOOK_JSON__", json.dumps(md).replace("</", "<\\/"))
    out = out or ROOT / "build" / "handbook.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html)
    return out


if __name__ == "__main__":
    print(build())
