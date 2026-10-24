r"""Hokage Obito Mode.esp (ESL, masters Skyrim + Update): the what-if Obito who became Hokage, for the player.

Stage 1 (2026-10-20): the mode, Sam's moveset on any one-handed sword (OAR, tools/make_sam_oar.py), Hiraishin kunai.
  0x800 QUST HKO_Quest          HKO_QuestScript (Start Game Enabled, no aliases)
  0x801 MGEF HKO_ToggleEffect   script HKO_ToggleEffect -> Master.Toggle()
  0x802 SPEL HKO_TogglePower    lesser power "Hokage"
  0x803 MGEF HKO_ModeMark       shown in Active Effects; THE OAR condition for the Sam moveset
  0x804 SPEL HKO_Mode           ability carrying it
  0x805 GLOB HKO_WarpMethod     warp test: 0 Uchiha Clan's way (controls off + MoveTo), 1 plain MoveTo, 2 = 0 + IdleForceDefaultState
  0x806 PROJ HKO_KunaiProj      arrow type, Naruto Overhaul's Iron Kunai model (meshes\\ironkunai.nif); data = Sharingan
                                Copy's Kamui shuriken projectile, slower, a little gravity
  0x807 MGEF HKO_KunaiDamage    damage health, aimed (copy of Sharingan Copy's shuriken damage, our projectile)
  0x808 MGEF HKO_SealMark       script HKO_SealEffect, aimed, 30 s, hit shader LifeDetectedEnemy (red outline through walls)
  0x809 SPEL HKO_KunaiSpell     kunai 12 + the seal
  0x80A MGEF HKO_WarpDamage     damage health, target actor
  0x80B MGEF HKO_WarpStagger    stagger, target actor
  0x80C SPEL HKO_WarpStrike     cast on the sealed enemy he lands behind: 15 + stagger
Stage 3 (2026-10-20): the Copy Wheel (H cycles Leaf -> Fire Release -> Copied). Leaf = no style mark (Sam).
  0x80D MGEF HKO_StyleFire      OAR/DAR condition: Kagutsuchi's EvilFire set (tools/make_style_oar.py)
  0x80E MGEF HKO_StyleCopied    OAR condition: Mitsunari's sets
  0x80F SPEL HKO_FireStyle      ability carrying 0x80D
  0x810 SPEL HKO_CopiedStyle    ability carrying 0x80E

Stage 3b (2026-10-20): the Copied blade, so the Copied style shows Mitsunari's iaido stance as he made it.
  0x811 WEAP HKO_CopiedBlade    copy of Mitsunari's Akaviri Dai-Katana override, his scabbard script pointed at the two
                                visible props below; the Copy Wheel equips it in Copied and swaps back
  0x812 ARMO HKO_CopiedScbHand  visible copy of Mitsunari's Blade_scb_hand (left-hand scabbard prop, slot 60)
  0x813 ARMO HKO_CopiedScbMouth visible copy of Blade_scb_Mouth (slot 59)
  0x814 ARMA HKO_CopiedScbHandA / 0x815 ARMA HKO_CopiedScbMouthA  (his own ARMAs stay blanked by
                                'Hokage - Hide Mitsunari Scabbards.esp' for every other katana)
  2026-10-23: blade + props use their own nifs (tools/make_copied_rigs.py, the author's custom-model process: own file
  names, model node names renamed); the Leaf / Fire Dai-Katana is not overridden (Mitsunari's record, plain model).
Masters now Skyrim, Update, KatanaCrafting (own records index 3).

usage: build_hko_esp.py <Skyrim.esm> <Sharingan Copy.esp> <MCO Ishida Mitsunari.esp> <out.esp>
"""
import struct, sys, zlib

SKYRIM, CSHC, MITSU, OUT = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
# the Copied blade + props: Mitsunari's rigs rebuilt by make_copied_rigs.py (own names, the author's process)
COPIED_BLADE = r'Weapons\HKOCopied\HKOCopiedKatana.nif'
COPIED_PROP = {'HKO_CopiedScbHandA': r'Weapons\HKOCopied\HKOCopiedKatanaHand.nif',
               'HKO_CopiedScbMouthA': r'Weapons\HKOCopied\HKOCopiedKatanaMouth.nif'}
OWN = 3 << 24          # masters: Skyrim.esm, Update.esm, KatanaCrafting.esp
NAMES = ['HKO_Quest', 'HKO_ToggleEffect', 'HKO_TogglePower', 'HKO_ModeMark', 'HKO_Mode', 'HKO_WarpMethod',
         'HKO_KunaiProj', 'HKO_KunaiDamage', 'HKO_SealMark', 'HKO_KunaiSpell', 'HKO_WarpDamage', 'HKO_WarpStagger',
         'HKO_WarpStrike', 'HKO_StyleFire', 'HKO_StyleCopied', 'HKO_FireStyle', 'HKO_CopiedStyle',
         'HKO_CopiedBlade', 'HKO_CopiedScbHand', 'HKO_CopiedScbMouth', 'HKO_CopiedScbHandA', 'HKO_CopiedScbMouthA']
FID = {n: OWN | (0x800 + i) for i, n in enumerate(NAMES)}
PLAYER_REF, VOICE_SLOT = 0x00000014, 0x00025BEE
LIFE_DETECTED_ENEMY = 0x000DC209


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
    if quest:
        out += bytes([2]) + struct.pack('<H', 0) + ws('') + struct.pack('<H', 0)    # no fragments, no aliases
    return sub('VMAD', out)
def subs_of(d):
    i = 0
    while i < len(d):
        t = d[i:i+4].decode('latin1'); n = struct.unpack_from('<H', d, i+4)[0]
        yield t, d[i+6:i+6+n]; i += 6 + n
def records(path, want):
    """{fid & 0xFFFFFF: [(sub, data)]} for the wanted (type, local id) pairs"""
    buf = open(path, 'rb').read(); got = {}
    def walk(o, e):
        while o < e:
            t = buf[o:o+4].decode('latin1'); n = struct.unpack_from('<I', buf, o+4)[0]
            if t == 'GRUP': walk(o+24, o+n); o += n; continue
            fl, fid = struct.unpack_from('<II', buf, o+8); b = buf[o+24:o+24+n]; o += 24 + n
            if (t, fid & 0xFFFFFF) in want:
                if fl & 0x40000: b = zlib.decompress(b[4:])
                got[(t, fid & 0xFFFFFF)] = list(subs_of(b))
    walk(24 + struct.unpack_from('<I', buf, 4)[0], len(buf))
    assert len(got) == len(want), (want, got.keys())
    return got


# MGEF DATA template (as the Ronin builder): vanilla CWAbRegenEffect, cleared
buf = open(SKYRIM, 'rb').read(); V = {}
def walk(o, e):
    while o < e:
        t = buf[o:o+4].decode('latin1'); n = struct.unpack_from('<I', buf, o+4)[0]
        if t == 'GRUP': walk(o+24, o+n); o += n; continue
        fl, fid = struct.unpack_from('<II', buf, o+8); b = buf[o+24:o+24+n]; o += 24 + n
        if t != 'MGEF': continue
        if fl & 0x40000: b = zlib.decompress(b[4:])
        s = list(subs_of(b))
        if dict(s).get('EDID', b'').rstrip(b'\0') == b'CWAbRegenEffect': V['regen'] = s
walk(24 + struct.unpack_from('<I', buf, 4)[0], len(buf))
del buf
MGEF_FID_OFFSETS = [0x08, 0x18, 0x20, 0x24, 0x48, 0x4C, 0x5C, 0x60, 0x64, 0x6C, 0x74, 0x78, 0x7C, 0x80, 0x84, 0x88]
HOSTILE, DETRIMENTAL, NO_DUR, NO_MAG, NO_AREA, HIDE_UI = 0x1, 0x4, 0x200, 0x400, 0x800, 0x8000
def mdata(archetype, av, cast, delivery, flags, hit_shader=0):
    d = bytearray(dict(V['regen'])['DATA'])
    for o in MGEF_FID_OFFSETS: struct.pack_into('<I', d, o, 0)
    struct.pack_into('<If', d, 0x00, flags, 0.0)
    struct.pack_into('<ii', d, 0x0C, -1, -1)
    struct.pack_into('<I', d, 0x20, hit_shader)
    struct.pack_into('<Ii', d, 0x40, archetype, av)
    struct.pack_into('<II', d, 0x50, cast, delivery)
    return bytes(d)

qust = rec('QUST', FID['HKO_Quest'], [
    sub('EDID', z('HKO_Quest')),
    vmad([script('HKO_QuestScript', [p_obj('PlayerRef', PLAYER_REF), p_obj('TogglePower', FID['HKO_TogglePower']),
                                      p_obj('ModeAbility', FID['HKO_Mode']), p_obj('KunaiSpell', FID['HKO_KunaiSpell']),
                                      p_obj('WarpStrike', FID['HKO_WarpStrike']),
                                      p_obj('WarpMethod', FID['HKO_WarpMethod']),
                                      p_obj('FireStyle', FID['HKO_FireStyle']),
                                      p_obj('CopiedStyle', FID['HKO_CopiedStyle']),
                                      p_obj('CopiedBlade', FID['HKO_CopiedBlade'])])], quest=True),
    sub('FULL', z('Hokage Obito')),
    sub('DNAM', struct.pack('<HBBII', 0x0011, 50, 0, 0, 0)),   # Start Game Enabled (no Run Once)
    sub('NEXT', b''), sub('ANAM', u32(0))])

toggle_fx = rec('MGEF', FID['HKO_ToggleEffect'], [
    sub('EDID', z('HKO_ToggleEffect')),
    vmad([script('HKO_ToggleEffect', [p_obj('Master', FID['HKO_Quest'])])]),
    sub('FULL', z('Hokage')), sub('DATA', mdata(1, -1, 1, 0, NO_DUR | NO_MAG | NO_AREA)), sub('SNDD', b''),
    sub('DNAM', z('The Hokage of the Hidden Leaf takes the field.'))])
DESC = ("He came back from under the rock in time. Rin lives, both his eyes are his own, and the Leaf calls him Hokage. "
        "He fights the way his teachers did: Minato's seals and space-time warps, Kakashi's eye for copying any style. "
        "Use to take up the Hokage's mantle, or to set it aside.")
toggle = rec('SPEL', FID['HKO_TogglePower'], [
    sub('EDID', z('HKO_TogglePower')), sub('OBND', bytes(12)), sub('FULL', z('Hokage')),
    sub('ETYP', u32(VOICE_SLOT)), sub('DESC', z(DESC)),
    sub('SPIT', u32(0, 1, 3) + f32(0.0) + u32(1, 0) + f32(0.0, 0.0) + u32(0)),   # Lesser Power, F&F, Self
    sub('EFID', u32(FID['HKO_ToggleEffect'])), sub('EFIT', f32(0.0) + u32(0, 0))])

mode_mark = rec('MGEF', FID['HKO_ModeMark'], [sub('EDID', z('HKO_ModeMark')), sub('FULL', z('Hokage')),
    sub('DATA', mdata(1, -1, 0, 0, NO_DUR | NO_MAG | NO_AREA)), sub('SNDD', b''),
    sub('DNAM', z('The Will of Fire: Leaf style with any two-handed blade, Hiraishin kunai at hand.'))])
mode = rec('SPEL', FID['HKO_Mode'], [sub('EDID', z('HKO_Mode')), sub('OBND', bytes(12)), sub('FULL', z('Hokage')),
    sub('SPIT', u32(0, 0, 4) + f32(0.0) + u32(0, 0) + f32(0.0, 0.0) + u32(0)),   # Ability, constant, self
    sub('EFID', u32(FID['HKO_ModeMark'])), sub('EFIT', f32(0.0) + u32(0, 0))])
warp_method = rec('GLOB', FID['HKO_WarpMethod'], [sub('EDID', z('HKO_WarpMethod')), sub('FNAM', b's'), sub('FLTV', f32(0.0))])

# ---- kunai: Sharingan Copy's Kamui shuriken projectile + damage (0x833 / 0x834), retargeted ----
src = records(CSHC, {('PROJ', 0x833), ('MGEF', 0x834)})
sp = dict(src[('PROJ', 0x833)])
pdata = bytearray(sp['DATA'])
struct.pack_into('<ff', pdata, 4, 0.15, 4200.0)          # gravity, speed (the shuriken: 0, 6000)
kunai_proj = rec('PROJ', FID['HKO_KunaiProj'], [
    sub('EDID', z('HKO_KunaiProj')), sub('OBND', sp['OBND']), sub('FULL', z('Kunai')),
    sub('MODL', z('ironkunai.nif')), sub('DATA', bytes(pdata)), sub('NAM1', sp['NAM1']), sub('VNAM', sp['VNAM'])])
sm = src[('MGEF', 0x834)]
dmg_subs = []
for t, d in sm:
    if t == 'EDID': d = z('HKO_KunaiDamage')
    elif t == 'FULL': d = z('Kunai')
    elif t == 'DATA':
        d = bytearray(d); struct.pack_into('<I', d, 0x48, FID['HKO_KunaiProj']); d = bytes(d)
    elif t == 'DNAM': d = z('A thrown kunai: <mag> damage.')
    dmg_subs.append(sub(t, d))
kunai_damage = rec('MGEF', FID['HKO_KunaiDamage'], dmg_subs)
seal_data = bytearray(mdata(1, -1, 1, 2, HOSTILE | NO_MAG | NO_AREA, hit_shader=LIFE_DETECTED_ENEMY))
struct.pack_into('<I', seal_data, 0x48, FID['HKO_KunaiProj'])
seal = rec('MGEF', FID['HKO_SealMark'], [sub('EDID', z('HKO_SealMark')),
    vmad([script('HKO_SealEffect', [p_obj('Master', FID['HKO_Quest'])])]),
    sub('FULL', z('Hiraishin Seal')), sub('DATA', bytes(seal_data)), sub('SNDD', b''),
    sub('DNAM', z('Marked by the Flying Raijin formula: the Hokage can be at your back in an instant.'))])
NO_RESIST_FLAGS = 0x1 | 0x100000 | 0x200000          # manual cost, no absorb/reflect... (as Ronin's script spells)
kunai_spell = rec('SPEL', FID['HKO_KunaiSpell'], [sub('EDID', z('HKO_KunaiSpell')), sub('OBND', bytes(12)),
    sub('FULL', z('Kunai')),
    sub('SPIT', u32(0, NO_RESIST_FLAGS, 0) + f32(0.0) + u32(1, 2) + f32(0.0, 0.0) + u32(0)),    # F&F, aimed
    sub('EFID', u32(FID['HKO_KunaiDamage'])), sub('EFIT', f32(12.0) + u32(0, 0)),
    sub('EFID', u32(FID['HKO_SealMark'])), sub('EFIT', f32(0.0) + u32(0, 30))])

warp_damage = rec('MGEF', FID['HKO_WarpDamage'], [sub('EDID', z('HKO_WarpDamage')), sub('FULL', z('Flying Raijin')),
    sub('DATA', mdata(0, 24, 1, 3, HOSTILE | DETRIMENTAL | NO_DUR | NO_AREA)), sub('SNDD', b''),
    sub('DNAM', z('He was already behind you: <mag> damage.'))])
warp_stagger = rec('MGEF', FID['HKO_WarpStagger'], [sub('EDID', z('HKO_WarpStagger')), sub('FULL', z('Flying Raijin')),
    sub('DATA', mdata(33, -1, 1, 3, HOSTILE | DETRIMENTAL | NO_DUR | NO_AREA | HIDE_UI)), sub('SNDD', b''), sub('DNAM', z(''))])
warp_strike = rec('SPEL', FID['HKO_WarpStrike'], [sub('EDID', z('HKO_WarpStrike')), sub('OBND', bytes(12)),
    sub('FULL', z('Flying Raijin')),
    sub('SPIT', u32(0, NO_RESIST_FLAGS, 0) + f32(0.0) + u32(1, 3) + f32(0.0, 0.0) + u32(0)),    # F&F, target actor
    sub('EFID', u32(FID['HKO_WarpDamage'])), sub('EFIT', f32(15.0) + u32(0, 0)),
    sub('EFID', u32(FID['HKO_WarpStagger'])), sub('EFIT', f32(1.0) + u32(0, 0))])

def style(mark, spell, full, desc):
    return (rec('MGEF', FID[mark], [sub('EDID', z(mark)), sub('FULL', z(full)),
                sub('DATA', mdata(1, -1, 0, 0, NO_DUR | NO_MAG | NO_AREA)), sub('SNDD', b''), sub('DNAM', z(desc))]),
            rec('SPEL', FID[spell], [sub('EDID', z(spell)), sub('OBND', bytes(12)), sub('FULL', z(full)),
                sub('SPIT', u32(0, 0, 4) + f32(0.0) + u32(0, 0) + f32(0.0, 0.0) + u32(0)),
                sub('EFID', u32(FID[mark])), sub('EFIT', f32(0.0) + u32(0, 0))]))
fire_m, fire_s = style('HKO_StyleFire', 'HKO_FireStyle', 'Copy Wheel: Fire Release',
                       'The Uchiha flame style, copied from the fire god Kagutsuchi: blazing directional strikes.')
copy_m, copy_s = style('HKO_StyleCopied', 'HKO_CopiedStyle', 'Copy Wheel: Copied',
                       "A rival's blade art read and copied by the Sharingan: quick draws, pursuit and aerial cuts.")
# ---- the Copied blade: Mitsunari's records, master indices remapped (his: 0 Skyrim .. 4 KatanaCrafting, 7 self) ----
MREMAP = {0: 0, 4: 2}
def remap(fid):
    if fid == 0: return 0
    return (MREMAP[fid >> 24] << 24) | (fid & 0xFFFFFF)
def remap_sub(v, offsets):
    v = bytearray(v)
    for o in offsets: struct.pack_into('<I', v, o, remap(struct.unpack_from('<I', v, o)[0]))
    return bytes(v)
ms = records(MITSU, {('WEAP', 0x18F), ('ARMO', 0x856), ('ARMO', 0x857), ('ARMA', 0x822), ('ARMA', 0x823)})
def arma(src, name):
    out = []
    for t, v in ms[src]:
        if t == 'EDID': v = z(name)
        elif t in ('RNAM', 'MODL'): v = remap_sub(v, [0])
        elif t in ('MOD2', 'MOD3', 'MOD4', 'MOD5'): v = z(COPIED_PROP[name])
        elif t in ('MO2T', 'MO3T', 'MO4T', 'MO5T'): continue
        out.append(sub(t, v))
    return rec('ARMA', FID[name], out, ver=39)
def armo(src, name, full, addon):
    out = []
    for t, v in ms[src]:
        if t == 'EDID': v = z(name)
        elif t == 'MODL': v = u32(FID[addon])
        elif t in ('RNAM', 'YNAM', 'ZNAM', 'EITM', 'ETYP', 'BIDS', 'BAMT', 'TNAM'): v = remap_sub(v, [0])
        elif t == 'KWDA': v = remap_sub(v, range(0, len(v), 4))
        out.append(sub(t, v))
    out.insert(1, sub('FULL', z(full)))
    return rec('ARMO', FID[name], out, flags=0x4)
scb_hand_a = arma(('ARMA', 0x822), 'HKO_CopiedScbHandA')
scb_mouth_a = arma(('ARMA', 0x823), 'HKO_CopiedScbMouthA')
scb_hand = armo(('ARMO', 0x856), 'HKO_CopiedScbHand', 'Copied Scabbard', 'HKO_CopiedScbHandA')
scb_mouth = armo(('ARMO', 0x857), 'HKO_CopiedScbMouth', 'Copied Scabbard', 'HKO_CopiedScbMouthA')
blade_subs = []
for t, v in ms[('WEAP', 0x18F)]:
    if t == 'EDID': v = z('HKO_CopiedBlade')
    elif t == 'VMAD':
        blade_subs.append(vmad([script('KatanaScarbbardScript', [p_obj('ScabbardHand', FID['HKO_CopiedScbHand']),
                                                                  p_obj('ScabbardMouth', FID['HKO_CopiedScbMouth'])])]))
        continue
    elif t == 'FULL': v = z('Akaviri Dai-Katana (Copied)')
    elif t == 'MODL': v = z(COPIED_BLADE)
    elif t == 'MODT': continue
    elif t in ('ETYP', 'BIDS', 'BAMT', 'INAM', 'WNAM', 'TNAM', 'NAM9', 'NAM8', 'SNAM', 'XNAM', 'UNAM', 'EITM', 'CNAM'):
        v = remap_sub(v, [0])
    elif t == 'KWDA': v = remap_sub(v, range(0, len(v), 4))
    blade_subs.append(sub(t, v))
copied_blade = rec('WEAP', FID['HKO_CopiedBlade'], blade_subs)

groups = (grup('GLOB', warp_method)
          + grup('MGEF', toggle_fx + mode_mark + kunai_damage + seal + warp_damage + warp_stagger + fire_m + copy_m)
          + grup('SPEL', toggle + mode + kunai_spell + warp_strike + fire_s + copy_s)
          + grup('PROJ', kunai_proj) + grup('QUST', qust)
          + grup('WEAP', copied_blade) + grup('ARMO', scb_hand + scb_mouth) + grup('ARMA', scb_hand_a + scb_mouth_a))
hdr = [sub('HEDR', f32(1.7) + u32(len(FID), 0x800 + len(FID))),
       sub('CNAM', z('Claude')),
       sub('SNAM', z('Hokage Obito Mode')), sub('MAST', z('Skyrim.esm')), sub('DATA', bytes(8)),
       sub('MAST', z('Update.esm')), sub('DATA', bytes(8)),
       sub('MAST', z('KatanaCrafting.esp')), sub('DATA', bytes(8))]
open(OUT, 'wb').write(rec('TES4', 0, hdr, flags=0x200) + groups)
print('wrote', OUT)
for k, v in FID.items(): print(f'  {v:08X} {k}')
