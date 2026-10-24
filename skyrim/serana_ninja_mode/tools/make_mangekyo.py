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
    """Draft 2 (2026-10-18), after the user's Blood Eclipse references: the eclipse burns. A dark crimson haze at the
    rim, swirling vortex streaks spiralling inward, a fiery red-orange halo with bright filaments hugging the black
    disc. The three bat wings stay black (draft 1 is make_mangekyo_v1.py)."""
    import random
    rnd = random.Random(7)
    img = Image.new('RGBA', (N, N), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # haze: near-black crimson at the rim, deep blood red toward the centre
    for r in range(int(C), 0, -2):
        f = r / C
        col = (int(40 + 150 * (1 - f) ** 0.8), int(2 + 6 * (1 - f)), int(4 + 6 * (1 - f)), 255)
        d.ellipse((C - r, C - r, C + r, C + r), fill=col)
    # vortex streaks: thin bright-red arcs spiralling around the eclipse
    swirl = Image.new('RGBA', (N, N), (0, 0, 0, 0))
    sd = ImageDraw.Draw(swirl)
    for k in range(70):
        r0 = rnd.uniform(0.40, 0.95) * C
        a0 = rnd.uniform(0, 2 * math.pi)
        span = rnd.uniform(0.6, 1.6)
        pts = []
        for j in range(30):
            t = j / 29
            a = a0 + span * t
            r = r0 * (1 - 0.18 * t)                 # spiral inward
            pts.append((C + r * math.cos(a), C + r * math.sin(a)))
        bright = 1.0 - (r0 / C - 0.40) / 0.55       # brighter near the eclipse
        col = (int(170 + 85 * bright), int(20 + 70 * bright ** 2), int(10 + 20 * bright ** 3), int(70 + 120 * bright))
        sd.line(pts, fill=col, width=max(2, int(rnd.uniform(0.006, 0.016) * N)))
    swirl = swirl.filter(ImageFilter.GaussianBlur(0.006 * N))
    img = Image.alpha_composite(img, swirl)
    # the burning halo: a wide red bloom, then a hot orange ring, then bright yellow filaments right at the disc
    re = 0.33 * C
    for rad, width, col, blur in ((0.62, 0.30, (230, 20, 10, 150), 0.10),
                                  (0.44, 0.14, (255, 90, 30, 230), 0.035),
                                  (0.375, 0.05, (255, 210, 120, 255), 0.012)):
        layer = Image.new('RGBA', (N, N), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        rr = rad * C
        ld.ellipse((C - rr, C - rr, C + rr, C + rr), outline=col, width=int(width * C))
        layer = layer.filter(ImageFilter.GaussianBlur(blur * C))
        img = Image.alpha_composite(img, layer)
    fil = Image.new('RGBA', (N, N), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fil)
    for k in range(26):                               # crackling filaments in the halo
        a0 = rnd.uniform(0, 2 * math.pi)
        pts = [(C + (re * 1.04 + rnd.uniform(0, 0.12) * C) * math.cos(a0 + 0.04 * j + rnd.uniform(-0.02, 0.02)),
                C + (re * 1.04 + rnd.uniform(0, 0.12) * C) * math.sin(a0 + 0.04 * j + rnd.uniform(-0.02, 0.02)))
               for j in range(8)]
        fd.line(pts, fill=(255, 235, 170, 200), width=max(1, int(0.004 * N)))
    img = Image.alpha_composite(img, fil.filter(ImageFilter.GaussianBlur(0.002 * N)))
    d = ImageDraw.Draw(img)
    d.ellipse((2, 2, N - 2, N - 2), outline=(12, 0, 0, 255), width=int(0.05 * C))   # dark limbal ring
    # three bat wings (draft 1 shapes), black with a faint ember edge
    for i in range(3):
        w = wing(math.radians(-90 + 120 * i))
        d.polygon(w, fill=(6, 0, 0, 255), outline=(90, 10, 5, 255))
    # the eclipsed sun
    d.ellipse((C - re, C - re, C + re, C + re), fill=(4, 0, 0, 255))
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
