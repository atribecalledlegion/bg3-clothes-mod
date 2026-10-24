"""Jetstream Sam -> Hokage Obito (2026-10-20).

Writes override copies of every Sam OAR config.json into <out>/meshes/... (same relative paths), so a higher-priority
MO2 mod wins them; Sam's own folder is never touched and its animations are still read from there.
In each config, the weapon gate (an OR of IsEquipped / IsEquippedRight on the Ebony Blade 0x4A38F / 0xEA29C or Legacy's
gallery copy 0x1259F3) is replaced by:  HasMagicEffect HKO_ModeMark (Hokage Obito Mode.esp 0x803)  AND  a two-handed
sword (IsEquippedType 5; 2026-10-20: all three movesets are two-handed sets, the Ebony Blade here is anim type 5). Everything else (keytrace directions, NEAE / Mouse Tracker effects,
priorities) is kept.

usage: make_sam_oar.py <Sam mod folder> <out mod folder>
"""
import json, os, sys

SAM, OUT = sys.argv[1], sys.argv[2]
ESP = 'Hokage Obito Mode.esp'
# 2026-10-20: Sam's resting-stance set (NOT HasMagicEffect sam_counter 0x8C2) played its shoulder-carry run for a moment
# at every run start until the run clip's SamState1 event switched to the blade-out set; off = one consistent stance.
DISABLED_SETS = {'Sheath Move&Idle'}
EBONY = {('skyrim.esm', '4a38f'), ('skyrim.esm', 'ea29c'), ('legacyofthedragonborn.esm', '1259f3')}
HOKAGE = [
    {'condition': 'HasMagicEffect', 'requiredVersion': '1.0.0.0', 'negated': False,
     'Magic effect': {'pluginName': ESP, 'formID': '803'}, 'Active effects only': True},
    {'condition': 'IsEquippedType', 'requiredVersion': '1.0.0.0', 'Type': {'value': 5.0}, 'Left hand': False},
]


def is_ebony(c):
    f = c.get('Form') or {}
    return (c.get('condition') in ('IsEquipped', 'IsEquippedRight') and not c.get('negated')
            and (f.get('pluginName', '').lower(), f.get('formID', '').lower()) in EBONY)


def retarget(conds):
    out, hit = [], 0
    for c in conds:
        if c.get('condition') == 'OR' and c.get('Conditions') and all(is_ebony(x) for x in c['Conditions']):
            out.extend(json.loads(json.dumps(HOKAGE))); hit += 1
        elif is_ebony(c):
            out.extend(json.loads(json.dumps(HOKAGE))); hit += 1
        else:
            out.append(c)
    return out, hit


def main():
    n = changed = 0
    for root, _dirs, files in os.walk(SAM):
        if 'config.json' not in files or 'OpenAnimationReplacer' not in root:
            continue
        p = os.path.join(root, 'config.json'); n += 1
        j = json.load(open(p, encoding='utf-8'))
        if 'conditions' not in j:
            continue                      # the mod's own folder config
        j['conditions'], hit = retarget(j['conditions'])
        if not hit:
            print('NO WEAPON GATE (left alone):', os.path.relpath(p, SAM)); continue
        if hit > 1:
            print('two gates?', os.path.relpath(p, SAM))
        if j.get('name') in DISABLED_SETS:
            j['disabled'] = True
        dst = os.path.join(OUT, os.path.relpath(p, SAM))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        json.dump(j, open(dst, 'w', encoding='utf-8'), indent=4, ensure_ascii=False)
        changed += 1
    print(f'{n} configs read, {changed} retargeted to Hokage mode + two-handed sword')


main()
