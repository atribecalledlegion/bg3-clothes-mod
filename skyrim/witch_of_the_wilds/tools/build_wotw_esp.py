"""Build Witch of the Wilds.esp (ESL, master Skyrim.esm only).

Usage: build_wotw_esp.py <Skyrim.esm> <out.esp>

Records (append-only object IDs, saves reference them):
  0x800 QUST WOTW_Quest          Start Game Enabled, script WOTW_QuestScript (gives the power on start)
  0x801 MGEF WOTW_ToggleEffect   Script archetype, Fire and Forget, Self, script WOTW_ToggleEffect
  0x802 SPEL WOTW_TogglePower    Lesser Power "Serana: Witch of the Wilds"
  0x803 CONT WOTW_Storage        empty, non-respawning chest for Serana's weapons while she wields the staff
  0x804 CSTY WOTW_WitchStyle     staff caster that keeps her distance (her moveset casts from range)
  0x805 GLOB WOTW_SetGrimoire    test hook: 'set WOTW_SetGrimoire to <0-100>' sets her Grimoire rank (-1 = idle)
  0x806-0x80A MGEF WOTW_Tier1..5 hidden markers; the OAR tier folders (tools/make_oar.py) check for them
  0x80B-0x80F SPEL WOTW_TierAbility1..5  abilities carrying those markers (the script gives exactly one)
Serana herself, the Bladestaff (BladeStaff.esp) and the Daughter of Coldharbour spells are found at runtime,
so none of those plugins is a master. Helpers follow serana_taekwondo_toggle/tools/build_ctkd_esp.py.
"""
import struct, sys, zlib

SKYRIM, OUT = sys.argv[1], sys.argv[2]
OWN = 1 << 24
NAMES = ['WOTW_Quest', 'WOTW_ToggleEffect', 'WOTW_TogglePower', 'WOTW_Storage', 'WOTW_WitchStyle', 'WOTW_SetGrimoire']
NAMES += ['WOTW_Tier%d' % i for i in range(1, 6)] + ['WOTW_TierAbility%d' % i for i in range(1, 6)]
FID = {n: OWN | (0x800 + i) for i, n in enumerate(NAMES)}
assert FID['WOTW_Tier1'] == OWN | 0x806 and FID['WOTW_TierAbility1'] == OWN | 0x80B
PLAYER_REF, VOICE_SLOT = 0x00000014, 0x00025BEE
TIER_NAMES = ['Novice', 'Apprentice', 'Adept', 'Expert', 'Master']

def sub(t, data): return t.encode() + struct.pack('<H', len(data)) + data
def z(s): return s.encode('cp1252') + b'\0'
def u32(*v): return struct.pack('<%dI' % len(v), *v)
def f32(*v): return struct.pack('<%df' % len(v), *v)
def ws(s): b = s.encode('cp1252'); return struct.pack('<H', len(b)) + b
def rec(t, fid, subs, flags=0, ver=44):
    body = b''.join(subs)
    return t.encode() + struct.pack('<IIIIHH', len(body), flags, fid, 0, ver, 0) + body
def grup(label, body):
    return b'GRUP' + struct.pack('<I', 24 + len(body)) + label.encode() + struct.pack('<IHHI', 0, 0, 0, 0) + body
def p_obj(name, fid): return ws(name) + bytes([1, 1]) + struct.pack('<hhI', 0, -1, fid)
def script(name, props): return ws(name) + bytes([0]) + struct.pack('<H', len(props)) + b''.join(props)
def vmad(scripts, quest=False):
    out = struct.pack('<hhH', 5, 2, len(scripts)) + b''.join(scripts)
    if quest:   # QUST: empty fragment block, no alias scripts
        out += bytes([2]) + struct.pack('<H', 0) + ws('') + struct.pack('<H', 0)
    return sub('VMAD', out)
def subs_of(d):
    i = 0
    while i < len(d):
        t = d[i:i+4].decode('latin1'); n = struct.unpack_from('<H', d, i+4)[0]
        yield t, d[i+6:i+6+n]; i += 6 + n

# --- vanilla templates: MGEF DATA layout, and a plain chest ---
buf = open(SKYRIM, 'rb').read(); V = {}
def walk(o, e):
    while o < e:
        t = buf[o:o+4].decode('latin1'); n = struct.unpack_from('<I', buf, o+4)[0]
        if t == 'GRUP': walk(o+24, o+n); o += n; continue
        fl, fid = struct.unpack_from('<II', buf, o+8); b = buf[o+24:o+24+n]; o += 24 + n
        if t not in ('MGEF', 'CONT'): continue
        if fl & 0x40000: b = zlib.decompress(b[4:])
        s = list(subs_of(b)); ed = dict(s).get('EDID', b'').rstrip(b'\0').decode('latin1')
        if ed == 'CWAbRegenEffect': V[ed] = s
        if t == 'CONT' and ed == 'PlayerHouseChest': V['chest'] = s
walk(24 + struct.unpack_from('<I', buf, 4)[0], len(buf))
assert 'CWAbRegenEffect' in V and 'chest' in V, sorted(V)

MGEF_FID_OFFSETS = [0x08, 0x18, 0x20, 0x24, 0x48, 0x4C, 0x5C, 0x60, 0x64, 0x6C, 0x74, 0x78, 0x7C, 0x80, 0x84, 0x88]
NO_DUR, NO_MAG, NO_AREA, HIDE_UI = 0x200, 0x400, 0x800, 0x8000
def mdata(cast, delivery, flags):
    d = bytearray(dict(V['CWAbRegenEffect'])['DATA'])
    for o in MGEF_FID_OFFSETS: struct.pack_into('<I', d, o, 0)
    struct.pack_into('<If', d, 0x00, flags, 0.0)
    struct.pack_into('<ii', d, 0x0C, -1, -1)       # no magic skill, no resistance
    struct.pack_into('<Ii', d, 0x40, 1, -1)        # Script archetype, no actor value
    struct.pack_into('<II', d, 0x50, cast, delivery)
    return bytes(d)

mgef = rec('MGEF', FID['WOTW_ToggleEffect'], [
    sub('EDID', z('WOTW_ToggleEffect')),
    vmad([script('WOTW_ToggleEffect', [p_obj('Master', FID['WOTW_Quest'])])]),
    sub('FULL', z('Serana: Witch of the Wilds')), sub('DATA', mdata(1, 0, NO_DUR | NO_MAG | NO_AREA)), sub('SNDD', b''),
    sub('DNAM', z("Serana takes up the bladestaff and the witch's grimoire: frost, blood and the bats of Coldharbour."))])

DESC = ("Valerica taught her daughter the old magic of Coldharbour: frost that never thaws, blood that answers "
        "when called. Since meeting Obito, Serana has stopped holding it back. She trades her blade for a "
        "bladestaff and fights as a witch of the wilds would: from a distance, never where her enemies expect "
        "her, feeding when her reserves run dry. Each spell she casts teaches her more of her grimoire. "
        "Use to have her take up the staff, or to set it aside.")
spel = rec('SPEL', FID['WOTW_TogglePower'], [
    sub('EDID', z('WOTW_TogglePower')), sub('OBND', bytes(12)), sub('FULL', z('Serana: Witch of the Wilds')),
    sub('ETYP', u32(VOICE_SLOT)), sub('DESC', z(DESC)),
    sub('SPIT', u32(0, 1, 3) + f32(0.0) + u32(1, 0) + f32(0.0, 0.0) + u32(0)),   # Lesser Power, F&F, Self
    sub('EFID', u32(FID['WOTW_ToggleEffect'])), sub('EFIT', f32(0.0) + u32(0, 0))])

# tier markers: hidden constant effects on self, carried by abilities
tier_mgefs = b''; tier_spels = b''
for i in range(1, 6):
    tier_mgefs += rec('MGEF', FID['WOTW_Tier%d' % i], [
        sub('EDID', z('WOTW_Tier%d' % i)), sub('FULL', z('Grimoire: %s' % TIER_NAMES[i-1])),
        sub('DATA', mdata(0, 0, NO_DUR | NO_MAG | NO_AREA | HIDE_UI)), sub('SNDD', b''), sub('DNAM', z(''))])
    tier_spels += rec('SPEL', FID['WOTW_TierAbility%d' % i], [
        sub('EDID', z('WOTW_TierAbility%d' % i)), sub('OBND', bytes(12)),
        sub('FULL', z('Grimoire: %s' % TIER_NAMES[i-1])),
        sub('SPIT', u32(0, 0, 4) + f32(0.0) + u32(0, 0) + f32(0.0, 0.0) + u32(0)),   # Ability, constant, self
        sub('EFID', u32(FID['WOTW_Tier%d' % i])), sub('EFIT', f32(0.0) + u32(0, 0))])

# chest: vanilla PlayerHouseChest minus its items, respawn flag cleared
csubs = []
for t, d in V['chest']:
    if t in ('CNTO', 'COCT', 'COED', 'VMAD'): continue
    if t == 'EDID': d = z('WOTW_Storage')
    elif t == 'FULL': d = z('Serana Weapon Storage')
    elif t == 'DATA': d = bytes([d[0] & ~0x02]) + d[1:]
    csubs.append(sub(t, d))
cont = rec('CONT', FID['WOTW_Storage'], csubs)

qust = rec('QUST', FID['WOTW_Quest'], [
    sub('EDID', z('WOTW_Quest')),
    vmad([script('WOTW_QuestScript', [p_obj('PlayerRef', PLAYER_REF), p_obj('TogglePower', FID['WOTW_TogglePower']),
                                      p_obj('StorageBase', FID['WOTW_Storage']),
                                      p_obj('WitchStyle', FID['WOTW_WitchStyle']),
                                      p_obj('SetGrimoireGlobal', FID['WOTW_SetGrimoire'])])], quest=True),
    sub('FULL', z('Serana: Witch of the Wilds')),
    sub('DNAM', struct.pack('<HBBII', 0x0011, 50, 0, 0, 0)),   # Start Game Enabled, priority 50 (as CTKD)
    sub('NEXT', b''), sub('ANAM', u32(0))])

# The staff is a warhammer to the AI, so melee weight stays up (she must "attack" to cast), but she keeps her
# distance: high circling/fallback, low offensive pressure, hand magic only as a rare fallback (switching to
# hand spells would drop the staff moveset).
witch_style = rec('CSTY', FID['WOTW_WitchStyle'], [
    sub('EDID', z('WOTW_WitchStyle')),
    # offensive, defensive, group offensive | equipment weights: melee, magic, ranged, shout, unarmed, staff | avoid threat
    sub('CSGD', f32(0.6, 0.7, 0.5, 1.0, 0.2, 0.0, 0.0, 0.0, 0.0, 0.6)),
    sub('CSME', f32(1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.5)),
    sub('CSCR', f32(0.7, 0.8, 0.2, 0.2)),        # circling and falling back are wanted here
    sub('CSLR', f32(0.2)),
    sub('CSFL', f32(0.33, 1.0, 0.5, 0.5, 0.5, 0.5, 0.5, 0.75)),
    sub('DATA', u32(0))])
set_grimoire = rec('GLOB', FID['WOTW_SetGrimoire'], [sub('EDID', z('WOTW_SetGrimoire')), sub('FNAM', b'f'),
                                                     sub('FLTV', f32(-1.0))])

groups = (grup('GLOB', set_grimoire) + grup('CSTY', witch_style) + grup('MGEF', mgef + tier_mgefs)
          + grup('SPEL', spel + tier_spels) + grup('CONT', cont) + grup('QUST', qust))
hdr = [sub('HEDR', f32(1.7) + u32(len(FID) + 6, 0x800 + len(FID))), sub('CNAM', z('Claude')),
       sub('SNAM', z('Serana: Witch of the Wilds')), sub('MAST', z('Skyrim.esm')), sub('DATA', bytes(8))]
open(OUT, 'wb').write(rec('TES4', 0, hdr, flags=0x200) + groups)
print('wrote', OUT)
for k, v in FID.items(): print(f'  {v:08X} {k}')
