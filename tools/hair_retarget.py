"""Put a sculpted hair into the vanilla hair's glTF skeleton, for Divine -a convert-model.

    python tools/hair_retarget.py <vanilla.glb> <fitted.glb> <out.glb> [--lod-from-lod0]

This is tools/gltf_retarget.py extended to the shape hair has: several mesh nodes (LOD0, LOD1,
accessories), .glb files, and more than one UV set. The reason it exists is the same:
LSLib's glTF importer crashes on what Blender exports (ImportBone -> NullReferenceException),
so the file is rebuilt around the skeleton LSLib itself wrote:

  * every node, the skin and its inverse-bind matrices come from the VANILLA file untouched
  * for each vanilla mesh node, the vertex data comes from the FITTED mesh of the SAME NAME
  * JOINTS_0 is remapped by bone NAME (Blender orders the joints its own way)
  * TEXCOORD_0/1 and COLOR_0 are copied when the fitted mesh has them; a missing COLOR_0 is
    filled from the vanilla mesh's first vertex

A vanilla mesh node with no same-named fitted mesh is a LOD you did not author. With
--lod-from-lod0 it takes the geometry of the matching LOD0 mesh (heavier at distance, but
the same hair); without it the script stops so nothing ships half old, half new.
"""
import argparse, json, os, struct, sys
import numpy as np

CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16,
      5125: np.uint32, 5126: np.float32}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def read(path):
    """-> (json, accessor reader). Handles .glb and .gltf with external buffers, and the
    interleaved vertex buffers Divine writes (bufferView.byteStride)."""
    base = os.path.dirname(os.path.abspath(path))
    if path.lower().endswith('.glb'):
        raw = open(path, 'rb').read()
        assert raw[:4] == b'glTF', 'not a GLB'
        pos, g, blob = 12, None, b''
        while pos < len(raw):
            ln, kind = struct.unpack('<II', raw[pos:pos + 8])
            body = raw[pos + 8:pos + 8 + ln]
            if kind == 0x4E4F534A:
                g = json.loads(body)
            elif kind == 0x004E4942:
                blob = body
            pos += 8 + ln
        bins = [blob]
    else:
        g = json.load(open(path))
        bins = [open(os.path.join(base, b['uri']), 'rb').read() for b in g['buffers']]

    def acc(i):
        a = g['accessors'][i]
        v = g['bufferViews'][a['bufferView']]
        n = NC[a['type']]
        dt = CT[a['componentType']]
        isz = np.dtype(dt).itemsize
        off = v.get('byteOffset', 0) + a.get('byteOffset', 0)
        stride = v.get('byteStride')
        if stride and stride != n * isz:
            r = np.frombuffer(bins[v['buffer']], np.uint8, a['count'] * stride, off)
            r = r.reshape(a['count'], stride)[:, :n * isz]
            arr = np.ascontiguousarray(r).view(dt).reshape(a['count'], n)
        else:
            arr = np.frombuffer(bins[v['buffer']], dt, a['count'] * n, off).reshape(a['count'], n)
        return arr if n > 1 else arr.reshape(-1)
    return g, acc


NORM_DIV = {5120: 127.0, 5121: 255.0, 5122: 32767.0, 5123: 65535.0}


def as_float(g, acc, i):
    """An accessor as float32. A NORMALIZED integer accessor (vertex colours are usually uint8 from Divine and
    uint16 from Blender) holds 0..max, meaning 0..1; copying the raw integers into a float accessor makes every
    colour 255x or 65535x too bright and Divine clamps it to white."""
    a = np.asarray(acc(i), np.float32)
    ac = g['accessors'][i]
    if ac.get('normalized') and ac['componentType'] in NORM_DIV:
        a = a / NORM_DIV[ac['componentType']]
    return a


def mesh_nodes(g):
    """{name: (node index, primitive)} for every node that carries a mesh."""
    out = {}
    for i, n in enumerate(g['nodes']):
        if 'mesh' in n:
            m = g['meshes'][n['mesh']]
            out[n.get('name') or m.get('name')] = (i, m['primitives'][0])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('vanilla')
    ap.add_argument('fitted')
    ap.add_argument('out')
    ap.add_argument('--lod-from-lod0', action='store_true')
    a = ap.parse_args()

    van, van_acc = read(a.vanilla)
    fit, fit_acc = read(a.fitted)
    van_joints = [van['nodes'][j].get('name') for j in van['skins'][0]['joints']]
    fit_joints = [fit['nodes'][j].get('name') for j in fit['skins'][0]['joints']]
    missing = set(fit_joints) - set(van_joints)
    if missing:
        raise SystemExit('the fitted hair uses bones the vanilla hair does not have: %s' % sorted(missing))
    remap = np.array([van_joints.index(n) for n in fit_joints], np.uint16)

    vmesh, fmesh = mesh_nodes(van), mesh_nodes(fit)
    extra = set(fmesh) - set(vmesh)
    if extra:
        print('WARNING: fitted meshes with no vanilla counterpart are DROPPED (VisualBank refers to '
              'meshes by name): %s' % sorted(extra), file=sys.stderr)

    data, views, accessors = bytearray(), [], []

    def add(arr, comp_type, typ, target=None, minmax=False):
        raw = np.ascontiguousarray(arr).tobytes()
        while len(data) % 4:
            data.append(0)
        off = len(data)
        data.extend(raw)
        views.append(dict(buffer=0, byteOffset=off, byteLength=len(raw), **({'target': target} if target else {})))
        acc = dict(bufferView=len(views) - 1, componentType=comp_type, count=len(arr), type=typ)
        if minmax:
            acc['min'] = [float(x) for x in np.asarray(arr).min(0)]
            acc['max'] = [float(x) for x in np.asarray(arr).max(0)]
        accessors.append(acc)
        return len(accessors) - 1

    def lod0_name(name):
        return name.replace('_LOD1', '').replace('_LOD2', '').replace('_LOD3', '').replace('_LOD4', '')

    nodes = [dict(n) for n in van['nodes']]
    meshes, report = [], []
    for name, (ni, vp) in vmesh.items():
        src = name
        if name not in fmesh:
            src = lod0_name(name)
            if not a.lod_from_lod0 or src not in fmesh:
                raise SystemExit('fitted file has no mesh named %r (has: %s). Keep the vanilla mesh '
                                 'names, or pass --lod-from-lod0 for LODs you did not author.'
                                 % (name, sorted(fmesh)))
            print('note: %s reuses the geometry of %s' % (name, src))
        fp = fmesh[src][1]
        attrs = {k: fit_acc(v) for k, v in fp['attributes'].items()}
        idx = fit_acc(fp['indices']).astype(np.uint32)
        joints = remap[attrs['JOINTS_0'].astype(int)].astype(np.uint8)
        weights = attrs['WEIGHTS_0'].astype(np.float32)
        weights /= np.maximum(weights.sum(1, keepdims=True), 1e-6)
        n = len(attrs['POSITION'])

        prim = {'attributes': {}, 'mode': 4}
        A = prim['attributes']
        A['POSITION'] = add(attrs['POSITION'].astype(np.float32), 5126, 'VEC3', 34962, True)
        A['NORMAL'] = add(attrs['NORMAL'].astype(np.float32), 5126, 'VEC3', 34962)
        if 'TANGENT' in attrs:
            A['TANGENT'] = add(attrs['TANGENT'].astype(np.float32), 5126, 'VEC4', 34962)
        for k in sorted(k for k in attrs if k.startswith('TEXCOORD_')):
            A[k] = add(attrs[k].astype(np.float32), 5126, 'VEC2', 34962)
        if 'COLOR_0' in attrs:
            c = as_float(fit, fit_acc, fp['attributes']['COLOR_0'])
            if c.shape[1] == 3:
                c = np.hstack([c, np.ones((n, 1), np.float32)])
            A['COLOR_0'] = add(c, 5126, 'VEC4', 34962)
        elif 'COLOR_0' in vp['attributes']:
            vc = as_float(van, van_acc, vp['attributes']['COLOR_0'])
            if vc.shape[1] == 3:
                vc = np.hstack([vc, np.ones((len(vc), 1), np.float32)])
            A['COLOR_0'] = add(np.tile(vc[0], (n, 1)).astype(np.float32), 5126, 'VEC4', 34962)
        A['JOINTS_0'] = add(joints, 5121, 'VEC4', 34962)
        A['WEIGHTS_0'] = add(weights, 5126, 'VEC4', 34962)
        prim['indices'] = add(idx, 5125, 'SCALAR', 34963)

        nodes[ni]['mesh'] = len(meshes)
        nodes[ni]['skin'] = 0
        meshes.append({'name': van['meshes'][van['nodes'][ni]['mesh']].get('name') or name, 'primitives': [prim]})
        report.append((name, n, len(idx) // 3))

    ibm = van_acc(van['skins'][0]['inverseBindMatrices']).astype(np.float32)
    ibm_idx = add(ibm.reshape(-1, 16), 5126, 'MAT4')

    out = {
        'asset': {'version': '2.0', 'generator': 'bg3-clothes-mod hair_retarget'},
        'scenes': van['scenes'], 'scene': van.get('scene', 0),
        'nodes': nodes,
        'skins': [dict(joints=van['skins'][0]['joints'], inverseBindMatrices=ibm_idx)],
        'meshes': meshes,
        'bufferViews': views, 'accessors': accessors,
    }
    for k in ('extensions', 'extensionsUsed'):
        if k in van:
            out[k] = van[k]

    # write as .glb (one file)
    while len(data) % 4:
        data.append(0)
    out['buffers'] = [{'byteLength': len(data)}]
    js = json.dumps(out).encode()
    js += b' ' * ((4 - len(js) % 4) % 4)
    total = 12 + 8 + len(js) + 8 + len(data)
    with open(a.out, 'wb') as f:
        f.write(struct.pack('<4sII', b'glTF', 2, total))
        f.write(struct.pack('<II', len(js), 0x4E4F534A) + js)
        f.write(struct.pack('<II', len(data), 0x004E4942) + bytes(data))
    for name, v, t in report:
        print('  %-52s verts %6d tris %6d' % (name, v, t))
    print('wrote %s (%d meshes, %d bones)' % (a.out, len(meshes), len(remap)))


if __name__ == '__main__':
    main()
