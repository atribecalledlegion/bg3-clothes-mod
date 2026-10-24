"""Add a looping spin to a simple SSE NIF (root NiNode -> one BSTriShape child).
Inserts a 'Spin' NiNode between the root and its first child, driven by NiTransformController ->
NiTransformInterpolator -> NiTransformData (XYZ rotation, Z: 0 -> 2pi over `period` seconds, loop), and gives the
root a BSXFlags (Animated). usage: nif_add_spin.py <in.nif> <out.nif> [period]"""
import struct, sys, math
src, dst = sys.argv[1], sys.argv[2]
period = float(sys.argv[3]) if len(sys.argv) > 3 else 0.25
d = open(src, 'rb').read()

# ---- parse header ----
end = d.index(b'\n') + 1
hdr_line = d[:end]
ver, endian, user, nblocks = struct.unpack_from('<IBII', d, end); o = end + 13
bsver = struct.unpack_from('<I', d, o)[0]; o += 4
bs_strings = []
for _ in range(3):
    n = d[o]; bs_strings.append(d[o:o+1+n]); o += 1 + n
ntypes = struct.unpack_from('<H', d, o)[0]; o += 2
types = []
for i in range(ntypes):
    n = struct.unpack_from('<I', d, o)[0]; types.append(d[o+4:o+4+n].decode()); o += 4 + n
idx = list(struct.unpack_from('<%dH' % nblocks, d, o)); o += 2 * nblocks
sizes = list(struct.unpack_from('<%dI' % nblocks, d, o)); o += 4 * nblocks
nstr, maxlen = struct.unpack_from('<II', d, o); o += 8
strings = []
for i in range(nstr):
    n = struct.unpack_from('<I', d, o)[0]; strings.append(d[o+4:o+4+n].decode('latin1')); o += 4 + n
ngroups = struct.unpack_from('<I', d, o)[0]; groups = d[o+4:o+4+4*ngroups]; o += 4 + 4 * ngroups
blocks = []
for i in range(nblocks):
    blocks.append(bytearray(d[o:o+sizes[i]])); o += sizes[i]
footer = d[o:]
assert types[idx[0]] in ('NiNode', 'BSFadeNode'), types[idx[0]]

# ---- root layout ----
root = blocks[0]
nextra = struct.unpack_from('<I', root, 4)[0]
p_ctrl = 8 + 4 * nextra
p_flags = p_ctrl + 4
p_coll = p_flags + 4 + 12 + 36 + 4
p_nchild = p_coll + 4
nchild = struct.unpack_from('<I', root, p_nchild)[0]
children = list(struct.unpack_from('<%di' % nchild, root, p_nchild + 4))
assert nchild >= 1
shape = children[0]

def type_index(name):
    if name not in types: types.append(name)
    return types.index(name)
def string_index(s):
    if s not in strings: strings.append(s)
    return strings.index(s)

SPIN, CTRL, INTERP, DATA, BSX = range(nblocks, nblocks + 5)
# Spin NiNode: identity transform, child = the shape, controller = CTRL
spin = struct.pack('<iIiI', string_index('Spin'), 0, CTRL, 14)          # name, no extra data, controller, flags
spin += struct.pack('<3f', 0, 0, 0) + struct.pack('<9f', 1, 0, 0, 0, 1, 0, 0, 0, 1) + struct.pack('<f', 1.0)
spin += struct.pack('<i', -1) + struct.pack('<Ii', 1, shape) + struct.pack('<I', 0)
# NiTransformController: next ctrl, flags (active, loop), frequency, phase, start, stop, target, interpolator
ctrl = struct.pack('<iHffffii', -1, 0x0008, 1.0, 0.0, 0.0, period, SPIN, INTERP)
# NiTransformInterpolator: identity NiQuatTransform (translation, quat w x y z, scale) + data
interp = struct.pack('<3f4ff', 0, 0, 0, 1, 0, 0, 0, 1.0) + struct.pack('<i', DATA)
# NiTransformData: 1 rotation key of XYZ type; X, Y empty; Z linear 0 -> 2pi; no translation / scale keys
data = struct.pack('<II', 1, 4) + struct.pack('<I', 0) + struct.pack('<I', 0)
data += struct.pack('<II', 2, 1) + struct.pack('<ff', 0.0, 0.0) + struct.pack('<ff', period, 2 * math.pi)
data += struct.pack('<I', 0) + struct.pack('<I', 0)
# BSXFlags (NiIntegerExtraData): name "BSX", value 1 = Animated
bsx = struct.pack('<iI', string_index('BSX'), 1)

# root: child -> spin, add BSXFlags to its extra data list
struct.pack_into('<i', root, p_nchild + 4, SPIN)
root = root[:4] + struct.pack('<I', nextra + 1) + root[8:8 + 4 * nextra] + struct.pack('<i', BSX) + root[8 + 4 * nextra:]
blocks[0] = root

new = [(spin, 'NiNode'), (ctrl, 'NiTransformController'), (interp, 'NiTransformInterpolator'),
       (data, 'NiTransformData'), (bsx, 'BSXFlags')]
for b, t in new:
    blocks.append(bytearray(b)); idx.append(type_index(t))

# ---- write ----
out = bytearray(hdr_line)
out += struct.pack('<IBII', ver, endian, user, len(blocks)) + struct.pack('<I', bsver) + b''.join(bs_strings)
out += struct.pack('<H', len(types))
for t in types: out += struct.pack('<I', len(t)) + t.encode()
out += struct.pack('<%dH' % len(idx), *idx)
out += struct.pack('<%dI' % len(blocks), *[len(b) for b in blocks])
out += struct.pack('<II', len(strings), max(len(s) for s in strings))
for s in strings: out += struct.pack('<I', len(s)) + s.encode('latin1')
out += struct.pack('<I', ngroups) + groups
for b in blocks: out += b
out += footer
open(dst, 'wb').write(out)
print('wrote', dst, '- blocks', len(blocks), 'types', types)
