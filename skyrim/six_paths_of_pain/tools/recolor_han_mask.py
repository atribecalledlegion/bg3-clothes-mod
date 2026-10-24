"""Han's mask: Wet and Cold's gray face cover recoloured to his crimson (his own copy; Wet and Cold untouched).

Usage: recolor_han_mask.py <facecover1_gray png> <out png> [r,g,b]
Keeps the cloth shading at half strength (the gray source is contrasty), so folds stay visible without clipping.
"""
import sys
import numpy as np
from PIL import Image

# crimson of his mask and kasa in the anime (was off-white 228,226,220 in the first try)
COLOUR = np.array([float(c) for c in (sys.argv[3] if len(sys.argv) > 3 else '178,44,62').split(',')])
im = np.asarray(Image.open(sys.argv[1]).convert('RGBA')).astype(np.float64)
L = im[..., :3] @ [0.299, 0.587, 0.114]
ref = np.median(L[im[..., 3] > 0]) if (im[..., 3] > 0).any() else np.median(L)
shade = 0.82 + 0.5 * (L / max(ref, 1) - 1)          # half-strength folds, centred a bit below full white
im[..., :3] = np.clip(COLOUR * np.clip(shade, 0.45, 1.08)[..., None], 0, 255)
Image.fromarray(im.astype(np.uint8), 'RGBA').save(sys.argv[2])
print('median luminance', ref, '-> wrote', sys.argv[2])
