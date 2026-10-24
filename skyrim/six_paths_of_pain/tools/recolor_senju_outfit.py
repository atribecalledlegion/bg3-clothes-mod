"""Recolour the Senju outfit (The Uchiha Clan) and friends for one path (his own copies; originals untouched).

Usage: recolor_senju_outfit.py <han|roushi> <decoded png dir> <out png dir>
Recolour keeps the shading: new = colour * (luminance / median luminance), folds at the given strength.
"""
import os, sys
import numpy as np
from PIL import Image

CRIMSON = (178, 44, 62)          # same as Han's mask (tools/recolor_han_mask.py)
OLIVE = (104, 106, 76)
MAGENTA = (160, 58, 112)
PLATE_BROWN = (104, 84, 56)
PALETTES = {                     # file: (colour, shading strength)
    # Han: crimson plates, kasa and boots; olive tunic and trousers; dark lacing (white kasa drapes kept)
    'han': {
        'chest_plate.PNG': (CRIMSON, 0.8), 'plates_upper.PNG': (CRIMSON, 0.8), 'plates_lower.PNG': (CRIMSON, 0.8),
        'plates_lower_middle.PNG': (CRIMSON, 0.8),
        'shirt.PNG': (OLIVE, 0.8), 'pants.PNG': (OLIVE, 0.8),
        'boots.PNG': ((150, 38, 52), 0.7),
        'ropes.PNG': ((44, 40, 38), 0.6),
        'cap.PNG': (CRIMSON, 0.6),
    },
    # Roushi: magenta kimono top and trousers, brown armour plates, dark lacing; dark grey calf wraps on
    # Tobi's war sandals (waroutfit_bigbelt is the wrap texture there)
    'roushi': {
        'chest_plate.PNG': (PLATE_BROWN, 0.8), 'plates_upper.PNG': (PLATE_BROWN, 0.8),
        'plates_lower.PNG': (PLATE_BROWN, 0.8),
        'shirt.PNG': (MAGENTA, 0.8), 'pants.PNG': (MAGENTA, 0.8),
        'ropes.PNG': ((44, 42, 42), 0.6),
        'waroutfit_bigbelt.PNG': ((74, 76, 76), 0.7),
    },
}

who, src, out = sys.argv[1:4]
for name, (colour, k) in PALETTES[who].items():
    im = np.asarray(Image.open(os.path.join(src, name)).convert('RGBA')).astype(np.float64)
    L = im[..., :3] @ [0.299, 0.587, 0.114]
    shade = 1 + k * (L / max(np.median(L), 1) - 1)
    im[..., :3] = np.clip(np.array(colour, float) * np.clip(shade, 0.3, 1.5)[..., None], 0, 255)
    Image.fromarray(im.astype(np.uint8), 'RGBA').save(os.path.join(out, name))
    print('wrote', name)
