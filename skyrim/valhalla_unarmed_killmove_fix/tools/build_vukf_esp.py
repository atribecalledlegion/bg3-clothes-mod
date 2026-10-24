"""Build "Valhalla Unarmed Killmove Fix.esp" (ESL).

Usage: build_vukf_esp.py <ValhallaCombat.esp> <VioLens SE.esp> <out.esp>

Valhalla Combat hangs its killmove tree under the vanilla killmove root (Update.esm), so the vanilla killmove
system (which also runs for followers) picks from it. None of its branches check the attacker's weapon, so an
unarmed attacker (Serana in Taekwondo mode, an unarmed player) can be handed a sword killmove and plays it with an
invisible sword. This patch copies the branch records and adds one condition each:
  weapon branches  : GetEquippedItemType(right hand) != 0   (not fists)
  unarmed branches : GetEquippedItemType(right hand) == 0   (fists)
v2 (2026-10-19): Valhalla's Val_KillMoveShortRoot has no conditions, where the vanilla KillMoveShortRoot it copies
requires a humanoid target (HasKeyword ActorTypeNPC on the target). So its humanoid killmoves (the unarmed punch
combo, slam, body slam, knee throw, the short weapon killmoves) fired on creatures - a dwarven spider's skeleton can't
play the human victim's half of the pair, the death in that animation never comes, and the victim is stuck
unkillable (Serana, unarmed, nearly every dwarven spider fight). The humanoid check is now the FIRST condition of
Val_KillMoveShortRoot and of the from-behind H2H suplex (first, so it ANDs the whole OR group after it).
v3 (2026-10-19): every Valhalla creature root but the dragon's had no race check either, so a wolf, troll or spider
killmove could fire on any creature (or a human). Each creature root now gets, first, the target-race conditions of
VioLens's root for the same creature (VioLens's lists are the fullest: DLC races included), FormIDs remapped to this
plugin's masters; the from-behind weapon killmoves get the humanoid check.
Everything else in the records is copied unchanged. The master list is Valhalla's own plus ValhallaCombat.esp,
so FormIDs inside the copied records need no remapping.
"""
import os, struct, sys, zlib

SRC, VL, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
GET_EQUIPPED_ITEM_TYPE = 597
RIGHT_HAND = 1
# Valhalla's own object IDs (low 24 bits)
WEAPON = [0xA9C8, 0xA9D0, 0xA9D8, 0xA9E1, 0xA9E7, 0xA9ED, 0xA9F5, 0xA9FB, 0xAA01, 0xAA07, 0xAA0D, 0xAA16, 0xAA1D,
          0xAA25, 0xAA67, 0xAA6B, 0xAA6F, 0xAA75, 0xAA7B,          # creature branches (all weapon killmoves)
          0xAA2F, 0xAA3E, 0xAA44, 0xAA4B, 0xAA51, 0xAA61,          # humanoid: 1HM, 2HW, 2HM, dual wield, short blade, axe/mace
          0xAA82, 0xAA83, 0xAA85]                                  # from behind: 2HM, 2HW, 1HM
UNARMED = [0xAA39, 0xAA84]                                         # H2H root, H2H suplex from behind
NEEDS_HUMANOID = [0xAA2E, 0xAA84, 0xAA82, 0xAA83, 0xAA85]          # short root; from behind: H2H suplex, 2HM, 2HW, 1HM
# Valhalla creature root -> VioLens root for the same creature (its target conditions are copied)
RACE_FROM_VIOLENS = {
    0xA9D0: 0x055ABF,     # draugr
    0xA9D8: 0x0B858B,     # falmer
    0xA9E1: 0x05BA3C,     # vampire brute (gargoyle)          VL_KillMoveVampireBrute   (VioLens own: 04...)
    0xA9E7: 0x05BA42,     # chaurus hunter                     VL_KillMoveChaurusFlyer
    0xA9ED: 0x040873,     # bear
    0xA9F5: 0x0D0792,     # steam centurion
    0xA9FB: 0x0C19B3,     # hagraven
    0xAA01: 0x0BFB2E,     # spriggan
    0xAA07: 0x0BD6D9,     # frostbite spider
    0xAA0D: 0x09BB84,     # wolf
    0xAA16: 0x08A908,     # giant
    0xAA1D: 0x0BCF32,     # troll
    0xAA25: 0x024CD3,     # sabre cat
    0xAA67: 0x05BA48,     # dwarven ballista                   VL_KillMoveDwarvenBallistaRoot
    0xAA6B: 0x05BA4C,     # benthic lurker
    0xAA6F: 0x05BA50,     # boar
    0xAA75: 0x05BA56,     # scrib
    0xAA7B: 0x05BA5C,     # riekling
}
GET_IS_RACE, RUN_ON_TARGET_ID = 69, 1
HAS_KEYWORD, ACTOR_TYPE_NPC, RUN_ON_TARGET = 560, 0x00013794, 1

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
def ctda(op, value):
    return struct.pack('<B3xfHHIIIIi', op, value, GET_EQUIPPED_ITEM_TYPE, 0, RIGHT_HAND, 0, 0, 0, -1)
def humanoid_target():
    return struct.pack('<B3xfHHIIIIi', 0x00, 1.0, HAS_KEYWORD, 0, ACTOR_TYPE_NPC, 0, RUN_ON_TARGET, 0, -1)

def plugin_masters(b):
    n = struct.unpack_from('<I', b, 4)[0]
    return [d.rstrip(b'\0').decode() for t, d in subs_of(b[24:24 + n]) if t == 'MAST']

def violens_target_conditions(path, masters_out):
    """{VioLens object id: [CTDA bytes]} - only conditions run on the target (the race / type checks), FormID
    params remapped to masters_out; the last one never carries the OR flag (it must not OR into what follows)."""
    b = open(path, 'rb').read()
    vm = plugin_masters(b) + [os.path.basename(path)]
    found = {}
    def w(o, e):
        while o < e:
            t = b[o:o+4].decode('latin1'); n = struct.unpack_from('<I', b, o+4)[0]
            if t == 'GRUP': w(o + 24, o + n); o += n; continue
            fl, fid = struct.unpack_from('<II', b, o+8); d = b[o+24:o+24+n]; o += 24 + n
            if t != 'IDLE' or (fid & 0xFFFFFF) not in RACE_FROM_VIOLENS.values(): continue
            if fl & 0x40000: d = zlib.decompress(d[4:])
            conds = []
            for k, v in subs_of(d):
                if k != 'CTDA': continue
                v = bytearray(v)
                func, p1, run = struct.unpack_from('<H', v, 8)[0], struct.unpack_from('<I', v, 12)[0], struct.unpack_from('<I', v, 20)[0]
                if run != RUN_ON_TARGET_ID: continue
                if func in (GET_IS_RACE, HAS_KEYWORD):
                    src = vm[p1 >> 24]
                    assert src in masters_out, ('race/keyword from a plugin this patch does not master', src, hex(p1))
                    struct.pack_into('<I', v, 12, (masters_out.index(src) << 24) | (p1 & 0xFFFFFF))
                conds.append(v)
            if conds:
                conds[-1][0] &= ~0x01
                found[fid & 0xFFFFFF] = [bytes(c) for c in conds]
    w(24 + struct.unpack_from('<I', b, 4)[0], len(b))
    return found

buf = open(SRC, 'rb').read(); hsize = struct.unpack_from('<I', buf, 4)[0]
masters = [d.rstrip(b'\0').decode() for t, d in subs_of(buf[24:24 + hsize]) if t == 'MAST']
own = len(masters)
want = {i: ctda(0x20, 0.0) for i in WEAPON}            # != 0, appended
want.update({i: ctda(0x00, 0.0) for i in UNARMED})     # == 0, appended
first = {i: [humanoid_target()] for i in NEEDS_HUMANOID}  # target is humanoid, prepended
vl = violens_target_conditions(VL, masters + ['ValhallaCombat.esp'])
for val_id, vl_id in RACE_FROM_VIOLENS.items():
    assert vl_id in vl, 'VioLens root %06X not found' % vl_id
    first[val_id] = vl[vl_id]                                # its target race checks, prepended
targets = set(want) | set(first)
out, found = [], set()
def walk(o, e):
    while o < e:
        t = buf[o:o+4].decode('latin1'); n = struct.unpack_from('<I', buf, o+4)[0]
        if t == 'GRUP': walk(o + 24, o + n); o += n; continue
        fl, fid, _, ver = struct.unpack_from('<IIIH', buf, o+8)
        b = buf[o+24:o+24+n]; o += 24 + n
        if t != 'IDLE' or fid >> 24 != own or (fid & 0xFFFFFF) not in targets: continue
        if fl & 0x40000: b = zlib.decompress(b[4:]); fl &= ~0x40000
        subs = list(subs_of(b))
        key = fid & 0xFFFFFF
        if key in want:
            last = max([i for i, (k, _) in enumerate(subs) if k in ('EDID', 'CTDA')])
            subs.insert(last + 1, ('CTDA', want[key]))
        if key in first:
            at = min([i for i, (k, _) in enumerate(subs) if k == 'CTDA'] or
                     [max(i for i, (k, _) in enumerate(subs) if k == 'EDID') + 1])
            for c in reversed(first[key]):
                subs.insert(at, ('CTDA', c))
        out.append(rec('IDLE', fid, [sub(k, v) for k, v in subs], fl))
        found.add(fid & 0xFFFFFF)
walk(24 + hsize, len(buf))
missing = targets - found
assert not missing, 'missing: ' + ', '.join('%X' % m for m in sorted(missing))
hdr = [sub('HEDR', struct.pack('<fII', 1.7, len(out), 0x800)), sub('CNAM', z('Claude')),
       sub('SNAM', z('Valhalla Combat: unarmed attackers only get unarmed killmoves; each killmove family only on the race it was made for'))]
for m in masters + ['ValhallaCombat.esp']: hdr += [sub('MAST', z(m)), sub('DATA', bytes(8))]
open(OUT, 'wb').write(rec('TES4', 0, hdr, flags=0x200) + grup('IDLE', b''.join(out)))
print('wrote', OUT, '-', len(out), 'IDLE overrides')
