"""Sharingan Vision.esp (ESL, master Skyrim.esm): vanilla Night Eye -> a Sharingan look (2026-10-20).

The Uchiha Clan Sharingan uses vanilla Night Eye, whose screen filters (IMAD) tint the screen 50% blue, add a radial
blur and a big bloom boost (the "blur") and halve saturation. This overrides the three filters (NightEyeImod 0x6B108,
NightEyeImodIntro 0x6B10A (USSEP's version as base), NightEyeImodOutro 0x6B10B), keeping every key time and count:
  tint     -> red, at TINT_STRENGTH of the old alpha (0.502 -> ~0.18)
  fade col -> alpha 0           blur / radial blur / double vision -> 0
  bloom    -> the adds for blur radius, threshold, scale, receive threshold -> 0
  saturation mult 0.5/0.55 -> SATURATION   contrast add -> +CONTRAST_ADD   brightness (the night vision part) kept
Everything else in the night eye (eye adaptation, brightness) is unchanged. Affects every Night Eye user (Khajiit too).

usage: build_vision.py <Skyrim.esm> <USSEP.esp> <out.esp>
"""
import struct, sys, zlib

SKYRIM, USSEP, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
RED = (1.0, 0.18, 0.15)
TINT_STRENGTH = 0.36       # x old alpha
SATURATION = 0.9
CONTRAST_ADD = 0.1


def read(path, fids):
    d = open(path, 'rb').read(); got = {}
    def walk(o, e):
        while o < e:
            t = d[o:o+4]; n = struct.unpack_from('<I', d, o+4)[0]
            if t == b'GRUP': walk(o+24, o+n); o += n; continue
            fl, fid = struct.unpack_from('<II', d, o+8)
            if t == b'IMAD' and fid in fids:
                body = d[o+24:o+24+n]
                if fl & 0x40000: body = zlib.decompress(body[4:])
                got[fid] = (bytearray(d[o:o+24]), body)
            o += 24 + n
    walk(24 + struct.unpack_from('<I', d, 4)[0], len(d))
    return got


def keys(v, width):
    f = list(struct.unpack('<%df' % (len(v) // 4), v))
    return [f[i:i+width] for i in range(0, len(f), width)]


def pack(ks):
    return b''.join(struct.pack('<%df' % len(k), *k) for k in ks)


ZERO = {b'BNAM', b'VNAM', b'RNAM', b'NAM4', b'AIAD', b'BIAD', b'CIAD', b'DIAD'}   # blur, double vision, radial blur, motion blur, bloom adds


def convert(body):
    out = b''; i = 0
    while i < len(body):
        st = body[i:i+4]; n = struct.unpack_from('<H', body, i+4)[0]; v = body[i+6:i+6+n]; i += 6 + n
        if st == b'TNAM':
            v = pack([[k[0], *RED, k[4] * TINT_STRENGTH] for k in keys(v, 5)])
        elif st == b'NAM3':
            v = pack([[k[0], k[1], k[2], k[3], 0.0] for k in keys(v, 5)])
        elif st in ZERO:
            v = pack([[k[0], 0.0] for k in keys(v, 2)])
        elif st == b'\x11IAD':                                  # saturation multiplier
            v = pack([[k[0], SATURATION if k[1] < 0.99 else k[1]] for k in keys(v, 2)])
        elif st == b'SIAD':                                     # contrast add
            v = pack([[k[0], k[1] + CONTRAST_ADD if k[1] > 0 else k[1]] for k in keys(v, 2)])
        out += st + struct.pack('<H', len(v)) + v
    return out


recs = read(SKYRIM, {0x6B108, 0x6B10B})
recs.update(read(USSEP, {0x6B10A}))
assert len(recs) == 3, recs.keys()
body = b''
for fid in sorted(recs):
    head, b = recs[fid]
    nb = convert(b)
    struct.pack_into('<II', head, 4, len(nb), struct.unpack_from('<I', head, 8)[0] & ~0x40000)
    body += bytes(head) + nb


def sub(t, data): return t.encode() + struct.pack('<H', len(data)) + data


hdr = b''.join([sub('HEDR', struct.pack('<fII', 1.7, 3, 0x800)), sub('CNAM', b'Claude\0'),
                sub('SNAM', b'Night Eye as the Sharingan: slight red tint, no blur, clearer.\0'),
                sub('MAST', b'Skyrim.esm\0'), sub('DATA', bytes(8))])
grup = b'GRUP' + struct.pack('<I', 24 + len(body)) + b'IMAD' + struct.pack('<IHHI', 0, 0, 0, 0) + body
open(OUT, 'wb').write(b'TES4' + struct.pack('<IIIIHH', len(hdr), 0x200, 0, 0, 44, 0) + hdr + grup)
print('wrote', OUT)
