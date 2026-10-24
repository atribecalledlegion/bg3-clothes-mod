"""List NiTriShape/BSTriShape/NiNode blocks of a Skyrim NIF (name + flags), or hide shapes by name.
usage: nif_hide.py <in.nif> [out.nif keep_name1,keep_name2]   (with out: every shape NOT in keep list is hidden)"""
import struct, sys
src = sys.argv[1]; d = bytearray(open(src, 'rb').read())
end = d.index(b'\n') + 1
ver, en, user, nb = struct.unpack_from('<IBII', d, end); o = end + 13
o += 4
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
keep = sys.argv[3].split(',') if len(sys.argv) > 3 else None
p = o
for i in range(nb):
    t = types[idx[i]]
    if t in ('NiTriShape', 'BSTriShape', 'NiNode', 'NiBillboardNode', 'BSOrderedNode'):
        name_i = struct.unpack_from('<i', d, p)[0]; name = strings[name_i] if name_i >= 0 else ''
        nx = struct.unpack_from('<I', d, p + 4)[0]; fo = p + 8 + 4 * nx + 4
        flags = struct.unpack_from('<I', d, fo)[0]
        act = ''
        if keep is not None and t in ('NiTriShape', 'BSTriShape') and name not in keep:
            struct.pack_into('<I', d, fo, flags | 1); act = ' -> hidden'
        print('%3d %-16s %-18s flags %X%s' % (i, t, name, flags, act))
    p += sizes[i]
if keep is not None:
    open(sys.argv[2], 'wb').write(d); print('wrote', sys.argv[2])
