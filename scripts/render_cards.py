#!/usr/bin/env python3
"""Renders the animated SVG cards for the GitHub profile README into cards/.

Usage:
  python scripts/render_cards.py            # animated cards (what you commit)
  STATIC=1 python scripts/render_cards.py   # final frame only, for screenshots

Fonts (optional but recommended): drop these into fonts/ and they get subset
and embedded as base64 per card (GitHub blocks external fonts in <img> SVGs):
  fonts/InstrumentSerif-Regular.ttf
  fonts/SpaceGrotesk[wght].ttf
"""
import base64, io, json, os, re, textwrap, datetime as dt
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

REPOS = [  # name, meta line, description, flagship?
    ("AccredIQ", "WON TECHATHON 2K26", "NBA accreditation management platform for Indian engineering colleges.", True),
    ("Scholaris", "CAP-ROUND ADMISSIONS", "CAP-round admission parser that turns messy PDFs into structured, queryable data.", False),
    ("Classly", "REACT · TYPESCRIPT · NODE · MONGODB", "Tuition management SaaS for Indian tuition centres.", False),
    ("Trace", "NEXT.JS · PRISMA · MINIO", "Collaborative project management tool for student groups.", False),
    ("MediKiosk", "SIH 2026 · RESULT PENDING", "AI-powered multimodal clinical intake kiosk for Indian hospital OPDs.", False),
    ("Tulis", "EXPENSE SPLITTING", "Splits trip expenses equally among everyone travelling.", False),
]
CORE_STACK = ["TypeScript", "JavaScript", "React", "Next.js", "Node.js", "Express", "Supabase",
              "MongoDB", "Prisma", "Docker", "Python", "HTML / CSS"]
AI_STACK = ["Gemini API", "Claude", "Cursor", "GitHub Copilot"]
# ---------------------------------------------------------------------------

def _rgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
def mix(a, b, t):
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * t) for x, y in zip(_rgb(a), _rgb(b)))

DEEP = mix(BRAND, "#000000", .62)
MID = mix(BRAND, CREAM, .30)
TINT = mix(BRAND, CREAM, .62)
LINE = mix(BRAND, CREAM, .80)
SOFT = mix(CREAM, BRAND, .06)

SERIF = "'RS Serif','Instrument Serif',Georgia,'Times New Roman',serif"
SANS = "'RS Sans','Space Grotesk','Segoe UI',Helvetica,Arial,sans-serif"

ANIM_CSS = """
@keyframes rise{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}
@keyframes grow{from{transform:scaleY(0)}to{transform:scaleY(1)}}
@keyframes pop{from{opacity:0;transform:scale(.4)}to{opacity:1;transform:none}}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
@keyframes drift{from{stroke-dashoffset:0}to{stroke-dashoffset:-120}}
.a{animation:rise .8s cubic-bezier(.2,.7,.2,1) both}
.g{transform-box:fill-box;transform-origin:50% 100%;animation:grow .9s cubic-bezier(.2,.7,.2,1) both}
.p{transform-box:fill-box;transform-origin:50% 50%;animation:pop .5s ease-out both}
.pulse{animation:pulse 2.2s ease-in-out infinite}
.drift{stroke-dasharray:6 14;animation:drift 12s linear infinite}
@media (prefers-reduced-motion:reduce){.a,.g,.p,.pulse,.drift{animation:none!important}}
"""

def A(cls, d):
    """Animation attributes (staggered delay). Empty in STATIC mode."""
    return "" if STATIC else f' class="{cls}" style="animation-delay:{d:.2f}s"'

def C(cls):
    return "" if STATIC else f' class="{cls}"'

# ----------------------------------------------------------------- fonts ---
FONT_FILES = {"RS Serif": ("InstrumentSerif-Regular.ttf", "400"),
              "RS Sans": ("SpaceGrotesk[wght].ttf", "300 700")}

def font_css(text):
    fdir = ROOT / "fonts"
    out = ""
    try:
        from fontTools import subset
        from fontTools.ttLib import TTFont
    except ImportError:
        return out
    for fam, (fname, weight) in FONT_FILES.items():
        path = fdir / fname
        if not path.exists():
            continue
        try:
            opts = subset.Options(); opts.layout_features = ["*"]
            font = TTFont(path)
            sub = subset.Subsetter(opts); sub.populate(text=text + " 0123456789"); sub.subset(font)
            buf = io.BytesIO()
            try:
                font.flavor = "woff2"; font.save(buf); fmt = "woff2"
            except Exception:
                buf = io.BytesIO(); font.flavor = "woff"; font.save(buf); fmt = "woff"
            b64 = base64.b64encode(buf.getvalue()).decode()
            out += (f"@font-face{{font-family:'{fam}';font-weight:{weight};"
                    f"src:url(data:font/{fmt};base64,{b64}) format('{fmt}')}}")
        except Exception as e:  # never break the build over a font
            print("font skipped:", fname, e)
    return out

def card(name, w, h, label, body):
    text = re.sub(r"<[^>]+>", "", body)
    css = font_css(text) + ("" if STATIC else ANIM_CSS)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
           f'role="img" aria-label="{escape(label)}"><title>{escape(label)}</title>'
           f'<style>{css}</style>{body}</svg>')
    OUT.mkdir(exist_ok=True)
    (OUT / name).write_text(svg, encoding="utf-8")
    print("wrote", name, f"{len(svg)//1024} KB")

def T(x, y, s, size, fill, font=SANS, anchor="start", ls=0):
    return (f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" letter-spacing="{ls}">{escape(s)}</text>')

# ----------------------------------------------------------------- cards ---
def hero():
    w, h = 1200, 380
    arcs = ""
    for i, (r, o) in enumerate([(90, .5), (170, .35), (250, .22), (330, .12)]):
        arcs += (f'<circle cx="1050" cy="190" r="{r}" fill="none" stroke="{TINT}" '
                 f'stroke-opacity="{o}" stroke-width="1.5"{C("drift") if i == 1 else ""}/>')
    b = (f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
         f'<stop offset="0" stop-color="{DEEP}"/><stop offset="1" stop-color="{BRAND}"/></linearGradient>'
         f'<clipPath id="c"><rect width="{w}" height="{h}" rx="28"/></clipPath></defs>'
         f'<g clip-path="url(#c)"><rect width="{w}" height="{h}" fill="url(#g)"/>{arcs}</g>')
    b += f'<g{A("a", .1)}>{T(72, 84, "FULL-STACK DEVELOPER  ·  PUNE", 18, TINT, ls=4)}</g>'
    b += f'<g{A("a", .25)}>{T(72, 190, NAME, 104, CREAM, SERIF)}</g>'
    b += f'<g{A("a", .45)}>{T(72, 250, "I build AI-powered products, from UI to deployment.", 28, CREAM)}</g>'
    b += f'<g{A("a", .6)}>{T(72, 290, "First-year CS student at SPPU. Video editing is my side quest.", 20, TINT)}</g>'
    b += (f'<g{A("a", .8)}><circle cx="78" cy="336" r="6" fill="{CREAM}"{C("pulse")}/>'
          f'{T(96, 342, "Now building: AccredIQ · Scholaris · MediKiosk", 18, CREAM)}</g>')
    card("hero.svg", w, h, f"{NAME}. Full-stack developer in Pune. Video editing on the side.", b)

def tile(fname, label, num, caption, variant, d0):
    w, h = 400, 250
    bg, fg, sub, stroke, dash = {
        "solid": (BRAND, CREAM, TINT, BRAND, ""),
        "light": (CREAM, BRAND, MID, LINE, ""),
        "side": (CREAM, BRAND, MID, BRAND, ' stroke-dasharray="7 7"'),
    }[variant]
    b = f'<rect x="1.5" y="1.5" width="{w-3}" height="{h-3}" rx="26" fill="{bg}" stroke="{stroke}" stroke-width="3"{dash}/>'
    b += f'<g{A("a", d0)}>{T(32, 52, label, 16, sub, ls=3.5)}</g>'
    b += f'<g{A("a", d0 + .12)}>{T(30, 150, num, 98, fg, SERIF)}</g>'
    for i, ln in enumerate(textwrap.wrap(caption, 33)[:3]):
        b += f'<g{A("a", d0 + .25 + i * .08)}>{T(32, 186 + i * 22, ln, 17, fg)}</g>'
    card(fname, w, h, f"{label}: {num} {caption}", b)

def title_card(fname, text):
    w, h = 1200, 84
    b = f'<g{A("a", .1)}>{T(8, 58, text, 46, BRAND, SERIF)}</g>'
    x = 40 + len(text) * 21
    b += f'<rect x="{x}" y="46" width="{w - 8 - x}" height="2" fill="{LINE}"/>'
    card(fname, w, h, text, b)

def repo_card(slug, name, meta, desc, flagship, d0):
    w, h = 400, 270
    bg, fg, sub, stroke = (BRAND, CREAM, TINT, BRAND) if flagship else (CREAM, BRAND, MID, LINE)
    b = f'<rect x="1.5" y="1.5" width="{w-3}" height="{h-3}" rx="26" fill="{bg}" stroke="{stroke}" stroke-width="3"/>'
    b += f'<g{A("a", d0)}>{T(30, 50, meta, 13.5, sub, ls=2)}</g>'
    b += f'<g{A("a", d0 + .1)}>{T(28, 112, name, 46, fg, SERIF)}</g>'
    for i, ln in enumerate(textwrap.wrap(desc, 31)[:4]):
        b += f'<g{A("a", d0 + .2 + i * .07)}>{T(30, 152 + i * 25, ln, 18, fg)}</g>'
    b += f'<rect x="30" y="{h-30}" width="48" height="4" rx="2" fill="{sub}"/>'
    card(f"repo-{slug}.svg", w, h, f"{name}: {desc}", b)

def chips(items, x0, y0, maxx, fill, stroke, tc, d0):
    x, y, out = x0, y0, []
    for i, it in enumerate(items):
        wd = int(len(it) * 11.8 + 40)
        if x + wd > maxx:
            x = x0; y += 58
        out.append(f'<g{A("a", d0 + i * .05)}><rect x="{x}" y="{y}" width="{wd}" height="44" rx="22" fill="{fill}" '
                   f'stroke="{stroke}" stroke-width="1.5"/>{T(x + wd / 2, y + 29, it, 20, tc, anchor="middle")}</g>')
        x += wd + 14
    return "".join(out), y + 44

def stack_card():
    w = 1200
    b1, y1 = chips(CORE_STACK, 44, 78, w - 44, CREAM, MID, BRAND, .2)
    ya = y1 + 52
    b2, y2 = chips(AI_STACK, 44, ya + 22, w - 44, BRAND, BRAND, CREAM, .6)
    h = y2 + 36
    b = f'<rect x="1.5" y="1.5" width="{w-3}" height="{h-3}" rx="28" fill="{SOFT}" stroke="{LINE}" stroke-width="3"/>'
    b += T(44, 50, "STACK", 16, MID, ls=4) + T(44, ya + 8, "BUILDING WITH AI", 16, MID, ls=4) + b1 + b2
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

def heatmap(days, real):
    w = 1200
    off = (days[0][0].weekday() + 1) % 7
    cols = (len(days) + off + 6) // 7
    pitch = min(20, 1060 / cols); cell = pitch - 4
    levels = [mix(CREAM, BRAND, t) for t in (.10, .30, .52, .76, 1.0)]
    def lv(c): return 0 if c == 0 else 1 if c <= 2 else 2 if c <= 5 else 3 if c <= 9 else 4
    total = sum(c for _, c in days)
    b = f'<rect x="1.5" y="1.5" width="{w-3}" height="276" rx="28" fill="{CREAM}" stroke="{LINE}" stroke-width="3"/>'
    b += f'<g{A("a", .1)}>{T(44, 66, "Contributions, last 12 months", 34, BRAND, SERIF)}</g>'
    note = f"{total} contributions" if real else "fills in after the first daily refresh"
    b += f'<g{A("a", .2)}>{T(w - 44, 64, note, 20, MID, anchor="end")}</g>'
    for i, (d, c) in enumerate(days):
        col, row = (i + off) // 7, (i + off) % 7
        x, y = 70 + col * pitch, 100 + row * pitch
        b += (f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell:.1f}" height="{cell:.1f}" rx="3.5" '
              f'fill="{levels[lv(c)]}"{A("p", .3 + col * .012)}/>')
    lx = w - 44 - 5 * 22 - 90
    b += T(lx - 12, 256, "Less", 14, MID, anchor="end")
    for i, col in enumerate(levels):
        b += f'<rect x="{lx + i * 22}" y="243" width="16" height="16" rx="3.5" fill="{col}"/>'
    b += T(lx + 5 * 22 + 6, 256, "More", 14, MID)
    card("heatmap.svg", w, 280, f"Contribution graph for {USER}, {total} contributions in the last year", b)

def activity(days, real):
    w, h = 1200, 340
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
    b = f'<rect x="1.5" y="1.5" width="{w-3}" height="{h-3}" rx="28" fill="{CREAM}" stroke="{LINE}" stroke-width="3"/>'
    b += f'<g{A("a", .1)}>{T(44, 66, "Activity by month", 34, BRAND, SERIF)}</g>'
    base, bh, pitch = 280, 150, 58
    for i, k in enumerate(keys):
        v = tot[k]; ht = max(3, v / mx * bh) if v else 3
        x = 56 + i * pitch
        b += f'<rect x="{x}" y="{base - ht:.1f}" width="38" height="{ht:.1f}" rx="6" fill="{BRAND if v else LINE}"{A("g", .3 + i * .06)}/>'
        if v: b += f'<g{A("a", .6 + i * .06)}>{T(x + 19, base - ht - 8, str(v), 14, BRAND, anchor="middle")}</g>'
        b += T(x + 19, base + 24, dt.date(k[0], k[1], 1).strftime("%b"), 14, MID, anchor="middle")
    stats = [("CURRENT STREAK", f"{cur} days"), ("LONGEST STREAK", f"{longest} days"),
             ("ACTIVE DAYS", str(active)), ("BUSIEST DAY", busiest)]
    for i, (lab, val) in enumerate(stats):
        x, y = 820 + (i % 2) * 190, 120 + (i // 2) * 100
        b += f'<g{A("a", .5 + i * .12)}>{T(x, y, lab, 13.5, MID, ls=2)}{T(x, y + 42, val, 32, BRAND, SERIF)}</g>'
    card("activity.svg", w, h, f"Contributions per month. Current streak {cur} days, longest {longest}, {active} active days", b)

def main():
    hero()
    days, real = load_days()
    heatmap(days, real); activity(days, real)
    stack_card()
    tile("build.svg", "BUILD", str(len(REPOS)), "projects built end to end: UI, backend, database and deployment.", "solid", .2)
    tile("compete.svg", "COMPETE", "1", "hackathon win at Techathon 2k26. HackCelestial offline round. SIH 2026 pending.", "light", .35)
    tile("edit.svg", "SIDE QUEST: EDIT", "25+", "reels edited, including paid work for a real estate client.", "side", .5)
    title_card("title-building.svg", "What I'm building")
    for i, (n, meta, desc, fl) in enumerate(REPOS):
        repo_card(n.lower(), n, meta, desc, fl, .3 + i * .12)

if __name__ == "__main__":
    main()
