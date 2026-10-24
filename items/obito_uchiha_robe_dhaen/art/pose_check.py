"""Offline check for the robe's skirt: pose the legs in a run stride and measure how far
the back of the skirt stretches open, for the original weights and the patched ones.

    python items/obito_uchiha_robe_dhaen/art/pose_check.py obito_uchiha_robe_dhaen

Linear blend skinning in numpy, no game needed. It measures the skirt itself (edge stretch
across the back seam), not the legs, so it says whether the tear is gone, not whether
every last clip is.
"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
import item as itemlib
from gltf_retarget import read


def local_mat(node):
    if 'matrix' in node:
        return np.array(node['matrix'], float).reshape(4, 4).T
    T = np.eye(4); R = np.eye(4); S = np.eye(4)
    if 'translation' in node:
        T[:3, 3] = node['translation']
    if 'rotation' in node:
        x, y, z, w = node['rotation']
        R[:3, :3] = [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]
    if 'scale' in node:
        S[0, 0], S[1, 1], S[2, 2] = node['scale']
    return T @ R @ S


def rot_x(theta):
    c, s = np.cos(theta), np.sin(theta)
    return np.array([[1, 0, 0, 0], [0, c, -s, 0], [0, s, c, 0], [0, 0, 0, 1]], float)


def posed_vertices(path, pose, override=None):
    """pose: {bone name: degrees about the world X axis (positive swings the foot back)}.
    override: optional (positions, joints, weights) to skin instead of the file's own."""
    g, acc = read(path)
    nodes = g['nodes']
    parent = {}
    for i, n in enumerate(nodes):
        for c in n.get('children', []):
            parent[c] = i
    world = [None] * len(nodes)

    def rest(i):
        if world[i] is None:
            world[i] = (rest(parent[i]) if i in parent else np.eye(4)) @ local_mat(nodes[i])
        return world[i]
    for i in range(len(nodes)):
        rest(i)
    names = [n.get('name') for n in nodes]
    by_name = {n: i for i, n in enumerate(names)}

    posed = [w.copy() for w in world]
    # apply top-down so a knee inherits its hip's swing
    order = sorted(pose, key=lambda b: len(_chain(by_name[b], parent)))
    for bone in order:
        i = by_name[bone]
        pivot = world[i][:3, 3]
        T = np.eye(4); T[:3, 3] = pivot
        Ti = np.eye(4); Ti[:3, 3] = -pivot
        P = T @ rot_x(np.radians(pose[bone])) @ Ti
        for j in range(len(nodes)):
            if i in _chain(j, parent):
                posed[j] = P @ posed[j]

    skin = g['skins'][0]
    ibm = acc(skin['inverseBindMatrices']).reshape(-1, 4, 4).astype(float).transpose(0, 2, 1)
    mesh_node = next(i for i, n in enumerate(nodes) if 'mesh' in n)
    inv_mesh = np.linalg.inv(world[mesh_node])
    joints = skin['joints']
    p = g['meshes'][0]['primitives'][0]
    pos = acc(p['attributes']['POSITION']).astype(float)
    J, W = acc(p['attributes']['JOINTS_0']), acc(p['attributes']['WEIGHTS_0'])
    idx = acc(p['indices']).reshape(-1, 3).astype(int)
    if override is not None:
        pos, J, W = override
        pos = pos.astype(float)
    skin_m = np.array([inv_mesh @ posed[joints[k]] @ ibm[k] for k in range(len(joints))])
    h = np.c_[pos, np.ones(len(pos))]
    out = np.zeros_like(pos)
    for k in range(4):
        m = skin_m[J[:, k].astype(int)]                       # (N, 4, 4) matrix of influence k
        out += W[:, k, None].astype(float) * np.einsum('nij,nj->ni', m, h)[:, :3]
    return pos, out, idx


def _chain(i, parent):
    c = set()
    while i is not None:
        c.add(i)
        i = parent.get(i)
    return c


def stretch(path, pose, label):
    """How far the back of the skirt comes apart: (a) coincident vertices -- the mesh is
    cut into pieces at its seams, so a hard weight step there tears the pieces apart --
    and (b) how much the ordinary edges stretch."""
    rest_p, pose_p, idx = posed_vertices(path, pose)
    skirt = rest_p[:, 1] < 0.62
    zmid = np.median(rest_p[skirt, 2])
    back = skirt & (rest_p[:, 2] < zmid)

    groups = {}
    for i in np.nonzero(back)[0]:
        groups.setdefault(tuple(np.round(rest_p[i], 4)), []).append(i)
    gaps = []
    for vs in groups.values():
        if len(vs) > 1:
            pts = pose_p[vs]
            gaps.append(max(np.linalg.norm(a - b) for a in pts for b in pts))
    gaps = np.array(gaps) if gaps else np.zeros(1)

    edges = sorted({(min(u, v), max(u, v)) for a, b, c in idx for u, v in ((a, b), (b, c), (c, a))
                    if back[u] and back[v]})
    r = np.array([np.linalg.norm(pose_p[u] - pose_p[v]) / max(np.linalg.norm(rest_p[u] - rest_p[v]), 1e-6)
                  for u, v in edges])
    print('  %-9s seam pieces pulled apart (%d coincident spots):  mean %.1f cm   worst %.1f cm   | edge stretch 99th pct %.2fx' % (
        label, int((gaps > 0).sum()) if len(gaps) else 0, 100 * gaps.mean(), 100 * gaps.max(), np.percentile(r, 99)))
    return gaps


def main():
    it = itemlib.load()
    work = os.path.join(it.work, 'dhaen_patch')
    stride = {'Hip_R': 35, 'Knee_R': 50, 'Hip_L': -30, 'Knee_L': 10}
    print('run stride: right leg back (hip 35, knee 50 deg), left leg forward (hip -30 deg)')
    stretch(os.path.join(work, 'original.gltf'), stride, 'original')
    stretch(os.path.join(work, 'check.gltf'), stride, 'patched')
    swap = {'Hip_L': 35, 'Knee_L': 50, 'Hip_R': -30, 'Knee_R': 10}
    print('mirrored stride: left leg back')
    stretch(os.path.join(work, 'original.gltf'), swap, 'original')
    stretch(os.path.join(work, 'check.gltf'), swap, 'patched')


if __name__ == '__main__':
    main()
