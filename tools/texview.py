"""Texture-map a COLLADA mesh from +Z or -Z to check where a texture region lands."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uvmap import load

def render(tris, tex, TS, size, back=True, X=(-0.55, 0.55), Y=(0.25, 1.75)):
    buf = bytearray(size * size * 3)
    zbuf = [-1e9] * (size * size)
    for t in tris:
        n = sum(v[1][2] for v in t) / 3.0
        if (back and n < 0.05) or (not back and n > -0.05):
            continue
        P = []
        for pos, _, uv in t:
            x = (pos[0] - X[0]) / (X[1] - X[0])
            if back:
                x = 1.0 - x
            y = 1.0 - (pos[1] - Y[0]) / (Y[1] - Y[0])
            P.append((x * (size - 1), y * (size - 1), pos[2], uv[0], 1.0 - uv[1]))
        xs = [p[0] for p in P]; ys = [p[1] for p in P]
        x0, x1 = max(0, int(min(xs))), min(size - 1, int(max(xs)) + 1)
        y0, y1 = max(0, int(min(ys))), min(size - 1, int(max(ys)) + 1)
        ax, ay = P[0][0], P[0][1]
        d = (P[1][1]-P[2][1])*(P[0][0]-P[2][0]) + (P[2][0]-P[1][0])*(P[0][1]-P[2][1])
        if abs(d) < 1e-9:
            continue
        for py in range(y0, y1 + 1):
            for px in range(x0, x1 + 1):
                w0 = ((P[1][1]-P[2][1])*(px-P[2][0]) + (P[2][0]-P[1][0])*(py-P[2][1])) / d
                w1 = ((P[2][1]-P[0][1])*(px-P[2][0]) + (P[0][0]-P[2][0])*(py-P[2][1])) / d
                w2 = 1.0 - w0 - w1
                if w0 < -0.001 or w1 < -0.001 or w2 < -0.001:
                    continue
                z = w0*P[0][2] + w1*P[1][2] + w2*P[2][2]
                if not back:
                    z = -z
                i = py*size + px
                if z <= zbuf[i]:
                    continue
                zbuf[i] = z
                u = w0*P[0][3] + w1*P[1][3] + w2*P[2][3]
                v = w0*P[0][4] + w1*P[1][4] + w2*P[2][4]
                tx = min(TS-1, max(0, int(u*(TS-1)))); ty = min(TS-1, max(0, int(v*(TS-1))))
                k = (ty*TS + tx)*3
                j = i*3
                buf[j], buf[j+1], buf[j+2] = tex[k], tex[k+1], tex[k+2]
    return buf

if __name__ == '__main__':
    dae, geom, texraw, TS, out, size, side = sys.argv[1:8]
    tex = open(texraw, 'rb').read()
    b = render(load(dae, geom), tex, int(TS), int(size), back=(side == 'back'))
    open(out, 'wb').write(bytes(b))
    print('wrote', out)
