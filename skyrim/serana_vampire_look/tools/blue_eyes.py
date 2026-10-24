"""Serana DF Edit (Goth Redux): recolour the dark-red iris of eyegoth.dds to an icy vampire blue.
The iris is found as the dark disc in the eye texture; pixels inside it get a blue ramp from their brightness
(structure kept), with a soft edge. Sclera and veins outside the disc are left alone.
usage: blue_eyes.py <eyegoth.dds> <out.png> <preview.png>"""
import sys, math
from PIL import Image
src, out, prev = sys.argv[1:4]
im = Image.open(src).convert('RGBA'); W, H = im.size; px = im.load()
# the iris: dark pixels in the lower half (the eye block); centroid + radius from their area
pts = [(x, y) for y in range(H // 2, H) for x in range(W)
       if sum(px[x, y][:3]) / 3 < 70 and px[x, y][3] > 0]
cx = sum(p[0] for p in pts) / len(pts); cy = sum(p[1] for p in pts) / len(pts)
r = math.sqrt(len(pts) / math.pi) * 1.08
print('iris centre (%.0f, %.0f) radius %.0f' % (cx, cy, r))
for y in range(int(cy - r - 4), int(cy + r + 5)):
    for x in range(int(cx - r - 4), int(cx + r + 5)):
        if not (0 <= x < W and 0 <= y < H): continue
        dd = math.hypot(x - cx, y - cy)
        if dd > r + 3: continue
        R, G, B, A = px[x, y]
        lum = (0.5 * R + 0.35 * G + 0.15 * B) / 255.0          # the red channel carries the iris detail
        t = min(1.0, 0.25 + lum * 2.2)                           # lift the dark iris so the blue reads
        nb = (int(40 * t), int(140 * t + 20), int(255 * t))      # icy blue ramp
        w = 1.0 if dd <= r - 3 else max(0.0, (r + 3 - dd) / 6.0) # soft edge
        px[x, y] = tuple(int(nb[i] * w + (R, G, B)[i] * (1 - w)) for i in range(3)) + (A,)
im.save(out)
im.convert('RGB').resize((256, 256)).save(prev)
