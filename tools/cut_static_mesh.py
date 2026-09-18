"""Cut a garment out of a static (unrigged) model by height and texture colour.

    python tools/cut_static_mesh.py <model.glb> <out.obj> --y LO HI [--drop-skin]
                                    [--max-x X] [--flip-v]

Scanned or generated character models arrive as ONE fused surface: skin, hair, clothes and
all. There is no object to select, so the garment is picked out by what the texture says a
triangle is (orange cloth vs skin) and where it sits on the body.

Skin is told from orange cloth by the blue-to-red ratio, which survives shading: shaded
skin is as dark as cloth but never as saturated. Whole connected pieces are then dropped
when they are mostly skin -- that removes the hands, which hang inside the trouser region,
without deleting cloth patches (the model is split into ~170 pieces at its texture seams,
so dropping small pieces by size alone tears holes in the garment).

UV convention: BG3's own glTF exports store image v directly (verified against the robe's
mask: 73.6% of triangles land inside one mask region that way, 66.9% flipped). Models from
other pipelines often store it upside down -- the naruto-r model does -- which renders as
scrambled patches; pass --flip-v for those. OBJ stores v bottom-up either way, so it is
inverted on write.
"""
import argparse, json, os, struct, sys
import numpy as np
from PIL import Image


def load_glb(path):
    b = open(path, 'rb').read()
    jl, _ = struct.unpack_from('<II', b, 12)
    g = json.loads(b[20:20 + jl])
    off = 20 + jl
    bl, _ = struct.unpack_from('<II', b, off)
    bin_ = b[off + 8:off + 8 + bl]
    CT = {5126: np.float32, 5125: np.uint32, 5123: np.uint16}
    NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3}
    def acc(i):
        a = g['accessors'][i]
        v = g['bufferViews'][a['bufferView']]
        n = NC[a['type']]
        o = v.get('byteOffset', 0) + a.get('byteOffset', 0)
        arr = np.frombuffer(bin_, CT[a['componentType']], a['count'] * n, o)
        return arr.reshape(a['count'], n) if n > 1 else arr
    p = g['meshes'][0]['primitives'][0]
    return (acc(p['attributes']['POSITION']).astype(np.float64),
            acc(p['attributes']['NORMAL']).astype(np.float64),
            acc(p['attributes']['TEXCOORD_0']).astype(np.float64),
            acc(p['indices']).reshape(-1, 3).astype(int))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('model'); ap.add_argument('out')
    ap.add_argument('--texture', required=True)
    ap.add_argument('--y', nargs=2, type=float, required=True, help='keep triangles between these heights')
    ap.add_argument('--max-x', type=float, default=1e9)
    ap.add_argument('--drop-skin', action='store_true')
    ap.add_argument('--flip-v', action='store_true',
                    help='the model stores v upside down (image v = 1 - v)')
    ap.add_argument('--skin-frac', type=float, default=0.5,
                    help='drop a connected piece when this much of it is skin')
    a = ap.parse_args()

    pos, nrm, uv, idx = load_glb(a.model)
    if a.flip_v:
        uv = uv.copy()
        uv[:, 1] = 1.0 - uv[:, 1]        # from here on uv is image space
    tex = np.asarray(Image.open(a.texture).convert('RGB')).astype(np.float32) / 255
    S = tex.shape[0]
    cuv = uv[idx].mean(1)
    col = tex[np.clip((cuv[:, 1] * S).astype(int), 0, S - 1), np.clip((cuv[:, 0] * S).astype(int), 0, S - 1)]
    r, g, b = col.T
    white = (r > 0.8) & (g > 0.8) & (b > 0.8)
    navy = (b > r) & (r < 0.35)
    skin = (r > g) & (g > b) & (b / np.maximum(r, 1e-3) > 0.38) & ~white & ~navy

    cy = pos[idx][:, :, 1].mean(1)
    cx = pos[idx][:, :, 0].mean(1)
    sel = (cy >= a.y[0]) & (cy <= a.y[1]) & (np.abs(cx) <= a.max_x)
    print('%d of %d triangles in range' % (sel.sum(), len(idx)))

    if a.drop_skin:
        ti = np.nonzero(sel)[0]
        parent = np.arange(len(pos))
        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]; x = parent[x]
            return x
        for t in idx[ti]:
            ra = find(t[0])
            for v in t[1:]:
                rb = find(v)
                if rb != ra:
                    parent[rb] = ra
        roots = np.array([find(t[0]) for t in idx[ti]])
        keep = np.ones(len(ti), bool)
        dropped = 0
        for rt in np.unique(roots):
            m = roots == rt
            if skin[ti[m]].mean() >= a.skin_frac:
                keep &= ~m; dropped += 1
        sel = np.zeros(len(idx), bool)
        sel[ti[keep]] = True
        print('dropped %d skin pieces; %d triangles left' % (dropped, sel.sum()))

    tri = idx[sel]
    used = np.unique(tri)
    remap = -np.ones(len(pos), int)
    remap[used] = np.arange(len(used))
    with open(a.out, 'w') as f:
        f.write('# cut from %s  y %s..%s\n' % (os.path.basename(a.model), a.y[0], a.y[1]))
        for v in pos[used]:
            f.write('v %.6f %.6f %.6f\n' % tuple(v))
        for t in uv[used]:
            f.write('vt %.6f %.6f\n' % (t[0], 1.0 - t[1]))   # glTF image v -> OBJ bottom-up v
        for n in nrm[used]:
            f.write('vn %.6f %.6f %.6f\n' % tuple(n))
        for x, y, z in remap[tri] + 1:
            f.write('f %d/%d/%d %d/%d/%d %d/%d/%d\n' % (x, x, x, y, y, y, z, z, z))
    print('wrote %s  (%d verts, %d tris)' % (a.out, len(used), len(tri)))


if __name__ == '__main__':
    main()
