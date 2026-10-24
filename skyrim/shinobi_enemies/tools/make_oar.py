"""Write the Shinobi Enemies OAR submods (bandit movesets) into data/.

Usage: make_oar.py <MO2 mods dir>
Copies the animations from installed player-only movesets (personal use) and gives them bandit-only conditions:
  Bandit Tank - Warlord        any SNE_Bandit with a sword/war axe/mace + shield  <- For Honor Warlord (DAR 8071020)
  Bandit Chief - Kenjutsu Axe  SNE_BanditChief with a battleaxe/warhammer         <- Olivier Kenjutsu BattleAxe (DAR 90000600)
Both are plain MCO clips (MCO_* windows + PIE @SGVI MCO_nextattack), nothing player-specific.
"""
import json, os, shutil, sys
MODS = sys.argv[1]
OUT = 'data/meshes/actors/character/animations/OpenAnimationReplacer/Shinobi Enemies'
DAR = 'animations/DynamicAnimationReplacer/_CustomConditions'
ESP = 'Shinobi Enemies.esp'
def kw(fid, neg=False):
    c = {'condition': 'HasKeyword', 'requiredVersion': '1.0.0.0', 'Keyword': {'form': {'pluginName': ESP, 'formID': fid}}}
    if neg: c['negated'] = True
    return c
def eq(t, left):
    return {'condition': 'IsEquippedType', 'requiredVersion': '1.0.0.0', 'Type': {'value': float(t)}, 'Left hand': left}
def anyof(*cs): return {'condition': 'OR', 'requiredVersion': '1.0.0.0', 'Conditions': list(cs)}
def find_dar(mod, num):
    for dp, dn, fn in os.walk(os.path.join(MODS, mod)):
        if os.path.normpath(dp).lower().endswith(os.path.normpath(f'{DAR}/{num}').lower()): return dp
    raise SystemExit(f'not found: {mod} {num}')
SUBS = [
    ('Bandit Tank - Warlord', 'For Honor in Skyrim I Warlord I Sword and shield I MCO Animation', '8071020', 1100000001,
     'Bandits with a one-handed weapon and a shield: For Honor Warlord (shield bashes, headbutts).',
     [kw('800'), anyof(eq(1, False), eq(3, False), eq(4, False)), eq(11, True)]),
    ('Bandit Chief - Kenjutsu Axe', 'Olivier Kenjutsu BattleAxe MCO v', '90000600', 1100000002,
     'Bandit chiefs with a battleaxe or warhammer: Olivier Kenjutsu BattleAxe.',
     [kw('805'), eq(6, False)]),
]
os.makedirs(OUT, exist_ok=True)
json.dump({'name': 'Shinobi Enemies', 'author': 'Claude', 'description': 'Faction movesets for enemies (bandits first). Keywords come from SPID.'},
          open(f'{OUT}/config.json', 'w'), indent=4)
for name, mod, num, prio, desc, conds in SUBS:
    src = find_dar(mod, num); dst = f'{OUT}/{name}'
    os.makedirs(dst, exist_ok=True)
    n = 0
    for f in os.listdir(src):
        if f.lower().endswith('.hkx'): shutil.copy2(os.path.join(src, f), dst); n += 1
    json.dump({'name': name, 'description': desc, 'priority': prio, 'conditions': conds}, open(f'{dst}/config.json', 'w'), indent=4)
    print(f'{name}: {n} clips from {mod} ({num}), priority {prio}')
