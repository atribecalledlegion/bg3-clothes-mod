"""Copied style sword-pose fix (2026-10-20). Mitsunari's sword rig is switched by annotations: IshidaState1 = blade
out in the right hand, IshidaBeginState = sheathed in the left hand. Two clips fight the attacks in this setup
(OAR event log, control test 23:16):
  - attacking while moving starts his walk/run clip next to the attack; its 0.0 IshidaBeginState lands 1 ms after the
    attack's IshidaState1, so the first swing has no blade (later combo hits don't restart the walk clip)
  - the quick-draw equip clip (0.033 s) loops ~200 ms into the attack, sending IshidaBeginState every loop
Fix, as copies of his clips at the same paths in <out mod> (only Copied plays his sets):
  - attack clips whose first pose event is IshidaState1 (<= 0.1 s) get IshidaState1 again at 0.06 / 0.15 / 0.25 s,
    each only before the clip's next pose change (tools/hkanno.py appends them)
  - Quick Draw / Quick Draw NA 2hc_equip: IshidaBeginState made inert in place (his drawn idle sheathes on its own)
Delete the copied .hkx files from the Hokage mod to undo.

usage: make_copied_anno_fix.py <Mitsunari mod folder> <out mod folder>
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'serana_ninja_mode', 'tools'))
from hkanno import Pack

MITSU, OUT = sys.argv[1], sys.argv[2]
REASSERT = (0.06, 0.15, 0.25)
INERT = b'HKOoff'
EQUIP_SETS = ('quick draw', 'quick draw na')

patched = inert = failed = 0
for root, _d, fs in os.walk(MITSU):
    if 'OpenAnimationReplacer' not in root:
        continue
    for f in fs:
        if not f.lower().endswith('.hkx'):
            continue
        src = os.path.join(root, f)
        dst = os.path.join(OUT, os.path.relpath(src, MITSU))
        if f.lower() == '2hc_equip.hkx' and os.path.basename(root).lower() in EQUIP_SETS:
            d = bytearray(open(src, 'rb').read())
            key = b'IshidaBeginState\0'
            i = d.find(key)
            if i >= 0:
                d[i:i + len(key)] = INERT + b'\0' * (len(key) - len(INERT))
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                open(dst, 'wb').write(bytes(d))
                inert += 1
            continue
        pk = Pack(src)
        anim = pk.animations()[0]
        ish = sorted((t, x) for _tr, _n, anns in pk.tracks(anim) for _a, t, x in anns if x.startswith('IshidaState')
                     or x == 'IshidaBeginState')
        if not ish or ish[0][1] != 'IshidaState1' or ish[0][0] > 0.1:
            continue
        nxt = min([t for t, x in ish if t > ish[0][0] and x != 'IshidaState1'] + [pk.duration(anim)])
        adds = [(t, 'IshidaState1') for t in REASSERT if ish[0][0] < t < nxt]
        if not adds:
            continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        try:
            pk.add_annotations(anim, adds, dst)
            patched += 1
        except AssertionError as e:
            print('skipped', os.path.relpath(src, MITSU), e)
            failed += 1
print(f'{patched} attack clips re-assert the blade, {inert} quick-draw equips made inert, {failed} skipped')
