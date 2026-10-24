"""Minimal SSE NIF (20.2.0.7, user 12, bs 100) reader: print header blocks; optionally scale the root node.
usage: nif_root.py <in.nif> [<out.nif> <scale>]"""
import struct, sys
d = bytearray(open(sys.argv[1], 'rb').read())
end = d.index(b'\n') + 1
ver, endian, user, nblocks = struct.unpack_from('<IBII', d, end); o = end + 13
bsver = struct.unpack_from('<I', d, o)[0]; o += 4
def sstr(o):  # byte-length string
    n = d[o]; return d[o+1:o+1+n].decode('latin1'), o + 1 + n
author, o = sstr(o); proc, o = sstr(o); export, o = sstr(o)
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
print('version %08X user %d bs %d blocks %d' % (ver, user, bsver, nblocks))
starts = []; p = o
for i in range(nblocks):
    starts.append(p); print('  %2d %-28s %6d @%d' % (i, types[idx[i]], sizes[i], p)); p += sizes[i]
# root = block 0 (NiNode / BSFadeNode): name(4) nextra(4) extra[](4n) controller(4) flags(4) trans(12) rot(36) scale(4)
r = starts[0]; nextra = struct.unpack_from('<I', d, r + 4)[0]
so = r + 4 + 4 + 4 * nextra + 4 + 4 + 12 + 36
print('root', types[idx[0]], 'name', strings[struct.unpack_from('<i', d, r)[0]] if struct.unpack_from('<i', d, r)[0] >= 0 else None,
      'translation', struct.unpack_from('<3f', d, so - 48), 'scale', struct.unpack_from('<f', d, so)[0])
if len(sys.argv) > 3:
    struct.pack_into('<f', d, so, float(sys.argv[3])); open(sys.argv[2], 'wb').write(d); print('wrote', sys.argv[2], 'scale', sys.argv[3])
