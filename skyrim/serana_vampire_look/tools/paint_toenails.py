"""Paint black toenails onto the body texture (feet are UV-mapped into its top band), using the fitted toenail mesh
as a stencil: every nail vertex takes the UV of the feet surface under it (inverse-distance blend of the 3 nearest
feet vertices); each nail's UV points are wrapped in a convex hull, shrunk a little, and filled near-black.
usage: paint_toenails.py <feet.nif> <nails.nif> <body_in.png> <body_out.png> [shrink]"""
import sys, os, math, struct
from PIL import Image, ImageDraw, ImageFilter
here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, 'fit_toenails.py'), encoding='utf-8').read()
ns = {}; exec(compile(src[:src.index('NAIL_VERTS =')], 'fit', 'exec'), ns)
parse, get = ns['parse'], ns['get']
FEET, NAILS, BODY_IN, BODY_OUT = sys.argv[1:5]
SHRINK = float(sys.argv[5]) if len(sys.argv) > 5 else 0.9
COLOR = (16, 16, 20)

def half(h): return struct.unpack('<e', struct.pack('<H', h))[0]
fd, fs = parse(FEET)
fverts = [v for n, vs in fs for v in vs]
fpos = [get(fd, v) for v in fverts]
fuv = [tuple(half(h) for h in struct.unpack_from('<2H', fd, off + 16)) for kind, off in fverts]   # UV at +16 (checked)
nd, nshapes = parse(NAILS)
nverts = [v for n, vs in nshapes for v in vs]

def uv_at(p):
    """UV of the nearest feet vertex (blending neighbours mixed UVs across the toe seam)."""
    i = min(range(len(fpos)), key=lambda i: (fpos[i][0]-p[0])**2 + (fpos[i][1]-p[1])**2 + (fpos[i][2]-p[2])**2)
    return fuv[i]

def inliers(uvs, tol=0.012):
    """Drop points that jumped to another UV island: keep those near the median of the nail."""
    mu = sorted(u for u, v in uvs)[len(uvs) // 2]; mv = sorted(v for u, v in uvs)[len(uvs) // 2]
    return [(u, v) for u, v in uvs if abs(u - mu) < tol and abs(v - mv) < tol]

def hull(pts):
    pts = sorted(set(pts))
    if len(pts) < 3: return pts
    def cross(o, a, b): return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]

img = Image.open(BODY_IN).convert('RGBA'); W, H = img.size
mask = Image.new('L', (W * 2, H * 2), 0); dr = ImageDraw.Draw(mask)      # 2x supersampled mask
NV = 194
# ovals, not hulls: the mesh nails of neighbouring toes overlapped, so their outlines merged. Each nail is an oval at
# its projected centre, sized per toe (big toe largest), in UV units (half width, half height).
SIZES = {'big': (0.0085, 0.0070), 'second': (0.0058, 0.0050), 'middle': (0.0054, 0.0047), 'ring': (0.0050, 0.0043),
         'pinky': (0.0042, 0.0037)}
# nail centres read off the toe lobes of the body texture (the projected mesh nails sat between toes 2/3 and off the
# pinky); u for the x<0 foot, the other foot is mirrored (u -> 1 - u, checked symmetric)
TOE_UV = {'big': (0.7556, 0.2038), 'second': (0.7821, 0.2088), 'middle': (0.8013, 0.2081), 'ring': (0.8181, 0.2038),
          'pinky': (0.8331, 0.1988)}
blocks = [nverts[k:k + NV] for k in range(0, len(nverts), NV)]
for side in (-1, 1):
    mine = [b for b in blocks if get(nd, b[0])[0] * side > 0]
    mine.sort(key=lambda b: abs(sum(get(nd, v)[0] for v in b) / len(b)))
    for name, block in zip(['big', 'second', 'middle', 'ring', 'pinky'], mine):
        uvs = inliers([uv_at(get(nd, v)) for v in block])
        cu = sum(u for u, v in uvs) / len(uvs); cv = sum(v for u, v in uvs) / len(uvs)
        if name in TOE_UV:                       # placed by eye on each toe lobe of the texture (feet are mirrored)
            cu, cv = TOE_UV[name]
            if side > 0: cu = 1.0 - cu
        hw, hh = SIZES[name]
        dr.ellipse([(cu - hw) * W * 2, (cv - hh) * H * 2, (cu + hw) * W * 2, (cv + hh) * H * 2], fill=255)
        print('side %+d %-6s nail at uv (%.4f, %.4f)' % (side, name, cu, cv))
# round the hull corners (blur + threshold), then a light blur for a soft painted edge
mask = mask.filter(ImageFilter.GaussianBlur(1.2)).resize((W, H), Image.LANCZOS)
black = Image.new('RGBA', (W, H), COLOR + (255,))
out = Image.composite(black, img, mask)
out.putalpha(img.getchannel('A'))                                           # keep the specular/alpha channel
out.save(BODY_OUT)
print('wrote', BODY_OUT)
