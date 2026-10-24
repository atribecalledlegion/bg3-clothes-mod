"""Shorten each toenail so its front edge stops just behind its toe tip (close-ups 2026-10-15: nails overhung the
toes like claws). The back edge (cuticle) stays put; the nail is scaled along y (forward) from it.
usage: trim_toenails.py <feet.nif> <nails_in.nif> <nails_out.nif> [tip_gap] [--scale S]
--scale S: shorten every nail to S of its length from the cuticle (the tip measure picks up neighbouring toes, so
the user's close-ups decided: 0.75 on 2026-10-15)."""
import sys, os
here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, 'fit_toenails.py'), encoding='utf-8').read()
ns = {}; exec(compile(src[:src.index('NAIL_VERTS =')], 'fit', 'exec'), ns)
parse, get, put = ns['parse'], ns['get'], ns['put']
FIXED = None
if '--scale' in sys.argv:
    i = sys.argv.index('--scale'); FIXED = float(sys.argv[i + 1]); del sys.argv[i:i + 2]
FEET, IN, OUT = sys.argv[1:4]
GAP = float(sys.argv[4]) if len(sys.argv) > 4 else 0.12
fd, fs = parse(FEET); nd, nshapes = parse(IN)
feet = [get(fd, v) for n, vs in fs for v in vs]
verts = [v for n, vs in nshapes for v in vs]
NV = 194
for side in (-1, 1):
    nails = [verts[k:k + NV] for k in range(0, len(verts), NV) if get(nd, verts[k])[0] * side > 0]
    nails.sort(key=lambda b: abs(sum(get(nd, v)[0] for v in b) / len(b)))
    for name, b in zip(['big', 'second', 'middle', 'ring', 'pinky'], nails):
        pts = [get(nd, v) for v in b]
        cx = sum(p[0] for p in pts) / len(pts); cy = sum(p[1] for p in pts) / len(pts)
        half_w = (max(p[0] for p in pts) - min(p[0] for p in pts)) / 2
        toe = [f for f in feet if abs(f[0] - cx) < half_w * 0.8 and f[1] > cy - 1.2 and f[0] * side > 0]
        y0 = min(p[1] for p in pts); y1 = max(p[1] for p in pts)
        tip = max(f[1] for f in toe) - GAP
        s = FIXED if FIXED else max(0.6, min(1.0, (tip - y0) / (y1 - y0)))
        print('side %+d %-6s nail: length %.2f, overhang %.2f -> scale %.2f' % (side, name, y1 - y0, y1 - tip, s))
        for v, p in zip(b, pts): put(nd, v, (p[0], y0 + (p[1] - y0) * s, p[2]))
open(OUT, 'wb').write(nd)
