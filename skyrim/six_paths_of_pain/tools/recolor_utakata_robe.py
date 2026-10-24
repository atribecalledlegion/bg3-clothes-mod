"""Utakata's robe: Blades Samurai Armour's monk robe texture (kimono_monk.dds, used on the vanilla Greybeard robe
mesh) recoloured to his look: light-blue robe, dark-blue trim (hems, cuffs, collar), orange sash, black undershirt.
His own copy; the samurai mod's files are untouched.

Usage: recolor_utakata_robe.py <kimono_monk png> <out png>
Regions are UV boxes read off the 2048 texture (u, v in 0..1): the grey parts are the sash bands (front/back),
the hems and cuffs and the small undershirt triangle at the neck; everything else dark is robe cloth.
"""
import sys
import numpy as np
from PIL import Image

ROBE = np.array([92, 148, 196.])          # light blue (paler values read as white under in-game lighting)
TRIM = np.array([64, 74, 150.])           # dark blue
SASH = np.array([226, 118, 34.])          # orange
UNDER = np.array([36, 36, 40.])           # black under-kimono
SASH_BOXES = [(0.010, 0.390, 0.430, 0.455), (0.470, 0.345, 0.725, 0.440),   # (u0, v0, u1, v1): front, back band
              (0.640, 0.400, 1.000, 0.800)]                                 # the cords hanging from the knot
UNDER_BOX = (0.140, 0.075, 0.215, 0.170)

im = np.asarray(Image.open(sys.argv[1]).convert('RGBA')).astype(np.float64)
h, w = im.shape[:2]; vv, uu = np.mgrid[0:h, 0:w]; uu = uu / w; vv = vv / h
rgb = im[..., :3]; L = rgb @ [0.299, 0.587, 0.114]
def box_blur(a, r):
    for _ in range(2):
        for ax in (0, 1):
            c = np.cumsum(np.pad(a, [(r + 1, r) if i == ax else (0, 0) for i in range(2)], mode='edge'), axis=ax)
            a = (np.take(c, range(2 * r + 1, c.shape[ax]), axis=ax) - np.take(c, range(0, c.shape[ax] - 2 * r - 1), axis=ax)) / (2 * r + 1)
    return a
Ls = box_blur(L, 4)                    # classify on smoothed brightness: the cloth grain is noisy
grey = Ls > (np.median(L[L < 45]) + np.median(L[L > 90])) / 2      # the light parts: sash, trim, undershirt
def box(b): return (uu >= b[0]) & (uu <= b[2]) & (vv >= b[1]) & (vv <= b[3])
sash = grey & np.any([box(b) for b in SASH_BOXES], axis=0)
under = grey & box(UNDER_BOX)
trim = grey & ~sash & ~under
robe = ~grey
def recolour(sel, colour, k=0.7):
    # shade from a lightly smoothed luminance at reduced strength: keeps folds, drops most of the grain
    Lk = 0.5 * L + 0.5 * box_blur(L, 2)
    ref = np.median(Lk[sel]); shade = np.clip(1 + k * (Lk / max(ref, 1) - 1), 0.55, 1.3)
    rgb[sel] = np.clip(colour * shade[sel][:, None], 0, 255)
for sel, colour, k in ((robe, ROBE, 0.45), (trim, TRIM, 0.5), (sash, SASH, 0.5), (under, UNDER, 0.5)):
    recolour(sel, colour, k)
im[..., 3] = 255     # the source alpha is 0 on the cords/trim strips, which the game draws black
Image.fromarray(im.astype(np.uint8), 'RGBA').save(sys.argv[2])
print('robe %.0f%%, trim %.1f%%, sash %.1f%%, undershirt %.2f%%' % tuple(100 * m.mean() for m in (robe, trim, sash, under)))
