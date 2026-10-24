"""Render Skyrim SE .nif meshes (BSTriShape / BSDynamicTriShape, incl. skinned ones whose vertices live in
NiSkinPartition) to a PNG: shaded front + side orthographic views, one colour per shape (texture average
colour when the diffuse DDS can be read). Meant for comparing outfit shapes, not for pretty pictures.

Usage: render_nif.py out.png <data_dir_for_textures|-> mesh1.nif [mesh2.nif ...]
  Each mesh may be given as path=label to set the caption. A mesh path prefixed with ~ is drawn as a
  faint grey reference (e.g. the body).
"""
import os, struct, sys
import numpy as np
from PIL import Image, ImageDraw

def read_nif(path):
    b = open(path, 'rb').read()
    o = b.index(b'\n') + 1
    ver, endian, user_ver, nblocks = struct.unpack_from('<IBII', b, o); o += 13
    bsver = struct.unpack_from('<I', b, o)[0]; o += 4
    for _ in range(3): o += 1 + b[o]
    ntypes = struct.unpack_from('<H', b, o)[0]; o += 2; types = []
    for _ in range(ntypes):
        n = struct.unpack_from('<I', b, o)[0]; types.append(b[o+4:o+4+n].decode('latin1')); o += 4 + n
    btype = struct.unpack_from('<%dH' % nblocks, b, o); o += 2 * nblocks
    bsize = struct.unpack_from('<%dI' % nblocks, b, o); o += 4 * nblocks
    nstr = struct.unpack_from('<I', b, o)[0]; o += 8; strings = []
    for _ in range(nstr):
        n = struct.unpack_from('<I', b, o)[0]; strings.append(b[o+4:o+4+n].decode('latin1')); o += 4 + n
    o += 4 + 4 * struct.unpack_from('<I', b, o)[0]
    blocks = []
    for i in range(nblocks):
        blocks.append((types[btype[i] & 0x7FFF], o, bsize[i])); o += bsize[i]
    return b, blocks, strings, bsver

def vertex_layout(desc):
    flags = desc >> 44
    return {'size': (desc & 0xF) * 4, 'uv': ((desc >> 8) & 0xF) * 4, 'has_uv': bool(flags & 0x2),
            'full': bool(flags & 0x400) or True}       # SSE vertex data is always full-precision positions

def parse_positions(data, count, layout):
    sz = layout['size']
    arr = np.frombuffer(data[:count * sz], dtype=np.uint8).reshape(count, sz)
    pos = arr[:, 0:12].copy().view('<f4').reshape(count, 3)
    return pos.astype(np.float64)

def shapes_of(path):
    b, blocks, strings, bsver = read_nif(path)
    out = []
    for i, (t, p, n) in enumerate(blocks):
        if t == 'NiTriShape':                                    # Oldrim-format geometry (bsver 83)
            r = legacy_trishape(b, blocks, strings, p)
            if r: out.append(r)
            continue
        if t not in ('BSTriShape', 'BSDynamicTriShape', 'BSSubIndexTriShape'):
            continue
        name = struct.unpack_from('<i', b, p)[0]; name = strings[name] if name >= 0 else '?'
        ne = struct.unpack_from('<I', b, p + 4)[0]; q = p + 8 + 4 * ne + 4
        if struct.unpack_from('<I', b, q)[0] & 1: continue        # hidden shape
        q += 4                                                   # flags
        tr = np.array(struct.unpack_from('<3f', b, q)); rot = np.array(struct.unpack_from('<9f', b, q + 12)).reshape(3, 3)
        sc = struct.unpack_from('<f', b, q + 48)[0]; q += 52 + 4  # + collision ref
        q += 16                                                  # bounding sphere
        skin, shader, alpha = struct.unpack_from('<iii', b, q); q += 12
        desc = struct.unpack_from('<Q', b, q)[0]; q += 8
        ntri = struct.unpack_from('<H' if bsver < 130 else '<I', b, q)[0]; q += 2 if bsver < 130 else 4
        nvert = struct.unpack_from('<H', b, q)[0]; q += 2
        dsize = struct.unpack_from('<I', b, q)[0]; q += 4
        lay = vertex_layout(desc)
        pos = tris = None
        if dsize:
            pos = parse_positions(b[q:q + nvert * lay['size']], nvert, lay); q += nvert * lay['size']
            tris = np.frombuffer(b[q:q + ntri * 6], dtype='<u2').reshape(ntri, 3).astype(np.int64)
        if t == 'BSDynamicTriShape':
            # dynamic (morphed) positions follow the shape data
            e = p + n
            dyn = struct.unpack_from('<I', b, e - 4 - 0)[0] if False else None
        if pos is None and skin >= 0:
            st, sp, _ = blocks[skin]
            part_ref = struct.unpack_from('<i', b, sp + 4)[0]
            if part_ref >= 0:
                pt, pp, pn = blocks[part_ref]
                r = pp; nparts = struct.unpack_from('<I', b, r)[0]; r += 4
                dsz, vsz = struct.unpack_from('<II', b, r); r += 8
                pdesc = struct.unpack_from('<Q', b, r)[0]; r += 8
                play = vertex_layout(pdesc); play['size'] = vsz
                nv = dsz // vsz if vsz else 0
                pos = parse_positions(b[r:r + dsz], nv, play); r += dsz
                all_tris = []
                for _ in range(nparts):
                    pnv, pnt, pnb, pns, pnw = struct.unpack_from('<5H', b, r); r += 10
                    r += 2 * pnb
                    has_map = b[r]; r += 1
                    vmap = np.frombuffer(b[r:r + 2 * pnv], dtype='<u2').astype(np.int64) if has_map else np.arange(pnv); r += 2 * pnv if has_map else 0
                    has_w = b[r]; r += 1; r += 4 * pnv * pnw if has_w else 0
                    strip_lens = struct.unpack_from('<%dH' % pns, b, r) if pns else (); r += 2 * pns
                    has_faces = b[r]; r += 1
                    if has_faces:
                        if pns:
                            r += 2 * sum(strip_lens)
                        else:
                            tt = np.frombuffer(b[r:r + 6 * pnt], dtype='<u2').reshape(pnt, 3).astype(np.int64); r += 6 * pnt
                            # SSE partitions index the shared vertex buffer directly; older data uses the map
                            all_tris.append(tt if (not has_map or tt.max() >= pnv) else vmap[tt])
                    has_bi = b[r]; r += 1; r += pnv * pnw if has_bi else 0
                    r += 2                                       # LOD level / global VB flag
                    r += 8                                       # vertex desc
                    tc = np.frombuffer(b[r:r + 6 * pnt], dtype='<u2').reshape(pnt, 3).astype(np.int64); r += 6 * pnt
                    if not has_faces:
                        all_tris.append(tc)
                tris = np.concatenate(all_tris) if all_tris else np.zeros((0, 3), np.int64)
        if pos is None or tris is None or not len(tris):
            continue
        pos = pos @ (rot.T * sc) + tr if not np.allclose(rot, np.eye(3)) or sc != 1 or tr.any() else pos
        tex = None
        if shader >= 0:
            sh_t, sh_p, sh_n = blocks[shader]
            if sh_t == 'BSLightingShaderProperty':
                # shader type(u32) + name + extra + controller + flags.. -> texture set ref sits after a fixed run
                sp2 = sh_p + 4 + 4; ne2 = struct.unpack_from('<I', b, sp2)[0]; sp2 += 4 + 4 * ne2 + 4 + 8 + 8 + 4 + 4
                ts = struct.unpack_from('<i', b, sp2)[0]
                if 0 <= ts < len(blocks) and blocks[ts][0] == 'BSShaderTextureSet':
                    tp = blocks[ts][1]; cnt = struct.unpack_from('<I', b, tp)[0]
                    if cnt:
                        ln = struct.unpack_from('<I', b, tp + 4)[0]; tex = b[tp + 8:tp + 8 + ln].decode('latin1')
        out.append((name, pos, tris, tex))
    return out

def legacy_trishape(b, blocks, strings, p):
    """NiTriShape + NiTriShapeData (20.2.0.7, bsver 83). Returns (name, pos, tris, tex) or None."""
    name = struct.unpack_from('<i', b, p)[0]; name = strings[name] if name >= 0 else '?'
    ne = struct.unpack_from('<I', b, p + 4)[0]; q = p + 8 + 4 * ne + 4 + 4      # extra list, controller, flags
    tr = np.array(struct.unpack_from('<3f', b, q)); rot = np.array(struct.unpack_from('<9f', b, q + 12)).reshape(3, 3)
    sc = struct.unpack_from('<f', b, q + 48)[0]; q += 52 + 4                     # + collision ref
    data_ref, skin_ref = struct.unpack_from('<ii', b, q); q += 8
    if data_ref < 0 or blocks[data_ref][0] != 'NiTriShapeData':
        return None
    d = blocks[data_ref][1]
    d += 4                                                       # group id
    nv = struct.unpack_from('<H', b, d)[0]; d += 2
    d += 2                                                       # keep / compress flags
    has_v = b[d]; d += 1
    if not has_v: return None
    pos = np.frombuffer(b[d:d + 12 * nv], dtype='<f4').reshape(nv, 3).astype(np.float64); d += 12 * nv
    vflags = struct.unpack_from('<H', b, d)[0]; d += 2
    d += 4                                                       # material CRC (Skyrim)
    has_n = b[d]; d += 1
    if has_n:
        d += 12 * nv
        if vflags & 4096: d += 24 * nv                           # tangents + bitangents
    d += 16                                                      # center + radius
    has_c = b[d]; d += 1
    if has_c: d += 16 * nv
    d += 8 * nv * (vflags & 1)                                   # Bethesda vector flags: bit 0 = one UV set
    d += 2 + 4                                                   # consistency flags, additional data
    ntri = struct.unpack_from('<H', b, d)[0]; d += 2
    d += 4                                                       # num triangle points
    has_t = b[d]; d += 1
    if not has_t or not ntri: return None
    tris = np.frombuffer(b[d:d + 6 * ntri], dtype='<u2').reshape(ntri, 3).astype(np.int64)
    if not (np.allclose(rot, np.eye(3)) and sc == 1 and not tr.any()):
        pos = pos @ (rot.T * sc) + tr
    return (name, pos, tris, None)

def tex_colour(data_dir, tex):
    if not tex or data_dir == '-':
        return None
    rel = tex.replace('\\', '/')
    if not rel.lower().startswith('textures/'):
        rel = 'textures/' + rel
    for root in data_dir.split(';'):
        p = os.path.join(root, rel)
        if not os.path.exists(p):
            # case-insensitive lookup
            cur = root
            for part in rel.split('/'):
                if not os.path.isdir(cur): cur = None; break
                m = [x for x in os.listdir(cur) if x.lower() == part.lower()]
                if not m: cur = None; break
                cur = os.path.join(cur, m[0])
            p = cur
        if p and os.path.isfile(p):
            try:
                im = Image.open(p).convert('RGB').resize((32, 32))
                return tuple(int(c) for c in np.asarray(im).reshape(-1, 3).mean(0))
            except Exception:
                return None
    return None

PALETTE = [(220, 90, 90), (90, 160, 230), (110, 200, 120), (230, 190, 80), (180, 110, 220), (90, 210, 210), (240, 140, 60)]

def render(meshes, data_dir, out_png, W=420, H=640):
    items = []
    for k, (path, label, ref) in enumerate(meshes):
        for name, pos, tris, tex in shapes_of(path):
            col = (170, 170, 170) if ref else (tex_colour(data_dir, tex) or PALETTE[len(items) % len(PALETTE)])
            items.append((label, name, pos, tris, col, ref))
    allpos = np.concatenate([it[2] for it in items])
    zmin, zmax = allpos[:, 2].min(), allpos[:, 2].max()
    xr = max(abs(allpos[:, 0]).max(), abs(allpos[:, 1]).max())
    scale = min((H - 40) / (zmax - zmin), (W / 2 - 20) / max(xr, 1e-6))
    views = []
    for view in ('front', 'side'):
        img = np.full((H, W, 3), 245, np.uint8); zbuf = np.full((H, W), -1e9)
        light = np.array([0.3, 0.8, 0.5]); light /= np.linalg.norm(light)
        for label, name, pos, tris, col, ref in items:
            v = pos[tris]                                         # (n,3,3)
            nrm = np.cross(v[:, 1] - v[:, 0], v[:, 2] - v[:, 0]); ln = np.linalg.norm(nrm, axis=1); ln[ln == 0] = 1; nrm /= ln[:, None]
            if view == 'front':   # actors face +Y: camera at +Y looking back, so the character's right (+X) is on the left
                sx = W / 2 - v[..., 0] * scale; depth = v[..., 1]; vn = nrm[:, [0, 2, 1]]
            else:                 # camera at +X (character's right side); facing direction +Y points right
                sx = W / 2 + v[..., 1] * scale; depth = v[..., 0]; vn = nrm[:, [1, 2, 0]]
            sy = H - 20 - (v[..., 2] - zmin) * scale
            shade = 0.35 + 0.65 * np.abs(vn @ light)
            for t in range(len(tris)):
                x0, x1, x2 = sx[t]; y0, y1, y2 = sy[t]
                minx, maxx = int(max(min(x0, x1, x2), 0)), int(min(max(x0, x1, x2), W - 1))
                miny, maxy = int(max(min(y0, y1, y2), 0)), int(min(max(y0, y1, y2), H - 1))
                if minx > maxx or miny > maxy: continue
                xs, ys = np.meshgrid(np.arange(minx, maxx + 1) + .5, np.arange(miny, maxy + 1) + .5)
                d = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
                if abs(d) < 1e-9: continue
                a = ((y1 - y2) * (xs - x2) + (x2 - x1) * (ys - y2)) / d
                bb = ((y2 - y0) * (xs - x2) + (x0 - x2) * (ys - y2)) / d
                c = 1 - a - bb
                inside = (a >= 0) & (bb >= 0) & (c >= 0)
                if not inside.any(): continue
                z = a * depth[t, 0] + bb * depth[t, 1] + c * depth[t, 2]
                sub = zbuf[miny:maxy + 1, minx:maxx + 1]
                m = inside & (z > sub)
                sub[m] = z[m]
                f = shade[t] * (0.55 if ref else 1.0)
                img[miny:maxy + 1, minx:maxx + 1][m] = (np.array(col) * f + (110 if ref else 0)).clip(0, 255).astype(np.uint8)
        views.append(Image.fromarray(img))
    canvas = Image.new('RGB', (W * 2, H + 20 + 14 * len(meshes)), (255, 255, 255))
    canvas.paste(views[0], (0, 0)); canvas.paste(views[1], (W, 0))
    dr = ImageDraw.Draw(canvas)
    for k, (path, label, ref) in enumerate(meshes):
        dr.text((6, H + 4 + 14 * k), ('[ref] ' if ref else '') + label, fill=(0, 0, 0))
    canvas.save(out_png)

if __name__ == '__main__':
    out, data = sys.argv[1], sys.argv[2]
    meshes = []
    for a in sys.argv[3:]:
        ref = a.startswith('~'); a = a.lstrip('~')
        path, _, label = a.partition('=')
        meshes.append((path, label or os.path.basename(path), ref))
    render(meshes, data, out)
    print('wrote', out)
