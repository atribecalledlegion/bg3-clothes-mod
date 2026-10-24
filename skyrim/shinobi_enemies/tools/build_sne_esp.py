"""Build Shinobi Enemies.esp (ESL, master Skyrim.esm only). Phase 1: bandits.

Usage: build_sne_esp.py <Skyrim.esm> <out.esp>

Records (append-only object IDs, saves reference them):
  0x800 KYWD SNE_Bandit          every bandit (SPID: BanditFaction)
  0x801 KYWD SNE_BanditThug      melee bandits         -> flanking gang fighter
  0x802 KYWD SNE_BanditTank      shield bandits        -> holds the front, bashes
  0x803 KYWD SNE_BanditArcher    csHumanMissile bandits -> keeps behind the melee line
  0x804 KYWD SNE_BanditMage      csHumanMagic bandits  -> keeps range, falls back
  0x805 KYWD SNE_BanditChief     csHumanBoss bandits   -> punishes blocking and staggers
  0x806-0x80A CSTY SNE_cs<Role>  the role combat styles (values below, vanilla source in the comments)
  0x80B MGEF SNE_BanditBrainEffect  hidden script effect, script SNE_BanditBrain
  0x80C SPEL SNE_BanditBrain        ability with that effect (SPID gives it to BanditFaction)
  0x80D GLOB SNE_BanditTactics      1 = on, 0 = off (console: set SNE_BanditTactics to 0) for A/B testing
  0x80E CSTY SNE_csBanditThugVeteran  thugs level 25+ (Plunderer and up): patient, opportunistic
  0x80F GLOB SNE_ArchersInCombat      running count of bandit archers in combat (archer repositioning needs 2+)
  0x810 GLOB SNE_RepositionLock       real time until which no other archer may start repositioning
  0x811 MGEF SNE_MageMarkEffect       hidden marker: this bandit fights as a mage (the script adds 0x812)
  0x812 SPEL SNE_MageMark             ability carrying 0x811
  0x813 PERK SNE_BanditPerk           SPID gives it to every bandit; its entries only apply with the mage mark:
                                      spell magnitude x1.3, damage taken x1.25 (glass cannon)
  0x814 SPEL SNE_ParalyzeShort        vanilla Paralyze with a 3 s duration (unused since the support redesign; kept,
                                      IDs are append-only)
  --- vampires (2026-10-15) ---
  0x816 CSTY SNE_csVampireFledgling   lesser vampires: aggressive, flanking
  0x817 CSTY SNE_csVampireElderWait   elders while their lessers still fight: stay back, magic from range
  0x818 CSTY SNE_csVampireElderStrike elders once they engage (or ambush a distracted target)
  0x819 CSTY SNE_csVampireThrall      thralls: fodder, all offense
  0x81A MGEF SNE_VampireBrainEffect   hidden script effect, script SNE_VampireBrain
  0x81B SPEL SNE_VampireBrain         ability (SPID: VampireFaction + VampireThrallFaction)
  0x81C GLOB SNE_VampireTactics       1 on / 0 off
  0x81D FLST SNE_ReinforcedCells      lair cells that already got their extra thralls/fledglings
  0x81E MGEF SNE_BloodHealthEffect    Fortify Health (value modifier, recovers)
  0x81F MGEF SNE_BloodArmorEffect     Fortify armor rating (DamageResist)
  0x820 SPEL SNE_BloodEmpowered       elder's prepared feed: +100 health, +75 armor for 300 s
  --- companion brain (Serana + Ashe, 2026-10-15) ---
  0x821 QUST SNE_CQ                    start-game-enabled, script SNE_CompanionBrain (battlefield analysis, protection,
                                       callouts); owns the callout topics
  0x822 MGEF SNE_AsheShockResistEffect Ashe (automaton): shock resistance -25 (canon: lightning shut her down once)
  0x823 MGEF SNE_AsheShutdownEffect    script SNE_AsheShutdown: strong shock hits can glitch her for 1.5 s
  0x824 SPEL SNE_AsheAutomaton         ability with both (the quest adds it to Ashe)
  0x825 GLOB SNE_CompanionTactics      1 on / 0 off
  --- draugr (2026-10-15) ---
  0x826 CSTY SNE_csDraugrRelentless    common draugr: fearless, never backs off
  0x827 CSTY SNE_csDraugrLord          lords: patient, punishing duelists
  0x828 MGEF SNE_DraugrBrainEffect     script SNE_DraugrBrain; 0x829 SPEL SNE_DraugrBrain (SPID: DraugrFaction)
  0x82A QUST SNE_DQ                    script SNE_DraugrQuest: life force to the master, Edo Tensei revivals
  0x82B FACT SNE_DraugrRevivedFaction  a draugr that already rose again (once only)
  0x82C GLOB SNE_DraugrTactics         1 on / 0 off
  --- warlocks (2026-10-15) ---
  0x82D CSTY SNE_csWarlockSummoner     necromancers/conjurers: stay behind their summons
  0x82E CSTY SNE_csWarlockElemental    fire/frost/storm mages
  0x82F CSTY SNE_csWarlockArmour       a storm mage inside Lightning Release Armour: all offense
  (0x830-0x86F: callout DIAL/INFO pairs, see below; names continue at 0x870)
  0x870 MGEF / 0x871 SPEL SNE_WarlockBrain   script SNE_WarlockBrain (SPID: WarlockFaction + NecromancerFaction)
  0x872 QUST SNE_WQ                    script SNE_WarlockQuest: phylactery revival (outlives the death)
  0x873 FACT SNE_WarlockRevivedFaction already rose from its phylactery
  0x874 GLOB SNE_WarlockTactics        1 on / 0 off
  0x875/0x876 MGEF + 0x877 SPEL SNE_LightningArmour: SpeedMult +30, DamageResist +60, 10 s
  --- Falmer (2026-10-15) ---
  0x878 CSTY SNE_csFalmerHunter        strike and fade in the dark
  0x879 CSTY SNE_csFalmerBoss          steady, punishing
  0x87A MGEF / 0x87B SPEL SNE_FalmerBrain   script SNE_FalmerBrain (SPID: FalmerFaction)
  0x87C GLOB SNE_FalmerTactics         1 on / 0 off
  0x87D GLOB SNE_HiveScreechLock       real time until the next hive screech
  0x87E CSTY SNE_csFalmerRush          against a heavy-armoured player: rush and ambush the tank
  0x880 CSTY SNE_csDraugrSwarm         common draugr behind the front two: wrap around the target, pile on
  0x881 PERK SNE_DraugrPerk            SPID: DraugrFaction. Melee/bow attack damage x1.3 (they hit harder than
                                       bandits to make up for their slow, readable fighting)
  --- Forsworn (2026-10-16), script SNE_ForswornBrain ---
  0x882-0x886 CSTY Fanatic, Archer, Shaman, Briarheart, HagravenSupport
  0x887 MGEF / 0x888 SPEL SNE_ForswornBrain   SPID: ForswornFaction, HagravenFaction
  0x889 GLOB SNE_ForswornTactics
  0x88A PERK SNE_ForswornPerk          shaman mark: spells x0.85, incoming damage x0.8; attack damage x1.19 per
                                       Blessing tier, x1.08 per Blood Tide step, x1.5 under Curse Mark
  0x88B/0x88C ShamanMark, 0x88D/0x88E blessing speed/health effects, 0x88F-0x896 Blessing tiers 1-4,
  0x897-0x8A0 Blood Tide 1-5, 0x8A1-0x8A3 Curse Mark, 0x8A4-0x8A6 Exhaustion
  --- Dwemer automatons (2026-10-16), script SNE_DwemerBrain ---
  0x8A9-0x8AD CSTY SpiderSwarm, SpiderSupport, SphereGuard, SphereLinked, CenturionLinked
  0x8AE MGEF / 0x8AF SPEL SNE_DwemerBrain    SPID: DwarvenAutomatonFaction
  0x8B0 GLOB SNE_DwemerTactics, 0x8B1 GLOB SNE_DwemerAlarmLock, 0x8B2 FLST SNE_DwemerReinforced
  0x8B3 PERK SNE_DwemerPerk            Master Link x0.9 incoming per tier (4 max), slashing x0.7, impact x1.25,
                                       Overdrive attack x1.4, Overheat incoming x1.5
  0x8B4-0x8BB Master Link tiers 1-4, 0x8BC-0x8BE Overdrive, 0x8BF-0x8C0 Overheat
  --- Thalmor (2026-10-16), script SNE_ThalmorBrain ---
  0x8C1-0x8C5 CSTY Contempt, Soldier, Archer, Justiciar, JusticiarContempt
  0x8C6 MGEF / 0x8C7 SPEL SNE_ThalmorBrain   SPID: ThalmorFaction
  0x8C8 GLOB SNE_ThalmorTactics, 0x8C9-0x8CB GLOB intel (melee hits, magic hits, time), 0x8CC GLOB voice lock
  0x8CD FLST SNE_HaughtyVoices         the voice types that recorded the Thalmor lines
  0x8CE/0x8CF Thalmor Ward (magic resist +40, 6 s), 0x8D0/0x8D1 Silencing Seal (no magicka regen, 6 s)
  --- Imperial Legion (2026-10-16), script SNE_LegionBrain ---
  0x8D2-0x8D6 CSTY Line, Soldier, Archer, Mage, Press
  0x8D7 MGEF / 0x8D8 SPEL SNE_LegionBrain    SPID: CWImperialFaction, PenitusOculatusFaction
  0x8D9 GLOB SNE_LegionTactics, 0x8DA-0x8DE GLOB squad intel (power, magic, ranged, melee, time), 0x8DF GLOB adapt
  0x8E0-0x8E2 Formation (+25 block, +25 armour, 4 s), 0x8E3-0x8EA adaptation counters, 0x8EB/0x8EC Legion Ward
  0x8ED PERK SNE_LegionPerk            formation x0.9 incoming; adapted to archery: arrows x0.8
  --- Leaf ninja (2026-10-16), script SNE_LeafNinja (added by SNE_LegionBrain) ---
  0x8EE/0x8EF CSTY LeafJonin, LeafMedic; 0x8F0 MGEF / 0x8F1 SPEL SNE_LeafNinja (ability)
  0x8F2 OTFT SNE_LeafMedicOutfit (grey robes + Penitus boots), 0x8F3 OTFT SNE_LeafEmptyOutfit (captain: Sakura items)
  0x8F4-0x8F6 Strength of a Hundred Seal (+100 armour, +0.3 attack speed, 20 s)
  0x8F7 MGEF / 0x8F8 SPEL SNE_JoninMark  ability on Leaf Jonin: drives the Tobirama moveset (DAR condition
                                       HasMagicEffect 0x8F7) and the upgraded kunai (SNE_LegionPerk: daggers x2)
  0x8A8 FACT SNE_BurnedFaction         a Briarheart killed by fire: no Briar Rite
  0x8A7 FLST SNE_MyLadyVoices          vampire turncoat: voice types that recorded Dawnguard's "My Lady."
  0x87F PERK SNE_FalmerPerk            SPID: FalmerFaction. Spell magnitude x1.15 (their spells hit harder; their
                                       aim comes from hearing, see SNE_FalmerBrain)
  0xA00.. generic vanilla-line DIAL/INFO pairs (warlock arrogance)
  0x830.. DIAL/INFO pairs, one per callout line (tools/companion_lines.py; voice files copied by
          tools/copy_companion_voice.py)
  0x815 CSTY SNE_csBanditBattlemage   damage mages: magic first, keeps range (support mages use 0x809)
The keywords are distributed by SKSE/Plugins/SNE_DISTR.ini; OAR submods key off them.
Combat styles are applied at runtime (SKSE SetCombatStyle on the leveled base), so no NPC record is edited.
Helpers follow skyrim/serana_taekwondo_toggle/tools/build_ctkd_esp.py (tested in game).
"""
import struct, sys, zlib

SKYRIM, OUT = sys.argv[1], sys.argv[2]
OWN = 1 << 24
NAMES = ['SNE_Bandit', 'SNE_BanditThug', 'SNE_BanditTank', 'SNE_BanditArcher', 'SNE_BanditMage', 'SNE_BanditChief',
         'SNE_csBanditThug', 'SNE_csBanditTank', 'SNE_csBanditArcher', 'SNE_csBanditMage', 'SNE_csBanditChief',
         'SNE_BanditBrainEffect', 'SNE_BanditBrain', 'SNE_BanditTactics',
         'SNE_csBanditThugVeteran', 'SNE_ArchersInCombat', 'SNE_RepositionLock',
         'SNE_MageMarkEffect', 'SNE_MageMark', 'SNE_BanditPerk', 'SNE_ParalyzeShort', 'SNE_csBanditBattlemage',
         'SNE_csVampireFledgling', 'SNE_csVampireElderWait', 'SNE_csVampireElderStrike', 'SNE_csVampireThrall',
         'SNE_VampireBrainEffect', 'SNE_VampireBrain', 'SNE_VampireTactics', 'SNE_ReinforcedCells',
         'SNE_BloodHealthEffect', 'SNE_BloodArmorEffect', 'SNE_BloodEmpowered',
         'SNE_CQ', 'SNE_AsheShockResistEffect', 'SNE_AsheShutdownEffect', 'SNE_AsheAutomaton', 'SNE_CompanionTactics',
         'SNE_csDraugrRelentless', 'SNE_csDraugrLord', 'SNE_DraugrBrainEffect', 'SNE_DraugrBrain', 'SNE_DQ',
         'SNE_DraugrRevivedFaction', 'SNE_DraugrTactics',
         'SNE_csWarlockSummoner', 'SNE_csWarlockElemental', 'SNE_csWarlockArmour', 'SNE_WarlockBrainEffect',
         'SNE_WarlockBrain', 'SNE_WQ', 'SNE_WarlockRevivedFaction', 'SNE_WarlockTactics',
         'SNE_LightningArmourSpeedEffect', 'SNE_LightningArmourResistEffect', 'SNE_LightningArmour',
         'SNE_csFalmerHunter', 'SNE_csFalmerBoss', 'SNE_FalmerBrainEffect', 'SNE_FalmerBrain', 'SNE_FalmerTactics',
         'SNE_HiveScreechLock', 'SNE_csFalmerRush', 'SNE_FalmerPerk', 'SNE_csDraugrSwarm', 'SNE_DraugrPerk',
         'SNE_csForswornFanatic', 'SNE_csForswornArcher', 'SNE_csForswornShaman', 'SNE_csForswornBriarheart',
         'SNE_csHagravenSupport', 'SNE_ForswornBrainEffect', 'SNE_ForswornBrain', 'SNE_ForswornTactics', 'SNE_ForswornPerk',
         'SNE_ShamanMarkEffect', 'SNE_ShamanMark', 'SNE_BlessSpeedEffect', 'SNE_BlessHealthEffect',
         'SNE_BlessTier1Effect', 'SNE_BlessTier1', 'SNE_BlessTier2Effect', 'SNE_BlessTier2',
         'SNE_BlessTier3Effect', 'SNE_BlessTier3', 'SNE_BlessTier4Effect', 'SNE_BlessTier4',
         'SNE_BloodTide1Effect', 'SNE_BloodTide1', 'SNE_BloodTide2Effect', 'SNE_BloodTide2',
         'SNE_BloodTide3Effect', 'SNE_BloodTide3', 'SNE_BloodTide4Effect', 'SNE_BloodTide4',
         'SNE_BloodTide5Effect', 'SNE_BloodTide5', 'SNE_CurseArmourEffect', 'SNE_CurseSpeedEffect', 'SNE_CurseMark',
         'SNE_ExhaustMoveEffect', 'SNE_ExhaustSwingEffect', 'SNE_Exhaustion', 'SNE_MyLadyVoices', 'SNE_BurnedFaction',
         'SNE_csSpiderSwarm', 'SNE_csSpiderSupport', 'SNE_csSphereGuard', 'SNE_csSphereLinked', 'SNE_csCenturionLinked',
         'SNE_DwemerBrainEffect', 'SNE_DwemerBrain', 'SNE_DwemerTactics', 'SNE_DwemerAlarmLock', 'SNE_DwemerReinforced',
         'SNE_DwemerPerk', 'SNE_Link1Effect', 'SNE_Link1', 'SNE_Link2Effect', 'SNE_Link2', 'SNE_Link3Effect', 'SNE_Link3',
         'SNE_Link4Effect', 'SNE_Link4', 'SNE_OverdriveEffect', 'SNE_OverdriveMoveEffect', 'SNE_Overdrive',
         'SNE_OverheatEffect', 'SNE_Overheat',
         'SNE_csThalmorContempt', 'SNE_csThalmorSoldier', 'SNE_csThalmorArcher', 'SNE_csJusticiar',
         'SNE_csJusticiarContempt', 'SNE_ThalmorBrainEffect', 'SNE_ThalmorBrain', 'SNE_ThalmorTactics',
         'SNE_ThalmorIntelMelee', 'SNE_ThalmorIntelMagic', 'SNE_ThalmorIntelTime', 'SNE_ThalmorVoiceLock',
         'SNE_HaughtyVoices', 'SNE_ThalmorWardEffect', 'SNE_ThalmorWard', 'SNE_SilencingSealEffect', 'SNE_SilencingSeal',
         'SNE_csLegionLine', 'SNE_csLegionSoldier', 'SNE_csLegionArcher', 'SNE_csLegionMage', 'SNE_csLegionPress',
         'SNE_LegionBrainEffect', 'SNE_LegionBrain', 'SNE_LegionTactics', 'SNE_LegionIntelPower', 'SNE_LegionIntelMagic',
         'SNE_LegionIntelRanged', 'SNE_LegionIntelMelee', 'SNE_LegionIntelTime', 'SNE_LegionAdapt',
         'SNE_FormationBlockEffect', 'SNE_FormationArmourEffect', 'SNE_Formation',
         'SNE_AdaptPowerEffect', 'SNE_AdaptPower', 'SNE_AdaptMagicEffect', 'SNE_AdaptMagic',
         'SNE_AdaptRangedEffect', 'SNE_AdaptRanged', 'SNE_AdaptMeleeEffect', 'SNE_AdaptMelee',
         'SNE_LegionWardEffect', 'SNE_LegionWard', 'SNE_LegionPerk',
         'SNE_csLeafJonin', 'SNE_csLeafMedic', 'SNE_LeafNinjaEffect', 'SNE_LeafNinja', 'SNE_LeafMedicOutfit',
         'SNE_LeafEmptyOutfit', 'SNE_HundredArmourEffect', 'SNE_HundredSpeedEffect', 'SNE_StrengthOfHundred',
         'SNE_JoninMarkEffect', 'SNE_JoninMark']
def slot(i):    # 0x830-0x86F belongs to the companion callout DIAL/INFO pairs; names after 0x82F continue at 0x870
    v = 0x800 + i
    return v if v < 0x830 else 0x870 + (v - 0x830)
FID = {n: OWN | slot(i) for i, n in enumerate(NAMES)}
# vanilla combat styles the script uses to work out a role when SPID gave no role keyword
PLAYER_REF, XMARKER = 0x14, 0x3B
# vanilla spells the support mages cast through the script (Skyrim.esm, EDIDs checked 2026-10-15).
# Heals: HealOther (target actor, projectile), CloseWounds (self), GrandHealing (self area). Armor: the four
# Flesh spells. Elemental: the three cloaks (cast with the ally as source, so the ally carries the cloak).
MAGE_SPELLS = {'SpellHealOther': 0x12FD2, 'SpellCloseWounds': 0xB62EF, 'SpellGrandHealing': 0xB62EE,
               'SpellOakflesh': 0x5AD5C, 'SpellStoneflesh': 0x5AD5D, 'SpellIronflesh': 0x51B16, 'SpellEbonyflesh': 0x5AD5E,
               'SpellFlameCloak': 0x3AE9F, 'SpellFrostCloak': 0x3AEA2, 'SpellLightningCloak': 0x3AEA3,
               'SpellFrostRune': 0x6796F, 'SpellFus': 0x13E09,
               # battlemages: attack spells by tier
               'SpellFrostbite': 0x2B96B, 'SpellIceSpike': 0x2B96C, 'SpellFireRune': 0x5DB90,
               'SpellIceStorm': 0x45F9C, 'SpellChainLightning': 0x45F9D}
BANDIT_FACTION = 0x1BCC0
PARALYZE = 0x5AD5F
VANILLA = {'VanillaMissile': 0x3BE1D, 'VanillaMagic': 0x3BE1C, 'VanillaBoss1H': 0x3DECE, 'VanillaBoss2H': 0x3DECF,
           'VanillaTank': 0x3CF5A, 'VanillaForswornBossMagic': 0x442D1, 'VanillaWarlock': 0x44CD0}

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
def p_objs(name, fids):    # array of objects (type 11)
    return ws(name) + bytes([11, 1]) + struct.pack('<I', len(fids)) + b''.join(struct.pack('<hhI', 0, -1, f) for f in fids)
def script(name, props): return ws(name) + bytes([0]) + struct.pack('<H', len(props)) + b''.join(props)
def vmad(scripts): return sub('VMAD', struct.pack('<hhH', 5, 2, len(scripts)) + b''.join(scripts))
def subs_of(d):
    i = 0
    while i < len(d):
        t = d[i:i+4].decode('latin1'); n = struct.unpack_from('<H', d, i+4)[0]
        yield t, d[i+6:i+6+n]; i += 6 + n

# --- vanilla template: MGEF DATA layout ---
buf = open(SKYRIM, 'rb').read(); V = {}
def walk(o, e):
    while o < e:
        t = buf[o:o+4].decode('latin1'); n = struct.unpack_from('<I', buf, o+4)[0]
        if t == 'GRUP': walk(o+24, o+n); o += n; continue
        fl, fid = struct.unpack_from('<II', buf, o+8); b = buf[o+24:o+24+n]; o += 24 + n
        if t not in ('MGEF', 'SPEL'): continue
        if t == 'SPEL' and fid != PARALYZE: continue
        if fl & 0x40000: b = zlib.decompress(b[4:])
        s = list(subs_of(b))
        if t == 'SPEL': V['paralyze'] = s; continue
        if dict(s).get('EDID', b'').rstrip(b'\0') == b'CWAbRegenEffect': V['regen'] = s
walk(24 + struct.unpack_from('<I', buf, 4)[0], len(buf))
assert 'regen' in V and 'paralyze' in V

kywds = b''.join(rec('KYWD', FID[n], [sub('EDID', z(n))]) for n in NAMES[:6])

# --- combat styles ---
# CSGD: offensive, defensive, group offensive | weights melee, magic, ranged, shout, unarmed, staff | avoid threat
# CSME: attack staggered, power attack staggered, power attack blocking, bash, bash recoil, bash attack,
#       bash power attack, special attack   (all multipliers)
# CSCR: circle, fallback, flank distance, stalk time      CSLR: strafe
# DATA flags: 0x1 dueling (uses circle/fallback), 0x2 flanking (uses flank distance/stalk time),
#             0x4 allow dual wielding. No vanilla bandit style flanks; wolves (0x2) and Mercer Frey (0x6) do.
CSFL = f32(0.33, 1.0, 0.5, 0.5, 0.5)
DUEL, FLANK, DUAL = 0x1, 0x2, 0x4
def csty(name, csgd, csme, cscr, strafe, flags):
    return rec('CSTY', FID[name], [sub('EDID', z(name)), sub('CSGD', f32(*csgd)), sub('CSME', f32(*csme)),
                                   sub('CSCR', f32(*cscr)), sub('CSLR', f32(strafe)), sub('CSFL', CSFL),
                                   sub('DATA', u32(flags))])
styles = (
    # Thug (below level 25): untrained, bloodthirsty gang fighter. Reckless (offensive .9, defensive .15),
    # flanks (stalk/flank values from vanilla wolves), piles on staggered targets,
    # power attacks into your block, shoves a lot.  (from csHumanMeleeLvl1/Berserker)
    csty('SNE_csBanditThug', (0.9, 0.15, 1.0, 1, 1, 1, 1, 1, 1, 0.2),
         (3.0, 3.0, 3.0, 2.0, 1.5, 1.5, 1.2, 0.5), (0.5, 0.3, 0.5, 0.4), 0.3, FLANK | DUAL)
    # Tank: holds the line, blocks, lots of shield bashes and bash follow-ups.  (from csHumanTankLvl1)
    + csty('SNE_csBanditTank', (0.35, 0.75, 0.6, 1, 1, 1, 1, 1, 1, 0.2),
           (1.5, 2.0, 1.5, 3.0, 3.0, 2.5, 2.0, 0.3), (0.2, 0.1, 0.2, 0.2), 0.2, DUEL)
    # Archer: shoots from behind the melee line, falls back and strafes when you close in.  (from csHumanMissile)
    + csty('SNE_csBanditArcher', (0.4, 0.4, 0.5, 0.6, 1, 4.0, 1, 1, 1, 0.6),
           (0.42, 0.3, 0.72, 0.6, 0.6, 0.3, 0.2, 0.1), (0.5, 0.9, 0.2, 0.2), 0.6, DUEL)
    # Mage = support (2026-10-15 redesign): passive, stays at the back and avoids fighting; the script does the
    # healing and buffing. Very low offensive/group offensive, max defensive and avoid threat, always falls back.
    + csty('SNE_csBanditMage', (0.1, 1.0, 0.15, 0.2, 1.0, 0.5, 1, 1, 1, 1.0),
           (0.5, 0.5, 0.5, 1.0, 1.0, 0.5, 0.5, 0.1), (0.3, 1.0, 0.2, 0.2), 0.5, DUEL)
    # Battlemage: magic first, keeps range, avoids threats.  (from csHumanMagic)
    + csty('SNE_csBanditBattlemage', (0.7, 0.35, 0.5, 0.5, 5.0, 1, 1, 1, 1, 0.7),
           (1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.1), (0.4, 0.9, 0.2, 0.2), 0.5, DUEL)
    # Chief: patient but brutal: waits behind his guard, then punishes blocks and staggers.  (from csHumanBoss1H/2H)
    # 2026-10-15: defensive .6 -> .45, avoid threat .2 -> .1 (reacted too well to power attacks)
    + csty('SNE_csBanditChief', (0.7, 0.45, 0.85, 1, 1, 1, 1, 1, 1, 0.1),
           (4.0, 4.0, 6.0, 4.0, 2.5, 4.0, 2.5, 0.5), (0.15, 0.1, 0.2, 0.2), 0.2, DUEL | DUAL)
    # Veteran thug (level 25+): still flanks, but waits for openings (longer stalk, more circling, guards more)
    # and then punishes them hard (staggered / blocking multipliers).
    # 2026-10-15: defensive .5 -> .35, avoid threat .3 -> .1 (reacted too well to power attacks)
    + csty('SNE_csBanditThugVeteran', (0.6, 0.35, 0.8, 1, 1, 1, 1, 1, 1, 0.1),
           (4.0, 4.0, 3.0, 2.0, 2.0, 2.0, 1.5, 0.5), (0.7, 0.4, 0.5, 0.8), 0.4, FLANK | DUAL))

# --- the bandit brain ability ---
MDATA = bytearray(dict(V['regen'])['DATA'])
NO_DUR, NO_MAG, NO_AREA, HIDE_UI = 0x200, 0x400, 0x800, 0x8000
struct.pack_into('<I', MDATA, 0x00, NO_DUR | NO_MAG | NO_AREA | HIDE_UI)
struct.pack_into('<Ii', MDATA, 0x40, 1, -1)        # Script archetype, no actor value
struct.pack_into('<II', MDATA, 0x50, 0, 0)         # Constant Effect, Self
props = [p_obj('KwThug', FID['SNE_BanditThug']), p_obj('KwTank', FID['SNE_BanditTank']),
         p_obj('KwArcher', FID['SNE_BanditArcher']), p_obj('KwMage', FID['SNE_BanditMage']),
         p_obj('KwChief', FID['SNE_BanditChief']),
         p_obj('StyleThug', FID['SNE_csBanditThug']), p_obj('StyleTank', FID['SNE_csBanditTank']),
         p_obj('StyleArcher', FID['SNE_csBanditArcher']), p_obj('StyleMage', FID['SNE_csBanditMage']),
         p_obj('StyleChief', FID['SNE_csBanditChief']), p_obj('TacticsOn', FID['SNE_BanditTactics']),
         p_obj('StyleThugVeteran', FID['SNE_csBanditThugVeteran']),
         p_obj('ArchersInCombat', FID['SNE_ArchersInCombat']), p_obj('RepositionLock', FID['SNE_RepositionLock']),
         p_obj('PlayerRef', PLAYER_REF), p_obj('XMarkerBase', XMARKER),
         p_obj('MageMark', FID['SNE_MageMark']), p_obj('BanditFaction', BANDIT_FACTION),
         p_obj('StyleBattlemage', FID['SNE_csBanditBattlemage']), p_obj('SpellParalyzeShort', FID['SNE_ParalyzeShort'])]
props += [p_obj(k, v) for k, v in MAGE_SPELLS.items()]
props += [p_obj(k, v) for k, v in VANILLA.items()]
mgef = rec('MGEF', FID['SNE_BanditBrainEffect'], [
    sub('EDID', z('SNE_BanditBrainEffect')), vmad([script('SNE_BanditBrain', props)]),
    sub('FULL', z('Bandit Tactics')), sub('DATA', bytes(MDATA)), sub('SNDD', b''), sub('DNAM', z(''))])
spel = rec('SPEL', FID['SNE_BanditBrain'], [
    sub('EDID', z('SNE_BanditBrain')), sub('OBND', bytes(12)), sub('FULL', z('Bandit Tactics')),
    sub('SPIT', u32(0, 0, 4) + f32(0.0) + u32(0, 0) + f32(0.0, 0.0) + u32(0)),   # Ability, Constant Effect, Self
    sub('EFID', u32(FID['SNE_BanditBrainEffect'])), sub('EFIT', f32(0.0) + u32(0, 0))])
# --- bandit mages ---
MARK = bytearray(dict(V['regen'])['DATA'])
struct.pack_into('<I', MARK, 0x00, NO_DUR | NO_MAG | NO_AREA | HIDE_UI)
struct.pack_into('<Ii', MARK, 0x40, 1, -1)
struct.pack_into('<II', MARK, 0x50, 0, 0)
mage_mgef = rec('MGEF', FID['SNE_MageMarkEffect'], [sub('EDID', z('SNE_MageMarkEffect')), sub('FULL', z('Bandit Mage')),
                                                     sub('DATA', bytes(MARK)), sub('SNDD', b''), sub('DNAM', z(''))])
mage_spel = rec('SPEL', FID['SNE_MageMark'], [
    sub('EDID', z('SNE_MageMark')), sub('OBND', bytes(12)), sub('FULL', z('Bandit Mage')),
    sub('SPIT', u32(0, 0, 4) + f32(0.0) + u32(0, 0) + f32(0.0, 0.0) + u32(0)),
    sub('EFID', u32(FID['SNE_MageMarkEffect'])), sub('EFIT', f32(0.0) + u32(0, 0))])
HAS_MAGIC_EFFECT = 214
def ctda(fn, p1, value=1.0, op=0x00, runon=0):
    return sub('CTDA', struct.pack('<B3xfHHIIIIi', op, value, fn, 0, p1, 0, runon, 0, -1))
def entry_mult(ep, value, tab, conds):
    """Entry point, Multiply Value, 3 condition tabs; conds go on tab `tab` (as in sharingan_copy build_cshc_esp.py)."""
    return (sub('PRKE', bytes([2, 0, 0])) + sub('DATA', bytes([ep, 3, 3])) + sub('PRKC', bytes([tab])) + b''.join(conds)
            + sub('EPFT', bytes([1])) + sub('EPFD', struct.pack('<f', value)) + sub('PRKF', b''))
MOD_INCOMING_DAMAGE, MOD_SPELL_MAGNITUDE = 0x24, 0x1D    # 0x1D as in vanilla AugmentedFlames; tab 0 = perk owner
bandit_perk = rec('PERK', FID['SNE_BanditPerk'], [
    sub('EDID', z('SNE_BanditPerk')), sub('FULL', z('Bandit Tactics')), sub('DESC', z('')),
    sub('DATA', bytes([0, 0, 1, 0, 1])),
    entry_mult(MOD_SPELL_MAGNITUDE, 1.3, 0, [ctda(HAS_MAGIC_EFFECT, FID['SNE_MageMarkEffect'])]),
    entry_mult(MOD_INCOMING_DAMAGE, 1.25, 0, [ctda(HAS_MAGIC_EFFECT, FID['SNE_MageMarkEffect'])])])
psubs = []
for t, d in V['paralyze']:
    if t == 'EDID': d = z('SNE_ParalyzeShort')
    elif t == 'FULL': d = z('Paralysis Bolt')
    elif t == 'EFIT': d = d[:8] + struct.pack('<I', 3)    # magnitude, area kept; duration 10 s -> 3 s (shown as 3)
    psubs.append(sub(t, d))
paralyze_short = rec('SPEL', FID['SNE_ParalyzeShort'], psubs)

def gl(name, v): return rec('GLOB', FID[name], [sub('EDID', z(name)), sub('FNAM', b'f'), sub('FLTV', f32(v))])
glob = gl('SNE_BanditTactics', 1.0) + gl('SNE_ArchersInCombat', 0.0) + gl('SNE_RepositionLock', 0.0)

# --- vampires ---
vstyles = (
    # fledgling: hungry and reckless, flanks, piles on
    csty('SNE_csVampireFledgling', (0.8, 0.3, 0.9, 1, 2.0, 1, 1, 1, 1, 0.4),
         (2.5, 2.5, 2.5, 1.5, 1.5, 1.5, 1.2, 0.5), (0.6, 0.3, 0.5, 0.3), 0.5, FLANK | DUAL)
    # elder, waiting: selfish, lets the lessers bleed for it; drains and raises the dead from the back
    + csty('SNE_csVampireElderWait', (0.15, 0.9, 0.2, 0.3, 4.0, 1, 1, 1, 1, 1.0),
           (1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.1), (0.3, 1.0, 0.2, 0.2), 0.6, DUEL)
    # elder, striking: fast, punishing
    + csty('SNE_csVampireElderStrike', (0.85, 0.5, 0.9, 1, 2.5, 1, 1, 1, 1, 0.5),
           (4.0, 4.0, 4.0, 2.5, 2.0, 3.0, 2.5, 0.5), (0.4, 0.2, 0.6, 0.3), 0.5, FLANK | DUAL)
    # thrall: disposable fodder
    + csty('SNE_csVampireThrall', (1.0, 0.05, 1.0, 1, 1, 1, 1, 1, 1, 0.0),
           (2.0, 2.0, 2.0, 1.0, 1.0, 1.0, 1.0, 0.5), (0.0, 0.0, 0.2, 0.2), 0.1, DUEL))
VAMP_VANILLA = {'VanillaVampireBoss': 0x2DFB6, 'VampireThrallFaction': 0x2EB13, 'VampireFaction': 0x27242,
                'VampireKeyword': 0xA82BB,
                'SpellRaiseZombie': 0x7E8E1, 'SpellRevenant': 0x96D94, 'SpellDreadZombie': 0x96D95,
                'SpellInvisibility': 0x33976, 'SpellVampireDrain': 0x8D5C2,
                'ThrallMelee': 0x2ED6E, 'ThrallMissile': 0x2EEDC, 'LesserVampire': 0x2F9E1}
vprops = [p_obj('StyleFledgling', FID['SNE_csVampireFledgling']), p_obj('StyleElderWait', FID['SNE_csVampireElderWait']),
          p_obj('StyleElderStrike', FID['SNE_csVampireElderStrike']), p_obj('StyleThrall', FID['SNE_csVampireThrall']),
          p_obj('TacticsOn', FID['SNE_VampireTactics']), p_obj('ReinforcedCells', FID['SNE_ReinforcedCells']),
          p_obj('PlayerRef', PLAYER_REF), p_obj('XMarkerBase', XMARKER)]
vprops += [p_obj(k, v) for k, v in VAMP_VANILLA.items()]
vprops += [p_obj('BloodEmpowered', FID['SNE_BloodEmpowered'])]
exec(open(__file__.replace('build_sne_esp.py', 'companion_lines.py')).read())
vprops += [p_obj('PlayerFaction', 0xDB1), p_obj('MyLadyVoices', FID['SNE_MyLadyVoices']),
           p_obj('DustFX', 0x4780E), p_obj('AshPile', 0x1B)]    # TurnUnDisintegrate02FXS, DefaultAshPile1
vprops += [p_objs(c, [OWN | generic_ids(i)[0] for i, g in enumerate(GENERIC) if g[1] == c]) for c in ('TurnMyLady', 'TurnObey')]
mylady = rec('FLST', FID['SNE_MyLadyVoices'], [sub('EDID', z('SNE_MyLadyVoices'))]
             + [sub('LNAM', u32(v)) for v in MY_LADY_VOICES.values()])
vmgef = rec('MGEF', FID['SNE_VampireBrainEffect'], [
    sub('EDID', z('SNE_VampireBrainEffect')), vmad([script('SNE_VampireBrain', vprops)]),
    sub('FULL', z('Vampire Tactics')), sub('DATA', bytes(MDATA)), sub('SNDD', b''), sub('DNAM', z(''))])
vspel = rec('SPEL', FID['SNE_VampireBrain'], [
    sub('EDID', z('SNE_VampireBrain')), sub('OBND', bytes(12)), sub('FULL', z('Vampire Tactics')),
    sub('SPIT', u32(0, 0, 4) + f32(0.0) + u32(0, 0) + f32(0.0, 0.0) + u32(0)),
    sub('EFID', u32(FID['SNE_VampireBrainEffect'])), sub('EFIT', f32(0.0) + u32(0, 0))])
glob += gl('SNE_VampireTactics', 1.0)
flst = rec('FLST', FID['SNE_ReinforcedCells'], [sub('EDID', z('SNE_ReinforcedCells'))])
RECOVER = 0x2
HEALTH_AV, DAMAGE_RESIST_AV = 24, 39
def blood_mgef(name, full, av):
    d = bytearray(dict(V['regen'])['DATA'])
    struct.pack_into('<I', d, 0x00, RECOVER | NO_AREA)
    struct.pack_into('<Ii', d, 0x40, 0, av)       # Value Modifier
    struct.pack_into('<II', d, 0x50, 1, 0)        # Fire and Forget, Self
    return rec('MGEF', FID[name], [sub('EDID', z(name)), sub('FULL', z(full)), sub('DATA', bytes(d)),
                                   sub('SNDD', b''), sub('DNAM', z(''))])
blood_mgefs = (blood_mgef('SNE_BloodHealthEffect', 'Blood Empowered', HEALTH_AV)
               + blood_mgef('SNE_BloodArmorEffect', 'Blood Empowered', DAMAGE_RESIST_AV))
blood_spel = rec('SPEL', FID['SNE_BloodEmpowered'], [
    sub('EDID', z('SNE_BloodEmpowered')), sub('OBND', bytes(12)), sub('FULL', z('Blood Empowered')),
    sub('SPIT', u32(0, 0x1, 0) + f32(0.0) + u32(1, 0) + f32(0.0, 0.0) + u32(0)),   # spell, manual cost 0, F&F, self
    sub('EFID', u32(FID['SNE_BloodHealthEffect'])), sub('EFIT', f32(100.0) + u32(0, 300)),
    sub('EFID', u32(FID['SNE_BloodArmorEffect'])), sub('EFIT', f32(75.0) + u32(0, 300))])

# --- companion brain ---
exec(open(__file__.replace('build_sne_esp.py', 'companion_lines.py')).read())
def qvmad(scripts):    # QUST: script list + empty fragment block, no alias scripts
    return sub('VMAD', struct.pack('<hhH', 5, 2, len(scripts)) + b''.join(scripts) + bytes([2]) + struct.pack('<H', 0)
               + ws('') + struct.pack('<H', 0))
line_fids = {}
for i, l in enumerate(LINES):
    d, n = line_ids(i)
    line_fids.setdefault(l[1], []).append(OWN | d)
cq_props = [p_obj('PlayerRef', PLAYER_REF), p_obj('AsheAutomaton', FID['SNE_AsheAutomaton']),
            p_obj('TacticsOn', FID['SNE_CompanionTactics']), p_obj('VampElderWait', FID['SNE_csVampireElderWait'])]
cq_props += [p_objs(cat, fids) for cat, fids in line_fids.items()]
cq = rec('QUST', FID['SNE_CQ'], [
    sub('EDID', z(QUEST)), qvmad([script('SNE_CompanionBrain', cq_props),
                                  script('SNE_JutsuPoseFix', [p_obj('PlayerRef', PLAYER_REF)])]),    # player: Ryuka pose fix
    sub('FULL', z('Shinobi Enemies: Companions')),
    sub('DNAM', struct.pack('<HBBII', 0x0011, 50, 0, 0, 0)),   # start game enabled (as CTKD_Quest, tested)
    sub('NEXT', b''), sub('ANAM', u32(0))])
def child_grup(dial_fid, body):    # topic children group (type 7)
    return b'GRUP' + struct.pack('<IIIHHI', 24 + len(body), dial_fid, 7, 0, 0, 0) + body
dials = b''
for i, (topic, cat, source, src_id, emo, text) in enumerate(LINES):
    d, n = line_ids(i)
    dial = rec('DIAL', OWN | d, [sub('EDID', z(topic)), sub('PNAM', f32(50.0)), sub('QNAM', u32(FID['SNE_CQ'])),
                                 sub('DATA', bytes(4)), sub('SNAM', b'CUST'), sub('TIFC', u32(1))])
    info = rec('INFO', OWN | n, [
        sub('ENAM', struct.pack('<HH', 0, 0)), sub('PNAM', u32(0)), sub('CNAM', b'\0'),
        sub('TRDT', struct.pack('<II4sB3sIB3s', emo, 50, bytes(4), 1, bytes(3), 0, 0, bytes(3))),
        sub('NAM1', z(text)), sub('NAM2', b'\0'), sub('NAM3', b'\0')])
    dials += dial + child_grup(OWN | d, info)
# Ashe automaton: shock weakness (value modifier ElectricResist, detrimental) + shutdown script effect
ELECTRIC_RESIST_AV, DETRIMENTAL = 42, 0x4
ad = bytearray(dict(V['regen'])['DATA'])
struct.pack_into('<I', ad, 0x00, RECOVER | DETRIMENTAL | NO_DUR | NO_AREA | HIDE_UI)
struct.pack_into('<Ii', ad, 0x40, 0, ELECTRIC_RESIST_AV)
struct.pack_into('<II', ad, 0x50, 0, 0)    # constant, self
ashe_resist = rec('MGEF', FID['SNE_AsheShockResistEffect'], [sub('EDID', z('SNE_AsheShockResistEffect')),
    sub('FULL', z('Automaton: Shock Vulnerability')), sub('DATA', bytes(ad)), sub('SNDD', b''), sub('DNAM', z(''))])
ashe_shut = rec('MGEF', FID['SNE_AsheShutdownEffect'], [sub('EDID', z('SNE_AsheShutdownEffect')),
    vmad([script('SNE_AsheShutdown', [p_obj('PlayerRef', PLAYER_REF), p_obj('TacticsOn', FID['SNE_CompanionTactics']),
                                      p_objs('ShutdownLines', line_fids['AsheShutdown'])])]),
    sub('FULL', z('Automaton')), sub('DATA', bytes(MDATA)), sub('SNDD', b''), sub('DNAM', z(''))])
ashe_spel = rec('SPEL', FID['SNE_AsheAutomaton'], [
    sub('EDID', z('SNE_AsheAutomaton')), sub('OBND', bytes(12)), sub('FULL', z('Automaton')),
    sub('SPIT', u32(0, 0, 4) + f32(0.0) + u32(0, 0) + f32(0.0, 0.0) + u32(0)),
    sub('EFID', u32(FID['SNE_AsheShockResistEffect'])), sub('EFIT', f32(25.0) + u32(0, 0)),
    sub('EFID', u32(FID['SNE_AsheShutdownEffect'])), sub('EFIT', f32(0.0) + u32(0, 0))])
glob += gl('SNE_CompanionTactics', 1.0)
# --- draugr ---
dstyles = (
    csty('SNE_csDraugrRelentless', (0.85, 0.25, 0.9, 1, 1, 1, 1, 1, 1, 0.0),
         (2.0, 2.0, 2.5, 1.5, 1.5, 1.2, 1.2, 0.3), (0.05, 0.0, 0.2, 0.2), 0.1, DUEL)
    + csty('SNE_csDraugrLord', (0.7, 0.55, 0.9, 1, 1, 1, 1, 1, 1, 0.2),
           (3.5, 3.5, 4.0, 3.0, 2.0, 3.0, 2.5, 0.5), (0.25, 0.1, 0.2, 0.2), 0.2, DUEL | DUAL)
    # the swarm: the ones that can't reach the front go round the sides and back, and pile on anything staggered
    + csty('SNE_csDraugrSwarm', (0.95, 0.1, 1.0, 1, 1, 1, 1, 1, 1, 0.0),
           (3.0, 3.5, 2.5, 1.5, 1.5, 1.5, 1.2, 0.3), (0.3, 0.0, 0.3, 0.1), 0.4, FLANK))
DRAUGR_VANILLA = {'VanillaBoss1': 0x52197, 'VanillaBoss2': 0xDDDA3, 'VanillaMissile': 0x38A23, 'VanillaMagic': 0x38A24}
dprops = [p_obj('StyleRelentless', FID['SNE_csDraugrRelentless']), p_obj('StyleLord', FID['SNE_csDraugrLord']),
          p_obj('DQ', FID['SNE_DQ']), p_obj('TacticsOn', FID['SNE_DraugrTactics']), p_obj('PlayerRef', PLAYER_REF),
          p_obj('XMarkerBase', XMARKER), p_obj('RevivedFaction', FID['SNE_DraugrRevivedFaction']),
          p_obj('StyleSwarm', FID['SNE_csDraugrSwarm']), p_obj('DraugrFaction', 0x2430D)]
dprops += [p_obj(k, v) for k, v in DRAUGR_VANILLA.items()]
dmgef = rec('MGEF', FID['SNE_DraugrBrainEffect'], [
    sub('EDID', z('SNE_DraugrBrainEffect')), vmad([script('SNE_DraugrBrain', dprops)]),
    sub('FULL', z('Draugr Tactics')), sub('DATA', bytes(MDATA)), sub('SNDD', b''), sub('DNAM', z(''))])
dspel = rec('SPEL', FID['SNE_DraugrBrain'], [
    sub('EDID', z('SNE_DraugrBrain')), sub('OBND', bytes(12)), sub('FULL', z('Draugr Tactics')),
    sub('SPIT', u32(0, 0, 4) + f32(0.0) + u32(0, 0) + f32(0.0, 0.0) + u32(0)),
    sub('EFID', u32(FID['SNE_DraugrBrainEffect'])), sub('EFIT', f32(0.0) + u32(0, 0))])
DRAGON_PRIEST_RACE, DRAUGR_FACTION = 0x131EF, 0x2430D
REANIMATE_FXS, SOULTRAP_TARGET_FXS, SOULTRAP_CAST_FXS = 0x75272, 0x54223, 0x54224
dq = rec('QUST', FID['SNE_DQ'], [
    sub('EDID', z('SNE_DQ')), qvmad([script('SNE_DraugrQuest', [
        p_obj('PlayerRef', PLAYER_REF), p_obj('RevivedFaction', FID['SNE_DraugrRevivedFaction']),
        p_obj('DraugrFaction', DRAUGR_FACTION), p_obj('DragonPriestRace', DRAGON_PRIEST_RACE),
        p_obj('ReanimateFX', REANIMATE_FXS), p_obj('SoulLeaveFX', SOULTRAP_TARGET_FXS),
        p_obj('SoulTakeFX', SOULTRAP_CAST_FXS), p_obj('TacticsOn', FID['SNE_DraugrTactics'])])]),
    sub('FULL', z('Shinobi Enemies: Draugr')),
    sub('DNAM', struct.pack('<HBBII', 0x0011, 50, 0, 0, 0)), sub('NEXT', b''), sub('ANAM', u32(0))])
dfact = rec('FACT', FID['SNE_DraugrRevivedFaction'], [sub('EDID', z('SNE_DraugrRevivedFaction')),
                                                       sub('DATA', u32(1)), sub('CRVA', bytes(20))])
glob += gl('SNE_DraugrTactics', 1.0)
MOD_ATTACK_DAMAGE = 0x23
draugr_perk = rec('PERK', FID['SNE_DraugrPerk'], [
    sub('EDID', z('SNE_DraugrPerk')), sub('FULL', z('Draugr')), sub('DESC', z('')), sub('DATA', bytes([0, 0, 1, 0, 1])),
    sub('PRKE', bytes([2, 0, 0])) + sub('DATA', bytes([MOD_ATTACK_DAMAGE, 3, 3])) + sub('EPFT', bytes([1]))
    + sub('EPFD', struct.pack('<f', 1.3)) + sub('PRKF', b'')])
# --- warlocks ---
wstyles = (
    csty('SNE_csWarlockSummoner', (0.35, 0.75, 0.5, 0.3, 4.0, 1, 1, 1, 1, 0.9),
         (1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.1), (0.3, 1.0, 0.2, 0.2), 0.6, DUEL)
    + csty('SNE_csWarlockElemental', (0.6, 0.5, 0.6, 0.4, 4.0, 1, 1, 1, 1, 0.7),
           (1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.1), (0.4, 0.8, 0.2, 0.2), 0.6, DUEL)
    + csty('SNE_csWarlockArmour', (1.0, 0.2, 0.9, 1.0, 2.0, 1, 1, 1, 1, 0.1),
           (2.5, 2.5, 2.5, 1.5, 1.5, 1.5, 1.2, 0.5), (0.2, 0.0, 0.5, 0.2), 0.3, DUEL | FLANK))
SPEED_AV = 30
def armour_mgef(name, av):
    d = bytearray(dict(V['regen'])['DATA'])
    struct.pack_into('<I', d, 0x00, RECOVER | NO_AREA)
    struct.pack_into('<Ii', d, 0x40, 0, av)
    struct.pack_into('<II', d, 0x50, 1, 0)
    return rec('MGEF', FID[name], [sub('EDID', z(name)), sub('FULL', z('Lightning Release Armour')),
                                   sub('DATA', bytes(d)), sub('SNDD', b''), sub('DNAM', z(''))])
la_mgefs = (armour_mgef('SNE_LightningArmourSpeedEffect', SPEED_AV)
            + armour_mgef('SNE_LightningArmourResistEffect', DAMAGE_RESIST_AV))
la_spel = rec('SPEL', FID['SNE_LightningArmour'], [
    sub('EDID', z('SNE_LightningArmour')), sub('OBND', bytes(12)), sub('FULL', z('Lightning Release Armour')),
    sub('SPIT', u32(0, 0x1, 0) + f32(0.0) + u32(1, 0) + f32(0.0, 0.0) + u32(0)),
    sub('EFID', u32(FID['SNE_LightningArmourSpeedEffect'])), sub('EFIT', f32(30.0) + u32(0, 10)),
    sub('EFID', u32(FID['SNE_LightningArmourResistEffect'])), sub('EFIT', f32(60.0) + u32(0, 10))])
WARLOCK_VANILLA = {
    'ClassNecro': 0xC969F, 'ClassConjurer': 0x1CE14, 'NecromancerFaction': 0x34B74,
    'KwUndead': 0x13796, 'KwDaedra': 0x13797,
    'SpellRaiseZombie': 0x7E8E1, 'SpellRevenant': 0x96D94, 'SpellDreadZombie': 0x96D95,
    'SpellFireball': 0x1C789, 'SpellIceSpike': 0x2B96C,
    'SpellFlameCloak': 0x3AE9F, 'SpellFrostCloak': 0x3AEA2, 'SpellLightningCloak': 0x3AEA3,
    'SpellOakflesh': 0x5AD5C, 'SpellStoneflesh': 0x5AD5D, 'SpellIronflesh': 0x51B16, 'SpellEbonyflesh': 0x5AD5E,
    'Phylactery': 0x2E504, 'FrostFX': 0xDC20D, 'SummonFX': 0x54224}
wprops = [p_obj('StyleSummoner', FID['SNE_csWarlockSummoner']), p_obj('StyleElemental', FID['SNE_csWarlockElemental']),
          p_obj('StyleArmour', FID['SNE_csWarlockArmour']), p_obj('WQ', FID['SNE_WQ']),
          p_obj('TacticsOn', FID['SNE_WarlockTactics']), p_obj('PlayerRef', PLAYER_REF), p_obj('XMarkerBase', XMARKER),
          p_obj('LightningArmour', FID['SNE_LightningArmour']), p_obj('RevivedFaction', FID['SNE_WarlockRevivedFaction'])]
wprops += [p_obj(k, v) for k, v in WARLOCK_VANILLA.items()]
# arrogance meter (2026-10-15): generic vanilla lines, DIAL/INFO at GENERIC_BASE (0xA00+), owned by SNE_WQ
gen_fids = {}
for i, g in enumerate(GENERIC):
    gen_fids.setdefault(g[1], []).append(OWN | generic_ids(i)[0])
wprops += [p_obj('WarlockFaction', 0x26724)] + [p_objs(cat, f) for cat, f in gen_fids.items() if cat.startswith('Warlock')]
wmgef = rec('MGEF', FID['SNE_WarlockBrainEffect'], [
    sub('EDID', z('SNE_WarlockBrainEffect')), vmad([script('SNE_WarlockBrain', wprops)]),
    sub('FULL', z('Warlock Tactics')), sub('DATA', bytes(MDATA)), sub('SNDD', b''), sub('DNAM', z(''))])
wspel = rec('SPEL', FID['SNE_WarlockBrain'], [
    sub('EDID', z('SNE_WarlockBrain')), sub('OBND', bytes(12)), sub('FULL', z('Warlock Tactics')),
    sub('SPIT', u32(0, 0, 4) + f32(0.0) + u32(0, 0) + f32(0.0, 0.0) + u32(0)),
    sub('EFID', u32(FID['SNE_WarlockBrainEffect'])), sub('EFIT', f32(0.0) + u32(0, 0))])
wq = rec('QUST', FID['SNE_WQ'], [
    sub('EDID', z('SNE_WQ')), qvmad([script('SNE_WarlockQuest', [
        p_obj('PlayerRef', PLAYER_REF), p_obj('RevivedFaction', FID['SNE_WarlockRevivedFaction']),
        p_obj('ReanimateFX', REANIMATE_FXS), p_obj('TacticsOn', FID['SNE_WarlockTactics'])])]),
    sub('FULL', z('Shinobi Enemies: Warlocks')),
    sub('DNAM', struct.pack('<HBBII', 0x0011, 50, 0, 0, 0)), sub('NEXT', b''), sub('ANAM', u32(0))])
wfact = rec('FACT', FID['SNE_WarlockRevivedFaction'], [sub('EDID', z('SNE_WarlockRevivedFaction')),
                                                        sub('DATA', u32(1)), sub('CRVA', bytes(20))])
glob += gl('SNE_WarlockTactics', 1.0)
# --- Falmer ---
fstyles = (
    csty('SNE_csFalmerHunter', (0.75, 0.5, 0.9, 1, 1, 1, 1, 1, 1, 0.4),
         (3.5, 3.0, 2.0, 1.5, 1.5, 1.5, 1.2, 0.5), (0.7, 0.5, 0.6, 0.4), 0.4, FLANK)    # savage: piles on staggered prey
    + csty('SNE_csFalmerBoss', (0.7, 0.6, 0.9, 1, 1, 1, 1, 1, 1, 0.2),
           (3.5, 3.5, 3.0, 3.0, 2.0, 2.5, 2.0, 0.5), (0.3, 0.1, 0.2, 0.2), 0.2, DUEL)
    # heavy armour sounds like the men they have fought for centuries: rush it, swarm it
    + csty('SNE_csFalmerRush', (1.0, 0.15, 1.0, 1, 1, 1, 1, 1, 1, 0.1),
           (4.0, 4.0, 3.5, 2.0, 2.0, 2.0, 2.0, 0.5), (0.5, 0.0, 0.5, 0.15), 0.3, FLANK))
FALMER_VANILLA = {'VanillaMagic': 0x5238B, 'VanillaMissile': 0x5238A, 'VanillaBoss': 0x52389,
                  'FalmerFaction': 0x2997E, 'ChaurusFaction': 0x3C9A8, 'SpellHealOther': 0x12FD2,
                  'SpellIronflesh': 0x51B16, 'SpellInvisibility': 0x27EB6, 'MistImod': 0xB97F7,
                  'ChaurusSummon': 0x1FA27, 'SummonFX': 0x54224, 'ArmorHeavy': 0x6BBD2,
                  'Muffle1': 0xF23CA, 'Muffle2': 0x92A57, 'Muffle3': 0x9379B, 'Muffle4': 0x8F3EA, 'Muffle5': 0xED098}
fprops = [p_obj('StyleHunter', FID['SNE_csFalmerHunter']), p_obj('StyleBoss', FID['SNE_csFalmerBoss']),
          p_obj('StyleRush', FID['SNE_csFalmerRush']), p_obj('XMarkerBase', XMARKER),
          p_obj('TacticsOn', FID['SNE_FalmerTactics']), p_obj('ScreechLock', FID['SNE_HiveScreechLock']),
          p_obj('PlayerRef', PLAYER_REF)]
fprops += [p_obj(k, v) for k, v in FALMER_VANILLA.items()]
fmgef = rec('MGEF', FID['SNE_FalmerBrainEffect'], [
    sub('EDID', z('SNE_FalmerBrainEffect')), vmad([script('SNE_FalmerBrain', fprops)]),
    sub('FULL', z('Falmer Tactics')), sub('DATA', bytes(MDATA)), sub('SNDD', b''), sub('DNAM', z(''))])
fspel = rec('SPEL', FID['SNE_FalmerBrain'], [
    sub('EDID', z('SNE_FalmerBrain')), sub('OBND', bytes(12)), sub('FULL', z('Falmer Tactics')),
    sub('SPIT', u32(0, 0, 4) + f32(0.0) + u32(0, 0) + f32(0.0, 0.0) + u32(0)),
    sub('EFID', u32(FID['SNE_FalmerBrainEffect'])), sub('EFIT', f32(0.0) + u32(0, 0))])
glob += gl('SNE_FalmerTactics', 1.0) + gl('SNE_HiveScreechLock', 0.0)
falmer_perk = rec('PERK', FID['SNE_FalmerPerk'], [
    sub('EDID', z('SNE_FalmerPerk')), sub('FULL', z('Falmer')), sub('DESC', z('')), sub('DATA', bytes([0, 0, 1, 0, 1])),
    sub('PRKE', bytes([2, 0, 0])) + sub('DATA', bytes([MOD_SPELL_MAGNITUDE, 3, 3])) + sub('EPFT', bytes([1]))
    + sub('EPFD', struct.pack('<f', 1.15)) + sub('PRKF', b'')])
# --- Forsworn ---
FSTYLES = (
    # fanatic: wild dual-wielder, darts in and circles
    csty('SNE_csForswornFanatic', (0.9, 0.2, 1.0, 1, 1, 1, 1, 1, 1, 0.1),
         (3.0, 3.0, 2.5, 1.5, 1.0, 1.2, 1.0, 0.5), (0.8, 0.3, 0.6, 0.3), 0.5, FLANK | DUAL)
    # archer: the most evasive archer - ranged first, keeps the gap, falls back a lot, strafes
    + csty('SNE_csForswornArcher', (0.45, 0.5, 0.5, 0.4, 1, 5.0, 1, 1, 1, 0.8),
           (0.42, 0.3, 0.72, 0.6, 0.6, 0.3, 0.2, 0.1), (0.6, 1.6, 0.2, 0.2), 0.8, DUEL)
    # shaman: battlemage-like, keeps some range
    + csty('SNE_csForswornShaman', (0.55, 0.55, 0.6, 0.4, 5.0, 1, 1, 1, 1, 0.6),
           (1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.1), (0.4, 0.9, 0.2, 0.2), 0.5, DUEL)
    # Briarheart: the champion - aggressive duelist, punishes blocks and staggers
    + csty('SNE_csForswornBriarheart', (0.85, 0.4, 0.9, 1, 1, 1, 1, 1, 1, 0.1),
           (4.0, 4.0, 4.0, 3.0, 2.0, 3.0, 2.0, 0.5), (0.4, 0.1, 0.4, 0.3), 0.3, DUEL | DUAL)
    # hagraven supporting: passive, stays at the back
    + csty('SNE_csHagravenSupport', (0.1, 1.0, 0.15, 0.2, 1.0, 0.5, 1, 1, 1, 1.0),
           (0.5, 0.5, 0.5, 1.0, 1.0, 0.5, 0.5, 0.1), (0.3, 1.0, 0.2, 0.2), 0.5, DUEL))
WEAPON_SPEED_AV, DETRIMENTAL = 85, 0x4
def val_mgef(name, full, av, flags=RECOVER | NO_AREA):
    d = bytearray(dict(V['regen'])['DATA'])
    struct.pack_into('<I', d, 0x00, flags)
    struct.pack_into('<Ii', d, 0x40, 0, av)       # Value Modifier
    struct.pack_into('<II', d, 0x50, 1, 0)        # Fire and Forget, Self
    return rec('MGEF', FID[name], [sub('EDID', z(name)), sub('FULL', z(full)), sub('DATA', bytes(d)),
                                   sub('SNDD', b''), sub('DNAM', z(''))])
def fspell(name, full, effects):    # effects: (mgef name, magnitude, duration)
    return rec('SPEL', FID[name], [sub('EDID', z(name)), sub('OBND', bytes(12)), sub('FULL', z(full)),
        sub('SPIT', u32(0, 0x1, 0) + f32(0.0) + u32(1, 0) + f32(0.0, 0.0) + u32(0))]
        + [s for m, mag, dur in effects for s in (sub('EFID', u32(FID[m])), sub('EFIT', f32(mag) + u32(0, dur)))])
f_mgefs = (rec('MGEF', FID['SNE_ShamanMarkEffect'], [sub('EDID', z('SNE_ShamanMarkEffect')), sub('FULL', z('Forsworn Shaman')),
                                                    sub('DATA', bytes(MARK)), sub('SNDD', b''), sub('DNAM', z(''))])
           + val_mgef('SNE_BlessSpeedEffect', "Hagraven's Blessing", WEAPON_SPEED_AV)
           + val_mgef('SNE_BlessHealthEffect', "Hagraven's Blessing", HEALTH_AV))
f_spels = rec('SPEL', FID['SNE_ShamanMark'], [
    sub('EDID', z('SNE_ShamanMark')), sub('OBND', bytes(12)), sub('FULL', z('Forsworn Shaman')),
    sub('SPIT', u32(0, 0, 4) + f32(0.0) + u32(0, 0) + f32(0.0, 0.0) + u32(0)),
    sub('EFID', u32(FID['SNE_ShamanMarkEffect'])), sub('EFIT', f32(0.0) + u32(0, 0))])
for k in range(1, 5):    # tier marker first: the script checks GetNthEffectMagicEffect(0)
    f_mgefs += val_mgef(f'SNE_BlessTier{k}Effect', "Hagraven's Blessing", DAMAGE_RESIST_AV)
    f_spels += fspell(f'SNE_BlessTier{k}', "Hagraven's Blessing", [(f'SNE_BlessTier{k}Effect', 40.0, 30),
                      ('SNE_BlessSpeedEffect', 0.08, 30), ('SNE_BlessHealthEffect', 25.0, 30)])
for k in range(1, 6):
    f_mgefs += val_mgef(f'SNE_BloodTide{k}Effect', 'Blood Magic', HEALTH_AV)
    f_spels += fspell(f'SNE_BloodTide{k}', 'Blood Magic', [(f'SNE_BloodTide{k}Effect', 30.0, 40)])
f_mgefs += (val_mgef('SNE_CurseArmourEffect', 'Curse Mark', DAMAGE_RESIST_AV) + val_mgef('SNE_CurseSpeedEffect', 'Curse Mark', WEAPON_SPEED_AV)
            + val_mgef('SNE_ExhaustMoveEffect', 'Exhausted', SPEED_AV, RECOVER | NO_AREA | DETRIMENTAL)
            + val_mgef('SNE_ExhaustSwingEffect', 'Exhausted', WEAPON_SPEED_AV, RECOVER | NO_AREA | DETRIMENTAL))
f_spels += (fspell('SNE_CurseMark', 'Curse Mark', [('SNE_CurseArmourEffect', 100.0, 12), ('SNE_CurseSpeedEffect', 0.35, 12)])
            + fspell('SNE_Exhaustion', 'Exhausted', [('SNE_ExhaustMoveEffect', 35.0, 8), ('SNE_ExhaustSwingEffect', 0.25, 8)]))
FORSWORN_FACTION, HAGRAVEN_FACTION = 0x43599, 0x4359E
f_entries = [entry_mult(MOD_SPELL_MAGNITUDE, 0.85, 0, [ctda(HAS_MAGIC_EFFECT, FID['SNE_ShamanMarkEffect'])]),
             entry_mult(MOD_INCOMING_DAMAGE, 0.8, 0, [ctda(HAS_MAGIC_EFFECT, FID['SNE_ShamanMarkEffect'])])]
f_entries += [entry_mult(MOD_ATTACK_DAMAGE, 1.19, 0, [ctda(HAS_MAGIC_EFFECT, FID[f'SNE_BlessTier{k}Effect'])]) for k in range(1, 5)]
f_entries += [entry_mult(MOD_ATTACK_DAMAGE, 1.08, 0, [ctda(HAS_MAGIC_EFFECT, FID[f'SNE_BloodTide{k}Effect'])]) for k in range(1, 6)]
f_entries += [entry_mult(MOD_ATTACK_DAMAGE, 1.5, 0, [ctda(HAS_MAGIC_EFFECT, FID['SNE_CurseArmourEffect'])])]
forsworn_perk = rec('PERK', FID['SNE_ForswornPerk'], [
    sub('EDID', z('SNE_ForswornPerk')), sub('FULL', z('Forsworn')), sub('DESC', z('')), sub('DATA', bytes([0, 0, 1, 0, 1]))]
    + f_entries)
FORSWORN_VANILLA = {'VanillaMissile': 0x442CF, 'VanillaMagic': 0x442CD, 'VanillaBossMagic': 0x442D1, 'VanillaHagraven': 0x2A54E,
                    'ForswornFaction': FORSWORN_FACTION, 'HagravenFaction': HAGRAVEN_FACTION, 'HagravenRace': 0x131FB,
                    'BriarHeart': 0x3AD61, 'CurseFX': 0xFE68C, 'ReviveFX': REANIMATE_FXS, 'MelodyImod': 0x101DAC,
                    'SpellHealOther': 0x12FD2, 'SpellCloseWounds': 0xB62EF, 'SpellOakflesh': 0x5AD5C,
                    'SpellStoneflesh': 0x5AD5D, 'SpellIronflesh': 0x51B16, 'SpellFlameCloak': 0x3AE9F,
                    'SpellFrostCloak': 0x3AEA2, 'SpellFirebolt': 0x12FD0, 'SpellFrostbite': 0x2B96B,
                    'SpellIceSpike': 0x2B96C, 'SpellFlameAtronach': 0x204C3, 'SpellFrostAtronach': 0x204C4}
foprops = [p_obj('StyleFanatic', FID['SNE_csForswornFanatic']), p_obj('StyleArcher', FID['SNE_csForswornArcher']),
           p_obj('StyleShaman', FID['SNE_csForswornShaman']), p_obj('StyleBriarheart', FID['SNE_csForswornBriarheart']),
           p_obj('StyleHagravenSupport', FID['SNE_csHagravenSupport']), p_obj('TacticsOn', FID['SNE_ForswornTactics']),
           p_obj('PlayerRef', PLAYER_REF), p_obj('XMarkerBase', XMARKER), p_obj('ShamanMark', FID['SNE_ShamanMark']),
           p_objs('Blessing', [FID[f'SNE_BlessTier{k}'] for k in range(1, 5)]),
           p_objs('BloodTide', [FID[f'SNE_BloodTide{k}'] for k in range(1, 6)]),
           p_obj('CurseMark', FID['SNE_CurseMark']), p_obj('Exhaustion', FID['SNE_Exhaustion']),
           p_obj('BurnedFaction', FID['SNE_BurnedFaction'])]
burned_fact = rec('FACT', FID['SNE_BurnedFaction'], [sub('EDID', z('SNE_BurnedFaction')), sub('DATA', u32(1)), sub('CRVA', bytes(20))])
foprops += [p_obj(k, v) for k, v in FORSWORN_VANILLA.items()]
f_mgefs += rec('MGEF', FID['SNE_ForswornBrainEffect'], [
    sub('EDID', z('SNE_ForswornBrainEffect')), vmad([script('SNE_ForswornBrain', foprops)]),
    sub('FULL', z('Forsworn Tactics')), sub('DATA', bytes(MDATA)), sub('SNDD', b''), sub('DNAM', z(''))])
f_spels += rec('SPEL', FID['SNE_ForswornBrain'], [
    sub('EDID', z('SNE_ForswornBrain')), sub('OBND', bytes(12)), sub('FULL', z('Forsworn Tactics')),
    sub('SPIT', u32(0, 0, 4) + f32(0.0) + u32(0, 0) + f32(0.0, 0.0) + u32(0)),
    sub('EFID', u32(FID['SNE_ForswornBrainEffect'])), sub('EFIT', f32(0.0) + u32(0, 0))])
glob += gl('SNE_ForswornTactics', 1.0)
# --- Dwemer automatons ---
DSTYLES = (
    csty('SNE_csSpiderSwarm', (0.95, 0.1, 1.0, 1, 1, 1, 1, 1, 1, 0.0),
         (3.0, 3.5, 2.5, 1.5, 1.5, 1.5, 1.2, 0.3), (0.8, 0.0, 0.3, 0.1), 0.5, FLANK)
    + csty('SNE_csSpiderSupport', (0.2, 0.9, 0.2, 1, 1, 1, 1, 1, 1, 0.9),
           (1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.1), (0.3, 1.0, 0.2, 0.2), 0.5, DUEL)
    + csty('SNE_csSphereGuard', (0.45, 0.8, 0.6, 1, 1, 1, 1, 1, 1, 0.2),
           (1.5, 2.0, 1.5, 3.0, 3.0, 2.5, 2.0, 0.3), (0.2, 0.1, 0.2, 0.2), 0.2, DUEL)
    + csty('SNE_csSphereLinked', (0.65, 0.6, 0.9, 1, 1, 1, 1, 1, 1, 0.1),
           (2.5, 3.0, 2.0, 2.5, 2.5, 2.0, 1.5, 0.3), (0.5, 0.2, 0.5, 0.3), 0.4, FLANK)
    + csty('SNE_csCenturionLinked', (0.8, 0.4, 1.0, 1, 1, 1, 1, 1, 1, 0.0),
           (3.5, 3.5, 3.0, 2.0, 2.0, 2.0, 2.0, 0.5), (0.4, 0.1, 0.4, 0.2), 0.2, FLANK))
d_mgefs = b''; d_spels = b''
for k in range(1, 5):
    d_mgefs += val_mgef(f'SNE_Link{k}Effect', 'Master Link', DAMAGE_RESIST_AV)
    d_spels += fspell(f'SNE_Link{k}', 'Master Link', [(f'SNE_Link{k}Effect', 15.0, 5)])
d_mgefs += (val_mgef('SNE_OverdriveEffect', 'Overdrive', WEAPON_SPEED_AV) + val_mgef('SNE_OverdriveMoveEffect', 'Overdrive', SPEED_AV)
            + val_mgef('SNE_OverheatEffect', 'Overheated', DAMAGE_RESIST_AV, RECOVER | NO_AREA | DETRIMENTAL))
d_spels += (fspell('SNE_Overdrive', 'Overdrive', [('SNE_OverdriveEffect', 0.3, 12), ('SNE_OverdriveMoveEffect', 20.0, 12)])
            + fspell('SNE_Overheat', 'Overheated', [('SNE_OverheatEffect', 50.0, 5)]))
KW = {'Sword': 0x1E711, 'Dagger': 0x1E713, 'WarAxe': 0x1E712, 'Greatsword': 0x6D931, 'Battleaxe': 0x6D932,
      'Mace': 0x1E714, 'Warhammer': 0x6D930}
HAS_KEYWORD = 560
d_entries = [entry_mult(MOD_INCOMING_DAMAGE, 0.9, 0, [ctda(HAS_MAGIC_EFFECT, FID[f'SNE_Link{k}Effect'])]) for k in range(1, 5)]
d_entries += [entry_mult(MOD_INCOMING_DAMAGE, 0.7, 2, [ctda(HAS_KEYWORD, KW[w])]) for w in ('Sword', 'Dagger', 'WarAxe', 'Greatsword', 'Battleaxe')]
d_entries += [entry_mult(MOD_INCOMING_DAMAGE, 1.25, 2, [ctda(HAS_KEYWORD, KW[w])]) for w in ('Mace', 'Warhammer')]
d_entries += [entry_mult(MOD_ATTACK_DAMAGE, 1.4, 0, [ctda(HAS_MAGIC_EFFECT, FID['SNE_OverdriveEffect'])]),
              entry_mult(MOD_INCOMING_DAMAGE, 1.5, 0, [ctda(HAS_MAGIC_EFFECT, FID['SNE_OverheatEffect'])])]
dwemer_perk = rec('PERK', FID['SNE_DwemerPerk'], [
    sub('EDID', z('SNE_DwemerPerk')), sub('FULL', z('Dwemer Automaton')), sub('DESC', z('')), sub('DATA', bytes([0, 0, 1, 0, 1]))]
    + d_entries)
DWEMER_VANILLA = {'AutomatonFaction': 0x43598, 'SpiderRace': 0x131F3, 'SphereRace': 0x131F2, 'CenturionRace': 0x131F1,
                  'LocDwarven': 0x130E3, 'LvlSpider': 0x10EC90, 'SpiderBlast': 0xF9B0B, 'ShockFX': 0x57C67,
                  'SteamFX': 0x10FDF9}
dwprops = [p_obj('StyleSpiderSwarm', FID['SNE_csSpiderSwarm']), p_obj('StyleSpiderSupport', FID['SNE_csSpiderSupport']),
           p_obj('StyleSphereGuard', FID['SNE_csSphereGuard']), p_obj('StyleSphereLinked', FID['SNE_csSphereLinked']),
           p_obj('StyleCenturionLinked', FID['SNE_csCenturionLinked']), p_obj('TacticsOn', FID['SNE_DwemerTactics']),
           p_obj('AlarmLock', FID['SNE_DwemerAlarmLock']), p_obj('ReinforcedCells', FID['SNE_DwemerReinforced']),
           p_obj('PlayerRef', PLAYER_REF), p_objs('Link', [FID[f'SNE_Link{k}'] for k in range(1, 5)]),
           p_obj('Overdrive', FID['SNE_Overdrive']), p_obj('Overheat', FID['SNE_Overheat'])]
dwprops += [p_obj(k, v) for k, v in DWEMER_VANILLA.items()]
d_mgefs += rec('MGEF', FID['SNE_DwemerBrainEffect'], [
    sub('EDID', z('SNE_DwemerBrainEffect')), vmad([script('SNE_DwemerBrain', dwprops)]),
    sub('FULL', z('Dwemer Tactics')), sub('DATA', bytes(MDATA)), sub('SNDD', b''), sub('DNAM', z(''))])
d_spels += rec('SPEL', FID['SNE_DwemerBrain'], [
    sub('EDID', z('SNE_DwemerBrain')), sub('OBND', bytes(12)), sub('FULL', z('Dwemer Tactics')),
    sub('SPIT', u32(0, 0, 4) + f32(0.0) + u32(0, 0) + f32(0.0, 0.0) + u32(0)),
    sub('EFID', u32(FID['SNE_DwemerBrainEffect'])), sub('EFIT', f32(0.0) + u32(0, 0))])
glob += gl('SNE_DwemerTactics', 1.0) + gl('SNE_DwemerAlarmLock', 0.0)
dwemer_flst = rec('FLST', FID['SNE_DwemerReinforced'], [sub('EDID', z('SNE_DwemerReinforced'))])
# --- Thalmor ---
TSTYLES = (
    # contempt: individualist, unguarded, never flanks
    csty('SNE_csThalmorContempt', (0.8, 0.15, 0.4, 1, 1, 1, 1, 1, 1, 0.0),
         (1.5, 1.5, 2.0, 1.0, 1.0, 1.0, 1.0, 0.3), (0.2, 0.0, 0.2, 0.2), 0.1, DUEL)
    # serious soldier: Great War discipline - guarded line that punishes openings and works the flanks
    + csty('SNE_csThalmorSoldier', (0.6, 0.6, 0.9, 1, 1, 1, 1, 1, 1, 0.2),
           (3.5, 3.5, 3.0, 3.0, 2.5, 3.0, 2.5, 0.5), (0.4, 0.3, 0.4, 0.4), 0.4, DUEL | FLANK | DUAL)
    + csty('SNE_csThalmorArcher', (0.45, 0.5, 0.6, 0.4, 1, 5.0, 1, 1, 1, 0.7),
           (0.42, 0.3, 0.72, 0.6, 0.6, 0.3, 0.2, 0.1), (0.6, 1.4, 0.5, 0.3), 0.7, DUEL | FLANK)
    + csty('SNE_csJusticiar', (0.6, 0.5, 0.7, 0.4, 5.0, 1, 1, 1, 1, 0.7),
           (1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.1), (0.4, 1.0, 0.2, 0.2), 0.6, DUEL)
    + csty('SNE_csJusticiarContempt', (0.5, 0.1, 0.3, 0.6, 4.0, 1, 1, 1, 1, 0.0),
           (1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.1), (0.1, 0.0, 0.2, 0.2), 0.1, DUEL))
MAGIC_RESIST_AV, MAGICKA_RATE_AV = 44, 28
t_mgefs = (val_mgef('SNE_ThalmorWardEffect', 'Thalmor Ward', MAGIC_RESIST_AV)
           + val_mgef('SNE_SilencingSealEffect', 'Silencing Seal', MAGICKA_RATE_AV, RECOVER | NO_AREA | DETRIMENTAL))
t_spels = (fspell('SNE_ThalmorWard', 'Thalmor Ward', [('SNE_ThalmorWardEffect', 40.0, 6)])
           + fspell('SNE_SilencingSeal', 'Silencing Seal', [('SNE_SilencingSealEffect', 100.0, 6)]))
haughty = rec('FLST', FID['SNE_HaughtyVoices'], [sub('EDID', z('SNE_HaughtyVoices')), sub('LNAM', u32(0x13AF0)), sub('LNAM', u32(0x13AF1))])
THALMOR_VANILLA = {'ThalmorFaction': 0x39F26, 'ClassWizard': 0x72887, 'ClassMissile': 0x72891, 'HighElfRace': 0x13743,
                   'TalosAmulet': 0xCC846, 'TalosAmulet2': 0x64796, 'TalosBlessing': 0xFB99A, 'SpellFus': 0x13E09,
                   'SpellHealOther': 0x12FD2, 'SpellStoneflesh': 0x5AD5D, 'SpellEbonyflesh': 0x5AD5E, 'WardFX': 0x1C858}
tprops = [p_obj('StyleContempt', FID['SNE_csThalmorContempt']), p_obj('StyleSoldier', FID['SNE_csThalmorSoldier']),
          p_obj('StyleArcher', FID['SNE_csThalmorArcher']), p_obj('StyleJusticiar', FID['SNE_csJusticiar']),
          p_obj('StyleJusticiarContempt', FID['SNE_csJusticiarContempt']), p_obj('TacticsOn', FID['SNE_ThalmorTactics']),
          p_obj('IntelMelee', FID['SNE_ThalmorIntelMelee']), p_obj('IntelMagic', FID['SNE_ThalmorIntelMagic']),
          p_obj('IntelTime', FID['SNE_ThalmorIntelTime']), p_obj('VoiceLock', FID['SNE_ThalmorVoiceLock']),
          p_obj('PlayerRef', PLAYER_REF), p_obj('HaughtyVoices', FID['SNE_HaughtyVoices']),
          p_obj('ThalmorWard', FID['SNE_ThalmorWard']), p_obj('SilencingSeal', FID['SNE_SilencingSeal']),
          p_obj('SealingChains', FID['SNE_ParalyzeShort'])]
tprops += [p_obj(k, v) for k, v in THALMOR_VANILLA.items()]
tprops += [p_objs(c, [OWN | generic_ids(i)[0] for i, g in enumerate(GENERIC) if g[1] == c])
           for c in ('ThalContempt', 'ThalFlea', 'ThalSerious', 'ThalPanic', 'ThalHeretic')]
t_mgefs += rec('MGEF', FID['SNE_ThalmorBrainEffect'], [
    sub('EDID', z('SNE_ThalmorBrainEffect')), vmad([script('SNE_ThalmorBrain', tprops)]),
    sub('FULL', z('Thalmor Tactics')), sub('DATA', bytes(MDATA)), sub('SNDD', b''), sub('DNAM', z(''))])
t_spels += rec('SPEL', FID['SNE_ThalmorBrain'], [
    sub('EDID', z('SNE_ThalmorBrain')), sub('OBND', bytes(12)), sub('FULL', z('Thalmor Tactics')),
    sub('SPIT', u32(0, 0, 4) + f32(0.0) + u32(0, 0) + f32(0.0, 0.0) + u32(0)),
    sub('EFID', u32(FID['SNE_ThalmorBrainEffect'])), sub('EFIT', f32(0.0) + u32(0, 0))])
# --- Imperial Legion ---
LSTYLES = (
    # shield line: guarded, blocks, bashes, holds its place
    csty('SNE_csLegionLine', (0.45, 0.85, 0.8, 1, 1, 1, 1, 1, 1, 0.1),
         (2.0, 2.5, 1.5, 3.5, 3.5, 3.0, 2.5, 0.3), (0.1, 0.1, 0.2, 0.3), 0.2, DUEL)
    + csty('SNE_csLegionSoldier', (0.6, 0.65, 0.9, 1, 1, 1, 1, 1, 1, 0.15),
           (2.5, 3.0, 2.0, 2.5, 2.5, 2.0, 2.0, 0.4), (0.3, 0.2, 0.4, 0.4), 0.4, DUEL | FLANK | DUAL)
    + csty('SNE_csLegionArcher', (0.4, 0.6, 0.6, 0.4, 1, 4.5, 1, 1, 1, 0.7),
           (0.42, 0.3, 0.72, 0.6, 0.6, 0.3, 0.2, 0.1), (0.5, 1.2, 0.3, 0.3), 0.6, DUEL)
    + csty('SNE_csLegionMage', (0.4, 0.7, 0.5, 0.3, 4.0, 1, 1, 1, 1, 0.8),
           (1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.1), (0.3, 1.0, 0.2, 0.2), 0.5, DUEL)
    # adapted to archers or casters: shields up and close the distance
    + csty('SNE_csLegionPress', (0.8, 0.5, 1.0, 1, 1, 1, 1, 1, 1, 0.0),
           (2.5, 3.0, 2.5, 2.0, 2.0, 2.0, 1.5, 0.3), (0.2, 0.0, 0.6, 0.1), 0.5, FLANK | DUEL))
BLOCK_AV = 9
l_mgefs = (val_mgef('SNE_FormationBlockEffect', 'Formation', BLOCK_AV) + val_mgef('SNE_FormationArmourEffect', 'Formation', DAMAGE_RESIST_AV)
           + val_mgef('SNE_AdaptPowerEffect', 'Adapted: power attacks', DAMAGE_RESIST_AV)
           + val_mgef('SNE_AdaptMagicEffect', 'Adapted: magic', MAGIC_RESIST_AV)
           + val_mgef('SNE_AdaptRangedEffect', 'Adapted: archery', BLOCK_AV)
           + val_mgef('SNE_AdaptMeleeEffect', 'Adapted: melee', DAMAGE_RESIST_AV)
           + val_mgef('SNE_LegionWardEffect', 'Legion Ward', MAGIC_RESIST_AV))
l_spels = (fspell('SNE_Formation', 'Formation', [('SNE_FormationBlockEffect', 25.0, 4), ('SNE_FormationArmourEffect', 25.0, 4)])
           + fspell('SNE_AdaptPower', 'Adapted: power attacks', [('SNE_AdaptPowerEffect', 40.0, 4)])
           + fspell('SNE_AdaptMagic', 'Adapted: magic', [('SNE_AdaptMagicEffect', 30.0, 4)])
           + fspell('SNE_AdaptRanged', 'Adapted: archery', [('SNE_AdaptRangedEffect', 20.0, 4)])
           + fspell('SNE_AdaptMelee', 'Adapted: melee', [('SNE_AdaptMeleeEffect', 30.0, 4)])
           + fspell('SNE_LegionWard', 'Legion Ward', [('SNE_LegionWardEffect', 35.0, 8)]))
def entry_mult_tabs(ep, value, tabs):    # tabs: [(tab, [ctda...]), ...] - all conditions must hold
    out = sub('PRKE', bytes([2, 0, 0])) + sub('DATA', bytes([ep, 3, 3]))
    for tab, conds in tabs:
        out += sub('PRKC', bytes([tab])) + b''.join(conds)
    return out + sub('EPFT', bytes([1])) + sub('EPFD', struct.pack('<f', value)) + sub('PRKF', b'')
legion_perk = rec('PERK', FID['SNE_LegionPerk'], [
    sub('EDID', z('SNE_LegionPerk')), sub('FULL', z('Imperial Legion')), sub('DESC', z('')), sub('DATA', bytes([0, 0, 1, 0, 1])),
    entry_mult(MOD_INCOMING_DAMAGE, 0.9, 0, [ctda(HAS_MAGIC_EFFECT, FID['SNE_FormationArmourEffect'])]),
    entry_mult_tabs(MOD_ATTACK_DAMAGE, 2.0, [(0, [ctda(HAS_MAGIC_EFFECT, FID['SNE_JoninMarkEffect'])]),
                                             (1, [ctda(HAS_KEYWORD, 0x1E713)])]),    # Leaf Jonin kunai (WeapTypeDagger) x2
    entry_mult_tabs(MOD_INCOMING_DAMAGE, 0.8, [(0, [ctda(HAS_MAGIC_EFFECT, FID['SNE_AdaptRangedEffect'])]),
                                               (2, [ctda(HAS_KEYWORD, 0x1E715)])])])    # WeapTypeBow
LEGION_VANILLA = {'VanillaMagic': 0x46B9E, 'VanillaMissile': 0x46B9D, 'VanillaCWMissile': 0xD3A0E,
                  'LegionFaction': 0x2BF9A, 'OculatusFaction': 0x2584B, 'FieldCOFaction': 0xC4A99, 'ThalmorFaction': 0x39F26,
                  'SpellHealOther': 0x12FD2, 'SpellCloseWounds': 0xB62EF, 'SpellOakflesh': 0x5AD5C,
                  'SpellStoneflesh': 0x5AD5D, 'SpellIronflesh': 0x51B16}
# --- Leaf ninja ---
LSTYLES += (
    # jonin: quick and agile rogue - in, out, round the flanks; light armour so it relies on dodging
    csty('SNE_csLeafJonin', (0.85, 0.3, 0.95, 1, 1, 1, 1, 1, 1, 0.15),
         (2.5, 3.5, 2.0, 1.5, 1.5, 1.5, 1.2, 0.5), (0.9, 0.6, 0.7, 0.5), 0.8, FLANK | DUEL | DUAL)
    # medic: Tsunade's rules - stay out of reach
    + csty('SNE_csLeafMedic', (0.15, 1.0, 0.2, 0.3, 1.0, 0.5, 1, 1, 1, 1.0),
           (0.5, 0.5, 0.5, 1.0, 1.0, 0.5, 0.5, 0.1), (0.5, 1.2, 0.2, 0.2), 0.8, DUEL))
leaf_mgefs = (val_mgef('SNE_HundredArmourEffect', 'Strength of a Hundred Seal', DAMAGE_RESIST_AV)
              + val_mgef('SNE_HundredSpeedEffect', 'Strength of a Hundred Seal', WEAPON_SPEED_AV))
leaf_spels = fspell('SNE_StrengthOfHundred', 'Strength of a Hundred Seal', [('SNE_HundredArmourEffect', 100.0, 20), ('SNE_HundredSpeedEffect', 0.3, 20)])
leaf_otft = (rec('OTFT', FID['SNE_LeafMedicOutfit'], [sub('EDID', z('SNE_LeafMedicOutfit')), sub('INAM', u32(0x10CFF1, 0xD3EA7))])
             + rec('OTFT', FID['SNE_LeafEmptyOutfit'], [sub('EDID', z('SNE_LeafEmptyOutfit'))]))
leafprops = [p_obj('TacticsOn', FID['SNE_LegionTactics']), p_obj('PlayerRef', PLAYER_REF),
             p_obj('LegionFaction', 0x2BF9A), p_obj('OculatusFaction', 0x2584B),
             p_obj('JoninOutfit', 0xD5EB5), p_obj('MedicOutfit', FID['SNE_LeafMedicOutfit']),
             p_obj('EmptyOutfit', FID['SNE_LeafEmptyOutfit']), p_obj('StyleJonin', FID['SNE_csLeafJonin']),
             p_obj('StyleMedic', FID['SNE_csLeafMedic']), p_obj('SpellIronflesh', 0x51B16),
             p_obj('Exhaustion', FID['SNE_Exhaustion']), p_obj('StrengthOfHundred', FID['SNE_StrengthOfHundred']),
             p_obj('HealFX', 0x4E220), p_obj('ShockFX', 0x57C67), p_obj('ChakraFX', 0xABF08),
             p_obj('TagBlast', 0x73327), p_obj('LogItem', 0x6F993), p_obj('XMarkerBase', XMARKER),
             p_obj('JoninMark', FID['SNE_JoninMark']), p_obj('SpellLightning', 0x2DD29), p_obj('SpellChainLightning', 0x45F9D),
             p_obj('SpellIceSpike', 0x2B96C), p_obj('SpellFus', 0x13E09)]
leaf_mgefs += rec('MGEF', FID['SNE_LeafNinjaEffect'], [
    sub('EDID', z('SNE_LeafNinjaEffect')), vmad([script('SNE_LeafNinja', leafprops)]),
    sub('FULL', z('Leaf Ninja')), sub('DATA', bytes(MDATA)), sub('SNDD', b''), sub('DNAM', z(''))])
leaf_spels += rec('SPEL', FID['SNE_LeafNinja'], [
    sub('EDID', z('SNE_LeafNinja')), sub('OBND', bytes(12)), sub('FULL', z('Leaf Ninja')),
    sub('SPIT', u32(0, 0, 4) + f32(0.0) + u32(0, 0) + f32(0.0, 0.0) + u32(0)),
    sub('EFID', u32(FID['SNE_LeafNinjaEffect'])), sub('EFIT', f32(0.0) + u32(0, 0))])
leaf_mgefs += rec('MGEF', FID['SNE_JoninMarkEffect'], [sub('EDID', z('SNE_JoninMarkEffect')), sub('FULL', z('Leaf Jonin')),
                                                       sub('DATA', bytes(MARK)), sub('SNDD', b''), sub('DNAM', z(''))])
leaf_spels += rec('SPEL', FID['SNE_JoninMark'], [
    sub('EDID', z('SNE_JoninMark')), sub('OBND', bytes(12)), sub('FULL', z('Leaf Jonin')),
    sub('SPIT', u32(0, 0, 4) + f32(0.0) + u32(0, 0) + f32(0.0, 0.0) + u32(0)),
    sub('EFID', u32(FID['SNE_JoninMarkEffect'])), sub('EFIT', f32(0.0) + u32(0, 0))])
l_mgefs += leaf_mgefs
l_spels += leaf_spels
lprops = [p_obj('LeafAbility', FID['SNE_LeafNinja']), p_obj('StyleLine', FID['SNE_csLegionLine']), p_obj('StyleSoldier', FID['SNE_csLegionSoldier']),
          p_obj('StyleArcher', FID['SNE_csLegionArcher']), p_obj('StyleMage', FID['SNE_csLegionMage']),
          p_obj('StylePress', FID['SNE_csLegionPress']), p_obj('TacticsOn', FID['SNE_LegionTactics']),
          p_obj('IntelPower', FID['SNE_LegionIntelPower']), p_obj('IntelMagic', FID['SNE_LegionIntelMagic']),
          p_obj('IntelRanged', FID['SNE_LegionIntelRanged']), p_obj('IntelMelee', FID['SNE_LegionIntelMelee']),
          p_obj('IntelTime', FID['SNE_LegionIntelTime']), p_obj('Adapt', FID['SNE_LegionAdapt']),
          p_obj('PlayerRef', PLAYER_REF), p_obj('Formation', FID['SNE_Formation']),
          p_obj('AdaptPower', FID['SNE_AdaptPower']), p_obj('AdaptMagic', FID['SNE_AdaptMagic']),
          p_obj('AdaptRanged', FID['SNE_AdaptRanged']), p_obj('AdaptMelee', FID['SNE_AdaptMelee']),
          p_obj('LegionWard', FID['SNE_LegionWard'])]
lprops += [p_obj(k, v) for k, v in LEGION_VANILLA.items()]
l_mgefs += rec('MGEF', FID['SNE_LegionBrainEffect'], [
    sub('EDID', z('SNE_LegionBrainEffect')), vmad([script('SNE_LegionBrain', lprops)]),
    sub('FULL', z('Legion Tactics')), sub('DATA', bytes(MDATA)), sub('SNDD', b''), sub('DNAM', z(''))])
l_spels += rec('SPEL', FID['SNE_LegionBrain'], [
    sub('EDID', z('SNE_LegionBrain')), sub('OBND', bytes(12)), sub('FULL', z('Legion Tactics')),
    sub('SPIT', u32(0, 0, 4) + f32(0.0) + u32(0, 0) + f32(0.0, 0.0) + u32(0)),
    sub('EFID', u32(FID['SNE_LegionBrainEffect'])), sub('EFIT', f32(0.0) + u32(0, 0))])
glob += (gl('SNE_LegionTactics', 1.0) + gl('SNE_LegionIntelPower', 0.0) + gl('SNE_LegionIntelMagic', 0.0)
         + gl('SNE_LegionIntelRanged', 0.0) + gl('SNE_LegionIntelMelee', 0.0) + gl('SNE_LegionIntelTime', 0.0)
         + gl('SNE_LegionAdapt', 0.0))
glob += (gl('SNE_ThalmorTactics', 1.0) + gl('SNE_ThalmorIntelMelee', 0.0) + gl('SNE_ThalmorIntelMagic', 0.0)
         + gl('SNE_ThalmorIntelTime', 0.0) + gl('SNE_ThalmorVoiceLock', 0.0))
for i, (topic, cat, src_id, emo, text) in enumerate(GENERIC):
    d, n = generic_ids(i)
    dial = rec('DIAL', OWN | d, [sub('EDID', z(topic)), sub('PNAM', f32(50.0)), sub('QNAM', u32(FID['SNE_WQ'])),
                                 sub('DATA', bytes(4)), sub('SNAM', b'CUST'), sub('TIFC', u32(1))])
    info = rec('INFO', OWN | n, [
        sub('ENAM', struct.pack('<HH', 0, 0)), sub('PNAM', u32(0)), sub('CNAM', bytes(1)),
        sub('TRDT', struct.pack('<II4sB3sIB3s', emo, 50, bytes(4), 1, bytes(3), 0, 0, bytes(3))),
        sub('NAM1', z(text)), sub('NAM2', bytes(1)), sub('NAM3', bytes(1))])
    dials += dial + child_grup(OWN | d, info)
ALL_IDS = [v & 0xFFFFFF for v in FID.values()] + [line_ids(len(LINES) - 1)[1], generic_ids(len(GENERIC) - 1)[1]]

groups = (grup('KYWD', kywds) + grup('GLOB', glob) + grup('FACT', dfact + wfact + burned_fact) + grup('CSTY', styles + vstyles + dstyles + wstyles + fstyles + FSTYLES + DSTYLES + TSTYLES + LSTYLES)
          + grup('OTFT', leaf_otft) + grup('FLST', flst + mylady + dwemer_flst + haughty)
          + grup('MGEF', mgef + mage_mgef + vmgef + blood_mgefs + ashe_resist + ashe_shut + dmgef + la_mgefs + wmgef + fmgef + f_mgefs + d_mgefs + t_mgefs + l_mgefs)
          + grup('SPEL', spel + mage_spel + paralyze_short + vspel + blood_spel + ashe_spel + dspel + la_spel + wspel + fspel + f_spels + d_spels + t_spels + l_spels) + grup('PERK', bandit_perk + falmer_perk + draugr_perk + forsworn_perk + dwemer_perk + legion_perk)
          + grup('QUST', cq + dq + wq) + grup('DIAL', dials))
hdr = [sub('HEDR', f32(1.7) + u32(len(FID) + 2 * (len(LINES) + len(GENERIC)) + 8, max(ALL_IDS) + 1)), sub('CNAM', z('Claude')),
       sub('SNAM', z('Shinobi Enemies: faction tactics for enemies')), sub('MAST', z('Skyrim.esm')), sub('DATA', bytes(8))]
open(OUT, 'wb').write(rec('TES4', 0, hdr, flags=0x200) + groups)
print('wrote', OUT)
for k, v in FID.items(): print(f'  {v:08X} {k}')
