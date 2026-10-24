"""nif_bounds.py <nif> - per shape: name, own transform (translation, scale), bounding sphere; vertex extents when
it can read them (LE NiTriShapeData, SSE BSTriShape full-precision or half vertices). Skyrim LE (bs 83) / SE (bs 100)."""
import struct, sys
d = open(sys.argv[1], 'rb').read()
end = d.index(b'\n') + 1
ver, endian, user, nblocks = struct.unpack_from('<IBII', d, end); o = end + 13
bsver = struct.unpack_from('<I', d, o)[0]; o += 4
def sstr(o):
    n = d[o]; return o + 1 + n
o = sstr(o); o = sstr(o); o = sstr(o)
if bsver < 100 and False: pass
ntypes = struct.unpack_from('<H', d, o)[0]; o += 2
types = []
for i in range(ntypes):
    n = struct.unpack_from('<I', d, o)[0]; types.append(d[o+4:o+4+n].decode()); o += 4 + n
idx = struct.unpack_from('<%dH' % nblocks, d, o); o += 2 * nblocks
sizes = struct.unpack_from('<%dI' % nblocks, d, o); o += 4 * nblocks
nstr, maxlen = struct.unpack_from('<II', d, o); o += 8
strings = []
for i in range(nstr):
    n = struct.unpack_from('<I', d, o)[0]; strings.append(d[o+4:o+4+n].decode('latin1')); o += 4 + n
ngroups = struct.unpack_from('<I', d, o)[0]; o += 4 + 4 * ngroups
starts = []; p = o
for i in range(nblocks):
    starts.append(p); p += sizes[i]
def avobj(s):
    name = struct.unpack_from('<i', d, s)[0]; nx = struct.unpack_from('<I', d, s + 4)[0]
    q = s + 8 + 4 * nx + 4          # controller
    flags = struct.unpack_from('<I', d, q)[0]; q += 4
    tr = struct.unpack_from('<3f', d, q); q += 12
    q += 36
    sc = struct.unpack_from('<f', d, q)[0]; q += 4
    if bsver < 130: q += 4          # collision
    return (strings[name] if name >= 0 else None), tr, sc, q
print('bs', bsver, 'blocks', nblocks)
r0 = starts[0]; nm, tr, sc, q = avobj(r0)
print('root', types[idx[0]], nm, 'translation', [round(x, 2) for x in tr], 'scale', sc)
for i in range(nblocks):
    t = types[idx[i]]; s = starts[i]
    if t in ('NiNode', 'BSFadeNode') and i:
        nm, tr, sc, q = avobj(s); print('  node', i, nm, 'tr', [round(x, 2) for x in tr], 'scale', round(sc, 4))
    if t == 'BSTriShape':
        nm, tr, sc, q = avobj(s)
        c = struct.unpack_from('<3f', d, q); rad = struct.unpack_from('<f', d, q + 12)[0]
        print('  BSTriShape', i, nm, 'tr', [round(x, 2) for x in tr], 'scale', round(sc, 4), 'sphere c', [round(x, 2) for x in c], 'r', round(rad, 2))
    if t == 'NiTriShape':
        nm, tr, sc, q = avobj(s)
        print('  NiTriShape', i, nm, 'tr', [round(x, 2) for x in tr], 'scale', round(sc, 4))
    if t == 'NiTriShapeData':
        q = s + 4                         # group id
        nv = struct.unpack_from('<H', d, q)[0]; q += 2
        q += 2                            # keep flags, compress flags
        hasv = d[q]; q += 1
        if hasv:
            vs = [struct.unpack_from('<3f', d, q + 12 * k) for k in range(nv)]
            mn = [min(v[a] for v in vs) for a in range(3)]; mx = [max(v[a] for v in vs) for a in range(3)]
            print('  NiTriShapeData', i, 'verts', nv, 'extent', [round(mx[a] - mn[a], 2) for a in range(3)],
                  'min', [round(x, 1) for x in mn], 'max', [round(x, 1) for x in mx])
# SSE BSTriShape vertex extents
for i in range(nblocks):
    if types[idx[i]] != 'BSTriShape': continue
    nm, tr, sc, q = avobj(starts[i])
    q += 16                     # bounding sphere
    q += 12                     # skin, shader, alpha refs
    desc = struct.unpack_from('<Q', d, q)[0]; q += 8
    ntri = struct.unpack_from('<H', d, q)[0]; q += 2
    nv = struct.unpack_from('<H', d, q)[0]; q += 2
    dsize = struct.unpack_from('<I', d, q)[0]; q += 4
    vsize = (desc & 0xF) * 4
    attrs = (desc >> 44) & 0xFFF
    full = bsver < 130 or bool(attrs & 0x400)    # SSE always stores float positions
    vs = []
    for k in range(nv):
        b = q + k * vsize
        if full: vs.append(struct.unpack_from('<3f', d, b))
        else: vs.append(struct.unpack_from('<3e', d, b))
    mn = [min(v[a] for v in vs) for a in range(3)]; mx = [max(v[a] for v in vs) for a in range(3)]
    print('  BSTriShape verts', i, nv, 'full', full, 'extent', [round(mx[a] - mn[a], 2) for a in range(3)],
          'min', [round(x, 1) for x in mn], 'max', [round(x, 1) for x in mx], '(+ shape translation', tr, ')')
