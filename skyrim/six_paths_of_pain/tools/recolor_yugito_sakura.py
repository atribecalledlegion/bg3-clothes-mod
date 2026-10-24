"""Recolour the Sakura outfit textures for Yugito (her own copies; Sakura's originals are untouched).

Usage: recolor_yugito_sakura.py <decoded png dir> <uv mask dir> <out png dir>
Inputs: DressPink.PNG, Pants.PNG (texconv-decoded), uvmap_*.png masks from tools/inspect/uv_masks.py.
Writes DressYugito.png and PantsYugito.png (2048x2048), encoded to BC7 afterwards with texconv.

Recolour keeps the fabric shading: new = target_colour * (luminance / median luminance of the region).
"""
import os, sys
import numpy as np
from PIL import Image, ImageFilter

src, masks, out = sys.argv[1:4]
SIZE = 2048
TOP_NAVY = np.array([58, 62, 82.])          # Yugito's dark charcoal-navy top (from the user's reference shots)
SASH_RED = np.array([175, 42, 42.])         # her red sash (the dress's black waist band)
SLEEVE_WHITE = np.array([214, 208, 196.])   # off-white, reads like her bandaged forearms
SHORTS_PURPLE = np.array([62, 54, 88.])     # dark purple-navy trousers

def load(name):
    im = Image.open(os.path.join(src, name)).convert('RGBA')
    # resize channels separately: resizing RGBA as a whole darkens colour under transparent pixels
    chans = [c.resize((SIZE, SIZE), Image.LANCZOS) for c in im.split()]
    return np.stack([np.asarray(c) for c in chans], -1).astype(np.float64)

def mask(name, grow=0):
    m = Image.open(os.path.join(masks, name)).convert('L').resize((SIZE, SIZE), Image.NEAREST)
    if grow: m = m.filter(ImageFilter.MaxFilter(2 * grow + 1))
    return np.asarray(m) > 0

def lum(rgb):
    return rgb[..., 0] * 0.299 + rgb[..., 1] * 0.587 + rgb[..., 2] * 0.114

def blur(a, r):
    # three passes of a separable box blur ~ gaussian (Pillow can't blur float images)
    a = a.astype(np.float64)
    for _ in range(3):
        for ax in (0, 1):
            c = np.cumsum(np.pad(a, [(r + 1, r) if i == ax else (0, 0) for i in range(2)], mode='edge'), axis=ax)
            a = (np.take(c, range(2 * r + 1, c.shape[ax]), axis=ax) - np.take(c, range(0, c.shape[ax] - 2 * r - 1), axis=ax)) / (2 * r + 1)
    return a

def recolour(img, sel, target, ref=None):
    rgb = img[..., :3]; L = lum(rgb)
    ref = ref if ref is not None else np.median(L[sel])
    shade = np.clip(L / max(ref, 1), 0.35, 1.8)[..., None]
    rgb[sel] = np.clip(target * shade[sel], 0, 255)
    return img

yy, xx = np.mgrid[0:SIZE, 0:SIZE] / SIZE            # UV coordinates (u = x, v = y)

# --- dress atlas ---------------------------------------------------------------------------------
dress = load('DressPink.PNG')
rgb = dress[..., :3]; L = lum(rgb); sat = rgb.max(-1) - rgb.min(-1)
top = mask('uvmap_Top_Top.png')
reddish = (rgb[..., 0] > 1.4 * rgb[..., 1]) & (rgb[..., 0] > 1.4 * rgb[..., 2]) & (rgb[..., 0] > 50)
top_sel = top | (mask('uvmap_Top_Top.png', grow=8) & reddish)      # include red padding around the islands
band = top & (xx > 0.41) & (xx < 0.80) & (yy > 0.64) & (yy < 0.75)  # black waist band -> her red sash
metal = band & (L > 90) & (sat < 35)                                 # keep the band's metal loops
# Haruno crest: light ring on the chest panel -> fill with the surrounding cloth (normalised blur)
crest = top & ((xx - 0.14) ** 2 + (yy - 0.30) ** 2 < 0.05 ** 2) & (L > np.median(L[top & reddish]) * 1.25)
crest = np.asarray(Image.fromarray(crest.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(5))) > 0
w = (top & ~crest).astype(np.float64)
for c in range(3):
    filled = blur(rgb[..., c] * w, 12) / np.maximum(blur(w, 12), 1e-3)
    rgb[..., c][crest] = filled[crest]
ref_top = np.median(lum(rgb)[top & ~band])
dress = recolour(dress, top_sel & ~band, TOP_NAVY, ref=ref_top)
dress = recolour(dress, band & ~metal, SASH_RED, ref=max(np.median(L[band & ~metal]), 20))
sleeves = mask('uvmap_Sleeve_Sleeves.png')
pinkish = (rgb[..., 0] > rgb[..., 1] + 15) & (L > 60)
dress = recolour(dress, sleeves | (mask('uvmap_Sleeve_Sleeves.png', grow=8) & pinkish), SLEEVE_WHITE)
Image.fromarray(dress.astype(np.uint8), 'RGBA').save(os.path.join(out, 'DressYugito.png'))

# --- shorts --------------------------------------------------------------------------------------
pants = load('Pants.PNG')
shorts = mask('uvmap_Shorts_Shorts.png')
prgb = pants[..., :3]; psat = prgb.max(-1) - prgb.min(-1)
white_band = shorts & (lum(prgb) > 150) & (psat < 40)                # keep the white striped band
pants = recolour(pants, shorts & ~white_band, SHORTS_PURPLE)
Image.fromarray(pants.astype(np.uint8), 'RGBA').save(os.path.join(out, 'PantsYugito.png'))

# previews (original vs recoloured)
for a, b, name in (('DressPink.PNG', dress, 'preview_dress.png'), ('Pants.PNG', pants, 'preview_pants.png')):
    prev = Image.new('RGB', (1600, 800))
    prev.paste(Image.open(os.path.join(src, a)).convert('RGB').resize((800, 800)), (0, 0))
    prev.paste(Image.fromarray(b[..., :3].astype(np.uint8)).resize((800, 800)), (800, 0))
    prev.save(os.path.join(out, name))
print('wrote DressYugito.png, PantsYugito.png and previews')
