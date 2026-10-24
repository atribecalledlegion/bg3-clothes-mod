"""Recolour a colour-ramp (gradient) texture: keep its alpha, replace RGB along X with a saturated fire ramp
(dark red -> red-orange -> orange -> yellow-orange, no white). Writes an uncompressed A8R8G8B8 DDS.
usage: make_fire_ramp.py <in.dds> <out.dds>"""
import sys, struct
from PIL import Image
STOPS = [(0.0, (40, 4, 0)), (0.35, (190, 35, 0)), (0.7, (255, 110, 10)), (1.0, (255, 185, 70))]
def ramp(t):
    for (a, ca), (b, cb) in zip(STOPS, STOPS[1:]):
        if t <= b:
            k = (t - a) / (b - a); return tuple(round(x + (y - x) * k) for x, y in zip(ca, cb))
    return STOPS[-1][1]
im = Image.open(sys.argv[1]).convert("RGBA"); w, h = im.size; px = im.load()
out = bytearray()
for y in range(h):
    for x in range(w):
        r, g, b = ramp(x / (w - 1)); a = px[x, y][3]
        out += bytes((b, g, r, a))                      # A8R8G8B8 is stored B, G, R, A
hdr = struct.pack("<4sIIIIIII44x", b"DDS ", 124, 0x100F, h, w, w * 4, 0, 1)
pf = struct.pack("<II4sIIIII", 32, 0x41, b"\0\0\0\0", 32, 0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000)
caps = struct.pack("<IIIII", 0x1000, 0, 0, 0, 0)
open(sys.argv[2], "wb").write(hdr + pf + caps + bytes(out))
print(f"{sys.argv[2]}: {w}x{h}")
