"""Least-squares affine fit of world (X,Y) -> UV over a selected patch of a mesh."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uvmap import load

def fit(P):
    n = len(P)
    Sx = sum(p[0] for p in P); Sy = sum(p[1] for p in P)
    Sxx = sum(p[0]*p[0] for p in P); Syy = sum(p[1]*p[1] for p in P); Sxy = sum(p[0]*p[1] for p in P)
    def solve(k):
        St = sum(p[k] for p in P)
        A = [[Sxx, Sxy, Sx], [Sxy, Syy, Sy], [Sx, Sy, n]]
        B = [sum(p[0]*p[k] for p in P), sum(p[1]*p[k] for p in P), St]
        for i in range(3):
            pv = max(range(i, 3), key=lambda r: abs(A[r][i]))
            A[i], A[pv] = A[pv], A[i]; B[i], B[pv] = B[pv], B[i]
            for r in range(3):
                if r == i: continue
                f = A[r][i]/A[i][i]
                for cc in range(3): A[r][cc] -= f*A[i][cc]
                B[r] -= f*B[i]
        return [B[i]/A[i][i] for i in range(3)]
    return solve(2), solve(3)

def report(au, av, P):
    n = len(P)
    rms = math.sqrt(sum((au[0]*p[0]+au[1]*p[1]+au[2]-p[2])**2 +
                        (av[0]*p[0]+av[1]*p[1]+av[2]-p[3])**2 for p in P)/n)
    ex = (au[0], av[0]); ey = (au[1], av[1])
    return rms, ex, ey

if __name__ == '__main__':
    tris = load(sys.argv[1], sys.argv[2])
    XL, YLO, YHI, NZ = float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6])
    def c(t, i): return sum(v[0][i] for v in t)/3
    def nz(t):  return sum(v[1][2] for v in t)/3
    sel = [t for t in tris if nz(t) > NZ and c(t,2) > 0.05
           and YLO <= c(t,1) <= YHI and abs(c(t,0)) < XL]
    P = [(v[0][0], v[0][1], v[2][0], 1.0-v[2][1]) for t in sel for v in t]
    au, av = fit(P)
    rms, ex, ey = report(au, av, P)
    S = 2048
    print('patch: %d tris, %d verts   |X|<%.2f  Y %.2f..%.2f  nz>%.2f' % (len(sel), len(P), XL, YLO, YHI, NZ))
    print('u = %+.5f*X %+.5f*Y %+.5f' % tuple(au))
    print('v = %+.5f*X %+.5f*Y %+.5f' % tuple(av))
    print('fit rms %.5f uv = %.1f px' % (rms, rms*S))
    print('world +X -> %8.1f px/unit   dir (%+.3f,%+.3f)' % (math.hypot(*ex)*S, ex[0]/math.hypot(*ex), ex[1]/math.hypot(*ex)))
    print('world +Y -> %8.1f px/unit   dir (%+.3f,%+.3f)' % (math.hypot(*ey)*S, ey[0]/math.hypot(*ey), ey[1]/math.hypot(*ey)))
    print('orthogonality cos %.4f   anisotropy %.3f' % (
        (ex[0]*ey[0]+ex[1]*ey[1])/(math.hypot(*ex)*math.hypot(*ey)), math.hypot(*ey)/math.hypot(*ex)))
