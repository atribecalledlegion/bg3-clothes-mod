"""Serana Ninja Mode: Serana-only copies of the "Shinobi Normal and Power For MCO" sword moveset, one per tier,
with her jutsu added to the clips as Payload Interpreter casts, plus the ini that maps them per tier.

Usage: make_oar.py <Shinobi mod folder> <out mod folder>

The Shinobi clips are a player-only DAR set (one-handed sword or greatsword). Each copy here is an OAR folder for
Serana (Dawnguard 0x2B6C) with a one-handed sword (her Kusanagi) and the tier's hidden effect (Serana Ninja
Mode.esp 0x806-0x80A, given by the toggle script). Priorities 2147483001-005 beat Daughter of Coldharbour
(97000000), which otherwise owns her sword animations, and everything else. The clips keep their own $Shinobi
payloads (short invisibility flashes on the dashes, ShinobiEffects.esp).

Her jutsu (lightning first, like Sasuke; frost where an Uchiha would use fire; fire stays her weakness) are
appended as 'PIE.$NJ<tier><slot>' annotations at the strike frames (tools/hkanno.py). The Chidori kit lives in
Serana Ninja Mode.esp (fire-and-forget copies of Naruto Overhaul's Chidori effects, 2026-10-17):
  c   power attack 1, at the start: Chidori charge (her body crackles)
  p1  power attack 1, the hit:  Chidori (the thrust; heavy shock + stagger)
  k   light attacks 1-5, on the hit: Chidori Katana arcs (one tomoe and up)
  p2  power attack 2:           Hyoton (frost, her Gokakyu)
  p3  power attack 3, 2nd hit:  Chidori Nagashi (Naruto Overhaul's own burst)
  p4  power attack 4, 2nd hit:  Chidori Eiso (lightning spear; lightning bolt before two tomoe)
  p5  power attack 5, x4:       Chidori Senbon (needle volley; sparks before two tomoe)
  p6  power attack 6 (long):    Kirin from three tomoe (SNJ_KirinCallSpell: needs her Hyoton clouds or a storm),
                                Eiso twice at two tomoe, chain lightning before
  p7  power attack 7, 2nd hit:  Hyoton storm (seeds the clouds for Kirin)
  s   attack 6 (6-hit flurry), last hit: Chidori Nagashi (two tomoe and up)
"""
import json, os, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hkanno

SRC, OUT = sys.argv[1], sys.argv[2]
DAR = os.path.join(SRC, 'meshes', 'actors', 'character', 'animations', 'DynamicAnimationReplacer', '_CustomConditions', '31117035')
# her standing stance (user, 2026-10-17): cool and reserved like Sasuke, blade low and loose in one hand; the ER Katana
# one-handed: MCO Elden Ring FlamingStrike (ER Katana was two-handed; Tobirama too coiled)
STANCE_IDLE = os.path.join(os.path.dirname(os.path.normpath(SRC)), 'MCO Elden Ring FlamingStrike', 'meshes', 'actors',
                           'character', 'animations', 'DynamicAnimationReplacer', '_CustomConditions', '95333334', '1hm_idle.hkx')
TOBIRAMA_DIR = os.path.join(os.path.dirname(os.path.normpath(SRC)), 'ADXP-MCO Inspired by Tobirama in Naruto dagger animation',
                            'meshes', 'actors', 'character', 'animations', 'DynamicAnimationReplacer', '_CustomConditions', '822888888')
OAR = os.path.join(OUT, 'meshes', 'actors', 'character', 'animations', 'OpenAnimationReplacer', 'Serana Ninja Mode')
ESP = 'Serana Ninja Mode.esp'
TIER_MGEF = {1: 0x806, 2: 0x807, 3: 0x808, 4: 0x809, 5: 0x80A}
TIER_NAMES = {1: 'Genin', 2: 'One Tomoe', 3: 'Two Tomoe', 4: 'Three Tomoe', 5: 'Awakened'}

# clip -> [(time, slot)]; times are the clips' own HitFrames
CASTS = {
    'mco_attack1.hkx': [(0.550, 'k')], 'mco_attack2.hkx': [(0.267, 'k')], 'mco_attack3.hkx': [(0.200, 'k')],
    'mco_attack4.hkx': [(0.767, 'k')], 'mco_attack5.hkx': [(0.750, 'k')],
    'mco_attack6.hkx': [(2.810, 's')],
    'mco_powerattack1.hkx': [(0.070, 'c'), (0.430, 'p1')], 'mco_powerattack2.hkx': [(0.555, 'p2')],
    'mco_powerattack3.hkx': [(0.767, 'p3')], 'mco_powerattack4.hkx': [(1.083, 'p4')],
    'mco_powerattack5.hkx': [(0.700, 'p5'), (0.760, 'p5'), (0.820, 'p5'), (0.880, 'p5')], 'mco_powerattack6.hkx': [(1.200, 'p6'), (2.400, 'p6')],
    'mco_powerattack7.hkx': [(1.500, 'p7')],
}

SK, NO, ME = 'Skyrim.esm', 'naruto overhaul.esp', 'Serana Ninja Mode.esp'
LIGHTNING_BOLT = (0x02DD29, SK, 'Lightning Bolt')
CHAIN_LIGHTNING = (0x045F9D, SK, 'Chain Lightning')
ICE_SPIKE = (0x02B96C, SK, 'Ice Spike')
ICY_SPEAR = (0x10F7EC, SK, 'Icy Spear')
ICE_STORM = (0x045F9C, SK, 'Ice Storm')
BLIZZARD = (0x07E8E4, SK, 'Blizzard')
# her own Chidori Nagashi (Serana Ninja Mode.esp 0x81F): Naruto Overhaul's look and damage without the 128-force push
# that likely crashed Havok in a ruin full of automaton ragdolls (2026-10-18); its strength scales with the tier power
NAGASHI_SPELL = (0x81F, 'Serana Ninja Mode.esp', 'Chidori Nagashi (no push)')
CHARGE = (0x816, ME, 'Chidori charge')
CHIDORI = (0x817, ME, 'Chidori')
KATANA = (0x818, ME, 'Chidori Katana')
EISO = (0x819, ME, 'Chidori Eiso')
SENBON = (0x81A, ME, 'Chidori Senbon')
KIRIN_CALL = (0x81C, ME, 'Kirin (needs her Hyoton clouds or a storm, outdoors)')

# tiers: 1 Genin, 2 one tomoe, 3 two tomoe, 4 three tomoe, 5 awakened
# slot -> (spell, magicka cost, effectiveness multiplier on top of the tier's power, cast on self); None = no cast
def tier_slots(t):
    # 2026-10-17 costs cut by about a third: the mode leans on her Sharingan and jutsu, she must not gas out
    nag = NAGASHI_SPELL
    return {
        'c':  (CHARGE, 0, 1.0, True),
        'p1': (CHIDORI, 20, 1.0, False),
        'k':  (KATANA, 0, 1.0, False) if t >= 2 else None,
        'p2': (ICE_SPIKE if t < 3 else ICY_SPEAR, 15, 1.0, False),
        'p3': (nag, 25, 1.0, False),
        'p4': (EISO, 25, 1.0, False) if t >= 3 else (LIGHTNING_BOLT, 20, 1.0, False),
        'p5': (SENBON, 6, 1.0, False) if t >= 3 else (LIGHTNING_BOLT, 5, 0.3, False),
        'p6': (KIRIN_CALL, 45, 1.0, True) if t >= 4 else ((EISO, 30, 1.2, False) if t == 3 else (CHAIN_LIGHTNING, 35, 1.2, False)),
        'p7': (ICE_STORM if t < 5 else BLIZZARD, 40, 1.0, False),
        's':  (nag, 15, 1.0, False) if t >= 3 else None,
    }
POWER = {1: 1.0, 2: 1.25, 3: 1.5, 4: 1.8, 5: 2.2}



def conditions(tier):
    return [
        {'condition': 'IsActorBase', 'requiredVersion': '1.0.0.0',
         'Actor base': {'pluginName': 'Dawnguard.esm', 'formID': '2B6C'}},
        {'condition': 'IsEquippedType', 'requiredVersion': '1.0.0.0', 'Type': {'value': 1.0}, 'Left hand': False},
        {'condition': 'HasMagicEffect', 'requiredVersion': '1.0.0.0', 'negated': False,
         'Magic effect': {'pluginName': ESP, 'formID': '%X' % TIER_MGEF[tier]}},
    ]


def main():
    clips = [f for f in os.listdir(DAR) if f.lower().endswith('.hkx')]
    assert 'mco_attack1.hkx' in clips, clips
    if os.path.isdir(OAR):
        shutil.rmtree(OAR)
    os.makedirs(OAR)
    json.dump({'name': 'Serana Ninja Mode', 'description': "Serana's kenjutsu and jutsu, one folder per tier",
               'author': 'Claude'}, open(os.path.join(OAR, 'config.json'), 'w'), indent=2)
    ini = ['; Serana Ninja Mode: her jutsu by tier (generated by tools/make_oar.py).',
           '; @CAST|spell|plugin|effectiveness|magnitude|self|HealthReq|HealthCost|StaminaReq|StaminaCost|MagickaReq|MagickaCost',
           '; A jutsu that will not cast for her can be swapped here: edit the form id and plugin, then reload the game.', '']
    for tier in range(1, 6):
        prio = 2147483000 + tier
        d = os.path.join(OAR, str(prio))
        os.makedirs(d)
        slots = tier_slots(tier)
        added = 0
        for f in clips:
            src = os.path.join(DAR, f)
            dst = os.path.join(d, f.lower())
            casts = [(tm, 'PIE.$NJ%d%s' % (tier, s)) for tm, s in CASTS.get(f.lower(), []) if slots.get(s)]
            if casts:
                pk = hkanno.Pack(src)
                pk.add_annotations(pk.animations()[0], casts, dst)
                added += len(casts)
            else:
                shutil.copyfile(src, dst)
        # her standing stance: the Shinobi set has none, so Daughter of Coldharbour's sword idle showed
        shutil.copyfile(STANCE_IDLE, os.path.join(d, '1hm_idle.hkx'))
        cfg = {'name': 'Serana Ninja Mode - %s' % TIER_NAMES[tier], 'description': 'Ninja tier %d' % tier,
               'priority': prio, 'overrideAnimationsFolder': '', 'conditions': conditions(tier)}
        json.dump(cfg, open(os.path.join(d, 'config.json'), 'w'), indent=2)
        print('tier %d: %d clips, %d jutsu casts added' % (tier, len(clips), added))
        ini.append('[Tier %d - %s]' % (tier, TIER_NAMES[tier]))
        for slot, v in slots.items():
            if not v:
                continue
            (fid, plugin, comment), cost, mult, on_self = v
            ini.append('; ' + comment)
            ini.append('$NJ%d%s = @CAST|0X%06X|%s|%s|1|%d|0|0|0|0|%d|%d' % (
                tier, slot, fid, plugin, round(POWER[tier] * mult, 3), 1 if on_self else 0, cost, cost))
        ini.append('')
    # kid era: kunai only when it gets serious; the Tobirama dagger moveset, for her, only with the Iron Kunai
    kdir = os.path.join(OAR, '2147483010')
    os.makedirs(kdir)
    for f in os.listdir(TOBIRAMA_DIR):
        if f.lower().endswith('.hkx'):
            shutil.copyfile(os.path.join(TOBIRAMA_DIR, f), os.path.join(kdir, f.lower()))
    json.dump({'name': 'Serana Ninja Mode - Kunai', 'description': 'kid era: the kunai comes out when it gets serious',
               'priority': 2147483010, 'overrideAnimationsFolder': '', 'conditions': [
                   {'condition': 'IsActorBase', 'requiredVersion': '1.0.0.0',
                    'Actor base': {'pluginName': 'Dawnguard.esm', 'formID': '2B6C'}},
                   {'condition': 'IsEquipped', 'requiredVersion': '1.0.0.0', 'Left hand': False,
                    'Form': {'pluginName': 'naruto overhaul.esp', 'formID': '2BB3D'}}]},
              open(os.path.join(kdir, 'config.json'), 'w'), indent=2)
    print('kunai folder:', len([f for f in os.listdir(kdir) if f.endswith('.hkx')]), 'clips')
    p = os.path.join(OUT, 'SKSE', 'PayloadInterpreter', 'Config')
    os.makedirs(p, exist_ok=True)
    open(os.path.join(p, 'SeranaNinjaMode.ini'), 'w', encoding='utf-8').write('\n'.join(ini))
    print('wrote', os.path.join(p, 'SeranaNinjaMode.ini'))


main()
