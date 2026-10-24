"""Close-up flat render of the Yamato's sword and scabbard shapes with an atlas: orthographic, looking along the
mesh's thinnest axis, each triangle filled with the atlas colour at its UV centroid (painter's order). For checking
which parts got which colours.

usage (from the Yamato's meshes\\Chaos2 folder): render_katana.py <atlas png> <out png> <sword nif> <scabbard nif>
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw

ATLAS, OUT = sys.argv[1], sys.argv[2]
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'yamato_uv_map.py'), encoding='utf-8').read()
ns = {}
exec(src.split('sword = read(')[0].replace('W, H = (int(x) for x in sys.argv[2].split(\'x\'))', 'W = H = 1'), ns)
tex = np.array(Image.open(ATLAS).convert('RGB'))
TH, TW = tex.shape[:2]


def draw(shapes, size=(1800, 360)):
    verts = np.vstack([v for v, u, t in shapes])
    span = verts.max(0) - verts.min(0)
    long_ax, thin_ax = int(np.argmax(span)), int(np.argmin(span))
    up_ax = 3 - long_ax - thin_ax
    lo, hi = verts.min(0), verts.max(0)
    scale = min((size[0] - 40) / span[long_ax], (size[1] - 40) / max(span[up_ax], 1e-6))
    img = Image.new('RGB', size, (236, 236, 236))
    g = ImageDraw.Draw(img)
    tris = []
    for v, u, t in shapes:
        for tri in t:
            p = v[tri]
            uv = u[tri].mean(0) % 1.0
            col = tuple(int(c) for c in tex[min(int(uv[1] * TH), TH - 1), min(int(uv[0] * TW), TW - 1)])
            xy = [(20 + (q[long_ax] - lo[long_ax]) * scale, size[1] - 20 - (q[up_ax] - lo[up_ax]) * scale) for q in p]
            tris.append((p[:, thin_ax].mean(), xy, col))
    for _, xy, col in sorted(tris, key=lambda x: x[0]):
        g.polygon(xy, fill=col)
    return img


sword = ns['read'](sys.argv[3])
scab = ns['read'](sys.argv[4])
a = draw([sword['IronLongSword01:0']])
b = draw([scab['saya'], scab['guard']])
out = Image.new('RGB', (a.width, a.height + b.height + 10), (200, 200, 200))
out.paste(a, (0, 0)); out.paste(b, (0, a.height + 10))
out.save(OUT)
print('wrote', OUT)
