"""Witch of the Wilds: Serana-only copies of the Dragon Age Staff Moveset's Ice set, one per Grimoire tier,
plus the Payload Interpreter ini that maps each tier's spell slots to her spells.

Usage: make_oar.py <DA Staff Enhanced mod folder> <out mod folder>

The Ice set's clips call named payloads (PIE.$DASi1 = light attacks, $DASi3 = power attacks 1-2, ...), and
DAstaff.ini maps those names to spells for everyone. Each tier folder here gets its own copies of the clips with
'PIE.$DAS' renamed to 'PIE.$WT<n>' (same length, so the hkx layout does not change), so Serana's spells can differ
per tier without touching what the player gets from the staff.

Folder conditions: Serana (Dawnguard 0x2B6C) + a warhammer-type weapon in the right hand (the Bladestaff) + the
tier's hidden effect (Witch of the Wilds.esp 0x806-0x80A, given by the toggle script). Priorities 2147482001-005
sit above the staff mod's own folders (2147481201-209) and everything else in the load order.

Slots in the Ice clips (from the annotations):
  i1  light attacks 1-5           i2  attack 5's second cast        i3  power attacks 1 and 2
  i4  power attack 3              i5  power attack 4 (breath pose)  i6  power attack 7 (summon pose)
  i12 power attack 5 first cast   i10 power attack 5 big finish     i11 power attack 6 (self buff)
  d   roll / step dodge clips
"""
import json, os, shutil, sys

SRC, OUT = sys.argv[1], sys.argv[2]
ICE = os.path.join(SRC, 'meshes', 'actors', 'character', 'animations', 'OpenAnimationReplacer',
                   'Dragon Age Staff Moveset', '2147481204')
OAR = os.path.join(OUT, 'meshes', 'actors', 'character', 'animations', 'OpenAnimationReplacer', 'Witch of the Wilds')
ESP = 'Witch of the Wilds.esp'
TIER_MGEF = {1: 0x806, 2: 0x807, 3: 0x808, 4: 0x809, 5: 0x80A}
TIER_NAMES = {1: 'Novice', 2: 'Apprentice', 3: 'Adept', 4: 'Expert', 5: 'Master'}

SK, DG, DOC, ARC = 'Skyrim.esm', 'Dawnguard.esm', 'Daughter of Coldharbor.esp', 'Arcanum.esp'
# spell: (form id, plugin, comment)
ICE_SPIKE = (0x02B96C, SK, 'Ice Spike')
ICY_SPEAR = (0x10F7EC, SK, 'Icy Spear')
ICE_STORM = (0x045F9C, SK, 'Ice Storm')
BLIZZARD = (0x07E8E4, SK, 'Blizzard')
FROST_CLOAK = (0x03AEA2, SK, 'Frost Cloak')
DRAIN = (0x00080D, DOC, 'Drain Life (Daughter of Coldharbour)')
BAT_CLOAK = (0x000809, DOC, 'Bat Swarm cloak (Daughter of Coldharbour)')
VAMP_DODGE = (0x000813, DOC, 'Vampiric Dodge (Daughter of Coldharbour)')
GARGOYLE = (0x000801, DOC, 'Summon Gargoyle (Daughter of Coldharbour)')
# (Raise Dead is not used: it needs a corpse as its target, and these casts aim at her living target.
#  Her own AI still raises the dead with her vanilla spell list.)
CRIPPLING_CHILL = (0x39009D, ARC, "Crippling Chill (Winter's Grasp)")
ICY_CANNONADE = (0xB442BC, ARC, 'Icy Cannonade')
FROST_VEIL = (0x367850, ARC, 'Frost Veil')
GELID_GALE = (0x144993, ARC, 'Gelid Gale (Cone of Cold)')
ICICLE_FALL = (0x14EBAB, ARC, 'Icicle Fall')
CRYSTAL_SPEAR = (0x37BC76, ARC, 'Crystalline Spear')
GLACIAL_PILLAR = (0x13F88D, ARC, 'Glacial Pillar')
SOUL_OF_WINTER = (0x36C961, ARC, 'Soul of Winter')

# slot -> list of (spell, magicka cost); a slot may cast more than one spell
TIERS = {
    1: {'i1': [(ICE_SPIKE, 0)], 'i2': [(DRAIN, 15)], 'i3': [(CRIPPLING_CHILL, 25)], 'i4': [(ICE_STORM, 40)],
        'i5': [(DRAIN, 20)], 'i6': [(GARGOYLE, 50)], 'i12': [(FROST_CLOAK, 30)], 'i10': [(ICE_STORM, 60)],
        'i11': [(BAT_CLOAK, 35)], 'd': [(VAMP_DODGE, 0)]},
    2: {'i1': [(ICE_SPIKE, 0)], 'i2': [(ICY_CANNONADE, 20)], 'i3': [(CRIPPLING_CHILL, 25)], 'i4': [(ICE_STORM, 40)],
        'i5': [(DRAIN, 20)], 'i6': [(GARGOYLE, 50)], 'i12': [(FROST_VEIL, 35)], 'i10': [(ICY_SPEAR, 60)],
        'i11': [(BAT_CLOAK, 35)], 'd': [(VAMP_DODGE, 0)]},
    3: {'i1': [(ICY_SPEAR, 0)], 'i2': [(ICY_CANNONADE, 20)], 'i3': [(GELID_GALE, 35)], 'i4': [(ICE_STORM, 40)],
        'i5': [(DRAIN, 20)], 'i6': [(GARGOYLE, 50)], 'i12': [(FROST_VEIL, 35)], 'i10': [(ICICLE_FALL, 80)],
        'i11': [(BAT_CLOAK, 35)], 'd': [(VAMP_DODGE, 0)]},
    4: {'i1': [(ICY_SPEAR, 0)], 'i2': [(CRYSTAL_SPEAR, 30)], 'i3': [(GELID_GALE, 35)], 'i4': [(ICICLE_FALL, 50)],
        'i5': [(DRAIN, 20)], 'i6': [(GARGOYLE, 50)], 'i12': [(FROST_VEIL, 35)],
        'i10': [(GLACIAL_PILLAR, 90)], 'i11': [(BAT_CLOAK, 35)], 'd': [(VAMP_DODGE, 0)]},
    5: {'i1': [(ICY_SPEAR, 0)], 'i2': [(CRYSTAL_SPEAR, 30)], 'i3': [(GELID_GALE, 35)], 'i4': [(ICICLE_FALL, 50)],
        'i5': [(DRAIN, 20)], 'i6': [(GARGOYLE, 50)], 'i12': [(SOUL_OF_WINTER, 50)],
        'i10': [(BLIZZARD, 100)], 'i11': [(BAT_CLOAK, 35)], 'd': [(VAMP_DODGE, 0)]},
}
# effectiveness per tier (her spells hit harder as the Grimoire opens up); the mode is meant to be strong
POWER = {1: 1.0, 2: 1.3, 3: 1.6, 4: 1.9, 5: 2.25}
# magnitude field as the staff mod uses it (duration-style spells: cloaks, summons, Blizzard)
MAGNITUDE = {'i6': 10, 'i12': 10, 'i11': 10, 'i10': 30}


def conditions(tier):
    return [
        {'condition': 'IsActorBase', 'requiredVersion': '1.0.0.0',
         'Actor base': {'pluginName': 'Dawnguard.esm', 'formID': '2B6C'}},
        {'condition': 'IsEquippedType', 'requiredVersion': '1.0.0.0', 'Type': {'value': 10.0}, 'Left hand': False},
        {'condition': 'HasMagicEffect', 'requiredVersion': '1.0.0.0', 'negated': False,
         'Magic effect': {'pluginName': ESP, 'formID': '%X' % TIER_MGEF[tier]}},
    ]


def main():
    clips = [f for f in os.listdir(ICE) if f.lower().endswith('.hkx')]
    assert 'mco_attack1.hkx' in clips, clips
    if os.path.isdir(OAR):
        shutil.rmtree(OAR)
    os.makedirs(OAR)
    json.dump({'name': 'Witch of the Wilds', 'description': "Serana's staff spells, one folder per Grimoire tier",
               'author': 'Claude'}, open(os.path.join(OAR, 'config.json'), 'w'), indent=2)
    for tier in TIERS:
        prio = 2147482000 + tier
        d = os.path.join(OAR, str(prio))
        os.makedirs(d)
        renamed = 0
        for f in clips:
            data = open(os.path.join(ICE, f), 'rb').read()
            n = data.count(b'PIE.$DAS')
            data = data.replace(b'PIE.$DAS', b'PIE.$WT%d' % tier)
            renamed += n
            open(os.path.join(d, f), 'wb').write(data)
        cfg = {'name': 'Witch of the Wilds - %s' % TIER_NAMES[tier], 'description': 'Grimoire tier %d' % tier,
               'priority': prio, 'overrideAnimationsFolder': '', 'conditions': conditions(tier)}
        json.dump(cfg, open(os.path.join(d, 'config.json'), 'w'), indent=2)
        print('tier %d: %d clips, %d payload names renamed' % (tier, len(clips), renamed))

    ini = ['; Witch of the Wilds: Serana\'s staff spells by Grimoire tier (generated by tools/make_oar.py).',
           '; @CAST|spell|plugin|effectiveness|magnitude|self|HealthReq|HealthCost|StaminaReq|StaminaCost|MagickaReq|MagickaCost',
           '; A spell that will not cast for her can be swapped here: edit the form id and plugin, then reload the game.', '']
    for tier, slots in TIERS.items():
        ini.append('[Tier %d - %s]' % (tier, TIER_NAMES[tier]))
        for slot, spells in slots.items():
            for (fid, plugin, comment), cost in spells:
                mag = MAGNITUDE.get(slot, 1)
                line = '$WT%d%s = @CAST|0X%06X|%s|%s|%d|0|0|0|0|0|%d|%d' % (
                    tier, slot, fid, plugin, POWER[tier], mag, cost, cost)
                ini.append('; ' + comment)
                ini.append(line)
                if slot == 'd':   # the bat dodge: a moment of invulnerability, as Daughter of Coldharbour does it
                    ini.append('$WT%dd = @SETGHOST|1' % tier)
                    ini.append('$WT%dd = ![1]@SETGHOST|0' % tier)
        ini.append('')
    p = os.path.join(OUT, 'SKSE', 'PayloadInterpreter', 'Config')
    os.makedirs(p, exist_ok=True)
    open(os.path.join(p, 'WitchOfTheWilds.ini'), 'w', encoding='utf-8').write('\n'.join(ini))
    print('wrote', os.path.join(p, 'WitchOfTheWilds.ini'))


main()
