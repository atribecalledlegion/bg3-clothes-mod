"""Ronin Obito's kimono: the Blades Samurai "Shihanke" kimono (kimono_jin.dds: dark navy kimono, black hakama, red
belt) turned Kamui purple with the Uchiha crest on the back, like the Wandering Ronin art.

- the three diamond crests (front chest, upper back, sleeve) are painted over with plain fabric copied from nearby
- the navy kimono becomes PURPLE, keeping the fabric's own shading (each pixel's brightness relative to the
  kimono's average); hakama, belt, undershirt and seams are untouched
- a clean Uchiha crest (red fan, white lower half and handle, dark outline) is drawn, supersampled, on the middle
  of the back, only over kimono fabric (the front collar's UV island sits close to it)
Output: DXT5 2048 with the source's 12 mips (Ronin Purple FX's purple_core.write_dds), plus a PNG preview.

usage: make_ronin_kimono.py <kimono_jin.dds> <purple_core dir> <out.dds>
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw

SRC, CORE, OUT = sys.argv[1:4]
sys.path.insert(0, CORE)
from purple_core import write_dds

PURPLE = np.array([82, 44, 128], float)      # the kimono's average colour after
CRESTS = {                                   # bbox (x0, x1, y0, y1) at 2048, and where to copy plain fabric from
    'front': ((539, 622, 317, 377), (0, 250)),
    'back': ((1011, 1141, 270, 362), (-200, 0)),
    'sleeve': ((1684, 1769, 155, 221), (0, 200)),
}
BACK_CREST = (1076, 360, 200)                # centre x, y and fan diameter at 2048 (mid-back)

img = np.array(Image.open(SRC).convert('RGBA')).astype(float)
rgb = img[..., :3]

# 1. paint the crests over with fabric copied from (dx, dy) away (a few px of margin for the soft edges)
for (x0, x1, y0, y1), (dx, dy) in CRESTS.values():
    x0, y0, x1, y1 = x0 - 6, y0 - 6, x1 + 6, y1 + 6
    rgb[y0:y1, x0:x1] = rgb[y0 + dy:y1 + dy, x0 + dx:x1 + dx]

# 2. navy -> purple, shading kept
a = rgb / 255.0
mx, mn = a.max(-1), a.min(-1)
sat = (mx - mn) / np.maximum(mx, 1e-6)
d = np.maximum(mx - mn, 1e-6)
hue = np.where(mx == a[..., 2], 60 * ((a[..., 0] - a[..., 1]) / d + 4),
      np.where(mx == a[..., 1], 60 * ((a[..., 2] - a[..., 0]) / d + 2), 60 * (((a[..., 1] - a[..., 2]) / d) % 6)))
navy = (hue > 185) & (hue < 255) & (sat > 0.2) & (mx > 0.02)
lum = rgb.mean(-1)
ref = lum[navy].mean()
ratio = (lum / ref)[..., None]
rgb = np.where(navy[..., None], np.clip(PURPLE * ratio, 0, 255), rgb)
print('kimono pixels: %.1f%% of the texture, average brightness %.1f -> purple %s' % (100 * navy.mean(), ref, PURPLE.astype(int)))

# 3. the Uchiha crest, drawn 4x and scaled down
cx, cy, dia = BACK_CREST
S = 4
size = int(dia * 1.45)
layer = Image.new('RGBA', (size * S, size * S), (0, 0, 0, 0))
g = ImageDraw.Draw(layer)
c, r = size * S // 2, dia * S // 2
top = c - int(dia * S * 0.22)                  # fan centre sits above the middle so the handle fits below
ol = int(dia * S * 0.035)                      # outline
DARK, RED, WHITE = (24, 14, 30, 255), (196, 24, 32, 255), (236, 232, 226, 255)
hw = int(dia * S * 0.07)                       # handle
g.rectangle([c - hw - ol, top + r - ol, c + hw + ol, top + r + int(dia * S * 0.42) + ol], fill=DARK)
g.rectangle([c - hw, top + r - ol, c + hw, top + r + int(dia * S * 0.42)], fill=WHITE)
g.ellipse([c - r - ol, top - r - ol, c + r + ol, top + r + ol], fill=DARK)
g.ellipse([c - r, top - r, c + r, top + r], fill=WHITE)
g.pieslice([c - r, top - r, c + r, top + r], 180, 360, fill=RED)            # upper half red
g.rectangle([c - r, top - ol // 2, c + r, top + ol // 2], fill=DARK)          # the dividing line
layer = layer.resize((size, size), Image.LANCZOS)
out = Image.fromarray(np.dstack([rgb, img[..., 3]]).astype(np.uint8), 'RGBA')
crest_rgb = Image.new('RGBA', out.size, (0, 0, 0, 0))
crest_rgb.paste(layer, (cx - size // 2, cy - size // 2 + int(dia * 0.22)))
on_kimono = navy    # only on the kimono fabric (the collar's UV island is close by)
out = Image.alpha_composite(out, Image.fromarray(np.dstack([np.array(crest_rgb)[..., :3],
                            np.array(crest_rgb)[..., 3] * on_kimono]).astype(np.uint8), 'RGBA'))
out = Image.fromarray(np.dstack([np.array(out)[..., :3], img[..., 3]]).astype(np.uint8), 'RGBA')   # source alpha kept

write_dds(out, 12, 'DXT5', OUT)
out.convert('RGB').save(os.path.splitext(OUT)[0] + '_preview.png')
print('wrote', OUT)
