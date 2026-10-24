"""Per-toe touch-ups of the fitted toenails (user feedback 2026-10-15), measured from the feet mesh:
  big toe  : forward (+y) until the nail's front edge sits just behind the toe tip
  ring toe : up (+z) until the nail's top sits just above the toe's top
  pinky    : sideways (x) to the toe's centre
Nails are the 194-vertex blocks of fit_toenails.py; per foot they are ordered by |x| (big toe nearest the middle).
usage: adjust_toenails.py <feet.nif> <nails_in.nif> <nails_out.nif>"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
argv = sys.argv[:]; sys.argv = [argv[0], argv[1], argv[2], os.devnull, '0']   # reuse fit_toenails' parser only
import importlib.util
spec = importlib.util.spec_from_file_location('fit', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fit_toenails.py'))
src = open(spec.origin, encoding='utf-8').read()
src = src[:src.index('PER_NAIL =')] if 'PER_NAIL =' in src else src
ns = {}; exec(compile(src[:src.index('NAIL_VERTS =')] if 'NAIL_VERTS =' in src else src, 'fit', 'exec'), ns)
parse, get, put = ns['parse'], ns['get'], ns['put']
FEET, IN, OUT = argv[1:4]
fd, fs = parse(FEET); nd, nshapes = parse(IN)
feet = [get(fd, v) for n, vs in fs for v in vs]
verts = [v for n, vs in nshapes for v in vs]
NV = 194
blocks = [verts[k:k + NV] for k in range(0, len(verts), NV)]
TIP_GAP, TOP_LIFT = 0.15, 0.05
for side in (-1, 1):
    nails = [b for b in blocks if get(nd, b[0])[0] * side > 0]
    nails.sort(key=lambda b: abs(sum(get(nd, v)[0] for v in b) / len(b)))
    names = ['big', 'second', 'middle', 'ring', 'pinky']
    for name, b in zip(names, nails):
        pts = [get(nd, v) for v in b]
        cx = sum(p[0] for p in pts) / len(pts); cy = sum(p[1] for p in pts) / len(pts)
        half_w = (max(p[0] for p in pts) - min(p[0] for p in pts)) / 2
        toe = [f for f in feet if abs(f[0] - cx) < half_w * 1.1 and f[1] > cy - 1.2 and f[0] * side > 0]
        d = [0.0, 0.0, 0.0]
        if name == 'big' and toe:
            d[1] = (max(f[1] for f in toe) - TIP_GAP) - max(p[1] for p in pts)
        elif name == 'ring' and toe:
            near = [f for f in toe if abs(f[1] - cy) < 0.4]
            if near: d[2] = (max(f[2] for f in near) + TOP_LIFT) - max(p[2] for p in pts)
        elif name == 'pinky' and toe:
            band = [f for f in feet if abs(f[1] - cy) < 0.35 and abs(f[0] - cx) < half_w * 2.2 and f[0] * side > 0]
            if band: d[0] = (min(f[0] for f in band) + max(f[0] for f in band)) / 2 - cx
        d = [max(-0.8, min(0.8, x)) for x in d]                       # never jump more than 0.8 units
        print('side %+d %-6s nail: move (%.2f %.2f %.2f)  [%d toe points]' % (side, name, d[0], d[1], d[2], len(toe)))
        for v, p in zip(b, pts): put(nd, v, (p[0] + d[0], p[1] + d[1], p[2] + d[2]))
open(OUT, 'wb').write(nd)
