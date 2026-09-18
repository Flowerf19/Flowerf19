#!/usr/bin/env python3
"""Build a Thyca-style GitHub profile and responsive, self-hosted SVGs.

Normal runs refresh public GitHub About descriptions. --offline uses the last
checked-in metadata; --check verifies generated output without writing files.
Editorial summaries and selection live in profile.json.
"""
import argparse
from html import escape
import json
import os
from pathlib import Path
import sys
import urllib.request

from notebook_svg import cover, focus, heading, project_card

ROOT = Path(__file__).resolve().parent.parent
CACHE = Path("data/repositories.json")
GEN = Path("assets/gen")


def fetch_repositories(handle):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "profile-notebook"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    result = {}
    page = 1
    while True:
        url = f"https://api.github.com/users/{handle}/repos?type=owner&per_page=100&page={page}"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as response:
            rows = json.load(response)
        if not isinstance(rows, list):
            raise ValueError("GitHub returned an invalid repository list")
        for repo in rows:
            if not repo.get("fork") and repo["name"] != handle:
                result[repo["name"]] = {key: repo.get(key) for key in ("description", "html_url", "language")}
        if len(rows) < 100:
            break
        page += 1
    return result


def summary_for(project, repositories):
    about = (repositories.get(project["repo"], {}).get("description") or "").strip()
    return project["summary"] if project.get("curated") else about or project["summary"]


def picture(name, alt, link=None):
    markup = (f'<picture>\n'
              f'  <source media="(max-width: 600px)" srcset="./{GEN}/{name}-mobile.svg">\n'
              f'  <img src="./{GEN}/{name}.svg" width="800" alt="{escape(alt, quote=True)}">\n'
              f'</picture>')
    if link:
        markup = f'<a href="{escape(link, quote=True)}">\n{markup}\n</a>'
    return f'<p align="center">\n{markup}\n</p>'


def build(profile, repositories, template):
    artifacts = {}

    def pair(name, renderer, alt, link=None):
        artifacts[GEN / f"{name}.svg"] = renderer(False)
        artifacts[GEN / f"{name}-mobile.svg"] = renderer(True)
        return picture(name, alt, link)

    blocks = {
        "COVER": pair("cover", lambda m: cover(profile, m),
                      profile["name"] + " — " + profile["role"] + ". " + profile["intro"]),
        "FOCUS": pair("focus", lambda m: focus(profile, m),
                      "Areas of work: " + "; ".join(a + ": " + b for a, b in profile["focus"])),
        "PROJECTS_HEADING": pair("projects-heading", lambda m: heading(
            "Things I am building", "Assistants, memories, and the tools around them.", m), "Selected projects"),
        "CONTACT_HEADING": pair("contact-heading", lambda m: heading(
            "Leave a note", "A question, an idea, or a project worth talking about.", m), "Contact Nguyễn Hoà"),
    }
    text_version = [f'### {profile["name"]} · {profile["role"]}',
                    profile["intro"], "### Areas of work"]
    text_version += [f'- **{label}:** {detail}' for label, detail in profile["focus"]]
    index = 0
    for group, label in (("projects", "Selected projects"), ("notes", "Research notes")):
        if not profile[group]:
            continue
        cards = []
        text_version.append(f"### {label}")
        for project in profile[group]:
            index += 1
            repo = project["repo"]
            url = f'https://github.com/{profile["handle"]}/{repo}'
            description = summary_for(project, repositories)
            name = "project-" + repo.lower().replace("_", "-")
            cards.append(pair(name,
                lambda m, p=project, d=description, n=index: project_card(p, d, n, m),
                f'{project["title"]} — {description}', url))
            text_version.append(f'- **[{project["title"]}]({url}):** {description}')
        blocks[group.upper()] = "\n\n".join(cards)
    contacts = " &nbsp; · &nbsp; ".join(
        f'<a href="{escape(c["url"], quote=True)}">{escape(c["name"])}</a>'
        for c in profile["contacts"][:2])
    emails = " &nbsp; · &nbsp; ".join(
        f'<a href="{escape(c["url"], quote=True)}">{escape(c["name"])}</a>'
        for c in profile["contacts"][2:])
    blocks["CONTACTS"] = f'<p align="center">{contacts}<br>{emails}</p>'
    blocks["TEXT_VERSION"] = "\n\n".join(text_version)
    for name, block in blocks.items():
        template = template.replace("{{" + name + "}}", block)
    if "{{" in template or "}}" in template:
        raise ValueError("Unresolved README template placeholder")
    artifacts[Path("README.md")] = template
    artifacts[CACHE] = json.dumps(repositories, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    return artifacts


def main(argv=None, root=ROOT):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true", help="Use checked-in public metadata")
    parser.add_argument("--check", action="store_true", help="Report stale output without changing files")
    args = parser.parse_args(argv)
    try:
        profile = json.loads((root / "profile.json").read_text(encoding="utf-8"))
        repositories = (json.loads((root / CACHE).read_text(encoding="utf-8"))
                        if args.offline else fetch_repositories(profile["handle"]))
        expected = [p["repo"] for p in profile["projects"] + profile["notes"]]
        missing = sorted(set(expected) - repositories.keys())
        if missing:
            raise ValueError("Selected repositories missing from public metadata: " + ", ".join(missing))
        repositories = {name: repositories[name] for name in expected}
        template = (root / "README.template.md").read_text(encoding="utf-8")
        artifacts = build(profile, repositories, template)
    except Exception as error:
        print(f"Profile generation failed before writing output: {type(error).__name__}: {error}", file=sys.stderr)
        return 2
    existing = {path.relative_to(root) for path in (root / GEN).glob("*.svg")}
    stale = existing - artifacts.keys()
    changed = [path for path, content in artifacts.items()
               if not (root / path).exists() or (root / path).read_text(encoding="utf-8") != content]
    if args.check:
        if changed or stale:
            print("Stale generated files: " + ", ".join(map(str, sorted(set(changed) | stale))), file=sys.stderr)
            return 1
        print("README and generated assets are up to date.")
        return 0
    for path in changed:
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_text(artifacts[path], encoding="utf-8")
        temporary.replace(target)
    for path in stale:
        (root / path).unlink()
    print(f"Updated {len(changed)} files; removed {len(stale)} obsolete generated SVGs.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
