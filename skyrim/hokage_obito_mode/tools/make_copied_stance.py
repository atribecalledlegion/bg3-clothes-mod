"""Copied style stance fix (2026-10-20): Mitsunari's idle / block / walk / run / sprint clips hold the katana as if it
were sheathed in his left-hand scabbard (iaido stance). With the scabbard hidden (Hide Mitsunari Scabbards) that reads
as a backwards grip. This OAR set gives the Copied style Sam's blade-out stance and movement instead, while
Mitsunari's attacks and skills still play:
  idle / block / combat idles  <- Sam Basic
  forward walk + diagonals     <- Sam Basic RUN (Sam's own walk rests the sword on the shoulder; same as Leaf)
  backward / side / strafe     <- Sam Strafe set
  sprint                       <- Sam Sprint Loop
Gate: Hokage mode + Copied style (0x80E) + two-handed sword + player. Priority 1961251000: above Mitsunari Basic
(1961250000), below his reactions like Perfect Block Recovery (1961252010). Delete the folder to undo.

usage: make_copied_stance.py <Sam mod folder> <out mod folder>
"""
import json, os, shutil, sys

SAM, OUT = sys.argv[1], sys.argv[2]
REL = os.path.join('meshes', 'actors', 'character', 'animations', 'OpenAnimationReplacer', 'MCO Jetstream Sam NEW')
SRC = os.path.join(SAM, REL)
DST = os.path.join(OUT, REL, 'Hokage Copied Stance')
ESP = 'Hokage Obito Mode.esp'


def find(folder, name):
    d = os.path.join(SRC, folder)
    for f in os.listdir(d):
        if f.lower() == name.lower():
            return os.path.join(d, f)
    raise SystemExit('missing %s/%s' % (folder, name))


PLAN = {}
for n in ('2hm_idle', '2hm_blockidle', '2hm_blockanticipate', 'combatidlea', 'combatidleb', 'combatidlec',
          'combatidlesmalla', 'combatidlesmallb'):
    PLAN[n] = ('Basic', n)
for n in ('2hm_runforward', '2hm_runforwardleft', '2hm_runforwardright',
          '2hm_walkforward', '2hm_walkforwardleft', '2hm_walkforwardright'):
    PLAN[n] = ('Basic', '2hm_runforward')
for n in ('2hm_runbackward', '2hm_runbackwardleft', '2hm_runbackwardright', '2hm_runleft', '2hm_runright',
          '2hm_runstrafeleft', '2hm_runstraferight', '2hm_walkbackward', '2hm_walkbackwardleft',
          '2hm_walkbackwardright', '2hm_walkleft', '2hm_walkright'):
    PLAN[n] = ('Strafe', n)
PLAN['2hm_runstrafeleft3'] = ('Strafe', '2hm_runstrafeleft')
PLAN['2hm_runstraferight3'] = ('Strafe', '2hm_runstraferight')
PLAN['2hm_sprintForwardSword'] = ('Sprint Loop', '2hm_sprintforwardsword')

if os.path.isdir(DST):
    shutil.rmtree(DST)
os.makedirs(DST)
for out, (folder, name) in PLAN.items():
    shutil.copy2(find(folder, name + '.hkx'), os.path.join(DST, out + '.hkx'))
config = {
    'name': 'Hokage Copied Stance',
    'description': "Copied style: Sam's blade-out stance/movement over Mitsunari's sheathed-grip ones.",
    'priority': 1961251000,
    'conditions': [
        {'condition': 'HasMagicEffect', 'requiredVersion': '1.0.0.0', 'negated': False,
         'Magic effect': {'pluginName': ESP, 'formID': '803'}, 'Active effects only': True},
        {'condition': 'HasMagicEffect', 'requiredVersion': '1.0.0.0', 'negated': False,
         'Magic effect': {'pluginName': ESP, 'formID': '80E'}, 'Active effects only': True},
        {'condition': 'IsEquippedType', 'requiredVersion': '1.0.0.0', 'Type': {'value': 5.0}, 'Left hand': False},
        {'condition': 'IsActorBase', 'requiredVersion': '1.0.0.0',
         'Actor base': {'pluginName': 'Skyrim.esm', 'formID': '7'}},
    ],
}
json.dump(config, open(os.path.join(DST, 'config.json'), 'w', encoding='utf-8'), indent=4)
print('wrote', len(PLAN), 'clips to', DST)
