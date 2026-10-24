"""Sam without knockdown/push physics (2026-10-20, after two Havok physics crashes in Sam combat).

Copies every Sam OAR clip that calls a ragdoll/push payload into <out mod> at the same path, with those PIE calls
overwritten in place by an annotation nothing listens to (shorter text + null padding, so no offsets move; the Ronin
taunt technique). Sam's own files, and the same payloads in other movesets (Vergil uses $knockdown too), are untouched.
Delete the copied .hkx files from the Hokage mod to undo.
  $PushBack        NEAE PushBackS: Ordinator Windswept script, PushActorAway 32-128
  $knockdown(2)    stagger + explosion force 10 (every 5th combo hit)
  $blowup1         stagger + explosion force 10
  $SmashDownFogSam script that places a FireballExplosion at a marker

usage: make_sam_nopush.py <Sam mod folder> <out mod folder>
"""
import os, sys

SAM, OUT = sys.argv[1], sys.argv[2]
NAMES = [b'PIE.$PushBack', b'PIE.$knockdown2', b'PIE.$knockdown', b'PIE.$blowup1', b'PIE.$SmashDownFogSam']
INERT = b'HKOoff'

files = calls = 0
for root, _d, fs in os.walk(SAM):
    if 'OpenAnimationReplacer' not in root:
        continue
    for f in fs:
        if not f.lower().endswith('.hkx'):
            continue
        p = os.path.join(root, f)
        d = bytearray(open(p, 'rb').read())
        hit = 0
        for name in NAMES:
            key = name + b'\0'
            i = d.find(key)
            while i >= 0:
                d[i:i + len(key)] = INERT + b'\0' * (len(key) - len(INERT))
                hit += 1
                i = d.find(key, i + 1)
        if hit:
            dst = os.path.join(OUT, os.path.relpath(p, SAM))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            open(dst, 'wb').write(bytes(d))
            files += 1; calls += hit
print(f'{files} Sam clips copied with {calls} push/knockdown calls made inert')
