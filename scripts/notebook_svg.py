"""Static, readable SVG stationery for a GitHub profile; no external assets."""
from html import escape
import unicodedata

PAPER = "#fbf3e4"
INK = "#48372b"
RUST = "#a65c43"
MUTED = "#82705c"
RULE = "#ddc7a8"
FONT = "Georgia, 'DejaVu Serif', 'Times New Roman', serif"


def estimated_width(value: str, size: float) -> float:
    """Conservative proportional width; generous margins handle font fallback."""
    total = 0.0
    for char in value:
        if unicodedata.combining(char):
            continue
        if char in "MW@%&":
            total += 1.02
        elif char in "ilI.,:;!|' ":
            total += 0.36
        elif char.isupper():
            total += 0.79
        else:
            total += 0.66
    return total * size


def wrap(value: str, width: int, size: int) -> list[str]:
    lines, current = [], ""
    for word in value.split():
        candidate = f"{current} {word}".strip()
        if current and estimated_width(candidate, size) > width:
            lines.append(current)
            current = ""
        while estimated_width(word, size) > width:
            end = 1
            while end < len(word) and estimated_width(word[:end + 1], size) <= width:
                end += 1
            if current:
                lines.append(current)
                current = ""
            lines.append(word[:end])
            word = word[end:]
        current = f"{current} {word}".strip()
    if current:
        lines.append(current)
    return lines or [""]


def text(value, x, y, size=20, color=INK, *, italic=False, weight=400, anchor="start"):
    attrs = f'font-style="italic" ' if italic else ""
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" '
            f'font-weight="{weight}" text-anchor="{anchor}" {attrs}>'
            f'{escape(str(value))}</text>')


def paragraph(value, x, y, width, size=20, line_height=30, color=INK, italic=False):
    lines = wrap(value, width, size)
    return [text(line, x, y + i * line_height, size, color, italic=italic)
            for i, line in enumerate(lines)], y + len(lines) * line_height


def feather(x, y, scale=1, opacity=.15):
    return f'''<g transform="translate({x} {y}) scale({scale})" opacity="{opacity}"
      fill="none" stroke="{RUST}" stroke-width="1.5" stroke-linecap="round">
      <path d="M8 176 Q45 94 102 9 C110 54 92 96 64 116 Q45 130 29 137"/>
      <path d="M23 145 Q22 82 102 9 M27 132 L61 113 M33 116 L74 96
        M42 97 L86 77 M52 78 L94 58 M64 59 L100 37
        M30 125 L26 101 M39 104 L37 80 M49 82 L49 63 M62 62 L64 44"/>
    </g>'''


def sheet(width, height, elements, title, description="", *, ruled=True):
    rules = (f'<path d="M0 31.5 H{width}" stroke="{RULE}" stroke-opacity=".20"/>'
             if ruled else "")
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"
      viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
      <title id="title">{escape(title)}</title><desc id="desc">{escape(description or title)}</desc>
      <defs><pattern id="lines" width="{width}" height="32" patternUnits="userSpaceOnUse">{rules}</pattern></defs>
      <rect x=".5" y=".5" width="{width-1}" height="{height-1}" rx="10" fill="{PAPER}" stroke="{RULE}"/>
      <rect x="1" y="1" width="{width-2}" height="{height-2}" rx="10" fill="url(#lines)"/>
      <path d="M22 22 V{height-22}" stroke="{RUST}" stroke-opacity=".26"/>
      <g font-family="{FONT}">{''.join(elements)}</g>
    </svg>\n'''


def cover(profile, mobile=False):
    width, x = (400, 40) if mobile else (800, 48)
    elements = [text("THE NOTEBOOK OF", x, 43, 12, RUST)]
    elements.append(text(profile["name"], x, 105 if mobile else 110, 43 if mobile else 58))
    elements.append(text(profile["role"] + " · " + profile["location"], x,
                         139 if mobile else 149, 15 if mobile else 18, MUTED, italic=True))
    elements.append(text(profile["headline"], x, 195 if mobile else 205,
                         23 if mobile else 30, RUST, italic=True))
    body, end = paragraph(profile["intro"], x, 233 if mobile else 247,
                          width - 2 * x if mobile else 590, 18 if mobile else 21,
                          28 if mobile else 31)
    elements.extend(body)
    elements.append(text("@" + profile["handle"], x, end + 19, 14, MUTED, italic=True))
    if not mobile:
        elements.insert(0, feather(643, 58, 1.0, .19))
    else:
        elements.insert(0, feather(296, 178, .55, .09))
    return sheet(width, end + 43, elements, profile["name"] + " — " + profile["headline"], profile["intro"])


def focus(profile, mobile=False):
    width, x = (400, 40) if mobile else (800, 48)
    elements = [text("What I keep working on", x, 44, 23 if mobile else 29, RUST)]
    y = 84
    for label, detail in profile["focus"]:
        elements.append(text(label, x, y, 19 if mobile else 20, weight=700))
        if mobile:
            lines, y = paragraph(detail, x, y + 27, width - 2 * x, 17, 25, MUTED)
            elements.extend(lines)
            y += 19
        else:
            lines, end = paragraph(detail, 300, y, 450, 18, 27, MUTED)
            elements.extend(lines)
            y = max(y + 44, end + 12)
    return sheet(width, y + 4, elements, "Areas of work", "; ".join(a + ": " + b for a, b in profile["focus"]))


def heading(title, subtitle, mobile=False):
    width, x = (400, 40) if mobile else (800, 48)
    elements = [text(title, x, 46, 27 if mobile else 33, RUST)]
    lines, end = paragraph(subtitle, x, 79, width - x * 2, 16 if mobile else 18, 25, MUTED, True)
    elements.extend(lines)
    return sheet(width, end + 5, elements, title, subtitle, ruled=False)


def project_card(project, summary, number, mobile=False):
    width, x = (400, 40) if mobile else (800, 48)
    usable = width - x * 2
    category, end = paragraph(project["category"], x, 38, usable - 30,
                              14, 22, RUST, True)
    elements = list(category)
    elements.append(text(f"{number:02}", width - x, 39, 13, MUTED, anchor="end"))
    title, end = paragraph(project["title"], x, end + 25, usable,
                           27 if mobile else 35, 35 if mobile else 44)
    elements.extend(title)
    body, end = paragraph(summary, x, end + 4, usable, 18 if mobile else 20,
                          28 if mobile else 31, MUTED)
    elements.extend(body)
    elements.append(f'<path d="M{x} {end+5} H{width-x}" stroke="{RULE}"/>')
    note, end = paragraph(project["note"], x, end + 33, usable, 13 if mobile else 15, 22, RUST, True)
    elements.extend(note)
    return sheet(width, end + 14, elements, project["title"], summary)
