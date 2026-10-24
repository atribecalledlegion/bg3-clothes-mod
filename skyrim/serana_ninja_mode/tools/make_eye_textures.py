"""Serana's Sharingan eye textures, fitted to her Serana DF Edit eye (2026-10-18).

Usage: make_eye_textures.py <eyeGoth.dds> <sharingan 1.dds> <sharingan 2.dds> <sharingan 3.dds> <out dir>

Her eye (SDFEyes, diffuse textures\\SDF\\Eyes\\eyeGoth.dds) uses the vanilla eye layout, but its iris is small: radius
about 80 px at (256, 384) in the 512 texture. Naruto Overhaul's 1- and 2-tomoe Sharingan are drawn with a disc of radius
about 125 (black ring included), so on her eye only the red centre showed and the tomoe sat under her eyelids. The
Uchiha Clan 3-tomoe Sharingan already has radius about 80. Each output = her goth eye (sclera, shading, alpha kept) with
the Sharingan disc scaled to her iris and blended in with a soft edge. Written as uncompressed RGBA DDS.
"""
import os, sys
from PIL import Image, ImageDraw, ImageFilter

GOTH, S1, S2, S3, OUT = sys.argv[1:6]
CENTER = (256, 384)
IRIS_R = 80          # her iris radius (512 texture)
SRC_R = {1: 125, 2: 125, 3: 82}   # Sharingan disc radius incl. the black ring, per source


def disc(src, src_r, size):
    im = Image.open(src).convert('RGBA')
    if im.size != size:
        im = im.resize(size, Image.LANCZOS)
    cx, cy = CENTER
    box = (cx - src_r, cy - src_r, cx + src_r, cy + src_r)
    d = im.crop(box).resize((2 * IRIS_R, 2 * IRIS_R), Image.LANCZOS)
    mask = Image.new('L', d.size, 0)
    ImageDraw.Draw(mask).ellipse((2, 2, 2 * IRIS_R - 2, 2 * IRIS_R - 2), fill=255)
    return d, mask.filter(ImageFilter.GaussianBlur(2.5))


def main():
    base = Image.open(GOTH).convert('RGBA')
    os.makedirs(OUT, exist_ok=True)
    for n, src in ((1, S1), (2, S2), (3, S3)):
        d, mask = disc(src, SRC_R[n], base.size)
        out = base.copy()
        alpha = out.getchannel('A')              # keep her eye's alpha (shader mask)
        rgb = out.convert('RGB')
        rgb.paste(d.convert('RGB'), (CENTER[0] - IRIS_R, CENTER[1] - IRIS_R), mask)
        out = rgb.convert('RGBA'); out.putalpha(alpha)
        path = os.path.join(OUT, 'sharingan%d.dds' % n)
        out.save(path, format='DDS')
        out.save(os.path.join(OUT, 'preview%d.png' % n))
        print('wrote', path)


main()
