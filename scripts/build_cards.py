"""Build the profile README cards as SVGs, in the style of himanshunaik.dev.

Edit the DATA section below, then run:

    python3 scripts/build_cards.py

It writes assets/<card>-dark.svg and assets/<card>-light.svg.
Pillow is used to measure text so lines wrap correctly. Without it the
script falls back to an average character width, which wraps a bit early.
"""

import base64
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

# ---------------------------------------------------------------- DATA --

INTRO = {
    "greeting": "Hey there, I'm Himanshu",
    "tagline": "Backend & AI engineer · Pune, India",
    "status": "Open to backend & AI roles",
    # Each paragraph is a list of (text, highlight) runs. highlight: None, "amber", "blue"
    "bio": [
        [("I build ", None), ("AI agents", "amber"),
         (", RAG systems and the backend services they run on.", None)],
        [("For 8 months I worked at ", None), ("Upswing", "blue"),
         (", a Pune startup making AI booking assistants for hotels. First as an "
          "intern, then part-time as a backend developer. I'm now in my final "
          "year of AI & Data Science at SPPU.", None)],
    ],
}

WORK = {
    "company": "Upswing",
    "description": "Cognitive Hospitality Solutions",
    "logo": ASSETS / "upswing-112.png",
    "roles": [
        ("Jr. Backend Developer (Part-time)", "Apr – Oct 2026"),
        ("Software Developer Intern", "Feb – Apr 2026"),
    ],
    "highlights": [
        "Built a staff agent on an MCP server, then rebuilt it as a read-only RAG agent "
        "with document citations and role-based access",
        "Led 2 of the 11 live hotel PMS integrations (StayNtouch, Hop) and took "
        "StayNtouch through vendor pre-certification",
        "Shipped a versioned prompt service that hot-reloads prompts over RabbitMQ, "
        "so prompt changes no longer need a redeploy",
        "Hardened the platform with rate limits, Origin allow-lists and LLM-outage "
        "detection, and fixed RabbitMQ and MongoDB connection leaks",
    ],
    "stats": [
        ("~178×", "faster hotel availability checks"),
        ("11 s → 4 ms", "webhook credential lookup"),
        ("40+", "organizations on the 27-service platform"),
    ],
}

NOW = {
    "name": "research-pal",
    "description": "An assistant that answers questions from research papers. Building the "
                   "ingestion pipeline first: PDF in, clean typed text out, with a "
                   "Groq-backed LLM layer.",
    "steps": [
        ("Open PDFs safely", "done"),
        ("Extract text, positions, fonts", "done"),
        ("Clean up headers, hyphens, Unicode", "now"),
    ],
    "tech": "Python · PyMuPDF · Pydantic · Groq",
}

PROJECTS = [
    ("AI Feedback System", None,
     "Users get an AI reply to their review; admins get summaries and suggested actions",
     "FastAPI · PostgreSQL · Gemini"),
    ("Shared Object", "demo",
     "Co-built at an AI Tinkerers hackathon: an agent that flags when two Slack threads "
     "decide opposite things",
     "TypeScript · OpenAI SDK · PostgreSQL"),
    ("Parchi", "download",
     "A macOS app for notes, to-dos and photos that stay on your desktop. No account",
     "Swift · macOS"),
    ("Network Intrusion Detection", "live",
     "XGBoost on 2.8M network flows, served with FastAPI, Prometheus metrics and drift detection",
     "Python · ZenML · MLflow"),
    ("Waste Watch Campus", None,
     "Campus waste reports where Gemini classifies waste type and severity from photos",
     "Flask · Gemini"),
]

STACK = [
    ("Languages", ["Python", "TypeScript", "SQL", "Swift"]),
    ("AI & agents", ["LangGraph", "LangChain", "LangSmith", "MCP", "RAG", "Qdrant"]),
    ("Backend", ["FastAPI", "Flask", "gRPC", "RabbitMQ", "Airflow"]),
    ("Data", ["PostgreSQL", "MongoDB", "Redis"]),
    ("ML & MLOps", ["scikit-learn", "XGBoost", "MLflow", "ZenML", "Docker"]),
]

EDUCATION = {
    "year": "2027",
    "degree": "B.E. Artificial Intelligence & Data Science",
    "school": "Savitribai Phule Pune University",
    "dates": "Aug 2023 – May 2027",
}

CONTACT = {
    "title": "Hiring for backend or AI?",
    "text": "I'm open to internships and entry-level roles, and I take on small "
            "freelance projects.",
    "email": "himanshucnaik45@gmail.com",
}

# --------------------------------------------------------------- THEME --
# Same tokens as the site's src/index.css

THEMES = {
    "dark": {
        "surface": "#171717", "border": "#292929", "border_hover": "#3d3d3d",
        "text": "#f1eee9", "soft": "#a8a8a8", "muted": "#8a8a8a",
        "hl_blue": "rgba(96,165,250,0.22)", "hl_amber": "rgba(251,191,36,0.2)",
        "green": "#34d399",
    },
    "light": {
        "surface": "#f6f6f5", "border": "#e6e6e4", "border_hover": "#cfcfcc",
        "text": "#171717", "soft": "#525252", "muted": "#707070",
        "hl_blue": "rgba(59,130,246,0.16)", "hl_amber": "rgba(245,158,11,0.2)",
        "green": "#10b981",
    },
}

SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
MONO = "'Geist Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

W = 840          # card width; GitHub shrinks it on narrow screens
PAD = 22         # card padding
RADIUS = 16
SAFETY = 0.93    # wrap a little early, other systems' fonts run wider

# ---------------------------------------------------------- MEASURING --

try:
    from PIL import ImageFont

    _SANS = "/System/Library/Fonts/SFNS.ttf"
    _MONO = "/System/Library/Fonts/SFNSMono.ttf"
    _cache = {}

    def _font(size, mono, weight):
        key = (size, mono, weight)
        if key not in _cache:
            font = ImageFont.truetype(_MONO if mono else _SANS, size * 4)
            if not mono:
                # Browsers set SF's optical size to the font size; Pillow defaults
                # to 28, which measures ~12% narrow at body sizes.
                axis = {"Width": 100, "Optical Size": max(17, min(96, size)),
                        "GRAD": 400, "Weight": weight}
                font.set_variation_by_axes([
                    axis.get(a["name"].decode() if isinstance(a["name"], bytes) else a["name"],
                             a["default"])
                    for a in font.get_variation_axes()])
            _cache[key] = font
        return _cache[key]

    def text_width(text, size, mono=False, bold=False):
        return _font(size, mono, 600 if bold else 400).getlength(text) / 4
except Exception:  # no Pillow or no font file
    def text_width(text, size, mono=False, bold=False):
        per = 0.6 if mono else 0.53
        return len(text) * size * per * (1.06 if bold else 1.0)


def wrap(text, size, width, mono=False, bold=False):
    words, lines, line = text.split(" "), [], ""
    for word in words:
        trial = f"{line} {word}".strip()
        if line and text_width(trial, size, mono, bold) > width * SAFETY:
            lines.append(line)
            line = word
        else:
            line = trial
    if line:
        lines.append(line)
    return lines


# ------------------------------------------------------------ SVG BITS --

def svg(width, height, body, title):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">\n'
        f'<title>{escape(title)}</title>\n'
        "<style>@keyframes pulse{0%,100%{opacity:1}50%{opacity:.35}}"
        ".pulse{animation:pulse 1.6s ease-in-out infinite}</style>\n"
        f"{body}</svg>\n"
    )


def card(x, y, w, h, t):
    return (f'<rect x="{x + .5}" y="{y + .5}" width="{w - 1}" height="{h - 1}" rx="{RADIUS}" '
            f'fill="{t["surface"]}" stroke="{t["border"]}"/>\n')


def text(x, y, s, size, fill, weight=400, mono=False, anchor="start"):
    fam = MONO if mono else SANS
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{escape(fam)}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{escape(s)}</text>\n')


def pill(x, y, label, t, size=13, dot=None, strong=False, mono=False, pad=10, h=26):
    """Rounded tag. Returns (svg, width). y is the top edge."""
    tw = text_width(label, size, mono)
    dot_w = 14 if dot else 0
    w = tw + pad * 2 + dot_w
    out = (f'<rect x="{x + .5}" y="{y + .5}" width="{w - 1:.1f}" height="{h - 1}" '
           f'rx="{h / 2}" fill="none" stroke="{t["border_hover"] if strong else t["border"]}"/>\n')
    if dot:
        cls = ' class="pulse"' if dot == "pulse" else ""
        color = t["green"] if dot in ("green", "pulse") else t["muted"]
        out += f'<circle{cls} cx="{x + pad + 3.5}" cy="{y + h / 2}" r="3.5" fill="{color}"/>\n'
    out += text(x + pad + dot_w, y + h / 2 + size * 0.36, label, size,
                t["text"] if strong else t["soft"], mono=mono)
    return out, w


def label(x, y, s, t):
    return text(x, y, s, 13, t["muted"])


def write(name, build, title):
    for theme, t in THEMES.items():
        body, height = build(t)
        (ASSETS / f"{name}-{theme}.svg").write_text(svg(W, height, body, title), encoding="utf-8")


# --------------------------------------------------------------- CARDS --

def build_intro(t):
    # No card: on the site the intro sits on the page background
    x, y, out = 2, 26, ""
    out += text(x, y, INTRO["greeting"], 20, t["text"], 600)
    y += 26
    out += text(x, y, INTRO["tagline"], 15, t["muted"])
    y += 18
    p, _ = pill(x, y, INTRO["status"], t, dot="pulse", strong=True)
    out += p
    y += 26 + 30

    size, lh, maxw = 16, 27, 700
    for para in INTRO["bio"]:
        # word-level runs so highlights survive wrapping
        # glue=True means a space comes before this word
        tokens, space_pending = [], False
        for chunk, hl in para:
            for i, word in enumerate(chunk.split(" ")):
                if i > 0:
                    space_pending = True
                if word == "":
                    continue
                tokens.append([word, hl, space_pending])
                space_pending = False
        lines, line, width = [], [], 0.0
        space = text_width(" ", size)
        for word, hl, glue in tokens:
            add = text_width(word, size) + (space if line and glue else 0)
            if line and width + add > maxw * SAFETY:
                lines.append(line)
                line, width = [], 0.0
                add = text_width(word, size)
            line.append((word, hl, glue))
            width += add
        lines.append(line)

        for ln in lines:
            cx = x
            # merge neighbours with the same highlight; spaces stay outside highlights
            runs = []
            for i, (word, hl, glue) in enumerate(ln):
                sep = " " if (i > 0 and glue) else ""
                if runs and runs[-1][1] == hl:
                    runs[-1][0] += sep + word
                elif hl is None:
                    runs.append([sep + word, None])
                else:
                    if sep and runs:
                        runs[-1][0] += sep
                    runs.append([word, hl])
            for run, hl in runs:
                rw = text_width(run, size)
                if hl:
                    out += (f'<rect x="{cx - 3:.1f}" y="{y - size + 1:.1f}" width="{rw + 6:.1f}" '
                            f'height="{size + 7}" rx="4" fill="{t["hl_" + hl]}"/>\n')
                    out += text(cx, y, run, size, t["text"])
                else:
                    out += f'<text x="{cx:.1f}" y="{y:.1f}" font-family="{escape(SANS)}" ' \
                           f'font-size="{size}" fill="{t["soft"]}" xml:space="preserve">' \
                           f'{escape(run)}</text>\n'
                cx += rw
            y += lh
        y += 10
    return out, int(y)


def build_work(t):
    x0, y = PAD, PAD + 13
    inner = W - PAD * 2
    out = label(x0, y, "Work", t)
    y += 22

    logo = base64.b64encode(WORK["logo"].read_bytes()).decode()
    out += (f'<clipPath id="lg"><rect x="{x0}" y="{y}" width="56" height="56" rx="10"/></clipPath>'
            f'<rect x="{x0}" y="{y}" width="56" height="56" rx="10" fill="#fff"/>'
            f'<image href="data:image/png;base64,{logo}" x="{x0}" y="{y}" width="56" height="56" '
            f'clip-path="url(#lg)"/>\n')
    tx = x0 + 56 + 16
    head = WORK["company"] + " ↗"
    out += text(tx, y + 15, head, 16, t["text"], 600)
    out += text(tx + text_width(head, 16, bold=True) + 4, y + 15,
                "· " + WORK["description"], 16, t["muted"])
    ry = y + 40
    for title, dates in WORK["roles"]:
        out += text(tx, ry, title, 15, t["soft"])
        out += text(W - PAD, ry, dates, 12.5, t["muted"], mono=True, anchor="end")
        ry += 24
    y = max(y + 56, ry - 10) + 26

    for h in WORK["highlights"]:
        lines = wrap(h, 15, inner - 18)
        out += f'<circle cx="{x0 + 5}" cy="{y - 5}" r="2.2" fill="{t["muted"]}"/>\n'
        for ln in lines:
            out += text(x0 + 18, y, ln, 15, t["soft"])
            y += 23
        y += 5
    y += 6

    gap, n = 10, len(WORK["stats"])
    sw = (inner - gap * (n - 1)) / n
    sh = 82
    for i, (value, desc) in enumerate(WORK["stats"]):
        sx = x0 + i * (sw + gap)
        out += (f'<rect x="{sx + .5:.1f}" y="{y + .5}" width="{sw - 1:.1f}" height="{sh - 1}" '
                f'rx="10" fill="none" stroke="{t["border_hover"]}" stroke-dasharray="3 3"/>\n')
        out += text(sx + 14, y + 32, value, 22, t["text"], 600)
        for j, ln in enumerate(wrap(desc, 13, sw - 28)):
            out += text(sx + 14, y + 55 + j * 17, ln, 13, t["muted"])
    y += sh + PAD
    return card(0, 0, W, y, t) + out, y


def build_now(t):
    x0, y = PAD, PAD + 13
    inner = W - PAD * 2
    out = label(x0, y, "Now building", t)
    y += 32
    out += text(x0, y, NOW["name"] + " ↗", 16, t["text"], 600)
    y += 28
    for ln in wrap(NOW["description"], 15, inner):
        out += text(x0, y, ln, 15, t["soft"])
        y += 23
    y += 8
    px = x0
    for step, status in NOW["steps"]:
        tw = text_width(step, 13) + 34
        if px + tw > W - PAD:
            px = x0
            y += 34
        p, w = pill(px, y, step, t, dot="green" if status == "now" else "grey",
                    strong=status == "now")
        out += p
        px += w + 8
    y += 26 + 26
    out += text(x0, y, NOW["tech"], 12.5, t["muted"], mono=True)
    y += PAD - 2
    return card(0, 0, W, y, t) + out, y


def build_projects(t):
    x0, y = PAD, PAD + 13
    inner = W - PAD * 2
    out = label(x0, y, "Projects", t)
    y += 34
    for i, (name, badge, desc, tech) in enumerate(PROJECTS):
        head = name + " ↗"
        out += text(x0, y, head, 16, t["text"], 600)
        if badge:
            bx = x0 + text_width(head, 16, bold=True) + 10
            p, _ = pill(bx, y - 15, badge, t, size=11.5, mono=True, pad=7, h=20)
            out += p
        y += 24
        for ln in wrap(desc, 15, inner):
            out += text(x0, y, ln, 15, t["soft"])
            y += 22
        y += 2
        out += text(x0, y, tech, 12.5, t["muted"], mono=True)
        y += 18
        if i < len(PROJECTS) - 1:
            out += (f'<line x1="{x0}" y1="{y}" x2="{W - PAD}" y2="{y}" stroke="{t["border"]}" '
                    f'stroke-dasharray="3 3"/>\n')
            y += 30
    y += PAD - 6
    return card(0, 0, W, y, t) + out, y


def build_stack(t):
    x0, y = PAD, PAD + 13
    col = x0 + 150
    out = label(x0, y, "Stack", t)
    y += 22
    for i, (group, items) in enumerate(STACK):
        top = y
        px, py = col, y
        for item in items:
            w = text_width(item, 13) + 22
            if px + w > W - PAD:
                px, py = col, py + 34
            p, w = pill(px, py, item, t, strong=True)
            out += p
            px += w + 8
        out += text(x0, top + 17, group, 12.5, t["muted"], mono=True)
        y = py + 26 + 12
        if i < len(STACK) - 1:
            out += (f'<line x1="{x0}" y1="{y}" x2="{W - PAD}" y2="{y}" stroke="{t["border"]}" '
                    f'stroke-dasharray="3 3"/>\n')
            y += 12
    y += PAD - 12
    return card(0, 0, W, y, t) + out, y


def build_edu_contact(t):
    gap = 12
    cw = (W - gap) / 2
    h = 250
    out = card(0, 0, cw, h, t) + card(cw + gap, 0, cw, h, t)

    x, y = PAD, PAD + 13
    out += label(x, y, "Education", t)
    out += text(x, y + 58, EDUCATION["year"], 48, t["text"], 500)
    out += text(x, y + 80, "graduating", 13, t["muted"])
    yy = y + 118
    for ln in wrap(EDUCATION["degree"], 16, cw - PAD * 2, bold=True):
        out += text(x, yy, ln, 16, t["text"], 600)
        yy += 23
    out += text(x, yy + 2, EDUCATION["school"], 15, t["soft"])
    out += text(x, yy + 26, EDUCATION["dates"], 12.5, t["muted"], mono=True)

    x = cw + gap + PAD
    out += label(x, y, "Get in touch", t)
    yy = y + 72
    out += text(x, yy, CONTACT["title"], 16, t["text"], 600)
    yy += 28
    for ln in wrap(CONTACT["text"], 15, cw - PAD * 2):
        out += text(x, yy, ln, 15, t["soft"])
        yy += 23
    out += text(x, h - PAD - 4, CONTACT["email"] + " ↗", 12.5, t["text"], mono=True)
    return out, h


def main():
    plain = lambda runs: "".join(s for s, _ in runs)
    write("intro", build_intro,
          f'{INTRO["greeting"]}. {INTRO["tagline"]}. {INTRO["status"]}. '
          + " ".join(plain(p) for p in INTRO["bio"]))
    write("work", build_work,
          f'Work: {WORK["company"]}, {WORK["description"]}. '
          + " ".join(f"{a} ({b})." for a, b in WORK["roles"]) + " "
          + " ".join(h + "." for h in WORK["highlights"]) + " "
          + " ".join(f"{v} {d}." for v, d in WORK["stats"]))
    write("now", build_now, f'Now building: {NOW["name"]}. {NOW["description"]}')
    write("projects", build_projects,
          "Projects: " + " ".join(f"{n}: {d}." for n, _, d, _ in PROJECTS))
    write("stack", build_stack,
          "Stack: " + " ".join(f'{g}: {", ".join(i)}.' for g, i in STACK))
    write("edu-contact", build_edu_contact,
          f'Education: {EDUCATION["degree"]}, {EDUCATION["school"]}, graduating '
          f'{EDUCATION["year"]}. {CONTACT["title"]} {CONTACT["text"]} {CONTACT["email"]}')


if __name__ == "__main__":
    main()
