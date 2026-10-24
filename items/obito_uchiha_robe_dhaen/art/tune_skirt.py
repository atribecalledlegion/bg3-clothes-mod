"""Search for a back-of-skirt setup that keeps the legs covered in a run.

    python items/obito_uchiha_robe_dhaen/art/tune_skirt.py obito_uchiha_robe_dhaen

Each variant re-skins the back of the Dhaen robe's skirt in memory (no files written):
  ramp    half-width of the left/right leg blend across the back
  pelvis  share of the back's weight moved onto the pelvis, so it hangs from the hips and
          stops swinging with each leg (0 = follow the legs as Dhaen Extended has it)
  push    how far the back of the skirt is moved out (metres), growing toward the hem
  fat     how much the back is widened toward the hem (fraction)
and is scored with clip_check.py: body vertices newly outside the robe, over four run poses.
Skinning only (no cloth simulation), so the ranking is what matters, not the absolute numbers.
"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
import item as itemlib
import clip_check as cc
import pose_check as pc
from gltf_retarget import read

SKIRT_TOP, HEM = 0.62, 0.17


def smoothstep(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


def mirror(n):
    for a, b in (('_L', '_R'), ('_R', '_L')):
        if n.endswith(a):
            return n[:-2] + b
        if a + '_' in n:
            return n.replace(a + '_', b + '_')
    return None


def side(n):
    if mirror(n) is None:
        return None
    return 'L' if ('_L' in n and '_R' not in n) else 'R'


def load(path):
    g, acc = read(path)
    names = [n.get('name') for n in g['nodes']]
    jn = [names[j] for j in g['skins'][0]['joints']]
    p = g['meshes'][0]['primitives'][0]
    return (acc(p['attributes']['POSITION']).astype(float), acc(p['attributes']['JOINTS_0']).astype(int),
            acc(p['attributes']['WEIGHTS_0']).astype(float), jn)


def variant(base, ramp, pelvis, push, fat, taper=0.08, pelvis_bone='Root_M'):
    """taper: metres either side of the skirt's centre plane over which the change fades
    out, so the back joins the sides and front without tearing at the seams."""
    pos, J, W, jn = base
    index = {n: i for i, n in enumerate(jn)}
    pos, J, W = pos.copy(), J.copy(), W.copy()
    skirt = np.nonzero(pos[:, 1] < SKIRT_TOP)[0]
    zmid = np.median(pos[skirt, 2])
    for i in skirt:
        # the character faces -z (see clip_check.POSES), so the BACK is the +z side
        b = float(smoothstep((pos[i, 2] - zmid) / taper)) if taper > 0 else float(pos[i, 2] > zmid)
        if b <= 0:
            continue
        x, y = pos[i, 0], pos[i, 1]
        cur = {}
        for j, w in zip(J[i], W[i]):
            if w > 0:
                cur[jn[j]] = cur.get(jn[j], 0.0) + float(w)
        if ramp > 0 and len({side(n) for n in cur if side(n)}) == 1 and abs(x) < ramp + 0.06:
            as_r, as_l = {}, {}
            for n, w in cur.items():
                m = mirror(n)
                r = n if m is None or side(n) == 'R' else m
                l = n if m is None or side(n) == 'L' else m
                as_r[r] = as_r.get(r, 0.0) + w
                as_l[l] = as_l.get(l, 0.0) + w
            f = float(smoothstep((x + ramp) / (2 * ramp)))
            f0 = 1.0 if side(next(n for n in cur if side(n))) == 'L' else 0.0   # what it had
            f = f0 + (f - f0) * b
            cur = {}
            for n, w in as_r.items():
                cur[n] = cur.get(n, 0.0) + (1 - f) * w
            for n, w in as_l.items():
                cur[n] = cur.get(n, 0.0) + f * w
        if pelvis > 0:
            pm = pelvis * b
            cur = {n: w * (1 - pm) for n, w in cur.items()}
            cur[pelvis_bone] = cur.get(pelvis_bone, 0.0) + pm
        top = sorted(((w, n) for n, w in cur.items() if w > 1e-4), reverse=True)[:4]
        tot = sum(w for w, _ in top)
        Jn, Wn = np.zeros(4, int), np.zeros(4)
        for k, (w, n) in enumerate(top):
            Jn[k], Wn[k] = index[n], w / tot
        J[i], W[i] = Jn, Wn
        g = float(smoothstep((SKIRT_TOP - y) / (SKIRT_TOP - HEM))) * b
        pos[i, 2] += push * g
        pos[i, 0] *= 1 + fat * g
    return pos, J, W


def seams(rest_p, pose_p, idx):
    """Worst stretch anywhere on the skirt, and how far coincident vertices (the mesh is cut
    into pieces at its seams) are pulled apart: a torn seam shows as a gap."""
    skirt = rest_p[:, 1] < SKIRT_TOP
    edges = sorted({(min(u, v), max(u, v)) for a, b, c in idx for u, v in ((a, b), (b, c), (c, a))
                    if skirt[u] and skirt[v]})
    r = np.array([np.linalg.norm(pose_p[u] - pose_p[v]) / max(np.linalg.norm(rest_p[u] - rest_p[v]), 1e-6)
                  for u, v in edges])
    groups = {}
    for i in np.nonzero(skirt)[0]:
        groups.setdefault(tuple(np.round(rest_p[i], 3)), []).append(i)
    gap = 0.0
    for vs in groups.values():
        if len(vs) > 1:
            q = pose_p[vs]
            gap = max(gap, max(np.linalg.norm(a - b) for a in q for b in q))
    return np.percentile(r, 99), gap


def evaluate(base, robe_path, body, baselines, params):
    ov = variant(base, *params)
    tot_out = tot_holes = 0
    deepest = 0.0
    per = []
    for name, pose in cc.POSES.items():
        if name.startswith('rest'):
            continue
        n, holes, depth = cc.score(robe_path, body, pose, baselines[name], ov)
        tot_out += n; tot_holes += holes; deepest = max(deepest, depth); per.append(n)
    # stretch and torn seams over the WHOLE skirt in the worst of the poses
    e99, gap = 0.0, 0.0
    for name, pose in cc.POSES.items():
        if name.startswith('rest'):
            continue
        rest_p, pose_p, idx = pc.posed_vertices(robe_path, pose, ov)
        a, b = seams(rest_p, pose_p, idx)
        e99, gap = max(e99, a), max(gap, b)
    return tot_out, tot_holes, deepest, e99, gap, per


def main():
    it = itemlib.load()
    work = os.path.join(it.work, 'dhaen_patch')
    robe = os.path.join(work, 'original.gltf')
    body = os.path.abspath('extracted/dhaen/cmp/body_HUM_CHD_NKD_Body_A.gltf')
    base = load(robe)
    rest = {'Hip_R': 0, 'Hip_L': 0}
    baselines = {}
    for name, pose in cc.POSES.items():
        baselines[name] = cc.measure(robe, body, rest, None)[0]
    grid = [(0.0, 0.0, 0.0, 0.0, 0.0), (0.20, 0.0, 0.0, 0.0, 0.0)]
    for ramp in (0.0, 0.20):
        for pelvis in (0.5, 0.7, 0.85):
            for push in (0.03, 0.06, 0.09):
                for fat in (0.0, 0.15):
                    for taper in (0.06, 0.12):
                        grid.append((ramp, pelvis, push, fat, taper))
    rows = []
    for params in grid:
        rows.append((params,) + evaluate(base, robe, body, baselines, params))
    hdr = '%-40s %8s %6s %8s %8s %8s  %s' % ('ramp/pelvis/push/fat/taper', 'exposed', 'holes', 'deepest', 'stretch', 'seamgap', 'per pose')
    fmt = lambda r, extra='': '%-40s %8d %6d %6.1fcm %7.2fx %6.1fcm  %s%s' % (r[0], r[1], r[2], 100 * r[3], r[4], 100 * r[5], r[6], extra)
    print(hdr)
    print('-- references')
    for params, tag in (((0.0, 0.0, 0.0, 0.0, 0.0), 'as shipped'), ((0.20, 0.0, 0.0, 0.0, 0.0), 'current patch')):
        print(fmt(next(x for x in rows if x[0] == params), '   <- ' + tag))
    shipped = next(x for x in rows if x[0] == (0.0, 0.0, 0.0, 0.0, 0.0))
    ok = [r for r in rows if r[4] <= shipped[4] * 1.02 and r[5] <= shipped[5] * 1.05]
    ok.sort(key=lambda r: r[1])
    print('-- best 12 that stretch the skirt no more than the shipped one (%.2fx) and tear no seam more than it does (%.1f cm) (%d of %d qualify)' % (shipped[4], 100 * shipped[5], len(ok), len(rows)))
    for r in ok[:12]:
        print(fmt(r))


if __name__ == '__main__':
    main()
