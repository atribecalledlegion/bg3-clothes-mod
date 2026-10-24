"""Build Serana Ninja Mode.esp (ESL, master Skyrim.esm only).

Usage: build_snj_esp.py <Skyrim.esm> <out.esp> <naruto overhaul.esp>

Masters: Skyrim.esm, Update.esm, naruto overhaul.esp (2026-10-17, for the Chidori kit). naruto overhaul.esp has the
same first two masters, so its records copied here keep their form IDs as they are (index 02 in both files).

Records (append-only object IDs, saves reference them):
  0x800 QUST SNJ_Quest           Start Game Enabled, script SNJ_QuestScript (gives the power on start)
  0x801 MGEF SNJ_ToggleEffect    Script archetype, Fire and Forget, Self, script SNJ_ToggleEffect
  0x802 SPEL SNJ_TogglePower     Lesser Power "Serana: Way of the Shinobi"
  0x803 CONT SNJ_Storage         empty, non-respawning chest for Serana's other weapons while she wields the Kusanagi
  0x804 CSTY SNJ_ShinobiStyle    aggressive swordswoman who flanks; lightning from range (driven by the script)
  0x805 GLOB SNJ_SetMastery      test hook: 'set SNJ_SetMastery to <0-100>' sets her Ninja Mastery (-1 = idle)
  0x806-0x80A MGEF SNJ_Tier1..5  hidden markers; the OAR tier folders (tools/make_oar.py) check for them
  0x80B-0x80F SPEL SNJ_TierAbility1..5  abilities carrying those markers (the script gives exactly one)
  --- Chidori kit (copies of naruto overhaul.esp's Chidori effects, fire-and-forget so her moveset can cast them) ---
  0x810 MGEF SNJ_ChidoriCharge     her hand crackles (copy of A0FXChidoriBodyHolder, timed, with the Chidori sounds)
  0x811 MGEF SNJ_ChidoriShock      copy of A0Chidori1 (close-range strike, Resist Shock, health + magicka)
  0x812 MGEF SNJ_EisoShock         copy of A0ChidoriEisoueffect1 (the lightning spear beam, range 1200)
  0x813 MGEF SNJ_KirinShock        copy of A0KirinBoltEffect (the Kirin beam + explosion)
  0x814 MGEF SNJ_JutsuStagger      stagger rider for Chidori and Kirin
  0x815 MGEF SNJ_KirinCallEffect   script SNJ_KirinCallEffect: calls Kirin down from the sky onto her target
  0x816 SPEL SNJ_ChidoriChargeSpell  0x817 SNJ_ChidoriSpell  0x818 SNJ_KatanaSpell  0x819 SNJ_EisoSpell
  0x81A SPEL SNJ_SenbonSpell         0x81B SNJ_KirinSpell    0x81C SNJ_KirinCallSpell
  0x81D EXPL SNJ_NagashiBurst      copy of A0ChidoriNagashiExplosion with NO physics push (force 128 -> 0): the push
                                   in a narrow ruin full of automaton ragdolls is a likely Havok crash (2026-10-18)
  0x81E MGEF SNJ_NagashiShock      copy of A0ChidoriNagashi4, exploding with SNJ_NagashiBurst
  0x81F SPEL SNJ_NagashiSpell      fire-and-forget, self
  --- Mangekyo (2026-10-18; tier 5, mastery 80) ---
  0x820 MGEF SNJ_BlackFrostBurn    frost from the blood outward: health damage over time, no resistance (it never thaws)
  0x821 MGEF SNJ_MSParalysis       paralysis (the frost seizes the blood / the stasis / the Soul Cairn genjutsu)
  0x822 MGEF SNJ_BlackFrostSpread  script SNJ_BlackFrostEffect: frost shader, spreads to enemies beside the victim
  0x823 SPEL SNJ_BlackFrostSpell   left eye: burn 10/s 12 s + paralysis 2 s + spread
  0x824 MGEF SNJ_DimhollowEffect   script SNJ_DimhollowEffect: the right eye's seal (shatter / stasis / protect)
  0x825 SPEL SNJ_DimhollowSpell    right eye
  0x826 SPEL SNJ_StasisParalysis   6 s, for the stasis seal
  0x827 SPEL SNJ_SoulCairnParalysis 4 s, the Mangekyo genjutsu
  0x828 PROJ SNJ_GokakyuProj       copy of A0FireBallJutsuProjectile1 with the frost mesh (meshes/SNJ/HyotonGokakyu.nif,
                                   tools/make_gokakyu_nif.py) and Ice Spike's light
  0x829 EXPL SNJ_GokakyuBurst      copy of ExplosionRuneFrost01, NO physics push (force 128 -> 0, the Nagashi crash lesson)
  0x82A MGEF SNJ_GokakyuFrost      copy of FrostDamageFFAimed (frost damage + stamina), on the Gokakyu projectile + burst
  0x82B SPEL SNJ_GokakyuSpell      Hyoton: Gokakyu no Jutsu: frost 55 + slow 50% 3 s + stagger, 15 ft area (breathed out
                                   by the script with the shout animation)
  0x82C ARMA SNJ_RibcageAA         The Uchiha Clan's Sasuke Susanoo ribcage, recoloured black ice (tools/make_susanoo_assets.py),
                                   slot 51 (as the original)
  0x82D ARMA SNJ_RibcageParticlesAA its particles, slot 50
  0x82E ARMO SNJ_Ribcage           non-playable: her flash Susanoo (mastery 55), worn for a moment by the script
  0x82F EXPL SNJ_EisoBurst         copy of ExplosionShockMass01, NO physics push (128 -> 0)
  0x830 PROJ SNJ_EisoProj          copy of A0ChidoriEisouProjectile, exploding with SNJ_EisoBurst
  0x831 EXPL SNJ_KirinBurst        copy of A0KirinExplosion, NO physics push (128 -> 0)
  0x832 PROJ SNJ_KirinProj         copy of A0KirinProjectile, exploding with SNJ_KirinBurst
                                   (the game froze 2026-10-18 in a Taka fight full of Eiso pushes on Black Frost-
                                   paralysed, ragdolled bandits; the Nagashi crash lesson again)
  0x833 PROJ SNJ_SusanooArrowProj  her spectral bow's arrow (mastery 65): Ice Spike's missile with The Uchiha Clan's Sasuke
                                   Susanoo arrow in black ice (meshes/SNJ/susanoo/arrow.nif), fast, no explosion
  0x834 MGEF SNJ_SusanooArrowFrost copy of FrostDamageFFAimed on that projectile
  0x835 SPEL SNJ_SusanooArrowSpell frost 90 + slow 50% 3 s + stagger (cast by the script as the bow forms)
Serana, the Kusanagi (naruto overhaul.esp) and her jutsu are found at runtime, so none of those is a master.
Same layout and helpers as witch_of_the_wilds/tools/build_wotw_esp.py.
"""
import struct, sys, zlib

SKYRIM, OUT, NARUTO = sys.argv[1], sys.argv[2], sys.argv[3]
OWN = 3 << 24          # masters: Skyrim.esm, Update.esm, naruto overhaul.esp
NAMES = ['SNJ_Quest', 'SNJ_ToggleEffect', 'SNJ_TogglePower', 'SNJ_Storage', 'SNJ_ShinobiStyle', 'SNJ_SetMastery']
NAMES += ['SNJ_Tier%d' % i for i in range(1, 6)] + ['SNJ_TierAbility%d' % i for i in range(1, 6)]
NAMES += ['SNJ_ChidoriCharge', 'SNJ_ChidoriShock', 'SNJ_EisoShock', 'SNJ_KirinShock', 'SNJ_JutsuStagger',
          'SNJ_KirinCallEffect', 'SNJ_ChidoriChargeSpell', 'SNJ_ChidoriSpell', 'SNJ_KatanaSpell', 'SNJ_EisoSpell',
          'SNJ_SenbonSpell', 'SNJ_KirinSpell', 'SNJ_KirinCallSpell',
          'SNJ_NagashiBurst', 'SNJ_NagashiShock', 'SNJ_NagashiSpell',
          'SNJ_BlackFrostBurn', 'SNJ_MSParalysis', 'SNJ_BlackFrostSpread', 'SNJ_BlackFrostSpell',
          'SNJ_DimhollowEffect', 'SNJ_DimhollowSpell', 'SNJ_StasisParalysis', 'SNJ_SoulCairnParalysis',
          'SNJ_GokakyuProj', 'SNJ_GokakyuBurst', 'SNJ_GokakyuFrost', 'SNJ_GokakyuSpell',
          'SNJ_RibcageAA', 'SNJ_RibcageParticlesAA', 'SNJ_Ribcage',
          'SNJ_EisoBurst', 'SNJ_EisoProj', 'SNJ_KirinBurst', 'SNJ_KirinProj',
          'SNJ_SusanooArrowProj', 'SNJ_SusanooArrowFrost', 'SNJ_SusanooArrowSpell']
FID = {n: OWN | (0x800 + i) for i, n in enumerate(NAMES)}
assert FID['SNJ_Tier1'] == OWN | 0x806 and FID['SNJ_TierAbility1'] == OWN | 0x80B
PLAYER_REF, VOICE_SLOT = 0x00000014, 0x00025BEE
TIER_NAMES = ['Genin', 'One Tomoe', 'Two Tomoe', 'Three Tomoe', 'Awakened']

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
        if t not in ('MGEF', 'CONT', 'EXPL', 'PROJ'): continue
        if fl & 0x40000: b = zlib.decompress(b[4:])
        s = list(subs_of(b)); ed = dict(s).get('EDID', b'').rstrip(b'\0').decode('latin1')
        if ed == 'CWAbRegenEffect': V[ed] = s
        if fid in (0x00044089, 0x0001CEA2, 0x0002F774, 0x000D13E8): V[fid] = s    # frost rune burst, frost damage, ice spike proj
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

mgef = rec('MGEF', FID['SNJ_ToggleEffect'], [
    sub('EDID', z('SNJ_ToggleEffect')),
    vmad([script('SNJ_ToggleEffect', [p_obj('Master', FID['SNJ_Quest'])])]),
    sub('FULL', z('Serana: Way of the Shinobi')), sub('DATA', mdata(1, 0, NO_DUR | NO_MAG | NO_AREA)), sub('SNDD', b''),
    sub('DNAM', z("Serana draws the Kusanagi and fights as a shinobi of the Leaf: blade, lightning and frost."))])

DESC = ("Obito never asked her to fight like an Uchiha. She chose it. Serana trains the way the Leaf trains its "
        "shinobi: the Kusanagi in her hand, lightning in her blade, and frost where an Uchiha would breathe fire. "
        "Fire was never hers; it is the one thing that can still burn her. The harder she trains, the sharper her "
        "eyes become, until one day they see everything. Use to have her draw the Kusanagi, or to sheathe it.")
spel = rec('SPEL', FID['SNJ_TogglePower'], [
    sub('EDID', z('SNJ_TogglePower')), sub('OBND', bytes(12)), sub('FULL', z('Serana: Way of the Shinobi')),
    sub('ETYP', u32(VOICE_SLOT)), sub('DESC', z(DESC)),
    sub('SPIT', u32(0, 1, 3) + f32(0.0) + u32(1, 0) + f32(0.0, 0.0) + u32(0)),   # Lesser Power, F&F, Self
    sub('EFID', u32(FID['SNJ_ToggleEffect'])), sub('EFIT', f32(0.0) + u32(0, 0))])

# tier markers: hidden constant effects on self, carried by abilities
tier_mgefs = b''; tier_spels = b''
for i in range(1, 6):
    tier_mgefs += rec('MGEF', FID['SNJ_Tier%d' % i], [
        sub('EDID', z('SNJ_Tier%d' % i)), sub('FULL', z('Shinobi: %s' % TIER_NAMES[i-1])),
        sub('DATA', mdata(0, 0, NO_DUR | NO_MAG | NO_AREA | HIDE_UI)), sub('SNDD', b''), sub('DNAM', z(''))])
    tier_spels += rec('SPEL', FID['SNJ_TierAbility%d' % i], [
        sub('EDID', z('SNJ_TierAbility%d' % i)), sub('OBND', bytes(12)),
        sub('FULL', z('Shinobi: %s' % TIER_NAMES[i-1])),
        sub('SPIT', u32(0, 0, 4) + f32(0.0) + u32(0, 0) + f32(0.0, 0.0) + u32(0)),   # Ability, constant, self
        sub('EFID', u32(FID['SNJ_Tier%d' % i])), sub('EFIT', f32(0.0) + u32(0, 0))])

# chest: vanilla PlayerHouseChest minus its items, respawn flag cleared
csubs = []
for t, d in V['chest']:
    if t in ('CNTO', 'COCT', 'COED', 'VMAD'): continue
    if t == 'EDID': d = z('SNJ_Storage')
    elif t == 'FULL': d = z('Serana Weapon Storage')
    elif t == 'DATA': d = bytes([d[0] & ~0x02]) + d[1:]
    csubs.append(sub(t, d))
cont = rec('CONT', FID['SNJ_Storage'], csubs)

qust = rec('QUST', FID['SNJ_Quest'], [
    sub('EDID', z('SNJ_Quest')),
    vmad([script('SNJ_QuestScript', [p_obj('PlayerRef', PLAYER_REF), p_obj('TogglePower', FID['SNJ_TogglePower']),
                                      p_obj('StorageBase', FID['SNJ_Storage']),
                                      p_obj('ShinobiStyle', FID['SNJ_ShinobiStyle']),
                                      p_obj('SetMasteryGlobal', FID['SNJ_SetMastery'])])], quest=True),
    sub('FULL', z('Serana: Way of the Shinobi')),
    sub('DNAM', struct.pack('<HBBII', 0x0011, 50, 0, 0, 0)),   # Start Game Enabled, priority 50 (as CTKD)
    sub('NEXT', b''), sub('ANAM', u32(0))])

# Sasuke's kenjutsu as a rogue: guarded, flanking, waits for openings (her parries/dodges come from the script); magic only as a fallback (her jutsu come from the
# moveset and the script's openers, which cast lightning from range while she closes in).
shinobi_style = rec('CSTY', FID['SNJ_ShinobiStyle'], [
    sub('EDID', z('SNJ_ShinobiStyle')),
    # offensive, defensive, group offensive | equipment weights: melee, magic, ranged, shout, unarmed, staff | avoid threat
    sub('CSGD', f32(0.7, 0.65, 0.6, 1.0, 0.2, 0.0, 0.0, 0.0, 0.0, 0.4)),   # rogue: patient, guarded, picks her openings
    sub('CSME', f32(1.0, 1.0, 1.0, 1.4, 1.3, 1.1, 1.1, 0.5)),
    sub('CSCR', f32(0.4, 0.2, 0.5, 0.2)),        # some circling and flanking, little falling back
    sub('CSLR', f32(0.2)),
    sub('CSFL', f32(0.33, 1.0, 0.5, 0.5, 0.5, 0.5, 0.5, 0.75)),
    sub('DATA', u32(0))])
set_mastery = rec('GLOB', FID['SNJ_SetMastery'], [sub('EDID', z('SNJ_SetMastery')), sub('FNAM', b'f'),
                                                     sub('FLTV', f32(-1.0))])

# ---- Chidori kit: naruto overhaul.esp's Chidori effects, made fire-and-forget ----
nbuf = open(NARUTO, 'rb').read(); NR = {}; NT = {}
def nwalk(o, e):
    while o < e:
        t = nbuf[o:o+4].decode('latin1'); n = struct.unpack_from('<I', nbuf, o+4)[0]
        if t == 'GRUP': nwalk(o+24, o+n); o += n; continue
        fl, fid = struct.unpack_from('<II', nbuf, o+8); b = nbuf[o+24:o+24+n]; o += 24 + n
        if t not in ('MGEF', 'EXPL', 'PROJ'): continue
        if fl & 0x40000: b = zlib.decompress(b[4:])
        NR[fid & 0xFFFFFF] = list(subs_of(b))
        NT[fid & 0xFFFFFF] = t
nwalk(24 + struct.unpack_from('<I', nbuf, 4)[0], len(nbuf))
NO = 0x02000000     # naruto overhaul.esp's index in this plugin (and in its own file)

def clone_mgef(src, name, full, cast=1, delivery=None, sounds_from=None, clear_flags=0, proj=None):
    out = []
    snd = dict(NR[sounds_from])['SNDD'] if sounds_from else None
    for t, d in NR[src]:
        if t == 'EDID': d = z(name)
        elif t == 'FULL': d = z(full)
        elif t == 'DATA':
            d = bytearray(d)
            struct.pack_into('<I', d, 0x50, cast)
            struct.pack_into('<I', d, 0x00, struct.unpack_from('<I', d, 0x00)[0] & ~clear_flags)
            if delivery is not None: struct.pack_into('<I', d, 0x54, delivery)
            if proj is not None: struct.pack_into('<I', d, 0x48, FID[proj])
            d = bytes(d)
        elif t == 'SNDD' and snd is not None: d = snd
        out.append(sub(t, d))
    if snd is not None and not any(t == 'SNDD' for t, _ in NR[src]):
        out.insert(len(out) - 1, sub('SNDD', snd))
    return rec('MGEF', FID[name], out)

charge = clone_mgef(0x02F884, 'SNJ_ChidoriCharge', 'Chidori', cast=1, delivery=0, sounds_from=0x008EFA,
                    clear_flags=NO_DUR)    # it was a constant effect: give it a duration (the charge, about 1 s)
chidori = clone_mgef(0x008EFA, 'SNJ_ChidoriShock', 'Chidori')
eiso = clone_mgef(0x0053AE, 'SNJ_EisoShock', 'Chidori Eiso', proj='SNJ_EisoProj')
kirin = clone_mgef(0x013105, 'SNJ_KirinShock', 'Kirin', proj='SNJ_KirinProj')

def kit_mdata(archetype, cast, delivery, flags):
    d = bytearray(mdata(cast, delivery, flags))
    struct.pack_into('<Ii', d, 0x40, archetype, -1)
    return bytes(d)
HOSTILE, DETRIMENTAL = 0x1, 0x4
stagger = rec('MGEF', FID['SNJ_JutsuStagger'], [
    sub('EDID', z('SNJ_JutsuStagger')), sub('FULL', z('Chidori')),
    sub('DATA', kit_mdata(33, 1, 2, HOSTILE | DETRIMENTAL | NO_DUR | NO_AREA | HIDE_UI)), sub('SNDD', b''), sub('DNAM', z(''))])
XMARKER = 0x0000003B
kirin_call = rec('MGEF', FID['SNJ_KirinCallEffect'], [
    sub('EDID', z('SNJ_KirinCallEffect')),
    vmad([script('SNJ_KirinCallEffect', [p_obj('Master', FID['SNJ_Quest']), p_obj('KirinSpell', FID['SNJ_KirinSpell']),
                                         p_obj('EisoSpell', FID['SNJ_EisoSpell']), p_obj('XMarker', XMARKER)])]),
    sub('FULL', z('Kirin')), sub('DATA', kit_mdata(1, 1, 0, NO_DUR | NO_MAG | NO_AREA | HIDE_UI)), sub('SNDD', b''),
    sub('DNAM', z(''))])
# Chidori Nagashi without the shove
burst_subs = []
for t, d in NR[0x02F883]:
    if t == 'EDID': d = z('SNJ_NagashiBurst')
    elif t == 'DATA':
        d = bytearray(d); struct.pack_into('<f', d, 24, 0.0); d = bytes(d)    # force (after 6 form ids)
    burst_subs.append(sub(t, d))
nagashi_burst = rec('EXPL', FID['SNJ_NagashiBurst'], burst_subs)
nag_subs = []
for t, d in NR[0x0053B4]:
    if t == 'EDID': d = z('SNJ_NagashiShock')
    elif t == 'FULL': d = z('Chidori Nagashi')
    elif t == 'DATA':
        d = bytearray(d); struct.pack_into('<I', d, 0x4C, FID['SNJ_NagashiBurst']); d = bytes(d)
    nag_subs.append(sub(t, d))
nagashi = rec('MGEF', FID['SNJ_NagashiShock'], nag_subs)
# ---- Mangekyo ----
FROST_SHADER, ICE_SHADER, ICE_BREAK, ICE_PILE = 0x0001F03A, 0x000DC20D, 0x000EA519, 0x001069E4
burn_d = bytearray(kit_mdata(0, 1, 3, HOSTILE | DETRIMENTAL | NO_AREA))
struct.pack_into('<Ii', burn_d, 0x40, 0, 24)              # Value Modifier, Health
ms_burn = rec('MGEF', FID['SNJ_BlackFrostBurn'], [sub('EDID', z('SNJ_BlackFrostBurn')), sub('FULL', z('Black Frost')),
    sub('DATA', bytes(burn_d)), sub('SNDD', b''), sub('DNAM', z('Frost that starts in the blood and never thaws.'))])
ms_para = rec('MGEF', FID['SNJ_MSParalysis'], [sub('EDID', z('SNJ_MSParalysis')), sub('FULL', z('Sealed')),
    sub('DATA', kit_mdata(21, 1, 3, HOSTILE | DETRIMENTAL | NO_MAG | NO_AREA)), sub('SNDD', b''), sub('DNAM', z(''))])
ms_spread = rec('MGEF', FID['SNJ_BlackFrostSpread'], [sub('EDID', z('SNJ_BlackFrostSpread')),
    vmad([script('SNJ_BlackFrostEffect', [p_obj('Master', FID['SNJ_Quest']), p_obj('BlackFrostSpell', FID['SNJ_BlackFrostSpell']),
                                          p_obj('FrostShader', FROST_SHADER)])]),
    sub('FULL', z('Black Frost')), sub('DATA', kit_mdata(1, 1, 3, HOSTILE | DETRIMENTAL | NO_MAG | NO_AREA)), sub('SNDD', b''),
    sub('DNAM', z(''))])
ms_dim = rec('MGEF', FID['SNJ_DimhollowEffect'], [sub('EDID', z('SNJ_DimhollowEffect')),
    vmad([script('SNJ_DimhollowEffect', [p_obj('Master', FID['SNJ_Quest']), p_obj('StasisParalysis', FID['SNJ_StasisParalysis']),
                                         p_obj('IceShader', ICE_SHADER), p_obj('BreakShader', ICE_BREAK), p_obj('IcePile', ICE_PILE)])]),
    sub('FULL', z('Dimhollow')), sub('DATA', kit_mdata(1, 1, 3, NO_MAG | NO_AREA)), sub('SNDD', b''), sub('DNAM', z(''))])
kit_mgefs = charge + chidori + eiso + kirin + stagger + kirin_call + nagashi + ms_burn + ms_para + ms_spread + ms_dim
# ---- Hyoton: Gokakyu (her Great Fireball, in ice) ----
ice_light = struct.unpack_from('<I', dict(V[0x0002F774])['DATA'], 0x10)[0]
gp_subs = []
for t, d in NR[0x010063]:
    if t == 'MODT': continue                                  # texture hashes of the old mesh
    if t == 'EDID': d = z('SNJ_GokakyuProj')
    elif t == 'MODL': d = z(r'SNJ\HyotonGokakyu.nif')
    elif t == 'DATA':
        d = bytearray(d); struct.pack_into('<I', d, 0x10, ice_light); struct.pack_into('<I', d, 0x24, FID['SNJ_GokakyuBurst'])
        # 2026-10-19: the ball sometimes stops at point-blank range without detonating and sat there for good (no
        # lifetime, no alternate trigger). Explosion + Alt. Trigger flags, a 1.5 s alternate-trigger timer (it bursts
        # then at the latest) and a 2.5 s lifetime cap.
        struct.pack_into('<H', d, 0x00, struct.unpack_from('<H', d, 0x00)[0] | 0x0002 | 0x0004)
        struct.pack_into('<f', d, 0x20, 1.5)
        struct.pack_into('<f', d, 0x4C, 2.5)
        d = bytes(d)
    gp_subs.append(sub(t, d))
gokakyu_proj = rec('PROJ', FID['SNJ_GokakyuProj'], gp_subs)
gb_subs = []
for t, d in V[0x00044089]:
    # Skyrim.esm's record is form version 39: its MODT texture hashes are in the old layout and crash the game when
    # read as version 44 (this plugin's), so drop them; EITM is the frost rune's own damage enchantment
    if t in ('MODT', 'EITM'): continue
    if t == 'EDID': d = z('SNJ_GokakyuBurst')
    elif t == 'DATA':
        d = bytearray(d); struct.pack_into('<f', d, 24, 0.0); struct.pack_into('<f', d, 32, 260.0); d = bytes(d)    # no push; radius
    gb_subs.append(sub(t, d))
gokakyu_burst = rec('EXPL', FID['SNJ_GokakyuBurst'], gb_subs)
gf_subs = []
for t, d in V[0x0001CEA2]:
    if t == 'EDID': d = z('SNJ_GokakyuFrost')
    elif t == 'FULL': d = z('Hyoton: Gokakyu')    # Skyrim.esm's strings are localized ids: write real text
    elif t == 'DNAM': d = z('A great ball of freezing mist that does <mag> points of frost damage.')
    elif t == 'DATA':
        d = bytearray(d); struct.pack_into('<II', d, 0x48, FID['SNJ_GokakyuProj'], FID['SNJ_GokakyuBurst']); d = bytes(d)
    gf_subs.append(sub(t, d))
gokakyu_frost = rec('MGEF', FID['SNJ_GokakyuFrost'], gf_subs)
kit_mgefs += gokakyu_frost
FROST_SLOW = 0x000B729F    # FrostSlowFFAimed
gokakyu_spel = rec('SPEL', FID['SNJ_GokakyuSpell'], [sub('EDID', z('SNJ_GokakyuSpell')), sub('OBND', bytes(12)),
    sub('FULL', z('Hyoton: Gokakyu no Jutsu')),
    sub('SPIT', u32(0, 0x1 | 0x100000 | 0x200000, 0) + f32(0.0) + u32(1, 2) + f32(0.0, 0.0) + u32(0)),
    sub('EFID', u32(FID['SNJ_GokakyuFrost'])), sub('EFIT', f32(55.0) + u32(15, 0)),
    sub('EFID', u32(FROST_SLOW)), sub('EFIT', f32(50.0) + u32(15, 3)),
    sub('EFID', u32(FID['SNJ_JutsuStagger'])), sub('EFIT', f32(1.0) + u32(15, 0))])

# ---- flash Susanoo, the spectral bow: one black-ice arrow ----
ap_subs = []
for t, d in V[0x0002F774]:                         # Ice Spike's missile
    if t == 'MODT': continue
    if t == 'EDID': d = z('SNJ_SusanooArrowProj')
    elif t == 'MODL': d = z(r'SNJ\susanoo\arrow.nif')
    elif t == 'DATA':
        d = bytearray(d); struct.pack_into('<f', d, 0x08, 4500.0); struct.pack_into('<I', d, 0x24, 0); d = bytes(d)
    ap_subs.append(sub(t, d))
arrow_proj = rec('PROJ', FID['SNJ_SusanooArrowProj'], ap_subs)
af_subs = []
for t, d in V[0x0001CEA2]:                         # FrostDamageFFAimed
    if t == 'EDID': d = z('SNJ_SusanooArrowFrost')
    elif t == 'FULL': d = z('Susanoo Arrow')
    elif t == 'DNAM': d = z('An arrow of black ice from her Susanoo: <mag> points of frost damage.')
    elif t == 'DATA':
        d = bytearray(d); struct.pack_into('<II', d, 0x48, FID['SNJ_SusanooArrowProj'], 0); d = bytes(d)
    af_subs.append(sub(t, d))
arrow_frost = rec('MGEF', FID['SNJ_SusanooArrowFrost'], af_subs)
arrow_spel = rec('SPEL', FID['SNJ_SusanooArrowSpell'], [sub('EDID', z('SNJ_SusanooArrowSpell')), sub('OBND', bytes(12)),
    sub('FULL', z('Susanoo Arrow')),
    sub('SPIT', u32(0, 0x1 | 0x100000 | 0x200000, 0) + f32(0.0) + u32(1, 2) + f32(0.0, 0.0) + u32(0)),
    sub('EFID', u32(FID['SNJ_SusanooArrowFrost'])), sub('EFIT', f32(90.0) + u32(0, 0)),
    sub('EFID', u32(FROST_SLOW)), sub('EFIT', f32(50.0) + u32(0, 3)),
    sub('EFID', u32(FID['SNJ_JutsuStagger'])), sub('EFIT', f32(1.0) + u32(0, 0))])
def kit_spel(name, full, delivery, effects):
    """effects: [(mgef name, magnitude, duration)]; manual cost 0 (the Payload Interpreter casts pay the magicka)"""
    return rec('SPEL', FID[name], [sub('EDID', z(name)), sub('OBND', bytes(12)), sub('FULL', z(full)),
        sub('SPIT', u32(0, 0x1 | 0x100000 | 0x200000, 0) + f32(0.0) + u32(1, delivery) + f32(0.0, 0.0) + u32(0))]
        + [sub('EFID', u32(FID[m])) + sub('EFIT', f32(mag) + u32(0, dur)) for m, mag, dur in effects])
SELF, AIMED = 0, 2
kit_spels = (kit_spel('SNJ_ChidoriChargeSpell', 'Chidori', SELF, [('SNJ_ChidoriCharge', 0.0, 1)])
             + kit_spel('SNJ_ChidoriSpell', 'Chidori', AIMED, [('SNJ_ChidoriShock', 70.0, 0), ('SNJ_JutsuStagger', 1.0, 0)])
             + kit_spel('SNJ_KatanaSpell', 'Chidori Katana', AIMED, [('SNJ_ChidoriShock', 10.0, 0)])
             + kit_spel('SNJ_EisoSpell', 'Chidori Eiso', AIMED, [('SNJ_EisoShock', 50.0, 0), ('SNJ_JutsuStagger', 1.0, 0)])
             + kit_spel('SNJ_SenbonSpell', 'Chidori Senbon', AIMED, [('SNJ_EisoShock', 12.0, 0)])
             + kit_spel('SNJ_KirinSpell', 'Kirin', AIMED, [('SNJ_KirinShock', 220.0, 0), ('SNJ_JutsuStagger', 1.0, 0)])
             + kit_spel('SNJ_KirinCallSpell', 'Kirin', SELF, [('SNJ_KirinCallEffect', 0.0, 0)])
             + kit_spel('SNJ_NagashiSpell', 'Chidori Nagashi', SELF, [('SNJ_NagashiShock', 40.0, 0)])
             + kit_spel('SNJ_BlackFrostSpell', 'Black Frost', 3, [('SNJ_BlackFrostBurn', 10.0, 12), ('SNJ_MSParalysis', 0.0, 2),
                                                                   ('SNJ_BlackFrostSpread', 0.0, 12)])
             + kit_spel('SNJ_DimhollowSpell', 'Dimhollow', 3, [('SNJ_DimhollowEffect', 0.0, 6)])
             + kit_spel('SNJ_StasisParalysis', 'Dimhollow', 3, [('SNJ_MSParalysis', 0.0, 6)])
             + kit_spel('SNJ_SoulCairnParalysis', 'Soul Cairn', 3, [('SNJ_MSParalysis', 0.0, 4)])
             + gokakyu_spel + arrow_spel)

# ---- flash Susanoo: the black-ice ribcage (worn for a moment) ----
# the original's race list (Skyrim.esm races: the playable ones and their vampire forms); default race first
SUS_RACES = [0x00013740, 0x0008883A, 0x00013741, 0x0008883C, 0x00097A3D, 0x00013742, 0x0008883D, 0x000131F0,
             0x00067CD8, 0x000A82BA, 0x00013743, 0x00088840, 0x00013744, 0x00088844, 0x00013745, 0x00088845,
             0x0010760A, 0x00013746, 0x00088794, 0x00013747, 0x000A82B9, 0x00013748, 0x00088846, 0x00013749,
             0x00088884]
def arma(name, slot, dnam, model):
    return rec('ARMA', FID[name], [sub('EDID', z(name)), sub('BOD2', u32(1 << (slot - 30), 2)), sub('RNAM', u32(0x19)),
        sub('DNAM', bytes.fromhex(dnam)), sub('MOD2', z(model)), sub('MOD3', z(model)), sub('MOD4', z(model)),
        sub('MOD5', z(model))] + [sub('MODL', u32(r)) for r in SUS_RACES])
ribcage_aa = arma('SNJ_RibcageAA', 51, '05050000000000179a99193f', r'SNJ\susanoo\ribcage.nif')
ribcage_fx_aa = arma('SNJ_RibcageParticlesAA', 50, '050500000000001700000000', r'SNJ\susanoo\ribcageparticles.nif')
ribcage = rec('ARMO', FID['SNJ_Ribcage'], [sub('EDID', z('SNJ_Ribcage')), sub('OBND', bytes(12)),
    sub('FULL', z('Susanoo')), sub('BOD2', u32((1 << 20) | (1 << 21), 2)), sub('RNAM', u32(0x19)), sub('DESC', z('')),
    sub('MODL', u32(FID['SNJ_RibcageAA'])), sub('MODL', u32(FID['SNJ_RibcageParticlesAA'])),
    sub('DATA', u32(0) + f32(0.0)), sub('DNAM', u32(0))], flags=0x4)     # non-playable
# ---- Eiso and Kirin without the physics shove ----
def no_push(src_subs, name):
    out = []
    for t, d in src_subs:
        if t in ('MODT', 'EITM'): continue      # old-layout hashes / an enchantment of its own (the Gokakyu crash lesson)
        if t == 'EDID': d = z(name)
        elif t == 'DATA':
            d = bytearray(d); struct.pack_into('<f', d, 24, 0.0); d = bytes(d)    # force
        out.append(sub(t, d))
    return rec('EXPL', FID[name], out)
def proj_with(src, name, burst):
    out = []
    for t, d in NR[src]:
        if t == 'MODT': continue
        if t == 'EDID': d = z(name)
        elif t == 'DATA':
            d = bytearray(d); struct.pack_into('<I', d, 0x24, FID[burst]); d = bytes(d)
        out.append(sub(t, d))
    return rec('PROJ', FID[name], out)
eiso_burst = no_push(V[0x000D13E8], 'SNJ_EisoBurst')
kirin_burst = no_push(NR[0x02F887], 'SNJ_KirinBurst')
eiso_proj = proj_with(0x02F881, 'SNJ_EisoProj', 'SNJ_EisoBurst')
kirin_proj = proj_with(0x015158, 'SNJ_KirinProj', 'SNJ_KirinBurst')
groups = (grup('PROJ', gokakyu_proj + eiso_proj + kirin_proj + arrow_proj) + grup('EXPL', nagashi_burst + gokakyu_burst + eiso_burst + kirin_burst) + grup('GLOB', set_mastery) + grup('CSTY', shinobi_style) + grup('MGEF', mgef + tier_mgefs + kit_mgefs + arrow_frost)
          + grup('SPEL', spel + tier_spels + kit_spels) + grup('CONT', cont) + grup('QUST', qust) + grup('ARMA', ribcage_aa + ribcage_fx_aa) + grup('ARMO', ribcage))
hdr = [sub('HEDR', f32(1.7) + u32(len(FID) + 6, 0x800 + len(FID))), sub('CNAM', z('Claude')),
       sub('SNAM', z('Serana Ninja Mode')), sub('MAST', z('Skyrim.esm')), sub('DATA', bytes(8)),
       sub('MAST', z('Update.esm')), sub('DATA', bytes(8)), sub('MAST', z('naruto overhaul.esp')), sub('DATA', bytes(8))]
open(OUT, 'wb').write(rec('TES4', 0, hdr, flags=0x200) + groups)
print('wrote', OUT)
for k, v in FID.items(): print(f'  {v:08X} {k}')
