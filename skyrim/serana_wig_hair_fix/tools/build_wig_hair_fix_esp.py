"""Build "Serana Wig Hair Fix.esp" (ESL).

Usage: build_wig_hair_fix_esp.py <Serana Vampire Look.esp> <out.esp>

Equipping armour on the Hair slot (31) hides the wearer's head parts of type Hair (and their extra parts). Serana's
Wendigo hair (Serana Vampire Look.esp, copied from Valerica DF Edition) has its main part SVL_WendigoNoHorn with no
PNAM, so its type is Misc and wigs/hoods (e.g. the [Odd] Sakura wig, slot 31) drew on top of it. Her original SDFHair
was type Hair, female-only. This patch overrides that one HDPT with PNAM = Hair and DATA = female; everything else is
copied unchanged. Master list = Serana Vampire Look's own plus itself, so FormIDs need no remapping.
"""
import struct, sys, zlib

SRC, OUT = sys.argv[1], sys.argv[2]
MAIN_HAIR = 0x000808          # SVL_WendigoNoHorn
HAIR_TYPE, FEMALE = 3, 0x04

def sub(t, data): return t.encode() + struct.pack('<H', len(data)) + data
def z(s): return s.encode('cp1252') + b'\0'
def subs_of(d):
    i = 0
    while i < len(d):
        t = d[i:i+4].decode('latin1'); n = struct.unpack_from('<H', d, i+4)[0]
        yield t, d[i+6:i+6+n]; i += 6 + n
def rec(t, fid, subs, flags=0, ver=44):
    body = b''.join(subs)
    return t.encode() + struct.pack('<IIIIHH', len(body), flags, fid, 0, ver, 0) + body
def grup(label, body):
    return b'GRUP' + struct.pack('<I', 24 + len(body)) + label.encode() + struct.pack('<IHHI', 0, 0, 0, 0) + body

buf = open(SRC, 'rb').read(); hsize = struct.unpack_from('<I', buf, 4)[0]
masters = [d.rstrip(b'\0').decode() for t, d in subs_of(buf[24:24 + hsize]) if t == 'MAST']
own = len(masters)
out = []
def walk(o, e):
    while o < e:
        t = buf[o:o+4].decode('latin1'); n = struct.unpack_from('<I', buf, o+4)[0]
        if t == 'GRUP': walk(o + 24, o + n); o += n; continue
        fl, fid = struct.unpack_from('<II', buf, o+8)
        b = buf[o+24:o+24+n]; o += 24 + n
        if t != 'HDPT' or fid != (own << 24 | MAIN_HAIR): continue
        if fl & 0x40000: b = zlib.decompress(b[4:]); fl &= ~0x40000
        subs = [(k, v) for k, v in subs_of(b) if k != 'PNAM']
        keys = [k for k, _ in subs]
        assert keys[0] == 'EDID' and subs[0][1].rstrip(b'\0') == b'SVL_WendigoNoHorn', keys
        subs = [(k, bytes([FEMALE]) + v[1:] if k == 'DATA' else v) for k, v in subs]
        # field order: EDID FULL? MODL.. DATA PNAM HNAM..
        at = keys.index('DATA') + 1
        subs.insert(at, ('PNAM', struct.pack('<I', HAIR_TYPE)))
        out.append(rec('HDPT', fid, [sub(k, v) for k, v in subs], fl))
walk(24 + hsize, len(buf))
assert len(out) == 1, 'SVL_WendigoNoHorn not found'
hdr = [sub('HEDR', struct.pack('<fII', 1.7, len(out), 0x800)), sub('CNAM', z('Claude')),
       sub('SNAM', z("Serana's Wendigo hair is type Hair, so slot-31 wigs and hoods hide it"))]
for m in masters + ['Serana Vampire Look.esp']: hdr += [sub('MAST', z(m)), sub('DATA', bytes(8))]
open(OUT, 'wb').write(rec('TES4', 0, hdr, flags=0x200) + grup('HDPT', b''.join(out)))
print('wrote', OUT, '-', len(out), 'HDPT override')
