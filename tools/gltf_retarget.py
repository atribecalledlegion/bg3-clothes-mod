"""Put a fitted mesh into a vanilla garment's glTF skeleton, for Divine -a convert-model.

    python tools/gltf_retarget.py <vanilla.gltf> <fitted.gltf> <out.gltf> [mesh name]

Why this exists: LSLib's glTF importer crashes on what Blender exports
(ImportBone -> NullReferenceException). Blender wraps the bones in an armature node and
orders them its own way; the vanilla file, which LSLib wrote itself, has the bone tree
directly under the scene. Rather than fight the exporter, this rebuilds the file:

  * every node, skin and inverse-bind matrix is copied from the VANILLA file untouched,
    so the skeleton is byte-for-byte what LSLib expects
  * only the mesh's vertex data comes from the fitted file
  * JOINTS_0 indices are remapped by BONE NAME, because Blender's joint order differs
  * the mesh KEEPS the vanilla mesh's name by default: Divine's --conform-path matches
    meshes between the two files by name, and refuses with "No matching mesh found in
    source file" otherwise
  * COLOR_0 is copied from the VANILLA mesh's first vertex when the vanilla mesh has it.
    BG3 uses this channel to drive how a garment hides the body under it (the shader is
    called CHAR_BASE_VertCut), and vanilla trousers carry black there -- filling it with
    white instead left the garment sitting badly against the body
"""
import json, os, struct, sys
import numpy as np

CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16,
      5125: np.uint32, 5126: np.float32}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def read(path):
    g = json.load(open(path))
    base = os.path.dirname(os.path.abspath(path))
    bins = [open(os.path.join(base, b['uri']), 'rb').read() for b in g['buffers']]
    def acc(i):
        a = g['accessors'][i]
        v = g['bufferViews'][a['bufferView']]
        n = NC[a['type']]
        dt = CT[a['componentType']]
        off = v.get('byteOffset', 0) + a.get('byteOffset', 0)
        # Divine writes INTERLEAVED vertex buffers (bufferView.byteStride). Reading them
        # as if they were tightly packed silently returns another attribute's bytes.
        stride = v.get('byteStride')
        if stride and stride != n * np.dtype(dt).itemsize:
            raw = np.frombuffer(bins[v['buffer']], np.uint8, a['count'] * stride, off)
            raw = raw.reshape(a['count'], stride)[:, :n * np.dtype(dt).itemsize]
            arr = np.ascontiguousarray(raw).view(dt).reshape(a['count'], n)
        else:
            arr = np.frombuffer(bins[v['buffer']], dt, a['count'] * n, off).reshape(a['count'], n)
        return arr if n > 1 else arr.reshape(-1)
    return g, acc


def main():
    vanilla_path, fitted_path, out_path = sys.argv[1:4]
    mesh_name = sys.argv[4] if len(sys.argv) > 4 else None
    van, van_acc = read(vanilla_path)
    fit, fit_acc = read(fitted_path)

    van_joint_names = [van['nodes'][j].get('name') for j in van['skins'][0]['joints']]
    fit_joint_names = [fit['nodes'][j].get('name') for j in fit['skins'][0]['joints']]
    missing = set(fit_joint_names) - set(van_joint_names)
    if missing:
        raise SystemExit('fitted mesh uses bones the vanilla garment does not have: %s' % missing)
    remap = np.array([van_joint_names.index(n) for n in fit_joint_names], np.uint16)

    fp = fit['meshes'][0]['primitives'][0]
    attrs = {k: fit_acc(v) for k, v in fp['attributes'].items()}
    idx = fit_acc(fp['indices']).astype(np.uint32)
    joints = remap[attrs['JOINTS_0'].astype(int)].astype(np.uint8)
    weights = attrs['WEIGHTS_0'].astype(np.float32)
    weights /= np.maximum(weights.sum(1, keepdims=True), 1e-6)

    vp = van['meshes'][0]['primitives'][0]
    data, views, accessors = bytearray(), [], []

    def add(arr, comp_type, typ, target=None, minmax=False):
        raw = arr.tobytes()
        while len(data) % 4:
            data.append(0)
        off = len(data)
        data.extend(raw)
        views.append(dict(buffer=0, byteOffset=off, byteLength=len(raw), **({'target': target} if target else {})))
        a = dict(bufferView=len(views) - 1, componentType=comp_type, count=len(arr), type=typ)
        if minmax:
            a['min'] = [float(x) for x in np.asarray(arr).min(0)]
            a['max'] = [float(x) for x in np.asarray(arr).max(0)]
        accessors.append(a)
        return len(accessors) - 1

    prim = {'attributes': {}, 'mode': 4}
    prim['attributes']['POSITION'] = add(attrs['POSITION'].astype(np.float32), 5126, 'VEC3', 34962, True)
    prim['attributes']['NORMAL'] = add(attrs['NORMAL'].astype(np.float32), 5126, 'VEC3', 34962)
    if 'TANGENT' in attrs:
        prim['attributes']['TANGENT'] = add(attrs['TANGENT'].astype(np.float32), 5126, 'VEC4', 34962)
    prim['attributes']['TEXCOORD_0'] = add(attrs['TEXCOORD_0'].astype(np.float32), 5126, 'VEC2', 34962)
    if 'COLOR_0' in vp['attributes']:
        n = len(attrs['POSITION'])
        vc = np.asarray(van_acc(vp['attributes']['COLOR_0']), np.float32)
        if vc.max() > 1.5:                     # stored 0..255
            vc = vc / 255.0
        prim['attributes']['COLOR_0'] = add(np.tile(vc[0], (n, 1)).astype(np.float32), 5126, 'VEC4', 34962)
    prim['attributes']['JOINTS_0'] = add(joints, 5121, 'VEC4', 34962)
    prim['attributes']['WEIGHTS_0'] = add(weights, 5126, 'VEC4', 34962)
    prim['indices'] = add(idx, 5125, 'SCALAR', 34963)

    ibm = van_acc(van['skins'][0]['inverseBindMatrices']).astype(np.float32)
    ibm_idx = add(ibm.reshape(-1, 16), 5126, 'MAT4')

    name = os.path.splitext(os.path.basename(out_path))[0]
    # conform matches meshes by name
    mesh = mesh_name or van['meshes'][0].get('name') or (name + '_Mesh')
    nodes = [dict(n) for n in van['nodes']]
    # The vanilla file may carry several mesh nodes (LOD0..LOD4). We have ONE mesh, so the
    # first node takes it and the rest stop being mesh nodes -- otherwise every LOD node
    # points at our mesh and the GR2 ends up with the same geometry several times over.
    mesh_nodes = [i for i, n in enumerate(nodes) if 'mesh' in n]
    for k, i in enumerate(mesh_nodes):
        if k == 0:
            nodes[i]['mesh'] = 0
            nodes[i]['skin'] = 0
            nodes[i]['name'] = mesh
        else:
            nodes[i] = {key: v for key, v in nodes[i].items() if key not in ('mesh', 'skin')}

    out = {
        'asset': {'version': '2.0', 'generator': 'bg3-clothes-mod gltf_retarget'},
        'scenes': van['scenes'],
        'scene': van.get('scene', 0),
        'nodes': nodes,
        'skins': [dict(joints=van['skins'][0]['joints'], inverseBindMatrices=ibm_idx)],
        'meshes': [{'name': mesh, 'primitives': [prim]}],
        'buffers': [{'uri': name + '.bin', 'byteLength': len(data)}],
        'bufferViews': views,
        'accessors': accessors,
    }
    if 'extensions' in van:
        out['extensions'] = van['extensions']
    if 'extensionsUsed' in van:
        out['extensionsUsed'] = van['extensionsUsed']
    json.dump(out, open(out_path, 'w'), indent=1)
    open(os.path.join(os.path.dirname(os.path.abspath(out_path)), name + '.bin'), 'wb').write(bytes(data))
    print('wrote %s  (%d verts, %d tris, %d bones, mesh %r)'
          % (out_path, len(attrs['POSITION']), len(idx) // 3, len(remap), mesh))


if __name__ == '__main__':
    main()
