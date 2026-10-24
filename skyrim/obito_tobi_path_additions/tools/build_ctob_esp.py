r"""Build Obito Tobi Path Additions.esp (ESL).

Usage: build_ctob_esp.py <naruto overhaul.esp> <UchihaClan.esp> <Elemental Destruction Magic Redux.esp> <out.esp>

Records (append-only object IDs, saves reference them):
  0x800 QUST CTOB_Quest              Start Game Enabled, script CTOB_TobiPathQuestScript
  0x801 SPEL CTOB_BakufuRanbu        "Katon: Bakufu Ranbu" - fire vortex: EDM Tornado retinted to fire (0x805-0x807)
  0x802 SPEL CTOB_Sashiki            "Mokuton: Sashiki no Jutsu" - clone of EDM Stalagmite with a wood-tentacle burst
  0x803 MGEF CTOB_SashikiEffect      clone of EDM EarthDamageFFAimedAreaProjectile, explosion -> 0x804
  0x804 EXPL CTOB_SashikiExplosion   clone of EDM EarthExp01, model -> Uchiha Clan Mokuton tentacle impact
  0x805 PROJ CTOB_BakufuProjectile   clone of EDM TornadoProjectile01, model magic\ctob\bakufuranbuprojectile.nif
                                     (make_bakufu_assets.py: fire colour ramps, 1.6x scale), fireball light
  0x806 MGEF CTOB_BakufuCarrier      clone of EDM WindDamageFFAimedAreaProjectile with Fireball's fire visuals,
                                     sounds, keyword, fire resist, fireball explosion; fires 0x805
  0x807 MGEF CTOB_BakufuFireDamage   clone of EDM WindDamageFFAimedArea as fire damage (resist fire, fire keyword)
  0x808 SPEL CTOB_HashiramaAbility   ability "Hashirama Cell Healing Factor" (level/magicka-conditioned regen)
  0x809 SPEL CTOB_ZetsuBurst         5 s +300% health regen, cast by 0x80A
  0x80A MGEF CTOB_ZetsuWatchEffect   hidden script effect (levels 1-15): White Zetsu armor burst once a day
  0x80B MGEF CTOB_HashiramaCellEffect item effect, script adds 0x808
  0x80C ALCH CTOB_HashiramaCell      "Hashirama Cell" (given once by the quest)
  0x80D GLOB CTOB_ZetsuNextDay       day the Zetsu burst is next allowed
  0x80E SPEL CTOB_KannabiWatchAbility hidden ability holding 0x80F (Tobi path, no cells yet)
  0x80F MGEF CTOB_KannabiWatchEffect  near-death 'Kannabi Bridge' event -> Naka Shrine + healing factor
  0x810 GLOB CTOB_KannabiDone         1 once the event has happened
  --- Sharingan genjutsu (2026-10-14), script CTOB_GenjutsuQuestScript (2nd script on the quest) ---
  0x811 MGEF CTOB_GenjutsuFreezeEffect  Paralysis archetype (as vanilla ParalysisFFAimed, flags 0x401403, AV 53),
                                        target actor, no hit shader: the target goes rigid and falls
  0x812 SPEL CTOB_GenjutsuFreezeSpell   target actor; duration set by script (4 s, 7 s with the Mangekyou)
  0x813 MGEF CTOB_PuppetEffect          script CTOB_PuppetEffect: Sharingan Puppet on the target (not hostile)
  0x814 SPEL CTOB_PuppetSpell           target actor; duration set by script (60/90 s, beasts 30 s)
  0x815 MGEF CTOB_GenjutsuGazeEffect    power effect, CTOB_GenjutsuPowerEffect Mode 1
  0x816 SPEL CTOB_GenjutsuGazePower     lesser power "Genjutsu: Sharingan"
  0x817 MGEF CTOB_PuppetPowerEffect     power effect, CTOB_GenjutsuPowerEffect Mode 2
  0x818 SPEL CTOB_PuppetPower           lesser power "Genjutsu: Sharingan Puppet"
  --- Rinnegan: Preta Path (2026-10-14), the one Path of Pain the Uchiha Clan's Rinnegan lacks ---
  0x819 MGEF CTOB_PretaSealEffect       Absorb Chance +100 (AV 83, as the Atronach Stone), recover, self, absorb shader
  0x81A SPEL CTOB_PretaSealSpell        8 s: spells hitting you are absorbed into your Magicka (Fujutsu Kyuin)
  0x81B MGEF CTOB_PretaDrainMagicka     Absorb Magicka per second (as vanilla AbsorbMagicka), target actor
  0x81C MGEF CTOB_PretaDrainStamina     Absorb Stamina per second, target actor
  0x81D SPEL CTOB_PretaDrainSpell       4 s touch drain of the target's chakra (Magicka) and stamina
  0x81E MGEF CTOB_PretaSealPowerEffect  power effect, CTOB_GenjutsuPowerEffect Mode 3
  0x81F SPEL CTOB_PretaSealPower        lesser power "Preta Path: Absorption Seal"
  0x820 MGEF CTOB_PretaDrainPowerEffect power effect, CTOB_GenjutsuPowerEffect Mode 4
  0x821 SPEL CTOB_PretaDrainPower       lesser power "Preta Path: Chakra Absorption"
  --- Unmasked: Will of the Uchiha (2026-10-15): Tobi war outfit + boots + gloves (either version), NO war mask ---
  0x822 SPEL CTOB_UnmaskedAbility       ability: the war mask's enchantment (Resist Magic 25, Magicka regen 120,
                                        Magicka 60, Alteration 20, Destruction 20) + 0x823, every effect conditioned
                                        on the gear, so wearing the mask gives only the mask's own enchantment
  0x823 MGEF CTOB_UnmaskedEffect        marker + Chakra Surge (script CTOB_ChakraSurgeEffect); Sharingan Copy's Kamui
                                        checks it for Kamui Focus (cheaper, faster Kamui)
  --- Rinnegan rework (2026-10-15), logic in CTOB_RinneganQuestScript (third quest script) ---
  0x824 MGEF CTOB_ExposedEffect         Damage Resist -<mag> (armour broken; open to the Human Path soul rip)
  0x825 SPEL CTOB_ExposedSpell          target actor, 250 for 6 s (perfect Shinra Tensei, Bansho Tenin)
  0x826 MGEF CTOB_PinnedEffect          Speed -<mag>% (chakra receivers in the body; Bansho Tenin tears them)
  0x827 SPEL CTOB_PinnedSpell           target actor, 50 for 8 s
  0x828 PROJ CTOB_RodProjectile         clone of Uchiha Clan Additions' aaaChakraBladeProjectile (ChakraBladeFlight.nif)
  0x829 IPCT CTOB_RodImpact             clone of aaaChakraBladeImpact (the rod stays stuck where it lands)
  0x82A IPDS CTOB_RodImpactSet          clone of aaaChakraBladeImpactSet, pointing at 0x829
  0x82B MGEF CTOB_RodEffect             script CTOB_ReceiverRodEffect, aimed, projectile 0x828, impacts 0x82A
  0x82C SPEL CTOB_RodSpell              one rod, script-cast (unused since the hand-cast version)
  0x82D MGEF CTOB_RodsPowerEffect       unused (the first version was a lesser power firing three rods)
  0x82E SPEL CTOB_RodsPower             hand-cast spell "Outer Path: Chakra Receivers": one rod per cast, like the
                                        Uchiha Clan Additions' "Launch Chakra Disruptive Blade"
  --- Eye Adaptation (2026-10-15), logic in CTOB_EyeMasteryScript (fourth quest script) ---
  0x82F MGEF CTOB_EyeAdaptEffect        shown in Active Effects; the script renames it "Eye Adaptation (rank N)"
  0x830 GLOB CTOB_EyeMastery            rank 0-100
  0x831 GLOB CTOB_SetEyeMastery         console hook (-1 = unused): set CTOB_SetEyeMastery to N
  0x832 SPEL CTOB_EyeAdaptAbility       0x82F + Fortify Magicka Rate 10% while rank >= 100 and the Sharingan is open
  --- Hashirama cells in combat (2026-10-16), given by the quest to anyone with 0x808 ---
  0x833 MGEF CTOB_OvergrowthEffect      Speed -<mag>% (the cells run wild), self, detrimental, not hostile
  0x834 SPEL CTOB_OvergrowthSpell       40 for 4 s, cast by CTOB_CellCombatEffect on itself
  0x835 MGEF CTOB_CellCombatEffect      script CTOB_CellCombatEffect: chakra-fuelled combat regen, Cell Activation,
                                        wound regrowth, cell overgrowth
  0x836 SPEL CTOB_CellCombatAbility     ability "Hashirama Cells: Combat Regeneration" holding 0x835
  --- Preta Path: Chakra Grasp (2026-10-16), follows the Rinnegan like 0x81F/0x821 ---
  0x837 MGEF CTOB_DrainedEffect         Magicka Rate -<mag>% (peak value modifier on MagickaRateMult), target actor
  0x838 SPEL CTOB_DrainedSpell          75 for 15 s, cast by CTOB_PretaTouchEffect on its victim
  0x839 MGEF CTOB_PretaTouchEffect      concentration, self: script CTOB_PretaTouchEffect (2.5 s touch -> -100 Magicka)
  0x83A SPEL CTOB_PretaTouchSpell       hand-cast concentration spell "Preta Path: Chakra Grasp", 10 Magicka/s
  --- Ninja Travel (2026-10-17), given on the Tobi path ---
  0x83B MGEF CTOB_NinjaTravelEffect     script CTOB_NinjaTravelEffect: momentum sprint, leap, water running, strike
  0x83C SPEL CTOB_NinjaTravelAbility    ability "Ninja Travel" holding 0x83B
  --- Bakufu Ranbu rework (2026-10-17): canon Kamui fire whirlwind, short range ---
  0x83D MGEF CTOB_BakufuBurn            clone of 0x807 with a duration: fire damage per second
  0x83E MGEF CTOB_BakufuVortexEffect    hidden script CTOB_BakufuVortexEffect: Exposed, Kamui pull with the Mangekyou
Cloned subrecords are copied verbatim except FormIDs, which are remapped from the source plugin's
master list to ours (only at the offsets listed below, which are the ones these records use).
Helpers follow skyrim/six_paths_of_pain/tools/build_spp_esp.py (tested in game).
"""
import struct, sys, zlib, os

NARUTO, UCHIHA, EDM, OUT = sys.argv[1:5]
ADDITIONS = sys.argv[5] if len(sys.argv) > 5 else os.path.join(os.path.dirname(os.path.dirname(UCHIHA)),
                                                               'The Uchiha Clan Additions', 'Uchiha Clan Additions.esp')
MASTERS = ['Skyrim.esm', 'Update.esm', 'Dawnguard.esm', 'Dragonborn.esm', 'RaceCompatibility.esm',
           'naruto overhaul.esp', 'UchihaClan.esp', 'Elemental Destruction Magic Redux.esp']
OWN = len(MASTERS) << 24
FID = {n: OWN | (0x800 + i) for i, n in enumerate(
    ['CTOB_Quest', 'CTOB_BakufuRanbu', 'CTOB_Sashiki', 'CTOB_SashikiEffect', 'CTOB_SashikiExplosion',
     'CTOB_BakufuProjectile', 'CTOB_BakufuCarrier', 'CTOB_BakufuFireDamage',
     'CTOB_HashiramaAbility', 'CTOB_ZetsuBurst', 'CTOB_ZetsuWatchEffect', 'CTOB_HashiramaCellEffect',
     'CTOB_HashiramaCell', 'CTOB_ZetsuNextDay',
     'CTOB_KannabiWatchAbility', 'CTOB_KannabiWatchEffect', 'CTOB_KannabiDone',
     'CTOB_GenjutsuFreezeEffect', 'CTOB_GenjutsuFreezeSpell', 'CTOB_PuppetEffect', 'CTOB_PuppetSpell',
     'CTOB_GenjutsuGazeEffect', 'CTOB_GenjutsuGazePower', 'CTOB_PuppetPowerEffect', 'CTOB_PuppetPower',
     'CTOB_PretaSealEffect', 'CTOB_PretaSealSpell', 'CTOB_PretaDrainMagicka', 'CTOB_PretaDrainStamina',
     'CTOB_PretaDrainSpell', 'CTOB_PretaSealPowerEffect', 'CTOB_PretaSealPower', 'CTOB_PretaDrainPowerEffect',
     'CTOB_PretaDrainPower', 'CTOB_UnmaskedAbility', 'CTOB_UnmaskedEffect',
     'CTOB_ExposedEffect', 'CTOB_ExposedSpell', 'CTOB_PinnedEffect', 'CTOB_PinnedSpell',
     'CTOB_RodProjectile', 'CTOB_RodImpact', 'CTOB_RodImpactSet', 'CTOB_RodEffect', 'CTOB_RodSpell',
     'CTOB_RodsPowerEffect', 'CTOB_RodsPower',
     'CTOB_EyeAdaptEffect', 'CTOB_EyeMastery', 'CTOB_SetEyeMastery', 'CTOB_EyeAdaptAbility',
     'CTOB_OvergrowthEffect', 'CTOB_OvergrowthSpell', 'CTOB_CellCombatEffect', 'CTOB_CellCombatAbility',
     'CTOB_DrainedEffect', 'CTOB_DrainedSpell', 'CTOB_PretaTouchEffect', 'CTOB_PretaTouchSpell',
     'CTOB_NinjaTravelEffect', 'CTOB_NinjaTravelAbility', 'CTOB_BakufuBurn', 'CTOB_BakufuVortexEffect'])}
# vanilla Fireball (Skyrim.esm) pieces used for the fire look
FIRE_KEYWORD, FIRE_LIGHT, FIRE_HIT_SHADER, FIRE_EXPLOSION = 0x0001CEAD, 0x000140EC, 0x0001B212, 0x000439C0
FIRE_HAND_ART, FIRE_IMPACT_SET, FIRE_PROJ_LIGHT, RESIST_FIRE = 0x0001B211, 0x0001C2AF, 0x0001CBB3, 41
FIRE_SNDD = bytes.fromhex('00000000f8c8030001000000f9c8030002000000fac8030003000000eaf20300')
FIREBALL_ART, EITHER_HAND, DESTRUCTION_EXPERT = 0x0004E264, 0x00013F44, 0x000C44C1
CHARGE_TIME = 1.1   # length of the mouth-cast hand-sign animation

def sub(t, data): return t.encode() + struct.pack('<H', len(data)) + data
def z(s): return s.encode('cp1252') + b'\0'
def u32(*v): return struct.pack('<%dI' % len(v), *v)
def ws(s): b = s.encode('cp1252'); return struct.pack('<H', len(b)) + b
def rec(t, fid, subs, flags=0, ver=44):
    body = b''.join(subs)
    return t.encode() + struct.pack('<IIIIHH', len(body), flags, fid, 0, ver, 0) + body
def grup(label, body):
    return b'GRUP' + struct.pack('<I', 24 + len(body)) + label.encode() + struct.pack('<IHHI', 0, 0, 0, 0) + body
def p_obj(name, fid): return ws(name) + bytes([1, 1]) + struct.pack('<hhI', 0, -1, fid)
def p_objs(name, fids): return ws(name) + bytes([11, 1]) + u32(len(fids)) + b''.join(struct.pack('<hhI', 0, -1, f) for f in fids)
def script(name, props): return ws(name) + bytes([0]) + struct.pack('<H', len(props)) + b''.join(props)
def subs_of(d):
    i = 0
    while i < len(d):
        t = d[i:i+4].decode('latin1'); n = struct.unpack_from('<H', d, i+4)[0]
        yield t, d[i+6:i+6+n]; i += 6 + n

def load(path):
    buf = open(path, 'rb').read(); recs = {}; masters = []
    hsize = struct.unpack_from('<I', buf, 4)[0]
    for t, d in subs_of(buf[24:24 + hsize]):
        if t == 'MAST': masters.append(d.rstrip(b'\0').decode())
    def walk(o, e):
        while o < e:
            t = buf[o:o+4].decode('latin1'); n = struct.unpack_from('<I', buf, o+4)[0]
            if t == 'GRUP': walk(o+24, o+n); o += n; continue
            fl, fid = struct.unpack_from('<II', buf, o+8); b = buf[o+24:o+24+n]; o += 24 + n
            if fl & 0x40000: b = zlib.decompress(b[4:])
            s = list(subs_of(b)); recs[dict(s).get('EDID', b'').rstrip(b'\0').decode('latin1')] = (t, fid, s)
    walk(24 + hsize, len(buf))
    name = path.replace('\\', '/').split('/')[-1]
    table = {i: MASTERS.index(m) for i, m in enumerate(masters + [name])}
    return recs, table

def remap(fid, table):
    if fid == 0 or fid == 0xFFFFFFFF: return fid
    return (table[fid >> 24] << 24) | (fid & 0xFFFFFF)
def remap_at(data, offsets, table):
    d = bytearray(data)
    for o in offsets: struct.pack_into('<I', d, o, remap(struct.unpack_from('<I', d, o)[0], table))
    return bytes(d)
def remap_all(data, table):          # every u32 in the field is a FormID (EFID, ETYP, MDOB, KWDA, MNAM...)
    return remap_at(data, range(0, len(data), 4), table)
def remap_ctda(data, table):         # only the parameter FormIDs of the functions these records use
    func = struct.unpack_from('<H', data, 8)[0]
    if func in (69, 448, 182, 72, 560):   # GetIsRace / HasPerk / HasMagicEffect / HasKeyword...: param 1 is a form
        return remap_at(data, [12], table)
    return data

NRECS, NT = load(NARUTO)
URECS, UT = load(UCHIHA)
ERECS, ET = load(EDM)
def u(edid): return remap(URECS[edid][1], UT)

# ---- Katon: Bakufu Ranbu (fire vortex built on EDM's Tornado) ----
MGEF_FID_OFFSETS = [0x08, 0x18, 0x20, 0x24, 0x48, 0x4C, 0x5C, 0x60, 0x64, 0x6C, 0x74, 0x78, 0x7C, 0x80, 0x84, 0x88]
PROJ_FID_OFFSETS = [0x10, 0x14, 0x24, 0x28, 0x38, 0x3C, 0x40, 0x54]

BAKUFU_RANGE = 840.0    # ~12 m; canon Bakufu Ranbu is short to mid range (0-10 m)
t, fid, src = ERECS['TornadoProjectile01']; assert t == 'PROJ'
out = []
for st, d in src:
    if st == 'EDID': d = z('CTOB_BakufuProjectile')
    elif st == 'FULL': d = z('Bakufu Ranbu')
    elif st == 'MODL': d = z('magic\\ctob\\bakufuranbuprojectile.nif')
    elif st == 'MODT': continue
    elif st == 'DATA':
        d = bytearray(remap_at(d, PROJ_FID_OFFSETS, ET))
        struct.pack_into('<f', d, 0x08, 800.0)              # speed (tornado is 512)
        struct.pack_into('<f', d, 0x0C, BAKUFU_RANGE)       # canon short to mid range (tornado is 2560)
        struct.pack_into('<I', d, 0x10, FIRE_PROJ_LIGHT)    # orange fireball light instead of blue
        d = bytes(d)
    out.append(sub(st, d))
bakufu_proj = rec('PROJ', FID['CTOB_BakufuProjectile'], out)

def fire_mgef(src_edid, edid, carrier):
    t, fid, src = ERECS[src_edid]; assert t == 'MGEF'
    out = []
    for st, d in src:
        if st == 'EDID': d = z(edid)
        elif st == 'FULL': d = z('Bakufu Ranbu')
        elif st == 'MDOB': d = u32(FIREBALL_ART)
        elif st == 'KWDA': d = u32(FIRE_KEYWORD)
        elif st == 'KSIZ': d = u32(1)
        elif st == 'SNDD': d = FIRE_SNDD
        elif st == 'DATA':
            d = bytearray(remap_at(d, MGEF_FID_OFFSETS, ET))
            struct.pack_into('<I', d, 0x10, RESIST_FIRE)
            struct.pack_into('<I', d, 0x18, FIRE_LIGHT)
            struct.pack_into('<I', d, 0x20, FIRE_HIT_SHADER)
            struct.pack_into('<I', d, 0x48, FID['CTOB_BakufuProjectile'])
            struct.pack_into('<I', d, 0x4C, FIRE_EXPLOSION if carrier else 0)
            struct.pack_into('<I', d, 0x5C, FIRE_HAND_ART)
            struct.pack_into('<I', d, 0x64, FIRE_IMPACT_SET)
            struct.pack_into('<f', d, 0x30, CHARGE_TIME)
            d = bytes(d)
        elif st == 'CTDA': d = remap_ctda(d, ET)
        elif st == 'VMAD': raise SystemExit('unexpected VMAD on ' + src_edid)
        out.append(sub(st, d))
    return rec('MGEF', FID[edid], out)
bakufu_carrier = fire_mgef('WindDamageFFAimedAreaProjectile', 'CTOB_BakufuCarrier', True)
bakufu_damage = fire_mgef('WindDamageFFAimedArea', 'CTOB_BakufuFireDamage', False)
def with_duration(m):                 # clear 'no duration' (0x200) in an MGEF's DATA flags
    body = bytearray(m[24:]); i = 0
    while i < len(body):
        t = bytes(body[i:i+4]); n = struct.unpack_from('<H', body, i+4)[0]
        if t == b'DATA':
            o = i + 6; struct.pack_into('<I', body, o, struct.unpack_from('<I', body, o)[0] & ~0x200)
        i += 6 + n
    return m[:24] + bytes(body)
bakufu_burn = with_duration(fire_mgef('WindDamageFFAimedArea', 'CTOB_BakufuBurn', False))

def effect(mgef, mag, area, dur=0): return sub('EFID', u32(mgef)) + sub('EFIT', struct.pack('<fII', mag, area, dur))
# 2026-10-17: Bakufu is the close-range control spell, Madara's Gouka Mekkyaku (250 fire, 350 Magicka) the nuke.
# Canon: fire breathed out and spun by Kamui into a whirlwind. Impact + burn, armour melt (Exposed), and with the
# Mangekyou the whirlwind drags everyone caught together (CTOB_BakufuVortexEffect). The knockback is gone.
BAKUFU_COST, BAKUFU_FIRE, BAKUFU_BURN, BAKUFU_BURN_SECONDS = 220, 120.0, 15.0, 6
# Two hands like Gouka Mekkyaku (BothHands: the hand signs). A both-hands spell can't be dual cast, so the dual cast
# overcharge is built in: with the Destruction Dual Casting perk, impact and burn are BAKUFU_DUAL x stronger.
BOTH_HANDS, DESTRUCTION_DUAL_CASTING, HAS_PERK, BAKUFU_DUAL = 0x00013F45, 0x000153CF, 448, 1.5
def caster_has_perk(perk, value):    # spell effect condition run on the caster ('Target' in a spell's conditions)
    return sub('CTDA', struct.pack('<B3xfHHIIIIi', 0x00, value, HAS_PERK, 0, perk, 0, 1, 0, -1))   # ==
bakufu = rec('SPEL', FID['CTOB_BakufuRanbu'], [
    sub('EDID', z('CTOB_BakufuRanbu')), sub('OBND', bytes(12)), sub('FULL', z('Katon: Bakufu Ranbu')),
    sub('MDOB', u32(FIREBALL_ART)), sub('ETYP', u32(BOTH_HANDS)),
    sub('DESC', z("Katon: Bakufu Ranbu. Fire breathed out at close range and spun by Kamui into a whirlwind. It sears "
                  "armour away and keeps burning; once the Mangekyou has awakened, the whirlwind drags everyone it "
                  "catches into the flames together.")),
    # flag 0x1 = manual cost/charge so the 1.1 s charge time is used: the Fire Style mouth-cast hand signs
    # (mrh_preCharge.hkx) last 1.1 s and were cut off by the 0.5 s charge inherited from EDM's tornado
    sub('SPIT', struct.pack('<IIIfIIffI', BAKUFU_COST, 0x1, 0, CHARGE_TIME, 1, 2, 0.0, 0.0, DESTRUCTION_EXPERT)),   # fire and forget, aimed
    effect(FID['CTOB_BakufuCarrier'], 40.0, 18),
    effect(FID['CTOB_BakufuFireDamage'], BAKUFU_FIRE, 18), caster_has_perk(DESTRUCTION_DUAL_CASTING, 0.0),
    effect(FID['CTOB_BakufuFireDamage'], BAKUFU_FIRE * BAKUFU_DUAL, 18), caster_has_perk(DESTRUCTION_DUAL_CASTING, 1.0),
    effect(FID['CTOB_BakufuBurn'], BAKUFU_BURN, 18, BAKUFU_BURN_SECONDS), caster_has_perk(DESTRUCTION_DUAL_CASTING, 0.0),
    effect(FID['CTOB_BakufuBurn'], BAKUFU_BURN * BAKUFU_DUAL, 18, BAKUFU_BURN_SECONDS), caster_has_perk(DESTRUCTION_DUAL_CASTING, 1.0),
    effect(FID['CTOB_BakufuVortexEffect'], 0.0, 18, 2)])   # 2 s so the group still has it when the pull is worked out

# ---- Mokuton: Sashiki no Jutsu (clone of EDM Stalagmite) ----
t, fid, src = ERECS['EarthExp01']; assert t == 'EXPL'
out = []
for st, d in src:
    if st == 'EDID': d = z('CTOB_SashikiExplosion')
    elif st == 'MODL': d = z('magic\\the uchiha clan\\mokuton\\tentacleimpacteffect.nif')
    elif st == 'MODT': continue
    elif st == 'MNAM': d = remap_all(d, ET)
    elif st == 'DATA': d = remap_at(d, [0, 4, 8, 12, 16, 20], ET)
    out.append(sub(st, d))
sashiki_expl = rec('EXPL', FID['CTOB_SashikiExplosion'], out)

t, fid, src = ERECS['EarthDamageFFAimedAreaProjectile']; assert t == 'MGEF'
MGEF_FIDS = [0x08, 0x18, 0x20, 0x24, 0x48, 0x4C, 0x5C, 0x60, 0x64, 0x6C, 0x74, 0x78, 0x7C, 0x80, 0x84, 0x88]
out = []
for st, d in src:
    if st == 'EDID': d = z('CTOB_SashikiEffect')
    elif st == 'FULL': d = z('Sashiki no Jutsu')
    elif st in ('MDOB', 'KWDA', 'ESCE'): d = remap_all(d, ET)
    elif st == 'SNDD': d = remap_at(d, range(4, len(d), 8), ET)
    elif st == 'DATA':
        d = remap_at(d, MGEF_FIDS, ET)
        d = d[:0x4C] + struct.pack('<I', FID['CTOB_SashikiExplosion']) + d[0x50:]
    elif st == 'CTDA': d = remap_ctda(d, ET)
    elif st == 'VMAD': raise SystemExit('unexpected VMAD on source MGEF')
    out.append(sub(st, d))
sashiki_mgef = rec('MGEF', FID['CTOB_SashikiEffect'], out)

t, fid, src = ERECS['Stalagmite']; assert t == 'SPEL'
out, first_efid, first_efit = [], True, True
for st, d in src:
    if st == 'EDID': d = z('CTOB_Sashiki')
    elif st == 'FULL': d = z('Mokuton: Sashiki no Jutsu')
    elif st == 'DESC': d = z('Sharpened wood bursts out at the target, impaling everything around it.')
    elif st == 'SPIT': d = remap_at(d, [32], ET)
    elif st == 'EFID':
        d = u32(FID['CTOB_SashikiEffect']) if first_efid else remap_all(d, ET); first_efid = False
    elif st == 'EFIT' and first_efit: d = struct.pack('<f', 60.0) + d[4:]; first_efit = False   # Stalagmite is 40
    elif st in ('MDOB', 'ETYP'): d = remap_all(d, ET)
    elif st == 'CTDA': d = remap_ctda(d, ET)
    out.append(sub(st, d))
sashiki = rec('SPEL', FID['CTOB_Sashiki'], out)

# ---- Hashirama Cell Healing Factor ----
# Tier values (percent bonus to health regen). Edit here to rebalance.
TIER = [(1, 15, 50.0), (16, 40, 150.0), (41, 999, 300.0)]   # 41+ was 400: full heal in ~34 s felt too strong
CHAKRA_BONUS = 100.0        # extra while Magicka > 50%
ZETSU_BURST, ZETSU_SECONDS = 1500.0, 5   # 300 only healed ~10%; 1500 is ~40% over 5 s
FORTIFY_HEALRATE_CONST, ALCH_FORTIFY_HEALRATE = 0x0007A0F8, 0x0003EB06   # Skyrim.esm MGEFs (Health regen %)
AB_RESIST_POISON, AB_RESIST_DISEASE = 0x000AA024, 0x000E40D3
GAME_DAYS_PASSED, VENDOR_ITEM_POTION, ITM_POTION_USE = 0x00000039, 0x0008CDEC, 0x000B6435
GET_LEVEL, GET_AV_PERCENT, AV_MAGICKA = 80, 640, 25
OP = {'==': 0x00, '!=': 0x20, '>': 0x40, '>=': 0x60, '<': 0x80, '<=': 0xA0}
def cond(func, op, value, p1=0):   # run on subject, AND with the next condition
    return sub('CTDA', struct.pack('<B3xfHHIIIIi', OP[op], value, func, 0, p1, 0, 0, 0, -1))
def script_mgef(edid, name, flags, cast, scr):
    t, fid, src = ERECS['WindForceFFAimedArea']; assert t == 'MGEF'   # a script-archetype MGEF, used for its DATA layout
    d = bytearray(dict(src)['DATA'])
    for o in MGEF_FID_OFFSETS: struct.pack_into('<I', d, o, 0)
    struct.pack_into('<I', d, 0x00, flags)
    struct.pack_into('<ii', d, 0x0C, -1, -1)          # no magic skill, no resist
    struct.pack_into('<Ii', d, 0x40, 1, -1)            # Script archetype
    struct.pack_into('<II', d, 0x50, cast, 0)          # cast type, Self
    return rec('MGEF', FID[edid], [sub('EDID', z(edid)), sub('VMAD', struct.pack('<hhH', 5, 2, 1) + scr),
                                   sub('FULL', z(name)), sub('DATA', bytes(d)), sub('SNDD', b''), sub('DNAM', z(''))])
NO_DUR, NO_MAG, NO_AREA, HIDE_UI = 0x200, 0x400, 0x800, 0x8000
zetsu_watch = script_mgef('CTOB_ZetsuWatchEffect', 'White Zetsu Armor', NO_DUR | NO_MAG | NO_AREA | HIDE_UI, 0,
    script('CTOB_ZetsuArmorEffect', [p_obj('BurstSpell', FID['CTOB_ZetsuBurst']),
           p_obj('NextAllowedDay', FID['CTOB_ZetsuNextDay']), p_obj('GameDaysPassed', GAME_DAYS_PASSED)]))
cell_effect = script_mgef('CTOB_HashiramaCellEffect', 'Hashirama Cell', NO_DUR | NO_MAG | NO_AREA, 1,
    script('CTOB_HashiramaCellEffect', [p_obj('HealingFactor', FID['CTOB_HashiramaAbility'])]))

ab = [sub('EDID', z('CTOB_HashiramaAbility')), sub('OBND', bytes(12)), sub('FULL', z('Hashirama Cell Healing Factor')),
      sub('DESC', z('The First Hokage\'s cells, grafted into you after Kannabi Bridge, knit your wounds closed. They '
                    'heal you faster as you grow stronger, and faster still while your chakra runs high. Spend it all, '
                    'and the healing stops. In battle they burn your chakra to close wounds as they open.')),
      sub('SPIT', struct.pack('<IIIfIIffI', 0, 0, 4, 0.0, 0, 0, 0.0, 0.0, 0))]   # Ability, constant, self
for lo, hi, mag in TIER:
    ab += [effect(FORTIFY_HEALRATE_CONST, mag, 0), cond(GET_LEVEL, '>=', lo), cond(GET_LEVEL, '<=', hi),
           cond(GET_AV_PERCENT, '>', 0.0, AV_MAGICKA)]
ab += [effect(FORTIFY_HEALRATE_CONST, CHAKRA_BONUS, 0), cond(GET_AV_PERCENT, '>', 0.5, AV_MAGICKA)]
ab += [effect(AB_RESIST_POISON, 100.0, 0), cond(GET_LEVEL, '>=', 41)]
ab += [effect(AB_RESIST_DISEASE, 100.0, 0), cond(GET_LEVEL, '>=', 41)]
ab += [effect(FID['CTOB_ZetsuWatchEffect'], 0.0, 0), cond(GET_LEVEL, '<=', 15)]
healing_ability = rec('SPEL', FID['CTOB_HashiramaAbility'], ab)
zetsu_burst = rec('SPEL', FID['CTOB_ZetsuBurst'], [
    sub('EDID', z('CTOB_ZetsuBurst')), sub('OBND', bytes(12)), sub('FULL', z('White Zetsu Armor')),
    sub('ETYP', u32(EITHER_HAND)), sub('DESC', z('')),
    sub('SPIT', struct.pack('<IIIfIIffI', 0, 0x1, 0, 0.0, 1, 0, 0.0, 0.0, 0)),
    effect(ALCH_FORTIFY_HEALRATE, ZETSU_BURST, 0, ZETSU_SECONDS)])
cell_item = rec('ALCH', FID['CTOB_HashiramaCell'], [
    sub('EDID', z('CTOB_HashiramaCell')), sub('OBND', bytes(12)), sub('FULL', z('Hashirama Cell')),
    sub('KSIZ', u32(1)), sub('KWDA', u32(VENDOR_ITEM_POTION)),
    sub('MODL', z('Clutter\\Potions\\PotionFortifyHealRateExtreme.nif')),
    sub('DATA', struct.pack('<f', 0.5)),
    sub('ENIT', struct.pack('<iIIfI', 1000, 0x1, 0, 0.0, ITM_POTION_USE)),   # value 1000, manual value
    effect(FID['CTOB_HashiramaCellEffect'], 0.0, 0)])
NAKA_SHRINE_INNER_DOOR = 0x05008F7F   # UchihaClan.esp REFR (persistent), inside the Naka Shrine
kannabi_effect = script_mgef('CTOB_KannabiWatchEffect', 'Kannabi Bridge', NO_DUR | NO_MAG | NO_AREA | HIDE_UI, 0,
    script('CTOB_KannabiWatchEffect', [p_obj('HealingFactor', FID['CTOB_HashiramaAbility']),
           p_obj('WatchAbility', FID['CTOB_KannabiWatchAbility']), p_obj('WakeSpot', remap(NAKA_SHRINE_INNER_DOOR, UT)),
           p_obj('KannabiDone', FID['CTOB_KannabiDone'])]))
kannabi_ability = rec('SPEL', FID['CTOB_KannabiWatchAbility'], [
    sub('EDID', z('CTOB_KannabiWatchAbility')), sub('OBND', bytes(12)), sub('FULL', z('Kannabi Bridge')),
    sub('DESC', z('')), sub('SPIT', struct.pack('<IIIfIIffI', 0, 0, 4, 0.0, 0, 0, 0.0, 0.0, 0)),
    effect(FID['CTOB_KannabiWatchEffect'], 0.0, 0)])
kannabi_glob = rec('GLOB', FID['CTOB_KannabiDone'], [sub('EDID', z('CTOB_KannabiDone')), sub('FNAM', b's'),
                                                    sub('FLTV', struct.pack('<f', 0.0))])
zetsu_glob = rec('GLOB', FID['CTOB_ZetsuNextDay'], [sub('EDID', z('CTOB_ZetsuNextDay')), sub('FNAM', b'f'),
                                                    sub('FLTV', struct.pack('<f', 0.0))])

# ---- Sharingan genjutsu ----
HOSTILE, DETRIMENTAL, VOICE_SLOT = 0x1, 0x4, 0x00025BEE
NO_RESIST_SPELL = 0x1 | 0x100000 | 0x200000          # manual cost, ignore resistance, no absorb/reflect
def p_int(name, v): return ws(name) + bytes([3, 1]) + struct.pack('<i', v)
def gen_mgef(edid, name, flags, cast, deliv, scr):
    m = script_mgef(edid, name, flags, cast, scr)
    body = bytearray(m[24:]); i = 0
    while i < len(body):                                # set the delivery in DATA (0x54)
        t = bytes(body[i:i+4]); n = struct.unpack_from('<H', body, i+4)[0]
        if t == b'DATA': struct.pack_into('<I', body, i + 6 + 0x54, deliv)
        i += 6 + n
    return m[:24] + bytes(body)
def gen_spel(edid, name, stype, deliv, mgef, dur, flags, extra=()):
    return rec('SPEL', FID[edid], [sub('EDID', z(edid)), sub('OBND', bytes(12)), sub('FULL', z(name))] + list(extra)
               + [sub('SPIT', struct.pack('<IIIfIIffI', 0, flags, stype, 0.0, 1, deliv, 0.0, 0.0, 0)),
                  effect(FID[mgef], 0.0, 0, dur)])
master = p_obj('Master', FID['CTOB_Quest'])
# Paralysis, not an AI freeze: with AI off the body kept animating ("stasis"). Values as vanilla ParalysisFFAimed
# (Skyrim.esm 0x01EA6E: archetype 21, actor value 53 Paralysis, flags 0x401403) minus its blue hit shader.
PARALYSIS, AV_PARALYSIS, PARALYSIS_FLAGS = 21, 53, 0x401403
def paralysis_mgef(edid, name):
    t, fid, src = ERECS['WindForceFFAimedArea']
    d = bytearray(dict(src)['DATA'])
    for o in MGEF_FID_OFFSETS: struct.pack_into('<I', d, o, 0)
    struct.pack_into('<I', d, 0x00, PARALYSIS_FLAGS)
    struct.pack_into('<ii', d, 0x0C, -1, -1)
    struct.pack_into('<Ii', d, 0x40, PARALYSIS, AV_PARALYSIS)
    struct.pack_into('<II', d, 0x50, 1, 3)                 # fire and forget, target actor
    return rec('MGEF', FID[edid], [sub('EDID', z(edid)), sub('FULL', z(name)), sub('DATA', bytes(d)),
                                   sub('SNDD', b''), sub('DNAM', z(''))])
genjutsu_mgefs = paralysis_mgef('CTOB_GenjutsuFreezeEffect', 'Genjutsu: Sharingan')
genjutsu_mgefs += gen_mgef('CTOB_PuppetEffect', 'Genjutsu: Sharingan Puppet', NO_MAG | NO_AREA, 1, 3,
                           script('CTOB_PuppetEffect', [master]))
genjutsu_mgefs += gen_mgef('CTOB_GenjutsuGazeEffect', 'Genjutsu: Sharingan', NO_DUR | NO_MAG | NO_AREA, 1, 0,
                           script('CTOB_GenjutsuPowerEffect', [master, p_int('Mode', 1)]))
genjutsu_mgefs += gen_mgef('CTOB_PuppetPowerEffect', 'Genjutsu: Sharingan Puppet', NO_DUR | NO_MAG | NO_AREA, 1, 0,
                           script('CTOB_GenjutsuPowerEffect', [master, p_int('Mode', 2)]))
genjutsu_spels = gen_spel('CTOB_GenjutsuFreezeSpell', 'Genjutsu: Sharingan', 0, 3, 'CTOB_GenjutsuFreezeEffect', 4, NO_RESIST_SPELL)
genjutsu_spels += gen_spel('CTOB_PuppetSpell', 'Genjutsu: Sharingan Puppet', 0, 3, 'CTOB_PuppetEffect', 60, NO_RESIST_SPELL)
genjutsu_spels += gen_spel('CTOB_GenjutsuGazePower', 'Genjutsu: Sharingan', 3, 0, 'CTOB_GenjutsuGazeEffect', 0, 0x1,
    [sub('ETYP', u32(VOICE_SLOT)), sub('DESC', z('A single glance is enough. An enemy who meets the eyes of your '
     'Sharingan is caught in the illusion, their body locked rigid until it breaks. The hold lasts longer once the '
     'Mangekyo has awakened.'))])
genjutsu_spels += gen_spel('CTOB_PuppetPower', 'Genjutsu: Sharingan Puppet', 3, 0, 'CTOB_PuppetPowerEffect', 0, 0x1,
    [sub('ETYP', u32(VOICE_SLOT)), sub('DESC', z('This is how the Hidden Mist was ruled for years. Seize a mind with '
     'your Sharingan and its owner fights at your side; with the Mangekyo, even beasts bend to your will. Use it on your '
     'puppet to let them go, but few wake whole, and the weakened never wake at all.'))])

# ---- Rinnegan: Preta Path ----
SEAL_SECONDS, DRAIN_SECONDS, DRAIN_PER_SECOND = 8, 4, 30.0
AV_HEALTH, AV_MAGICKA_I, AV_STAMINA, AV_ABSORB_CHANCE = 24, 25, 26, 83
ABSORB_FLAGS = 0x10201805                 # vanilla AbsorbMagickaConcAimed / EnchAbsorbMagickaFFContact
ABSORB_MAGICKA_SHADER = 0x00058E9B        # shader of vanilla AbsorbMagickaConstant
def value_mgef(edid, name, flags, archetype, av, cast, deliv, shader=0):
    t, fid, src = ERECS['WindForceFFAimedArea']
    d = bytearray(dict(src)['DATA'])
    for o in MGEF_FID_OFFSETS: struct.pack_into('<I', d, o, 0)
    struct.pack_into('<I', d, 0x00, flags)
    struct.pack_into('<ii', d, 0x0C, -1, -1)
    struct.pack_into('<Ii', d, 0x40, archetype, av)
    struct.pack_into('<II', d, 0x50, cast, deliv)
    struct.pack_into('<I', d, 0x5C, shader)
    return rec('MGEF', FID[edid], [sub('EDID', z(edid)), sub('FULL', z(name)), sub('DATA', bytes(d)),
                                   sub('SNDD', b''), sub('DNAM', z(''))])
RECOVER = 0x2
preta_mgefs = value_mgef('CTOB_PretaSealEffect', 'Preta Path: Absorption Seal', RECOVER | NO_AREA, 0, AV_ABSORB_CHANCE, 1, 0,
                         ABSORB_MAGICKA_SHADER)
preta_mgefs += value_mgef('CTOB_PretaDrainMagicka', 'Preta Path: Chakra Absorption', ABSORB_FLAGS, 4, AV_MAGICKA_I, 1, 3)
preta_mgefs += value_mgef('CTOB_PretaDrainStamina', 'Preta Path: Chakra Absorption', ABSORB_FLAGS, 4, AV_STAMINA, 1, 3)
preta_mgefs += gen_mgef('CTOB_PretaSealPowerEffect', 'Preta Path: Absorption Seal', NO_DUR | NO_MAG | NO_AREA, 1, 0,
                        script('CTOB_GenjutsuPowerEffect', [master, p_int('Mode', 3)]))
preta_mgefs += gen_mgef('CTOB_PretaDrainPowerEffect', 'Preta Path: Chakra Absorption', NO_DUR | NO_MAG | NO_AREA, 1, 0,
                        script('CTOB_GenjutsuPowerEffect', [master, p_int('Mode', 4)]))
preta_spels = rec('SPEL', FID['CTOB_PretaSealSpell'], [sub('EDID', z('CTOB_PretaSealSpell')), sub('OBND', bytes(12)),
    sub('FULL', z('Preta Path: Absorption Seal')), sub('SPIT', struct.pack('<IIIfIIffI', 0, NO_RESIST_SPELL, 0, 0.0, 1, 0, 0.0, 0.0, 0)),
    sub('EFID', u32(FID['CTOB_PretaSealEffect'])) + sub('EFIT', struct.pack('<fII', 100.0, 0, SEAL_SECONDS))])
preta_spels += rec('SPEL', FID['CTOB_PretaDrainSpell'], [sub('EDID', z('CTOB_PretaDrainSpell')), sub('OBND', bytes(12)),
    sub('FULL', z('Preta Path: Chakra Absorption')), sub('SPIT', struct.pack('<IIIfIIffI', 0, NO_RESIST_SPELL, 0, 0.0, 1, 3, 0.0, 0.0, 0)),
    sub('EFID', u32(FID['CTOB_PretaDrainMagicka'])) + sub('EFIT', struct.pack('<fII', DRAIN_PER_SECOND, 0, DRAIN_SECONDS)),
    sub('EFID', u32(FID['CTOB_PretaDrainStamina'])) + sub('EFIT', struct.pack('<fII', DRAIN_PER_SECOND, 0, DRAIN_SECONDS))])
preta_spels += gen_spel('CTOB_PretaSealPower', 'Preta Path: Absorption Seal', 3, 0, 'CTOB_PretaSealPowerEffect', 0, 0x1,
    [sub('ETYP', u32(VOICE_SLOT)), sub('DESC', z('The Preta Path devours chakra. For a few heartbeats, every jutsu and '
     'spell that strikes you is swallowed whole and becomes your own. Steel and arrows still bite.'))])
preta_spels += gen_spel('CTOB_PretaDrainPower', 'Preta Path: Chakra Absorption', 3, 0, 'CTOB_PretaDrainPowerEffect', 0, 0x1,
    [sub('ETYP', u32(VOICE_SLOT)), sub('DESC', z('Lay hold of the enemy before you and the Preta Path draws out their '
     'chakra and strength, pouring it into you. Drained dry, they fall.'))])

# ---- Unmasked: Will of the Uchiha ----
GET_EQUIPPED = 182
MASK_ENCH = [(0x000B7A35, 25.0), (0x0007A0FD, 120.0), (0x00049504, 60.0), (0x0007A0F2, 20.0), (0x0007A0F6, 20.0)]
def eq(item, value, or_next=False):
    return sub('CTDA', struct.pack('<B3xfHHIIIIi', 0x00 | (0x01 if or_next else 0), value, GET_EQUIPPED, 0, item, 0, 0, 0, -1))
UNMASKED_CONDS = (eq(u('aaaTobiWarOutfit'), 1.0, True) + eq(u('aaaTobiWarOutfitUnenchanted'), 1.0)
                  + eq(u('aaaTobiWarBoots'), 1.0, True) + eq(u('aaaTobiWarBootsUnenchanted'), 1.0)
                  + eq(u('aaaTobiWarGloves'), 1.0, True) + eq(u('aaaTobiWarGlovesUnenchanted'), 1.0)
                  + eq(u('aaaTobiWarMask'), 0.0) + eq(u('aaaTobiWarMaskUnenchanted'), 0.0))
unmasked_mgef = script_mgef('CTOB_UnmaskedEffect', 'Unmasked: Will of the Uchiha', NO_DUR | NO_MAG | NO_AREA, 0,
                            script('CTOB_ChakraSurgeEffect', []))
unmasked_mgef = rec('MGEF', FID['CTOB_UnmaskedEffect'], [unmasked_mgef[24:].replace(sub('DNAM', z('')), sub('DNAM', z(
    'Without the mask, nothing is held back. When your chakra runs low in battle, it surges back, twice each fight, '
    'and your Kamui answers faster and costs less.')))])
ua = [sub('EDID', z('CTOB_UnmaskedAbility')), sub('OBND', bytes(12)), sub('FULL', z('Unmasked: Will of the Uchiha')),
      sub('DESC', z('In the war outfit, boots and gloves, Obito is as strong without the mask as with it.')),
      sub('SPIT', struct.pack('<IIIfIIffI', 0, 0, 4, 0.0, 0, 0, 0.0, 0.0, 0))]     # Ability, constant, self
for mgef_id, mag in MASK_ENCH:
    ua += [effect(mgef_id, mag, 0), UNMASKED_CONDS]
ua += [effect(FID['CTOB_UnmaskedEffect'], 0.0, 0), UNMASKED_CONDS]
unmasked_ability = rec('SPEL', FID['CTOB_UnmaskedAbility'], ua)

# ---- Rinnegan rework ----
AV_DAMAGE_RESIST, AV_SPEED_MULT, DESTRUCTION, ROD_MAGICKA = 39, 30, 20, 35
DEBUFF = HOSTILE | DETRIMENTAL | RECOVER | NO_AREA
def described(m, edid, text):         # put a description (DNAM) on an MGEF built above
    return rec('MGEF', FID[edid], [m[24:].replace(sub('DNAM', z('')), sub('DNAM', z(text)))])
rinne_mgefs = described(value_mgef('CTOB_ExposedEffect', 'Exposed', DEBUFF, 0, AV_DAMAGE_RESIST, 1, 3),
    'CTOB_ExposedEffect', 'Their guard is broken: <mag> less armour, and the Human Path can tear their soul out.')
rinne_mgefs += described(value_mgef('CTOB_PinnedEffect', 'Pinned', DEBUFF, 0, AV_SPEED_MULT, 1, 3),
    'CTOB_PinnedEffect', 'Chakra receivers in the body: <mag>% slower. Bansho Tenin tears at them.')
def debuff_spel(edid, name, mgef, mag, dur):
    return rec('SPEL', FID[edid], [sub('EDID', z(edid)), sub('OBND', bytes(12)), sub('FULL', z(name)),
        sub('SPIT', struct.pack('<IIIfIIffI', 0, NO_RESIST_SPELL, 0, 0.0, 1, 3, 0.0, 0.0, 0)),
        sub('EFID', u32(FID[mgef])) + sub('EFIT', struct.pack('<fII', mag, 0, dur))])
rinne_spels = debuff_spel('CTOB_ExposedSpell', 'Exposed', 'CTOB_ExposedEffect', 250.0, 6)
rinne_spels += debuff_spel('CTOB_PinnedSpell', 'Pinned', 'CTOB_PinnedEffect', 50.0, 8)

# the black rod: Uchiha Clan Additions' thrown Chakra Disruptive Blade (its masters are our first seven, same order,
# and the copied fields only point at Skyrim.esm forms, so only its own records need new IDs)
def additions_records(path, want):
    buf = open(path, 'rb').read(); out = {}
    hsize = struct.unpack_from('<I', buf, 4)[0]
    def walk(o, e):
        while o < e:
            t = buf[o:o+4].decode('latin1'); n = struct.unpack_from('<I', buf, o+4)[0]
            if t == 'GRUP': walk(o+24, o+n); o += n; continue
            fl, fid = struct.unpack_from('<II', buf, o+8); b = buf[o+24:o+24+n]; o += 24 + n
            if fid & 0xFFFFFF in want:
                if fl & 0x40000: b = zlib.decompress(b[4:])
                out[fid & 0xFFFFFF] = list(subs_of(b))
    walk(24 + hsize, len(buf))
    return out
A = additions_records(ADDITIONS, {0x00A690, 0x00A691, 0x00CE30, 0x00CE31})
def first(recsubs, t): return [d for k, d in recsubs if k == t][0]
rod_proj = rec('PROJ', FID['CTOB_RodProjectile'], [sub('EDID', z('CTOB_RodProjectile')), sub('OBND', bytes(12)),
    sub('MODL', first(A[0x00A690], 'MODL')), sub('DATA', first(A[0x00A690], 'DATA')), sub('NAM1', b'\0'),
    sub('VNAM', first(A[0x00A690], 'VNAM'))])
assert struct.unpack_from('<I', first(A[0x00CE30], 'SNAM'))[0] >> 24 == 0
rod_ipct = rec('IPCT', FID['CTOB_RodImpact'], [sub('EDID', z('CTOB_RodImpact')), sub('MODL', first(A[0x00CE30], 'MODL')),
    sub('DATA', first(A[0x00CE30], 'DATA')), sub('DODT', first(A[0x00CE30], 'DODT')), sub('SNAM', first(A[0x00CE30], 'SNAM'))])
pairs = []
for k, d in A[0x00CE31]:
    if k == 'PNAM':
        mat, imp = struct.unpack('<II', d)
        assert mat >> 24 == 0 and imp & 0xFFFFFF == 0x00CE30
        pairs.append(sub('PNAM', struct.pack('<II', mat, FID['CTOB_RodImpact'])))
rod_ipds = rec('IPDS', FID['CTOB_RodImpactSet'], [sub('EDID', z('CTOB_RodImpactSet'))] + pairs)
rod_mgef = gen_mgef('CTOB_RodEffect', 'Chakra Receiver', HOSTILE | DETRIMENTAL | NO_DUR | NO_MAG | NO_AREA, 1, 2,
                    script('CTOB_ReceiverRodEffect', [master]))
body = bytearray(rod_mgef[24:]); i = 0
while i < len(body):
    t = bytes(body[i:i+4]); n = struct.unpack_from('<H', body, i+4)[0]
    if t == b'DATA':
        struct.pack_into('<I', body, i + 6 + 0x48, FID['CTOB_RodProjectile'])
        struct.pack_into('<I', body, i + 6 + 0x64, FID['CTOB_RodImpactSet'])
        struct.pack_into('<f', body, i + 6 + 0x04, 1.4)                  # base cost and school, as the Uchiha blade
        struct.pack_into('<i', body, i + 6 + 0x0C, DESTRUCTION)
    i += 6 + n
sndd = first(A[0x00A691], 'SNDD')
assert all(struct.unpack_from('<I', sndd, o)[0] >> 24 == 0 for o in range(4, len(sndd), 8))
body = bytes(body).replace(sub('SNDD', b''), sub('SNDD', sndd))
rinne_mgefs += rec('MGEF', FID['CTOB_RodEffect'], [body])
rinne_mgefs += described(gen_mgef('CTOB_RodsPowerEffect', 'Outer Path: Chakra Receivers', NO_DUR | NO_MAG | NO_AREA, 1, 0,
                                  script('CTOB_GenjutsuPowerEffect', [master, p_int('Mode', 5)])),
    'CTOB_RodsPowerEffect', 'Three chakra receivers fly at the enemy you aim at.')
rinne_spels += gen_spel('CTOB_RodSpell', 'Chakra Receiver', 0, 2, 'CTOB_RodEffect', 0, NO_RESIST_SPELL)
rinne_spels += rec('SPEL', FID['CTOB_RodsPower'], [sub('EDID', z('CTOB_RodsPower')), sub('OBND', bytes(12)),
    sub('FULL', z('Outer Path: Chakra Receivers')), sub('ETYP', u32(EITHER_HAND)),
    sub('DESC', z('The black receivers the Paths of Pain were fed chakra through, shot from your palm. Each rod '
     'wounds, drains their chakra and pins them; three in one enemy hold them still. Pull a pinned enemy with '
     'Bansho Tenin and the rods tear free.')),
    sub('SPIT', struct.pack('<IIIfIIffI', ROD_MAGICKA, 0x1, 0, 0.0, 1, 2, 0.0, 0.0, 0)),   # manual cost, F&F, aimed
    effect(FID['CTOB_RodEffect'], 0.0, 0)])

# ---- Eye Adaptation ----
GET_GLOBAL_VALUE, NIGHT_EYE_TRANSITION, FORTIFY_MAGICKA_RATE = 74, 0x000EFC75, 0x0007A0FD
eye_mgef = described(value_mgef('CTOB_EyeAdaptEffect', 'Eye Adaptation', NO_DUR | NO_MAG | NO_AREA, 1, -1, 0, 0),
    'CTOB_EyeAdaptEffect', "The longer you fight with the Sharingan open, the less it costs you. Hashirama's cells "
    'carry half the burden already. At full adaptation the eye costs nothing and your chakra flows faster while it '
    'is open.')
eye_globs = rec('GLOB', FID['CTOB_EyeMastery'], [sub('EDID', z('CTOB_EyeMastery')), sub('FNAM', b'f'),
                                               sub('FLTV', struct.pack('<f', 0.0))])
eye_globs += rec('GLOB', FID['CTOB_SetEyeMastery'], [sub('EDID', z('CTOB_SetEyeMastery')), sub('FNAM', b'f'),
                                                   sub('FLTV', struct.pack('<f', -1.0))])
eye_ability = rec('SPEL', FID['CTOB_EyeAdaptAbility'], [sub('EDID', z('CTOB_EyeAdaptAbility')), sub('OBND', bytes(12)),
    sub('FULL', z('Eye Adaptation')),
    sub('DESC', z("Obito kept his Sharingan open even at death's door. Your eye is growing used to the strain.")),
    sub('SPIT', struct.pack('<IIIfIIffI', 0, 0, 4, 0.0, 0, 0, 0.0, 0.0, 0)),
    effect(FID['CTOB_EyeAdaptEffect'], 0.0, 0),
    effect(FORTIFY_MAGICKA_RATE, 10.0, 0), cond(GET_GLOBAL_VALUE, '>=', 100.0, FID['CTOB_EyeMastery']),
    cond(GET_GLOBAL_VALUE, '==', 2.0, NIGHT_EYE_TRANSITION)])

# ---- Hashirama cells in combat ----
OVERGROWTH_SLOW, OVERGROWTH_SECONDS = 40.0, 4
cell_combat_mgefs = described(value_mgef('CTOB_OvergrowthEffect', 'Cell Overgrowth', DETRIMENTAL | RECOVER | NO_AREA,
    0, AV_SPEED_MULT, 1, 0), 'CTOB_OvergrowthEffect', "Hashirama's cells are running wild: <mag>% slower, and they "
    'will not heal you until they settle.')
cell_combat_mgefs += described(script_mgef('CTOB_CellCombatEffect', 'Hashirama Cells: Combat Regeneration',
    NO_DUR | NO_MAG | NO_AREA, 0, script('CTOB_CellCombatEffect', [p_obj('OvergrowthSpell', FID['CTOB_OvergrowthSpell'])])),
    'CTOB_CellCombatEffect', 'In battle the cells burn chakra to heal you, faster the closer you are to death. A blow '
    'that leaves you below 30% health triggers Cell Activation (once a minute); a heavy blow regrows half its damage. '
    'Lean on them too hard and they run wild.')
cell_combat_spels = rec('SPEL', FID['CTOB_OvergrowthSpell'], [sub('EDID', z('CTOB_OvergrowthSpell')), sub('OBND', bytes(12)),
    sub('FULL', z('Cell Overgrowth')), sub('SPIT', struct.pack('<IIIfIIffI', 0, NO_RESIST_SPELL, 0, 0.0, 1, 0, 0.0, 0.0, 0)),
    sub('EFID', u32(FID['CTOB_OvergrowthEffect'])) + sub('EFIT', struct.pack('<fII', OVERGROWTH_SLOW, 0, OVERGROWTH_SECONDS))])
cell_combat_spels += rec('SPEL', FID['CTOB_CellCombatAbility'], [sub('EDID', z('CTOB_CellCombatAbility')),
    sub('OBND', bytes(12)), sub('FULL', z('Hashirama Cells: Combat Regeneration')),
    sub('DESC', z("Hashirama never needed hand seals to heal. His cells close your wounds mid-battle, paid for in "
                  'chakra, but they must be held in check.')),
    sub('SPIT', struct.pack('<IIIfIIffI', 0, 0, 4, 0.0, 0, 0, 0.0, 0.0, 0)),
    effect(FID['CTOB_CellCombatEffect'], 0.0, 0)])

# ---- Preta Path: Chakra Grasp ----
PEAK_VALUE_MOD, AV_MAGICKA_RATE_MULT, CONCENTRATION = 34, 156, 2
DRAINED_PCT, DRAINED_SECONDS, GRASP_COST = 75.0, 15, 10
grasp_mgefs = described(value_mgef('CTOB_DrainedEffect', 'Drained', DEBUFF, PEAK_VALUE_MOD, AV_MAGICKA_RATE_MULT, 1, 3),
    'CTOB_DrainedEffect', 'The Preta Path has drunk their chakra: it returns <mag>% slower.')
grasp_mgefs += described(script_mgef('CTOB_PretaTouchEffect', 'Preta Path: Chakra Grasp', NO_DUR | NO_MAG | NO_AREA,
    CONCENTRATION, script('CTOB_PretaTouchEffect', [p_obj('DrainedSpell', FID['CTOB_DrainedSpell']),
                                                    p_obj('AbsorbShader', ABSORB_MAGICKA_SHADER)])),
    'CTOB_PretaTouchEffect', "Hold an enemy within arm's reach and their chakra flows into you.")
grasp_spels = debuff_spel('CTOB_DrainedSpell', 'Drained', 'CTOB_DrainedEffect', DRAINED_PCT, DRAINED_SECONDS)
grasp_spels += rec('SPEL', FID['CTOB_PretaTouchSpell'], [sub('EDID', z('CTOB_PretaTouchSpell')), sub('OBND', bytes(12)),
    sub('FULL', z('Preta Path: Chakra Grasp')), sub('ETYP', u32(EITHER_HAND)),
    sub('DESC', z('The Preta body feeds by touch. Keep your hand on an enemy for a few heartbeats and you tear '
     '100 chakra out of them and into yourself, leaving them Drained: their chakra crawls back far slower.')),
    sub('SPIT', struct.pack('<IIIfIIffI', GRASP_COST, 0x1, 0, 0.0, CONCENTRATION, 0, 0.0, 0.0, 0)),  # manual cost/s, self
    effect(FID['CTOB_PretaTouchEffect'], 0.0, 0)])

# ---- Ninja Travel ----
travel_mgef = described(script_mgef('CTOB_NinjaTravelEffect', 'Ninja Travel', NO_DUR | NO_MAG | NO_AREA, 0,
    script('CTOB_NinjaTravelEffect', [])), 'CTOB_NinjaTravelEffect', 'Out of battle, a long sprint builds '
    'momentum: up to 60% faster, burning a little chakra. At full speed you leap like a shinobi through the trees, '
    'land without harm and run across water. The first blow struck out of a full sprint staggers.')
travel_ability = rec('SPEL', FID['CTOB_NinjaTravelAbility'], [sub('EDID', z('CTOB_NinjaTravelAbility')),
    sub('OBND', bytes(12)), sub('FULL', z('Ninja Travel')),
    sub('DESC', z('Every shinobi learns to pour chakra into their legs. Distances that take others days take you hours.')),
    sub('SPIT', struct.pack('<IIIfIIffI', 0, 0, 4, 0.0, 0, 0, 0.0, 0.0, 0)),
    effect(FID['CTOB_NinjaTravelEffect'], 0.0, 0)])

# ---- Bakufu Ranbu: Kamui vortex (script effect; needs gen_mgef, defined after the spell) ----
bakufu_vortex = gen_mgef('CTOB_BakufuVortexEffect', 'Bakufu Ranbu', HOSTILE | DETRIMENTAL | NO_MAG | HIDE_UI, 1, 2,
    script('CTOB_BakufuVortexEffect', [p_obj('ExposedSpell', FID['CTOB_ExposedSpell']),
                                       p_obj('KamuiEthereal', u('aaaTobiBecomeEthereal'))]))

# ---- quest ----
MOKUTON = ['aaaMokutonDeepForestEmergenceSpell', 'aaaMokutonWoodPrisonSpell', 'aaaMokutonDeepForestBloomSpell',
           'aaaMokutonWoodCloneSpell', 'aaaMokutonWoodCloneSettingsSpell', 'aaaMokutonWoodDragonSpell',
           'aaaMokutonTreeBindBurialSpell']
path_spells = [u(e) for e in MOKUTON] + [FID['CTOB_Sashiki'], FID['CTOB_BakufuRanbu']]
qvmad = struct.pack('<hhH', 5, 2, 4) + script('CTOB_TobiPathQuestScript', [
    p_obj('aaaPathTobi', u('aaaPathTobi')), p_objs('PathSpells', path_spells),
    p_obj('KamuiEthereal', u('aaaTobiBecomeEthereal')), p_obj('IzanagiSpell', u('aaaIzanagiSpell')),
    p_obj('IzanagiPower', u('aaaIzanagiPower')), p_obj('RinneganAbility', u('aaaRinneganAbility')),
    p_obj('RinneRebirthSpell', u('aaaRinneganGedoRebirthSpell')), p_obj('HashiramaCell', FID['CTOB_HashiramaCell']),
    p_obj('HealingFactor', FID['CTOB_HashiramaAbility']), p_obj('KannabiWatch', FID['CTOB_KannabiWatchAbility']),
    p_obj('KannabiDone', FID['CTOB_KannabiDone'])]) \
    + script('CTOB_GenjutsuQuestScript', []) + script('CTOB_RinneganQuestScript', []) + script('CTOB_EyeMasteryScript', []) \
    + bytes([2]) + struct.pack('<H', 0) + ws('') + struct.pack('<H', 0)
qust = rec('QUST', FID['CTOB_Quest'], [
    sub('EDID', z('CTOB_Quest')), sub('VMAD', qvmad), sub('FULL', z('Obito Tobi Path Additions')),
    sub('DNAM', struct.pack('<HBBII', 0x0011, 50, 0, 0, 0)), sub('NEXT', b''), sub('ANAM', u32(0))])

groups = (grup('GLOB', zetsu_glob + kannabi_glob + eye_globs)
          + grup('MGEF', sashiki_mgef + bakufu_carrier + bakufu_damage + bakufu_burn + bakufu_vortex + zetsu_watch + cell_effect + kannabi_effect + genjutsu_mgefs + preta_mgefs + unmasked_mgef + rinne_mgefs + eye_mgef + cell_combat_mgefs + grasp_mgefs + travel_mgef)
          + grup('PROJ', bakufu_proj + rod_proj) + grup('IPCT', rod_ipct) + grup('IPDS', rod_ipds) + grup('SPEL', bakufu + sashiki + healing_ability + zetsu_burst + kannabi_ability + genjutsu_spels + preta_spels + unmasked_ability + rinne_spels + eye_ability + cell_combat_spels + grasp_spels + travel_ability) + grup('ALCH', cell_item)
          + grup('EXPL', sashiki_expl) + grup('QUST', qust))
hdr = [sub('HEDR', struct.pack('<fII', 1.7, len(FID) + 7, 0x800 + len(FID))), sub('CNAM', z('Claude')),
       sub('SNAM', z('Obito Tobi Path Additions'))]
for m in MASTERS: hdr += [sub('MAST', z(m)), sub('DATA', bytes(8))]
open(OUT, 'wb').write(rec('TES4', 0, hdr, flags=0x200) + groups)
print('wrote', OUT)
for k, v in FID.items(): print(f'  {v:08X} {k}')
print('  path spells:', ' '.join(f'{x:08X}' for x in path_spells))
