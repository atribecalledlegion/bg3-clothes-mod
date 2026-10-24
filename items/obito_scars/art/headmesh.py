"""Geometry helpers for the vanilla human-male head: lets us draw on the FACE (in metres,
seen from the front) and land the result in the head's UV sheet with even line widths.

Two lookups are built from the converted mesh (extracted/head_hum_m_<x>/*.glb):

  * P_uv   -- for every texel of the 2048 sheet, its 3D position on the front of the face
  * front  -- for every point of a front view (0.2 mm grid), which UV texel is there

The Divine-converted glTF faces -Z. In a front view the mesh's +x lands on the VIEWER'S
LEFT, which is where the reference art has the scars. Whether that is the character's own
right in game is not something the files can prove; see README.md (the marker test).

  python items/obito_scars/art/headmesh.py [A]   # print landmarks, write out/head_a/front_view.png
"""
import os, json, struct
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
OUT = os.path.join(HERE, 'out')
HEADS = list('ABCDEFGHI') + ['Oscar', 'CHD_B']   # A-I: the adult human-male heads a player can pick; Oscar: an NPC;
                                                  # CHD_B: the human CHILD head B (Dhaen Extended calls it "HUM B")
_MODELS = 'Generated/Public/Shared/Assets/Characters/_Models/Humans/'
_ANIMS = 'Generated/Public/Shared/Assets/Characters/_Anims/Humans/'


def info(head):
    """Names and folders for one human-male head: 'A'..'I' (or 'Oscar')."""
    if head not in HEADS:
        raise SystemExit('head must be one of %s' % ', '.join(HEADS))
    if head == 'CHD_B':
        stem = 'HUM_CHD_NKD_Head_B'
        return dict(head=head, stem=stem, skin=stem + '_Mesh', tex_dir='HUM_CHD_NKD_Head_B',
                    tex_res=_MODELS + 'HUM_CHD_NKD/HUM_CHD_NKD_Head_B/Resources/',
                    gr2_path=_ANIMS + '_Children/Resources/' + stem + '.GR2', bank_name='HUM_CHD_Head_B',
                    eye_to=1.8183,                       # the child head is lowered/raised so its eyes sit where Head A's do
                    src=os.path.join(ROOT, 'extracted', 'head_hum_chd_b'), out=os.path.join(OUT, 'head_chd_b'))
    stem = 'HUM_M_NKD_Head_' + head
    tex_dir = 'HUM_M_Oscar' if head == 'Oscar' else 'HUM_M_Head_' + head
    return dict(head=head, stem=stem, skin=stem + '_Mesh', tex_dir=tex_dir,
                tex_res=_MODELS + 'HUM_M_NKD/' + tex_dir + '/Resources/',
                gr2_path=_ANIMS + '_Male/Resources/' + stem + '.GR2', bank_name=tex_dir,
                src=os.path.join(ROOT, 'extracted', 'head_hum_m_' + head.lower()),
                out=os.path.join(OUT, 'head_' + head.lower()))

STEP = 0.0002                                # front-view grid: 0.2 mm per pixel
XMAX, YTOP, YBOT = 0.09, 1.94, 1.59
FW = int(2 * XMAX / STEP)
FH = int((YTOP - YBOT) / STEP)
R0 = 0.075                                   # side lookup: distance around the head is measured on a cylinder of this radius
A_MAX = 0.16
CW = int(2 * A_MAX / STEP)


def load_meshes(path):
    d = open(path, 'rb').read()
    jl, _ = struct.unpack_from('<II', d, 12)
    js = json.loads(d[20:20 + jl])
    off = 20 + jl
    bl, _ = struct.unpack_from('<II', d, off)
    blob = np.frombuffer(d[off + 8:off + 8 + bl], dtype=np.uint8)

    def acc(i):
        a = js['accessors'][i]
        bv = js['bufferViews'][a['bufferView']]
        n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
        dt = np.dtype({5126: '<f4', 5123: '<u2', 5125: '<u4'}[a['componentType']])
        st = bv.get('byteStride') or n * dt.itemsize
        o = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
        out = np.empty((a['count'], n), dtype=dt)
        for k in range(n):
            ix = o + np.arange(a['count'])[:, None] * st + k * dt.itemsize + np.arange(dt.itemsize)[None, :]
            out[:, k] = blob[ix].view(dt)[:, 0]
        return out

    meshes = {}
    for m in js['meshes']:
        for p in m['primitives']:
            at = p['attributes']
            if 'TEXCOORD_0' not in at or 'indices' not in p:
                continue
            meshes[m['name']] = (acc(at['POSITION']).astype(float),
                                 acc(at['TEXCOORD_0']).astype(float),
                                 acc(p['indices'])[:, 0].astype(int).reshape(-1, 3))
    return meshes


def raster(tri2d, attrs, W, H, z=None):
    """Fill triangles (T,3,2) in pixel space with barycentric-interpolated attrs (T,3,K).
    Where triangles overlap, the smaller z wins. Returns (H,W,K) with NaN where empty."""
    K = attrs.shape[2]
    out = np.full((H, W, K), np.nan, dtype=np.float32)
    zb = np.full((H, W), np.inf, dtype=np.float32)
    for t in range(len(tri2d)):
        p = tri2d[t]
        x0 = max(int(np.floor(p[:, 0].min())), 0); x1 = min(int(np.ceil(p[:, 0].max())) + 1, W)
        y0 = max(int(np.floor(p[:, 1].min())), 0); y1 = min(int(np.ceil(p[:, 1].max())) + 1, H)
        if x1 <= x0 or y1 <= y0:
            continue
        den = (p[1, 1] - p[2, 1]) * (p[0, 0] - p[2, 0]) + (p[2, 0] - p[1, 0]) * (p[0, 1] - p[2, 1])
        if abs(den) < 1e-12:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
        l0 = ((p[1, 1] - p[2, 1]) * (gx - p[2, 0]) + (p[2, 0] - p[1, 0]) * (gy - p[2, 1])) / den
        l1 = ((p[2, 1] - p[0, 1]) * (gx - p[2, 0]) + (p[0, 0] - p[2, 0]) * (gy - p[2, 1])) / den
        l2 = 1 - l0 - l1
        inside = (l0 >= -1e-6) & (l1 >= -1e-6) & (l2 >= -1e-6)
        if not inside.any():
            continue
        zz = np.zeros_like(l0) if z is None else l0 * z[t, 0] + l1 * z[t, 1] + l2 * z[t, 2]
        win = inside & (zz < zb[y0:y1, x0:x1])
        if not win.any():
            continue
        val = l0[..., None] * attrs[t, 0] + l1[..., None] * attrs[t, 1] + l2[..., None] * attrs[t, 2]
        sub = out[y0:y1, x0:x1]; sub[win] = val[win]
        zb[y0:y1, x0:x1][win] = zz[win]
    return out


class Head:
    def __init__(self, head='A', size=2048):
        self.size = size
        self.info = info(head)
        self.meshes = load_meshes(os.path.join(self.info['src'], self.info['stem'] + '.glb'))
        self.y_shift = 0.0
        if 'eye_to' in self.info:           # a head that sits at another height: move it so the fixed grids below fit
            eyes = self.meshes[self.info['stem'] + '_Eyes_Mesh'][0]
            self.y_shift = self.info['eye_to'] - float(eyes[eyes[:, 0] > 0][:, 1].mean())
            self.meshes = {k: (v[0] + np.array([0, self.y_shift, 0]), v[1], v[2]) for k, v in self.meshes.items()}
        P, UV, idx = self.meshes[self.info['skin']]
        # where the ear starts, for clipping the scars: nothing is drawn behind this z on the side of the head
        ear = self.meshes[self.info['stem'] + '_Ears_Mesh'][0]
        self.z_stop = -0.030 if 'eye_to' not in self.info else float(ear[:, 2].min()) + 0.004
        self.side_x = 0.06 if 'eye_to' not in self.info else 0.72 * float(np.abs(P[:, 0]).max())
        tri = P[idx]                                            # (T,3,3)
        n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
        cen = tri.mean(1)
        nose = np.linalg.norm(cen - P[P[:, 2].argmin()], axis=1) < 0.02
        n *= 1 if n[nose, 2].mean() < 0 else -1                # make "outward" consistent
        self.front = idx[n[:, 2] < -0.15]                       # triangles that face the viewer
        self.P, self.UV = P, UV
        tri = P[self.front]; uv = UV[self.front]

        # UV texel -> 3D position. Now includes the sides of the head (up to 112 degrees round from the front),
        # so lines can run out to the ear; the front-only version stopped at the cheek's edge.
        self.zc = 0.5 * (P[:, 2].min() + P[:, 2].max())
        th = np.arctan2(P[:, 0], -(P[:, 2] - self.zc))                      # angle round the head, 0 = straight ahead
        rad = np.hypot(P[:, 0], P[:, 2] - self.zc)
        side = idx[(np.abs(th[idx]) < np.radians(112)).all(1)]
        uvpx = uv * size
        self.P_uv = raster(UV[side] * size, P[side].astype(np.float32), size, size)

        # side lookup: (distance round the head, y) -> UV texel, 3D position. Outermost surface wins.
        a = R0 * th
        cyl_tri = np.stack([(a[side] + A_MAX) / STEP, (YTOP - P[side][..., 1]) / STEP], -1)
        cyl_attr = np.concatenate([UV[side] * size, P[side]], axis=2).astype(np.float32)
        self.cyl = raster(cyl_tri, cyl_attr, CW, FH, z=-rad[side])

        # front view -> UV texel (in pixels) and z. mirrored so +x is on the viewer's left
        fx = (XMAX - tri[..., 0]) / STEP
        fy = (YTOP - tri[..., 1]) / STEP
        fa = np.concatenate([uvpx, tri[..., 2:3]], axis=2).astype(np.float32)
        self.front_uv = raster(np.stack([fx, fy], -1), fa, FW, FH, z=tri[..., 2])
        self._find_edges()

    def _find_edges(self):
        """Per row and side, the outermost column the front view covers, and how far round the head that is."""
        valid = np.isfinite(self.front_uv[..., 0]); c0 = int(round(XMAX / STEP))
        ex = np.zeros((FH, 2)); ea = np.zeros((FH, 2))
        for r in range(FH):
            row = valid[r]
            for k, d in ((0, -1), (1, 1)):                                  # +x is toward smaller columns
                c, last, gap = c0, c0, 0
                while 0 < c < FW - 1:
                    c += d
                    if row[c]:
                        last, gap = c, 0
                    else:
                        gap += 1
                        if gap > 4:
                            break
                if not row[last]:
                    continue
                x = XMAX - last * STEP; z = self.front_uv[r, last, 2]
                ex[r, k] = abs(x); ea[r, k] = R0 * abs(np.arctan2(x, -(z - self.zc)))
        def med(v, w=9):
            pad = np.pad(v, (w // 2, w // 2), mode='edge')
            return np.array([np.median(pad[i:i + w]) for i in range(len(v))])
        for k in (0, 1):
            self.edge_ax = getattr(self, 'edge_ax', np.zeros((FH, 2))); self.edge_a = getattr(self, 'edge_a', np.zeros((FH, 2)))
            self.edge_ax[:, k] = med(ex[:, k]); self.edge_a[:, k] = med(ea[:, k])

    def surface_uv(self, x, y):
        """Like face_to_uv, but carries on past the cheek's edge round the side of the head (out to the ear).
        Inside the front view's reach it returns exactly what face_to_uv does."""
        x = np.asarray(x, float); y = np.asarray(y, float)
        u, v, z = self.face_to_uv(x, y)
        r = np.clip(((YTOP - y) / STEP).astype(int), 0, FH - 1)
        k = (x < 0).astype(int); ax = np.abs(x)
        beyond = ~(ax <= self.edge_ax[r, k]) | ~np.isfinite(u)
        a = np.sign(x) * (self.edge_a[r, k] + (ax - self.edge_ax[r, k]))
        col = np.clip(((a + A_MAX) / STEP).astype(int), 0, CW - 1)
        c = self.cyl[r, col]
        return np.where(beyond, c[..., 0], u), np.where(beyond, c[..., 1], v), np.where(beyond, c[..., 4], z)

    # ---- lookups
    def face_to_uv(self, x, y):
        """(x, y) metres on the face -> (u_px, v_px, z); NaN off the front surface."""
        c = np.clip(((XMAX - np.asarray(x)) / STEP).astype(int), 0, FW - 1)
        r = np.clip(((YTOP - np.asarray(y)) / STEP).astype(int), 0, FH - 1)
        a = self.front_uv[r, c]
        return a[..., 0], a[..., 1], a[..., 2]

    def landmarks(self):
        stem = self.info['stem']
        eyes = self.meshes[stem + '_Eyes_Mesh'][0]
        mouth = [v[0] for k, v in self.meshes.items() if k.startswith(stem + '_Mouth_Interior') and 'LOD' not in k][0]
        lm = {}
        e = eyes[eyes[:, 0] > 0]; lm['eye'] = (float(e[:, 0].mean()), float(e[:, 1].mean()))
        lm['mouth_x'] = float(np.abs(mouth[:, 0]).max()); lm['mouth_y'] = float(mouth[:, 1].mean())
        lm['nose_y'] = float(self.P[self.P[:, 2].argmin(), 1])
        fp = self.P[np.unique(self.front)]
        mid = fp[np.abs(fp[:, 0]) < 0.006]
        lm['chin_y'] = float(mid[:, 1].min())
        rows = {}
        for y in np.arange(1.62, 1.90, 0.02):
            s = fp[np.abs(fp[:, 1] - y) < 0.004]
            rows[round(float(y), 2)] = round(float(np.abs(s[:, 0]).max()), 4) if len(s) else None
        lm['half_width_by_y'] = rows
        return lm


def shaded_front(head):
    """Grey-shaded front view (viewer's left = mesh +x), for previews."""
    z = head.front_uv[..., 2]
    zf = np.where(np.isnan(z), np.nanmax(z), z)
    gy, gx = np.gradient(zf / STEP * 0.0002 * 40)               # exaggerate relief
    shade = 0.62 + 0.9 * (-gx * 0.4 - gy * 0.7)
    img = np.clip(shade, 0.1, 1) * 200
    img[np.isnan(z)] = 30
    return img.astype(np.uint8)


if __name__ == '__main__':
    from PIL import Image
    import sys
    h = Head(sys.argv[1] if len(sys.argv) > 1 else 'A')
    os.makedirs(h.info['out'], exist_ok=True)
    print('front triangles:', len(h.front), ' P_uv coverage: %.1f%%' % (100 * np.isfinite(h.P_uv[..., 0]).mean()))
    lm = h.landmarks()
    for k, v in lm.items():
        print(' ', k, v)
    Image.fromarray(shaded_front(h)).save(os.path.join(h.info['out'], 'front_view.png'))
    print('wrote', os.path.join(h.info['out'], 'front_view.png'), (FW, FH))
