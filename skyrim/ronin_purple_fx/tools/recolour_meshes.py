"""Ronin Purple FX, mesh pass: Obito's Kamui purple for the Vergil kit's blue effects.

Most of the Vergil effects (Yamato, Summoned Swords, Bono Kustom slash, VergilSDT) take their colour from the effect
shader, not the texture: a blue emissive colour on a grey texture. This rewrites, per NIF:
- every BSEffectShaderProperty's emissive colour,
- the colour keys of each BSEffectShaderPropertyColorController (followed controller -> NiPoint3Interpolator ->
  NiPosData, so position keys are never touched) and the interpolator's resting value,
- the three colours of each BSPSysSimpleColorModifier (particles).
Only blue hues (HUE_LO..HUE_HI) move; reds, golds, whites and greys stay as they are. Brightness and saturation are
kept (an HDR colour above 1.0 is scaled down, shifted, and scaled back up).
Writes only the NIFs that changed, under <out>/meshes/... (same relative path, so MO2 overrides the original).

usage: recolour_meshes.py <nif_util dir> <out mod dir> <mod dir>...
"""
import json, os, struct, sys
sys.path.insert(0, sys.argv[1])
from nif_util import Nif, effect_emissive_offset

OUT = sys.argv[2]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from purple_core import purple


def tint(b, p):
    old = struct.unpack_from('<3f', b, p)
    if not all(abs(v) < 1e30 for v in old):          # -FLT_MAX = unset
        return 0
    new, moved = purple(old)
    if moved:
        struct.pack_into('<3f', b, p, *new)
    return int(moved)


def pos_data_keys(b):
    n, kind = struct.unpack_from('<II', b, 0)
    if not n:
        return []
    step = {1: 16, 2: 40, 3: 28}[kind]
    return [8 + i * step + 4 for i in range(n)]


def recolour(path):
    nif = Nif(path)
    moved = 0
    for i in nif.of_type('BSEffectShaderProperty'):
        moved += tint(nif.blocks[i], effect_emissive_offset(nif.blocks[i]))
    for i in nif.of_type('BSEffectShaderPropertyColorController'):
        interp = struct.unpack_from('<i', nif.blocks[i], 26)[0]          # NiTimeController (26 bytes), then interpolator
        if interp < 0 or nif.type_of(interp) != 'NiPoint3Interpolator':
            continue
        ib = nif.blocks[interp]
        moved += tint(ib, 0)
        data = struct.unpack_from('<i', ib, 12)[0]
        if data >= 0 and nif.type_of(data) == 'NiPosData':
            for p in pos_data_keys(nif.blocks[data]):
                moved += tint(nif.blocks[data], p)
    for i in nif.of_type('BSPSysSimpleColorModifier'):
        b = nif.blocks[i]
        for k in range(3):
            moved += tint(b, len(b) - 48 + 16 * k)
    return nif, moved


report = {}
for root in sys.argv[3:]:
    for dp, dn, fn in os.walk(root):
        for f in fn:
            if not f.lower().endswith('.nif'):
                continue
            src = os.path.join(dp, f)
            rel = os.path.relpath(src, root)
            try:
                nif, moved = recolour(src)
            except Exception as e:
                report[rel] = 'error: %s' % e
                continue
            if moved:
                dst = os.path.join(OUT, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                nif.write(dst)
                report[rel] = moved
json.dump(report, open(os.path.join(os.path.dirname(OUT.rstrip('/\\')), 'mesh_report.json'), 'w'), indent=1)
done = {k: v for k, v in report.items() if isinstance(v, int)}
print('recoloured %d nifs (%d colours), errors %d' % (len(done), sum(done.values()), len(report) - len(done)))
for k, v in report.items():
    if not isinstance(v, int):
        print(' ', k, v)
