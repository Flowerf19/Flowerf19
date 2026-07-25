#!/usr/bin/env python3
"""Generate README.md from README.template.md by fetching live repo descriptions.

Each repo's {{REPO_DESC_BLOCK}} placeholder is replaced by one or more typing-svg
<img> tags — descriptions wrap onto multiple lines (no truncation).
"""
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

USER = "Flowerf19"
REPOS = ["March7", "RAG", "agents-skills", "another-brain", "my_health_v001"]
LINE_WIDTH = 88  # chars per wrapped line (fits within typing-svg width=800)

ROOT = Path(__file__).resolve().parent.parent

SVG_BASE = (
    "https://readme-typing-svg.demolab.com/"
    "?font=Fira+Code&weight=500&size=15&height=26&color=7aa2f7&width=800"
    "&lines={lines}&repeat=false"
)


def fetch_description(repo: str) -> str:
    url = f"https://api.github.com/repos/{USER}/{repo}"
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.load(resp)
    return (data.get("description") or "").strip()


def wrap_lines(text: str, max_chars: int) -> list[str]:
    """Split text into lines of at most max_chars on word boundaries."""
    if not text:
        return []
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    current_len = 0
    for word in words:
        added = len(word) + (1 if current else 0)
        if current and current_len + added > max_chars:
            lines.append(" ".join(current))
            current = [word]
            current_len = len(word)
        else:
            current.append(word)
            current_len += added
    if current:
        lines.append(" ".join(current))
    return lines


def render_desc_block(desc: str, alt: str) -> str:
    """Render description as 1+ typing-svg <img> tags. First line has ↳ prefix."""
    chunks = wrap_lines(desc, LINE_WIDTH)
    if not chunks:
        return ""
    imgs = []
    for i, chunk in enumerate(chunks):
        prefix = "   ↳ " if i == 0 else "     "  # "   ↳ " or 5 spaces
        encoded = urllib.parse.quote(prefix + chunk)
        url = SVG_BASE.format(lines=encoded)
        imgs.append(f'    <img src="{url}" alt="{alt} desc {i + 1}" />')
    return "<br/>\n".join(imgs)


def placeholder_for(repo: str) -> str:
    key = repo.upper().replace("-", "_")
    return "{{" + key + "_DESC_BLOCK}}"


def main() -> int:
    template_path = ROOT / "README.template.md"
    if not template_path.exists():
        print(f"missing template: {template_path}", file=sys.stderr)
        return 1
    content = template_path.read_text(encoding="utf-8")

    for repo in REPOS:
        try:
            desc = fetch_description(repo)
        except Exception as e:
            print(f"  ! {repo}: failed ({e})", file=sys.stderr)
            return 2
        block = render_desc_block(desc, repo)
        content = content.replace(placeholder_for(repo), block)
        print(f"  {repo}: {desc}")

    (ROOT / "README.md").write_text(content, encoding="utf-8")
    print("ok: README.md generated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
