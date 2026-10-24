"""Measure the legs poking out of the back of the robe, offline.

    python items/obito_uchiha_robe_dhaen/art/clip_check.py obito_uchiha_robe_dhaen [robe.gltf ...]

Poses the Dhaen body mesh (HUM_CHD_NKD_Body_A, shipped inside Dhaen Extended) and the robe
with the same bones in several run-stride poses, then looks at the skirt from behind: for
every body vertex between the hips and the hem it finds the outermost back surface of the
skirt over that spot. A body vertex is "out" when it sits behind that surface, or when no
skirt covers the spot at all (a hole). Reports how many, and the deepest.

This tests exactly what the game shows when a calf comes through, without the game.
Linear blend skinning only: no cloth simulation, so treat the numbers as relative.
"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
import item as itemlib
import pose_check as pc

CELL = 0.01
Y_LO, Y_HI = 0.22, 0.62      # from just above the hem to the hips
TOL = 0.004                  # body may sit this far behind the surface before it counts

# In these files the character FACES -z (toes at z=-0.13, the crest print at z=+0.11), so
# the BACK is +z. pose_check.rot_x(+theta) swings a hanging foot toward -z (forward), hence a
# leg going BACK needs a NEGATIVE hip angle, and a knee bent back a negative knee angle.
POSES = {
    'rest (sanity)':   {'Hip_R': 0, 'Hip_L': 0},
    'right leg back':  {'Hip_R': -35, 'Knee_R': -50, 'Hip_L': 30, 'Knee_L': -10},
    'left leg back':   {'Hip_L': -35, 'Knee_L': -50, 'Hip_R': 30, 'Knee_R': -10},
    'long stride':     {'Hip_R': -55, 'Knee_R': -70, 'Hip_L': 40, 'Knee_L': -15},
    'knee lifted':     {'Hip_R': 50, 'Knee_R': -80, 'Hip_L': -20, 'Knee_L': -5},
}


def back_surface(pos, idx, x0, y0, nx, ny):
    """Outermost skirt depth per XY cell seen from behind (the back is +z, so the largest
    z); -inf where no back-layer triangle covers the cell."""
    zmin = np.full((ny, nx), -np.inf)
    for a, b, c in idx:
        p = pos[[a, b, c]]
        gx = (p[:, 0] - x0) / CELL
        gy = (p[:, 1] - y0) / CELL
        xmin, xmax = max(int(np.floor(gx.min())), 0), min(int(np.ceil(gx.max())), nx - 1)
        ymin, ymax = max(int(np.floor(gy.min())), 0), min(int(np.ceil(gy.max())), ny - 1)
        if xmax < xmin or ymax < ymin:
            continue
        den = (gy[1] - gy[2]) * (gx[0] - gx[2]) + (gx[2] - gx[1]) * (gy[0] - gy[2])
        if abs(den) < 1e-12:
            continue
        X, Y = np.meshgrid(np.arange(xmin, xmax + 1) + 0.5, np.arange(ymin, ymax + 1) + 0.5)
        l0 = ((gy[1] - gy[2]) * (X - gx[2]) + (gx[2] - gx[1]) * (Y - gy[2])) / den
        l1 = ((gy[2] - gy[0]) * (X - gx[2]) + (gx[0] - gx[2]) * (Y - gy[2])) / den
        l2 = 1 - l0 - l1
        ins = (l0 >= 0) & (l1 >= 0) & (l2 >= 0)
        if not ins.any():
            continue
        z = l0 * p[0, 2] + l1 * p[1, 2] + l2 * p[2, 2]
        sl = (slice(ymin, ymax + 1), slice(xmin, xmax + 1))
        cur = zmin[sl]
        cur[ins] = np.maximum(cur[ins], z[ins])
        zmin[sl] = cur
    return zmin


def measure(robe_path, body_path, pose, override=None):
    rest_r, pr, idx = pc.posed_vertices(robe_path, pose, override)
    rest_b, pb, _ = pc.posed_vertices(body_path, pose)
    # the back layer of the skirt = triangles that are behind the body's centre plane at
    # rest; the front panel (and its slit) is irrelevant from behind
    idx = idx[rest_r[idx][:, :, 2].mean(1) > 0.0]
    sel = (rest_b[:, 1] > Y_LO) & (rest_b[:, 1] < Y_HI)
    pts = pb[sel]
    x0 = min(pr[:, 0].min(), pts[:, 0].min()) - 0.05
    y0 = min(pr[:, 1].min(), pts[:, 1].min()) - 0.05
    nx = int((max(pr[:, 0].max(), pts[:, 0].max()) + 0.05 - x0) / CELL) + 2
    ny = int((max(pr[:, 1].max(), pts[:, 1].max()) + 0.05 - y0) / CELL) + 2
    zmin = back_surface(pr, idx, x0, y0, nx, ny)
    cx = np.clip(((pts[:, 0] - x0) / CELL).astype(int), 0, nx - 1)
    cy = np.clip(((pts[:, 1] - y0) / CELL).astype(int), 0, ny - 1)
    surf = zmin[cy, cx]
    hole = ~np.isfinite(surf)
    # only vertices on the BACK half of the leg (+z) can show through the back of the skirt
    back = pts[:, 2] > np.median(pts[:, 2])
    poke = np.where(hole, 0.0, pts[:, 2] - surf)
    out = back & (hole | (poke > TOL))
    return out, poke, hole, np.nonzero(sel)[0]


def score(robe_path, body_path, pose, baseline, override=None):
    """Vertices newly outside the robe compared with the rest pose (the front slit and the
    open sides show the leg by design), and the deepest of them."""
    out, poke, hole, ids = measure(robe_path, body_path, pose, override)
    new = out & ~baseline
    depth = poke[new & ~hole]
    return int(new.sum()), int((new & hole).sum()), (depth.max() if len(depth) else 0.0)


def main():
    it = itemlib.load()
    work = os.path.join(it.work, 'dhaen_patch')
    body = os.path.abspath('extracted/dhaen/cmp/body_HUM_CHD_NKD_Body_A.gltf')
    robes = sys.argv[2:] or [os.path.join(work, 'original.gltf'), os.path.join(work, 'check.gltf')]
    rest = {'Hip_R': 0, 'Hip_L': 0}
    base = {r: measure(r, body, rest)[0] for r in robes}
    print('back-of-leg body vertices newly outside the robe, compared with standing still')
    print('(%d body vertices between hem and hips are on the back of the leg)' % int(next(iter(base.values())).size and 0 or 0)
          if False else '')
    print('%-16s' % 'pose' + ''.join('%-40s' % os.path.basename(r) for r in robes))
    for name, pose in POSES.items():
        if name.startswith('rest'):
            continue
        row = '%-16s' % name
        for r in robes:
            n, holes, depth = score(r, body, pose, base[r])
            row += '%-40s' % ('%d out (%d through holes), deepest %.1f cm' % (n, holes, 100 * depth))
        print(row)


if __name__ == '__main__':
    main()
