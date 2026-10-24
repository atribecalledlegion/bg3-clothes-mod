"""Copy Wheel styles (2026-10-20): move the Fire Release and Copied movesets onto Hokage Obito.

Sam (Leaf) stays the base underneath every style (its sets have no style condition); a style's sets sit at a higher
priority, so they win only where they have an animation.

FIRE RELEASE = Aether Gazer Kagutsuchi's one-handed "EvilFire" set (DAR 999810201-999810205; its main longqie set is
two-handed). DAR priorities (999810xxx) are below Sam's OAR 1261250000, so the folders are COPIED (hkx + conditions)
into <out>/.../DynamicAnimationReplacer/_CustomConditions/2100810201-2100810205, with the weapon keyword gate
IsEquippedRightHasKeyword(AetherGazer 0x880) swapped for: Hokage mode + Fire style + a two-handed sword (2026-10-20: was one-handed).

COPIED = Mitsunari's OAR sets (priorities 1961250000+, already above Sam): override copies of their config.json at the
same paths, the Dai-Katana gate (OR of IsEquippedHasKeyword KatanaCrafting 0x157) swapped for Hokage mode + Copied
style + two-handed sword (its own weapon type: Dai-Katanas are two-handed).

usage: make_style_oar.py <mods folder> <out mod folder>
"""
import json, os, shutil, sys

MODS, OUT = sys.argv[1], sys.argv[2]
ESP = 'Hokage Obito Mode.esp'
KAGU = os.path.join(MODS, 'Aether Gazer Kagutsuchi', 'Meshes', 'actors', 'character', 'animations',
                    'DynamicAnimationReplacer', '_CustomConditions')
MITSU = os.path.join(MODS, 'MCO Ishida Mitsunari')
DAR_OUT = os.path.join(OUT, 'meshes', 'actors', 'character', 'animations', 'DynamicAnimationReplacer', '_CustomConditions')

# ---- Fire Release: Kagutsuchi EvilFire ----
GATE = 'IsEquippedRightHasKeyword("AetherGazer.esp" | 0x000880)'
FIRE = ('HasMagicEffect("%s" | 0x000803) AND\nHasMagicEffect("%s" | 0x00080D) AND\nIsEquippedRightType(5)' % (ESP, ESP))
for n in range(999810201, 999810206):
    src = os.path.join(KAGU, str(n))
    dst = os.path.join(DAR_OUT, str(n - 999810201 + 2100810201))
    if os.path.isdir(dst): shutil.rmtree(dst)
    os.makedirs(dst)
    for f in os.listdir(src):
        if f.lower() == '_conditions.txt':
            text = open(os.path.join(src, f), encoding='utf-8-sig').read()
            assert GATE in text, (n, text)
            open(os.path.join(dst, '_conditions.txt'), 'w', encoding='utf-8').write(text.replace(GATE, FIRE))
        else:
            shutil.copy2(os.path.join(src, f), dst)
    print('fire', n, '->', os.path.basename(dst), len(os.listdir(dst)) - 1, 'clips')

# ---- Copied: Mitsunari ----
HOKAGE_COPIED = [
    {'condition': 'HasMagicEffect', 'requiredVersion': '1.0.0.0', 'negated': False,
     'Magic effect': {'pluginName': ESP, 'formID': '803'}, 'Active effects only': True},
    {'condition': 'HasMagicEffect', 'requiredVersion': '1.0.0.0', 'negated': False,
     'Magic effect': {'pluginName': ESP, 'formID': '80E'}, 'Active effects only': True},
    {'condition': 'IsEquippedType', 'requiredVersion': '1.0.0.0', 'Type': {'value': 5.0}, 'Left hand': False},
]
def dai_katana_gate(c):
    kids = c.get('Conditions') or []
    return c.get('condition') == 'OR' and kids and all(
        k.get('condition') == 'IsEquippedHasKeyword' and not k.get('negated') for k in kids)
done = 0
for root, _d, files in os.walk(MITSU):
    if 'config.json' not in files or 'OpenAnimationReplacer' not in root:
        continue
    p = os.path.join(root, 'config.json'); j = json.load(open(p, encoding='utf-8'))
    if 'conditions' not in j:
        continue
    new, hit = [], 0
    for c in j['conditions']:
        if dai_katana_gate(c):
            new.extend(json.loads(json.dumps(HOKAGE_COPIED))); hit += 1
        else:
            new.append(c)
    if hit != 1:
        print('SKIPPED (gate not found):', os.path.relpath(p, MITSU)); continue
    j['conditions'] = new
    dst = os.path.join(OUT, os.path.relpath(p, MITSU))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    json.dump(j, open(dst, 'w', encoding='utf-8'), indent=4, ensure_ascii=False)
    done += 1
print('copied style:', done, 'Mitsunari sets retargeted')
