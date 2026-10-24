"""Han's samurai set: brighten the red lacquer of Blades Samurai Armour's Do-maru textures to his crimson
(the black lacing / quilting is left alone). His own copies; the samurai mod's files are untouched.

Usage: recolor_han_domaru.py <in png> <out png>
"""
import sys
import numpy as np
from PIL import Image

CRIMSON = np.array([150, 34, 48.])      # a shade darker than his mask/kasa (178,44,62): lacquer reads brighter
im = np.asarray(Image.open(sys.argv[1]).convert('RGBA')).astype(np.float64)
r, g, b = im[..., 0], im[..., 1], im[..., 2]
# how "red" a pixel is: 0 for grey/black, 1 for clearly red lacquer; soft edge keeps the lacing lines crisp
redness = np.clip(((r - np.maximum(g, b)) / np.maximum(r, 1) - 0.25) / 0.25, 0, 1) * np.clip((r - 12) / 20, 0, 1)
L = im[..., :3] @ [0.299, 0.587, 0.114]
ref = np.median(L[redness > 0.9])
new = CRIMSON * np.clip(1 + 0.5 * (L / ref - 1), 0.45, 1.25)[..., None]
im[..., :3] = im[..., :3] * (1 - redness[..., None]) + np.clip(new, 0, 255) * redness[..., None]
Image.fromarray(im.astype(np.uint8), 'RGBA').save(sys.argv[2])
print('red pixels %.1f%%, reference luminance %.1f -> wrote %s' % (100 * (redness > 0.5).mean(), ref, sys.argv[2]))
