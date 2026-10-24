"""Add a low nape ponytail to an existing strand-clump hair, changing nothing else (Blender, headless).

    "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b -P tools/hair_ponytail.py -- \
        --base extracted/hair01/M_Hair_01.glb --head extracted/head_hum_m_a/HUM_M_NKD_Head_A.glb \
        --out items/hair01_ponytail/art/out/hair01_ponytail.blend --renders build/hair01_renders

The hair is a set of loose strand clumps (islands). Those hanging at the back-lower part of the head are laid
into a bundle at the nape, stretched into a tail that hangs and flips out at the tip; extra copies fill the
bundle. Everything else is left byte-for-byte: untouched clumps keep their vertices, weights, UVs, vertex colours
and custom normals. Moved clumps keep their UVs, weights and colours, and their normals are carried through the
same rotation, so the tail shades like the rest of the hair.

Applied to every mesh in the file whose name starts with --mesh-prefix (LOD0 and LOD1 both), so the tail does not
pop in and out with distance.

Coordinates are Blender's: x lateral, y FRONT = +, z up. The nape tie sits just behind the head's skin, found by
ray-casting the head mesh at --tie-z.
"""
import argparse, math, os, random, sys

import bpy, bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

DEFAULTS = dict(
    seed=11, tie_z=1.775, tie_gap=0.026, tie_radius=0.015,
    tail_len=(0.19, 0.24), tail_flip=0.070, tail_back=0.022, tail_splay=0.016,
    tail_width=1.05, tail_taper=0.50,
    zone_y_max=-0.040, zone_z_max=1.800,          # clumps with their centre behind/below this become the tail
    strands={'': 190, '_LOD1': 120},               # total tail strands per LOD (originals + copies)
    push_out=0.004, vertical_bias=True,
)


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def head_bvh(path):
    before = {o.name for o in bpy.data.objects}
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o.name not in before]
    verts, polys = [], []
    for o in new:
        if o.type == 'MESH' and o.name.endswith(('_Head_A_Mesh', '_Ears_Mesh', '_Head_B_Mesh')):
            base = len(verts)
            verts += [tuple(o.matrix_world @ v.co) for v in o.data.vertices]
            polys += [tuple(base + i for i in p.vertices) for p in o.data.polygons]
    return BVHTree.FromPolygons(verts, polys), new


def islands(bm):
    seen, out = set(), []
    for v in bm.verts:
        if v.index in seen:
            continue
        stack, comp = [v], []
        seen.add(v.index)
        while stack:
            x = stack.pop()
            comp.append(x)
            for e in x.link_edges:
                w = e.other_vert(x)
                if w.index not in seen:
                    seen.add(w.index)
                    stack.append(w)
        out.append(comp)
    return out


class Clump:
    """One strand clump: its vertices and a frame (a = long axis, b = across, n = a x b)."""

    def __init__(self, verts, vn):
        self.verts = verts
        self.idx = np.array([v.index for v in verts])
        pts = np.array([tuple(v.co) for v in verts])
        self.pts = pts
        self.c = pts.mean(0)
        _, _, vt = np.linalg.svd(pts - self.c, full_matrices=False)
        self.a, self.b = vt[0], vt[1]
        self.n = np.cross(self.a, self.b)
        self.vn = vn[self.idx]                      # the original per-vertex normals

    def orient(self, down=True):
        if (self.a[2] < 0) != down:
            self.a, self.b = -self.a, -self.b
        self.n = np.cross(self.a, self.b)
        proj = (self.pts - self.c) @ self.a
        lo, hi = proj.min(), proj.max()
        self.L = max(hi - lo, 1e-6)
        self.u = (proj - lo) / self.L
        self.w = (self.pts - self.c) @ self.b
        self.t = (self.pts - self.c) @ self.n
        self.nl = np.stack([self.vn @ self.a, self.vn @ self.b, self.vn @ self.n], 1)   # normals in the clump frame
        return self


def lay(clump, path, across, normal, ws, taper):
    """Lay a clump along a centreline. Returns (positions, normals). The clump's own u/w/t are kept, so its
    thickness and UVs survive; its normals go through the same frame mapping."""
    path = np.asarray(path, float)
    seg = np.linalg.norm(np.diff(path, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    s /= s[-1]
    tang = np.gradient(path, axis=0)
    tang /= np.linalg.norm(tang, axis=1, keepdims=True)
    u = clump.u
    pos = np.stack([np.interp(u, s, path[:, k]) for k in range(3)], 1)
    T = np.stack([np.interp(u, s, tang[:, k]) for k in range(3)], 1)
    T /= np.linalg.norm(T, axis=1, keepdims=True)
    A = np.asarray(across, float)
    B = A - np.outer(T @ A, np.ones(3)) * T
    B /= np.linalg.norm(B, axis=1, keepdims=True)
    N = np.cross(T, B)
    if (N @ np.asarray(normal, float)).mean() < 0:
        B, N = -B, -N
    wid = (clump.w * ws * (1.0 - taper * u))[:, None]
    new_pos = pos + wid * B + clump.t[:, None] * N
    nrm = clump.nl[:, 0:1] * T + clump.nl[:, 1:2] * B + clump.nl[:, 2:3] * N
    nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-9)
    return new_pos, nrm


def corner_arrays(me):
    n = len(me.loops)
    lv = np.empty(n, np.int64)
    me.loops.foreach_get('vertex_index', lv)
    cn = np.empty(n * 3, np.float32)
    me.corner_normals.foreach_get('vector', cn)
    return lv, cn.reshape(n, 3)


def process(obj, suffix, tree, P, log):
    rnd = random.Random(P['seed'] + len(suffix))
    me = obj.data
    lv0, cn0 = corner_arrays(me)
    nv0 = len(me.vertices)
    vn = np.zeros((nv0, 3))
    cnt = np.zeros(nv0)
    np.add.at(vn, lv0, cn0)
    np.add.at(cnt, lv0, 1)
    vn /= np.maximum(cnt, 1)[:, None]
    vn /= np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-9)

    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    clumps = [Clump(c, vn) for c in islands(bm)]
    src = [c for c in clumps if c.c[1] < P['zone_y_max'] and c.c[2] < P['zone_z_max']]
    log('  %s: %d clumps, %d in the tail zone' % (obj.name, len(clumps), len(src)))
    if not src:
        raise SystemExit('no clumps in the tail zone; adjust zone_y_max / zone_z_max')

    # where the skull's back is at the tie height -> tie point just behind it
    hit = tree.ray_cast(Vector((0, -0.8, P['tie_z'])), Vector((0, 1, 0)), 2.0)
    skull_y = hit[0][1] if hit[0] is not None else -0.06
    tie = np.array([0.0, skull_y - P['tie_gap'], P['tie_z']])
    log('  skull back at z=%.3f is y=%+.3f -> tie %s' % (P['tie_z'], skull_y, tie.round(3)))

    def duplicate(c):
        faces = {f for v in c.verts for f in v.link_faces}
        edges = {e for v in c.verts for e in v.link_edges}
        res = bmesh.ops.duplicate(bm, geom=list(c.verts) + list(edges) + list(faces))
        vm = res['vert_map']
        d = Clump.__new__(Clump)
        d.verts = [vm[v] for v in c.verts]
        d.pts, d.c, d.a, d.b, d.n, d.vn = c.pts.copy(), c.c.copy(), c.a.copy(), c.b.copy(), c.n.copy(), c.vn.copy()
        d.idx = None
        d.u, d.w, d.t, d.nl, d.L = c.u, c.w, c.t, c.nl, c.L
        return d

    for c in src:
        c.orient(down=True)
    want = P['strands'].get(suffix, 120)
    dup = []
    while len(src) + len(dup) < want:
        dup.append(duplicate(rnd.choice(src)))
    bm.verts.index_update()
    for d in dup:
        d.idx = np.array([v.index for v in d.verts])

    n_all = len(bm.verts)
    new_n = np.zeros((n_all, 3))
    edited = np.zeros(n_all, bool)
    for c in src + dup:
        Lnew = rnd.uniform(*P['tail_len'])
        ang = rnd.uniform(0, 2 * math.pi)
        rr = P['tie_radius'] * rnd.random() ** 0.5
        root = tie + np.array([math.cos(ang) * rr, math.sin(ang) * rr * 0.8, 0.0])
        eps = rnd.uniform(-1, 1)
        pts = [root + np.array([eps * P['tail_splay'] * (0.3 + 1.2 * s),
                                -P['tail_back'] * s - P['tail_flip'] * s ** 3,
                                -Lnew * s]) for s in np.linspace(0, 1, 16)]
        yaw = rnd.uniform(-0.8, 0.8)
        pos, nrm = lay(c, pts, (math.cos(yaw), math.sin(yaw), 0.0), (0, -1, 0), P['tail_width'], P['tail_taper'])
        for v, p in zip(c.verts, pos):
            v.co = Vector(p)
        new_n[c.idx] = nrm
        edited[c.idx] = True

    # keep the tail out of the head
    bm.verts.ensure_lookup_table()                  # duplicates added vertices since the table was built
    pushed = 0
    for i in np.nonzero(edited)[0]:
        v = bm.verts[i]
        loc, nrmv, _, dist = tree.find_nearest(v.co)
        if loc is not None and dist < 0.03 and (v.co - loc).dot(nrmv) < P['push_out']:
            v.co = loc + nrmv * P['push_out']
            pushed += 1
    log('  tail: %d clumps (%d original + %d copies), %d vertices pushed off the head' % (len(src) + len(dup), len(src), len(dup), pushed))

    bm.to_mesh(me)
    bm.free()

    # custom normals: untouched loops keep theirs; moved/copied loops get the carried-through normal
    lv1, _ = corner_arrays(me)
    if len(lv1) >= len(lv0) and np.array_equal(lv1[:len(lv0)], lv0):
        cn1 = np.zeros((len(lv1), 3), np.float32)
        cn1[:len(lv0)] = cn0
        m = edited[lv1]
        cn1[m] = new_n[lv1[m]]
        me.normals_split_custom_set(cn1.tolist())
        log('  normals: %d of %d loops carried through, %d kept from the original' % (m.sum(), len(lv1), (~m).sum()))
    else:
        log('  WARNING: loop order changed; normals left to Blender')
    me.update()


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', required=True)
    ap.add_argument('--head', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--renders')
    ap.add_argument('--mesh-prefix', default='M_Hair_01')
    ap.add_argument('--set', nargs='*', default=[], help='override a parameter: key=value (numbers only)')
    a = ap.parse_args(argv)
    P = dict(DEFAULTS)
    for kv in a.set:
        k, v = kv.split('=')
        P[k] = float(v)

    clear()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.abspath(a.base))
    hair = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith(a.mesh_prefix)]
    hair_names = {o.name for o in bpy.data.objects}
    for o in list(bpy.data.objects):
        if o.type == 'MESH' and o.name.startswith('Icosphere') and not o.vertex_groups:
            bpy.data.objects.remove(o, do_unlink=True)
    tree, head_objs = head_bvh(os.path.abspath(a.head))
    for o in head_objs:
        o.hide_set(True)
    print('hair meshes:', [o.name for o in hair])
    for o in hair:
        suffix = '_LOD1' if o.name.endswith('_LOD1') else ''
        process(o, suffix, tree, P, print)

    if a.renders:
        render(hair, head_objs, a.renders)
    for o in head_objs:
        bpy.data.objects.remove(o, do_unlink=True)
    for o in hair:                                  # render() hides LOD1; a hidden object is skipped by the exporter
        o.hide_set(False)
        o.hide_render = False
        o.hide_viewport = False
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.out))
    print('saved', a.out)


def render(hair, head_objs, outdir):
    os.makedirs(outdir, exist_ok=True)
    sc = bpy.context.scene
    for o in hair:
        o.hide_render = o.name.endswith('_LOD1')
        o.hide_set(o.name.endswith('_LOD1'))
        o.color = (0.25, 0.42, 0.85, 1)
    for o in head_objs:
        keep = o.type == 'MESH' and o.name.endswith(('_Head_A_Mesh', '_Ears_Mesh', '_Head_B_Mesh'))
        o.hide_set(not keep)
        o.hide_render = not keep
        o.color = (0.86, 0.72, 0.62, 1)
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.render.resolution_x = sc.render.resolution_y = 560
    sh = sc.display.shading
    sh.light = 'STUDIO'
    sh.color_type = 'OBJECT'
    sh.show_cavity = True
    w = bpy.data.worlds.new('w')
    w.color = (0.93, 0.93, 0.93)
    sc.world = w
    cd = bpy.data.cameras.new('cam')
    cd.type = 'ORTHO'
    cd.ortho_scale = 0.62
    cam = bpy.data.objects.new('cam', cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    centre = Vector((0, -0.01, 1.74))
    for name, d in {'front34': Vector((0.7, 0.7, 0.15)), 'side': Vector((1, 0, 0.05)),
                    'back': Vector((0, -1, 0.05)), 'back34': Vector((0.7, -0.7, 0.15))}.items():
        d = d.normalized()
        cam.location = centre + d * 3
        cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(outdir, 'pony_%s.png' % name)
        bpy.ops.render.render(write_still=True)


main()

