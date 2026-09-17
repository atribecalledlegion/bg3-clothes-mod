"""Derive where the Uchiha crest goes on a BG3 robe texture, from the mesh itself.

    python tools/crestplace.py <mesh.dae> <geometry-name> [crest_w crest_h crest_d]

Method:
  1. Pick the back bodice: triangles facing +Z (the back -- the front carries the V-neck),
     on the outer surface, in the upper part of the mesh.
  2. Keep the dominant UV island, discarding strays from interior/lining faces.
  3. Least-squares fit affine (worldX, worldY) -> (u, v) over the FLAT central patch only.
     Fitting the whole panel includes the shoulders and collar, where the unwrap curves
     away, and the residual blows up from ~1px to ~165px.
  4. Landmarks: collar top and waist are the island's Y extremes. The reference art puts
     the crest centre 0.483 of the way from collar to waist, with a diameter 0.281 of the
     same span.
  5. Map centre and diameter through the fit. The panel is unwrapped rotated, so the
     crest image must be rotated to match -- the report says by how much.
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uvmap import load
from fitpanel import fit

FRAC_Y, FRAC_D = 0.483, 0.281      # measured from obito_uchiha_robe_back_profile.jpg
S = 2048

def derive(dae, geom):
    tris = load(dae, geom)
    def c(t, i): return sum(v[0][i] for v in t)/3
    def nz(t):  return sum(v[1][2] for v in t)/3
    def cu(t):  return sum(v[2][0] for v in t)/3
    def cv(t):  return sum(1.0-v[2][1] for v in t)/3
    ys = [v[0][1] for t in tris for v in t]
    lo, hi = min(ys), max(ys)
    sel = [t for t in tris if nz(t) > 0.5 and c(t,2) > 0.03
           and lo + 0.55*(hi-lo) <= c(t,1) <= lo + 0.99*(hi-lo)]
    # Group the selection into UV-connected islands and keep the largest. Hardcoding a
    # UV region does not work: the masculine and feminine robes use different layouts
    # (the feminine back panel sits top-left and is not rotated; the masculine one sits
    # right and is rotated 90 degrees).
    parent = list(range(len(sel)))
    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a
    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb: parent[ra] = rb
    seen = {}
    for i, t in enumerate(sel):
        for _, _, uv in t:
            k = (round(uv[0], 5), round(uv[1], 5))
            if k in seen: union(i, seen[k])
            else: seen[k] = i
    groups = {}
    for i in range(len(sel)):
        groups.setdefault(find(i), []).append(sel[i])
    isl = max(groups.values(), key=len)
    iy = [v[0][1] for t in isl for v in t]
    collar, waist = max(iy), min(iy)
    span = collar - waist

    # flat central patch for the fit
    xs = [abs(v[0][0]) for t in isl for v in t]
    XL = sorted(xs)[len(xs)//3]
    patch = [t for t in isl if abs(c(t,0)) < XL and nz(t) > 0.8
             and waist + 0.25*span <= c(t,1) <= waist + 0.85*span]
    P = [(v[0][0], v[0][1], v[2][0], 1.0-v[2][1]) for t in patch for v in t]
    au, av = fit(P)
    rms = math.sqrt(sum((au[0]*p[0]+au[1]*p[1]+au[2]-p[2])**2 +
                        (av[0]*p[0]+av[1]*p[1]+av[2]-p[3])**2 for p in P)/len(P))
    ex = (au[0], av[0]); ey = (au[1], av[1])
    sx, sy = math.hypot(*ex)*S, math.hypot(*ey)*S

    cy = collar - FRAC_Y*span
    dw = FRAC_D*span
    u = au[0]*0 + au[1]*cy + au[2]
    v = av[0]*0 + av[1]*cy + av[2]
    # garment "up" is world +Y; its direction in texture pixels
    upx, upy = ey[0], ey[1]
    rot = math.degrees(math.atan2(-upy, upx))   # 90 == up stays up in image terms
    return dict(collar=collar, waist=waist, span=span, rms=rms*S, sx=sx, sy=sy,
                cy=cy, dw=dw, cx_px=u*S, cy_px=v*S, d_px=dw*((sx+sy)/2),
                rot=rot, iso=sy/sx, tris=len(isl),
                island=(min(v[2][0] for t in isl for v in t)*S,
                        max(v[2][0] for t in isl for v in t)*S,
                        min(1.0-v[2][1] for t in isl for v in t)*S,
                        max(1.0-v[2][1] for t in isl for v in t)*S))

if __name__ == '__main__':
    dae, geom = sys.argv[1], sys.argv[2]
    r = derive(dae, geom)
    print('%s :: %s' % (os.path.basename(dae), geom))
    print('  back island      %d tris   px x %.0f..%.0f  y %.0f..%.0f' % ((r['tris'],) + r['island']))
    print('  collar Y %.3f   waist Y %.3f   span %.3f' % (r['collar'], r['waist'], r['span']))
    print('  affine fit rms   %.1f px      scale %.0f x %.0f px/unit   isotropy %.3f'
          % (r['rms'], r['sx'], r['sy'], r['iso']))
    print('  garment "up" points %.0f deg in texture space' % r['rot'])
    print('  CREST  centre (%.0f, %.0f) px   diameter %.0f px'
          % (r['cx_px'], r['cy_px'], r['d_px']))
    # paste geometry for a 1024x1360 crest whose circle is 900px centred at (512,512)
    SRC_W, SRC_H, SRC_D, SCX, SCY = 1024, 1360, 900.0, 512.0, 512.0
    s = r['d_px']/SRC_D
    w, h = round(SRC_W*s), round(SRC_H*s)
    ccx, ccy = SCX*s, SCY*s
    if abs(r['rot'] - 0) < 45:        # up -> +u : rotate image 90 clockwise
        rcx, rcy, rot = (h-1-ccy), ccx, 90
    else:
        rcx, rcy, rot = ccx, ccy, 0
    print('  PASTE  resize %dx%d  rotate %d  offset +%d+%d'
          % (w, h, rot, round(r['cx_px']-rcx), round(r['cy_px']-rcy)))
