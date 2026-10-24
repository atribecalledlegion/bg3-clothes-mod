"""Print NiNode names + local transforms (and string-table / extra data) of an SSE NIF. Usage: nif_nodes.py file.nif [filter]"""
import struct, sys
b = open(sys.argv[1], 'rb').read(); flt = sys.argv[2] if len(sys.argv) > 2 else ''
o = b.index(b'\n') + 1
ver, endian, user_ver, nblocks = struct.unpack_from('<IBII', b, o); o += 13; o += 4
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
p = o
for i in range(nblocks):
    t = types[btype[i] & 0x7FFF]
    if t in ('NiNode', 'BSFadeNode', 'NiStringExtraData'):
        name = struct.unpack_from('<i', b, p)[0]; nm = strings[name] if name >= 0 else None
        if t == 'NiStringExtraData':
            print(f'{i:3} {t} {nm!r} = {strings[struct.unpack_from("<i", b, p+4)[0]]!r}')
        elif flt in (nm or ''):
            ne = struct.unpack_from('<I', b, p + 4)[0]; q = p + 8 + 4 * ne + 4 + 4
            tr = struct.unpack_from('<3f', b, q); rot = struct.unpack_from('<9f', b, q + 12); sc = struct.unpack_from('<f', b, q + 48)[0]
            print(f'{i:3} {t:10} {nm!r:62} T=({tr[0]:8.3f},{tr[1]:8.3f},{tr[2]:8.3f}) R0=({rot[0]:.2f},{rot[1]:.2f},{rot[2]:.2f}) S={sc:.2f}')
    p += bsize[i]
