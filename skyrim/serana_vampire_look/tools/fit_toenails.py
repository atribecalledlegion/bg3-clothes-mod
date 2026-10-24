"""Fit the toenail mesh onto a feet mesh: for each foot (x < 0 / x > 0) find the translation that moves the nail
vertices onto the nearest feet surface (iterated nearest-point mean, translation only), then write the nails
moved by it. Handles BSTriShape (vertex data in the block) and BSDynamicTriShape (positions after it).
usage: fit_toenails.py <feet.nif> <nails_in.nif> <nails_out.nif> [lift]   lift = extra outward offset (units)"""
import struct, sys, math

def half(h): return struct.unpack('<e', struct.pack('<H', h))[0]
def tohalf(f): return struct.unpack('<H', struct.pack('<e', f))[0]

def parse(path):
    d = bytearray(open(path, 'rb').read()); end = d.index(b'\n') + 1
    ver, en, user, nb = struct.unpack_from('<IBII', d, end); o = end + 13 + 4
    for _ in range(3): o += 1 + d[o]
    nt = struct.unpack_from('<H', d, o)[0]; o += 2; types = []
    for i in range(nt):
        n = struct.unpack_from('<I', d, o)[0]; types.append(d[o+4:o+4+n].decode()); o += 4 + n
    idx = struct.unpack_from('<%dH' % nb, d, o); o += 2 * nb
    sizes = struct.unpack_from('<%dI' % nb, d, o); o += 4 * nb
    ns = struct.unpack_from('<I', d, o)[0]; o += 8; strings = []
    for i in range(ns):
        n = struct.unpack_from('<I', d, o)[0]; strings.append(d[o+4:o+4+n].decode('latin1')); o += 4 + n
    o += 4 + 4 * struct.unpack_from('<I', d, o)[0]
    shapes = []; p = o
    offs = []
    for i in range(nb): offs.append(p); p += sizes[i]
    p = o
    def partition_verts(skin_ref):
        """SSE skinned shapes keep their vertices in NiSkinPartition: numPartitions, dataSize, vertexSize, desc, data."""
        if skin_ref < 0: return []
        part = struct.unpack_from('<i', d, offs[skin_ref] + 4)[0]          # skin instance: data, partition, ...
        if part < 0 or types[idx[part]] != 'NiSkinPartition': return []
        s = offs[part]; npart, dsz, vsz = struct.unpack_from('<III', d, s)
        vdesc = struct.unpack_from('<Q', d, s + 12)[0]; full = bool((vdesc >> 54) & 1)
        base = s + 20
        return [('full', base + k * vsz) for k in range(dsz // vsz)]   # skin partitions here are full precision (checked)
    for i in range(nb):
        t = types[idx[i]]
        if t in ('BSTriShape', 'BSDynamicTriShape'):
            b = p; nx = struct.unpack_from('<I', d, b + 4)[0]
            q = b + 8 + 4 * nx + 4 + 4 + 12 + 36 + 4 + 4 + 16 + 12
            vdesc = struct.unpack_from('<Q', d, q)[0]; q += 8
            ntri = struct.unpack_from('<I', d, q)[0]; nv = struct.unpack_from('<H', d, q + 4)[0]
            dsz = struct.unpack_from('<I', d, q + 6)[0]; q += 10
            vsize = (vdesc & 0xF) * 4; full = bool((vdesc >> 54) & 1)
            verts = []
            if t == 'BSDynamicTriShape':
                # dynamic data (float4 per vertex) follows triangles + particle data at the block end
                dyn_count_off = b + sizes[i] - 4 * 4 * nv - 4
                assert struct.unpack_from('<I', d, dyn_count_off)[0] == nv, 'dynamic layout'
                for k in range(nv): verts.append(('dyn', dyn_count_off + 4 + 16 * k))
            elif dsz:
                for k in range(nv): verts.append(('full' if full else 'half', q + k * vsize))
            else:
                verts = partition_verts(struct.unpack_from('<i', d, b + 8 + 4 * nx + 4 + 4 + 12 + 36 + 4 + 4 + 16)[0])
            name = strings[struct.unpack_from('<i', d, b)[0]]
            shapes.append((name, verts))
        p += sizes[i]
    return d, shapes

def get(d, v):
    kind, off = v
    if kind == 'half': return tuple(half(h) for h in struct.unpack_from('<3H', d, off))
    return struct.unpack_from('<3f', d, off)
def put(d, v, xyz):
    kind, off = v
    if kind == 'half': struct.pack_into('<3H', d, off, *[tohalf(c) for c in xyz])
    else: struct.pack_into('<3f', d, off, *xyz)

NAIL_VERTS = 194
PER_NAIL = '--per-nail' in sys.argv
if PER_NAIL: sys.argv.remove('--per-nail')
feet_d, feet_shapes = parse(sys.argv[1])
nail_d, nail_shapes = parse(sys.argv[2])
lift = float(sys.argv[4]) if len(sys.argv) > 4 else 0.15
feet = [get(feet_d, v) for n, vs in feet_shapes for v in vs]
print('feet verts', len(feet), 'nail shapes', [(n, len(v)) for n, v in nail_shapes])
def icp(pts, fpts):
    """Translation that moves pts onto the nearest fpts surface points (iterated mean of nearest-point offsets)."""
    t = [0.0, 0.0, 0.0]; gap = 0.0
    for it in range(30):
        acc = [0.0, 0.0, 0.0]; gap = 0.0
        for p in pts:
            m = (p[0] + t[0], p[1] + t[1], p[2] + t[2])
            best = min(fpts, key=lambda f: (f[0]-m[0])**2 + (f[1]-m[1])**2 + (f[2]-m[2])**2)
            for a in range(3): acc[a] += best[a] - m[a]
            gap += math.dist(best, m)
        step = [a / len(pts) for a in acc]
        t = [t[a] + step[a] for a in range(3)]
        if max(abs(x) for x in step) < 0.005: break
    return t, gap / len(pts)

def clusters(vs, pts, radius=0.3):
    """Split vertices into separate nails: union of points closer than radius (gaps between toes are wider)."""
    parent = list(range(len(pts)))
    def find(i):
        while parent[i] != i: parent[i] = parent[parent[i]]; i = parent[i]
        return i
    order = sorted(range(len(pts)), key=lambda i: pts[i][0])
    for a in range(len(order)):
        i = order[a]
        for b in range(a + 1, len(order)):
            j = order[b]
            if pts[j][0] - pts[i][0] > radius: break
            if math.dist(pts[i], pts[j]) < radius: parent[find(i)] = find(j)
    groups = {}
    for i in range(len(pts)): groups.setdefault(find(i), []).append(i)
    return sorted(groups.values(), key=lambda g: sum(pts[i][0] for i in g) / len(g))

for side in (-1, 1):
    fpts_all = [p for p in feet if p[0] * side > 0]
    nverts = [v for n, vs in nail_shapes for v in vs if get(nail_d, v)[0] * side > 0]
    pts = [get(nail_d, v) for v in nverts]
    # whole-foot fit first, then (optionally) each nail on its own toe
    t, gap = icp(pts, fpts_all)
    print('side %+d: %d nail verts, whole move (%.2f %.2f %.2f), mean gap %.2f' % (side, len(pts), t[0], t[1], t[2], gap))
    pts = [(p[0] + t[0], p[1] + t[1], p[2] + t[2]) for p in pts]
    if PER_NAIL:
        lo = [min(p[a] for p in pts) - 3 for a in range(3)]; hi = [max(p[a] for p in pts) + 3 for a in range(3)]
        fpts = [f for f in fpts_all if all(lo[a] <= f[a] <= hi[a] for a in range(3))]
        # each nail is NAIL_VERTS consecutive vertices in the mesh (10 x 194 = 1940); fall back to spacing otherwise
        if len(pts) % NAIL_VERTS == 0:
            groups = [list(range(k, k + NAIL_VERTS)) for k in range(0, len(pts), NAIL_VERTS)]
        else:
            groups = clusters(nverts, pts)
        print('   %d nails (sizes %s), %d toe points' % (len(groups), [len(g) for g in groups], len(fpts)))
        for g in groups:
            gp = [pts[i] for i in g]
            tt, gg = icp(gp, fpts)
            print('   nail of %d verts: move (%.2f %.2f %.2f), gap %.2f' % (len(g), tt[0], tt[1], tt[2], gg))
            for i in g: pts[i] = (pts[i][0] + tt[0], pts[i][1] + tt[1], pts[i][2] + tt[2])
    for v, p in zip(nverts, pts):
        put(nail_d, v, (p[0], p[1], p[2] + lift))
open(sys.argv[3], 'wb').write(nail_d)
