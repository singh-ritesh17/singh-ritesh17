#!/usr/bin/env python3
"""
prep_portrait.py — prepare the portrait for ASCII conversion.

Outputs:
  assets/portrait/mask-preview.png   (white=foreground, black=background)
  assets/portrait/portrait-processed.png
  assets/portrait/eye_midpoint.json
"""

import json
import math
import os
from collections import deque
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "source" / "portrait-source.png"
OUT = ROOT / "assets" / "portrait"
OUT.mkdir(parents=True, exist_ok=True)

# ── 1. Load as grayscale ────────────────────────────────────────────────────
img = Image.open(SRC).convert("L")
orig_w, orig_h = img.size
print(f"Source image size: {orig_w} × {orig_h}")

# The prompt specifies ~960px wide cartoon face. Downscale if high-res source.
TARGET_W = 960
if orig_w > TARGET_W:
    new_h = round(orig_h * (TARGET_W / orig_w))
    img = img.resize((TARGET_W, new_h), Image.LANCZOS)
    print(f"Resized to target width: {img.size[0]} × {img.size[1]}")

W, H = img.size

# ── 2. Autocontrast ─────────────────────────────────────────────────────────
img = ImageOps.autocontrast(img, cutoff=1)

# ── 3. Unsharp mask ─────────────────────────────────────────────────────────
img = img.filter(ImageFilter.UnsharpMask(radius=1.5, percent=120, threshold=3))

# ── 4. Foreground mask ──────────────────────────────────────────────────────
pixels = img.load()

# 4a. Detect horizontal forehead cut and diagonal cut
# Scan y from 0.42*H to 0.50*H: find where the hair on the left cuts off at a straight horizontal line
forehead_y = None
for y in range(int(H * 0.42), int(H * 0.50)):
    has_hair = any(pixels[x, y] < 80 for x in range(100, 220))
    above_white = all(pixels[x, y - 5] > 240 for x in range(120, 250))
    if has_hair and above_white:
        forehead_y = y
        break

if forehead_y is None:
    forehead_y = int(H * 0.453)

left_x = 0
for x in range(W):
    if pixels[x, forehead_y] < 200:
        left_x = x
        break

right_x = W - 1
for x in range(int(W * 0.5), W):
    if pixels[x, forehead_y] < 200:
        right_x = x
        break

print(f"Forehead cut from x={left_x} to x={right_x} at y={forehead_y}")

# Diagonal cut edge points from top-left hair cut down to forehead_y:
diag_pts = []
for y in range(int(H * 0.15), forehead_y):
    for x in range(W):
        if pixels[x, y] < 240:
            diag_pts.append((x, y))
            break

print(f"Found {len(diag_pts)} diagonal edge points")

# 4b. Binary work image: 1 = potential background (>=240), 0 = foreground
binary = bytearray(W * H)
for y in range(H):
    for x in range(W):
        if pixels[x, y] >= 240:
            binary[y * W + x] = 1

# 4c. Draw barrier lines to seal the open crown cuts so skin stays foreground
# Horizontal barrier line along forehead_y
for x in range(left_x, right_x + 1):
    for dy in range(-2, 3):
        by = forehead_y + dy
        if 0 <= by < H:
            binary[by * W + x] = 0

# Diagonal barrier line along diagonal cut edge points
for x, y in diag_pts:
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            nx, ny = x + dx, y + dy
            if 0 <= nx < W and 0 <= ny < H:
                binary[ny * W + nx] = 0

# 4d. Flood-fill background from all 4 borders
visited = bytearray(W * H)
q = deque()

for x in range(W):
    if binary[0 * W + x] == 1 and not visited[0 * W + x]:
        visited[0 * W + x] = 1
        q.append((x, 0))
    if binary[(H - 1) * W + x] == 1 and not visited[(H - 1) * W + x]:
        visited[(H - 1) * W + x] = 1
        q.append((x, H - 1))

for y in range(H):
    if binary[y * W + 0] == 1 and not visited[y * W + 0]:
        visited[y * W + 0] = 1
        q.append((0, y))
    if binary[y * W + (W - 1)] == 1 and not visited[y * W + (W - 1)]:
        visited[y * W + (W - 1)] = 1
        q.append((W - 1, y))

while q:
    x, y = q.popleft()
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nx, ny = x + dx, y + dy
        if 0 <= nx < W and 0 <= ny < H:
            idx = ny * W + nx
            if not visited[idx] and binary[idx] == 1:
                visited[idx] = 1
                q.append((nx, ny))

# 4e. Build mask preview: white = foreground (unreached), black = background
mask_img = Image.new("L", (W, H), 0)
mask_pix = mask_img.load()
fg_count = 0
for y in range(H):
    for x in range(W):
        if not visited[y * W + x]:
            mask_pix[x, y] = 255
            fg_count += 1

mask_img.save(OUT / "mask-preview.png")
mask_pct = fg_count / (W * H) * 100
print(f"Mask coverage: {mask_pct:.1f}% foreground")

# 4f. Save processed image
img.save(OUT / "portrait-processed.png")
print(f"Saved {OUT / 'portrait-processed.png'}")

# ── 5. Eye detection ────────────────────────────────────────────────────────
# Look for dark blobs (< 80) within foreground mask in upper-middle of face
eye_top = int(H * 0.45)
eye_bot = int(H * 0.58)
eye_left = int(W * 0.20)
eye_right = int(W * 0.75)

dark_pixels = []
for y in range(eye_top, eye_bot):
    for x in range(eye_left, eye_right):
        if mask_pix[x, y] > 128 and pixels[x, y] < 80:
            dark_pixels.append((x, y))

pset = set(dark_pixels)
visited_dp = set()
components = []

for p in dark_pixels:
    if p in visited_dp:
        continue
    comp = []
    bq = deque([p])
    visited_dp.add(p)
    while bq:
        cx, cy = bq.popleft()
        comp.append((cx, cy))
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                np = (cx + dx, cy + dy)
                if np in pset and np not in visited_dp:
                    visited_dp.add(np)
                    bq.append(np)
    components.append(comp)

components.sort(key=len, reverse=True)

def centroid(comp):
    xs = [p[0] for p in comp]
    ys = [p[1] for p in comp]
    return sum(xs) / len(xs), sum(ys) / len(ys)

if len(components) >= 2:
    c1 = centroid(components[0])
    c2 = centroid(components[1])
    if c1[0] > c2[0]:
        c1, c2 = c2, c1
    left_eye = list(c1)
    right_eye = list(c2)
    mid_x = (c1[0] + c2[0]) / 2
    mid_y = (c1[1] + c2[1]) / 2
elif len(components) == 1:
    c = centroid(components[0])
    left_eye = right_eye = list(c)
    mid_x, mid_y = c
else:
    mid_x, mid_y = W / 2, H * 0.50
    left_eye = [mid_x - W * 0.15, mid_y]
    right_eye = [mid_x + W * 0.15, mid_y]

eye_data = {
    "x": mid_x,
    "y": mid_y,
    "left_eye": left_eye,
    "right_eye": right_eye,
}

with open(OUT / "eye_midpoint.json", "w") as f:
    json.dump(eye_data, f, indent=2)

print(f"Eye midpoint: ({mid_x:.1f}, {mid_y:.1f})")
print(f"Left eye: ({left_eye[0]:.1f}, {left_eye[1]:.1f})")
print(f"Right eye: ({right_eye[0]:.1f}, {right_eye[1]:.1f})")
print("Done with prep_portrait.py")
