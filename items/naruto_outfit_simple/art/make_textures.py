"""Paint the Naruto colours onto BG3's own human male shirt and shorts.

    python items/naruto_outfit_simple/art/make_textures.py naruto_outfit_simple

The garments keep Larian's meshes and UVs, so the colours are defined in 3D (height, side,
front/back) and rasterised through each mesh's UV layout: whatever the UV islands look like,
the paint lands where the position says. Every texel of the base colour is evaluated from
its own surface point, then the islands are padded outward so mip levels do not bleed the
gutter colour into the cloth.

The masks are one flat slot, as for every custom item here.
"""
import os, subprocess, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
import item as itemlib
from gltf_retarget import read

SIZE = 2048
PAD = 10
MASK_SLOT = '#0000FF'
DIVINE = os.path.join(os.environ.get('USERPROFILE', ''), 'Tools', 'LSLib', 'Tools', 'Divine.exe')

ORANGE = np.array([232, 119, 46], np.float32)
NAVY = np.array([35, 42, 74], np.float32)
RED = np.array([196, 38, 46], np.float32)
WHITE = np.array([226, 228, 222], np.float32)
GREY = np.array([150, 155, 165], np.float32)
DARK = np.array([98, 102, 112], np.float32)
VANILLA_GR2 = {'jacket': 'HUM_M_CLT_Shirt_A', 'pants': 'HUM_M_CLT_Pants_H_Short'}


def ensure_gltf(it, tag):
    out = os.path.abspath(os.path.join(it.work, tag + '_vanilla.gltf'))
    if not os.path.exists(out):
        gr2 = os.path.abspath('extracted/mesh/%s.GR2' % VANILLA_GR2[tag])
        if not os.path.exists(gr2):
            raise SystemExit('%s missing: extract it from Models.pak (see README, importing a model)' % gr2)
        subprocess.run([DIVINE, '-g', 'bg3', '-a', 'convert-model', '-s', gr2, '-d', out], check=True)
    return out


def rasterise(pos, nrm, uv, idx):
    """Per-texel surface position and normal, from the mesh's own UV layout."""
    P = np.zeros((SIZE, SIZE, 3), np.float32)
    N = np.zeros((SIZE, SIZE, 3), np.float32)
    cover = np.zeros((SIZE, SIZE), bool)
    px = uv[:, 0] * SIZE
    py = uv[:, 1] * SIZE
    for a, b, c in idx:
        x0, x1, x2 = px[a], px[b], px[c]
        y0, y1, y2 = py[a], py[b], py[c]
        den = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if abs(den) < 1e-9:
            continue
        xmin = max(int(np.floor(min(x0, x1, x2))), 0)
        xmax = min(int(np.ceil(max(x0, x1, x2))), SIZE - 1)
        ymin = max(int(np.floor(min(y0, y1, y2))), 0)
        ymax = min(int(np.ceil(max(y0, y1, y2))), SIZE - 1)
        gx, gy = np.meshgrid(np.arange(xmin, xmax + 1) + 0.5, np.arange(ymin, ymax + 1) + 0.5)
        l0 = ((y1 - y2) * (gx - x2) + (x2 - x1) * (gy - y2)) / den
        l1 = ((y2 - y0) * (gx - x2) + (x0 - x2) * (gy - y2)) / den
        l2 = 1.0 - l0 - l1
        ins = (l0 >= 0) & (l1 >= 0) & (l2 >= 0)
        if not ins.any():
            continue
        p = l0[..., None] * pos[a] + l1[..., None] * pos[b] + l2[..., None] * pos[c]
        n = l0[..., None] * nrm[a] + l1[..., None] * nrm[b] + l2[..., None] * nrm[c]
        sl = (slice(ymin, ymax + 1), slice(xmin, xmax + 1))
        P[sl][ins] = p[ins]
        N[sl][ins] = n[ins]
        cover[sl] |= ins
    return P, N, cover


def pad(P, N, cover, steps=PAD):
    """Grow every island outward so filtering never reaches the gutter colour."""
    cover = cover.copy()
    for _ in range(steps):
        grow = np.zeros_like(cover)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            src_c = np.roll(cover, (dy, dx), (0, 1))
            take = src_c & ~cover & ~grow
            if take.any():
                P[take] = np.roll(P, (dy, dx), (0, 1))[take]
                N[take] = np.roll(N, (dy, dx), (0, 1))[take]
                grow |= take
        cover |= grow
    return P, N, cover


def spiral(x, y, cx, cy, radius, turns=2.2):
    """Boolean mask of an Uzumaki-style spiral stroke inside a disc."""
    dx, dy = x - cx, y - cy
    r = np.hypot(dx, dy)
    phase = (np.arctan2(dy, dx) / (2 * np.pi) + r / (radius / turns)) % 1.0
    ring = (r > radius * 0.93) & (r < radius * 1.05)
    return ((r < radius) & (phase < 0.5) & (r > radius * 0.08)) | ring


def paint_jacket(P, N):
    x, y, z = P[..., 0], P[..., 1], P[..., 2]
    nz = N[..., 2]
    col = np.empty(P.shape, np.float32)
    col[:] = ORANGE
    navy = (np.abs(x) > 0.205) | (y > 1.515) | (y < 1.19) | ((np.abs(x) < 0.02) & (nz > 0.2))
    col[navy] = NAVY
    front = nz > 0.25
    back = nz < -0.25
    col[spiral(x, y, 0.0, 1.52, 0.055) & front] = RED
    col[spiral(x, y, 0.0, 1.50, 0.075) & back] = RED
    return col


def paint_pants(P, N):
    x, y, z = P[..., 0], P[..., 1], P[..., 2]
    col = np.empty(P.shape, np.float32)
    col[:] = ORANGE
    col[y > 1.105] = NAVY
    right = x < 0
    col[right & (y > 0.79) & (y < 0.825)] = WHITE
    col[right & (y >= 0.825) & (y < 0.86)] = NAVY
    col[right & (y >= 0.86) & (y < 0.895)] = WHITE
    pouch = (x > 0.105) & (x < 0.19) & (y > 0.93) & (y < 1.05) & (N[..., 2] > 0.1)
    col[pouch] = GREY
    col[pouch & (y > 1.015)] = DARK
    return col


def main():
    it = itemlib.load()
    os.makedirs(it.textures, exist_ok=True)
    paint = {'jacket': paint_jacket, 'pants': paint_pants}
    for tag, s, _ in it.sets():
        g, acc = read(ensure_gltf(it, tag))
        p = g['meshes'][0]['primitives'][0]
        pos = acc(p['attributes']['POSITION']).astype(np.float32)
        nrm = acc(p['attributes']['NORMAL']).astype(np.float32)
        uv = acc(p['attributes']['TEXCOORD_0']).astype(np.float32)
        idx = acc(p['indices']).reshape(-1, 3).astype(int)
        P, N, cover = rasterise(pos, nrm, uv, idx)
        P, N, cover = pad(P, N, cover)
        col = paint[tag](P, N)
        col[~cover] = NAVY
        png = os.path.join(it.work, '%s_BM.png' % tag)
        Image.fromarray(np.clip(col, 0, 255).astype(np.uint8)).save(png)
        subprocess.run([itemlib.MAGICK, png, '-alpha', 'off', '-define', 'dds:compression=dxt1',
                        '-define', 'dds:mipmaps=12', os.path.join(it.textures, s['bm'])], check=True)
        subprocess.run([itemlib.MAGICK, '-size', '%dx%d' % (SIZE, SIZE), 'xc:' + MASK_SLOT,
                        '-alpha', 'off', '-define', 'dds:compression=dxt1', '-define',
                        'dds:mipmaps=1', os.path.join(it.textures, s['msk'])], check=True)
        print('%-7s %d tris, %.1f%% of texels covered -> %s' % (
            tag, len(idx), 100.0 * cover.mean(), s['bm']))


if __name__ == '__main__':
    main()
