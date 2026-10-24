"""Refit PK's Hair_19_FS to the Dhaen head: scale the vertices, keep bones and skin weights untouched.

    python items/pk_hair19_dhaen/refit.py [--scale 0.85] [--drop 0.018]
        -> items/pk_hair19_dhaen/art/out/PKHair19_FS_Dhaen.GR2   (git-ignored: derived from PK's mesh, personal use only)

Why: with NeedsSkeletonRemap the game keeps a hair at the same place RELATIVE TO THE HEAD BONE as it was authored.
PK's Hair 19 was made for a bigger adult head (31 cm deep, 6.5 cm above the skull); the Dhaen head is smaller and
its eyes sit higher, so the fringe covered the eyes ("mask"). Rendering the mesh on the Dhaen head (fit_preview.py)
reproduced what the game showed, and Dhaen_Hair-Merged's own Dhaen-fitted Hair 01 (26 cm deep, 4 cm above the skull)
is the calibration: a uniform 0.85 about the fringe-top corner gives the same footprint and fringe height.

The transform runs in the GR2's bind space (v' = pivot + s * (v - pivot) + (0, -drop, 0)), so bones, inverse-bind
matrices and weights stay exactly as PK made them and the head-relative model above still holds.
"""
import argparse, json, os, struct, subprocess, sys, tempfile
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import hair_mod
from lspk import Pak

SRC = 'Generated/Public/PK_Hair_Collection/[PAK]_PK_Hair_Collection/Hair_19_FS.GR2'
OUT = os.path.join(HERE, 'art', 'out', 'PKHair19_FS_Dhaen.GR2')
CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}


def read_glb(path):
    raw = open(path, 'rb').read()
    assert raw[:4] == b'glTF'
    pos, js, blob = 12, None, None
    while pos < len(raw):
        ln, kind = struct.unpack('<II', raw[pos:pos + 8])
        body = raw[pos + 8:pos + 8 + ln]
        if kind == 0x4E4F534A:
            js = json.loads(body)
        elif kind == 0x004E4942:
            blob = bytearray(body)
        pos += 8 + ln
    return js, blob


def write_glb(path, js, blob):
    j = json.dumps(js, separators=(',', ':')).encode()
    j += b' ' * (-len(j) % 4)
    b = bytes(blob) + b'\0' * (-len(blob) % 4)
    total = 12 + 8 + len(j) + 8 + len(b)
    open(path, 'wb').write(struct.pack('<4sII', b'glTF', 2, total) + struct.pack('<II', len(j), 0x4E4F534A) + j
                           + struct.pack('<II', len(b), 0x004E4942) + b)


def positions(js, blob, ai):
    a = js['accessors'][ai]
    bv = js['bufferViews'][a['bufferView']]
    assert a['componentType'] == 5126 and a['type'] == 'VEC3'
    off = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    stride = bv.get('byteStride') or 12
    return np.ndarray(shape=(a['count'], 3), dtype='<f4', buffer=blob, offset=off, strides=(stride, 4))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--scale', type=float, default=0.85)
    ap.add_argument('--drop', type=float, default=0.018)
    ap.add_argument('--out', default='PKHair19_FS_Dhaen.GR2', help='file name inside art/out')
    ap.add_argument('--conform', action='store_true', help="Divine --conform-path: bind to PK's own GR2 skeleton")
    a = ap.parse_args()
    out_gr2 = os.path.join(os.path.dirname(OUT), a.out)
    work = os.path.join(ROOT, 'build', 'hair19_fit')
    os.makedirs(work, exist_ok=True)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    gr2 = os.path.join(work, 'Hair_19_FS.GR2')
    glb, glb2 = os.path.join(work, 'Hair_19_FS_export.glb'), os.path.join(work, 'Hair_19_FS_refit.glb')
    open(gr2, 'wb').write(Pak(os.path.join(hair_mod.MODS, 'PK_Hair_Collection.pak')).read(SRC))
    hair_mod.divine('-a', 'convert-model', '-s', gr2, '-d', glb, '-e', 'export-normals', '-e', 'export-tangents', '-e', 'export-uvs')
    js, blob = read_glb(glb)
    accs = sorted({pr['attributes']['POSITION'] for m in js['meshes'] for pr in m['primitives']})
    allp = np.vstack([positions(js, blob, i) for i in accs])
    pivot = np.array([0.0, allp[:, 1].max(), allp[:, 2].min()], dtype=np.float64)     # front-top corner of the hair
    print('meshes', [m.get('name') for m in js['meshes']], 'bounds before', np.round(allp.min(0), 3), np.round(allp.max(0), 3))
    for i in accs:
        p = positions(js, blob, i)
        q = pivot + a.scale * (p.astype(np.float64) - pivot) + np.array([0, -a.drop, 0])
        p[:] = q.astype(np.float32)
        js['accessors'][i]['min'] = [float(x) for x in p.min(0)]
        js['accessors'][i]['max'] = [float(x) for x in p.max(0)]
    allq = np.vstack([positions(js, blob, i) for i in accs])
    print('bounds after ', np.round(allq.min(0), 3), np.round(allq.max(0), 3), 'scale', a.scale, 'drop', a.drop)
    write_glb(glb2, js, blob)
    extra = ['--conform-path', gr2] if a.conform else []
    hair_mod.divine('-a', 'convert-model', '-s', glb2, '-d', out_gr2, '-e', 'export-uvs', '-e', 'export-normals', '-e', 'export-tangents', *extra)
    print('wrote', out_gr2, os.path.getsize(out_gr2), 'bytes (source GR2 %d)' % os.path.getsize(gr2), '(conformed)' if a.conform else '')


if __name__ == '__main__':
    main()
