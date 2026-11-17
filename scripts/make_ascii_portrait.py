#!/usr/bin/env python3
"""
make_ascii_portrait.py — convert the processed portrait to an animated SVG.

Reads:
  assets/portrait/portrait-processed.png
  assets/portrait/mask-preview.png
  assets/portrait/eye_midpoint.json

Outputs:
  assets/portrait/ascii-portrait.svg          (self-contained animated SVG)
  assets/portrait/portrait-fragment.svgfrag  (<g id="ascii-portrait"> only)

STATIC=1 → no animation, final frame only.
"""

import json
import math
import os
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
PORT_DIR = ROOT / "assets" / "portrait"
STATIC = os.environ.get("STATIC") == "1"

# ── Load inputs ─────────────────────────────────────────────────────────────
proc_img = Image.open(PORT_DIR / "portrait-processed.png").convert("L")
mask_img = Image.open(PORT_DIR / "mask-preview.png").convert("L")
with open(PORT_DIR / "eye_midpoint.json") as f:
    eye_data = json.load(f)

orig_w, orig_h = proc_img.size
print(f"Loaded processed image: {orig_w} × {orig_h}")

# ── Grid parameters ──────────────────────────────────────────────────────────
COLS = 150
ROWS = round(orig_h / orig_w * COLS * 0.5)
print(f"Grid: {COLS} cols × {ROWS} rows")

# Resize both images to grid size
small = proc_img.resize((COLS, ROWS), Image.LANCZOS)
small_mask = mask_img.resize((COLS, ROWS), Image.LANCZOS)

pix = small.load()
mpix = small_mask.load()

# ── Character ramp ──────────────────────────────────────────────────────────
RAMP = "@%#&WM8B0QOoc:;,. "   # index 0 = darkest, index 17 = lightest (space)
assert len(RAMP) == 18, f"Ramp length should be 18, got {len(RAMP)}"

# ── Eye midpoint in grid coordinates ────────────────────────────────────────
ex_grid = eye_data["x"] / orig_w * COLS
ey_grid = eye_data["y"] / orig_h * ROWS

left_eye_grid = (
    eye_data["left_eye"][0] / orig_w * COLS,
    eye_data["left_eye"][1] / orig_h * ROWS,
)
right_eye_grid = (
    eye_data["right_eye"][0] / orig_w * COLS,
    eye_data["right_eye"][1] / orig_h * ROWS,
)

# ── Cell and SVG dimensions ──────────────────────────────────────────────────
CELL_W = 7.5
CELL_H = CELL_W * 2        # 15.0
FONT_SIZE = CELL_H * 0.95  # 14.25
SVG_W = COLS * CELL_W      # 1125.0
SVG_H = ROWS * CELL_H      # 1500.0

ex_svg = ex_grid * CELL_W
ey_svg = ey_grid * CELL_H

print(f"SVG size: {SVG_W:.0f} × {SVG_H:.0f}")
print(f"Eye midpoint (grid): ({ex_grid:.1f}, {ey_grid:.1f})")
print(f"Eye midpoint (SVG px): ({ex_svg:.1f}, {ey_svg:.1f})")

# ── Local contrast helper ───────────────────────────────────────────────────
def local_avg(px_obj, col, row, radius=2):
    total = 0
    count = 0
    for dc in range(-radius, radius + 1):
        for dr in range(-radius, radius + 1):
            nc, nr = col + dc, row + dr
            if 0 <= nc < COLS and 0 <= nr < ROWS:
                total += px_obj[nc, nr]
                count += 1
    return total / count if count else 128

# ── Build character grid ────────────────────────────────────────────────────
chars = []
for row in range(ROWS):
    row_chars = []
    for col in range(COLS):
        v = pix[col, row]
        is_fg = mpix[col, row] > 128

        if not is_fg:
            row_chars.append(' ')
            continue

        # Local contrast boost: 5x5 neighbourhood
        avg = local_avg(pix, col, row, radius=2)
        contrast_v = v + 0.4 * (v - avg)
        contrast_v = max(0, min(255, contrast_v))

        # Gamma darkening (0.75) to bring out midtones
        v_gamma = 255 * ((contrast_v / 255) ** 0.75)

        # Map to ramp index
        idx = int(v_gamma / 256 * 18)
        idx = max(0, min(17, idx))

        # Skin protection: foreground capped at ',' (index 15) so skin never goes blank
        idx = min(idx, 15)

        row_chars.append(RAMP[idx])
    chars.append(row_chars)

# ── Assign reveal bands (Chebyshev distance from eye) ───────────────────────
MAX_RING = max(
    max(abs(col - ex_grid), abs(row - ey_grid))
    for row in range(ROWS)
    for col in range(COLS)
) + 1

bands = []
for row in range(ROWS):
    row_bands = []
    for col in range(COLS):
        ring = max(abs(col - ex_grid), abs(row - ey_grid))
        b = int(ring / MAX_RING * 23)
        b = max(0, min(23, b))

        # Special: cells within radius 3 of either eye centre go in band 0
        d_l = math.hypot(col - left_eye_grid[0], row - left_eye_grid[1])
        d_r = math.hypot(col - right_eye_grid[0], row - right_eye_grid[1])
        if d_l <= 3.0 or d_r <= 3.0:
            b = 0

        row_bands.append(b)
    bands.append(row_bands)

# ── Animation delay schedule ────────────────────────────────────────────────
def band_delay(b):
    if b == 0:
        return 0.0
    elif b <= 15:
        return 0.05 + b * 0.08
    elif b <= 22:
        return 1.3 + (b - 16) * 0.1
    else:
        return 2.0

# ── CSS style block ──────────────────────────────────────────────────────────
CSS = """
@keyframes band-reveal {
  0%   { opacity: 0; transform: scale(0.94); }
  100% { opacity: 1; transform: none; }
}
@media (prefers-reduced-motion: reduce) {
  .ab { animation: none !important; opacity: 1 !important; transform: none !important; }
}
""".strip()

# ── Gather characters per band ───────────────────────────────────────────────
band_rows = {b: {} for b in range(24)}
for row in range(ROWS):
    for col in range(COLS):
        ch = chars[row][col]
        b = bands[row][col]
        if row not in band_rows[b]:
            band_rows[b][row] = {}
        band_rows[b][row][col] = ch

def escape_xml(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def build_band_g(b, include_animation=True):
    delay = band_delay(b)
    if include_animation and not STATIC:
        style = (
            f"opacity:0; animation: band-reveal 0.35s ease-out both; "
            f"animation-delay: {delay:.2f}s; transform-box: fill-box; "
            f"transform-origin: {ex_svg:.1f}px {ey_svg:.1f}px"
        )
    else:
        style = "opacity:1"

    lines = [f'<g id="band-{b}" class="ab" style="{style}">']

    rows_in_band = band_rows.get(b, {})
    for row in sorted(rows_in_band.keys()):
        col_chars = rows_in_band[row]
        # Emit a full row where out-of-band characters are spaces
        # Only emit row if there is at least one non-space character in this band
        if not any(c != ' ' for c in col_chars.values()):
            continue
        row_str = []
        for col in range(COLS):
            row_str.append(col_chars.get(col, ' '))
        text_content = escape_xml(''.join(row_str))
        y_pos = (row + 1) * CELL_H
        lines.append(
            f'  <text x="0" y="{y_pos:.1f}" '
            f'font-family="ui-monospace,Menlo,Consolas,monospace" '
            f'font-size="{FONT_SIZE:.1f}" fill="#111111" '
            f'textLength="{SVG_W:.1f}" lengthAdjust="spacingAndGlyphs" '
            f'xml:space="preserve">{text_content}</text>'
        )
    lines.append('</g>')
    return '\n'.join(lines)

# ── Write ascii-portrait.svg ─────────────────────────────────────────────────
def write_svg(path, include_animation=True):
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {SVG_W:.1f} {SVG_H:.1f}" '
        f'width="{SVG_W:.0f}" height="{SVG_H:.0f}">',
        f'<style>{CSS}</style>',
        '<g id="ascii-portrait">',
    ]
    for b in range(23):
        lines.append(build_band_g(b, include_animation))
    lines.append('<g id="opening-slot"></g>')
    lines.append('</g>')
    lines.append('</svg>')
    content = '\n'.join(lines)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    size_kb = len(content.encode('utf-8')) / 1024
    print(f"Wrote {path} ({size_kb:.1f} KB)")
    return size_kb

# ── Write portrait-fragment.svgfrag ─────────────────────────────────────────
def write_frag(path, include_animation=True):
    lines = [
        '<style>',
        CSS,
        '</style>',
        f'<g id="ascii-portrait" transform="scale(1)" data-rows="{ROWS}" data-native-height="{SVG_H:.1f}">',
    ]
    for b in range(23):
        lines.append(build_band_g(b, include_animation))
    lines.append('<g id="opening-slot"></g>')
    lines.append('</g>')
    content = '\n'.join(lines)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    size_kb = len(content.encode('utf-8')) / 1024
    print(f"Wrote {path} ({size_kb:.1f} KB)")
    return size_kb

# ── Main ─────────────────────────────────────────────────────────────────────
if STATIC:
    write_svg(PORT_DIR / "ascii-portrait-static.svg", include_animation=False)
    write_frag(PORT_DIR / "portrait-fragment-static.svgfrag", include_animation=False)
    print("STATIC run complete.")
else:
    svg_kb = write_svg(PORT_DIR / "ascii-portrait.svg", include_animation=True)
    frag_kb = write_frag(PORT_DIR / "portrait-fragment.svgfrag", include_animation=True)

    if svg_kb > 1500:
        print(f"WARNING: ascii-portrait.svg is {svg_kb:.1f} KB (over 1.5MB)")
    if frag_kb > 1500:
        print(f"WARNING: portrait-fragment.svgfrag is {frag_kb:.1f} KB (over 1.5MB)")

print(f"\nEye midpoint in SVG coords: ({ex_svg:.1f}px, {ey_svg:.1f}px)")
print("Done.")
