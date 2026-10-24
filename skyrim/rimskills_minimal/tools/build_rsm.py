"""Build the two "RimSkills Minimal" patches for Elden Rim - Weapon Art (EldenSkyrim_RimSkills.esp).

Usage: build_rsm.py <EldenSkyrim_RimSkills.esp> <EldenSkyrim.esp (Base 3.7.5)> <Skyrim.esm> <out dir>

Aether Gazer Kagutsuchi masters EldenSkyrim_RimSkills.esp (it uses 3 of its records), but the user does not want the
Weapon Art overhaul in their game. The plugin is loaded with only its assets (no SPID drops, OAR/DAR skill
animations, key config, MCM/HUD, BDI) and these two patches, loaded right after it:
  RimSkills Minimal - Quests.esp   its 3 start-game-enabled quests (ERBWQuest = HUD bar / rune levels / MCM,
                                   EldenUpdate, EldenWeaponPerkAdd2 = weapon-art abilities on the player) copied with
                                   the start-game-enabled flag cleared. Masters = RimSkills' own list + RimSkills,
                                   so the copied bytes need no remapping.
  RimSkills Minimal - Restore.esp  every Elden Base (EldenSkyrim.esp) record RimSkills rewrites, put back as it is in
                                   Base 3.7.5, plus Skyrim.esm's WardBroken idle. Masters = EldenSkyrim's own list +
                                   EldenSkyrim + RimSkills, so EldenSkyrim's records copy byte for byte.
Left as RimSkills has them: the Solstheim CELL/WRLD header edits (RimSkills loads right after EldenSkyrim.esp, so
every later mod's edit of those wins, as before) and FallRoot/LandRoot idles (RimImpactOfPlayer.esp, later, wins).
"""
import os, struct, sys, zlib

RIMS, ELDEN, SKYRIM, OUT = sys.argv[1:5]
QUESTS = {'ERBWQuest', 'EldenUpdate', 'EldenWeaponPerkAdd2'}
SKIP_IDLE_RESTORE = {0x0A790E, 0x0A790F}     # FallRoot, LandRoot: RimImpactOfPlayer.esp overrides them later anyway

def sub(t, data): return t.encode() + struct.pack('<H', len(data)) + data
def z(s): return s.encode('cp1252') + b'\0'
def subs_of(d):
    i = 0
    while i + 6 <= len(d):
        t = d[i:i+4].decode('latin1'); n = struct.unpack_from('<H', d, i+4)[0]
        yield t, d[i+6:i+6+n]; i += 6 + n
def masters(b):
    h = struct.unpack_from('<I', b, 4)[0]
    return [d.rstrip(b'\0').decode() for t, d in subs_of(b[24:24 + h]) if t == 'MAST']
def records(b):
    """yield (type, flags, formid, version fields, raw body) for every record outside of CELL/WRLD children."""
    h = struct.unpack_from('<I', b, 4)[0]
    def w(o, e):
        while o < e:
            t = b[o:o+4].decode('latin1'); n = struct.unpack_from('<I', b, o+4)[0]
            if t == 'GRUP':
                yield from w(o + 24, o + n); o += n; continue
            fl, fid, vc, ver, unk = struct.unpack_from('<IIIHH', b, o+8)
            yield t, fl, fid, (vc, ver, unk), b[o+24:o+24+n]; o += 24 + n
    yield from w(24 + h, len(b))
def rec(t, fl, fid, vers, body):
    return t.encode() + struct.pack('<IIIIHH', len(body), fl, fid, *vers) + body
def edid(fl, body):
    d = zlib.decompress(body[4:]) if fl & 0x40000 else body
    return next((v.rstrip(b'\0').decode('latin1') for k, v in subs_of(d) if k == 'EDID'), '')
def write_plugin(path, mast, by_type, desc):
    n = sum(len(v) for v in by_type.values())
    hdr = [sub('HEDR', struct.pack('<fII', 1.7, n, 0x800)), sub('CNAM', z('Claude')), sub('SNAM', z(desc))]
    for m in mast: hdr += [sub('MAST', z(m)), sub('DATA', bytes(8))]
    body = b''.join(b'GRUP' + struct.pack('<I', 24 + len(b''.join(rs))) + t.encode() + struct.pack('<IHHI', 0, 0, 0, 0)
                    + b''.join(rs) for t, rs in by_type.items())
    open(path, 'wb').write(rec('TES4', 0x200, 0, (0, 44, 0), b''.join(hdr)) + body)

rb = open(RIMS, 'rb').read(); eb = open(ELDEN, 'rb').read(); sb = open(SKYRIM, 'rb').read()
rm, em = masters(rb), masters(eb)
rown, eown = len(rm), len(em)
assert os.path.basename(ELDEN) in rm, rm
r_elden_idx = rm.index(os.path.basename(ELDEN)); r_skyrim_idx = rm.index('Skyrim.esm')

# 1) quests, start-game-enabled cleared
quests = []
for t, fl, fid, vers, body in records(rb):
    if t != 'QUST' or fid >> 24 != rown or edid(fl, body) not in QUESTS: continue
    if fl & 0x40000: body = zlib.decompress(body[4:]); fl &= ~0x40000
    out, done = [], False
    for k, v in subs_of(body):
        if k == 'DNAM' and not done:
            v = bytearray(v); struct.pack_into('<H', v, 0, struct.unpack_from('<H', v, 0)[0] & ~0x0001); v = bytes(v); done = True
        out.append(sub(k, v))
    quests.append(rec(t, fl, fid, vers, b''.join(out)))
assert len(quests) == len(QUESTS), len(quests)
os.makedirs(OUT, exist_ok=True)
write_plugin(os.path.join(OUT, 'RimSkills Minimal - Quests.esp'), rm + [os.path.basename(RIMS)], {'QUST': quests},
             'Elden Rim Weapon Art loaded for its records only: its 3 auto-start quests (HUD, rune levels, weapon-art perks) do not start')

# 2) restore Base records (+ WardBroken)
want_e, want_s = set(), set()
for t, fl, fid, vers, body in records(rb):
    i = fid >> 24
    if i == r_elden_idx: want_e.add(fid & 0xFFFFFF)
    elif i == r_skyrim_idx and t == 'IDLE' and (fid & 0xFFFFFF) not in SKIP_IDLE_RESTORE: want_s.add(fid & 0xFFFFFF)
by_type = {}
found = set()
for t, fl, fid, vers, body in records(eb):
    if fid >> 24 == eown and (fid & 0xFFFFFF) in want_e:
        by_type.setdefault(t, []).append(rec(t, fl, fid, vers, body)); found.add(('e', fid & 0xFFFFFF))
assert em[0] == 'Skyrim.esm'
for t, fl, fid, vers, body in records(sb):
    if t == 'IDLE' and fid >> 24 == 0 and (fid & 0xFFFFFF) in want_s:
        by_type.setdefault(t, []).append(rec(t, fl, fid, vers, body)); found.add(('s', fid & 0xFFFFFF))
missing = [('e', i) for i in want_e if ('e', i) not in found] + [('s', i) for i in want_s if ('s', i) not in found]
assert not missing, missing
write_plugin(os.path.join(OUT, 'RimSkills Minimal - Restore.esp'), em + [os.path.basename(ELDEN), os.path.basename(RIMS)],
             by_type, 'Puts back the Elden Rim Base records (and WardBroken) that Elden Rim Weapon Art rewrites')
print('Quests.esp: %d QUST | Restore.esp: %s' % (len(quests), {t: len(v) for t, v in by_type.items()}))
