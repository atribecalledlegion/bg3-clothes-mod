"""Serana's Rinnegan. Not Hagoromo's gift: she opens it through her bond with Obito, when both of them have begun to
overcome the dark hold of their pasts (the user's lore, 2026-10-18). The ripples stay; the centre carries the bond:
  kamui  Obito's Kamui pinwheel (three curved blades from a ring around the pupil) over the inner ripples
  sun    the opposite of her Blood Eclipse Mangekyo: a radiant sun where the black eclipse was
  tomoe  Sasuke's six tomoe (the first draft)

Usage: make_rinnegan.py <eyeGoth.dds> <out dir> [kamui|sun|tomoe]

Her eyes share one texture (both eyeballs of her FaceGen eye mesh use identical UVs, checked 2026-10-18), so the
Rinnegan shows in both eyes. Painted at 4x and downsampled, then fitted to her iris exactly like the tomoe eyes and the
Mangekyo (make_eye_textures.py, make_mangekyo.py): her goth eye as the base, iris radius 80 at (256, 384) in 512.
"""
import math, os, sys
from PIL import Image, ImageDraw, ImageFilter

GOTH, OUT = sys.argv[1], sys.argv[2]
DESIGN = sys.argv[3] if len(sys.argv) > 3 else 'sun'    # the user's pick (2026-10-18); kamui kept for later
CENTER, IRIS_R, S = (256, 384), 80, 4
N = 2 * IRIS_R * S
C = N / 2
BASE, INNER, LINE = (128, 86, 182), (92, 56, 150), (14, 6, 26)    # deep purple (the pale v1 washed out in dim light)
RINGS = (0.20, 0.42, 0.64, 0.86)          # ripple radii (fraction of the iris)


def tomoe(d, cx, cy, r, angle):
    """A comma: round head, tail sweeping back along the ring (clockwise, like the Sharingan's spin)."""
    pts = []
    for k in range(13):
        t = k / 12
        a = angle - 0.55 * t                     # tail trails behind along the ring
        rr = r * (1.0 - 0.9 * t)                 # thinning
        off = 2.2 * r * t
        pts.append((cx + off * math.cos(a + math.pi / 2) + rr * math.cos(a), cy + off * math.sin(a + math.pi / 2) + rr * math.sin(a)))
    for k in range(12, -1, -1):
        t = k / 12
        a = angle - 0.55 * t
        rr = r * (1.0 - 0.9 * t)
        off = 2.2 * r * t
        pts.append((cx + off * math.cos(a + math.pi / 2) - rr * math.cos(a), cy + off * math.sin(a + math.pi / 2) - rr * math.sin(a)))
    d.polygon(pts, fill=LINE)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=LINE)


def kamui(d):
    """Obito's Kamui Mangekyo (the user's references, 2026-10-18): a black hub around an iris-coloured pupil, three
    broad wedge blades from the hub to the rim (straight leading edge, curved trailing edge), and a thin curved arc
    sweeping from each blade toward the next. Drawn over the ripples, which show through the gaps."""
    def bez(p0, p1, p2, n=24):
        return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
                 (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in (k / n for k in range(n + 1))]
    pol = lambda a, r: (C + r * C * math.cos(a), C + r * C * math.sin(a))
    for i in range(3):
        a0 = math.radians(-90 + 120 * i)
        # the blade: hub -> tip along a straight edge, tip -> hub along a curve bowing outward
        tip = pol(a0 + 0.18, 0.99)
        lead = [pol(a0 - 0.62, 0.30), tip]
        trail = bez(tip, pol(a0 + 0.80, 0.60), pol(a0 + 1.05, 0.30))
        d.polygon(lead + trail, fill=LINE)
        # the arc: leaves the blade's trailing side and sweeps on toward the next blade, thinning to a point
        outer, inner = [], []
        for k in range(31):
            t = k / 30
            a = a0 + 0.30 + 1.65 * t                  # starts inside the blade, so it grows out of it
            r = 0.71 - 0.07 * t
            w = 0.10 * (1 - t) ** 0.8 + 0.004
            outer.append(pol(a, r + w / 2)); inner.append(pol(a, r - w / 2))
        d.polygon(outer + inner[::-1], fill=LINE)
    hub = 0.34 * C
    d.ellipse((C - hub, C - hub, C + hub, C + hub), fill=LINE)
    pr = 0.15 * C                                 # the pupil, in the iris colour (red in Obito's)
    d.ellipse((C - pr, C - pr, C + pr, C + pr), fill=BASE)


def sun(img):
    """The eclipse's opposite: a white-gold sun with a warm corona and long rays, on the ripples."""
    layer = Image.new('RGBA', (N, N), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    for i in range(12):                                       # rays, long and short alternating
        a = math.radians(-90 + 30 * i)
        L = (0.84 if i % 2 == 0 else 0.62) * C
        w = math.radians(9 if i % 2 == 0 else 6)
        ld.polygon([(C + 0.2 * C * math.cos(a - w * 2), C + 0.2 * C * math.sin(a - w * 2)),
                    (C + L * math.cos(a), C + L * math.sin(a)),
                    (C + 0.2 * C * math.cos(a + w * 2), C + 0.2 * C * math.sin(a + w * 2))], fill=(255, 196, 70, 255))
    layer = layer.filter(ImageFilter.GaussianBlur(0.012 * C))
    img = Image.alpha_composite(img, layer)
    for rad, col, blur in ((0.50, (255, 150, 30, 210), 0.08), (0.36, (255, 205, 90, 255), 0.03)):
        g = Image.new('RGBA', (N, N), (0, 0, 0, 0))
        rr = rad * C
        ImageDraw.Draw(g).ellipse((C - rr, C - rr, C + rr, C + rr), fill=col)
        img = Image.alpha_composite(img, g.filter(ImageFilter.GaussianBlur(blur * C)))
    d = ImageDraw.Draw(img)
    rr = 0.27 * C
    d.ellipse((C - rr, C - rr, C + rr, C + rr), fill=(255, 236, 170, 255))
    pr = 0.06 * C
    d.ellipse((C - pr, C - pr, C + pr, C + pr), fill=LINE)
    return img


def paint():
    img = Image.new('RGBA', (N, N), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for r in range(int(C), 0, -2):                # soft lavender, a little deeper toward the centre
        f = r / C
        col = tuple(int(b * f + i * (1 - f)) for b, i in zip(BASE, INNER)) + (255,)
        d.ellipse((C - r, C - r, C + r, C + r), fill=col)
    w = int(0.06 * C)                             # bold ripples, readable at a distance
    for rf in RINGS:
        rr = rf * C
        d.ellipse((C - rr, C - rr, C + rr, C + rr), outline=LINE, width=w)
    if DESIGN == 'sun':
        img = sun(img)
        d = ImageDraw.Draw(img)
    else:
        pr = 0.07 * C                             # the pupil
        d.ellipse((C - pr, C - pr, C + pr, C + pr), fill=LINE)
    if DESIGN == 'kamui':
        kamui(d)
    elif DESIGN == 'tomoe':
        # six tomoe: three on the first ring, three on the second, offset by 60 degrees
        for ring, start in ((RINGS[0], -90), (RINGS[1], -30)):
            for i in range(3):
                a = math.radians(start + 120 * i)
                rr = ring * C
                tomoe(d, C + rr * math.cos(a), C + rr * math.sin(a), 0.075 * C, a)
    d.ellipse((2, 2, N - 2, N - 2), outline=LINE, width=int(0.05 * C))      # limbal ring
    return img.filter(ImageFilter.GaussianBlur(0.004 * C)).resize((2 * IRIS_R, 2 * IRIS_R), Image.LANCZOS)


SCLERA_TOP, ICON_BOX = 246, (434, 246, 512, 322)     # the eyeball area of her goth eye texture; a small box to skip
SCLERA_NEAR, SCLERA_FAR = (150, 112, 202), (112, 76, 168)


def sclera(base):
    """The canon Rinnegan colours the whole eye: purple over the white, the ripples carried on outward from the iris
    at the same spacing. A little of her eye's own shading is kept so it doesn't look flat."""
    field = Image.new('RGB', base.size)
    fp, bp = field.load(), base.convert('L').load()
    for y in range(SCLERA_TOP, base.height):
        for x in range(base.width):
            dist = math.hypot(x - CENTER[0], y - CENTER[1])
            f = min(1.0, dist / 260.0)
            shade = 0.82 + 0.18 * bp[x, y] / 255.0
            fp[x, y] = tuple(int((n + (r - n) * f) * shade) for n, r in zip(SCLERA_NEAR, SCLERA_FAR))
    d = ImageDraw.Draw(field)
    step = (RINGS[1] - RINGS[0]) * IRIS_R                  # the iris's ripple spacing, in texture pixels
    r = RINGS[-1] * IRIS_R + step
    while r < 380:
        d.ellipse((CENTER[0] - r, CENTER[1] - r, CENTER[0] + r, CENTER[1] + r), outline=LINE, width=4)
        r += step
    mask = Image.new('L', base.size, 0)
    md = ImageDraw.Draw(mask)
    md.rectangle((0, SCLERA_TOP, base.width, base.height), fill=255)
    md.rectangle(ICON_BOX, fill=0)
    rgb = base.convert('RGB')
    rgb.paste(field, (0, 0), mask.filter(ImageFilter.GaussianBlur(1.5)))
    return rgb


def main():
    base = Image.open(GOTH).convert('RGBA')
    disc = paint()
    mask = Image.new('L', disc.size, 0)
    ImageDraw.Draw(mask).ellipse((2, 2, 2 * IRIS_R - 2, 2 * IRIS_R - 2), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(2.5))
    alpha = base.getchannel('A')
    rgb = sclera(base)
    rgb.paste(disc.convert('RGB'), (CENTER[0] - IRIS_R, CENTER[1] - IRIS_R), mask)
    out = rgb.convert('RGBA'); out.putalpha(alpha)
    os.makedirs(OUT, exist_ok=True)
    out.save(os.path.join(OUT, 'rinnegan.dds'), format='DDS')
    out.crop((96, 224, 416, 512)).resize((640, 576), Image.LANCZOS).save(os.path.join(OUT, 'preview_rinnegan_%s.png' % DESIGN))
    print('wrote', os.path.join(OUT, 'rinnegan.dds'))


main()
