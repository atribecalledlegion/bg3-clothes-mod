"""Build "NEAE3 Vergil Compat.esp" (ESL) + its Payload Interpreter config.

Usage: build_nvc_esp.py <old NEAE 1.6.5 NotEnoughAttackEffect.esp> <Vergil MirageEdgeChaos.ini> <out mod dir>

NEAE 3.0 (needed by MCO Jetstream Sam / Ishida Mitsunari) dropped five spells that Vergil Yamato 5.7 still casts,
and reused their FormIDs for other records, so under 3.0 those casts would fire the wrong effect (or nothing):
  0xF04 JudgeCut2, 0xF0C JudgeCut3        - $judge2 / $judge3 (were in NEAE 1.6.5's JudgeCut.ini, gone from 3.0's)
  0xF08 drive5, 0xF09 drive6              - $overdrive3 / $overdrive4 (Vergil's MirageEdgeChaos.ini)
  0xDDB MirageEdgeSlashHZLeft             - $MirageEdgeSlashHZLeft (Vergil's MirageEdgeChaos.ini)
This plugin carries copies of those five SPEL records. Their effects still exist, unchanged, in NEAE 3.0 (MGEF 0xDDC,
0xE92, 0xE94, 0xE9A) or in SummonSwords.esp (MGEF 0x83B), and the master order below keeps every master index the
same as in NEAE 1.6.5 (Skyrim 0, Dragonborn 1, SummonSwords 2, NEAE 3), so the copied bytes need no remapping.
The config: a new ini defining $judge2 / $judge3, and a copy of Vergil's MirageEdgeChaos.ini (same path, so it wins
in MO2) with its three lines pointed at this plugin.
"""
import os, re, struct, sys, zlib

OLD, VERGIL_INI, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
NAME = 'NEAE3 Vergil Compat.esp'
MASTERS = ['Skyrim.esm', 'Dragonborn.esm', 'SummonSwords.esp', 'NotEnoughAttackEffect.esp']
# old NEAE id -> (new local id, new EDID, PIE names that cast it)
SPELLS = {0xF04: (0x800, 'NVC_JudgeCut2', ['$judge2']),
          0xF0C: (0x801, 'NVC_JudgeCut3', ['$judge3']),
          0xF08: (0x802, 'NVC_drive5', ['$overdrive3']),
          0xF09: (0x803, 'NVC_drive6', ['$overdrive4']),
          0xDDB: (0x804, 'NVC_MirageEdgeSlashHZLeft', ['$MirageEdgeSlashHZLeft'])}
OWN = len(MASTERS) << 24

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

buf = open(OLD, 'rb').read(); hsize = struct.unpack_from('<I', buf, 4)[0]
old_masters = [d.rstrip(b'\0').decode() for t, d in subs_of(buf[24:24 + hsize]) if t == 'MAST']
assert old_masters == MASTERS[:3], old_masters
found = {}
def walk(o, e):
    while o < e:
        t = buf[o:o+4].decode('latin1'); n = struct.unpack_from('<I', buf, o+4)[0]
        if t == 'GRUP': walk(o + 24, o + n); o += n; continue
        fl, fid = struct.unpack_from('<II', buf, o+8); b = buf[o+24:o+24+n]; o += 24 + n
        if t == 'SPEL' and fid >> 24 == 3 and (fid & 0xFFFFFF) in SPELLS:
            if fl & 0x40000: b = zlib.decompress(b[4:]); fl &= ~0x40000
            found[fid & 0xFFFFFF] = (fl, list(subs_of(b)))
walk(24 + hsize, len(buf))
assert set(found) == set(SPELLS), 'missing: %s' % sorted(set(SPELLS) - set(found))

out = []
for old_id, (new_id, edid, _) in sorted(SPELLS.items(), key=lambda kv: kv[1][0]):
    fl, subs = found[old_id]
    subs = [(k, z(edid) if k == 'EDID' else v) for k, v in subs]
    out.append(rec('SPEL', OWN | new_id, [sub(k, v) for k, v in subs], fl))
hdr = [sub('HEDR', struct.pack('<fII', 1.7, len(out), 0x805)), sub('CNAM', z('Claude')),
       sub('SNAM', z('Restores five NEAE 1.6.5 spells Vergil Yamato 5.7 casts, removed or renumbered in NEAE 3.0'))]
for m in MASTERS: hdr += [sub('MAST', z(m)), sub('DATA', bytes(8))]
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME), 'wb').write(rec('TES4', 0, hdr, flags=0x200) + grup('SPEL', b''.join(out)))

cfg = os.path.join(OUT, 'SKSE', 'PayloadInterpreter', 'Config'); os.makedirs(cfg, exist_ok=True)
cast = lambda i: '@CAST|0x%X|%s|1|1|0|0|0|0|0|0|0' % (i, NAME)
open(os.path.join(cfg, 'NEAE3VergilCompat.ini'), 'w', encoding='utf-8', newline='\r\n').write(
    '; NEAE 3.0 no longer defines these (Vergil Yamato 5.7 uses them); the spells now live in %s\n' % NAME +
    '$judge2 = %s\n$judge3 = %s\n' % (cast(SPELLS[0xF04][0]), cast(SPELLS[0xF0C][0])))
ini = open(VERGIL_INI, 'rb').read().decode('utf-8', 'surrogateescape')
n_fixed = 0
for old_id, (new_id, _, names) in SPELLS.items():
    for name in names:
        pat = re.compile(r'^(\s*' + re.escape(name) + r'\s*=\s*)@CAST\|0x0*%X\|NotEnoughAttackEffect\.esp\|' % old_id, re.I | re.M)
        ini, k = pat.subn(lambda m: m.group(1) + '@CAST|0x%X|%s|' % (new_id, NAME), ini)
        n_fixed += k
open(os.path.join(cfg, 'MirageEdgeChaos.ini'), 'wb').write(ini.encode('utf-8', 'surrogateescape'))
assert n_fixed == 3, n_fixed
print('wrote', NAME, '-', len(out), 'SPEL; MirageEdgeChaos.ini lines repointed:', n_fixed)
