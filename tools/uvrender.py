"""Rasterise a mesh's UV layout, optionally colouring triangles by world-space region."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uvmap import load

def raster(tris, size, colour_fn, flip_v):
    buf = bytearray(size * size * 3)
    for t in tris:
        c = colour_fn(t)
        if c is None:
            continue
        pts = []
        for _, _, uv in t:
            u, v = uv[0], uv[1]
            if flip_v:
                v = 1.0 - v
            pts.append((u * (size - 1), v * (size - 1)))
        ys = [p[1] for p in pts]
        y0, y1 = max(0, int(min(ys))), min(size - 1, int(max(ys)) + 1)
        for y in range(y0, y1 + 1):
            xs = []
            for i in range(3):
                (xa, ya), (xb, yb) = pts[i], pts[(i + 1) % 3]
                if (ya <= y < yb) or (yb <= y < ya):
                    xs.append(xa + (y - ya) * (xb - xa) / (yb - ya))
            if len(xs) < 2:
                continue
            for x in range(max(0, int(min(xs))), min(size - 1, int(max(xs))) + 1):
                i = (y * size + x) * 3
                buf[i], buf[i+1], buf[i+2] = c
    return buf

if __name__ == '__main__':
    dae, geom, out, size, mode = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5]
    flip = len(sys.argv) > 6 and sys.argv[6] == 'flip'
    tris = load(dae, geom)
    def cy(t): return sum(v[0][1] for v in t) / 3.0
    def nz(t): return sum(v[1][2] for v in t) / 3.0
    if mode == 'all':
        fn = lambda t: (255, 255, 255)
    elif mode == 'zsign':
        def fn(t):
            n = nz(t)
            if n < -0.35: return (230, 60, 60)      # facing -Z
            if n >  0.35: return (60, 110, 230)     # facing +Z
            return (90, 90, 90)
    elif mode == 'height':
        def fn(t):
            y = cy(t); lo, hi = 0.26, 1.73
            f = (y - lo) / (hi - lo)
            return (int(40 + 215 * f), int(255 * (1 - abs(f - .5) * 2)), int(255 - 215 * f))
    open(out, 'wb').write(bytes(raster(tris, size, fn, flip)))
    print('wrote', out, size)
