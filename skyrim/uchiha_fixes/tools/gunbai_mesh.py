"""gunbai_mesh.py <in.nif> [<out.nif> <scale>] - SSE BSTriShape: report vertex layout and normals of the alternative
gunbai; with out/scale: scale the shape (translation + scale) and flatten the normals of the two broad faces."""
import struct, sys, math, collections
src = sys.argv[1]
d = bytearray(open(src, 'rb').read())
end = d.index(b'\n') + 1
ver, endian, user, nblocks = struct.unpack_from('<IBII', d, end); o = end + 13
bsver = struct.unpack_from('<I', d, o)[0]; o += 4
for _ in range(3):
    o += 1 + d[o]
ntypes = struct.unpack_from('<H', d, o)[0]; o += 2
types = []
for i in range(ntypes):
    n = struct.unpack_from('<I', d, o)[0]; types.append(d[o+4:o+4+n].decode()); o += 4 + n
idx = struct.unpack_from('<%dH' % nblocks, d, o); o += 2 * nblocks
sizes = struct.unpack_from('<%dI' % nblocks, d, o); o += 4 * nblocks
nstr, maxlen = struct.unpack_from('<II', d, o); o += 8
for i in range(nstr):
    n = struct.unpack_from('<I', d, o)[0]; o += 4 + n
ngroups = struct.unpack_from('<I', d, o)[0]; o += 4 + 4 * ngroups
starts = []; p = o
for i in range(nblocks):
    starts.append(p); p += sizes[i]
bi = [i for i in range(nblocks) if types[idx[i]] == 'BSTriShape'][0]
s = starts[bi]
nx = struct.unpack_from('<I', d, s + 4)[0]
q = s + 8 + 4 * nx + 4 + 4
tr_off = q; q += 12
rot_off = q; q += 36
sc_off = q; q += 4
q += 4                      # collision
q += 16                     # bounding sphere
sphere_off = q - 16
q += 12
desc = struct.unpack_from('<Q', d, q)[0]; q += 8
ntri = struct.unpack_from('<H', d, q)[0]; q += 2
nv = struct.unpack_from('<H', d, q)[0]; q += 2
dsize = struct.unpack_from('<I', d, q)[0]; q += 4
vstart = q
vsize = (desc & 0xF) * 4
attrs = (desc >> 44) & 0xFFF
rot = struct.unpack_from('<9f', d, rot_off)
print('tris', ntri, 'verts', nv, 'vertex size', vsize, 'attrs', hex(attrs), 'desc', hex(desc))
print('shape translation', struct.unpack_from('<3f', d, tr_off), 'scale', struct.unpack_from('<f', d, sc_off)[0])
print('rotation', [round(x, 3) for x in rot])
# SSE full precision layout: pos 3f + (bitangentX f if tangents else W f), uv 2 half, normal 3 ub + bitangentY b,
# tangent 3 ub + bitangentZ b, ...
has_t = bool(attrs & 0x10)
def nrm_off(k):
    return vstart + k * vsize + 16 + 4
def dec(b):
    return b / 255.0 * 2.0 - 1.0
def enc(x):
    return max(0, min(255, int(round((x + 1.0) / 2.0 * 255.0))))
groups = collections.Counter()
for k in range(nv):
    no = nrm_off(k)
    n = tuple(dec(d[no + a]) for a in range(3))
    groups[tuple(round(c, 1) for c in n)] += 1
print('normal directions (rounded):', groups.most_common(12))
if len(sys.argv) > 3:
    out, scale = sys.argv[2], float(sys.argv[3])
    t = struct.unpack_from('<3f', d, tr_off)
    struct.pack_into('<3f', d, tr_off, *(c * scale for c in t))
    struct.pack_into('<f', d, sc_off, struct.unpack_from('<f', d, sc_off)[0] * scale)
    flat = 0
    for k in range(nv):
        no = nrm_off(k)
        n = [dec(d[no + a]) for a in range(3)]
        # the broad faces: thickness axis is local Y; snap their normals to exactly +-Y
        if abs(n[1]) > 0.6:
            sign = 1.0 if n[1] > 0 else -1.0
            d[no] = enc(0.0); d[no + 1] = enc(sign); d[no + 2] = enc(0.0)
            flat += 1
    open(out, 'wb').write(d)
    print('wrote', out, 'scale x', scale, 'flattened normals on', flat, 'of', nv, 'vertices')
