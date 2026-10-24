"""Set the emissive colour/multiplier of one named shape's BSLightingShaderProperty in an SSE NIF (in place copy).
usage: glow_color.py <in.nif> <out.nif> <shape name> <r> <g> <b> <mult>"""
import struct, sys
src, dst, want = sys.argv[1:4]; r, g, b, mult = map(float, sys.argv[4:8])
d = bytearray(open(src, 'rb').read())
end = d.index(b'\n') + 1
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
offs = []
for i in range(nb): offs.append(o); o += sizes[i]
done = 0
for i in range(nb):
    if types[idx[i]] in ('BSTriShape', 'BSDynamicTriShape', 'BSSubIndexTriShape'):
        p = offs[i]
        if strings[struct.unpack_from('<i', d, p)[0]] != want: continue
        nx = struct.unpack_from('<I', d, p + 4)[0]; q = p + 8 + 4 * nx + 4 + 4 + 12 + 36 + 4 + 4 + 16 + 4
        sh = struct.unpack_from('<i', d, q)[0]; assert types[idx[sh]] == 'BSLightingShaderProperty'
        s = offs[sh] + 4 + 4
        nxe = struct.unpack_from('<I', d, s)[0]; s += 4 + 4 * nxe + 4 + 8 + 8 + 8 + 4   # extra, ctrl, flags, uv, texset
        old = struct.unpack_from('<4f', d, s)
        struct.pack_into('<4f', d, s, r, g, b, mult); done += 1
        print('%s: emissive (%.2f %.2f %.2f) x%.2f -> (%.2f %.2f %.2f) x%.2f' % ((want,) + old + (r, g, b, mult)))
assert done == 1, done
open(dst, 'wb').write(d)
