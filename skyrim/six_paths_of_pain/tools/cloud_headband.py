"""Yugito's forehead protector: Sakura's black headband with the Leaf symbol on the plate replaced by Kumogakure's
cloud symbol (her own texture copy; Sakura's files untouched).

Usage: cloud_headband.py <DressAlt png> <out png>
The plate (shape 'Metal' of HeadbandBlack.nif) samples DressAlt.dds around u 0.00-0.06, v 0.75-0.84. Its UVs are
turned 90 degrees: texture up = right on the forehead, texture right = down, so the symbol is drawn upright and
rotated 90 degrees counter-clockwise before stamping.
"""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

src, out = sys.argv[1:3]
im = Image.open(src).convert('RGBA'); a = np.asarray(im).astype(np.float64)
rgb = a[..., :3]; L = rgb @ [0.299, 0.587, 0.114]
orig = rgb.copy()
X0, Y0, X1, Y1 = 8, 1590, 92, 1700                 # leaf symbol box on the plate (texture pixels)

def box_blur(x, r):
    for _ in range(3):
        for ax in (0, 1):
            c = np.cumsum(np.pad(x, [(r + 1, r) if i == ax else (0, 0) for i in range(2)], mode='edge'), axis=ax)
            x = (np.take(c, range(2 * r + 1, c.shape[ax]), axis=ax) - np.take(c, range(0, c.shape[ax] - 2 * r - 1), axis=ax)) / (2 * r + 1)
    return x

# 1. erase the leaf: its engraved lines are much darker than the plate around them -> fill from the surroundings
reg = np.zeros(L.shape, bool); reg[Y0:Y1, X0:X1] = True
local = box_blur(L, 10)
lines = reg & (L < local - 12)
lines = np.asarray(Image.fromarray(lines.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(5))) > 0
w = (~lines).astype(np.float64)
for c in range(3):
    filled = box_blur(rgb[..., c] * w, 6) / np.maximum(box_blur(w, 6), 1e-3)
    rgb[..., c][lines] = filled[lines]
line_col = np.percentile(orig[lines & (L < local - 25)], 15, axis=0)  # the original engraving's dark core

# 2. Kumogakure cloud: rounded cloud outline with two inner strokes, drawn upright at 8x then reduced
K = 8; SW, SH = 70 * K, 56 * K
g = Image.new('L', (SW, SH), 0); d = ImageDraw.Draw(g)
def cloud(dr, grow, fill):
    for cx, cy, r in ((35, 22, 15), (18, 32, 11), (52, 32, 11), (9, 42, 7), (61, 42, 7)):
        dr.ellipse([(cx - r - grow) * K, (cy - r - grow) * K, (cx + r + grow) * K, (cy + r + grow) * K], fill=fill)
    dr.rectangle([(9 - grow) * K, (34 - grow) * K, (61 + grow) * K, (49 + grow) * K], fill=fill)
cloud(d, 0, 255); cloud(d, -3.2, 0)                 # outline ring ~3 px wide
for x0, x1, y in ((14, 30, 38), (40, 56, 38), (24, 46, 29)):
    d.rounded_rectangle([x0 * K, (y - 1.4) * K, x1 * K, (y + 1.4) * K], radius=1.4 * K, fill=255)
g = g.rotate(90, expand=True).resize((56, 70), Image.LANCZOS)   # 90 deg counter-clockwise (see docstring)
m = np.asarray(g) / 255.0
ox, oy = (X0 + X1) // 2 - g.width // 2, (Y0 + Y1) // 2 - g.height // 2
sl = (slice(oy, oy + g.height), slice(ox, ox + g.width))
rgb[sl] = rgb[sl] * (1 - m[..., None]) + line_col * m[..., None]
Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA').save(out)
print('line colour', line_col, '-> wrote', out)
