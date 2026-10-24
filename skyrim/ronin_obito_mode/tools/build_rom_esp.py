"""Ronin Obito Mode.esp (ESL): Obito Uchiha [Ronin], "the Wandering Ronin" (Naruto Mobile), for the player.

Phase 1 skeleton (2026-10-18), built before any moveset is chosen; the movesets hang off the stance abilities via OAR:
  0x800 QUST ROM_Quest             ROM_QuestScript (Start Game Enabled): the mode, stances, Ki, Ichishun, counter-slash;
                                   alias 0 = the player (ROM_PlayerAlias: the Vergil vanish -> Kamui teleports)
  0x801 MGEF ROM_ToggleEffect      script ROM_ToggleEffect -> Master.Toggle()
  0x802 SPEL ROM_TogglePower       lesser power "Ronin"
  0x803 MGEF ROM_SheathedMark      shown in Active Effects; the OAR condition for the sheathed moveset
  0x804 SPEL ROM_Sheathed          ability carrying it
  0x805 MGEF ROM_DrawnMark         the same for the drawn blade
  0x806 SPEL ROM_Drawn
  0x807 MGEF ROM_CutDamage         the delayed slash's damage (health, target actor, hostile)
  0x808 MGEF ROM_CutStagger        its large stagger
  0x809 SPEL ROM_DimensionCut      cast by the script on the countered enemy when the Kamui distortion tears
  0x80A GLOB ROM_TauntKey          phase 2: the taunt hotkey (DirectInput scan code, default 34 = G);
                                   'set ROM_TauntKey to <code>' in the console changes it
  0x80B MGEF ROM_TauntMark         while on him, OAR swaps his combat idle for the taunt in 'Ronin Obito/Taunt'
                                   (tools/make_taunt.py: VergilSDT's Devil Trigger power-up pose, 1.87 s, i-frames 1.5 s,
                                   its demon call made inert; earlier picks were 33 s and 8 s, far too long in a fight)
  0x80C SPEL ROM_TauntSpell        puts the mark on him for 2 s (the script removes it when he acts)
  0x80D GLOB ROM_FillResolve       test hook: 'set ROM_FillResolve to 1' in the console fills his resolve
  0x80E EXPL ROM_FlameBurst        copy of FireballStormImpactExplosionNoDamage, no push, small: the formation's flare
  0x80F MGEF ROM_FlameBurn         copy of FireDamageFFAimed with a duration, target actor: Uchiha fire
  0x810 SPEL ROM_FlameFormation    burn 8/s for 4 s + stagger (every 6th hit of a string)
  0x811 SPEL ROM_IssenSpell        25 damage + stagger on everyone the scabbard slam reaches
  0x812 MGEF ROM_IssenMark         while on him, OAR swaps his combat idle for the Issen draw in 'Ronin Obito/Issen'
                                   (the Yamato's Judgement Cut quick-draw, its MCO/SCAR calls made inert)
  0x813 SPEL ROM_IssenAnim         puts the mark on him for 2 s (the script removes it after the draw)
  0x814 ARMA ROM_KimonoAA          the Blades Samurai Shihanke kimono's body model (slots and races copied), male
                                   meshes = the purple copies in meshes/ROM/kimono (tools/make_kimono_meshes.py)
  0x815 ARMO ROM_Kimono            "Ronin Kimono": Kamui purple kimono, Uchiha crest on the back, black hakama

usage: build_rom_esp.py <Skyrim.esm> <out.esp>
"""
import struct, sys, zlib

SKYRIM, OUT = sys.argv[1], sys.argv[2]
OWN = 2 << 24          # masters: Skyrim.esm, Update.esm
NAMES = ['ROM_Quest', 'ROM_ToggleEffect', 'ROM_TogglePower', 'ROM_SheathedMark', 'ROM_Sheathed', 'ROM_DrawnMark',
         'ROM_Drawn', 'ROM_CutDamage', 'ROM_CutStagger', 'ROM_DimensionCut', 'ROM_TauntKey',
         'ROM_TauntMark', 'ROM_TauntSpell', 'ROM_FillResolve',
         'ROM_FlameBurst', 'ROM_FlameBurn', 'ROM_FlameFormation', 'ROM_IssenSpell',
         'ROM_IssenMark', 'ROM_IssenAnim', 'ROM_KimonoAA', 'ROM_Kimono']
FID = {n: OWN | (0x800 + i) for i, n in enumerate(NAMES)}
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
def vmad(scripts, quest=False, aliases=()):
    out = struct.pack('<hhH', 5, 2, len(scripts)) + b''.join(scripts)
    if quest:
        # fragment section (none), then the alias scripts: object (unused, alias id, quest), version, format, scripts
        out += bytes([2]) + struct.pack('<H', 0) + ws('') + struct.pack('<H', len(aliases))
        for alias_id, quest_fid, alias_scripts in aliases:
            out += struct.pack('<hhIhhH', 0, alias_id, quest_fid, 5, 2, len(alias_scripts)) + b''.join(alias_scripts)
    return sub('VMAD', out)
def subs_of(d):
    i = 0
    while i < len(d):
        t = d[i:i+4].decode('latin1'); n = struct.unpack_from('<H', d, i+4)[0]
        yield t, d[i+6:i+6+n]; i += 6 + n


# MGEF DATA template (as the Ninja Mode builder): vanilla CWAbRegenEffect, cleared
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
MGEF_FID_OFFSETS = [0x08, 0x18, 0x20, 0x24, 0x48, 0x4C, 0x5C, 0x60, 0x64, 0x6C, 0x74, 0x78, 0x7C, 0x80, 0x84, 0x88]
HOSTILE, DETRIMENTAL, NO_DUR, NO_MAG, NO_AREA, HIDE_UI = 0x1, 0x4, 0x200, 0x400, 0x800, 0x8000
def mdata(archetype, av, cast, delivery, flags):
    d = bytearray(dict(V['regen'])['DATA'])
    for o in MGEF_FID_OFFSETS: struct.pack_into('<I', d, o, 0)
    struct.pack_into('<If', d, 0x00, flags, 0.0)
    struct.pack_into('<ii', d, 0x0C, -1, -1)
    struct.pack_into('<Ii', d, 0x40, archetype, av)
    struct.pack_into('<II', d, 0x50, cast, delivery)
    return bytes(d)

qust = rec('QUST', FID['ROM_Quest'], [
    sub('EDID', z('ROM_Quest')),
    vmad([script('ROM_QuestScript', [p_obj('PlayerRef', PLAYER_REF), p_obj('TogglePower', FID['ROM_TogglePower']),
                                      p_obj('SheathedAbility', FID['ROM_Sheathed']), p_obj('DrawnAbility', FID['ROM_Drawn']),
                                      p_obj('DimensionCut', FID['ROM_DimensionCut']),
                                      p_obj('TauntKey', FID['ROM_TauntKey']),
                                      p_obj('TauntSpell', FID['ROM_TauntSpell']),
                                      p_obj('FillResolve', FID['ROM_FillResolve'])])], quest=True,
         aliases=[(0, FID['ROM_Quest'], [script('ROM_PlayerAlias', [])])]),
    sub('FULL', z('Ronin Obito')),
    sub('DNAM', struct.pack('<HBBII', 0x0011, 50, 0, 0, 0)),   # Start Game Enabled
    sub('NEXT', b''), sub('ANAM', u32(1)),
    # alias 0 = the player (forced): ROM_PlayerAlias hears the Vergil vanish spell land (Kamui teleports)
    sub('ALST', u32(0)), sub('ALID', z('Player')), sub('FNAM', u32(0)), sub('ALFR', u32(PLAYER_REF)), sub('ALED', b'')])

toggle_fx = rec('MGEF', FID['ROM_ToggleEffect'], [
    sub('EDID', z('ROM_ToggleEffect')),
    vmad([script('ROM_ToggleEffect', [p_obj('Master', FID['ROM_Quest'])])]),
    sub('FULL', z('Ronin')), sub('DATA', mdata(1, -1, 1, 0, NO_DUR | NO_MAG | NO_AREA)), sub('SNDD', b''),
    sub('DNAM', z('The wandering ronin draws breath and lays a hand on his sword.'))])
DESC = ("No village, no war, no Moon's Eye. Only the road, a blade at his hip and the eye that sees through every "
        "dimension. Obito walks as a ronin: his sword stays sheathed until it must not, his Kamui turns every blow "
        "into empty air. Use to take up the ronin's way, or to set it down.")
toggle = rec('SPEL', FID['ROM_TogglePower'], [
    sub('EDID', z('ROM_TogglePower')), sub('OBND', bytes(12)), sub('FULL', z('Ronin')),
    sub('ETYP', u32(VOICE_SLOT)), sub('DESC', z(DESC)),
    sub('SPIT', u32(0, 1, 3) + f32(0.0) + u32(1, 0) + f32(0.0, 0.0) + u32(0)),   # Lesser Power, F&F, Self
    sub('EFID', u32(FID['ROM_ToggleEffect'])), sub('EFIT', f32(0.0) + u32(0, 0))])

def mark(name, full, desc):
    return rec('MGEF', FID[name], [sub('EDID', z(name)), sub('FULL', z(full)),
        sub('DATA', mdata(1, -1, 0, 0, NO_DUR | NO_MAG | NO_AREA)), sub('SNDD', b''), sub('DNAM', z(desc))])
def ability(name, full, effect):
    return rec('SPEL', FID[name], [sub('EDID', z(name)), sub('OBND', bytes(12)), sub('FULL', z(full)),
        sub('SPIT', u32(0, 0, 4) + f32(0.0) + u32(0, 0) + f32(0.0, 0.0) + u32(0)),   # Ability, constant, self
        sub('EFID', u32(FID[effect])), sub('EFIT', f32(0.0) + u32(0, 0))])
marks = (mark('ROM_SheathedMark', 'Ronin: Sheathed', 'The blade rests in its scabbard. A parry answers with a cut '
              'that lands a moment later.')
         + mark('ROM_DrawnMark', 'Ronin: Drawn', 'The blade is out: his cuts bite deeper, and a Kamui that lets a '
                'blow pass through restores his chakra.'))
abilities = ability('ROM_Sheathed', 'Ronin: Sheathed', 'ROM_SheathedMark') + ability('ROM_Drawn', 'Ronin: Drawn', 'ROM_DrawnMark')

cut_damage = rec('MGEF', FID['ROM_CutDamage'], [sub('EDID', z('ROM_CutDamage')), sub('FULL', z('Dimension Cut')),
    sub('DATA', mdata(0, 24, 1, 3, HOSTILE | DETRIMENTAL | NO_DUR | NO_AREA)), sub('SNDD', b''),
    sub('DNAM', z('A cut that opens a moment after the blade has passed: <mag> damage.'))])
cut_stagger = rec('MGEF', FID['ROM_CutStagger'], [sub('EDID', z('ROM_CutStagger')), sub('FULL', z('Dimension Cut')),
    sub('DATA', mdata(33, -1, 1, 3, HOSTILE | DETRIMENTAL | NO_DUR | NO_AREA | HIDE_UI)), sub('SNDD', b''), sub('DNAM', z(''))])
cut = rec('SPEL', FID['ROM_DimensionCut'], [sub('EDID', z('ROM_DimensionCut')), sub('OBND', bytes(12)),
    sub('FULL', z('Dimension Cut')),
    sub('SPIT', u32(0, 0x1 | 0x100000 | 0x200000, 0) + f32(0.0) + u32(1, 3) + f32(0.0, 0.0) + u32(0)),   # F&F, target actor
    sub('EFID', u32(FID['ROM_CutDamage'])), sub('EFIT', f32(60.0) + u32(0, 0)),
    sub('EFID', u32(FID['ROM_CutStagger'])), sub('EFIT', f32(1.0) + u32(0, 0))])

taunt_mark = rec('MGEF', FID['ROM_TauntMark'], [sub('EDID', z('ROM_TauntMark')), sub('FULL', z('Ronin: Taunt')),
    sub('DATA', mdata(1, -1, 1, 0, NO_MAG | NO_AREA | HIDE_UI)), sub('SNDD', b''), sub('DNAM', z(''))])
taunt_spell = rec('SPEL', FID['ROM_TauntSpell'], [sub('EDID', z('ROM_TauntSpell')), sub('OBND', bytes(12)),
    sub('FULL', z('Ronin: Taunt')),
    sub('SPIT', u32(0, 0x1 | 0x100000 | 0x200000, 0) + f32(0.0) + u32(1, 0) + f32(0.0, 0.0) + u32(0)),    # F&F, self
    sub('EFID', u32(FID['ROM_TauntMark'])), sub('EFIT', f32(0.0) + u32(0, 2))])
issen_mark = rec('MGEF', FID['ROM_IssenMark'], [sub('EDID', z('ROM_IssenMark')), sub('FULL', z('Ronin: Issen')),
    sub('DATA', mdata(1, -1, 1, 0, NO_MAG | NO_AREA | HIDE_UI)), sub('SNDD', b''), sub('DNAM', z(''))])
issen_anim = rec('SPEL', FID['ROM_IssenAnim'], [sub('EDID', z('ROM_IssenAnim')), sub('OBND', bytes(12)),
    sub('FULL', z('Ronin: Issen')),
    sub('SPIT', u32(0, 0x1 | 0x100000 | 0x200000, 0) + f32(0.0) + u32(1, 0) + f32(0.0, 0.0) + u32(0)),    # F&F, self
    sub('EFID', u32(FID['ROM_IssenMark'])), sub('EFIT', f32(0.0) + u32(0, 2))])
# the Blades kimono's additional races (all Skyrim.esm / Dawnguard-free vanilla races and their vampire versions)
KIMONO_RACES = [0x013740, 0x08883A, 0x013741, 0x08883C, 0x097A3D, 0x013742, 0x08883D, 0x067CD8, 0x0A82BA, 0x013743,
                0x088840, 0x013744, 0x088844, 0x013745, 0x088845, 0x10760A, 0x013746, 0x088794, 0x013747, 0x0A82B9,
                0x013748, 0x088846, 0x013749, 0x088884]
kimono_aa = rec('ARMA', FID['ROM_KimonoAA'], [sub('EDID', z('ROM_KimonoAA')),
    sub('BOD2', u32(0x114, 2)), sub('RNAM', u32(0x19)), sub('DNAM', bytes.fromhex('0f0f020200000018cdcccc3d')),
    sub('MOD2', z(r'ROM\kimono\kimono_1.nif')), sub('MOD3', z(r'clothes\kimono\kimono_f_1.nif')),
    sub('MOD4', z(r'ROM\kimono\1stpersonkimono_1.nif'))] + [sub('MODL', u32(r)) for r in KIMONO_RACES])
kimono = rec('ARMO', FID['ROM_Kimono'], [sub('EDID', z('ROM_Kimono')), sub('OBND', bytes(12)),
    sub('FULL', z('Ronin Kimono')), sub('MOD2', z(r'ROM\kimono\kimono_gnd.nif')),
    sub('BOD2', u32(0x4, 2)), sub('YNAM', u32(0x03E879)), sub('ZNAM', u32(0x03E909)), sub('RNAM', u32(0x19)),
    sub('KSIZ', u32(3)), sub('KWDA', u32(0x06BBE8, 0x08F95B, 0x0A8657)), sub('DESC', b'\0'),
    sub('MODL', u32(FID['ROM_KimonoAA'])), sub('DATA', u32(250) + f32(1.0)), sub('DNAM', u32(0))])
taunt_key = rec('GLOB', FID['ROM_TauntKey'], [sub('EDID', z('ROM_TauntKey')), sub('FNAM', b's'), sub('FLTV', f32(34.0))])
fill_resolve = rec('GLOB', FID['ROM_FillResolve'], [sub('EDID', z('ROM_FillResolve')), sub('FNAM', b's'), sub('FLTV', f32(0.0))])
# ---- skills (2026-10-19): Uchiha Flame Formation, Issen ----
# vanilla sources (Skyrim.esm is form version 39/40 for EXPL: drop MODT and EITM, the Gokakyu crash lesson)
VS = {}
def vwalk(o, e):
    while o < e:
        t = buf[o:o+4].decode('latin1'); n = struct.unpack_from('<I', buf, o+4)[0]
        if t == 'GRUP': vwalk(o+24, o+n); o += n; continue
        fl, fid = struct.unpack_from('<II', buf, o+8); b = buf[o+24:o+24+n]; o += 24 + n
        if fid in (0x000EA517, 0x00012F03):
            if fl & 0x40000: b = zlib.decompress(b[4:])
            VS[fid] = list(subs_of(b))
vwalk(24 + struct.unpack_from('<I', buf, 4)[0], len(buf))
burst_subs = []
for t, d in VS[0x000EA517]:                     # FireballStormImpactExplosionNoDamage
    if t in ('MODT', 'EITM'): continue
    if t == 'EDID': d = z('ROM_FlameBurst')
    elif t == 'DATA':
        d = bytearray(d); struct.pack_into('<f', d, 24, 0.0); struct.pack_into('<f', d, 32, 180.0); d = bytes(d)    # no push; small
    burst_subs.append(sub(t, d))
flame_burst = rec('EXPL', FID['ROM_FlameBurst'], burst_subs)
burn_subs = []
for t, d in VS[0x00012F03]:                     # FireDamageFFAimed: fire damage, burning hit shader, fire keyword
    if t == 'EDID': d = z('ROM_FlameBurn')
    elif t == 'FULL': d = z('Uchiha Flame Formation')
    elif t == 'DNAM': d = z('Uchiha fire: <mag> damage per second for <dur> seconds.')
    elif t == 'DATA':
        d = bytearray(d)
        struct.pack_into('<I', d, 0x00, struct.unpack_from('<I', d, 0x00)[0] & ~NO_DUR)
        struct.pack_into('<II', d, 0x48, 0, 0)           # no projectile, no explosion: the script places the burst
        struct.pack_into('<II', d, 0x50, 1, 3)           # fire and forget, target actor
        d = bytes(d)
    burn_subs.append(sub(t, d))
flame_burn = rec('MGEF', FID['ROM_FlameBurn'], burn_subs)
def target_spell(name, full, effects):
    return rec('SPEL', FID[name], [sub('EDID', z(name)), sub('OBND', bytes(12)), sub('FULL', z(full)),
        sub('SPIT', u32(0, 0x1 | 0x100000 | 0x200000, 0) + f32(0.0) + u32(1, 3) + f32(0.0, 0.0) + u32(0))]
        + [sub('EFID', u32(FID[m])) + sub('EFIT', f32(mag) + u32(0, dur)) for m, mag, dur in effects])
flame_spell = target_spell('ROM_FlameFormation', 'Uchiha Flame Formation', [('ROM_FlameBurn', 8.0, 4), ('ROM_CutStagger', 1.0, 0)])
issen_spell = target_spell('ROM_IssenSpell', 'Issen', [('ROM_CutDamage', 25.0, 0), ('ROM_CutStagger', 1.0, 0)])
groups = (grup('GLOB', taunt_key + fill_resolve) + grup('EXPL', flame_burst) + grup('MGEF', flame_burn + taunt_mark + issen_mark + toggle_fx + marks + cut_damage + cut_stagger) + grup('SPEL', flame_spell + issen_spell + issen_anim + taunt_spell + toggle + abilities + cut)
          + grup('ARMO', kimono) + grup('QUST', qust) + grup('ARMA', kimono_aa))
hdr = [sub('HEDR', f32(1.7) + u32(len(FID), 0x800 + len(FID))), sub('CNAM', z('Claude')),
       sub('SNAM', z('Ronin Obito Mode')), sub('MAST', z('Skyrim.esm')), sub('DATA', bytes(8)),
       sub('MAST', z('Update.esm')), sub('DATA', bytes(8))]
open(OUT, 'wb').write(rec('TES4', 0, hdr, flags=0x200) + groups)
print('wrote', OUT)
for k, v in FID.items(): print(f'  {v:08X} {k}')
