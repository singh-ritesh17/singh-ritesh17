#!/usr/bin/env python3
"""Renders the animated SVG cards for the GitHub profile README into cards/.

  python scripts/render_cards.py            # animated cards (commit these)
  STATIC=1 python scripts/render_cards.py   # final frame only (for screenshots)

Optional inputs
  fonts/InstrumentSerif-Regular.ttf, InstrumentSerif-Italic.ttf, SpaceGrotesk[wght].ttf
  assets/portrait.png   -> turned into an ASCII portrait in the hero (needs Pillow)
"""
import base64, io, json, math, os, re, textwrap, datetime as dt
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "cards"
STATIC = os.environ.get("STATIC") == "1"

# ---------------------------------------------------------------- CONFIG ---
NAME = "Ritesh Singh"
USER = "singh-ritesh17"
BRAND = "#790b13"
CREAM = "#fff0dc"
PORTRAIT = Path(os.environ.get("PORTRAIT_PATH", ROOT / "assets" / "portrait.png"))
PORTRAIT_INVERT = False   # True if your photo has a dark background

REPOS = [  # name, meta line, description, flagship?
    ("AccredIQ", "WON TECHATHON 2K26", "NBA accreditation management platform for Indian engineering colleges.", True),
    ("Scholaris", "CAP-ROUND ADMISSIONS", "CAP-round admission parser that turns messy PDFs into structured, queryable data.", False),
    ("Classly", "REACT · TS · NODE · MONGODB", "Tuition management SaaS for Indian tuition centres.", False),
    ("Trace", "NEXT.JS · PRISMA · MINIO", "Collaborative project management tool for student groups.", False),
    ("MediKiosk", "SIH 2026 · RESULT PENDING", "AI-powered multimodal clinical intake kiosk for Indian hospital OPDs.", False),
    ("Tulis", "EXPENSE SPLITTING", "Splits trip expenses equally among everyone travelling.", False),
]
CORE_STACK = ["TypeScript", "JavaScript", "React", "Next.js", "Node.js", "Express", "Supabase",
              "MongoDB", "Prisma", "Docker", "Python", "HTML / CSS"]
AI_STACK = ["Gemini API", "Claude", "Cursor", "GitHub Copilot"]
TILES = [  # file, label, count, italic word, caption, style
    ("build.svg", "BUILD", len(REPOS), "projects", "built end to end: UI, backend, database and deployment.", "solid"),
    ("compete.svg", "COMPETE", 1, "win", "Techathon 2k26 winner. HackCelestial offline round. SIH 2026 pending.", "light"),
    ("edit.svg", "SIDE QUEST", "25+", "reels", "edited, including paid work for a real estate client.", "side"),
]
# ---------------------------------------------------------------------------

def _rgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
def mix(a, b, t):
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * t) for x, y in zip(_rgb(a), _rgb(b)))

DEEP = mix(BRAND, "#000000", .55)
MID = mix(BRAND, CREAM, .38)
TINT = mix(BRAND, CREAM, .62)
LINE = mix(BRAND, CREAM, .80)
SOFT = mix(CREAM, BRAND, .06)
BRIGHT = mix(BRAND, "#ff6b78", .55)   # a livelier tone of the brand colour (name shine)

SERIF = "'RS Serif','Instrument Serif',Georgia,'Times New Roman',serif"
SANS = "'RS Sans','Space Grotesk','Segoe UI',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"

ANIM_CSS = """
@keyframes rise{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}
@keyframes fade{from{opacity:0}to{opacity:1}}
@keyframes grow{from{transform:scaleY(0)}to{transform:scaleY(1)}}
@keyframes pop{0%{opacity:0;transform:scale(.3)}70%{opacity:1;transform:scale(1.15)}100%{opacity:1;transform:none}}
@keyframes flash{0%,45%{filter:brightness(.5)}100%{filter:brightness(1)}}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.25}}
@keyframes nudgeup{0%,100%{transform:none}50%{transform:translate(3px,-3px)}}
@keyframes tilein{0%{opacity:0;transform:translateY(90px) scale(.6) rotate(-9deg)}55%{opacity:1;transform:translateY(-10px) scale(1.05) rotate(2deg)}75%{transform:translateY(3px) scale(.98) rotate(-.8deg)}90%{transform:translateY(-1px) scale(1.01) rotate(.2deg)}100%{opacity:1;transform:none}}
@keyframes slidein{from{opacity:0;transform:translateX(-26px)}to{opacity:1;transform:none}}
@keyframes roll{from{transform:translateY(60px)}to{transform:none}}
@keyframes sheen{0%{transform:translateX(-260px) skewX(-20deg)}22%,100%{transform:translateX(420px) skewX(-20deg)}}
@keyframes ring{0%{opacity:.7;transform:scale(.2)}100%{opacity:0;transform:scale(2.4)}}
@keyframes shine{0%{transform:translateX(-220px)}45%,100%{transform:translateX(560px)}}
@keyframes cfr{from,to{opacity:1}}
.r{opacity:0;animation:rise .8s cubic-bezier(.2,.7,.2,1) both;transform-box:fill-box}
.f{opacity:0;animation:fade .5s ease-out both}
.g{transform-box:fill-box;transform-origin:bottom;transform:scaleY(0);animation:grow .8s cubic-bezier(.2,.7,.2,1) both}
.c{opacity:0;transform-box:fill-box;transform-origin:center;animation:pop .55s ease-out both}
.cg{opacity:0;transform-box:fill-box;transform-origin:center;animation:pop .55s ease-out both,flash .7s ease-out both}
.live{animation:pulse 1.6s ease-in-out infinite}
.nu{transform-box:fill-box;animation:nudgeup 1.8s ease-in-out infinite}
.ti{opacity:0;transform-box:fill-box;transform-origin:50% 60%;animation:tilein 1.1s cubic-bezier(.2,.8,.2,1) both}
.sl{opacity:0;transform-box:fill-box;animation:slidein .6s cubic-bezier(.2,.7,.2,1) both}
.ro{transform-box:fill-box;animation:roll .8s cubic-bezier(.15,.8,.2,1) both}
.sh{animation:sheen 5s ease-in-out infinite}
.rg{opacity:0;transform-box:fill-box;transform-origin:center;animation:ring 1s ease-out both}
.shn{animation:shine 7s ease-in-out infinite}
.cf{opacity:0;animation:cfr .061s linear}
.cf.last{animation-fill-mode:forwards}
@media (prefers-reduced-motion:reduce){
.r,.f,.g,.c,.cg,.live,.nu,.ti,.sl,.ro{animation:none!important;opacity:1!important;transform:none!important;filter:none!important}
.sh,.rg,.shn{display:none}
.cf{animation:none!important;opacity:0!important}.cf.last{opacity:1!important}}
"""

def A(cls, d):
    return "" if STATIC else f' class="{cls}" style="animation-delay:{d:.2f}s"'
def C(cls):
    return "" if STATIC else f' class="{cls}"'

# ----------------------------------------------------------------- fonts ---
FONT_FILES = [("RS Serif", "InstrumentSerif-Regular.ttf", "400", "normal"),
              ("RS Serif", "InstrumentSerif-Italic.ttf", "400", "italic"),
              ("RS Sans", "SpaceGrotesk[wght].ttf", "300 700", "normal")]

def font_css(text):
    try:
        from fontTools import subset
        from fontTools.ttLib import TTFont
    except ImportError:
        return ""
    out = ""
    for fam, fname, weight, style in FONT_FILES:
        path = ROOT / "fonts" / fname
        if not path.exists():
            continue
        try:
            opts = subset.Options(); opts.layout_features = ["*"]
            font = TTFont(path)
            sub = subset.Subsetter(opts); sub.populate(text=text + " 0123456789+·↗→"); sub.subset(font)
            buf = io.BytesIO()
            try:
                font.flavor = "woff2"; font.save(buf); fmt = "woff2"
            except Exception:
                buf = io.BytesIO(); font.flavor = "woff"; font.save(buf); fmt = "woff"
            b64 = base64.b64encode(buf.getvalue()).decode()
            out += (f"@font-face{{font-family:'{fam}';font-style:{style};font-weight:{weight};"
                    f"src:url(data:font/{fmt};base64,{b64}) format('{fmt}')}}")
        except Exception as e:
            print("font skipped:", fname, e)
    return out

def card(name, w, h, label, body, defs=""):
    text = re.sub(r"<[^>]+>", "", body + defs)
    css = font_css(text) + ("" if STATIC else ANIM_CSS)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:g} {h:g}" width="{w:g}" height="{h:g}" '
           f'role="img" aria-label="{escape(label)}"><title>{escape(label)}</title>'
           f'<style>{css}</style>{"<defs>" + defs + "</defs>" if defs else ""}{body}</svg>')
    OUT.mkdir(exist_ok=True)
    (OUT / name).write_text(svg, encoding="utf-8")
    print("wrote", name, f"{len(svg)/1024:.1f} KB")

def T(x, y, s, size, fill, font=SANS, anchor="start", ls=0, extra=""):
    return (f'<text x="{x:g}" y="{y:g}" font-family="{font}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" letter-spacing="{ls}"{extra}>{escape(s)}</text>')

# ------------------------------------------------------------ ASCII portrait ---
RAMP = " .:-=+*#%@"
def ascii_rows(path, cols=84):
    from PIL import Image, ImageOps
    im = ImageOps.autocontrast(Image.open(path).convert("L"), cutoff=2)
    if PORTRAIT_INVERT:
        im = ImageOps.invert(im)
    w, h = im.size
    rows = max(1, round(h / w * cols * 0.5))
    px = im.resize((cols, rows), Image.LANCZOS).load()
    n = len(RAMP)
    return ["".join(RAMP[min(n - 1, int((255 - px[x, y]) / 256 * n))] for x in range(cols)) for y in range(rows)]

# ----------------------------------------------------------------- hero ---
def hero():
    import re as _re
    w, h = 880, 432
    first, rest = NAME.split()[0], " ".join(NAME.split()[1:])
    b = f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="14" fill="{CREAM}" stroke="{LINE}" stroke-width="2"/>'
    b += f'<g{A("f", 0)}><rect x="48" y="49" width="8" height="8" rx="2" fill="{BRAND}"{C("live")}/>'
    b += T(66, 57, "FULL-STACK DEVELOPER  ·  PUNE", 12, MID, MONO, ls=1.4) + '</g>'
    # Both name parts BLACK #111111, Ritesh normal / Singh italic
    b += f'<g{A("r", .15)}>{T(44, 190, first, 116, "#111111", SERIF, ls=-2.5)}</g>'
    b += f'<g{A("r", .30)}>{T(44, 290, rest, 116, "#111111", SERIF, ls=-2.5, extra=" font-style=%sitalic%s" % (chr(34), chr(34)))}</g>'
    defs = ""
    if not STATIC and rest:
        # Clip path covers BOTH name lines (Ritesh y=190 normal, Singh y=290 italic)
        defs = (f'<clipPath id="nm">'
                f'<text x="44" y="190" font-family="{SERIF}" font-size="116" letter-spacing="-2.5">{escape(first)}</text>'
                f'<text x="44" y="290" font-family="{SERIF}" font-style="italic" font-size="116" letter-spacing="-2.5">{escape(rest)}</text>'
                f'</clipPath>'
                f'<linearGradient id="sg" x1="0" x2="1">'
                f'<stop offset="0" stop-color="{BRAND}" stop-opacity="0"/>'
                f'<stop offset=".5" stop-color="{BRAND}"/>'
                f'<stop offset="1" stop-color="{BRAND}" stop-opacity="0"/>'
                f'</linearGradient>')
        # Rect spans y=140..310 (height=170) covering both name lines
        b += f'<g clip-path="url(#nm)"><rect class="shn" style="animation-delay:1.6s" x="0" y="140" width="220" height="170" fill="url(#sg)"/></g>'
    b += f'<g{A("r", .55)}>{T(48, 338, "I build AI-powered products,", 18, DEEP)}{T(48, 365, "from UI to deployment. Editing is my side quest.", 18, DEEP)}</g>'
    link = f"github.com/{USER}"
    b += f'<g{A("f", .8)}>{T(48, 396, link, 13, DEEP, MONO)}'
    b += f'<g{A("nu", 0)}>{T(48 + len(link) * 7.9 + 6, 396, "↗", 13, BRAND, MONO)}</g></g>'

    # ---- portrait (right column x=510..870, y=10..422) ----
    portrait_frag_static = ROOT / "assets" / "portrait" / "portrait-fragment-static.svgfrag"
    portrait_frag_anim = ROOT / "assets" / "portrait" / "portrait-fragment.svgfrag"
    portrait_frag = portrait_frag_static if (STATIC and portrait_frag_static.exists()) else portrait_frag_anim

    if portrait_frag.exists():
        frag_text = portrait_frag.read_text(encoding="utf-8")
        m_h = _re.search(r'data-native-height="([0-9.]+)"', frag_text)
        if m_h:
            native_h = float(m_h.group(1))
        else:
            y_vals = set(_re.findall(r'y="([0-9.]+)"', frag_text))
            native_rows = len(y_vals) if y_vals else 100
            native_h = native_rows * 15.0
        native_w = 1125.0
        slot_x, slot_y, slot_w, slot_h = 510.0, 10.0, 360.0, 412.0
        scale = slot_h / native_h
        tx = max(slot_x, slot_x + (slot_w - native_w * scale) / 2.0)
        ty = slot_y
        defs += '<clipPath id="portrait-clip"><rect x="510" y="0" width="370" height="432"/></clipPath>'
        b += (f'<g clip-path="url(#portrait-clip)">'
              f'<g transform="translate({tx:.1f} {ty:.1f}) scale({scale:.4f})">'
              f'{frag_text}'
              f'</g></g>')
    else:  # decorative circles fallback until portrait fragment is generated
        b += '<!-- PORTRAIT_PLACEHOLDER: assets/portrait/portrait-fragment.svgfrag not yet generated -->'
        for i, r in enumerate([70, 130, 190, 250]):
            b += (f'<circle cx="690" cy="216" r="{r}" fill="none" stroke="{TINT}" stroke-width="1.5" '
                  f'stroke-opacity="{.7 - i * .12:.2f}"{A("f", .3 + i * .2)}/>')
        b += f'<circle cx="690" cy="216" r="40" fill="none" stroke="{BRAND}" stroke-width="2"{A("rg", 1.2)}/>'

    card("hero.svg", w, h, f"{NAME}. Full-stack developer in Pune. Video editing on the side.", b, defs)

# ----------------------------------------------------------------- tiles ---
def counter(count, word, x, y, size, fill, d0):
    """Count-up: frames flip with CSS delays; the last frame stays."""
    suffix = "+" if str(count).endswith("+") else ""
    n = int(str(count).rstrip("+"))
    word_svg = lambda v: (f'{v}{suffix} <tspan font-style="italic">{escape(word)}</tspan>')
    if STATIC:
        return f'<text x="{x}" y="{y}" font-family="{SERIF}" font-size="{size}" fill="{fill}">{word_svg(n)}</text>'
    F = 16
    vals = [round(n * (1 - (1 - i / (F - 1)) ** 3)) for i in range(F)]
    out = ""
    for i, v in enumerate(vals):
        cls = "cf last" if i == F - 1 else "cf"
        out += (f'<text class="{cls}" style="animation-delay:{d0 + i * .061:.3f}s" x="{x}" y="{y}" '
                f'font-family="{SERIF}" font-size="{size}" fill="{fill}">{word_svg(v)}</text>')
    return out

def tile(fname, label, count, word, caption, variant, d0):
    w, h = 293.333, 222
    bg, fg, sub, stroke, dash, glow = {
        "solid": (BRAND, CREAM, TINT, BRAND, "", "#ffffff"),
        "light": (CREAM, BRAND, MID, LINE, "", BRAND),
        "side": (CREAM, BRAND, MID, BRAND, ' stroke-dasharray="6 6"', BRAND),
    }[variant]
    defs = (f'<clipPath id="card"><rect width="{w}" height="{h}" rx="14"/></clipPath>'
            f'<linearGradient id="gl" x1="0" x2="1"><stop offset="0" stop-color="{glow}" stop-opacity="0"/>'
            f'<stop offset=".5" stop-color="{glow}" stop-opacity=".30"/><stop offset="1" stop-color="{glow}" stop-opacity="0"/></linearGradient>')
    b = f'<g{A("ti", d0)}>'
    b += f'<g clip-path="url(#card)"><rect width="{w}" height="{h}" fill="{bg}"/>'
    if not STATIC:
        b += (f'<circle class="rg" style="animation-delay:{d0 + .5:.2f}s" cx="{w - 40:g}" cy="170" r="60" fill="none" '
              f'stroke="{fg}" stroke-opacity=".5" stroke-width="2"/>'
              f'<rect class="sh" style="animation-delay:{d0 + 1.4:.2f}s" x="0" y="-20" width="90" height="250" fill="url(#gl)" transform="translate(-260 0)"/>')
    b += '</g>'
    if variant != "solid":
        b += f'<rect x="1" y="1" width="{w-2:g}" height="{h-2}" rx="13" fill="none" stroke="{stroke}" stroke-width="2"{dash}/>'
    b += f'<g{A("sl", d0 + .35)}>{T(24, 38, label, 12, sub, MONO, ls=1.4)}</g>'
    b += f'<g{A("nu", d0 + 1.3)}>{T(w - 38, 38, "↗", 14, fg, MONO)}</g>'
    b += f'<g clip-path="url(#slot)"><g{A("ro", d0 + .45)}>{counter(count, word, 22, 112, 44, fg, d0 + .45)}</g></g>'
    defs += f'<clipPath id="slot"><rect x="0" y="62" width="{w}" height="62"/></clipPath>'
    for i, ln in enumerate(textwrap.wrap(caption, 34)[:3]):
        b += f'<g{A("r", d0 + .75 + i * .1)}>{T(24, 150 + i * 19, ln, 14, fg)}</g>'
    b += '</g>'
    card(fname, w, h, f"{label}: {count} {word} {caption}", b, defs)

def title_card(fname, text, d0):
    w, h = 880, 72
    b = f'<g{A("r", d0)}>{T(6, 52, text, 40, BRAND, SERIF)}</g>'
    x = 30 + len(text) * 19
    b += f'<rect x="{x}" y="40" width="{w - 6 - x}" height="2" fill="{LINE}"{A("f", d0 + .2)}/>'
    card(fname, w, h, text, b)

def repo_card(slug, name, meta, desc, flagship, d0):
    w, h = 293.333, 222
    bg, fg, sub, stroke = (BRAND, CREAM, TINT, BRAND) if flagship else (CREAM, BRAND, MID, LINE)
    b = f'<g{A("ti", d0)}>'
    b += f'<rect x="1" y="1" width="{w-2:g}" height="{h-2}" rx="14" fill="{bg}" stroke="{stroke}" stroke-width="2"/>'
    b += f'<g{A("sl", d0 + .3)}>{T(22, 34, meta, 10.5, sub, MONO, ls=1.3)}</g>'
    b += f'<g{A("nu", d0 + 1.2)}>{T(w - 36, 34, "↗", 14, fg, MONO)}</g>'
    b += f'<g{A("r", d0 + .4)}>{T(22, 88, name, 38, fg, SERIF, ls=-.5)}</g>'
    for i, ln in enumerate(textwrap.wrap(desc, 34)[:4]):
        b += f'<g{A("r", d0 + .6 + i * .08)}>{T(22, 122 + i * 19, ln, 14, fg)}</g>'
    b += f'<rect x="22" y="{h - 24}" width="36" height="3" rx="1.5" fill="{sub}"/></g>'
    card(f"repo-{slug}.svg", w, h, f"{name}: {desc}", b)

# ----------------------------------------------------------------- stack ---
def chips(items, x0, y0, maxx, fill, stroke, tc, d0):
    x, y, out = x0, y0, []
    for i, it in enumerate(items):
        wd = int(len(it) * 9.4 + 34)
        if x + wd > maxx:
            x = x0; y += 48
        out.append(f'<g{A("r", d0 + i * .05)}><rect x="{x}" y="{y}" width="{wd}" height="36" rx="18" fill="{fill}" '
                   f'stroke="{stroke}" stroke-width="1.5"/>{T(x + wd / 2, y + 23.5, it, 16, tc, anchor="middle")}</g>')
        x += wd + 10
    return "".join(out), y + 36

def stack_card(d0):
    w = 880
    b1, y1 = chips(CORE_STACK, 32, 62, w - 32, CREAM, MID, BRAND, d0 + .2)
    ya = y1 + 34
    b2, y2 = chips(AI_STACK, 32, ya + 18, w - 32, BRAND, BRAND, CREAM, d0 + .7)
    h = y2 + 30
    b = f'<rect x="1" y="1" width="{w-2}" height="{h-2:g}" rx="14" fill="{SOFT}" stroke="{LINE}" stroke-width="2"/>'
    b += f'<g{A("sl", d0)}>{T(32, 40, "STACK", 12, MID, MONO, ls=2.5)}</g>' + f'<g{A("sl", d0 + .5)}>{T(32, ya + 6, "BUILDING WITH AI", 12, MID, MONO, ls=2.5)}</g>' + b1 + b2
    card("stack.svg", w, h, "Tech stack: " + ", ".join(CORE_STACK + AI_STACK), b)

# ------------------------------------------------------- contribution data ---
def load_days():
    p = ROOT / "data" / "contributions.json"
    today = dt.date.today()
    if p.exists():
        data = json.loads(p.read_text())
        days = sorted((dt.date.fromisoformat(d["date"]), int(d["count"])) for d in data["days"])
        if days:
            return days, True
    return [(today - dt.timedelta(days=364 - i), 0) for i in range(365)], False

def streaks(days):
    longest = run = 0
    for _, c in days:
        run = run + 1 if c > 0 else 0
        longest = max(longest, run)
    cur = 0
    seq = days[:-1] if days and days[-1][1] == 0 else days
    for _, c in reversed(seq):
        if c > 0: cur += 1
        else: break
    return cur, longest

def heatmap(days, real, d0):
    w, left, top = 880, 40, 76
    off = (days[0][0].weekday() + 1) % 7
    cols = (len(days) + off + 6) // 7
    pitch = min(15.5, (w - left - 24) / cols); cell = pitch - 3
    h = top + 7 * pitch + 66
    levels = [mix(CREAM, BRAND, t) for t in (.10, .32, .55, .78, 1.0)]
    lv = lambda c: 0 if c == 0 else 1 if c <= 2 else 2 if c <= 5 else 3 if c <= 9 else 4
    total = sum(c for _, c in days)
    b = f'<rect x="1" y="1" width="{w-2}" height="{h-2:g}" rx="14" fill="{CREAM}" stroke="{LINE}" stroke-width="2"/>'
    last_m, last_x = None, -99
    for c in range(cols):
        d = days[0][0] + dt.timedelta(days=c * 7 - off)
        if d.month != last_m:
            x = left + c * pitch
            if x - last_x >= 42:
                b += T(x, 52, d.strftime("%b"), 12, MID, MONO); last_x = x
            last_m = d.month
    for r, lab in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        b += T(10, top + r * pitch + cell - 1, lab, 11, MID, MONO)
    for i, (d, c) in enumerate(days):
        col, row = (i + off) // 7, (i + off) % 7
        x, y = left + col * pitch, top + row * pitch
        cls = "cg" if c else "c"
        b += (f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell:.1f}" height="{cell:.1f}" rx="2.5" '
              f'fill="{levels[lv(c)]}"{A(cls, d0 + (col * 7 + row) * .0085)}/>')
    note = f"{total:,} contributions in the last year" if real else "fills in after the first daily refresh"
    b += f'<g{A("f", d0 + 3.3)}>{T(40, h - 22, note, 15, BRAND, SANS, extra=" font-weight=%s600%s" % (chr(34), chr(34)))}</g>'
    lx = w - 40 - 5 * 18 - 70
    b += T(lx - 8, h - 22, "Less", 12, MID, MONO, anchor="end")
    for i, col in enumerate(levels):
        b += f'<rect x="{lx + i * 18}" y="{h - 34}" width="13" height="13" rx="2.5" fill="{col}"/>'
    b += T(lx + 5 * 18 + 4, h - 22, "More", 12, MID, MONO)
    card("heatmap.svg", w, h, f"Contribution graph for {USER}: {total} contributions in the last year", b)

def activity(days, real, d0):
    w, h = 880, 300
    last = days[-1][0]; keys = []; y, m = last.year, last.month
    for _ in range(12):
        keys.append((y, m)); m -= 1
        if m == 0: m, y = 12, y - 1
    keys.reverse()
    tot = {k: 0 for k in keys}
    for d, c in days:
        if (d.year, d.month) in tot: tot[(d.year, d.month)] += c
    mx = max(tot.values()) or 1
    cur, longest = streaks(days)
    active = sum(1 for _, c in days if c > 0)
    bd = max(days, key=lambda t: t[1])
    busiest = f"{bd[0].strftime('%b')} {bd[0].day} · {bd[1]}" if bd[1] else "—"
    b = f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="14" fill="{CREAM}" stroke="{LINE}" stroke-width="2"/>'
    b += f'<g{A("r", d0)}>{T(32, 54, "Activity by month", 30, BRAND, SERIF)}</g>'
    base, bh, pitch = 252, 130, 46
    for i, k in enumerate(keys):
        v = tot[k]; ht = max(3, v / mx * bh) if v else 3
        x = 34 + i * pitch
        b += f'<rect x="{x}" y="{base - ht:.1f}" width="30" height="{ht:.1f}" rx="5" fill="{BRAND if v else LINE}"{A("g", d0 + .2 + i * .06)}/>'
        if v: b += f'<g{A("r", d0 + .6 + i * .06)}>{T(x + 15, base - ht - 7, str(v), 12, BRAND, anchor="middle")}</g>'
        b += T(x + 15, base + 20, dt.date(k[0], k[1], 1).strftime("%b"), 12, MID, MONO, anchor="middle")
    stats = [("CURRENT STREAK", f"{cur} days"), ("LONGEST STREAK", f"{longest} days"),
             ("ACTIVE DAYS", str(active)), ("BUSIEST DAY", busiest)]
    for i, (lab, val) in enumerate(stats):
        x, y = 610 + (i % 2) * 130, 106 + (i // 2) * 84
        b += f'<g{A("r", d0 + .5 + i * .12)}>{T(x, y, lab, 10.5, MID, MONO, ls=1.4)}{T(x, y + 36, val, 26, BRAND, SERIF)}</g>'
    card("activity.svg", w, h, f"Contributions per month. Current streak {cur} days, longest {longest}, {active} active days", b)

def main():
    hero()
    days, real = load_days()
    heatmap(days, real, .6)
    activity(days, real, 1.0)
    stack_card(1.4)
    for i, (f, lab, cnt, word, cap, sty) in enumerate(TILES):
        tile(f, lab, cnt, word, cap, sty, 3.0 + i * .35)
    title_card("title-building.svg", "What I'm building", 4.2)
    for i, (n, meta, desc, fl) in enumerate(REPOS):
        repo_card(n.lower(), n, meta, desc, fl, 4.4 + i * .18)

if __name__ == "__main__":
    main()
