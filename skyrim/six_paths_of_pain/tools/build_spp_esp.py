"""Build SixPathsOfPain.esp: shared records (steps 1-2) + Yagura vertical slice (steps 3-5).

Usage: build_spp_esp.py <Skyrim.esm> <Elemental Destruction Magic Redux.esp> <naruto overhaul.esp> <out.esp> [<[Odd] Sakura.esp>]

Vanilla records are cloned from Skyrim.esm and edited, so layouts match what the CK writes.
Jutsu are cloned from Elemental Destruction Magic Redux (EDM) spells and renamed.

Object IDs (low 12 bits) must never be reordered: saves reference them. Append new records only.
"""
import os, struct, sys, zlib

SKYRIM, EDM, NARUTO, OUT = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
SAKURA = sys.argv[5] if len(sys.argv) > 5 else r'C:\games\ModOrganizer\Skyrim Special Edition\mods\Odd - Sakura Outfit CBBE 3BA\[Odd] Sakura.esp'
MASTERS = ['Skyrim.esm', 'Update.esm', 'Dawnguard.esm', 'Dragonborn.esm',
           'naruto overhaul.esp', 'UchihaClan.esp', 'Naruto-Hair-Pack.esp',
           'Elemental Destruction Magic Redux.esp', 'High Poly Head.esm', "KS Hairdo's.esp",
           'Jinxxed Followers - Hinata Hyuga.esp', '[Odd] Sakura.esp']
OWN = len(MASTERS) << 24
FID = {n: OWN | (0x800 + i) for i, n in enumerate([
    'SPP_SixPathsFaction', 'SPP_PathsState', 'SPP_AkatsukiOutfit', 'SPP_AkatsukiOutfitHan',
    'SPP_EdoRegenEffect', 'SPP_EdoTenseiAbility', 'SPP_CSJinchuriki', 'SPP_CSJinchurikiBrawler',
    'SPP_ClassJinchuriki',
    # steps 3-5
    'SPP_SixPathsQuest', 'SPP_PathFollowPlayer', 'SPP_PathWait', 'SPP_Yagura',
    'SPP_CmdEffectCommand', 'SPP_CmdEffectSummon', 'SPP_CmdEffectRelease',
    'SPP_PowerCommand', 'SPP_PowerSummon', 'SPP_PowerRelease',
    'SPP_YaguraRef', 'SPP_HomeMarker',
    # conjuration summon (testing powers without recruiting)
    'SPP_YaguraSummon', 'SPP_SummonYaguraEffect', 'SPP_SummonYagura',
    # Yagura's Three-Tails kit (EDM water clones)
    'SPP_JutsuWaterBullet', 'SPP_JutsuWaterShockwave', 'SPP_JutsuWaterSharkBullet',
    'SPP_JutsuCoralPalm', 'SPP_JutsuThreeTailsCloak', 'SPP_JutsuGreatTsunami',
    # Utakata (Six-Tails) + the summon-spell list the quest script hands out
    'SPP_SummonSpells',
    'SPP_Utakata', 'SPP_UtakataSummon', 'SPP_SummonUtakataEffect', 'SPP_SummonUtakata', 'SPP_UtakataRef',
    'SPP_BubbleFXEffect', 'SPP_JutsuExplodingBubbles', 'SPP_JutsuBubbleBurst', 'SPP_JutsuBubblePrison',
    'SPP_JutsuAlkaliSpray', 'SPP_JutsuSixTailsCloak',
    'SPP_PathRefs',
    # Roushi (Four-Tails, Lava Release)
    'SPP_Roushi', 'SPP_RoushiSummon', 'SPP_SummonRoushiEffect', 'SPP_SummonRoushi', 'SPP_RoushiRef',
    'SPP_JutsuLavaGlobs', 'SPP_JutsuMoltenBoulder', 'SPP_JutsuMagmaSpikes', 'SPP_JutsuLavaCloak',
    # Han (Five-Tails, Boil Release)
    'SPP_Han', 'SPP_HanSummon', 'SPP_SummonHanEffect', 'SPP_SummonHan', 'SPP_HanRef',
    'SPP_JutsuScaldingSteam', 'SPP_JutsuSteamExplosion', 'SPP_JutsuSteamArmor',
    # Fuu (Seven-Tails, insects + wings)
    'SPP_Fuu', 'SPP_FuuSummon', 'SPP_SummonFuuEffect', 'SPP_SummonFuu', 'SPP_FuuRef', 'SPP_HairColorMint',
    'SPP_JutsuInsectSwarm', 'SPP_JutsuScalePowder', 'SPP_JutsuWingTornado', 'SPP_JutsuWingGale',
    'SPP_JutsuSevenTailsCloak',
    # Yugito (Two-Tails, Matatabi's flames)
    'SPP_Yugito', 'SPP_YugitoSummon', 'SPP_SummonYugitoEffect', 'SPP_SummonYugito', 'SPP_YugitoRef',
    'SPP_JutsuWispFireball', 'SPP_JutsuCatFlameBreath', 'SPP_JutsuPhoenixSageFire', 'SPP_JutsuFlameInferno',
    'SPP_JutsuTwoTailsCloak',
    # Yugito's RaceMenu face (hair tint from her preset)
    'SPP_HairColorYugito',
    # Yugito's own body (Twins / Atomic Heart 3BA build, copied from Ashe's) + her Hinata-based outfit
    'SPP_YugitoSkin', 'SPP_YugitoTorsoAA', 'SPP_YugitoHandsAA', 'SPP_YugitoFeetAA', 'SPP_YugitoOutfit',
    # Yugito's recoloured Sakura (Boruto-era) pieces: own meshes/textures, Sakura's records untouched
    'SPP_YugitoSakuraTop', 'SPP_YugitoSakuraTopAA', 'SPP_YugitoSakuraSleeves', 'SPP_YugitoSakuraSleevesAA',
    'SPP_YugitoSakuraShorts', 'SPP_YugitoSakuraShortsAA',
    # Yugito's Kumogakure forehead protector (Sakura's black headband, cloud symbol on the plate)
    'SPP_YugitoHeadband', 'SPP_YugitoHeadbandAA',
    # Han's white lower-face mask (Wet and Cold's 'Face Cover', own retextured copy; no Wet and Cold master)
    'SPP_HanMask', 'SPP_HanMaskAA',
    # Han's recoloured Senju outfit / boots (unused since the samurai set) and crimson kasa (own meshes+textures)
    'SPP_HanArmor', 'SPP_HanArmorAA', 'SPP_HanBoots', 'SPP_HanBootsAA', 'SPP_HanHat', 'SPP_HanHatAA',
    # Roushi: Senju outfit recoloured magenta/brown + Tobi's war sandals with dark wraps
    'SPP_RoushiArmor', 'SPP_RoushiArmorAA', 'SPP_RoushiBoots', 'SPP_RoushiBootsAA', 'SPP_RoushiOutfit',
    # Han v2: Blades Samurai Armour's Do-maru set (crimson), replacing his recoloured Senju outfit
    'SPP_HanDomaru', 'SPP_HanDomaruAA', 'SPP_HanSuneate', 'SPP_HanSuneateAA', 'SPP_HanKote', 'SPP_HanKoteAA',
    # Utakata: light-blue robe with orange sash (samurai mod's monk robe recoloured) + Zori sandals
    'SPP_UtakataRobe', 'SPP_UtakataRobeAA', 'SPP_UtakataSandals', 'SPP_UtakataSandalsAA', 'SPP_UtakataOutfit'])}
assert FID['SPP_SummonYagura'] & 0xFFF == 0x817   # older saves got this one by ID
assert FID['SPP_SummonSpells'] & 0xFFF == 0x81E   # hard-coded in SPP_SixPathsQuestScript.GivePowers
assert FID['SPP_PathRefs'] & 0xFFF == 0x82A       # hard-coded in SPP_SixPathsQuestScript.FillNewPaths

# --- external forms, indexed by OUR master list --------------------------------
PLAYER_REF = 0x00000014
PLAYER_FACTION = 0x00000DB1
CURRENT_FOLLOWER_FACTION = 0x0005C84E
AB_RESIST_POISON = 0x000AA024
AB_RESIST_DISEASE = 0x000E40D3
EITHER_HAND, VOICE_SLOT = 0x00013F44, 0x00025BEE
ACTOR_TYPE_NPC = 0x00013794
XMARKER_HEADING = 0x00000034
QASMOKE = 0x00032AE7
SANDBOX_EDITOR_LOC = 0x0010F587          # DefaultSandboxEditorLocation1024NoConv
HAIR_GREY = 0x000A0438                   # HairColor13BrightGrey
AKA_ROBE, AKA_BOOTS, AKA_HAT = 0x051D03BF, 0x051D03C0, 0x051C653B   # UchihaClan.esp
RING_PAIN = 0x040E3C67                                              # naruto overhaul.esp
EYES_SHARINGAN_R_RINNEGAN_L = 0x0401F6B2  # naruto overhaul (UchihaClan overrides its meshes); extra part = left Rinnegan
HAIR_OBITO_TEEN = 0x06008939              # Naruto-Hair-Pack.esp
SCAR, NO_BEARD, BROWS = 0x000E4E2B, 0x000F5009, 0x000C7170          # Belrand's, kept
HAIR_ITACHI = 0x060022EB                  # Naruto-Hair-Pack.esp
HAIR_BLUE_BLACK = 0x000A0435              # HairColor10BlueBlack
NO_SCAR, BROWS_03 = 0x0008555F, 0x0005107F                         # Marcurio's, kept
BUBBLES_EFSH = 0x04074DA5                 # naruto overhaul A0Bubblesfxs (unused there; FXBubble01.dds)
PARALYSIS_FF_AIMED = 0x0001EA6E
FIRE_DAMAGE_FF_AIMED = 0x00012F03       # vanilla Firebolt's damage effect (with its burning hit shader)
HAIR_REDGUARD1, BEARD_41, BROWS_05 = 0x00051403, 0x000CDB77, 0x000C7122   # Stenvar's, kept
HAIR_AUBURN = 0x000A0431                 # HairColor06Auburn: closest vanilla colour to Roushi's red
FIRE_DAMAGE_CONC_AIMED = 0x00013CA9      # vanilla Flames' damage effect
CHAKRA_FIST_NPC = 0x040C61E4             # naruto overhaul: invisible hand-to-hand weapon, 50 dmg + knockback
HAIR_NORD01, BROWS_08 = 0x00051507, 0x000C716E                     # Vorstag's, kept
HAIR_DARK_BROWN = 0x000A0433
EYES_F_SHARINGAN_R_RINNEGAN_L = 0x0504657F  # UchihaClan female split eyes; extra part = left Rinnegan
BROWS_F02, NO_GASH_F = 0x000E4D88, 0x000EC1B2                     # Sayma's, kept
HAIR_F_IMPERIAL1 = 0x0010F79E             # HairShortHumanF: short bob
FEMALE_YOUNG_EAGER = 0x00013ADC
HAIR_HINATA = 0x060093FF                 # Naruto-Hair-Pack.esp: long straight hair
HAIR_BRIGHT_BLOND = 0x000A042F           # HairColor03BrightBlond
HPH_FEMALE_HEAD_NORD = 0x08000A06        # High Poly Head.esm 00KLH_FemaleHeadNord (softer, high-poly female head)
# KS Hairdo's.esp 0Traveler (static). The SMP version (KSHairdosSMP.esp KSSMP_Traveler) can't be baked into
# NPC FaceGen from a RaceMenu export: its physics bones come out flattened/renamed -> spike, then vanishing.
HAIR_KS_TRAVELER = 0x0902A0E0
MOUTH_F_DEFAULT, BROWS_F07 = 0x0005150F, 0x000E4DA1
HINATA_HOODIE, HINATA_PANTS, HINATA_SHOES = 0x0A0036DD, 0x0A0036E0, 0x0A0036DF   # Jinxxed Hinata follower
NAKED_TORSO, NAKED_HANDS, NAKED_FEET = 0x00000D67, 0x00000D6C, 0x00000D6E
SAKURA_SHOES, SAKURA_LEG_POUCH = 0x0B000D6A, 0x0B000D70                  # [Odd] Sakura.esp, used as-is
NORD_RACE = 0x00013746
YAGURA_SPELLS = [FID[n] for n in ('SPP_JutsuWaterBullet', 'SPP_JutsuWaterShockwave', 'SPP_JutsuWaterSharkBullet',
                                  'SPP_JutsuCoralPalm', 'SPP_JutsuThreeTailsCloak', 'SPP_JutsuGreatTsunami')]
ROUSHI_SPELLS = [FID[n] for n in ('SPP_JutsuLavaGlobs', 'SPP_JutsuMoltenBoulder', 'SPP_JutsuMagmaSpikes',
                                  'SPP_JutsuLavaCloak')]
# Steam Explosion (ranged) kept him at a distance in testing; he only gets close-range jutsu now.
HAN_SPELLS = [FID[n] for n in ('SPP_JutsuScaldingSteam', 'SPP_JutsuSteamArmor')]
FUU_SPELLS = [FID[n] for n in ('SPP_JutsuInsectSwarm', 'SPP_JutsuScalePowder', 'SPP_JutsuWingTornado',
                               'SPP_JutsuWingGale', 'SPP_JutsuSevenTailsCloak')]
YUGITO_SPELLS = [FID[n] for n in ('SPP_JutsuWispFireball', 'SPP_JutsuCatFlameBreath', 'SPP_JutsuPhoenixSageFire',
                                  'SPP_JutsuFlameInferno', 'SPP_JutsuTwoTailsCloak')]
UTAKATA_SPELLS = [FID[n] for n in ('SPP_JutsuExplodingBubbles', 'SPP_JutsuBubbleBurst', 'SPP_JutsuBubblePrison',
                                   'SPP_JutsuAlkaliSpray', 'SPP_JutsuSixTailsCloak')]

# --- binary helpers -------------------------------------------------------------
def sub(t, data): return t.encode() + struct.pack('<H', len(data)) + data
def z(s): return s.encode('cp1252') + b'\0'
def u32(*v): return struct.pack('<%dI' % len(v), *v)
def f32(*v): return struct.pack('<%df' % len(v), *v)
def ws(s): b = s.encode('cp1252'); return struct.pack('<H', len(b)) + b

def rec(t, fid, subs, flags=0, ver=44):
    body = b''.join(subs)
    return t.encode() + struct.pack('<IIIIHH', len(body), flags, fid, 0, ver, 0) + body

def grup(label, body, gtype=0):
    lab = label.encode() if isinstance(label, str) else struct.pack('<I', label)
    return b'GRUP' + struct.pack('<I', 24 + len(body)) + lab + struct.pack('<IHHI', gtype, 0, 0, 0) + body

def ctda_global_eq(glob, value):
    # == , comparison value, GetGlobalValue (74), param1 = global, run on subject
    return sub('CTDA', struct.pack('<B3xfHHIIIIi', 0, value, 74, 0, glob, 0, 0, 0, -1))

# Papyrus VMAD (version 5, object format 2)
def p_obj(name, fid, alias=-1): return ws(name) + bytes([1, 1]) + struct.pack('<hhI', 0, alias, fid)
def p_int(name, v): return ws(name) + bytes([3, 1]) + struct.pack('<i', v)
def p_objs(name, items): return ws(name) + bytes([11, 1]) + u32(len(items)) + b''.join(struct.pack('<hhI', 0, a, f) for f, a in items)
def script(name, props): return ws(name) + bytes([0]) + struct.pack('<H', len(props)) + b''.join(props)
def vmad(scripts, quest_aliases=None):
    out = struct.pack('<hhH', 5, 2, len(scripts)) + b''.join(scripts)
    if quest_aliases is not None:              # QUST: empty fragment block, then alias scripts
        out += bytes([2]) + struct.pack('<H', 0) + ws('') + struct.pack('<H', len(quest_aliases))
        for alias_id, scr in quest_aliases:
            out += struct.pack('<hhI', 0, alias_id, FID['SPP_SixPathsQuest']) + struct.pack('<hhH', 5, 2, len(scr)) + b''.join(scr)
    return sub('VMAD', out)

# --- read vanilla templates -------------------------------------------------------
def subs_of(d):
    i = 0
    while i < len(d):
        t = d[i:i+4].decode('latin1'); n = struct.unpack_from('<H', d, i+4)[0]
        yield t, d[i+6:i+6+n]; i += 6 + n

def vanilla(edids):
    buf = open(SKYRIM, 'rb').read(); out = {}
    def walk(o, e):
        while o < e:
            t = buf[o:o+4].decode('latin1'); n = struct.unpack_from('<I', buf, o+4)[0]
            if t == 'GRUP': walk(o+24, o+n); o += n; continue
            fl, fid = struct.unpack_from('<II', buf, o+8); b = buf[o+24:o+24+n]; o += 24 + n
            if t not in ('CSTY', 'MGEF', 'CLAS', 'PACK', 'NPC_', 'CELL', 'SPEL', 'ARMO', 'ARMA'): continue
            if t == 'CELL' and fid != QASMOKE: continue
            if fl & 0x40000: b = zlib.decompress(b[4:])
            s = list(subs_of(b)); ed = dict(s).get('EDID', b'').rstrip(b'\0').decode('latin1')
            if ed in edids: out[ed] = s
    walk(24 + struct.unpack_from('<I', buf, 4)[0], len(buf))
    missing = set(edids) - set(out)
    assert not missing, missing
    return out

V = vanilla({'csHumanMagic', 'CWAbRegenEffect', 'EncClassDremoraMelee', 'BladesFollowPlayerPackage',
             'DefaultSandboxCurrentLocation1024', 'HirelingBelrand', 'QASmoke',
             'SummonFlameAtronach', 'ConjureFlameAtronach', 'HirelingMarcurio',
             'HirelingStenvar', 'flameCloak', 'HirelingVorstag', 'Sayma', 'HousecarlWhiterun',
             'SkinNaked', 'NakedTorso', 'NakedHands', 'NakedFeet'})

records = {}

# ================= steps 1-2: shared records =================

records['GLOB'] = [rec('GLOB', FID['SPP_PathsState'], [
    sub('EDID', z('SPP_PathsState')), sub('FNAM', b's'), sub('FLTV', f32(0.0))])]

# CLAS. Skill order: 1H 2H Archery Block Smithing Heavy Light Pickpocket Lockpicking Sneak
#                    Alchemy Speech Alteration Conjuration Destruction Illusion Restoration Enchanting
tmpl = dict(V['EncClassDremoraMelee'])['DATA']
weights = [0] * 18
weights[12], weights[13], weights[14], weights[16] = 1, 2, 3, 1
clas_data = tmpl[:6] + bytes(weights) + f32(0.1) + u32(0) + bytes([2, 3, 1, 0])
records['CLAS'] = [rec('CLAS', FID['SPP_ClassJinchuriki'], [
    sub('EDID', z('SPP_ClassJinchuriki')), sub('FULL', z('Jinchuriki')), sub('DESC', z('')), sub('DATA', clas_data)])]

records['FACT'] = [rec('FACT', FID['SPP_SixPathsFaction'], [
    sub('EDID', z('SPP_SixPathsFaction')), sub('FULL', z('Six Paths of Pain')),
    sub('XNAM', struct.pack('<IiI', PLAYER_FACTION, 0, 2)),
    sub('XNAM', struct.pack('<IiI', CURRENT_FOLLOWER_FACTION, 0, 2)),
    sub('DATA', u32(0x1)), sub('CRVA', bytes.fromhex('0101000000000000000000000000000000000000'))])]

# MGEF DATA template: CWAbRegenEffect (Value Modifier, AV 134, Constant, Self)
MDATA = dict(V['CWAbRegenEffect'])['DATA']
assert struct.unpack_from('<I', MDATA, 0x40)[0] == 0 and struct.unpack_from('<i', MDATA, 0x44)[0] == 134
assert struct.unpack_from('<II', MDATA, 0x50) == (0, 0)

def mgef(edid, name, flags, archetype, av, cast_type, delivery, extra=()):
    d = bytearray(MDATA)
    struct.pack_into('<I', d, 0x00, flags)
    struct.pack_into('<Ii', d, 0x40, archetype, av)
    struct.pack_into('<II', d, 0x50, cast_type, delivery)
    return rec('MGEF', FID[edid], [sub('EDID', z(edid))] + list(extra) + [
        sub('FULL', z(name)), sub('DATA', bytes(d)), sub('SNDD', b''), sub('DNAM', z(''))])

def cmd_vmad(command):
    return vmad([script('SPP_ObitoCommandEffect', [
        p_obj('Master', FID['SPP_SixPathsQuest']), p_int('Command', command)])])

NO_DUR, NO_MAG, NO_AREA, RECOVER, HIDE_UI = 0x200, 0x400, 0x800, 0x2, 0x8000
records['MGEF'] = [
    mgef('SPP_EdoRegenEffect', 'Edo Tensei Regeneration', RECOVER | HIDE_UI, 0, 134, 0, 0),
    # Script archetype, Fire and Forget, Self
    mgef('SPP_CmdEffectCommand', 'Six Paths: Command', NO_DUR | NO_MAG | NO_AREA, 1, -1, 1, 0, [cmd_vmad(0)]),
    mgef('SPP_CmdEffectSummon', 'Six Paths: Summon', NO_DUR | NO_MAG | NO_AREA, 1, -1, 1, 0, [cmd_vmad(1)]),
    mgef('SPP_CmdEffectRelease', 'Six Paths: Release', NO_DUR | NO_MAG | NO_AREA, 1, -1, 1, 0, [cmd_vmad(2)]),
]

# Summon effect: clone of vanilla SummonFlameAtronach (Conjuration, Summon Creature, target location,
# atronach casting/summon art and sounds), conjuring a path's summon NPC. Its perk condition is dropped.
def summon_mgef(edid, name, desc, npc_edid):
    out = []
    for t, d in V['SummonFlameAtronach']:
        if t == 'EDID': d = z(edid)
        elif t == 'FULL': d = z(name)
        elif t == 'DNAM': d = z(desc)
        elif t == 'CTDA': continue
        elif t == 'DATA':
            d = bytearray(d)
            assert struct.unpack_from('<I', d, 0x40)[0] == 18 and struct.unpack_from('<i', d, 0x0C)[0] == 19  # Summon, Conjuration
            struct.pack_into('<I', d, 0x08, FID[npc_edid])
            d = bytes(d)
        out.append(sub(t, d))
    return rec('MGEF', FID[edid], out)
records['MGEF'] += [
    summon_mgef('SPP_SummonYaguraEffect', 'Edo Tensei: Yagura',
                'Reincarnates Yagura, the Three-Tails jinchuriki, to fight for you for <dur> seconds.', 'SPP_YaguraSummon'),
    summon_mgef('SPP_SummonUtakataEffect', 'Edo Tensei: Utakata',
                'Reincarnates Utakata, the Six-Tails jinchuriki, to fight for you for <dur> seconds.', 'SPP_UtakataSummon'),
    summon_mgef('SPP_SummonRoushiEffect', 'Edo Tensei: Roushi',
                'Reincarnates Roushi, the Four-Tails jinchuriki, to fight for you for <dur> seconds.', 'SPP_RoushiSummon'),
    summon_mgef('SPP_SummonHanEffect', 'Edo Tensei: Han',
                'Reincarnates Han, the Five-Tails jinchuriki, to fight for you for <dur> seconds.', 'SPP_HanSummon'),
    summon_mgef('SPP_SummonFuuEffect', 'Edo Tensei: Fuu',
                'Reincarnates Fuu, the Seven-Tails jinchuriki, to fight for you for <dur> seconds.', 'SPP_FuuSummon'),
    summon_mgef('SPP_SummonYugitoEffect', 'Edo Tensei: Yugito',
                'Reincarnates Yugito Nii, the Two-Tails jinchuriki, to fight for you for <dur> seconds.', 'SPP_YugitoSummon'),
]

# Visual-only effect: Script archetype with no script, Fire and Forget, Aimed. Its hit shader
# (naruto overhaul's bubble shader) plays on whoever the jutsu hits, for the effect's duration.
fx = bytearray(MDATA)
struct.pack_into('<I', fx, 0x00, NO_MAG | NO_AREA | HIDE_UI)
struct.pack_into('<I', fx, 0x20, BUBBLES_EFSH)                 # hit shader
struct.pack_into('<Ii', fx, 0x40, 1, -1)                       # Script archetype, no actor value
struct.pack_into('<II', fx, 0x50, 1, 2)                        # Fire and Forget, Aimed
records['MGEF'].append(rec('MGEF', FID['SPP_BubbleFXEffect'], [
    sub('EDID', z('SPP_BubbleFXEffect')), sub('FULL', z('Bubbles')), sub('DATA', bytes(fx)),
    sub('SNDD', b''), sub('DNAM', z(''))]))

def eff(mgef_fid, mag):
    return sub('EFID', u32(mgef_fid)) + sub('EFIT', f32(mag) + u32(0, 0))

def spit(spell_type, cast_type, delivery):
    return sub('SPIT', u32(0, 1, spell_type) + f32(0.0) + u32(cast_type, delivery) + f32(0.0, 0.0) + u32(0))

def power(edid, name, desc, effect):
    return rec('SPEL', FID[edid], [
        sub('EDID', z(edid)), sub('OBND', bytes(12)), sub('FULL', z(name)), sub('ETYP', u32(VOICE_SLOT)),
        sub('DESC', z(desc)), spit(3, 1, 0), eff(FID[effect], 0.0)])   # 3 = Lesser Power

records['SPEL'] = [
    rec('SPEL', FID['SPP_EdoTenseiAbility'], [
        sub('EDID', z('SPP_EdoTenseiAbility')), sub('OBND', bytes(12)), sub('FULL', z('Edo Tensei')),
        sub('ETYP', u32(EITHER_HAND)), sub('DESC', z('')), spit(4, 0, 0),   # 4 = Ability, Constant, Self
        eff(FID['SPP_EdoRegenEffect'], 2.0), eff(AB_RESIST_POISON, 100.0), eff(AB_RESIST_DISEASE, 100.0)]),
    power('SPP_PowerCommand', 'Six Paths: Command',
          'Bind the Six Paths to your will. Once bound, toggles them between following and waiting.', 'SPP_CmdEffectCommand'),
    power('SPP_PowerSummon', 'Six Paths: Summon', 'Call the Six Paths to your side.', 'SPP_CmdEffectSummon'),
    power('SPP_PowerRelease', 'Six Paths: Release', 'Send the Six Paths back to their resting place.', 'SPP_CmdEffectRelease'),
]

# ---- Yagura's Three-Tails kit: renamed clones of EDM water spells (script-free, NPC-castable) ----
def read_spells(path, edids):
    buf = open(path, 'rb').read(); hsz = struct.unpack_from('<I', buf, 4)[0]
    masters = [d.rstrip(b'\0').decode() for t, d in subs_of(buf[24:24+hsz]) if t == 'MAST']
    out = {}
    def walk(o, e):
        while o < e:
            t = buf[o:o+4].decode('latin1'); n = struct.unpack_from('<I', buf, o+4)[0]
            if t == 'GRUP': walk(o+24, o+n); o += n; continue
            fl = struct.unpack_from('<I', buf, o+8)[0]; b = buf[o+24:o+24+n]; o += 24 + n
            if t != 'SPEL': continue
            if fl & 0x40000: b = zlib.decompress(b[4:])
            s = list(subs_of(b)); ed = dict(s).get('EDID', b'').rstrip(b'\0').decode('latin1')
            if ed in edids: out[ed] = s
    walk(24 + hsz, len(buf))
    assert set(out) == set(edids), set(edids) - set(out)
    # their load-order index -> ours (their own records sit at index len(masters))
    remap = {i: MASTERS.index(m) for i, m in enumerate(masters)}
    remap[len(masters)] = MASTERS.index(path.replace('\\', '/').split('/')[-1])
    return out, lambda fid: (remap[fid >> 24] << 24) | (fid & 0xFFFFFF)

EDM_SPELLS, edm_fid = read_spells(EDM, {'Waterball', 'Geyser', 'Torrent', 'RainCloak', 'TidalWave', 'Rapids',
                                        'RockBlast', 'Boulder', 'Stalagmite',
                                        'Zephyr', 'Tornado', 'Tempest', 'WhirlwindCloak'})
NARUTO_SPELLS, naruto_fid = read_spells(NARUTO, {'SKInsectSpray', 'A0FireBallJutsuSpell2Rank3',
                                                 'A0DragonFlameJutsuSpell2Rank3', 'A0PhoenixFlowerJutsuSpell2Rank3',
                                                 'A0GFAspell'})

SAFE_CONDITION_FUNCS = {77}   # GetRandomPercent - EDM's stagger-chance rolls; no form parameters

def jutsu(edid, name, src, desc='', cost=None, extra_effects=b'', drop_conditions=False, vanilla=False, naruto=False):
    out = []
    source, fid_of = ((V[src], (lambda f: f)) if vanilla else
                      (NARUTO_SPELLS[src], naruto_fid) if naruto else (EDM_SPELLS[src], edm_fid))
    for t, d in source:
        if t == 'EDID': d = z(edid)
        elif t == 'FULL': d = z(name)
        elif t == 'DESC': d = z(desc)
        elif t in ('MDOB', 'ETYP', 'EFID'): d = u32(fid_of(struct.unpack('<I', d)[0]))
        elif t == 'CTDA':
            if drop_conditions: continue
            if struct.unpack_from('<H', d, 8)[0] not in SAFE_CONDITION_FUNCS:
                raise ValueError(f'{src} has conditions; remap their params before cloning')
        elif t == 'SPIT':
            d = bytearray(d)
            perk = struct.unpack_from('<I', d, 32)[0]
            if perk: struct.pack_into('<I', d, 32, fid_of(perk))
            if cost is not None: struct.pack_into('<II', d, 0, cost, struct.unpack_from('<I', d, 4)[0] | 0x1)
            d = bytes(d)
        out.append(sub(t, d))
    return rec('SPEL', FID[edid], out + ([extra_effects] if extra_effects else []))

records['SPEL'] += [
    jutsu('SPP_JutsuWaterBullet', 'Water Release: Water Bullet', 'Waterball'),
    jutsu('SPP_JutsuWaterShockwave', 'Water Release: Bursting Water Shockwave', 'Geyser'),
    jutsu('SPP_JutsuWaterSharkBullet', 'Water Release: Water Shark Bullet', 'Torrent'),
    # Coral Palm: Water Bullet that also encases the target in coral (3 s paralysis)
    jutsu('SPP_JutsuCoralPalm', 'Three-Tails: Coral Palm', 'Waterball', cost=90,
          extra_effects=sub('EFID', u32(PARALYSIS_FF_AIMED)) + sub('EFIT', f32(0.0) + u32(0, 3))),
    # EDM's Rain Cloak is gated on (swimming OR GetIsID Player); Yagura's copy is unconditional
    jutsu('SPP_JutsuThreeTailsCloak', 'Three-Tails: Chakra Cloak', 'RainCloak', drop_conditions=True),
    # Tidal Wave costs 1,411 in EDM - out of an NPC's reach. 400 lets him open with it once per fight.
    jutsu('SPP_JutsuGreatTsunami', 'Tailed Beast: Great Tsunami', 'TidalWave', cost=400),
]

# Conjuration spell: clone of vanilla ConjureFlameAtronach (keeps its menu object, Apprentice
# half-cost perk, 0.5 s charge, target location), one effect, 600 s, manual cost 50.
SUMMON_SECONDS = 600
def summon_spell(edid, name, effect_edid):
    out, effect_done = [], False
    for t, d in V['ConjureFlameAtronach']:
        if t == 'EDID': d = z(edid)
        elif t == 'FULL': d = z(name)
        elif t == 'DESC': d = z('')
        elif t == 'SPIT':
            d = bytearray(d)
            struct.pack_into('<II', d, 0, 50, 0x1)        # cost 50, manual cost
            d = bytes(d)
        elif t in ('EFID', 'EFIT'):
            if not effect_done:
                out.append(sub('EFID', u32(FID[effect_edid])) +
                           sub('EFIT', f32(0.0) + u32(0, SUMMON_SECONDS)))   # magnitude, area, duration
                effect_done = True
            continue
        out.append(sub(t, d))
    return rec('SPEL', FID[edid], out)
records['SPEL'] += [
    summon_spell('SPP_SummonYagura', 'Edo Tensei: Yagura', 'SPP_SummonYaguraEffect'),
    summon_spell('SPP_SummonUtakata', 'Edo Tensei: Utakata', 'SPP_SummonUtakataEffect'),
    summon_spell('SPP_SummonRoushi', 'Edo Tensei: Roushi', 'SPP_SummonRoushiEffect'),
    summon_spell('SPP_SummonHan', 'Edo Tensei: Han', 'SPP_SummonHanEffect'),
    summon_spell('SPP_SummonFuu', 'Edo Tensei: Fuu', 'SPP_SummonFuuEffect'),
    summon_spell('SPP_SummonYugito', 'Edo Tensei: Yugito', 'SPP_SummonYugitoEffect'),
]
SUMMON_SPELLS = ['SPP_SummonYagura', 'SPP_SummonUtakata', 'SPP_SummonRoushi', 'SPP_SummonHan', 'SPP_SummonFuu',
                 'SPP_SummonYugito']

# ---- Utakata's Six-Tails kit: bubble + alkali jutsu from EDM water, with the bubble shader ----
def bubble_fx(seconds, area=0):
    return sub('EFID', u32(FID['SPP_BubbleFXEffect'])) + sub('EFIT', f32(0.0) + u32(area, seconds))

records['SPEL'] += [
    jutsu('SPP_JutsuExplodingBubbles', 'Bubble Release: Exploding Bubbles', 'Waterball',
          extra_effects=bubble_fx(3)),
    jutsu('SPP_JutsuBubbleBurst', 'Bubble Release: Bubble Burst', 'Geyser',
          extra_effects=bubble_fx(4, area=15)),           # Geyser's 15-foot radius
    # Bubble Prison: traps the target in a bubble (3 s paralysis)
    jutsu('SPP_JutsuBubblePrison', 'Bubble Release: Bubble Prison', 'Waterball', cost=90,
          extra_effects=sub('EFID', u32(PARALYSIS_FF_AIMED)) + sub('EFIT', f32(0.0) + u32(0, 3)) + bubble_fx(3)),
    # Concentration spray; the bubble shader is Fire-and-Forget so it can't ride along here
    jutsu('SPP_JutsuAlkaliSpray', 'Six-Tails: Corrosive Alkali', 'Rapids', drop_conditions=True),
    jutsu('SPP_JutsuSixTailsCloak', 'Six-Tails: Chakra Cloak', 'RainCloak', drop_conditions=True),
]

# ---- Roushi's Four-Tails kit: Lava Release = EDM earth spells that also burn ----
def first_area(src):
    efit = next(d for t, d in EDM_SPELLS[src] if t == 'EFIT')
    return struct.unpack_from('<I', efit, 4)[0]

def burn(magnitude, area=0):
    # vanilla fire damage (Firebolt's effect) rides along on the rock; its hit shader sets targets alight
    return sub('EFID', u32(FIRE_DAMAGE_FF_AIMED)) + sub('EFIT', f32(magnitude) + u32(area, 0))

records['SPEL'] += [
    jutsu('SPP_JutsuLavaGlobs', 'Lava Release: Lava Globs', 'RockBlast', extra_effects=burn(15)),
    jutsu('SPP_JutsuMoltenBoulder', 'Lava Release: Molten Boulder', 'Boulder', extra_effects=burn(30)),
    jutsu('SPP_JutsuMagmaSpikes', 'Lava Release: Magma Spikes', 'Stalagmite',
          extra_effects=burn(20, area=first_area('Stalagmite'))),
    # vanilla Flame Cloak has the same caster gate as EDM's cloaks; dropped as for Yagura/Utakata (worked in game)
    jutsu('SPP_JutsuLavaCloak', 'Four-Tails: Lava Chakra Cloak', 'flameCloak', vanilla=True, drop_conditions=True),
]

# ---- Han's Five-Tails kit: Boil Release = EDM water that also scalds; he punches with Chakra Fist ----
records['SPEL'] += [
    jutsu('SPP_JutsuScaldingSteam', 'Boil Release: Scalding Steam', 'Rapids', drop_conditions=True,
          extra_effects=sub('EFID', u32(FIRE_DAMAGE_CONC_AIMED)) + sub('EFIT', f32(8.0) + u32(0, 1))),  # as Flames
    jutsu('SPP_JutsuSteamExplosion', 'Boil Release: Steam Explosion', 'Geyser',
          extra_effects=burn(25, area=first_area('Geyser'))),
    jutsu('SPP_JutsuSteamArmor', 'Five-Tails: Steam Armor', 'RainCloak', drop_conditions=True),
]

# ---- Fuu's Seven-Tails kit: insects (naruto overhaul) + Chomei's wings (EDM wind) ----
records['SPEL'] += [
    jutsu('SPP_JutsuInsectSwarm', 'Hidden Jutsu: Insect Swarm', 'SKInsectSpray', naruto=True),
    # scale powder blinds: a gust that leaves the target stunned for 2 s
    jutsu('SPP_JutsuScalePowder', 'Seven-Tails: Scale Powder', 'Zephyr', cost=90,
          extra_effects=sub('EFID', u32(PARALYSIS_FF_AIMED)) + sub('EFIT', f32(0.0) + u32(0, 2))),
    jutsu('SPP_JutsuWingTornado', 'Seven-Tails: Wing Tornado', 'Tornado'),
    jutsu('SPP_JutsuWingGale', 'Seven-Tails: Wing Gale', 'Tempest'),
    jutsu('SPP_JutsuSevenTailsCloak', 'Seven-Tails: Chakra Cloak', 'WhirlwindCloak', drop_conditions=True),
]

# ---- Yugito's Two-Tails kit: naruto overhaul Katon jutsu, renamed for Matatabi's flames ----
records['SPEL'] += [
    jutsu('SPP_JutsuWispFireball', "Two-Tails: Will-o'-Wisp Fireball", 'A0FireBallJutsuSpell2Rank3', naruto=True),
    jutsu('SPP_JutsuCatFlameBreath', 'Two-Tails: Cat Flame Breath', 'A0DragonFlameJutsuSpell2Rank3', naruto=True),
    jutsu('SPP_JutsuPhoenixSageFire', 'Fire Release: Phoenix Sage Fire', 'A0PhoenixFlowerJutsuSpell2Rank3', naruto=True),
    # Gouka Mekkyaku hits for 250 - it would dominate like Great Missile did. Costly finisher instead.
    jutsu('SPP_JutsuFlameInferno', 'Two-Tails: Blue Flame Inferno', 'A0GFAspell', naruto=True, cost=450),
    jutsu('SPP_JutsuTwoTailsCloak', 'Two-Tails: Blue Flame Cloak', 'flameCloak', vanilla=True, drop_conditions=True),
]

def csty(edid, csgd):
    out = []
    for t, d in V['csHumanMagic']:
        if t == 'EDID': d = z(edid)
        elif t == 'CSGD': d = f32(*csgd)
        elif t == 'DATA': d = u32(0x1 | 0x4)          # Dueling + Allow Dual Wielding
        out.append(sub(t, d))
    return rec('CSTY', FID[edid], out)
# CSGD: offensive, defensive, group offensive, melee, magic, ranged, shout, unarmed, staff, avoid threat
records['CSTY'] = [
    csty('SPP_CSJinchuriki',        [0.85, 0.30, 0.80, 0.30, 6.00, 0.0, 0.0, 0.30, 1.0, 0.20]),
    # tuned after testing: at magic 3.0 Han stayed back casting; now melee/unarmed dominate
    csty('SPP_CSJinchurikiBrawler', [1.00, 0.10, 0.90, 4.00, 0.50, 0.0, 0.0, 8.00, 0.0, 0.10]),
]

records['OTFT'] = [
    rec('OTFT', FID['SPP_AkatsukiOutfit'], [sub('EDID', z('SPP_AkatsukiOutfit')), sub('INAM', u32(AKA_ROBE, AKA_BOOTS, RING_PAIN))]),
    # Han (EDID kept from the cloak phase): crimson samurai Do-maru, suneate and black kote under his red kasa and
    # mask. (2026-10-14: Akatsuki robe -> recoloured Senju outfit -> this; the Senju clones 0x861-0x864 are unused.)
    rec('OTFT', FID['SPP_AkatsukiOutfitHan'], [sub('EDID', z('SPP_AkatsukiOutfitHan')), sub('INAM', u32(
        FID['SPP_HanDomaru'], FID['SPP_HanSuneate'], FID['SPP_HanKote'], FID['SPP_HanHat'], FID['SPP_HanMask']))]),
    # Utakata: light-blue robe, orange sash + Zori sandals (2026-10-14: replaced the shared Akatsuki outfit)
    rec('OTFT', FID['SPP_UtakataOutfit'], [sub('EDID', z('SPP_UtakataOutfit')), sub('INAM', u32(
        FID['SPP_UtakataRobe'], FID['SPP_UtakataSandals']))]),
    # Roushi: magenta/brown Senju outfit + war sandals (2026-10-14: replaced the shared Akatsuki outfit)
    rec('OTFT', FID['SPP_RoushiOutfit'], [sub('EDID', z('SPP_RoushiOutfit')), sub('INAM', u32(
        FID['SPP_RoushiArmor'], FID['SPP_RoushiBoots']))]),
    # Yugito: Boruto-era Sakura outfit recoloured to her look (navy top, red sash, off-white sleeves like
    # her bandaged forearms, purple-navy shorts) + Sakura's ninja sandals and leg pouch.
    # (2026-10-14: replaced Hinata's hoodie/trousers/sandals, which she wore before.)
    rec('OTFT', FID['SPP_YugitoOutfit'], [sub('EDID', z('SPP_YugitoOutfit')), sub('INAM', u32(
        FID['SPP_YugitoSakuraTop'], FID['SPP_YugitoSakuraSleeves'], FID['SPP_YugitoSakuraShorts'],
        SAKURA_SHOES, SAKURA_LEG_POUCH, FID['SPP_YugitoHeadband']))]),
]

# ================= step 3: the paths =================
# Each path is cloned from a vanilla hireling (for a ready-made face), stripped of hireling data.
def path_npc(edid, template, name, head_parts, hair_color, height, weight, spells,
             outfit='SPP_AkatsukiOutfit', combat_style='SPP_CSJinchuriki', inventory=(), voice=None, skin_rgb=None,
             skin=None, race=None):
    female = struct.unpack_from('<I', dict(V[template])['ACBS'], 0)[0] & 0x1
    acbs = struct.pack('<IhhHHHHHHHH',
                       female | 0x2 | 0x10 | 0x20 | 0x80,   # (Female), Essential, Auto-calc stats, Unique, PC level mult
                       200, 0,                     # magicka offset, stamina offset
                       1000, 20, 60,               # level mult 1.0, calc min, calc max
                       100, 35, 0,                 # speed mult, disposition, template flags
                       100, 0)                     # health offset, bleedout override
    replace = {
        'EDID': [sub('EDID', z(edid))],
        'ACBS': [sub('ACBS', acbs)],
        'SNAM': [sub('SNAM', u32(FID['SPP_SixPathsFaction']) + bytes(4))],
        'SPCT': [sub('SPCT', u32(1 + len(spells)))] +
                [sub('SPLO', u32(s)) for s in [FID['SPP_EdoTenseiAbility']] + spells],
        'PKID': [sub('PKID', u32(SANDBOX_EDITOR_LOC))],
        'KSIZ': [sub('KSIZ', u32(1)), sub('KWDA', u32(ACTOR_TYPE_NPC))],
        'CNAM': [sub('CNAM', u32(FID['SPP_ClassJinchuriki']))],
        'FULL': [sub('FULL', z(name))],
        'PNAM': [sub('PNAM', u32(p)) for p in head_parts],
        'HCLF': [sub('HCLF', u32(hair_color))],
        'ZNAM': [sub('ZNAM', u32(FID[combat_style]))],
        'NAM6': [sub('NAM6', f32(height))],
        'NAM7': [sub('NAM7', f32(weight))],
        'DOFT': [sub('DOFT', u32(FID[outfit]))],
    }
    if voice: replace['VTCK'] = [sub('VTCK', u32(voice))]
    if skin_rgb: replace['QNAM'] = [sub('QNAM', f32(*(c / 255.0 for c in skin_rgb)))]
    drop = {'SPLO', 'PRKZ', 'PRKR', 'COCT', 'CNTO', 'KWDA', 'CRIF', 'SOFT', 'VMAD', 'SHRT'}
    if race:   # another race than the template's: its face tint layers and skin texture set are race-specific
        replace['RNAM'] = [sub('RNAM', u32(race))]
        drop |= {'TINI', 'TINC', 'TINV', 'TIAS', 'FTST'}
    insert_after = {'PKID': 'KSIZ', 'HCLF': 'ZNAM'}   # fields some templates (e.g. Sayma) don't have
    if inventory:   # (form, count) pairs; replaces the template's own items
        replace['COCT'] = [sub('COCT', u32(len(inventory)))] + [sub('CNTO', struct.pack('<Ii', f, n)) for f, n in inventory]
    has = {t for t, d in V[template]}
    out, done = [], set()
    for t, d in V[template]:
        if skin and 'WNAM' not in done and t in ('PRKZ', 'COCT', 'AIDT'):
            out.append(sub('WNAM', u32(FID[skin]))); done.add('WNAM')
        if t == 'AIDT' and inventory and 'COCT' not in has:      # items go right before AI data
            out += replace['COCT']; done.add('COCT')
        if t == 'RNAM' and 'SPCT' not in has:       # template knows no spells (e.g. Stenvar): spell list goes after race
            out += replace.get('RNAM', [sub(t, d)]); done.add('RNAM')
            out += replace['SPCT']; done.add('SPCT'); continue
        if t == 'AIDT':
            a = bytearray(d)
            a[0], a[1], a[3], a[5] = 1, 4, 0, 2      # Aggressive, Foolhardy, no crime, helps friends+allies
            out.append(sub('AIDT', bytes(a))); continue
        if t in replace:
            if t not in done: out += replace[t]; done.add(t)
        elif t in drop: continue
        else: out.append(sub(t, d))
        missing = insert_after.get(t)
        if missing and missing not in has and missing not in done:
            out += replace[missing]; done.add(missing)
    assert done - {'WNAM'} == set(replace) | ({'RNAM'} & done), set(replace) - done
    assert not skin or 'WNAM' in done
    return out

# Summoned copy: templated on the path NPC so it shares their face (and FaceGen export), spells,
# combat style and outfit. Not unique, not essential, Summonable, no packages of its own.
TPL_TRAITS, TPL_STATS, TPL_FACTIONS, TPL_SPELLS, TPL_AIDATA = 0x1, 0x2, 0x4, 0x8, 0x10
TPL_INVENTORY, TPL_SCRIPT, TPL_ATTACK, TPL_KEYWORDS = 0x100, 0x200, 0x800, 0x1000
def summon_npc(edid, base_edid, base_subs):
    out = []
    for s in base_subs:
        t = s[:4].decode()
        if t == 'EDID': s = sub('EDID', z(edid))
        elif t == 'ACBS':
            a = bytearray(s[6:])
            struct.pack_into('<I', a, 0, 0x10 | 0x80 | 0x4000)     # Auto-calc, PC level mult, Summonable
            struct.pack_into('<H', a, 18, TPL_TRAITS | TPL_STATS | TPL_FACTIONS | TPL_SPELLS | TPL_AIDATA |
                             TPL_INVENTORY | TPL_SCRIPT | TPL_ATTACK | TPL_KEYWORDS)
            s = sub('ACBS', bytes(a))
        elif t == 'PKID': continue
        out.append(s)
        if t == 'VTCK': out.append(sub('TPLT', u32(FID[base_edid])))
    return rec('NPC_', FID[edid], out)

# Yagura: from HirelingBelrand (Nord). Short (0.8) and slim - an adult with a youthful look.
yagura_subs = path_npc('SPP_Yagura', 'HirelingBelrand', 'Yagura',
                       (SCAR, EYES_SHARINGAN_R_RINNEGAN_L, NO_BEARD, BROWS, HAIR_OBITO_TEEN),
                       HAIR_GREY, 0.80, 0.0, YAGURA_SPELLS)
# Utakata: from HirelingMarcurio (Imperial). Long dark hair, slim.
utakata_subs = path_npc('SPP_Utakata', 'HirelingMarcurio', 'Utakata',
                        (BROWS_03, NO_BEARD, HAIR_ITACHI, NO_SCAR, EYES_SHARINGAN_R_RINNEGAN_L),
                        HAIR_BLUE_BLACK, 1.0, 20.0, UTAKATA_SPELLS, outfit='SPP_UtakataOutfit',
                        skin_rgb=(236, 226, 214), race=NORD_RACE)   # pale Nord (Marcurio is a tan Imperial)

# Roushi: from HirelingStenvar (Nord, full beard, brute voice). Auburn hair, stocky.
roushi_subs = path_npc('SPP_Roushi', 'HirelingStenvar', 'Roushi',
                       (NO_SCAR, HAIR_REDGUARD1, BEARD_41, BROWS_05, EYES_SHARINGAN_R_RINNEGAN_L),
                       HAIR_AUBURN, 0.95, 100.0, ROUSHI_SPELLS, outfit='SPP_RoushiOutfit')

# Han: from HirelingVorstag (big Nord, no beard). Very tall and heavy; brawler with Chakra Fist,
# Akatsuki hat in place of his straw kasa.
han_subs = path_npc('SPP_Han', 'HirelingVorstag', 'Han',
                    (EYES_SHARINGAN_R_RINNEGAN_L, NO_BEARD, NO_SCAR, BROWS_08, HAIR_NORD01),
                    HAIR_DARK_BROWN, 1.15, 100.0, HAN_SPELLS,
                    outfit='SPP_AkatsukiOutfitHan', combat_style='SPP_CSJinchurikiBrawler',
                    inventory=[(CHAKRA_FIST_NPC, 1)])

# Fuu: from Sayma (Redguard woman, for Fuu's darker skin). Adult build; short mint-green bob.
fuu_subs = path_npc('SPP_Fuu', 'Sayma', 'Fuu',
                    (BROWS_F02, NO_GASH_F, EYES_F_SHARINGAN_R_RINNEGAN_L, HAIR_F_IMPERIAL1),
                    FID['SPP_HairColorMint'], 1.0, 40.0, FUU_SPELLS, voice=FEMALE_YOUNG_EAGER)

# Yugito: from HousecarlWhiterun (Lydia: Nord woman, even-toned voice). Her face is the user's
# RaceMenu sculpt (preset "Yugito Nii"), exported and installed as FaceGen 00000847 by
# tools/facegen_from_export.py - so head parts, weight, hair tint and skin tone here must match that export.
yugito_subs = path_npc('SPP_Yugito', 'HousecarlWhiterun', 'Yugito Nii',
                       (HPH_FEMALE_HEAD_NORD, MOUTH_F_DEFAULT, NO_GASH_F, HAIR_KS_TRAVELER,
                        EYES_F_SHARINGAN_R_RINNEGAN_L, BROWS_F07),
                       FID['SPP_HairColorYugito'], 1.0, 60.0, YUGITO_SPELLS, skin_rgb=(221, 221, 221),
                       outfit='SPP_YugitoOutfit', skin='SPP_YugitoSkin')

records['NPC_'] = [rec('NPC_', FID['SPP_Yagura'], yagura_subs),
                   summon_npc('SPP_YaguraSummon', 'SPP_Yagura', yagura_subs),
                   rec('NPC_', FID['SPP_Utakata'], utakata_subs),
                   summon_npc('SPP_UtakataSummon', 'SPP_Utakata', utakata_subs),
                   rec('NPC_', FID['SPP_Roushi'], roushi_subs),
                   summon_npc('SPP_RoushiSummon', 'SPP_Roushi', roushi_subs),
                   rec('NPC_', FID['SPP_Han'], han_subs),
                   summon_npc('SPP_HanSummon', 'SPP_Han', han_subs),
                   rec('NPC_', FID['SPP_Fuu'], fuu_subs),
                   summon_npc('SPP_FuuSummon', 'SPP_Fuu', fuu_subs),
                   rec('NPC_', FID['SPP_Yugito'], yugito_subs),
                   summon_npc('SPP_YugitoSummon', 'SPP_Yugito', yugito_subs)]

# Fuu's hair colour: vanilla has no green. CNAM = RGB + pad, FNAM 1 = playable.
records['CLFM'] = [rec('CLFM', FID['SPP_HairColorMint'], [
    sub('EDID', z('SPP_HairColorMint')), sub('FULL', z('Mint Green')),
    sub('CNAM', bytes([120, 220, 190, 0])), sub('FNAM', u32(1))]),
    # Yugito's hair tint, exactly as saved in her preset (the KS texture is already blonde; this darkens it)
    rec('CLFM', FID['SPP_HairColorYugito'], [
    sub('EDID', z('SPP_HairColorYugito')), sub('FULL', z('Yugito Blonde')),
    sub('CNAM', bytes([81, 77, 57, 0])), sub('FNAM', u32(1))])]

# Yugito's skin: clone of vanilla SkinNaked whose human torso/hands/feet addons point at her own copy of
# the Twins body (meshes/actors/character/SPP_Yugito, textures repointed to the standard female skin).
def body_addon(edid, template, female_mesh):
    out = []
    for t, d in V[template]:
        if t == 'EDID': d = z(edid)
        elif t == 'MOD3': d = z(female_mesh)
        elif t == 'MO3T': continue                     # texture hashes of the vanilla mesh
        out.append(sub(t, d))
    return rec('ARMA', FID[edid], out)

records['ARMA'] = [
    body_addon('SPP_YugitoTorsoAA', 'NakedTorso', 'Actors\\Character\\SPP_Yugito\\femalebody_1.nif'),
    body_addon('SPP_YugitoHandsAA', 'NakedHands', 'Actors\\Character\\SPP_Yugito\\femalehands_1.nif'),
    body_addon('SPP_YugitoFeetAA', 'NakedFeet', 'Actors\\Character\\SPP_Yugito\\femalefeet_1.nif'),
]
swap = {NAKED_TORSO: FID['SPP_YugitoTorsoAA'], NAKED_HANDS: FID['SPP_YugitoHandsAA'], NAKED_FEET: FID['SPP_YugitoFeetAA']}
skin_subs = []
for t, d in V['SkinNaked']:
    if t == 'EDID': d = z('SPP_YugitoSkin')
    elif t == 'MODL' and len(d) == 4: d = u32(swap.get(struct.unpack('<I', d)[0], struct.unpack('<I', d)[0]))
    elif t == 'DESC': d = z('')
    skin_subs.append(sub(t, d))
assert sum(s[:4] == b'MODL' and struct.unpack('<I', s[6:10])[0] in swap.values() for s in skin_subs) == 3
records['ARMO'] = [rec('ARMO', FID['SPP_YugitoSkin'], skin_subs)]

def read_records(path, types, edids):
    buf = open(path, 'rb').read(); hsz = struct.unpack_from('<I', buf, 4)[0]
    masters = [d.rstrip(b'\0').decode() for t, d in subs_of(buf[24:24+hsz]) if t == 'MAST']
    out = {}
    def walk(o, e):
        while o < e:
            t = buf[o:o+4].decode('latin1'); n = struct.unpack_from('<I', buf, o+4)[0]
            if t == 'GRUP': walk(o+24, o+n); o += n; continue
            fl = struct.unpack_from('<I', buf, o+8)[0]; b = buf[o+24:o+24+n]; o += 24 + n
            if t not in types: continue
            if fl & 0x40000: b = zlib.decompress(b[4:])
            sl = list(subs_of(b)); ed = dict(sl).get('EDID', b'').rstrip(b'\0').decode('latin1')
            if ed in edids: out[ed] = sl
    walk(24 + hsz, len(buf))
    assert set(out) == set(edids), set(edids) - set(out)
    # only masters that are actually referenced must be ours too (a KeyError names a missing one)
    remap = {i: MASTERS.index(m) for i, m in enumerate(masters) if m in MASTERS}
    if os.path.basename(path) in MASTERS:
        remap[len(masters)] = MASTERS.index(os.path.basename(path))
    return out, lambda fid: (remap[fid >> 24] << 24) | (fid & 0xFFFFFF)

SAK, sak_fid = read_records(SAKURA, {'ARMO', 'ARMA'}, {
    '00SakuraTop', '00SakuraTopAA', '00SakuraSleeves', '00SakuraSleeveAA', '00SakuraShorts', '00SakuraShortsAA',
    '00SakuraHeadbandBlack', '00SakuraHeadbandBlackAA'})

def clone_armor(edid, aa_edid, src, src_aa, name, female_mesh):
    # addon: same as Sakura's, but the female model is Yugito's retextured copy of the BodySlide build
    aa = []
    for t, d in SAK[src_aa]:
        if t == 'EDID': d = z(aa_edid)
        elif t == 'MOD3': d = z(female_mesh)
        elif t in ('MO3T', 'MO3S', 'MO2S'):
            assert t == 'MO3T', f'{src_aa} has alternate textures ({t}); remap them before cloning'
            continue
        elif t in ('RNAM', 'SNDD', 'NAM0', 'NAM1', 'NAM2', 'NAM3', 'ONAM') or (t == 'MODL' and len(d) == 4):
            d = u32(sak_fid(struct.unpack('<I', d)[0]))
        aa.append(sub(t, d))
    arm = []
    for t, d in SAK[src]:
        if t == 'EDID': d = z(edid)
        elif t == 'FULL': d = z(name)
        elif t == 'MODL' and len(d) == 4: d = u32(FID[aa_edid])
        elif t == 'KWDA': d = b''.join(u32(sak_fid(k)) for k in struct.unpack('<%dI' % (len(d) // 4), d))
        elif t in ('RNAM', 'EITM', 'ETYP', 'BIDS', 'BAMT', 'YNAM', 'ZNAM', 'TNAM'):
            d = u32(sak_fid(struct.unpack('<I', d)[0]))
        arm.append(sub(t, d))
    return rec('ARMO', FID[edid], arm), rec('ARMA', FID[aa_edid], aa)

for args in (('SPP_YugitoSakuraTop', 'SPP_YugitoSakuraTopAA', '00SakuraTop', '00SakuraTopAA',
              "Yugito's Shinobi Top", 'SPP\\Yugito\\Sakura\\Top_1.nif'),
             ('SPP_YugitoSakuraSleeves', 'SPP_YugitoSakuraSleevesAA', '00SakuraSleeves', '00SakuraSleeveAA',
              "Yugito's Arm Wraps", 'SPP\\Yugito\\Sakura\\Sleeve_1.nif'),
             ('SPP_YugitoSakuraShorts', 'SPP_YugitoSakuraShortsAA', '00SakuraShorts', '00SakuraShortsAA',
              "Yugito's Shorts", 'SPP\\Yugito\\Sakura\\Shorts_1.nif'),
             ('SPP_YugitoHeadband', 'SPP_YugitoHeadbandAA', '00SakuraHeadbandBlack', '00SakuraHeadbandBlackAA',
              "Yugito's Cloud Forehead Protector", 'SPP\\Yugito\\Sakura\\HeadbandCloud.nif')):
    a, aa = clone_armor(*args)
    records['ARMO'].append(a); records['ARMA'].append(aa)

# Han's mask: Wet and Cold's 'Face Cover' (_WetAshFaceCover2_Gray / AA) rebuilt from its human-race data with his
# white copy of the mesh. Only vanilla races/keywords are kept, so Wet and Cold is not a master.
DEFAULT_RACE = 0x00000019
MASK_RACES = (0x13741, 0x8883C, 0x97A3D, 0x13742, 0x8883D, 0x67CD8, 0xA82BA, 0x13743, 0x88840, 0x13744, 0x88844,
              0x10760A, 0x13746, 0x88794, 0x13748, 0x88846, 0xEBE18, 0xEB872, 0xB7998, 0x13749, 0x88884)
records['ARMA'].append(rec('ARMA', FID['SPP_HanMaskAA'], [
    sub('EDID', z('SPP_HanMaskAA')), sub('BOD2', u32(0x4000, 2)), sub('RNAM', u32(DEFAULT_RACE)),
    sub('DNAM', bytes.fromhex('0a0a00000000001800000000')),
    sub('MOD2', z('SPP\\Han\\facecover2_m.nif')), sub('MOD3', z('wetandcold\\ashes\\facecover2_f.nif'))]
    + [sub('MODL', u32(r)) for r in MASK_RACES]))
records['ARMO'].append(rec('ARMO', FID['SPP_HanMask'], [
    sub('EDID', z('SPP_HanMask')), sub('OBND', bytes(12)), sub('FULL', z("Han's Mask")),
    sub('MOD2', z('wetandcold\\ashes\\facecover2_world.nif')),
    sub('BOD2', u32(0x4000, 2)), sub('RNAM', u32(DEFAULT_RACE)),
    sub('KSIZ', u32(2)), sub('KWDA', u32(0x0008F95B, 0x0006BBE8)),          # VendorItemClothing, ArmorClothing
    sub('DESC', z('')), sub('MODL', u32(FID['SPP_HanMaskAA'])),
    sub('DATA', struct.pack('<If', 11, 0.5)), sub('DNAM', u32(0))]))

# Han: copies of UchihaClan's Senju outfit, Senju boots and Akatsuki hat whose male models are his recoloured
# meshes (meshes/SPP/Han, textures/SPP/Han: crimson plates/kasa/boots, olive cloth; tools/recolor_senju_outfit.py han).
UCHIHA = r'C:\games\ModOrganizer\Skyrim Special Edition\mods\The Uchiha Clan\UchihaClan.esp'
UCH, uch_fid = read_records(UCHIHA, {'ARMO', 'ARMA'}, {
    'aaaSenjuCuirassUnenchanted', 'aaaSenjuCuirassAA', 'aaaSenjuBootsUnenchanted', 'aaaSenjuBootsAA',
    'aaaAkatsukiHatUnenchanted', 'aaaAkatsukiHatAA', 'aaaTobiWarBootsUnenchanted', 'aaaTobiWarBootsAA'})

def clone_male(edid, aa_edid, src, src_aa, src_aa_fid, name, male_mesh, recs=UCH, fid_of=uch_fid):
    # src_aa_fid: the addon's FormID as the source plugin stores it (swapped for our addon in the ARMO).
    # Alternate-texture sets (MO*S) are dropped: their textures are baked into our mesh copies instead.
    aa = []
    for t, d in recs[src_aa]:
        if t == 'EDID': d = z(aa_edid)
        elif t == 'MOD2': d = z(male_mesh)
        elif t == 'MO2T': continue                     # texture hashes of the original model
        elif t in ('MO2S', 'MO3S', 'MO4S', 'MO5S'): continue
        elif t in ('RNAM', 'SNDD', 'ONAM') or (t == 'MODL' and len(d) == 4):
            d = u32(fid_of(struct.unpack('<I', d)[0]))
        aa.append(sub(t, d))
    arm, swapped = [], 0
    for t, d in recs[src]:
        if t == 'EDID': d = z(edid)
        elif t == 'FULL': d = z(name)
        elif t == 'MO2S': continue                      # ground model's alternate textures
        elif t == 'MODL' and len(d) == 4:
            f = struct.unpack('<I', d)[0]
            if f == src_aa_fid: d = u32(FID[aa_edid]); swapped += 1
            else: d = u32(fid_of(f))
        elif t == 'KWDA': d = b''.join(u32(fid_of(k)) for k in struct.unpack('<%dI' % (len(d) // 4), d))
        elif t in ('RNAM', 'EITM', 'ETYP', 'BIDS', 'BAMT', 'YNAM', 'ZNAM', 'TNAM'):
            d = u32(fid_of(struct.unpack('<I', d)[0]))
        arm.append(sub(t, d))
    assert swapped == 1, (src, swapped)
    return rec('ARMO', FID[edid], arm), rec('ARMA', FID[aa_edid], aa)

for args in (('SPP_HanArmor', 'SPP_HanArmorAA', 'aaaSenjuCuirassUnenchanted', 'aaaSenjuCuirassAA', 0x0528778E,
              "Han's Armour", 'SPP\\Han\\senjucuirassm_1.nif'),
             ('SPP_HanBoots', 'SPP_HanBootsAA', 'aaaSenjuBootsUnenchanted', 'aaaSenjuBootsAA', 0x0528778D,
              "Han's Boots", 'SPP\\Han\\senjubootsm_1.nif'),
             ('SPP_HanHat', 'SPP_HanHatAA', 'aaaAkatsukiHatUnenchanted', 'aaaAkatsukiHatAA', 0x051C653A,
              "Han's Kasa", 'SPP\\Han\\akatsukihat.nif'),
             # Roushi (meshes/SPP/Roushi, textures/SPP/Roushi; tools/recolor_senju_outfit.py roushi)
             ('SPP_RoushiArmor', 'SPP_RoushiArmorAA', 'aaaSenjuCuirassUnenchanted', 'aaaSenjuCuirassAA', 0x0528778E,
              "Roushi's Armour", 'SPP\\Roushi\\senjucuirassm_1.nif'),
             ('SPP_RoushiBoots', 'SPP_RoushiBootsAA', 'aaaTobiWarBootsUnenchanted', 'aaaTobiWarBootsAA', 0x0506B9CD,
              "Roushi's Sandals", 'SPP\\Roushi\\warbootsm_1.nif')):
    a, aa = clone_male(*args)
    records['ARMO'].append(a); records['ARMA'].append(aa)

# Han v2: Blades Samurai Armour and Kimonos (SamuraiBlades.esp, not a master: its records only reference vanilla
# forms once the alternate textures are baked). Do-maru armour (vanilla Blades mesh, crimson lacquer), Do-maru
# suneate, Yoroi (black) gauntlets. meshes/SPP/Han/{domaru,suneate,kote}_*.nif, textures/SPP/Han/Samurai;
# tools/recolor_han_domaru.py.
SAMURAI = r'C:\games\ModOrganizer\Skyrim Special Edition\mods\Blades Samurai Armour and Kimonos\SamuraiBlades.esp'
SBR, sb_fid = read_records(SAMURAI, {'ARMO', 'ARMA'}, {
    'ArmorBladesCuirassRed', 'BladesCuirassRedAA', 'ArmorBladesTabiBootsRed', 'BladesTabiBootsRedAA',
    'ArmorBladesGauntletsBlack', 'BladesGlovesBlackAA',
    'ClothesBladesKimonoButterfly', 'BladesKimonoColorButterflyAA', 'BladesSandals', 'BladesSandalsAA'})
for args in (('SPP_HanDomaru', 'SPP_HanDomaruAA', 'ArmorBladesCuirassRed', 'BladesCuirassRedAA', 0x02000D79,
              "Han's Do-maru", 'SPP\\Han\\domaru_1.nif'),
             ('SPP_HanSuneate', 'SPP_HanSuneateAA', 'ArmorBladesTabiBootsRed', 'BladesTabiBootsRedAA', 0x02019DB1,
              "Han's Suneate", 'SPP\\Han\\suneate_1.nif'),
             ('SPP_HanKote', 'SPP_HanKoteAA', 'ArmorBladesGauntletsBlack', 'BladesGlovesBlackAA', 0x02000D8E,
              "Han's Kote", 'SPP\\Han\\kote_1.nif'),
             # Utakata: the Chouchou kimono record (vanilla Greybeard robe mesh) with his recoloured texture baked
             # into meshes/SPP/Utakata/robe_*.nif (tools/recolor_utakata_robe.py); Zori sandals as they are
             ('SPP_UtakataRobe', 'SPP_UtakataRobeAA', 'ClothesBladesKimonoButterfly', 'BladesKimonoColorButterflyAA',
              0x02037D18, "Utakata's Robe", 'SPP\\Utakata\\robe_1.nif'),
             ('SPP_UtakataSandals', 'SPP_UtakataSandalsAA', 'BladesSandals', 'BladesSandalsAA', 0x02007F2D,
              "Utakata's Sandals", 'clothes\\tabi\\setta1_1.nif')):
    a, aa = clone_male(*args, recs=SBR, fid_of=sb_fid)
    records['ARMO'].append(a); records['ARMA'].append(aa)

records['FLST'] = [rec('FLST', FID['SPP_SummonSpells'],
                       [sub('EDID', z('SPP_SummonSpells'))] + [sub('LNAM', u32(FID[s])) for s in SUMMON_SPELLS])]

# ================= step 4: home = QASmoke (vanilla test cell, navmeshed, no actors) =================
# CELL header copied from the current winner (LotD / DBM patch): same as vanilla except
# the Has Water flag and an unlocalised name, so nothing they set gets reverted.
cell = []
for t, d in V['QASmoke']:
    if t == 'FULL': d = z('Editor Smoke Test Cell')
    elif t == 'DATA': d = struct.pack('<H', 0x3)
    cell.append(sub(t, d))
PERSISTENT = 0x400
home_pos = (2496.0, 2304.0, 6976.0, 0.0, 0.0, 3.1416)       # vanilla XMarkerHeading spot
yagura_pos = (2624.0, 2304.0, 6976.0, 0.0, 0.0, 3.1416)
utakata_pos = (2368.0, 2304.0, 6976.0, 0.0, 0.0, 3.1416)
roushi_pos = (2752.0, 2304.0, 6976.0, 0.0, 0.0, 3.1416)
han_pos = (2880.0, 2304.0, 6976.0, 0.0, 0.0, 3.1416)
fuu_pos = (2240.0, 2304.0, 6976.0, 0.0, 0.0, 3.1416)
yugito_pos = (3008.0, 2304.0, 6976.0, 0.0, 0.0, 3.1416)
refs = (rec('ACHR', FID['SPP_YaguraRef'], [sub('EDID', z('SPP_YaguraRef')), sub('NAME', u32(FID['SPP_Yagura'])),
                                           sub('DATA', f32(*yagura_pos))], flags=PERSISTENT) +
        rec('REFR', FID['SPP_HomeMarker'], [sub('EDID', z('SPP_HomeMarker')), sub('NAME', u32(XMARKER_HEADING)),
                                            sub('DATA', f32(*home_pos))], flags=PERSISTENT) +
        rec('ACHR', FID['SPP_UtakataRef'], [sub('EDID', z('SPP_UtakataRef')), sub('NAME', u32(FID['SPP_Utakata'])),
                                            sub('DATA', f32(*utakata_pos))], flags=PERSISTENT) +
        rec('ACHR', FID['SPP_RoushiRef'], [sub('EDID', z('SPP_RoushiRef')), sub('NAME', u32(FID['SPP_Roushi'])),
                                           sub('DATA', f32(*roushi_pos))], flags=PERSISTENT) +
        rec('ACHR', FID['SPP_HanRef'], [sub('EDID', z('SPP_HanRef')), sub('NAME', u32(FID['SPP_Han'])),
                                        sub('DATA', f32(*han_pos))], flags=PERSISTENT) +
        rec('ACHR', FID['SPP_FuuRef'], [sub('EDID', z('SPP_FuuRef')), sub('NAME', u32(FID['SPP_Fuu'])),
                                        sub('DATA', f32(*fuu_pos))], flags=PERSISTENT) +
        rec('ACHR', FID['SPP_YugitoRef'], [sub('EDID', z('SPP_YugitoRef')), sub('NAME', u32(FID['SPP_Yugito'])),
                                           sub('DATA', f32(*yugito_pos))], flags=PERSISTENT))
obj_id = QASMOKE & 0xFFFFFF
cell_body = rec('CELL', QASMOKE, cell) + grup(QASMOKE, grup(QASMOKE, refs, 8), 6)
cell_top = grup(obj_id % 10, grup((obj_id // 10) % 10, cell_body, 3), 2)

# ================= step 5: quest, packages =================
def clone_pack(edid, template, cond_value):
    out = []
    for t, d in V[template]:
        if t == 'EDID': out.append(sub('EDID', z(edid))); continue
        if t in ('CTDA', 'QNAM'): continue                    # drop the template's own conditions/owner
        out.append(sub(t, d))
        if t == 'PSDT': out.append(ctda_global_eq(FID['SPP_PathsState'], cond_value))
    return rec('PACK', FID[edid], out)

records['PACK'] = [
    clone_pack('SPP_PathFollowPlayer', 'BladesFollowPlayerPackage', 1.0),   # FollowerPackageTemplate -> Player
    clone_pack('SPP_PathWait', 'DefaultSandboxCurrentLocation1024', 2.0),
]

PATH_NAMES = ['Yugito', 'Yagura', 'Roushi', 'Han', 'Utakata', 'Fuu']   # alias IDs 1-6
FORCED = {'Yagura': FID['SPP_YaguraRef'], 'Utakata': FID['SPP_UtakataRef'], 'Roushi': FID['SPP_RoushiRef'],
          'Han': FID['SPP_HanRef'], 'Fuu': FID['SPP_FuuRef'], 'Yugito': FID['SPP_YugitoRef']}
OPTIONAL, ESSENTIAL, ALLOW_RESERVED = 0x2, 0x40, 0x200

aliases = [sub('ALST', u32(0)), sub('ALID', z('Player')), sub('FNAM', u32(0)),
           sub('ALFR', u32(PLAYER_REF)), sub('VTCK', u32(0)), sub('ALED', b'')]
for i, name in enumerate(PATH_NAMES, start=1):
    aliases += [sub('ALST', u32(i)), sub('ALID', z(name)), sub('FNAM', u32(OPTIONAL | ESSENTIAL | ALLOW_RESERVED))]
    if name in FORCED: aliases.append(sub('ALFR', u32(FORCED[name])))
    aliases += [sub('ALPC', u32(FID['SPP_PathFollowPlayer'])), sub('ALPC', u32(FID['SPP_PathWait'])),
                sub('VTCK', u32(0)), sub('ALED', b'')]

quest_vmad = vmad(
    [script('SPP_SixPathsQuestScript', [
        p_objs('Paths', [(FID['SPP_SixPathsQuest'], i) for i in range(1, 7)]),
        p_obj('PlayerRef', PLAYER_REF),
        p_obj('SPP_PathsState', FID['SPP_PathsState']),
        p_obj('SPP_SixPathsFaction', FID['SPP_SixPathsFaction']),
        p_obj('SPP_HomeMarker', FID['SPP_HomeMarker']),
        p_objs('CommandPowers', [(FID[p], -1) for p in ('SPP_PowerCommand', 'SPP_PowerSummon', 'SPP_PowerRelease')]),
    ])],
    quest_aliases=[(0, [script('SPP_PlayerAliasScript', [])])] +
                  [(i, [script('SPP_PathAliasScript', [])]) for i in range(1, 7)])

# Placed actors in alias order (Paths[0..5]); the home marker stands in for paths not built yet.
records['FLST'].append(rec('FLST', FID['SPP_PathRefs'], [sub('EDID', z('SPP_PathRefs'))] +
                           [sub('LNAM', u32(FORCED.get(n, FID['SPP_HomeMarker']))) for n in PATH_NAMES]))

records['QUST'] = [rec('QUST', FID['SPP_SixPathsQuest'], [
    sub('EDID', z('SPP_SixPathsQuest')), quest_vmad, sub('FULL', z('Six Paths of Pain')),
    sub('DNAM', struct.pack('<HBBII', 0x0011, 50, 0, 0, 0)),   # Start Game Enabled, priority 50
    sub('NEXT', b''), sub('ANAM', u32(1 + len(PATH_NAMES)))] + aliases)]

# ================= write =================
ORDER = ['GLOB', 'CLAS', 'FACT', 'MGEF', 'SPEL', 'ARMO', 'NPC_', 'CELL', 'QUST', 'PACK', 'CSTY', 'FLST', 'ARMA',
         'OTFT', 'CLFM']
groups = []
for t in ORDER:
    groups.append(grup('CELL', cell_top) if t == 'CELL' else grup(t, b''.join(records[t])))
nrec = sum(len(v) for v in records.values()) + 8 + 7 + len(ORDER)   # + CELL + 7 refs + cell subgroups

hdr = [sub('HEDR', f32(1.7) + u32(nrec, 0x800 + len(FID))), sub('CNAM', z('Claude')),
       sub('SNAM', z("Obito's Six Paths of Pain"))]
for m in MASTERS:
    hdr += [sub('MAST', z(m)), sub('DATA', bytes(8))]
header = rec('TES4', 0, hdr, flags=0x200)   # ESL: all FormIDs are 0x800+

open(OUT, 'wb').write(header + b''.join(groups))
print('wrote', OUT)
for k, v in FID.items(): print(f'  {v:08X} {k}')
