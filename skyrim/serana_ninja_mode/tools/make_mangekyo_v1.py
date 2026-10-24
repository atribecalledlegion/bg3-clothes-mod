"""Serana's Mangekyo Sharingan texture: an eclipsed sun with three bat-wing blades (user-approved design, 2026-10-18).

Usage: make_mangekyo.py <eyeGoth.dds> <out dir>

The eclipse is who she could become, or the one she fights never to be (her father's Tyranny of the Sun); the bat
wings are her Volkihar blood. Painted at 4x and downsampled, then fitted to her iris exactly like the tomoe eyes
(make_eye_textures.py): her goth eye as the base, iris radius 80 at (256, 384) in the 512 texture.
"""
import math, os, sys
from PIL import Image, ImageDraw, ImageFilter

GOTH, OUT = sys.argv[1], sys.argv[2]
CENTER, IRIS_R, S = (256, 384), 80, 4
N = 2 * IRIS_R * S            # canvas size (4x)
C = N / 2


def wing(angle):
    """One bat wing, pointing outward from the eclipse and swept with the spin. Drawn in local coordinates (u = out
    from the eclipse rim to the iris edge, 0..1; v = across) as a bat-wing silhouette: a curved leading edge out to
    the tip, then three finger points with scalloped membrane between them back to the root."""
    sil = [(0.0, 0.30), (0.25, 0.42), (0.55, 0.50), (0.80, 0.52), (1.00, 0.46)]          # leading edge -> tip
    fingers = [(1.00, 0.46), (0.86, 0.10), (0.70, -0.12), (0.46, -0.28), (0.20, -0.34), (0.0, -0.30)]
    def scallop(p, q, steps=10, depth=0.10):
        out = []
        for k in range(1, steps + 1):
            t = k / steps
            u = p[0] + (q[0] - p[0]) * t; v = p[1] + (q[1] - p[1]) * t
            # pull the middle of each span inward (toward the root and the leading edge): a membrane between bones
            sag = depth * math.sin(math.pi * t)
            out.append((max(0.0, u - sag * 0.8), v + sag))
        return out
    pts = list(sil)
    for i in range(len(fingers) - 1):
        pts += scallop(fingers[i], fingers[i + 1])
    root_r, tip_r = 0.29 * N / 2, 0.95 * N / 2
    res = []
    for u, v in pts:
        r = root_r + (tip_r - root_r) * u
        a = angle + v * 0.75 + 0.85 * u ** 1.3          # width across the wing + the spin
        res.append((C + r * math.cos(a), C + r * math.sin(a)))
    return res


def paint():
    img = Image.new('RGBA', (N, N), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # iris: deep crimson, darker at the rim
    for r in range(int(C), 0, -2):
        f = r / C
        col = (int(150 + 80 * (1 - f)), int(8 + 10 * (1 - f)), int(10 + 8 * (1 - f)), 255)
        d.ellipse((C - r, C - r, C + r, C + r), fill=col)
    d.ellipse((2, 2, N - 2, N - 2), outline=(10, 0, 0, 255), width=int(0.05 * N / 2))   # dark limbal ring
    # corona: a pale, burning ring just outside the eclipse
    corona = Image.new('RGBA', (N, N), (0, 0, 0, 0))
    cd = ImageDraw.Draw(corona)
    rc = 0.36 * N / 2
    cd.ellipse((C - rc, C - rc, C + rc, C + rc), outline=(255, 190, 150, 255), width=int(0.035 * N / 2))
    corona = corona.filter(ImageFilter.GaussianBlur(0.02 * N / 2))
    img = Image.alpha_composite(img, corona)
    d = ImageDraw.Draw(img)
    # three bat-wing blades
    for i in range(3):
        d.polygon(wing(math.radians(-90 + 120 * i)), fill=(8, 0, 0, 255))
    # the eclipsed sun: a black disc, with the pupil a touch darker
    re = 0.31 * N / 2
    d.ellipse((C - re, C - re, C + re, C + re), fill=(6, 0, 0, 255))
    return img.resize((2 * IRIS_R, 2 * IRIS_R), Image.LANCZOS)


def main():
    base = Image.open(GOTH).convert('RGBA')
    disc = paint()
    mask = Image.new('L', disc.size, 0)
    ImageDraw.Draw(mask).ellipse((2, 2, 2 * IRIS_R - 2, 2 * IRIS_R - 2), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(2.5))
    alpha = base.getchannel('A')
    rgb = base.convert('RGB')
    rgb.paste(disc.convert('RGB'), (CENTER[0] - IRIS_R, CENTER[1] - IRIS_R), mask)
    out = rgb.convert('RGBA'); out.putalpha(alpha)
    os.makedirs(OUT, exist_ok=True)
    out.save(os.path.join(OUT, 'mangekyo.dds'), format='DDS')
    big = paint().resize((480, 480), Image.LANCZOS) if False else None
    out.crop((96, 224, 416, 512)).resize((640, 576), Image.LANCZOS).save(os.path.join(OUT, 'preview_mangekyo.png'))
    print('wrote', os.path.join(OUT, 'mangekyo.dds'))


main()
