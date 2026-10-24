"""Naruto Wardrobe - Hide Underwear.esp (ESL override patch, 2026-10-20).

The Leaf flak vest "Shinobi Armor" (NarutoWardrobe.esp ARMO 0x4E18 / ARMA 0x4E17) only takes body slot 32, so the
Schlongs of Skyrim default underwear (slot 52) stayed on and showed through the trousers. The same mod's Uchiha robes
use 32 + 52. This patch copies those two records unchanged except BOD2 slots 32 -> 32 + 52.
Masters = NarutoWardrobe.esp's own masters + NarutoWardrobe.esp, in that order, so every FormID inside the copied
records keeps its meaning byte for byte.

usage: build_underwear_patch.py <NarutoWardrobe.esp> <out.esp>
"""
import struct, sys, zlib

SRC, OUT = sys.argv[1], sys.argv[2]
WANT = {('ARMO', 0x4E18), ('ARMA', 0x4E17)}
SLOT_52 = 1 << (52 - 30)

d = open(SRC, 'rb').read()
hsize = struct.unpack_from('<I', d, 4)[0]
hdr = d[24:24 + hsize]
masters = []
i = 0
while i < len(hdr):
    t = hdr[i:i+4]; n = struct.unpack_from('<H', hdr, i+4)[0]
    if t == b'MAST': masters.append(hdr[i+6:i+6+n].rstrip(b'\0').decode('cp1252'))
    i += 6 + n
own = len(masters)


def sub(t, data): return t.encode() + struct.pack('<H', len(data)) + data


got = {}
def walk(o, e):
    while o < e:
        t = d[o:o+4].decode('latin1'); n = struct.unpack_from('<I', d, o+4)[0]
        if t == 'GRUP': walk(o+24, o+n); o += n; continue
        fl, fid = struct.unpack_from('<II', d, o+8)
        if (t, fid & 0xFFFFFF) in WANT and fid >> 24 == own:
            head = bytearray(d[o:o+24]); body = d[o+24:o+24+n]
            if fl & 0x40000: body = zlib.decompress(body[4:])
            out = b''; j = 0; hit = False
            while j < len(body):
                st = body[j:j+4]; sn = struct.unpack_from('<H', body, j+4)[0]; v = bytearray(body[j+6:j+6+sn])
                if st == b'BOD2':
                    struct.pack_into('<I', v, 0, struct.unpack_from('<I', v, 0)[0] | SLOT_52); hit = True
                out += st + struct.pack('<H', sn) + bytes(v); j += 6 + sn
            assert hit, (t, hex(fid))
            struct.pack_into('<II', head, 4, len(out), fl & ~0x40000)
            got[t] = got.get(t, b'') + bytes(head) + out
        o += 24 + n
walk(24 + hsize, len(d))
assert set(got) == {'ARMO', 'ARMA'}, got.keys()


def grup(label, body):
    return b'GRUP' + struct.pack('<I', 24 + len(body)) + label.encode() + struct.pack('<IHHI', 0, 0, 0, 0) + body


hsubs = [sub('HEDR', struct.pack('<fII', 1.7, 2, 0x800)), sub('CNAM', b'Claude\0'),
         sub('SNAM', b'Shinobi Armor also takes slot 52, so the SOS underwear comes off.\0')]
for m in masters + ['NarutoWardrobe.esp']:
    hsubs += [sub('MAST', m.encode('cp1252') + b'\0'), sub('DATA', bytes(8))]
hbody = b''.join(hsubs)
tes4 = b'TES4' + struct.pack('<IIIIHH', len(hbody), 0x200, 0, 0, 44, 0) + hbody    # ESL flag
open(OUT, 'wb').write(tes4 + grup('ARMO', got['ARMO']) + grup('ARMA', got['ARMA']))
print('masters', masters, '+ NarutoWardrobe.esp; wrote', OUT)
