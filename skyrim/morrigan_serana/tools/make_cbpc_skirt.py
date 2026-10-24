"""Make a CBPC add-on that sways Skyrim's standard skirt bones (SkirtF/B/L/RBone02-03), as Morrigan's robe uses.
Writes CBPCMasterConfig_Skirt.txt (bone -> alias 'Skirt', females only) and CBPConfig_Skirt.txt (unconditioned
bounce settings for that alias only; CBPC merges unconditioned files, like its own *Amplitude files).
Every key the Breast alias has in CBPC's own CBPConfig.txt is written for Skirt, with skirt values."""
import os, re, sys
src, out = sys.argv[1], sys.argv[2]
keys = []
for line in open(src, encoding='utf-8', errors='replace'):
    m = re.match(r'\s*Breast\.(\w+)\s+(\S+)', line)
    if m and m.group(1) not in [k for k, _ in keys]:
        keys.append((m.group(1), float(m.group(2))))
skirt = {                      # a robe skirt: loose swing fore/aft and sideways (rotation), little vertical bounce
    'stiffness': 0.035, 'stiffness2': 0.015, 'damping': 0.16,
    'Xmaxoffset': 8.0, 'Xminoffset': -8.0, 'Ymaxoffset': 12.0, 'Yminoffset': -12.0, 'Zmaxoffset': 3.0, 'Zminoffset': -3.0,
    'timetick': 6.0, 'linearX': 1.2, 'linearY': 1.6, 'linearZ': 0.4,
    # v2 (2026-10-15): the first pass only slid the flaps a little ("moves but doesn't flap"). Turn the motion into
    # rotation like CBPC's butt/belly do: fore/aft motion tips the flaps (rotation X), sideways motion swings them (Y).
    'rotationalX': 0.12, 'rotationalY': 0.08, 'linearYrotationX': 1.0, 'linearXrotationY': 1.0,
}
zero_prefixes = ('linearXspread', 'linearYspread', 'linearZspread', 'rotational', 'linearXrotation', 'linearYrotation', 'linearZrotation')
lines = ['# Skirt sway for Skyrim\'s standard skirt bones (SkirtF/B/L/RBone02-03). Made for DAO Morrigan\'s Robes.',
         '# No Conditions line: merged with the default (unconditioned) CBPC bounce settings.']
for k, v in keys:
    if k in skirt: v = skirt[k]
    elif k.startswith(zero_prefixes): v = 0.0
    lines.append('Skirt.%s %g' % (k, v))
os.makedirs(out, exist_ok=True)
open(os.path.join(out, 'CBPConfig_Skirt.txt'), 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
bones = ['Skirt%sBone%02d' % (side, n) for side in 'FBLR' for n in (2, 3)]
master = ['# Skirt sway (see CBPConfig_Skirt.txt). The 01 bones at the waist stay still.', '[ConfigMap]']
master += ['%s=Skirt=IsFemale()' % b for b in bones]
open(os.path.join(out, 'CBPCMasterConfig_Skirt.txt'), 'w', encoding='utf-8').write('\n'.join(master) + '\n')
print('wrote', len(keys), 'Skirt settings and', len(bones), 'bones')
