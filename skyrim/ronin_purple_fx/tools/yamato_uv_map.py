"""Where the Yamato's parts sit on its shared colour atlas (Albedo.dds): paints each NiTriShape's triangles into UV
space. The sword shape (blade + guard + hilt in one) is coloured by position along its long axis (blue = tip,
red = pommel) so blade and hilt can be told apart; the scabbard nif's shapes get flat colours (saya = green,
guard = yellow). Writes <out>.png (the map) and <out>_<shape>.npy masks (uint8 coverage), plus per-pixel position
along the sword (_axis.npy, 0 = pommel end) and along the scabbard (_saya_axis.npy, 0 = mouth).

usage: yamato_uv_map.py <out prefix> <width>x<height> <sword nif> <scabbard nif>
"""
import struct, sys
import numpy as np
from PIL import Image, ImageDraw

OUT = sys.argv[1]
W, H = (int(x) for x in sys.argv[2].split('x'))     # the atlas is 2048x4096 (width x height)


def read(path):
    """-> {shape name: (verts Nx3, uvs Nx2, tris Mx3)} for every NiTriShape (old Skyrim-style geometry)."""
    d = open(path, 'rb').read()
    o = d.index(b'\n') + 1
    ver, _e, _u, nblocks, bsver = struct.unpack_from('<IBIII', d, o); o += 17
    for _ in range(3):
        o += 1 + d[o]
    ntypes = struct.unpack_from('<H', d, o)[0]; o += 2
    types = []
    for _ in range(ntypes):
        n = struct.unpack_from('<I', d, o)[0]; types.append(d[o + 4:o + 4 + n].decode('latin1')); o += 4 + n
    tidx = struct.unpack_from('<%dH' % nblocks, d, o); o += 2 * nblocks
    sizes = struct.unpack_from('<%dI' % nblocks, d, o); o += 4 * nblocks
    nstr = struct.unpack_from('<I', d, o)[0]; o += 8
    strings = []
    for _ in range(nstr):
        n = struct.unpack_from('<I', d, o)[0]; strings.append(d[o + 4:o + 4 + n].decode('latin1')); o += 4 + n
    o += 4 + 4 * struct.unpack_from('<I', d, o)[0]
    starts = []
    for s in sizes:
        starts.append(o); o += s
    btype = [types[t & 0x7FFF] for t in tidx]
    out = {}
    for i, t in enumerate(btype):
        if t != 'NiTriShape':
            continue
        p = starts[i]
        name = strings[struct.unpack_from('<i', d, p)[0]]
        # NiAVObject (Skyrim: no properties list): name, extra list, controller, flags u32, translation, rotation,
        # scale, collision; then NiGeometry's data ref
        q = p + 4
        q += 4 + 4 * struct.unpack_from('<I', d, q)[0]
        q += 4 + 4 + 12 + 36 + 4
        q += 4
        data = struct.unpack_from('<i', d, q)[0]
        out[name] = geometry(d, starts[data])
    return out


def geometry(d, p):
    p += 4                                              # group id
    n = struct.unpack_from('<H', d, p)[0]; p += 2
    p += 2                                              # keep / compress flags
    has_v = d[p]; p += 1
    verts = np.frombuffer(d, '<f4', n * 3, p).reshape(n, 3) if has_v else None
    p += 12 * n if has_v else 0
    vflags = struct.unpack_from('<H', d, p)[0]; p += 2
    p += 4                                              # material CRC
    has_n = d[p]; p += 1
    if has_n:
        p += 12 * n
        if vflags & 0x1000:
            p += 24 * n                                 # tangents + bitangents
    p += 16                                             # bound
    has_c = d[p]; p += 1
    p += 16 * n if has_c else 0
    nuv = vflags & 0x3F
    uvs = np.frombuffer(d, '<f4', n * 2, p).reshape(n, 2) if nuv else None
    p += 8 * n * nuv
    p += 2 + 4                                          # consistency, additional data
    ntri = struct.unpack_from('<H', d, p)[0]; p += 2
    p += 4                                              # num triangle points
    has_t = d[p]; p += 1
    tris = np.frombuffer(d, '<u2', ntri * 3, p).reshape(ntri, 3) if has_t else None
    return verts, uvs, tris


def paint(img, uvs, tris, colour_of):
    g = ImageDraw.Draw(img)
    px = np.column_stack([(uvs[:, 0] % 1.0) * W, (uvs[:, 1] % 1.0) * H])
    for t in tris:
        g.polygon([tuple(px[k]) for k in t], fill=colour_of(t))


sword = read(sys.argv[3])
scab = read(sys.argv[4])
print('sword shapes', {k: (v[0].shape[0], v[2].shape[0]) for k, v in sword.items()})
print('scabbard shapes', {k: (v[0].shape[0], v[2].shape[0]) for k, v in scab.items()})
img = Image.new('RGB', (W, H), (0, 0, 0))
axis_img = Image.new('F', (W, H), -1.0)
sv, su, st = sword['IronLongSword01:0']
ax = int(np.argmax(sv.max(0) - sv.min(0)))
lo, hi = sv[:, ax].min(), sv[:, ax].max()
print('sword long axis %d from %.1f to %.1f' % (ax, lo, hi))
f = (sv[:, ax] - lo) / (hi - lo)
for name, col in (('saya', (0, 160, 0)), ('guard', (200, 200, 0))):
    if name in scab:
        v, u, t = scab[name]
        paint(img, u, t, lambda tri, c=col: c)
paint(img, su, st, lambda tri: (int(255 * f[tri].mean()), 40, int(255 * (1 - f[tri].mean()))))
paint(axis_img, su, st, lambda tri: float(f[tri].mean()))
img.save(OUT + '.png')
np.save(OUT + '_axis.npy', np.array(axis_img))
for name in ('saya', 'guard'):
    if name in scab:
        m = Image.new('L', (W, H), 0)
        v, u, t = scab[name]
        paint(m, u, t, lambda tri: 255)
        np.save(OUT + '_' + name + '.npy', np.array(m))
# the scabbard's own long axis (0 = one end, 1 = the other), and which end meets the sword's guard
v, u, t = scab['saya']
gv = scab['guard'][0]
a2 = int(np.argmax(v.max(0) - v.min(0)))
g = (v[:, a2] - v[:, a2].min()) / (v[:, a2].max() - v[:, a2].min())
guard_at = (gv[:, a2].mean() - v[:, a2].min()) / (v[:, a2].max() - v[:, a2].min())
print('scabbard long axis %d; the guard sits at %.2f along it (the mouth end)' % (a2, guard_at))
sa = Image.new('F', (W, H), -1.0)
paint(sa, u, t, lambda tri: float(g[tri].mean()) if guard_at < 0.5 else float(1 - g[tri].mean()))   # 0 = mouth
np.save(OUT + '_saya_axis.npy', np.array(sa))
print('wrote', OUT + '.png')
