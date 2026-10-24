"""Hokage - Hide Mitsunari Scabbards.esp (ESL override patch, 2026-10-20).

MCO Ishida Mitsunari.esp gives every Katana Crafting Dai-Katana the script KatanaScarbbardScript, which equips two
scabbard armors (slot 60): <name>_scb_hand (a sheathed sword at the left hand / hip) and <name>_scb_Mouth. They are
meant to work with Mitsunari's own draw animations; under Sam's moveset they stay put, so the player shows a second,
never-drawn katana at the hip next to the real one on the back. This patch copies Mitsunari's 56 scabbard ARMA records
with their models removed (MOD2-MOD5 + texture hashes), so the pieces stay equipped but render nothing.
Masters = Mitsunari's own masters + MCO Ishida Mitsunari.esp, in order, so every FormID keeps its meaning.

usage: build_hide_scabbards.py <MCO Ishida Mitsunari.esp> <out.esp>
"""
import struct, sys, zlib

SRC, OUT = sys.argv[1], sys.argv[2]
DROP = {'MOD2', 'MO2T', 'MO2S', 'MOD3', 'MO3T', 'MO3S', 'MOD4', 'MO4T', 'MO4S', 'MOD5', 'MO5T', 'MO5S'}

d = open(SRC, 'rb').read()
hsize = struct.unpack_from('<I', d, 4)[0]
hdr = d[24:24 + hsize]
masters, i = [], 0
while i < len(hdr):
    t = hdr[i:i+4]; n = struct.unpack_from('<H', hdr, i+4)[0]
    if t == b'MAST': masters.append(hdr[i+6:i+6+n].rstrip(b'\0').decode('cp1252'))
    i += 6 + n
own = len(masters)

out = b''; count = 0
def walk(o, e):
    global out, count
    while o < e:
        t = d[o:o+4].decode('latin1'); n = struct.unpack_from('<I', d, o+4)[0]
        if t == 'GRUP': walk(o+24, o+n); o += n; continue
        fl, fid = struct.unpack_from('<II', d, o+8)
        if t == 'ARMA' and fid >> 24 == own:
            body = d[o+24:o+24+n]
            if fl & 0x40000: body = zlib.decompress(body[4:])
            edid = b''; new = b''; j = 0
            while j < len(body):
                st = body[j:j+4].decode('latin1'); sn = struct.unpack_from('<H', body, j+4)[0]
                if st == 'EDID': edid = body[j+6:j+6+sn]
                if st not in DROP: new += body[j:j+6+sn]
                j += 6 + sn
            if b'_scb_' in edid:
                head = bytearray(d[o:o+24]); struct.pack_into('<II', head, 4, len(new), fl & ~0x40000)
                out += bytes(head) + new; count += 1
        o += 24 + n
walk(24 + hsize, len(d))
assert count == 56, count


def sub(t, data): return t.encode() + struct.pack('<H', len(data)) + data


hsubs = [sub('HEDR', struct.pack('<fII', 1.7, count, 0x800)), sub('CNAM', b'Claude\0'),
         sub('SNAM', b"Hides Mitsunari's scabbard pieces (the extra hip katana) for Hokage Obito.\0")]
for m in masters + ['MCO Ishida Mitsunari.esp']:
    hsubs += [sub('MAST', m.encode('cp1252') + b'\0'), sub('DATA', bytes(8))]
hbody = b''.join(hsubs)
grup = b'GRUP' + struct.pack('<I', 24 + len(out)) + b'ARMA' + struct.pack('<IHHI', 0, 0, 0, 0) + out
open(OUT, 'wb').write(b'TES4' + struct.pack('<IIIIHH', len(hbody), 0x200, 0, 0, 44, 0) + hbody + grup)
print(f'{count} scabbard ARMA records blanked; masters {masters} + MCO Ishida Mitsunari.esp -> {OUT}')
