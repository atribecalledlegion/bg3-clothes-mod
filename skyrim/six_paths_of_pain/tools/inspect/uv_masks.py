"""Paint each shape's UV islands of SSE .nif meshes onto a texture-sized canvas, one colour per shape,
to learn which part of a texture atlas belongs to which garment piece.

Usage: uv_masks.py out.png size mesh1.nif [mesh2.nif ...]   (also writes out_<shape>.png masks)
"""
import os, struct, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
import render_nif as R

def shape_uvs(path):
    b, blocks, strings, bsver = R.read_nif(path)
    res = []
    for t, p, n in blocks:
        if t not in ('BSTriShape', 'BSDynamicTriShape', 'BSSubIndexTriShape'):
            continue
        name = struct.unpack_from('<i', b, p)[0]; name = strings[name] if name >= 0 else '?'
        ne = struct.unpack_from('<I', b, p + 4)[0]; q = p + 8 + 4 * ne + 4 + 4 + 52 + 4 + 16
        skin, shader, alpha = struct.unpack_from('<iii', b, q); q += 12
        desc = struct.unpack_from('<Q', b, q)[0]; q += 8
        ntri = struct.unpack_from('<H', b, q)[0]; q += 2; nvert = struct.unpack_from('<H', b, q)[0]; q += 2
        dsize = struct.unpack_from('<I', b, q)[0]; q += 4
        uvs = tris = None
        if dsize:
            vs = (desc & 0xF) * 4; uo = ((desc >> 8) & 0xF) * 4
            raw = np.frombuffer(b[q:q + nvert * vs], np.uint8).reshape(nvert, vs)
            uvs = raw[:, uo:uo + 4].copy().view('<f2').reshape(nvert, 2).astype(np.float64); q += nvert * vs
            tris = np.frombuffer(b[q:q + 6 * ntri], '<u2').reshape(ntri, 3).astype(np.int64)
        elif skin >= 0:
            part = struct.unpack_from('<i', b, blocks[skin][1] + 4)[0]
            r = blocks[part][1]; nparts = struct.unpack_from('<I', b, r)[0]; r += 4
            dsz, vsz = struct.unpack_from('<II', b, r); r += 8
            pdesc = struct.unpack_from('<Q', b, r)[0]; r += 8
            uo = ((pdesc >> 8) & 0xF) * 4; nv = dsz // vsz
            raw = np.frombuffer(b[r:r + dsz], np.uint8).reshape(nv, vsz); r += dsz
            uvs = raw[:, uo:uo + 4].copy().view('<f2').reshape(nv, 2).astype(np.float64)
            allt = []
            for _ in range(nparts):
                pnv, pnt, pnb, pns, pnw = struct.unpack_from('<5H', b, r); r += 10 + 2 * pnb
                hm = b[r]; r += 1; r += 2 * pnv if hm else 0
                hw = b[r]; r += 1; r += 4 * pnv * pnw if hw else 0
                sl = struct.unpack_from('<%dH' % pns, b, r) if pns else (); r += 2 * pns
                hf = b[r]; r += 1
                tt = None
                if hf:
                    if pns: r += 2 * sum(sl)
                    else: tt = np.frombuffer(b[r:r + 6 * pnt], '<u2').reshape(pnt, 3).astype(np.int64); r += 6 * pnt
                hb = b[r]; r += 1; r += pnv * pnw if hb else 0
                r += 2 + 8
                tc = np.frombuffer(b[r:r + 6 * pnt], '<u2').reshape(pnt, 3).astype(np.int64); r += 6 * pnt
                allt.append(tt if tt is not None else tc)
            tris = np.concatenate(allt)
        if uvs is not None:
            res.append((name, uvs, tris))
    return res

if __name__ == '__main__':
    out, size = sys.argv[1], int(sys.argv[2])
    pal = [(230, 60, 60), (60, 140, 230), (80, 200, 90), (240, 200, 60), (190, 90, 230), (60, 210, 210), (250, 140, 40), (200, 200, 200)]
    canvas = Image.new('RGB', (size, size), (0, 0, 0)); dr = ImageDraw.Draw(canvas); k = 0; legend = []
    base = os.path.splitext(out)[0]
    for path in sys.argv[3:]:
        for name, uvs, tris in shape_uvs(path):
            m = Image.new('L', (size, size), 0); dm = ImageDraw.Draw(m)
            px = uvs * size
            for t in tris:
                poly = [tuple(px[i]) for i in t]
                dr.polygon(poly, fill=pal[k % len(pal)]); dm.polygon(poly, fill=255)
            safe = ''.join(c if c.isalnum() else '_' for c in os.path.basename(path).split('_')[0] + '_' + name)
            m.save(f'{base}_{safe}.png'); legend.append((pal[k % len(pal)], f'{os.path.basename(path)}:{name}')); k += 1
    for i, (c, l) in enumerate(legend):
        dr.rectangle([4, 4 + 14 * i, 14, 14 + 14 * i], fill=c); dr.text((18, 3 + 14 * i), l, fill=(255, 255, 255))
    canvas.save(out); print('wrote', out, [l for c, l in legend])
