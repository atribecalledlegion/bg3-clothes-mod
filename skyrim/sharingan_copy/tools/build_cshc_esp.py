"""Build Sharingan Copy.esp (ESL).

Usage: build_cshc_esp.py <Data dir with Skyrim/Dawnguard/Dragonborn.esm> <MO2 mods dir> <out.esp>

Records (append-only object IDs, saves reference them):
  0x800 QUST CSHC_Quest          Start Game Enabled, script CSHC_CopyQuestScript
  0x801 SPEL CSHC_EyeAbility     hidden ability: the watching cloak, active only while the Sharingan is open
                                 (vanilla NightEyeTransitionGlobal == 2, set by the Uchiha Clan's Sharingan)
  0x802 MGEF CSHC_EyeCloak       Cloak archetype, applies 0x803 to actors within CLOAK_FEET
  0x803 SPEL CSHC_ObserveSpell   concentration/aimed carrier the cloak refreshes on nearby actors
  0x804 MGEF CSHC_ObserveEffect  script CSHC_ObserveEffect: reports the actor's spell casts to the quest
  0x805 FLST CSHC_Blocked        spells the Sharingan cannot copy (kekkei genkai, hiden, senjutsu, no hand signs,
                                 summoning contracts, vampire/werewolf blood)
  0x806 GLOB CSHC_CopyOn         1 while copying is switched on (cloak condition)
  0x807 MGEF CSHC_CopyToggleEffect script CSHC_CopyToggleEffect: flips 0x806
  0x808 SPEL CSHC_CopyPower      lesser power "Sharingan: Copy", only held while the Sharingan is open
  --- Sharingan Read + smoother Quick Reflexes (2026-10-14) ---
  0x809 MGEF CSHC_SlowTime       Slow Time archetype (no image flash); magnitude comes from the spell
  0x80A FLST CSHC_SlowSpells     the slow-time spells below, in SLOW_MAGS order (script picks the nearest)
  0x80B-0x818 SPEL CSHC_Slow_<n> one slow-time spell per magnitude in SLOW_MAGS
  0x819 MGEF CSHC_QRTriggerEffect script CSHC_QRTriggerEffect: an enemy power-attack swing at the player -> quest
  0x81A SPEL CSHC_QRTriggerSpell  cast by the Uchiha Clan's Quick Reflexes perk (overridden below) instead of its
                                 own instant slow-time spell
  0x81B MGEF CSHC_ReadEffect     script CSHC_ReadEffect on the player: hits taken / blocked -> quest
  0x81C SPEL CSHC_ReadAbility    hidden ability carrying 0x81B
  0x81D-0x81F MGEF CSHC_ReadMark1-3   markers on an enemy for Read tiers 1-3 (adaptation)
  0x820-0x822 SPEL CSHC_ReadMarkSpell1-3
  0x823 MGEF CSHC_OpeningEffect   Counter-Read opening on an enemy (script CSHC_OpeningEffect, 50% stagger)
  0x824 MGEF CSHC_OpeningPerfectEffect  same, read during Quick Reflexes slow time (guaranteed stagger)
  0x825 SPEL CSHC_OpeningSpell, 0x826 SPEL CSHC_OpeningPerfectSpell  (2 s)
  0x827 PERK CSHC_ReadPerk       damage taken from read enemies x0.85/0.75/0.65; damage to an opened enemy x1.5/x2
  --- Kamui upgrades (2026-10-14) ---
  0x828 MGEF CSHC_PhaseEffect     Etherealize: the actual intangibility (Kamui mode, Phase Strike, Reflex Phase)
  0x829 SPEL CSHC_PhaseSpell
  0x82A MGEF CSHC_KamuiSwirlEffect  shows Naruto Overhaul's Kamui swirl art (A0KamuiFX) on the player
  0x82B SPEL CSHC_KamuiSwirlSpell   (1 s)
  0x82C MGEF CSHC_KamuiModeEffect   script CSHC_KamuiModeEffect, added to the Uchiha "Kamui: Ethereal" power
  0x82D FLST CSHC_KamuiTeleports    Kamui travel spells (Uchiha Clan + Naruto Overhaul): using one solidifies you
  0x82E SNDR CSHC_KamuiSlipSD     "obito no kamui" voice line (Sound\FX\CSHC\obito_no_kamui.wav), settings from
                                 vanilla VOCShoutFXThrowVoice (SFX category, stereo output)
  0x82F SOUN CSHC_KamuiSlip       played when an attack passes through you in Kamui
  0x830 GLOB CSHC_InstinctOn      1 = Kamui Instinct on (default)
  0x831 MGEF CSHC_InstinctToggleEffect  script CSHC_InstinctToggleEffect: flips 0x830
  0x832 SPEL CSHC_InstinctPower   lesser power "Kamui: Instinct" (given once the Mangekyo is awakened)
  --- Kamui: Shuriken Barrage (2026-10-14) ---
  0x833 PROJ CSHC_KamuiShurikenProj    Fuma shuriken (meshes\CSHC\kamui_shuriken.nif: Shuriken Spells and Scrolls'
                                       shuriken at 2.5x), arrow type, straight and fast; data from that mod's projectile
  0x834 MGEF CSHC_KamuiShurikenDamage  damage health, aimed (magnitude set by script from level)
  0x835 SPEL CSHC_KamuiShurikenSpell   one shuriken, cast by script from a caster at Obito's eye
  0x836 MGEF CSHC_KamuiShurikenStagger stagger (finale)
  0x837 SPEL CSHC_KamuiShurikenFinal   last shuriken: damage + stagger
  0x838 MGEF CSHC_KamuiBarrageEffect   script CSHC_KamuiBarrageEffect -> CSHC_KamuiQuestScript.Barrage()
  0x839 SPEL CSHC_KamuiBarragePower    lesser power "Kamui: Shuriken Barrage" (given once the Mangekyo is awakened)
  0x83A SOUN CSHC_KamuiSwirlSound      Naruto Overhaul's Kamui warp sound (SNDR A0KamuiSD, kamui.wav) for the barrage's swirl
  --- Kamui: Severance, left eye (2026-10-14) ---
  0x83B MGEF CSHC_SeveranceFocusEffect  the Kamui distortion forming on the target (Naruto Overhaul swirl art)
  0x83C SPEL CSHC_SeveranceFocusSpell   (target actor, not hostile) - UNUSED: the swirl art never showed on the target;
                                        kept so the IDs stay stable (0x841/0x842 do the visual)
  0x83D MGEF CSHC_SeveranceStagger      large stagger when the distortion tears (hostile: counts as your attack)
  0x83E SPEL CSHC_SeveranceStrike
  0x83F MGEF CSHC_SeveranceEffect       script CSHC_KamuiSeveranceEffect -> CSHC_KamuiQuestScript.Severance()
  0x840 SPEL CSHC_SeverancePower        lesser power "Kamui: Severance" (given once the Mangekyo is awakened)
  0x841 ARTO CSHC_KamuiDistortArt       meshes\CSHC\kamui_distortion.nif: the Uchiha Clan's void effect (vanilla summon
                                        portal) with every coloured layer hidden, only its refraction ripple left
  0x842 RFCT CSHC_KamuiDistortVFX       visual effect for that art, played on Severance's target
  override MGEF aaaTobiBecomeEtherealEffect (UchihaClan 0x026C12): archetype Etherealize -> Script, so it keeps
                                 its eye swap, sounds and blindness while CSHC_PhaseEffect does the phasing
  override SPEL aaaTobiBecomeEthereal (UchihaClan 0x026C14): 5 minutes (canon limit) + CSHC_KamuiModeEffect
  override PERK aaaSharinganQuickReflexesPerk (UchihaClan 0x269C1D, as edited by Uchiha Clan Additions): same
                                 entries, but the weapon-swing entry casts 0x81A
Templates come from Skyrim.esm (vanilla Flame Cloak), so DATA layouts match what the CK writes.
"""
import struct, sys, zlib, re, os

DATA, MODS, OUT = sys.argv[1:4]
PLUGINS = {
    'Skyrim.esm': DATA + '/Skyrim.esm', 'Update.esm': DATA + '/Update.esm', 'Dawnguard.esm': DATA + '/Dawnguard.esm',
    'Dragonborn.esm': DATA + '/Dragonborn.esm', 'RaceCompatibility.esm': None,
    'naruto overhaul.esp': MODS + '/Naruto_Overhaul_Special_Edition_Files/naruto overhaul.esp',
    'UchihaClan.esp': MODS + '/The Uchiha Clan/UchihaClan.esp',
    'Uchiha Clan Additions.esp': MODS + '/The Uchiha Clan Additions/Uchiha Clan Additions.esp',
    'SixPathsOfPain.esp': MODS + '/Six Paths of Pain/SixPathsOfPain.esp',
}
MASTERS = list(PLUGINS)
OWN = len(MASTERS) << 24
FID = {n: OWN | (0x800 + i) for i, n in enumerate(
    ['CSHC_Quest', 'CSHC_EyeAbility', 'CSHC_EyeCloak', 'CSHC_ObserveSpell', 'CSHC_ObserveEffect', 'CSHC_Blocked',
     'CSHC_CopyOn', 'CSHC_CopyToggleEffect', 'CSHC_CopyPower', 'CSHC_SlowTime', 'CSHC_SlowSpells']
    + ['CSHC_Slow_%d' % i for i in range(14)]
    + ['CSHC_QRTriggerEffect', 'CSHC_QRTriggerSpell', 'CSHC_ReadEffect', 'CSHC_ReadAbility',
       'CSHC_ReadMark1', 'CSHC_ReadMark2', 'CSHC_ReadMark3', 'CSHC_ReadMarkSpell1', 'CSHC_ReadMarkSpell2',
       'CSHC_ReadMarkSpell3', 'CSHC_OpeningEffect', 'CSHC_OpeningPerfectEffect', 'CSHC_OpeningSpell',
       'CSHC_OpeningPerfectSpell', 'CSHC_ReadPerk',
       'CSHC_PhaseEffect', 'CSHC_PhaseSpell', 'CSHC_KamuiSwirlEffect', 'CSHC_KamuiSwirlSpell', 'CSHC_KamuiModeEffect',
       'CSHC_KamuiTeleports', 'CSHC_KamuiSlipSD', 'CSHC_KamuiSlip',
       'CSHC_InstinctOn', 'CSHC_InstinctToggleEffect', 'CSHC_InstinctPower',
       'CSHC_KamuiShurikenProj', 'CSHC_KamuiShurikenDamage', 'CSHC_KamuiShurikenSpell', 'CSHC_KamuiShurikenStagger',
       'CSHC_KamuiShurikenFinal', 'CSHC_KamuiBarrageEffect', 'CSHC_KamuiBarragePower', 'CSHC_KamuiSwirlSound',
       'CSHC_SeveranceFocusEffect', 'CSHC_SeveranceFocusSpell', 'CSHC_SeveranceStagger', 'CSHC_SeveranceStrike',
       'CSHC_SeveranceEffect', 'CSHC_SeverancePower', 'CSHC_KamuiDistortArt', 'CSHC_KamuiDistortVFX'])}
SLOW_MAGS = [0.01, 0.03, 0.05, 0.08, 0.1, 0.12, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.65, 0.8]   # must match the quest script
VOICE_SLOT = 0x00025BEE
PLAYER_REF, GAME_DAYS_PASSED, NIGHT_EYE_TRANSITION = 0x00000014, 0x00000039, 0x000EFC75
CLOAK_FEET = 80.0            # how far the Sharingan watches
GET_GLOBAL_VALUE = 74
HAS_MAGIC_EFFECT, GET_IS_ID = 214, 72
UCH = lambda local: (MASTERS.index('UchihaClan.esp') << 24) | local

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
def script(name, props): return ws(name) + bytes([0]) + struct.pack('<H', len(props)) + b''.join(props)
def vmad(scripts, quest=False):
    out = struct.pack('<hhH', 5, 2, len(scripts)) + b''.join(scripts)
    if quest: out += bytes([2]) + struct.pack('<H', 0) + ws('') + struct.pack('<H', 0)
    return sub('VMAD', out)
def subs_of(d):
    i = 0
    while i < len(d):
        t = d[i:i+4].decode('latin1'); n = struct.unpack_from('<H', d, i+4)[0]
        yield t, d[i+6:i+6+n]; i += 6 + n

def load(name):
    """-> (records list of (type, local fid in OUR master indexing, subrecord dict))"""
    path = PLUGINS[name]; buf = open(path, 'rb').read()
    hsize = struct.unpack_from('<I', buf, 4)[0]
    masters = [d.rstrip(b'\0').decode() for t, d in subs_of(buf[24:24 + hsize]) if t == 'MAST']
    table = {i: MASTERS.index(m) for i, m in enumerate(masters + [name]) if m in MASTERS}   # only the indexes we use
    out = []
    def walk(o, e):
        while o < e:
            t = buf[o:o+4].decode('latin1'); n = struct.unpack_from('<I', buf, o+4)[0]
            if t == 'GRUP': walk(o+24, o+n); o += n; continue
            fl, fid = struct.unpack_from('<II', buf, o+8); b = buf[o+24:o+24+n]; o += 24 + n
            if t not in ('SPEL', 'MGEF'): continue
            if fl & 0x40000: b = zlib.decompress(b[4:])
            if fid >> 24 != len(masters): continue          # only records this plugin defines
            out.append((t, (table[fid >> 24] << 24) | (fid & 0xFFFFFF), dict(subs_of(b))))
    walk(24 + hsize, len(buf))
    return out

def edid(s): return s.get('EDID', b'').rstrip(b'\0').decode('cp1252', 'replace')

# ---- block list ----
blocked, reasons = [], {}
def block(fid, why):
    if fid not in reasons: blocked.append(fid); reasons[fid] = why
for name in ('UchihaClan.esp', 'Uchiha Clan Additions.esp'):
    for t, fid, s in load(name):
        if t == 'SPEL': block(fid, 'Uchiha kekkei genkai (' + name + ')')
for t, fid, s in load('SixPathsOfPain.esp'):
    if t == 'SPEL': block(fid, 'jinchuriki / tailed-beast power')
NARUTO_BLOCK = re.compile(r'Amaterasu|ShinraTensei|Bansho|Gedo|JutsuUpkeep|Kamui|TruthSeeking|Kyuubi|Insect|'
                          r'Sagemode|SageMode|Rasengan|RasenShuriken|Gate\d|Muscletear|A0SJ', re.I)
for t, fid, s in load('naruto overhaul.esp'):
    if t == 'SPEL' and NARUTO_BLOCK.search(edid(s)): block(fid, 'kekkei genkai / hiden / senjutsu / no seals / summoning')
VANILLA_BLOCK = re.compile(r'Vampire|Werewolf|VampireLord|Lycanthropy', re.I)
for name in ('Skyrim.esm', 'Dawnguard.esm', 'Dragonborn.esm'):
    for t, fid, s in load(name):
        if t == 'SPEL' and VANILLA_BLOCK.search(edid(s)): block(fid, 'bloodline (vampire / werewolf)')

# ---- templates from vanilla Flame Cloak ----
SK = {fid: (t, s) for t, fid, s in load('Skyrim.esm') if fid in (0x0003AE9E, 0x0002B385)}
cloak_data = bytearray(SK[0x0003AE9E][1]['DATA'])
MGEF_FID_OFFSETS = [0x08, 0x18, 0x20, 0x24, 0x48, 0x4C, 0x5C, 0x60, 0x64, 0x6C, 0x74, 0x78, 0x7C, 0x80, 0x84, 0x88]
HIDE_UI, NO_HIT_EVENT, NO_MAG, NO_AREA, NO_DUR, PAINLESS, NO_HIT_EFFECT = 0x8000, 0x10, 0x400, 0x800, 0x200, 0x4000000, 0x8000000

def mgef_data(flags, archetype, cast, deliv, assoc=0):
    d = bytearray(cloak_data)
    for o in MGEF_FID_OFFSETS: struct.pack_into('<I', d, o, 0)
    struct.pack_into('<I', d, 0x00, flags)
    struct.pack_into('<I', d, 0x08, assoc)
    struct.pack_into('<ii', d, 0x0C, -1, -1)              # no magic skill, no resist
    struct.pack_into('<f', d, 0x04, 0.0)                   # base cost
    struct.pack_into('<Ii', d, 0x40, archetype, -1)
    struct.pack_into('<II', d, 0x50, cast, deliv)
    return bytes(d)

eye_cloak = rec('MGEF', FID['CSHC_EyeCloak'], [
    sub('EDID', z('CSHC_EyeCloak')), sub('FULL', z('Sharingan: Watching')),
    sub('DATA', mgef_data(HIDE_UI | NO_HIT_EVENT | PAINLESS | NO_HIT_EFFECT, 35, 0, 0, FID['CSHC_ObserveSpell'])),
    sub('SNDD', b''), sub('DNAM', z(''))])
observe_effect = rec('MGEF', FID['CSHC_ObserveEffect'], [
    sub('EDID', z('CSHC_ObserveEffect')),
    vmad([script('CSHC_ObserveEffect', [p_obj('Master', FID['CSHC_Quest'])])]),
    sub('FULL', z('Watched by the Sharingan')),
    sub('DATA', mgef_data(HIDE_UI | NO_HIT_EVENT | NO_MAG | NO_AREA | PAINLESS | NO_HIT_EFFECT, 1, 2, 2)),
    sub('SNDD', b''), sub('DNAM', z(''))])
def effect(mgef, mag, area, dur): return sub('EFID', u32(mgef)) + sub('EFIT', struct.pack('<fII', mag, area, dur))
def cond_global_eq(glob, value):
    return sub('CTDA', struct.pack('<B3xfHHIIIIi', 0x00, value, GET_GLOBAL_VALUE, 0, glob, 0, 0, 0, -1))
eye_ability = rec('SPEL', FID['CSHC_EyeAbility'], [
    sub('EDID', z('CSHC_EyeAbility')), sub('OBND', bytes(12)), sub('FULL', z('Sharingan: Copy')), sub('DESC', z('')),
    sub('SPIT', struct.pack('<IIIfIIffI', 0, 0, 4, 0.0, 0, 0, 0.0, 0.0, 0)),          # Ability, constant, self
    effect(FID['CSHC_EyeCloak'], CLOAK_FEET, 0, 0), cond_global_eq(NIGHT_EYE_TRANSITION, 2.0),
    cond_global_eq(FID['CSHC_CopyOn'], 1.0)])
copy_on = rec('GLOB', FID['CSHC_CopyOn'], [sub('EDID', z('CSHC_CopyOn')), sub('FNAM', b's'), sub('FLTV', struct.pack('<f', 0.0))])
toggle_effect = rec('MGEF', FID['CSHC_CopyToggleEffect'], [
    sub('EDID', z('CSHC_CopyToggleEffect')),
    vmad([script('CSHC_CopyToggleEffect', [p_obj('CopyOn', FID['CSHC_CopyOn'])])]),
    sub('FULL', z('Sharingan: Copy')),
    sub('DATA', mgef_data(NO_HIT_EVENT | NO_MAG | NO_AREA | NO_DUR | PAINLESS | NO_HIT_EFFECT, 1, 1, 0)),
    sub('SNDD', b''), sub('DNAM', z(''))])
copy_power = rec('SPEL', FID['CSHC_CopyPower'], [
    sub('EDID', z('CSHC_CopyPower')), sub('OBND', bytes(12)), sub('FULL', z('Sharingan: Copy')),
    sub('ETYP', u32(VOICE_SLOT)),
    sub('DESC', z("Before the Sharingan, no hand sign stays secret. With copying on, any jutsu cast before your eyes can "
                  "become your own. Use while your Sharingan is open to begin or end the copying.")),
    sub('SPIT', struct.pack('<IIIfIIffI', 0, 0x1, 3, 0.0, 1, 0, 0.0, 0.0, 0)),   # Lesser Power, fire and forget, self
    effect(FID['CSHC_CopyToggleEffect'], 0.0, 0, 0)])
observe_spell = rec('SPEL', FID['CSHC_ObserveSpell'], [
    sub('EDID', z('CSHC_ObserveSpell')), sub('OBND', bytes(12)), sub('FULL', z('Watched by the Sharingan')),
    sub('DESC', z('')), sub('SPIT', struct.pack('<IIIfIIffI', 0, 0x1, 0, 0.0, 2, 2, 0.0, 0.0, 0)),  # like FlameCloakDmg
    effect(FID['CSHC_ObserveEffect'], 0.0, 0, 2)])
blocked_list = rec('FLST', FID['CSHC_Blocked'], [sub('EDID', z('CSHC_Blocked'))] + [sub('LNAM', u32(f)) for f in blocked])
# ---- Sharingan Read + smoother Quick Reflexes ----
def p_bool(name, v): return ws(name) + bytes([5, 1, 1 if v else 0])
def spit(stype, cast, deliv, flags=0x1): return sub('SPIT', struct.pack('<IIIfIIffI', 0, flags, stype, 0.0, cast, deliv, 0.0, 0.0, 0))
QUIET = HIDE_UI | NO_HIT_EVENT | PAINLESS | NO_HIT_EFFECT
NO_RESIST = 0x1 | 0x100000 | 0x200000          # manual cost, ignore resistance, no absorb/reflect
def mgef(name, full, data, scripts=None):
    s_ = [sub('EDID', z(name))] + ([vmad(scripts)] if scripts else []) + [sub('FULL', z(full)), sub('DATA', data), sub('SNDD', b''), sub('DNAM', z(''))]
    return rec('MGEF', FID[name], s_)
def spel(name, full, stype, cast, deliv, effects, flags=0x1):
    return rec('SPEL', FID[name], [sub('EDID', z(name)), sub('OBND', bytes(12)), sub('FULL', z(full)), sub('DESC', z('')),
                                   spit(stype, cast, deliv, flags)] + effects)
master = [p_obj('Master', FID['CSHC_Quest'])]
# One slow-time effect per Quick Reflexes (an ending slow-time effect resets time to normal, so stepping through
# several effects cancelled the slowdown). Flags and screen effect as vanilla PerkQuickReflexesEffect:
# no recast, hide in UI, no area + MagicImodBasicScript with QuickReflexesImod (fades in and out).
def p_obj_raw(name, fid): return ws(name) + bytes([1, 1]) + struct.pack('<hhI', 0, -1, fid)
new_mgef = mgef('CSHC_SlowTime', 'Sharingan: Quick Reflexes', mgef_data(0x20000 | HIDE_UI | NO_AREA | NO_HIT_EVENT, 37, 1, 0),
                [script('MagicImodBasicScript', [p_obj_raw('ImodFX', 0x0010C761)])])
slow_spells = b''.join(spel('CSHC_Slow_%d' % i, 'Sharingan: Quick Reflexes', 0, 1, 0, [effect(FID['CSHC_SlowTime'], m, 0, 3)])
                       for i, m in enumerate(SLOW_MAGS))
slow_list = rec('FLST', FID['CSHC_SlowSpells'], [sub('EDID', z('CSHC_SlowSpells'))]
                + [sub('LNAM', u32(FID['CSHC_Slow_%d' % i])) for i in range(len(SLOW_MAGS))])
new_mgef += mgef('CSHC_QRTriggerEffect', 'Sharingan: Quick Reflexes', mgef_data(QUIET | NO_MAG | NO_AREA, 1, 1, 1),
                 [script('CSHC_QRTriggerEffect', master)])
new_spel = spel('CSHC_QRTriggerSpell', 'Quick Reflexes', 0, 1, 1, [effect(FID['CSHC_QRTriggerEffect'], 0.0, 0, 1)])
new_mgef += mgef('CSHC_ReadEffect', 'Sharingan: Read', mgef_data(QUIET | NO_MAG | NO_AREA | NO_DUR, 1, 0, 0),
                 [script('CSHC_ReadEffect', master)])
new_spel += spel('CSHC_ReadAbility', 'Sharingan: Read', 4, 0, 0, [effect(FID['CSHC_ReadEffect'], 0.0, 0, 0)], flags=0)
for i, txt in ((1, 'adapting'), (2, 'reading'), (3, 'seeing through')):
    new_mgef += mgef('CSHC_ReadMark%d' % i, 'Sharingan: ' + txt, mgef_data(QUIET | NO_MAG | NO_AREA, 1, 1, 3))
    new_spel += spel('CSHC_ReadMarkSpell%d' % i, 'Sharingan: ' + txt, 0, 1, 3,
                     [effect(FID['CSHC_ReadMark%d' % i], 0.0, 0, 3600)], NO_RESIST)
for name, perfect in (('CSHC_OpeningEffect', False), ('CSHC_OpeningPerfectEffect', True)):
    new_mgef += mgef(name, 'Sharingan: opening', mgef_data(QUIET | NO_MAG | NO_AREA, 1, 1, 3),
                     [script('CSHC_OpeningEffect', [p_obj('PlayerRef', PLAYER_REF), p_bool('Perfect', perfect)])])
new_spel += spel('CSHC_OpeningSpell', 'Sharingan: opening', 0, 1, 3, [effect(FID['CSHC_OpeningEffect'], 0.0, 0, 2)], NO_RESIST)
new_spel += spel('CSHC_OpeningPerfectSpell', 'Sharingan: opening', 0, 1, 3,
                 [effect(FID['CSHC_OpeningPerfectEffect'], 0.0, 0, 2)], NO_RESIST)

def ctda(fn, p1, value=1.0, op=0x00, runon=0):
    return sub('CTDA', struct.pack('<B3xfHHIIIIi', op, value, fn, 0, p1, 0, runon, 0, -1))
def entry_mult(ep, value, tab, conds):
    """Entry point, Multiply Value, 3 condition tabs; conds go on tab `tab`."""
    return (sub('PRKE', bytes([2, 0, 0])) + sub('DATA', bytes([ep, 3, 3])) + sub('PRKC', bytes([tab])) + b''.join(conds)
            + sub('EPFT', bytes([1])) + sub('EPFD', struct.pack('<f', value)) + sub('PRKF', b''))
MOD_ATTACK_DAMAGE, MOD_INCOMING_DAMAGE = 0x23, 0x24     # checked against vanilla perks (crExtraDamage, DeftMovement)
read_perk = rec('PERK', FID['CSHC_ReadPerk'], [
    sub('EDID', z('CSHC_ReadPerk')), sub('FULL', z('Sharingan: Read')),
    sub('DESC', z('The Sharingan sees the blow before it is thrown. The longer you fight an enemy with your eyes open, '
                  'the more of their rhythm you learn, until every attack they make is one you have already seen.')),
    sub('DATA', bytes([0, 0, 1, 0, 1])),
    entry_mult(MOD_INCOMING_DAMAGE, 0.85, 1, [ctda(HAS_MAGIC_EFFECT, FID['CSHC_ReadMark1'])]),
    entry_mult(MOD_INCOMING_DAMAGE, 0.75, 1, [ctda(HAS_MAGIC_EFFECT, FID['CSHC_ReadMark2'])]),
    entry_mult(MOD_INCOMING_DAMAGE, 0.65, 1, [ctda(HAS_MAGIC_EFFECT, FID['CSHC_ReadMark3'])]),
    entry_mult(MOD_ATTACK_DAMAGE, 1.5, 2, [ctda(HAS_MAGIC_EFFECT, FID['CSHC_OpeningEffect'])]),
    entry_mult(MOD_ATTACK_DAMAGE, 2.0, 2, [ctda(HAS_MAGIC_EFFECT, FID['CSHC_OpeningPerfectEffect'])])])

# Uchiha Quick Reflexes perk, taken from Uchiha Clan Additions (the winning version), weapon-swing spell swapped
def raw_record(name, want):
    buf = open(PLUGINS[name], 'rb').read(); hsize = struct.unpack_from('<I', buf, 4)[0]
    masters = [d.rstrip(b'\0').decode() for t, d in subs_of(buf[24:24 + hsize]) if t == 'MAST']
    found = []
    def walk(o, e):
        while o < e:
            t = buf[o:o+4].decode('latin1'); n = struct.unpack_from('<I', buf, o+4)[0]
            if t == 'GRUP': walk(o + 24, o + n); o += n; continue
            fl, fid = struct.unpack_from('<II', buf, o+8)
            if t == 'PERK' and (fid & 0xFFFFFF) == want:
                b = buf[o+24:o+24+n]
                if fl & 0x40000: b = zlib.decompress(b[4:])
                found.append(list(subs_of(b)))
            o += 24 + n
    walk(24 + hsize, len(buf))
    assert found, 'perk %X not found in %s' % (want, name)
    return masters, found[0]
add_masters, qr_subs = raw_record('Uchiha Clan Additions.esp', 0x269C1D)
remap = {i: MASTERS.index(m) for i, m in enumerate(add_masters)}
def fix_fid(v): return (remap[v >> 24] << 24) | (v & 0xFFFFFF) if (v >> 24) in remap else v
out_subs, swapped, last_ep = [], 0, None
for t, d in qr_subs:
    if t == 'DATA' and len(d) == 3: last_ep = d[0]
    if t == 'CTDA':
        d = bytearray(d); fn = struct.unpack_from('<H', d, 8)[0]
        if fn in (HAS_MAGIC_EFFECT, 448, 560, 693, GET_IS_ID):
            struct.pack_into('<I', d, 12, fix_fid(struct.unpack_from('<I', d, 12)[0]))
        d = bytes(d)
    if t == 'EPFD' and last_ep == 0x43 and len(d) == 4:
        d = u32(FID['CSHC_QRTriggerSpell']); swapped += 1
    out_subs.append(sub(t, d))
assert swapped == 1, swapped
qr_perk = rec('PERK', UCH(0x269C1D), out_subs)

# ---- Kamui upgrades ----
NARUTO = lambda local: (MASTERS.index('naruto overhaul.esp') << 24) | local
KAMUI_MODE_SECONDS = 300            # canon: about five minutes of intangibility
def mgef_art(name, full, flags, archetype, cast, deliv, hit_art=0, scripts=None):
    d = bytearray(mgef_data(flags, archetype, cast, deliv)); struct.pack_into('<I', d, 0x60, hit_art)
    return mgef(name, full, bytes(d), scripts)
kamui_mgef = mgef_art('CSHC_PhaseEffect', 'Kamui: Intangible', 0x20000 | HIDE_UI | NO_MAG | NO_AREA | NO_HIT_EVENT, 41, 1, 0)
kamui_mgef += mgef_art('CSHC_KamuiSwirlEffect', 'Kamui', QUIET | NO_MAG | NO_AREA, 1, 1, 0, NARUTO(0x0B9D76))
kamui_mgef += mgef('CSHC_KamuiModeEffect', 'Kamui: Ethereal', mgef_data(QUIET | NO_MAG | NO_AREA, 1, 1, 0),
                   [script('CSHC_KamuiModeEffect', [p_obj('Master', FID['CSHC_Quest'])])])
kamui_spel = spel('CSHC_PhaseSpell', 'Kamui: Intangible', 0, 1, 0, [effect(FID['CSHC_PhaseEffect'], 0.0, 0, KAMUI_MODE_SECONDS)])
kamui_spel += spel('CSHC_KamuiSwirlSpell', 'Kamui', 0, 1, 0, [effect(FID['CSHC_KamuiSwirlEffect'], 0.0, 0, 1)])
TELEPORTS = [UCH(x) for x in (0x026C11, 0x028CBD, 0x031F1E, 0x0334CF, 0x035551, 0x035AB8, 0x06922D, 0x377ADA)] \
          + [NARUTO(x) for x in (0x0B9D63, 0x0B9D67, 0x0B9D71, 0x0B9D74)]
kamui_teleports = rec('FLST', FID['CSHC_KamuiTeleports'], [sub('EDID', z('CSHC_KamuiTeleports'))] + [sub('LNAM', u32(f)) for f in TELEPORTS])

# Kamui slip sound: a copy of vanilla VOCShoutFXThrowVoice (0x000F8B) playing our file
slip_sd = rec('SNDR', FID['CSHC_KamuiSlipSD'], [
    sub('EDID', z('CSHC_KamuiSlipSD')), sub('CNAM', u32(0x1EEF540A)), sub('GNAM', u32(0x000172A1)),
    sub('ANAM', z(r'Data\Sound\FX\CSHC\obito_no_kamui.wav')), sub('ONAM', u32(0x000ABF1A)),
    sub('LNAM', bytes(4)), sub('BNAM', bytes.fromhex('00004000b000'))])
slip_sound = rec('SOUN', FID['CSHC_KamuiSlip'], [sub('EDID', z('CSHC_KamuiSlip')), sub('OBND', bytes(12)),
                                                  sub('SDSC', u32(FID['CSHC_KamuiSlipSD']))])

# Kamui Instinct: automatic short phase when overwhelmed; on/off power
instinct_on = rec('GLOB', FID['CSHC_InstinctOn'], [sub('EDID', z('CSHC_InstinctOn')), sub('FNAM', b's'), sub('FLTV', struct.pack('<f', 1.0))])
instinct_mgef = mgef('CSHC_InstinctToggleEffect', 'Kamui: Instinct', mgef_data(NO_HIT_EVENT | NO_MAG | NO_AREA | NO_DUR | PAINLESS | NO_HIT_EFFECT, 1, 1, 0),
                     [script('CSHC_InstinctToggleEffect', [p_obj('InstinctOn', FID['CSHC_InstinctOn'])])])
instinct_power = rec('SPEL', FID['CSHC_InstinctPower'], [
    sub('EDID', z('CSHC_InstinctPower')), sub('OBND', bytes(12)), sub('FULL', z('Kamui: Instinct')),
    sub('ETYP', u32(VOICE_SLOT)),
    sub('DESC', z('Years of war have taught your body to slip away before your mind decides. When two enemies strike '
                  'at once, or death draws close with foes still upon you, your Mangekyo pulls you into Kamui for a '
                  'heartbeat. Use to trust that instinct, or to rely on your own will. It needs 45 seconds to return.')),
    sub('SPIT', struct.pack('<IIIfIIffI', 0, 0x1, 3, 0.0, 1, 0, 0.0, 0.0, 0)),    # Lesser Power, fire and forget, self
    effect(FID['CSHC_InstinctToggleEffect'], 0.0, 0, 0)])

# ---- Kamui: Shuriken Barrage ----
SHURIKEN_ESP = 'C:/Users/harvey/AppData/Local/Temp/claude/C--Users-harvey-Documents-bg3-clothes-mods/b00002a5-33b0-4407-ad9d-c27f413627de/scratchpad/shuriken_mod/Shuriken Spells and Scrolls.esp'
def shuriken_record(want_type, want_id):
    buf = open(SHURIKEN_ESP, 'rb').read(); hsize = struct.unpack_from('<I', buf, 4)[0]
    found = []
    def walk(o, e):
        while o < e:
            t = buf[o:o+4].decode('latin1'); n = struct.unpack_from('<I', buf, o+4)[0]
            if t == 'GRUP': walk(o + 24, o + n); o += n; continue
            fl, fid = struct.unpack_from('<II', buf, o+8)
            if t == want_type and (fid & 0xFFFFFF) == want_id:
                b = buf[o+24:o+24+n]
                if fl & 0x40000: b = zlib.decompress(b[4:])
                found.append(dict(subs_of(b)))
            o += 24 + n
    walk(24 + hsize, len(buf))
    assert len(found) == 1, (want_type, hex(want_id))
    return found[0]
sp = shuriken_record('PROJ', 0x005909)
pdata = bytearray(sp['DATA'])
struct.pack_into('<fff', pdata, 4, 0.0, 6000.0, 6000.0)      # no drop, fast, long range
kamui_proj = rec('PROJ', FID['CSHC_KamuiShurikenProj'], [
    sub('EDID', z('CSHC_KamuiShurikenProj')), sub('OBND', sp['OBND']), sub('FULL', z('Fuma Shuriken')),
    sub('MODL', z(r'CSHC\kamui_shuriken.nif')), sub('MODT', sp['MODT']),
    sub('DATA', bytes(pdata)), sub('NAM1', sp['NAM1']), sub('VNAM', sp['VNAM'])])
sm = shuriken_record('MGEF', 0x005907)
mdata = bytearray(sm['DATA'])
struct.pack_into('<I', mdata, 0x48, FID['CSHC_KamuiShurikenProj'])     # only plugin reference; the rest are Skyrim.esm
dmg = rec('MGEF', FID['CSHC_KamuiShurikenDamage'], [
    sub('EDID', z('CSHC_KamuiShurikenDamage')), sub('FULL', z('Kamui: Shuriken')), sub('MDOB', sm['MDOB']),
    sub('KSIZ', sm['KSIZ']), sub('KWDA', sm['KWDA']), sub('DATA', bytes(mdata)), sub('SNDD', sm['SNDD']),
    sub('DNAM', z(''))])
sdata = bytearray(mdata)
struct.pack_into('<Ii', sdata, 0x40, 33, -1)                            # Stagger
stag = rec('MGEF', FID['CSHC_KamuiShurikenStagger'], [
    sub('EDID', z('CSHC_KamuiShurikenStagger')), sub('FULL', z('Kamui: Shuriken')), sub('MDOB', sm['MDOB']),
    sub('DATA', bytes(sdata)), sub('SNDD', b''), sub('DNAM', z(''))])
shot = spel('CSHC_KamuiShurikenSpell', 'Kamui: Shuriken', 0, 1, 2, [effect(FID['CSHC_KamuiShurikenDamage'], 20.0, 0, 0)], NO_RESIST)
final = spel('CSHC_KamuiShurikenFinal', 'Kamui: Shuriken', 0, 1, 2, [effect(FID['CSHC_KamuiShurikenDamage'], 20.0, 0, 0),
                                                                   effect(FID['CSHC_KamuiShurikenStagger'], 0.6, 0, 0)], NO_RESIST)
barrage_mgef = mgef('CSHC_KamuiBarrageEffect', 'Kamui: Shuriken Barrage', mgef_data(NO_HIT_EVENT | NO_MAG | NO_AREA | NO_DUR | PAINLESS | NO_HIT_EFFECT, 1, 1, 0),
                    [script('CSHC_KamuiBarrageEffect', [p_obj('Master', FID['CSHC_Quest'])])])
barrage_power = rec('SPEL', FID['CSHC_KamuiBarragePower'], [
    sub('EDID', z('CSHC_KamuiBarragePower')), sub('OBND', bytes(12)), sub('FULL', z('Kamui: Shuriken Barrage')),
    sub('ETYP', u32(VOICE_SLOT)),
    sub('DESC', z('Kamui hides more than its master. From the swirling dark behind your eye, a storm of Fuma shuriken '
                  'pours out at your foe, the last one heavy enough to stagger. Needs the Mangekyo Sharingan open.')),
    sub('SPIT', struct.pack('<IIIfIIffI', 0, 0x1, 3, 0.0, 1, 0, 0.0, 0.0, 0)),
    effect(FID['CSHC_KamuiBarrageEffect'], 0.0, 0, 0)])
swirl_sound = rec('SOUN', FID['CSHC_KamuiSwirlSound'], [sub('EDID', z('CSHC_KamuiSwirlSound')), sub('OBND', bytes(12)),
                                                        sub('SDSC', u32(NARUTO(0x0BAEE4)))])
barrage_mgefs = dmg + stag + barrage_mgef
barrage_spels = shot + final + barrage_power

# ---- Kamui: Severance (left eye: Kakashi's long-range Kamui) ----
HOSTILE, DETRIMENTAL = 0x1, 0x4
TARGET_ACTOR = 3
sev_mgefs = mgef_art('CSHC_SeveranceFocusEffect', 'Kamui: Severance', QUIET | NO_MAG | NO_AREA, 1, 1, TARGET_ACTOR, NARUTO(0x0B9D76))
sev_mgefs += mgef('CSHC_SeveranceStagger', 'Kamui: Severance',
                  mgef_data(HOSTILE | DETRIMENTAL | NO_AREA | NO_DUR | NO_HIT_EFFECT, 33, 1, TARGET_ACTOR))
sev_mgefs += mgef('CSHC_SeveranceEffect', 'Kamui: Severance', mgef_data(NO_HIT_EVENT | NO_MAG | NO_AREA | NO_DUR | PAINLESS | NO_HIT_EFFECT, 1, 1, 0),
                  [script('CSHC_KamuiSeveranceEffect', [p_obj('Master', FID['CSHC_Quest'])])])
sev_spels = spel('CSHC_SeveranceFocusSpell', 'Kamui: Severance', 0, 1, TARGET_ACTOR,
                 [effect(FID['CSHC_SeveranceFocusEffect'], 0.0, 0, 2)], NO_RESIST)
sev_spels += spel('CSHC_SeveranceStrike', 'Kamui: Severance', 0, 1, TARGET_ACTOR,
                  [effect(FID['CSHC_SeveranceStagger'], 1.0, 0, 0)], NO_RESIST)
sev_spels += rec('SPEL', FID['CSHC_SeverancePower'], [
    sub('EDID', z('CSHC_SeverancePower')), sub('OBND', bytes(12)), sub('FULL', z('Kamui: Severance')),
    sub('ETYP', u32(VOICE_SLOT)),
    sub('DESC', z("The left eye's Kamui reaches across the battlefield. Fix your gaze on a distant enemy and space folds "
                  "around them, tearing through flesh and armor alike, and whatever weapon they held is pulled into "
                  "your dimension. Needs the Mangekyo awakened.")),
    sub('SPIT', struct.pack('<IIIfIIffI', 0, 0x1, 3, 0.0, 1, 0, 0.0, 0.0, 0)),
    effect(FID['CSHC_SeveranceEffect'], 0.0, 0, 0)])
distort_art = rec('ARTO', FID['CSHC_KamuiDistortArt'], [sub('EDID', z('CSHC_KamuiDistortArt')), sub('OBND', bytes(12)),
                  sub('MODL', z(r'CSHC\kamui_distortion.nif')), sub('MODT', bytes.fromhex('020000000000000000000000')),
                  sub('DNAM', u32(1))])
distort_vfx = rec('RFCT', FID['CSHC_KamuiDistortVFX'], [sub('EDID', z('CSHC_KamuiDistortVFX')),
                  sub('DATA', u32(FID['CSHC_KamuiDistortArt'], 0, 0))])

# Uchiha records copied with every FormID moved from UchihaClan.esp's master order to ours
def plugin_record(name, want_type, want_id):
    buf = open(PLUGINS[name], 'rb').read(); hsize = struct.unpack_from('<I', buf, 4)[0]
    masters = [d.rstrip(b'\0').decode() for t, d in subs_of(buf[24:24 + hsize]) if t == 'MAST']
    found = []
    def walk(o, e):
        while o < e:
            t = buf[o:o+4].decode('latin1'); n = struct.unpack_from('<I', buf, o+4)[0]
            if t == 'GRUP': walk(o + 24, o + n); o += n; continue
            fl, fid = struct.unpack_from('<II', buf, o+8)
            if t == want_type and (fid & 0xFFFFFF) == want_id and (fid >> 24) == len(masters):
                b = buf[o+24:o+24+n]
                if fl & 0x40000: b = zlib.decompress(b[4:])
                found.append(list(subs_of(b)))
            o += 24 + n
    walk(24 + hsize, len(buf))
    assert len(found) == 1, (want_type, hex(want_id), len(found))
    table = {i: MASTERS.index(m) for i, m in enumerate(masters + [name])}
    def fix(v):
        return v if v in (0, 0xFFFFFFFF) else (table[v >> 24] << 24) | (v & 0xFFFFFF)
    return found[0], fix

def remap_vmad(v, fix):
    """VMAD v5 objFormat 2: rewrite the FormID of every object (and object-array) property."""
    v = bytearray(v); ver, objfmt, count = struct.unpack_from('<hhH', v, 0); assert ver == 5 and objfmt == 2
    o = 6
    def wstr(o): return o + 2 + struct.unpack_from('<H', v, o)[0]
    for _ in range(count):
        o = wstr(o); o += 1                                   # script name, status
        props = struct.unpack_from('<H', v, o)[0]; o += 2
        for _ in range(props):
            o = wstr(o); ptype = v[o]; o += 2                 # name, type, status
            if ptype == 1:
                struct.pack_into('<I', v, o + 4, fix(struct.unpack_from('<I', v, o + 4)[0])); o += 8
            elif ptype == 2: o = wstr(o)
            elif ptype in (3, 4): o += 4
            elif ptype == 5: o += 1
            elif ptype == 11:
                n = struct.unpack_from('<I', v, o)[0]; o += 4
                for k in range(n):
                    struct.pack_into('<I', v, o + 4, fix(struct.unpack_from('<I', v, o + 4)[0])); o += 8
            elif ptype == 12:
                n = struct.unpack_from('<I', v, o)[0]; o += 4
                for k in range(n): o = wstr(o)
            elif ptype in (13, 14): o += 4 + 4 * struct.unpack_from('<I', v, o)[0]
            elif ptype == 15: o += 4 + struct.unpack_from('<I', v, o)[0]
            else: raise ValueError('VMAD property type %d' % ptype)
    assert o == len(v), (o, len(v))
    return bytes(v)

eth_mgef_subs, fix = plugin_record('UchihaClan.esp', 'MGEF', 0x026C12)
out = []
for t, d in eth_mgef_subs:
    if t == 'VMAD': d = remap_vmad(d, fix)
    elif t == 'MDOB': d = u32(fix(struct.unpack('<I', d)[0]))
    elif t == 'DATA':
        d = bytearray(d)
        for o in MGEF_FID_OFFSETS: struct.pack_into('<I', d, o, fix(struct.unpack_from('<I', d, o)[0]))
        assert struct.unpack_from('<I', d, 0x40)[0] == 41
        struct.pack_into('<I', d, 0x40, 1)                     # Etherealize -> Script (CSHC_PhaseEffect phases now)
        d = bytes(d)
    elif t == 'DNAM':
        d = z('Your body slips partly into the Kamui dimension. Blades and spells pass through you for up to five '
              'minutes; you become solid only for the instant you strike. Cast again to return.')
    else: assert t in ('EDID', 'FULL', 'SNDD'), t
    out.append(sub(t, d))
eth_mgef = rec('MGEF', UCH(0x026C12), out)

eth_spel_subs, fix = plugin_record('UchihaClan.esp', 'SPEL', 0x026C14)
out = []
for t, d in eth_spel_subs:
    if t in ('MDOB', 'ETYP', 'EFID'): d = u32(fix(struct.unpack('<I', d)[0]))
    elif t == 'SPIT':
        d = bytearray(d); struct.pack_into('<I', d, 32, fix(struct.unpack_from('<I', d, 32)[0])); d = bytes(d)
    elif t == 'EFIT': d = struct.pack('<fII', 0.0, 0, KAMUI_MODE_SECONDS)
    elif t == 'DESC':
        d = z('Send your body halfway into the Kamui dimension. For up to five minutes, blades and spells pass through '
              'you, and you become solid only for the instant you strike. Cast again to return early. You cannot travel '
              'through Kamui while intangible.')
    else: assert t in ('EDID', 'OBND', 'FULL'), t
    out.append(sub(t, d))
out += [effect(FID['CSHC_KamuiModeEffect'], 0.0, 0, KAMUI_MODE_SECONDS)]
eth_spel = rec('SPEL', UCH(0x026C14), out)

qust = rec('QUST', FID['CSHC_Quest'], [
    sub('EDID', z('CSHC_Quest')),
    vmad([script('CSHC_CopyQuestScript', [
        p_obj('PlayerRef', PLAYER_REF), p_obj('EyeAbility', FID['CSHC_EyeAbility']), p_obj('Blocked', FID['CSHC_Blocked']),
        p_obj('Stage1', UCH(0x0048CF)), p_obj('Stage2', UCH(0x0048D0)),
        p_obj('GameDaysPassed', GAME_DAYS_PASSED), p_obj('TogglePower', FID['CSHC_CopyPower']),
        p_obj('CopyOn', FID['CSHC_CopyOn']), p_obj('SharinganState', NIGHT_EYE_TRANSITION),
        p_obj('SlowSpells', FID['CSHC_SlowSpells']), p_obj('ReadAbility', FID['CSHC_ReadAbility']),
        p_obj('ReadPerk', FID['CSHC_ReadPerk']), p_obj('MarkSpell1', FID['CSHC_ReadMarkSpell1']),
        p_obj('MarkSpell2', FID['CSHC_ReadMarkSpell2']), p_obj('MarkSpell3', FID['CSHC_ReadMarkSpell3']),
        p_obj('OpeningSpell', FID['CSHC_OpeningSpell']), p_obj('OpeningPerfectSpell', FID['CSHC_OpeningPerfectSpell'])]),
          script('CSHC_KamuiQuestScript', [
        p_obj('PlayerRef', PLAYER_REF), p_obj('PhaseSpell', FID['CSHC_PhaseSpell']),
        p_obj('SwirlSpell', FID['CSHC_KamuiSwirlSpell']), p_obj('KamuiEthereal', UCH(0x026C14)),
        p_obj('Teleports', FID['CSHC_KamuiTeleports']), p_obj('MangekyoAwakened', UCH(0x160CAE)),
        p_obj('SharinganState', NIGHT_EYE_TRANSITION), p_obj('SlipSound', FID['CSHC_KamuiSlip']),
        p_obj('InstinctOn', FID['CSHC_InstinctOn']), p_obj('InstinctPower', FID['CSHC_InstinctPower']),
        p_obj('ShurikenSpell', FID['CSHC_KamuiShurikenSpell']), p_obj('ShurikenFinal', FID['CSHC_KamuiShurikenFinal']),
        p_obj('BarragePower', FID['CSHC_KamuiBarragePower']), p_obj('CasterBase', 0x000B79FF),
        p_obj('SwirlSound', FID['CSHC_KamuiSwirlSound']),
        p_obj('SeveranceFocus', FID['CSHC_SeveranceFocusSpell']), p_obj('SeveranceStrike', FID['CSHC_SeveranceStrike']),
        p_obj('SeverancePower', FID['CSHC_SeverancePower'])])],
        quest=True),
    sub('FULL', z('Sharingan Copy')), sub('DNAM', struct.pack('<HBBII', 0x0011, 50, 0, 0, 0)),
    sub('NEXT', b''), sub('ANAM', u32(0))])

groups = (grup('GLOB', copy_on + instinct_on)
          + grup('MGEF', eye_cloak + observe_effect + toggle_effect + new_mgef + kamui_mgef + eth_mgef + instinct_mgef + barrage_mgefs + sev_mgefs)
          + grup('SPEL', eye_ability + observe_spell + copy_power + slow_spells + new_spel + kamui_spel + eth_spel + instinct_power + barrage_spels + sev_spels)
          + grup('PROJ', kamui_proj) + grup('ARTO', distort_art) + grup('RFCT', distort_vfx)
          + grup('PERK', qr_perk + read_perk)
          + grup('FLST', blocked_list + slow_list + kamui_teleports) + grup('QUST', qust)
          + grup('SNDR', slip_sd) + grup('SOUN', slip_sound + swirl_sound))
hdr = [sub('HEDR', struct.pack('<fII', 1.7, len(FID) + 5, 0x800 + len(FID))), sub('CNAM', z('Claude')),
       sub('SNAM', z('Sharingan Copy'))]
for m in MASTERS: hdr += [sub('MAST', z(m)), sub('DATA', bytes(8))]
open(OUT, 'wb').write(rec('TES4', 0, hdr, flags=0x200) + groups)
print('wrote', OUT, '-', len(blocked), 'blocked spells')
import collections
for why, n in collections.Counter(reasons.values()).most_common(): print(f'  {n:4d}  {why}')
