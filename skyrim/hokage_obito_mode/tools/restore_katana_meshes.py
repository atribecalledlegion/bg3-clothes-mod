"""Put Katana Crafting's own katana models back over Mitsunari's replacements (2026-10-20).

MCO Ishida Mitsunari ships replacement nifs for the Katana Crafting blades: a behaviour-driven rig (autoplay.hkx,
IshidaState1-5 sequences, myweaponroot/yamatoSCB/Blade nodes) whose sword shapes are ALSO children of the root node, so
every katana renders twice: one copy on the back, and one that only Mitsunari's own animations move, parked sheathed at
the hip while Sam's moves play. This copies Katana Crafting's originals (one sword + Scb) into the Hokage mod at the same
paths; the Hokage mod is top priority, so they win. Mitsunari's files are untouched (remove these copies to undo).
Amber/Dark/Golden Dai-Katana have no Katana Crafting original (they keep Mitsunari's model).

usage: restore_katana_meshes.py <mods folder> <out mod folder>
"""
import os, shutil, sys

MODS, OUT = sys.argv[1], sys.argv[2]
MITSU = os.path.join(MODS, 'MCO Ishida Mitsunari')
KC = os.path.join(MODS, 'Katana Crafting SE - NoCC 3.19.1')

kc = {}
for root, _d, files in os.walk(os.path.join(KC, 'Meshes')):
    for f in files:
        if f.lower().endswith('.nif'):
            p = os.path.join(root, f)
            kc[os.path.relpath(p, KC).lower().replace('\\', '/')] = p
done, missing = 0, []
for root, _d, files in os.walk(os.path.join(MITSU, 'meshes')):
    for f in files:
        if not f.lower().endswith('.nif'):
            continue
        rel = os.path.relpath(os.path.join(root, f), MITSU)
        key = rel.lower().replace('\\', '/')
        if '/scabbard/' in key:
            continue                      # Mitsunari's own scabbard pieces, not Katana Crafting files
        src = kc.get(key)
        if not src:
            missing.append(rel); continue
        dst = os.path.join(OUT, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        done += 1
print(f'{done} Katana Crafting models restored; no original for: {missing}')
