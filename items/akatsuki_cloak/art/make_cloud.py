"""Cut the Akatsuki cloud out of the reference image into a transparent PNG.

    python items/akatsuki_cloak/art/make_cloud.py

Source: textures/wallpaper2you_327472.jpeg from akatsuki-cloak-naruto-shippudden.zip,
extracted to extracted/akatsuki/cloak_texture.jpeg (local only, not committed).

The reference is a red cloud with a white outline and white swirls on pure black, so the
cut-out is exact rather than traced:
  * alpha = max(R,G,B). Over pure black, an anti-aliased edge pixel is colour x coverage,
    so the brightest channel is the coverage (red and white both have R = 255).
  * whiteness = G / alpha. Red has G ~ 0.03, white has G = 1.

The white strokes are then THICKENED. In the reference they are ~12 px on a 957 px cloud
(1.2% of its width). At the size the clouds are baked onto the cloak that is 4-5 texels,
and DXT1 stores two colours per 4x4 block: a block holding black cloth, white stroke and
red fill cannot be represented, and the stroke smears. That is the same edge bleed the
Obito crest showed until its outline was widened. Grey-scale dilation of the white
coverage keeps the anti-aliasing.

Measured colours: red #FE080B, white #FFFFFF.
"""
import os
import numpy as np
from PIL import Image

SRC = 'extracted/akatsuki/cloak_texture.jpeg'
OUT = 'items/akatsuki_cloak/art/source/akatsuki_cloud.png'
RED = np.array([0xFE, 0x08, 0x0B], np.float32) / 255
WHITE = np.array([1, 1, 1], np.float32)
STROKE_GROW = 5           # px added on each side: 12 px strokes become ~22 px
MARGIN = 16


def dilate(a, r):
    out = a.copy()
    p = np.pad(a, r)
    h, w = a.shape
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r + r:
                np.maximum(out, p[r + dy:r + dy + h, r + dx:r + dx + w], out=out)
    return out


def main():
    if not os.path.exists(SRC):
        raise SystemExit('%s missing: extract textures/wallpaper2you_327472.jpeg from '
                         'akatsuki-cloak-naruto-shippudden.zip to that path' % SRC)
    im = np.asarray(Image.open(SRC).convert('RGB')).astype(np.float32) / 255
    a = im.max(2)
    a[a < 0.02] = 0                                     # JPEG noise in the black
    w = np.clip((im[..., 1] / np.maximum(a, 1e-3) - 0.03) / 0.97, 0, 1)
    white_cov = dilate(w * a, STROKE_GROW)
    alpha = np.maximum(a, white_cov)
    red_cov = np.clip(alpha - white_cov, 0, 1)
    rgb = (white_cov[..., None] * WHITE + red_cov[..., None] * RED) / np.maximum(alpha, 1e-6)[..., None]

    ys, xs = np.nonzero(alpha > 0.01)
    y0, y1 = max(ys.min() - MARGIN, 0), ys.max() + MARGIN + 1
    x0, x1 = max(xs.min() - MARGIN, 0), xs.max() + MARGIN + 1
    rgba = np.dstack([rgb, alpha])[y0:y1, x0:x1]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    Image.fromarray((np.clip(rgba, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGBA').save(OUT)
    print('wrote %s  %dx%d' % (OUT, x1 - x0, y1 - y0))


if __name__ == '__main__':
    main()
