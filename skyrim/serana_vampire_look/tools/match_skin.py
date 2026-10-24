"""Tone Serana DF Edit's body/hands diffuse to her pale face: per-channel gain (measured in game: cheek vs belly
under the same light), alpha kept. Writes PNGs for texconv. usage: match_skin.py <in.dds> <out.png> <gR> <gG> <gB>"""
import sys
from PIL import Image
src, out = sys.argv[1:3]; g = [float(x) for x in sys.argv[3:6]]
im = Image.open(src).convert('RGBA')
r, gch, b, a = im.split()
lut = lambda k: [min(255, round(i * k)) for i in range(256)]
Image.merge('RGBA', (r.point(lut(g[0])), gch.point(lut(g[1])), b.point(lut(g[2])), a)).save(out)
print('wrote', out, im.size)
