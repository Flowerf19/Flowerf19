#!/usr/bin/env python3
"""Generate README.md and all typing-style SVG assets locally.

- Fetches live repo descriptions from the GitHub API (single source of truth).
- Renders every text block (headers + descriptions) as a self-hosted SVG in
  assets/gen/ with a CSS typewriter reveal — no external image services.
- Re-run and commit after changing any repo description on GitHub.
"""
import json
import os
import sys
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

USER = "Flowerf19"
REPOS = ["March7", "RAG", "agents-skills", "another-brain", "my_health_v001"]
LINE_WIDTH = 88  # max chars per desc line (fits 800px at 15px Fira Code)
FONT = "'Fira Code','Cascadia Code',Consolas,monospace"
GEN_DIR = "assets/gen"

ROOT = Path(__file__).resolve().parent.parent

HEADERS = {
    "header-main": {
        "lines": ["There is nothing in here...", "...except an AI Developer."],
        "size": 22, "weight": 700, "color": "#bb9af7",
        "width": 420, "line_height": 33, "center": True, "char_ms": 50,
        "alt": "There is nothing in here... except an AI Developer.",
    },
    "header-void": {
        "lines": ["> Inside the Void"],
        "size": 18, "weight": 700, "color": "#bb9af7",
        "width": 800, "line_height": 30, "center": False, "char_ms": 45,
        "alt": "Inside the Void",
    },
    "header-lab": {
        "lines": ["> The Lab"],
        "size": 18, "weight": 700, "color": "#bb9af7",
        "width": 800, "line_height": 30, "center": False, "char_ms": 45,
        "alt": "The Lab",
    },
    "header-access": {
        "lines": ["> Access Protocols:"],
        "size": 18, "weight": 700, "color": "#bb9af7",
        "width": 800, "line_height": 30, "center": False, "char_ms": 45,
        "alt": "Access Protocols",
    },
}


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


def render_svg(*, lines: list[str], size: int, weight: int, color: str,
               width: int, line_height: int, center: bool, char_ms: int) -> str:
    """Render text lines as an SVG with a staggered typewriter reveal."""
    height = line_height * len(lines)
    anchor = ' text-anchor="middle"' if center else ""
    x = width // 2 if center else 0
    css_lines = []
    texts = []
    delay = 0.0
    for i, line in enumerate(lines):
        dur = max(0.4, len(line) * char_ms / 1000)
        css_lines.append(
            f".l{i}{{animation-duration:{dur:.2f}s;animation-delay:{delay:.2f}s;"
            f"animation-timing-function:steps({max(1, len(line))});}}"
        )
        delay += dur + 0.15
        y = round(line_height * (i + 0.73))
        texts.append(
            f'  <text class="l{i}" x="{x}" y="{y}"{anchor}'
            f' xml:space="preserve">{escape(line)}</text>'
        )
    css = (
        f"text{{font-family:{FONT};font-size:{size}px;font-weight:{weight};"
        f"fill:{color};clip-path:inset(0 100% 0 0);animation-name:type;"
        f"animation-fill-mode:forwards;}}"
        "@keyframes type{to{clip-path:inset(0 0 0 0);}}"
        + "".join(css_lines)
    )
    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}"'
        f' fill="none" xmlns="http://www.w3.org/2000/svg">\n'
        f"  <style>{css}</style>\n" + "\n".join(texts) + "\n</svg>\n"
    )


def placeholder(key: str) -> str:
    return "{{" + key.upper().replace("-", "_") + "_BLOCK}}"


def write_block(outdir: Path, name: str, svg: str, alt: str, indent: str) -> str:
    (outdir / f"{name}.svg").write_text(svg, encoding="utf-8")
    return f'{indent}<img src="./{GEN_DIR}/{name}.svg" alt="{alt}" />'


def main() -> int:
    template_path = ROOT / "README.template.md"
    if not template_path.exists():
        print(f"missing template: {template_path}", file=sys.stderr)
        return 1
    content = template_path.read_text(encoding="utf-8")

    outdir = ROOT / GEN_DIR
    outdir.mkdir(parents=True, exist_ok=True)
    for stale in outdir.glob("*.svg"):
        stale.unlink()

    for name, spec in HEADERS.items():
        spec = dict(spec)
        alt = spec.pop("alt")
        content = content.replace(
            placeholder(name),
            write_block(outdir, name, render_svg(**spec), alt, "  "),
        )

    for repo in REPOS:
        try:
            desc = fetch_description(repo)
        except Exception as e:
            print(f"  ! {repo}: failed ({e})", file=sys.stderr)
            return 2
        chunks = wrap_lines(desc, LINE_WIDTH)
        lines = [("   ↳ " if i == 0 else "     ") + c for i, c in enumerate(chunks)]
        name = "desc-" + repo.lower().replace("_", "-")
        svg = render_svg(lines=lines, size=15, weight=500, color="#7aa2f7",
                         width=800, line_height=26, center=False, char_ms=22)
        content = content.replace(
            placeholder(repo + "-desc"),
            write_block(outdir, name, svg, f"{repo} description", "    "),
        )
        print(f"  {repo}: {desc}")

    (ROOT / "README.md").write_text(content, encoding="utf-8")
    print(f"ok: README.md + {len(HEADERS) + len(REPOS)} SVGs in {GEN_DIR}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
