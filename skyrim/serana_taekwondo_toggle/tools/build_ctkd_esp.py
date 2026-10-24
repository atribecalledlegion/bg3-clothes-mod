"""Build Serana Taekwondo Toggle.esp (ESL, master Skyrim.esm only).

Usage: build_ctkd_esp.py <Skyrim.esm> <out.esp>

Records (append-only object IDs, saves reference them):
  0x800 QUST CTKD_Quest          Start Game Enabled, script CTKD_QuestScript (gives the power on start)
  0x801 MGEF CTKD_ToggleEffect   Script archetype, Fire and Forget, Self, script CTKD_ToggleEffect
  0x802 SPEL CTKD_TogglePower    Lesser Power "Serana: Taekwondo Toggle"
  0x804 GLOB CTKD_UnarmedPowerMult  multiplier on her blade damage in Taekwondo mode (default 3.0)
  0x805 CSTY CTKD_JuriStyle         Taekwondo AI: aggressive unarmed, magic only as a fallback (from csWEBrawler)
  0x806 GLOB CTKD_SetMastery        test hook: 'set CTKD_SetMastery to <0-100>' in the console sets her Juri Mastery (-1 = idle)
  0x807 IDLE CTKD_PlayerSkyFXPowerAttack  for Obito (player): Dynamic Key Action Framework plays it on a key
                                    (SKSE/Plugins/DKAF/CTKD_SkyFXPowerAttack.json); sends MCO's unarmed power
                                    attack event, so SkyFX (OAR) picks the move; only when both hands are empty
  0x80F IDLE CTKD_PlayerWeaponPowerAttack  for Obito (player), Mouse5 via DKAF like 0x807, but for melee weapons
                                    (right hand sword..warhammer, item types 1-6): sends attackPowerStartInPlace
                                    (as SCAR's ADXP_NPCPowerAttack), so MCO plays the weapon's power attack. OCPA's keys
                                    are off and its long press repeats light attacks, so nothing else power attacks.
  0x810 IDLE CTKD_PlayerDualPowerAttack   Mouse5 (DKAF) with a one-handed weapon in each hand: attackPowerStartDualWield
  0x811 IDLE CTKD_PlayerLeftPowerAttack   Mouse5 (DKAF) with a one-handed weapon only in the left hand:
                                    attackPowerStartInPlaceLeftHand
  (0x80F now also requires the left hand NOT to hold a one-handed weapon, so dual wielding uses 0x810.)
  0x803 CONT CTKD_Storage        empty, non-respawning chest (clone of a vanilla chest) for Serana's weapons
  --- Sakkai Fuhazan ki blasts (2026-10-14) ---
  0x808 PROJ CTKD_KiBlastProj      small purple ki blast: vanilla IllusionNeg01Projectile (dark Illusion orb + its
                                   purple light) with meshes/CTKD/kiblast_small.nif (that orb at 0.45x)
  0x809 PROJ CTKD_KiBlastBigProj   the giant last blast: meshes/CTKD/kiblast_big.nif (1.3x), slower
  0x80A MGEF CTKD_KiBlastDamage    damage health, aimed, small projectile
  0x80B MGEF CTKD_KiBlastBigDamage damage health, aimed, big projectile
  0x80C MGEF CTKD_KiBlastStagger   stagger, aimed, big projectile
  0x80D SPEL CTKD_KiBlastSpell     one small blast; 0x80E SPEL CTKD_KiBlastBigSpell: damage + stagger
  Both are cast by PayloadInterpreter annotations (PIE.@CAST) on Serana's Sakkai Fuhazan kicks
  (SF6 Juri/Base/mco_powerattack9.hkx), so they fire exactly on each kick.
Serana herself is found at runtime (Dawnguard.esm 0x2B74), so Dawnguard is not a master.
Helpers follow skyrim/six_paths_of_pain/tools/build_spp_esp.py (tested in game).
"""
import struct, sys, zlib

SKYRIM, OUT = sys.argv[1], sys.argv[2]
OWN = 1 << 24
FID = {n: OWN | (0x800 + i) for i, n in enumerate(
    ['CTKD_Quest', 'CTKD_ToggleEffect', 'CTKD_TogglePower', 'CTKD_Storage', 'CTKD_UnarmedPowerMult',
     'CTKD_JuriStyle', 'CTKD_SetMastery', 'CTKD_PlayerSkyFXPowerAttack',
     'CTKD_KiBlastProj', 'CTKD_KiBlastBigProj', 'CTKD_KiBlastDamage', 'CTKD_KiBlastBigDamage', 'CTKD_KiBlastStagger',
     'CTKD_KiBlastSpell', 'CTKD_KiBlastBigSpell', 'CTKD_PlayerWeaponPowerAttack',
     'CTKD_PlayerDualPowerAttack', 'CTKD_PlayerLeftPowerAttack'])}
KI_DAMAGE, KI_BIG_DAMAGE = 15.0, 60.0
PLAYER_REF, VOICE_SLOT = 0x00000014, 0x00025BEE

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
buf = open(SKYRIM, 'rb').read(); V = {}; chests = []
def walk(o, e):
    while o < e:
        t = buf[o:o+4].decode('latin1'); n = struct.unpack_from('<I', buf, o+4)[0]
        if t == 'GRUP': walk(o+24, o+n); o += n; continue
        fl, fid = struct.unpack_from('<II', buf, o+8); b = buf[o+24:o+24+n]; o += 24 + n
        if t == 'PROJ' and fid == 0x00074796: V['illusion_proj'] = list(subs_of(b)); continue
        if t not in ('MGEF', 'CONT'): continue
        if fl & 0x40000: b = zlib.decompress(b[4:])
        s = list(subs_of(b)); ed = dict(s).get('EDID', b'').rstrip(b'\0').decode('latin1')
        if ed == 'CWAbRegenEffect': V[ed] = s
        if t == 'CONT' and ed == 'PlayerHouseChest': V['chest'] = s
walk(24 + struct.unpack_from('<I', buf, 4)[0], len(buf))
assert 'CWAbRegenEffect' in V and 'chest' in V and 'illusion_proj' in V, sorted(V)

MDATA = bytearray(dict(V['CWAbRegenEffect'])['DATA'])
NO_DUR, NO_MAG, NO_AREA, HIDE_UI = 0x200, 0x400, 0x800, 0x8000
struct.pack_into('<I', MDATA, 0x00, NO_DUR | NO_MAG | NO_AREA)
struct.pack_into('<Ii', MDATA, 0x40, 1, -1)        # Script archetype, no actor value
struct.pack_into('<II', MDATA, 0x50, 1, 0)         # Fire and Forget, Self

mgef = rec('MGEF', FID['CTKD_ToggleEffect'], [
    sub('EDID', z('CTKD_ToggleEffect')),
    vmad([script('CTKD_ToggleEffect', [p_obj('Master', FID['CTKD_Quest'])])]),
    sub('FULL', z('Serana: Taekwondo Toggle')), sub('DATA', bytes(MDATA)), sub('SNDD', b''),
    sub('DNAM', z("Serana fights with the Leaf taijutsu Obito taught her, built around her flexibility and vampiric strength."))])

spel = rec('SPEL', FID['CTKD_TogglePower'], [
    sub('EDID', z('CTKD_TogglePower')), sub('OBND', bytes(12)), sub('FULL', z('Serana: Taekwondo Toggle')),
    sub('ETYP', u32(VOICE_SLOT)),
    sub('DESC', z("Centuries sealed away left Serana's magic as sharp as ever, perhaps sharper, but her martial training has dulled. Since meeting Obito, she has trained in the taijutsu of the Hidden Leaf. Reading her movements with his Sharingan, he shaped a style around her natural flexibility and vampiric strength, and she has made it her own. As always, practice makes perfect. Use to have her set her weapons aside and fight hand to hand, or to take them up again.")),
    sub('SPIT', u32(0, 1, 3) + f32(0.0) + u32(1, 0) + f32(0.0, 0.0) + u32(0)),   # Lesser Power, F&F, Self
    sub('EFID', u32(FID['CTKD_ToggleEffect'])), sub('EFIT', f32(0.0) + u32(0, 0))])

# chest: vanilla PlayerHouseChest minus its items, respawn flag cleared
csubs = []
for t, d in V['chest']:
    if t in ('CNTO', 'COCT', 'COED', 'VMAD'): continue
    if t == 'EDID': d = z('CTKD_Storage')
    elif t == 'FULL': d = z('Serana Weapon Storage')
    elif t == 'DATA': d = bytes([d[0] & ~0x02]) + d[1:]
    csubs.append(sub(t, d))
cont = rec('CONT', FID['CTKD_Storage'], csubs)

qust = rec('QUST', FID['CTKD_Quest'], [
    sub('EDID', z('CTKD_Quest')),
    vmad([script('CTKD_QuestScript', [p_obj('PlayerRef', PLAYER_REF), p_obj('TogglePower', FID['CTKD_TogglePower']),
                                      p_obj('StorageBase', FID['CTKD_Storage']),
                                      p_obj('PowerMult', FID['CTKD_UnarmedPowerMult']),
                                      p_obj('BrawlerStyle', FID['CTKD_JuriStyle']),
                                      p_obj('SetMasteryGlobal', FID['CTKD_SetMastery'])])], quest=True),
    sub('FULL', z('Serana Taekwondo Toggle')),
    sub('DNAM', struct.pack('<HBBII', 0x0011, 50, 0, 0, 0)),   # Start Game Enabled (+Run Once bit as in SPP), priority 50
    sub('NEXT', b''), sub('ANAM', u32(0))])

power_mult = rec('GLOB', FID['CTKD_UnarmedPowerMult'], [sub('EDID', z('CTKD_UnarmedPowerMult')), sub('FNAM', b'f'),
                                                         sub('FLTV', f32(3.0))])
# Juri Han: aggressive melee. Values follow vanilla csWEBrawler except where noted.
juri_style = rec('CSTY', FID['CTKD_JuriStyle'], [
    sub('EDID', z('CTKD_JuriStyle')),
    # offensive, defensive, group offensive | equipment weights: melee, magic, ranged, shout, unarmed, staff | avoid threat
    sub('CSGD', f32(0.95, 0.3, 0.8, 1.0, 0.5, 0.0, 0.0, 10.0, 0.0, 0.0)),   # brawler: .8 .5 .61 | 0 0 0 0 10 0 | .2
    sub('CSME', f32(1.0, 1.0, 1.0, 1.7, 1.5, 1.1, 1.1, 0.5)),
    sub('CSCR', f32(0.0, 0.0, 0.2, 0.2)),        # no circling, no falling back (brawler: .41 .35)
    sub('CSLR', f32(0.2)),
    sub('CSFL', f32(0.33, 1.0, 0.5, 0.5, 0.5, 0.5, 0.5, 0.75)),
    sub('DATA', u32(0))])
set_mastery = rec('GLOB', FID['CTKD_SetMastery'], [sub('EDID', z('CTKD_SetMastery')), sub('FNAM', b'f'),
                                                   sub('FLTV', f32(-1.0))])
GET_EQUIPPED_ITEM_TYPE = 597
def ctda_eq(fn, p1, value):
    return sub('CTDA', struct.pack('<B3xfHHIIIIi', 0x00, value, fn, 0, p1, 0, 0, 0, -1))
# subrecords as in SCAR's ADXP_NPCPowerAttack_H2H, minus its NPC-only conditions
power_idle = rec('IDLE', FID['CTKD_PlayerSkyFXPowerAttack'], [
    sub('EDID', z('CTKD_PlayerSkyFXPowerAttack')),
    ctda_eq(GET_EQUIPPED_ITEM_TYPE, 1, 0.0),    # right hand: fists
    ctda_eq(GET_EQUIPPED_ITEM_TYPE, 0, 0.0),    # left hand: fists
    sub('DNAM', z(r'Actors\Character\Behaviors\0_Master.hkx')),
    sub('ENAM', z('attackPowerStartForwardH2HRightHand')),
    sub('ANAM', bytes(8)), sub('DATA', bytes([0, 0, 1, 0, 0, 0]))])
# ---- Sakkai Fuhazan ki blasts ----
def ki_proj(name, full, model, speed):
    src = dict(V['illusion_proj']); data = bytearray(src['DATA'])
    struct.pack_into('<ff', data, 8, speed, 4000.0)                 # speed, range
    return rec('PROJ', FID[name], [sub('EDID', z(name)), sub('OBND', src['OBND']), sub('FULL', z(full)),
                                   sub('MODL', z(model)), sub('MODT', bytes.fromhex('020000000000000000000000')),
                                   sub('DATA', bytes(data)), sub('NAM1', src.get('NAM1', b'\0')),
                                   sub('VNAM', src.get('VNAM', u32(1)))])
projs = ki_proj('CTKD_KiBlastProj', 'Ki Blast', r'CTKD\kiblast_small.nif', 3000.0)
projs += ki_proj('CTKD_KiBlastBigProj', 'Ki Blast', r'CTKD\kiblast_big.nif', 2200.0)
MGEF_FID_OFFSETS = [0x08, 0x18, 0x20, 0x24, 0x48, 0x4C, 0x5C, 0x60, 0x64, 0x6C, 0x74, 0x78, 0x7C, 0x80, 0x84, 0x88]
HOSTILE, DETRIMENTAL, NO_HIT_EFFECT = 0x1, 0x4, 0x8000000
def ki_mgef(name, archetype, av, proj):
    d = bytearray(dict(V['CWAbRegenEffect'])['DATA'])
    for o in MGEF_FID_OFFSETS: struct.pack_into('<I', d, o, 0)
    struct.pack_into('<If', d, 0x00, HOSTILE | DETRIMENTAL | NO_DUR | NO_AREA, 0.0)
    struct.pack_into('<ii', d, 0x0C, -1, -1)                         # no magic skill, no resistance
    struct.pack_into('<Ii', d, 0x40, archetype, av)
    struct.pack_into('<I', d, 0x48, FID[proj])
    struct.pack_into('<II', d, 0x50, 1, 2)                           # Fire and Forget, Aimed
    return rec('MGEF', FID[name], [sub('EDID', z(name)), sub('FULL', z('Ki Blast')), sub('DATA', bytes(d)),
                                   sub('SNDD', b''), sub('DNAM', z(''))])
HEALTH = 24
ki_mgefs = (ki_mgef('CTKD_KiBlastDamage', 0, HEALTH, 'CTKD_KiBlastProj') + ki_mgef('CTKD_KiBlastBigDamage', 0, HEALTH, 'CTKD_KiBlastBigProj')
            + ki_mgef('CTKD_KiBlastStagger', 33, -1, 'CTKD_KiBlastBigProj'))
def ki_spel(name, effects):
    return rec('SPEL', FID[name], [sub('EDID', z(name)), sub('OBND', bytes(12)), sub('FULL', z('Ki Blast')),
        sub('SPIT', u32(0, 0x1 | 0x100000 | 0x200000, 0) + f32(0.0) + u32(1, 2) + f32(0.0, 0.0) + u32(0))]   # spell, manual cost 0, F&F, aimed
        + [sub('EFID', u32(FID[m])) + sub('EFIT', f32(mag) + u32(0, 0)) for m, mag in effects])
ki_spels = ki_spel('CTKD_KiBlastSpell', [('CTKD_KiBlastDamage', KI_DAMAGE)])
ki_spels += ki_spel('CTKD_KiBlastBigSpell', [('CTKD_KiBlastBigDamage', KI_BIG_DAMAGE), ('CTKD_KiBlastStagger', 1.0)])

def ctda_op(fn, p1, op, value):
    return sub('CTDA', struct.pack('<B3xfHHIIIIi', op, value, fn, 0, p1, 0, 0, 0, -1))
GE, LE, LT, GT, OR = 0x60, 0xA0, 0x80, 0x40, 0x01
RIGHT, LEFT = 1, 0                                  # GetEquippedItemType parameter: 1 = right hand, 0 = left hand
# item types: 0 fists, 1 sword, 2 dagger, 3 war axe, 4 mace, 5 greatsword, 6 battleaxe/warhammer, 7 bow, 8 staff,
# 9 spell, 10 shield, 11 torch, 12 crossbow
def player_power_idle(name, event, conds):
    return rec('IDLE', FID[name], [sub('EDID', z(name))] + conds + [
        sub('DNAM', z(r'Actors\Character\Behaviors\0_Master.hkx')), sub('ENAM', z(event)),
        sub('ANAM', bytes(8)), sub('DATA', bytes([0, 0, 1, 0, 0, 0]))])
weapon_power_idle = player_power_idle('CTKD_PlayerWeaponPowerAttack', 'attackPowerStartInPlace', [
    ctda_op(GET_EQUIPPED_ITEM_TYPE, RIGHT, GE, 1.0), ctda_op(GET_EQUIPPED_ITEM_TYPE, RIGHT, LE, 6.0),   # right: melee
    ctda_op(GET_EQUIPPED_ITEM_TYPE, LEFT, LT | OR, 1.0), ctda_op(GET_EQUIPPED_ITEM_TYPE, LEFT, GT, 4.0)])  # left: no 1H weapon
weapon_power_idle += player_power_idle('CTKD_PlayerDualPowerAttack', 'attackPowerStartDualWield', [
    ctda_op(GET_EQUIPPED_ITEM_TYPE, RIGHT, GE, 1.0), ctda_op(GET_EQUIPPED_ITEM_TYPE, RIGHT, LE, 4.0),   # right: 1H weapon
    ctda_op(GET_EQUIPPED_ITEM_TYPE, LEFT, GE, 1.0), ctda_op(GET_EQUIPPED_ITEM_TYPE, LEFT, LE, 4.0)])    # left: 1H weapon
weapon_power_idle += player_power_idle('CTKD_PlayerLeftPowerAttack', 'attackPowerStartInPlaceLeftHand', [
    ctda_op(GET_EQUIPPED_ITEM_TYPE, RIGHT, LT | OR, 1.0), ctda_op(GET_EQUIPPED_ITEM_TYPE, RIGHT, GT, 6.0),  # right: no melee
    ctda_op(GET_EQUIPPED_ITEM_TYPE, LEFT, GE, 1.0), ctda_op(GET_EQUIPPED_ITEM_TYPE, LEFT, LE, 4.0)])     # left: 1H weapon

groups = grup('GLOB', power_mult + set_mastery) + grup('CSTY', juri_style) + grup('MGEF', mgef + ki_mgefs) + grup('SPEL', spel + ki_spels) + grup('PROJ', projs) + grup('CONT', cont) + grup('QUST', qust) + grup('IDLE', power_idle + weapon_power_idle)
hdr = [sub('HEDR', f32(1.7) + u32(len(FID) + 6, 0x800 + len(FID))), sub('CNAM', z('Claude')),
       sub('SNAM', z('Serana Taekwondo Toggle')), sub('MAST', z('Skyrim.esm')), sub('DATA', bytes(8))]
open(OUT, 'wb').write(rec('TES4', 0, hdr, flags=0x200) + groups)
print('wrote', OUT)
for k, v in FID.items(): print(f'  {v:08X} {k}')
