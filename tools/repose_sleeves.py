"""Rotate a garment's sleeves onto the target skeleton's arm direction.

    python tools/repose_sleeves.py in.obj out.obj --shoulder 0.20 0.45 -0.01 \
        --target 0.461 -0.298 -0.101 --blend 0.04 0.16

Imported character models stand however the artist posed them -- the naruto-r model has
its arms hanging 7 degrees from vertical. BG3's skeleton rests with the arms 58 degrees
out. Bone weights are transferred by matching surfaces in the REST pose, so sleeves in the
wrong pose take weights from whatever vanilla geometry happens to be nearby (the chest,
usually) and deform into the body as soon as the character moves.

This rotates each sleeve about its shoulder so it lies along the target arm direction,
mirroring the shoulder/target for the other side. The rotation fades in over --blend
(distance from the shoulder, in model units) so the torso is untouched and the shoulder
itself bends rather than shearing off.

Only positions and normals are changed: UVs are untouched, so the texture still fits.
"""
import argparse
import numpy as np


def rotation(a, b):
    """Rotation matrix taking unit vector a to unit vector b."""
    v = np.cross(a, b)
    c = float(np.dot(a, b))
    if np.linalg.norm(v) < 1e-9:
        return np.eye(3) if c > 0 else -np.eye(3)
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + vx + vx @ vx * (1 / (1 + c))


def slerp_rot(R, t):
    """R applied fractionally (t=0 identity, t=1 full), via axis-angle."""
    ang = np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1))
    if ang < 1e-9:
        return np.eye(3)
    axis = np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]]) / (2 * np.sin(ang))
    a = ang * t
    K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src'); ap.add_argument('out')
    ap.add_argument('--shoulder', nargs=3, type=float, required=True,
                    help='shoulder joint of the +X side, in model space')
    ap.add_argument('--target', nargs=3, type=float, required=True,
                    help='target arm direction of the +X side (shoulder -> wrist)')
    ap.add_argument('--torso-half', type=float, required=True,
                    help="body half width: vertices further out than this are sleeve")
    ap.add_argument('--length', type=float, default=0.60,
                    help='how far down the arm axis the sleeve reaches')
    ap.add_argument('--blend', nargs=2, type=float, default=[0.04, 0.16],
                    help='rotation fades in between these distances from the shoulder')
    a = ap.parse_args()

    lines = open(a.src).read().splitlines()
    V, N, rest = [], [], []
    for ln in lines:
        if ln.startswith('v '):
            V.append([float(x) for x in ln.split()[1:]])
        elif ln.startswith('vn '):
            N.append([float(x) for x in ln.split()[1:]])
    V = np.array(V); N = np.array(N) if N else None
    target = np.array(a.target, float)
    target /= np.linalg.norm(target)

    moved = 0
    for sgn in (+1, -1):
        sh = np.array(a.shoulder, float) * np.array([sgn, 1, 1])
        tgt = target * np.array([sgn, 1, 1])
        # First estimate the arm's axis from the outer half, then keep only what lies
        # along it: the SLEEVE is a tube around that axis. Selecting the whole side
        # instead drags the hem and chest round with the arm and flattens the jacket.
        # The sleeve is what lies OUTSIDE the torso on this side. With the arms hanging
        # nearly vertically, a tube around the arm axis also contains the torso's flank
        # and hem, and rotating those splays the jacket out like a skirt. --torso-half is
        # the body's half width (measure it: half width by height band).
        outer = (V[:, 0] * sgn) > a.torso_half
        seed = V[outer] - sh
        cur = seed[seed[:, 1] < -0.05].mean(0)
        cur /= np.linalg.norm(cur)
        rel_all = V - sh
        along = rel_all @ cur
        side = outer & (along > 0) & (along < a.length)
        rel = rel_all[side]
        R = rotation(cur, tgt)
        d = np.linalg.norm(rel, axis=1)
        t = np.clip((d - a.blend[0]) / (a.blend[1] - a.blend[0]), 0, 1)
        t = t * t * (3 - 2 * t)                            # smoothstep
        out = rel.copy()
        for i in range(len(rel)):
            if t[i] > 0:
                out[i] = slerp_rot(R, t[i]) @ rel[i]
        V[side] = out + sh
        moved += int((t > 0).sum())
        print('side %+d: arm %s -> %s  (%d vertices rotated)'
              % (sgn, np.round(cur, 3), np.round(tgt, 3), (t > 0).sum()))

    vi = ni = 0
    with open(a.out, 'w') as f:
        for ln in lines:
            if ln.startswith('v '):
                f.write('v %.6f %.6f %.6f\n' % tuple(V[vi])); vi += 1
            elif ln.startswith('vn '):
                # normals are left alone: the fit step recomputes shading from geometry,
                # and a wrong normal is less visible than a wrong position
                f.write(ln + '\n'); ni += 1
            else:
                f.write(ln + '\n')
    print('wrote %s (%d vertices moved)' % (a.out, moved))


if __name__ == '__main__':
    main()
