"""Move PK's Hair_19_FS onto the VANILLA hair skeleton (the route the Lloyd hair took, which loaded in game).

    python items/pk_hair19_dhaen/refit_vanilla.py [--scale 1.0] [--drop 0] --out PKHair19_van_x100.GR2

Why: a GR2 that Divine re-wrote from PK's own glTF (refit.py, even at scale 1.0) is not drawn by the game, while PK's
untouched file is. Here the mesh is rebuilt around Larian's skeleton with tools/hair_retarget.py, the same pipeline as
tools/hair_mod.py gr2.

Every vertex of Hair_19_FS is weighted 100% to Head_M, so the move onto the vanilla masculine skeleton is a translation:
delta = vanilla Head_M bind - PK Head_M bind = (0, -0.088, +0.001). Scale/drop are applied first, in PK's bind space,
exactly as in refit.py.
"""
import argparse, json, os, subprocess, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.path.insert(0, HERE)
import hair_mod
import refit
from refit import read_glb, write_glb, positions

DONOR = os.path.join(ROOT, 'extracted', 'hair_base', 'HAIR_HUM_M_Straight_Short_M.glb')
DONOR_MESH = 'HAIR_HUM_M_Straight_Short_M_Mesh'


def head_world_y_z(js):
    """Head_M bind translation (world) from the node hierarchy (translations only; rotations do not move the origin of a
    child chain we need here, so compute with full matrices)."""
    nodes = js['nodes']
    par = {c: i for i, n in enumerate(nodes) for c in n.get('children', [])}

    def local(n):
        m = np.eye(4)
        if 'matrix' in n:
            return np.array(n['matrix']).reshape(4, 4).T
        x, y, z, w = n.get('rotation', [0, 0, 0, 1])
        R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                      [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                      [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
        m[:3, :3] = R * np.array(n.get('scale', [1, 1, 1]))
        m[:3, 3] = n.get('translation', [0, 0, 0])
        return m

    def world(i):
        return (world(par[i]) @ local(nodes[i])) if i in par else local(nodes[i])
    idx = next(i for i, n in enumerate(nodes) if n.get('name') == 'Head_M')
    return world(idx)[:3, 3]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--scale', type=float, default=1.0)
    ap.add_argument('--drop', type=float, default=0.0)
    ap.add_argument('--out', required=True, help='file name inside art/out')
    a = ap.parse_args()
    out_gr2 = os.path.join(HERE, 'art', 'out', a.out)
    os.makedirs(os.path.dirname(out_gr2), exist_ok=True)
    work = os.path.join(ROOT, 'build', 'hair19_fit')
    os.makedirs(work, exist_ok=True)
    gr2 = os.path.join(work, 'Hair_19_FS.GR2')
    glb = os.path.join(work, 'Hair_19_FS_export.glb')
    fitted = os.path.join(work, 'Hair_19_FS_fitted_%s.glb' % os.path.splitext(a.out)[0])
    retargeted = fitted.replace('_fitted_', '_retargeted_')
    from lspk import Pak
    open(gr2, 'wb').write(Pak(os.path.join(hair_mod.MODS, 'PK_Hair_Collection.pak')).read(refit.SRC))
    hair_mod.divine('-a', 'convert-model', '-s', gr2, '-d', glb, '-e', 'export-normals', '-e', 'export-tangents', '-e', 'export-uvs')
    js, blob = read_glb(glb)
    dj, _ = read_glb(DONOR)
    delta = head_world_y_z(dj) - head_world_y_z(js)
    print('Head_M bind: PK', np.round(head_world_y_z(js), 3), 'vanilla', np.round(head_world_y_z(dj), 3), 'delta', np.round(delta, 3))
    accs = sorted({pr['attributes']['POSITION'] for m in js['meshes'] for pr in m['primitives']})
    allp = np.vstack([positions(js, blob, i) for i in accs])
    pivot = np.array([0.0, allp[:, 1].max(), allp[:, 2].min()], dtype=np.float64)
    for i in accs:
        p = positions(js, blob, i)
        q = pivot + a.scale * (p.astype(np.float64) - pivot) + np.array([0, -a.drop, 0]) + delta
        p[:] = q.astype(np.float32)
        js['accessors'][i]['min'] = [float(x) for x in p.min(0)]
        js['accessors'][i]['max'] = [float(x) for x in p.max(0)]
    # the retargeter wants the fitted mesh to carry the donor's mesh name and only bones the donor has
    assert len(js['meshes']) == 1
    js['meshes'][0]['name'] = DONOR_MESH
    sk = js['skins'][0]
    names = [js['nodes'][j].get('name') for j in sk['joints']]
    assert names[0] == 'Head_M'
    ja = js['meshes'][0]['primitives'][0]['attributes']['JOINTS_0']
    jn = np.ndarray(shape=(js['accessors'][ja]['count'], 4), dtype=np.uint8,
                    buffer=blob, offset=js['bufferViews'][js['accessors'][ja]['bufferView']].get('byteOffset', 0) + js['accessors'][ja].get('byteOffset', 0),
                    strides=(js['bufferViews'][js['accessors'][ja]['bufferView']].get('byteStride') or 4, 1))
    assert jn.max() == 0, 'this route assumes every vertex is weighted to joint 0 (Head_M)'
    sk['joints'] = [sk['joints'][0]]
    sk.pop('inverseBindMatrices', None)
    write_glb(fitted, js, blob)
    r = subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'hair_retarget.py'), DONOR, fitted, retargeted, '--lod-from-lod0'],
                       capture_output=True, text=True)
    print((r.stdout + r.stderr).strip())
    if r.returncode:
        raise SystemExit('retarget failed')
    hair_mod.divine('-a', 'convert-model', '-s', retargeted, '-d', out_gr2, '-e', 'export-uvs', '-e', 'export-normals', '-e', 'export-tangents')
    print('wrote', out_gr2, os.path.getsize(out_gr2), 'bytes; scale', a.scale, 'drop', a.drop)


if __name__ == '__main__':
    main()
