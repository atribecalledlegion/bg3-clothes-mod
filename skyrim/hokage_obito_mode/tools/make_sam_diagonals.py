"""Sam diagonals (2026-10-20): Sam's moveset ships only straight 2hm_walkforward / 2hm_runforward, so moving at an angle
fell back to Smooth Moveset's player diagonals (DAR 8000001, sword resting on the shoulder) for a moment.
Copies Sam's forward walk/run as the four forward diagonals into a new OAR set 'Hokage Diagonals' inside Sam's OAR mod
folder (in the Hokage mod), same conditions as Sam Basic (Hokage mode + two-handed sword + player), one priority above it.
The Copied style's Mitsunari diagonals (priority 1961250000+) still win in that style. Delete the folder to undo.

usage: make_sam_diagonals.py <Sam mod folder> <out mod folder>
"""
import json, os, shutil, sys

SAM, OUT = sys.argv[1], sys.argv[2]
REL = os.path.join('meshes', 'actors', 'character', 'animations', 'OpenAnimationReplacer', 'MCO Jetstream Sam NEW')
BASIC = os.path.join(SAM, REL, 'Basic')
DST = os.path.join(OUT, REL, 'Hokage Diagonals')
ESP = 'Hokage Obito Mode.esp'


def find(name):
    for f in os.listdir(BASIC):
        if f.lower() == name:
            return os.path.join(BASIC, f)
    raise SystemExit('missing ' + name)


os.makedirs(DST, exist_ok=True)
walk, run = find('2hm_walkforward.hkx'), find('2hm_runforward.hkx')
# 2026-10-20 (OAR animation log): Sam's own 2hm_walkforward (clip 2HM_WalkForwardSlow) carries the sword on the
# shoulder and blends in at every speed-up / slow-down -> the walk slots use Sam's RUN clip too (user: consistency
# over foot sliding).
shutil.copy2(run, os.path.join(DST, '2hm_walkforward.hkx'))
for side in ('left', 'right'):
    shutil.copy2(run, os.path.join(DST, '2hm_walkforward%s.hkx' % side))
    shutil.copy2(run, os.path.join(DST, '2hm_runforward%s.hkx' % side))
config = {
    'name': 'Hokage Diagonals',
    'description': "Sam's forward run used for walk + forward diagonals (his walk rests the sword on the shoulder).",
    'priority': 1261250001,
    'conditions': [
        {'condition': 'HasMagicEffect', 'requiredVersion': '1.0.0.0', 'negated': False,
         'Magic effect': {'pluginName': ESP, 'formID': '803'}, 'Active effects only': True},
        {'condition': 'IsEquippedType', 'requiredVersion': '1.0.0.0', 'Type': {'value': 5.0}, 'Left hand': False},
        {'condition': 'IsActorBase', 'requiredVersion': '1.0.0.0',
         'Actor base': {'pluginName': 'Skyrim.esm', 'formID': '7'}},
    ],
}
json.dump(config, open(os.path.join(DST, 'config.json'), 'w', encoding='utf-8'), indent=4)
print('wrote', DST, sorted(os.listdir(DST)))
