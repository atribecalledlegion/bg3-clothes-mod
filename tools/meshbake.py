"""Mesh-space texture baking and preview rendering (numpy).

Decals are placed on the garment in 3D and baked into UV space, rather than pasted onto
the texture in 2D. The Obito crest could be pasted because it sat inside one flat UV
island; a pattern that covers front, back and sleeves crosses UV seams and rotated
islands, and a 2D paste would cut every cloud that touches one.

Baking:  every texel covered by a triangle gets that triangle's interpolated world
position and normal (raster_uv). A decal is an orthographic projector -- a face
(front/back), a centre, a size and a rotation -- and a texel takes the decal's colour
when its world position falls inside the decal's footprint AND its normal faces the
projector. The normal test is what keeps a back decal off the lining and off the front.

Conventions, matching tools/texview.py and reference/UV_PLACEMENT.md:
  * image v = 1 - collada v
  * the back of the garment faces +Z, the front -Z
  * seen from the back the viewer's right is world -X; from the front it is +X
"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uvmap import load


def mesh_arrays(dae, geom):
    tris = load(dae, geom)
    P = np.array([[v[0] for v in t] for t in tris], np.float64)
    N = np.array([[v[1] for v in t] for t in tris], np.float64)
    UV = np.array([[(v[2][0], 1.0 - v[2][1]) for v in t] for t in tris], np.float64)
    return P, N, UV


def _bary(a, b, c, xs, ys):
    d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(d) < 1e-12:
        return None
    w0 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / d
    w1 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / d
    return w0, w1, 1.0 - w0 - w1


def raster_uv(P, N, UV, S):
    """World position / normal per texel. Returns pos (S,S,3), nrm (S,S,3), cov (S,S),
    and shared (S,S): texels claimed by two triangles far apart in world space. Those are
    mirrored or reused UVs -- whatever is painted there shows in BOTH places, so a decal
    landing on one of them also appears on the other surface."""
    pos = np.zeros((S, S, 3), np.float32)
    nrm = np.zeros((S, S, 3), np.float32)
    cov = np.zeros((S, S), bool)
    shared = np.zeros((S, S), bool)
    px = UV * S
    eps = -1e-4
    for t in range(len(P)):
        a, b, c = px[t]
        x0 = max(int(np.floor(min(a[0], b[0], c[0]))), 0)
        x1 = min(int(np.ceil(max(a[0], b[0], c[0]))), S - 1)
        y0 = max(int(np.floor(min(a[1], b[1], c[1]))), 0)
        y1 = min(int(np.ceil(max(a[1], b[1], c[1]))), S - 1)
        if x1 < x0 or y1 < y0:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        w = _bary(a, b, c, xs, ys)
        if w is None:
            continue
        m = (w[0] >= eps) & (w[1] >= eps) & (w[2] >= eps)
        if not m.any():
            continue
        W = np.stack([w[0][m], w[1][m], w[2][m]], 1)
        wp = W @ P[t]
        wn = W @ N[t]
        yy, xx = np.nonzero(m)
        yy += y0; xx += x0
        prev = cov[yy, xx]
        if prev.any():
            far = prev & (np.linalg.norm(pos[yy, xx] - wp, axis=1) > 0.05)
            shared[yy[far], xx[far]] = True
        pos[yy, xx] = wp
        nrm[yy, xx] = wn
        cov[yy, xx] = True
    n = np.linalg.norm(nrm, axis=2, keepdims=True)
    nrm /= np.where(n > 0, n, 1)
    return pos, nrm, cov, shared


FACES = {
    # face: (projector direction = outward normal it accepts, viewer-right axis sign on X)
    'back':  (np.array([0, 0, 1.0]), -1.0),
    'front': (np.array([0, 0, -1.0]), 1.0),
}


def garment_frame(P):
    lo, hi = P.reshape(-1, 3).min(0), P.reshape(-1, 3).max(0)
    return dict(xc=(lo[0] + hi[0]) / 2, half_w=(hi[0] - lo[0]) / 2, y0=lo[1], h=hi[1] - lo[1])


def apply_decals(base, pos, nrm, cov, frame, decals, images, min_facing=0.35):
    """base (S,S,3) float 0..1, modified in place.
    images: name -> (H,W,4) float 0..1, colour PREMULTIPLIED by alpha."""
    for d in decals:
        img = images[d['image']]
        ih, iw = img.shape[:2]
        direction, rsign = FACES[d['face']]
        cx = frame['xc'] + d['x'] * frame['half_w'] * rsign
        cy = frame['y0'] + d['y'] * frame['h']
        width = d['size'] * frame['h']
        height = width * ih / iw
        th = np.radians(d.get('rot', 0.0))
        facing = nrm @ direction.astype(np.float32)
        sel = cov & (facing > min_facing)
        yy, xx = np.nonzero(sel)
        p = pos[yy, xx]
        # view coordinates: right, up
        r = (p[:, 0] - cx) * rsign
        u = p[:, 1] - cy
        rr = r * np.cos(th) + u * np.sin(th)
        uu = -r * np.sin(th) + u * np.cos(th)
        if d.get('mirror'):
            rr = -rr
        fx = (rr / width + 0.5) * iw - 0.5
        fy = (0.5 - uu / height) * ih - 0.5
        inside = (fx >= 0) & (fx <= iw - 1) & (fy >= 0) & (fy <= ih - 1)
        yy, xx, fx, fy = yy[inside], xx[inside], fx[inside], fy[inside]
        x0 = np.floor(fx).astype(int); y0 = np.floor(fy).astype(int)
        x1 = np.minimum(x0 + 1, iw - 1); y1 = np.minimum(y0 + 1, ih - 1)
        ax = (fx - x0)[:, None]; ay = (fy - y0)[:, None]
        s = (img[y0, x0] * (1 - ax) * (1 - ay) + img[y0, x1] * ax * (1 - ay)
             + img[y1, x0] * (1 - ax) * ay + img[y1, x1] * ax * ay)
        a = s[:, 3:4]
        base[yy, xx] = base[yy, xx] * (1 - a) + s[:, :3]
    return base


def pad(img, cov, iterations=8):
    """Bleed island colours outward into uncovered texels so mip levels and bilinear
    filtering at UV seams sample garment colour, not the empty background."""
    img = img.copy(); cov = cov.copy()
    for _ in range(iterations):
        acc = np.zeros_like(img); cnt = np.zeros(cov.shape, np.float32)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            sc = np.roll(cov, (dy, dx), (0, 1))
            acc += np.roll(img, (dy, dx), (0, 1)) * sc[..., None]
            cnt += sc
        grow = (~cov) & (cnt > 0)
        img[grow] = acc[grow] / cnt[grow][:, None]
        cov |= grow
    return img


def render(P, UV, tex, face, size=900, pad_frac=0.04, N=None):
    """Orthographic textured render of the mesh from the front, back or side.

    With N (per-vertex normals) faces pointing away from the viewer are culled.

    Expect a sliver of print inside the robe's front wrap opening. Gale's robe is modelled
    double-sided: the inner surface duplicates the outer one with flipped normals and the
    SAME UVs, so the inside of the back panel carries the back's clouds and shows through
    the slit. The game draws exactly this; the character's legs hide most of it. It cannot
    be fixed in the texture, since both sides sample the same texels."""
    view = {'back': np.array([0, 0, 1.0]), 'front': np.array([0, 0, -1.0]),
            'side': np.array([1.0, 0, 0])}[face]
    lo, hi = P.reshape(-1, 3).min(0), P.reshape(-1, 3).max(0)
    if face == 'back':
        hx = lambda q: -q[..., 0]; dep = lambda q: q[..., 2]; hr = (-hi[0], -lo[0])
    elif face == 'front':
        hx = lambda q: q[..., 0]; dep = lambda q: -q[..., 2]; hr = (lo[0], hi[0])
    else:  # side: viewer at +X looking toward -X
        hx = lambda q: q[..., 2]; dep = lambda q: q[..., 0]; hr = (lo[2], hi[2])
    span = max(hr[1] - hr[0], hi[1] - lo[1]) * (1 + 2 * pad_frac)
    mx = (hr[0] + hr[1]) / 2; my = (lo[1] + hi[1]) / 2
    SX = (hx(P) - mx) / span * size + size / 2
    SY = (my - P[..., 1]) / span * size + size / 2
    Z = dep(P)
    out = np.zeros((size, size, 3), np.float32)
    alpha = np.zeros((size, size), np.float32)
    zb = np.full((size, size), -1e9)
    TS = tex.shape[0]
    facing = None if N is None else N.mean(1) @ view
    for t in range(len(P)):
        if facing is not None and facing[t] < 0:
            continue
        a = (SX[t, 0], SY[t, 0]); b = (SX[t, 1], SY[t, 1]); c = (SX[t, 2], SY[t, 2])
        x0 = max(int(min(a[0], b[0], c[0])), 0); x1 = min(int(max(a[0], b[0], c[0])) + 1, size - 1)
        y0 = max(int(min(a[1], b[1], c[1])), 0); y1 = min(int(max(a[1], b[1], c[1])) + 1, size - 1)
        if x1 < x0 or y1 < y0:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        w = _bary(a, b, c, xs, ys)
        if w is None:
            continue
        m = (w[0] >= 0) & (w[1] >= 0) & (w[2] >= 0)
        if not m.any():
            continue
        z = w[0] * Z[t, 0] + w[1] * Z[t, 1] + w[2] * Z[t, 2]
        sub = zb[y0:y1 + 1, x0:x1 + 1]
        m &= z > sub
        if not m.any():
            continue
        sub[m] = z[m]
        u = w[0] * UV[t, 0, 0] + w[1] * UV[t, 1, 0] + w[2] * UV[t, 2, 0]
        v = w[0] * UV[t, 0, 1] + w[1] * UV[t, 1, 1] + w[2] * UV[t, 2, 1]
        tx = np.clip((u * TS).astype(int), 0, TS - 1); ty = np.clip((v * TS).astype(int), 0, TS - 1)
        o = out[y0:y1 + 1, x0:x1 + 1]
        o[m] = tex[ty[m], tx[m]]
        alpha[y0:y1 + 1, x0:x1 + 1][m] = 1
    return out, alpha
