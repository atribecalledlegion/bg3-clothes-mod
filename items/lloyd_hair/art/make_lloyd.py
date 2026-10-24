"""Reshape vanilla HAIR_HUM_M_Straight_Short_M into the Lloyd de Saloum silhouette (Blender, headless).

    "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b -P items/lloyd_hair/art/make_lloyd.py -- \
        --base extracted/hair_base/HAIR_HUM_M_Straight_Short_M.glb \
        --head extracted/head_hum_m_a/HUM_M_NKD_Head_A.glb \
        --out  items/lloyd_hair/art/out/lloyd_v1.blend --renders build/lloyd_renders

Why cards, not sculpting: the vanilla hair is 684 separate strand ribbons on ONE material with ONE
UV set, all weighted to Head_M. Laying whole cards along new centrelines keeps every card's UVs,
weights and material, so the result renders like vanilla hair and needs no texture work.

Coordinates are Blender's (x lateral, y FRONT = +, z up). Head landmarks are from the Head A mesh:
    eyes z 1.818, brow z 1.83-1.86 (front y +0.135), nose bridge front y +0.147, skull back y -0.082 at z 1.83,
    nape (Socket_Hair_Neck1_M) y -0.059 z 1.775, head top z 1.933.

What each part does (all from the reference pictures):
    ahoge     the tallest cards become 3 ribbons rising from the crown and curling forward
    ponytail  the low-back cards are re-anchored into a bundle at the nape that hangs down and flips out at the tip
    bangs     front cards are laid along the forehead as an M: the centre strand longest (between the eyes)
    sidelocks two strands per side in front of the ear, hugging the cheek to mid-neck
    flares    cards over the ears splay outward and backward at their tips

Bangs and locks follow the real skin: the head mesh is ray-cast for where the surface is. Anything that ends
up inside the head is pushed back out. Parameters are at the top so they can be changed and re-run.
"""
import argparse, math, os, random, sys

import bpy, bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

# ---- parameters (metres) -------------------------------------------------------------------------
P = dict(
    seed=7,
    # ponytail: a tight bundle tied at the nape
    tie=(0.0, -0.074, 1.760), tie_radius=0.011, tail_len=(0.19, 0.25), tail_flip=0.060, tail_back=0.018,
    tail_strands=150, tail_width=0.75, tail_taper=0.60, tail_splay=0.013,
    tail_zone=dict(y_max=-0.040, z_max=1.800),          # original cards below/behind this feed the tail
    # ahoge
    ahoge_z_min=1.940, ahoge_base=(0.004, 0.030, 1.925), ahoge_len=0.095, ahoge_curl=2.0, ahoge_width=1.7,
    # bangs: hug the forehead; the centre strand is longest, the ones either side stop above the brow
    bang_zone=dict(y_min=0.070, z_min=1.835, x_max=0.062), bang_root_z=1.903,
    bang_tip_center=1.812, bang_tip_side=1.872, bang_center_half=0.014, bang_blend=0.020, bang_off=0.007,
    bang_center_thick=1.45,
    # side locks: two strands per side in front of the ear, tips to mid-neck, hugging the cheek
    lock_zone=dict(x_min=0.070, y_min=0.010, y_max=0.105, z_max=1.865), lock_root_z=1.868, lock_tip_z=1.660,
    lock_y=(0.034, 0.062), lock_off=0.008, lock_per_side=22,
    # flares over the ears (only cards that hang roughly vertically)
    flare_zone=dict(x_min=0.070, y_min=-0.100, y_max=0.010, z_min=1.745, z_max=1.905), flare_out=0.034, flare_back=0.022,
    vertical_min=0.55,
    push_out=0.005,
)


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def load_base(path):
    clear()
    bpy.ops.import_scene.gltf(filepath=path)
    for o in list(bpy.data.objects):
        if o.type == 'MESH' and (o.name.startswith('Icosphere') or 'LOD' in o.name):
            bpy.data.objects.remove(o, do_unlink=True)
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    assert len(meshes) == 1, [m.name for m in meshes]
    return meshes[0]


def head_bvh(path):
    """BVH of the head's skin and ears, in world space, from a Divine-converted glb."""
    before = {o.name for o in bpy.data.objects}
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o.name not in before]
    verts, polys = [], []
    for o in new:
        if o.type == 'MESH' and o.name.endswith(('_Head_A_Mesh', '_Ears_Mesh')):
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


class Card:
    """One strand ribbon: its vertices plus a frame (a = long axis, b = across, n = normal)."""

    def __init__(self, verts):
        self.verts = verts
        pts = np.array([tuple(v.co) for v in verts])
        self.c = pts.mean(0)
        u, s, vt = np.linalg.svd(pts - self.c, full_matrices=False)
        a, b = vt[0], vt[1]
        self.a, self.b, self.n = a, b, np.cross(a, b)     # right-handed: SVD's third row can be a mirror
        self.pts = pts

    def orient(self, down=True):
        """Point the long axis downward (root at the higher end) or upward (root at the lower end)."""
        if (self.a[2] < 0) != down:
            self.a = -self.a
            self.b = -self.b
        proj = (self.pts - self.c) @ self.a
        self.lo, self.hi = proj.min(), proj.max()
        self.L = max(self.hi - self.lo, 1e-6)
        self.u = (proj - self.lo) / self.L
        self.w = (self.pts - self.c) @ self.b
        self.t = (self.pts - self.c) @ self.n
        self.root = self.c + self.a * self.lo
        return self

    def vertical(self):
        return abs(self.a[2]) >= P['vertical_min']


def set_co(card, new):
    for v, p in zip(card.verts, new):
        v.co = Vector(p)


def strand(card, path, across, normal, ws=1.0, taper=0.0):
    """Lay a card along a centreline. path: (m,3) points root->tip; the card's own u/w/t are kept, so its
    UVs and thickness survive and only its shape follows the path. across = the ribbon's width direction,
    normal = the side its face should look toward."""
    path = np.asarray(path, float)
    seg = np.linalg.norm(np.diff(path, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    s /= s[-1]
    tang = np.gradient(path, axis=0)
    tang /= np.linalg.norm(tang, axis=1, keepdims=True)
    u = card.u
    pos = np.stack([np.interp(u, s, path[:, k]) for k in range(3)], 1)
    T = np.stack([np.interp(u, s, tang[:, k]) for k in range(3)], 1)
    T /= np.linalg.norm(T, axis=1, keepdims=True)
    A = np.asarray(across, float)
    B = A - np.outer(T @ A, np.ones(3)) * T
    B /= np.linalg.norm(B, axis=1, keepdims=True)
    N = np.cross(T, B)
    if (N @ np.asarray(normal, float)).mean() < 0:
        B, N = -B, -N
    wid = (card.w * ws * (1.0 - taper * u))[:, None]
    return pos + wid * B + card.t[:, None] * N


def smoothstep(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', required=True)
    ap.add_argument('--head', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--renders')
    a = ap.parse_args(argv)
    rnd = random.Random(P['seed'])

    obj = load_base(os.path.abspath(a.base))
    tree, head_objs = head_bvh(os.path.abspath(a.head))
    for o in head_objs:
        o.hide_set(True)

    def skin(origin, direction):
        loc, nrm, idx, dist = tree.ray_cast(Vector(origin), Vector(direction), 2.0)
        return None if loc is None else np.array(loc)

    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    cards = [Card(c) for c in islands(bm)]
    print('cards', len(cards))

    used = set()

    def pick(pred):
        out = []
        for i, c in enumerate(cards):
            if i not in used and pred(c.c):
                used.add(i)
                out.append(c)
        return out

    ahoge = sorted([c for c in cards if c.c[2] > P['ahoge_z_min']], key=lambda c: -c.c[2])[:4]
    used |= {cards.index(c) for c in ahoge}
    tz = P['tail_zone']
    tail = pick(lambda c: c[1] < tz['y_max'] and c[2] < tz['z_max'])
    bz = P['bang_zone']
    bangs = pick(lambda c: c[1] > bz['y_min'] and c[2] > bz['z_min'] and abs(c[0]) < bz['x_max'])
    lz = P['lock_zone']
    locks = pick(lambda c: abs(c[0]) > lz['x_min'] and lz['y_min'] < c[1] < lz['y_max'] and c[2] < lz['z_max'])
    fz = P['flare_zone']
    flares = pick(lambda c: abs(c[0]) > fz['x_min'] and fz['y_min'] < c[1] < fz['y_max'] and fz['z_min'] < c[2] < fz['z_max'])
    print('ahoge %d  tail %d  bangs %d  locks %d  flares %d  untouched %d'
          % (len(ahoge), len(tail), len(bangs), len(locks), len(flares), len(cards) - len(used)))

    edited = []

    def duplicate(c):
        faces = {f for v in c.verts for f in v.link_faces}
        edges = {e for v in c.verts for e in v.link_edges}
        res = bmesh.ops.duplicate(bm, geom=list(c.verts) + list(edges) + list(faces))
        vm = res['vert_map']                          # source vertex -> its copy
        d = Card([vm[v] for v in c.verts])
        d.a, d.b, d.n = c.a, c.b, c.n
        d.orient(down=c.a[2] < 0)
        return d

    # ---- flares over the ears: splay tips out and back (vertical cards only) -------------------------
    skipped = 0
    for c in flares:
        c.orient(down=True)
        if not c.vertical():
            skipped += 1
            continue
        side = 1.0 if c.c[0] > 0 else -1.0
        k = rnd.uniform(0.7, 1.3)
        Lnew = c.L * rnd.uniform(1.10, 1.30)
        new = c.root + np.outer(c.u * Lnew, c.a) + np.outer(c.w, c.b) + np.outer(c.t, c.n)
        new[:, 0] += side * P['flare_out'] * k * c.u ** 1.6
        new[:, 1] -= P['flare_back'] * k * c.u ** 1.6
        set_co(c, new)
        edited.append(c)
    print('flares reshaped %d, %d left as they were (not vertical)' % (len(flares) - skipped, skipped))

    # ---- bangs: strands hugging the forehead; an M (centre longest) ---------------------------------
    xs = sorted(rnd.uniform(-bz['x_max'], bz['x_max']) for _ in bangs)
    rnd.shuffle(bangs)
    for c, x in zip(bangs, xs):
        c.orient(down=True)
        m = smoothstep((abs(x) - P['bang_center_half']) / P['bang_blend'])
        tip = P['bang_tip_center'] + (P['bang_tip_side'] - P['bang_tip_center']) * m
        zr = P['bang_root_z'] + rnd.uniform(-0.004, 0.004)
        pts = []
        for sv in np.linspace(0, 1, 14):
            z = zr - sv * (zr - tip)
            hit = skin((x, 0.6, z), (0, -1, 0))
            y = (hit[1] if hit is not None else 0.12) + P['bang_off'] + 0.012 * sv
            pts.append((x, y, z))
        ws = 1.0 + (P['bang_center_thick'] - 1.0) * (1.0 - m)
        set_co(c, strand(c, pts, across=(1, 0, 0), normal=(0, 1, 0), ws=ws, taper=0.5))
        edited.append(c)

    # ---- side locks: hug the cheek in front of the ear, tips to mid-neck ------------------------------
    for side in (1.0, -1.0):
        mine = [c for c in locks if (c.c[0] > 0) == (side > 0)]
        rnd.shuffle(mine)
        for i, c in enumerate(mine[:P['lock_per_side']]):
            c.orient(down=True)
            y0 = P['lock_y'][i % 2] + rnd.uniform(-0.004, 0.004)
            tip = P['lock_tip_z'] + rnd.uniform(-0.012, 0.012)
            pts = []
            for sv in np.linspace(0, 1, 14):
                z = P['lock_root_z'] - sv * (P['lock_root_z'] - tip)
                y = y0 + 0.010 * sv
                hit = skin((side * 0.6, y, z), (-side, 0, 0))
                x = (hit[0] if hit is not None else side * 0.08) + side * (P['lock_off'] + 0.004 * sv)
                pts.append((x, y, z))
            # across = (0.5, 1, 0): tilted so the flat lock shows a little width from the front, not only from the side
            set_co(c, strand(c, pts, across=(0.5 * side, 1, 0), normal=(side, 0, 0), ws=1.5, taper=0.55))
            edited.append(c)

    # ---- ponytail: a tight bundle at the nape, hanging, flipping out at the tip ----------------------
    tie = np.array(P['tie'])
    src = [c.orient(down=True) for c in tail]
    dup = []
    while src and len(src) + len(dup) < P['tail_strands']:
        dup.append(duplicate(rnd.choice(src)))
    for c in src + dup:
        Lnew = rnd.uniform(*P['tail_len'])
        ang = rnd.uniform(0, 2 * math.pi)
        rr = P['tie_radius'] * rnd.random() ** 0.5
        root = tie + np.array([math.cos(ang) * rr, math.sin(ang) * rr * 0.8, 0.0])
        eps = rnd.uniform(-1, 1)
        pts = []
        for sv in np.linspace(0, 1, 16):
            pts.append(root + np.array([eps * P['tail_splay'] * (0.3 + 1.2 * sv),
                                        -P['tail_back'] * sv - P['tail_flip'] * sv ** 3,
                                        -Lnew * sv]))
        yaw = rnd.uniform(-0.8, 0.8)
        across = (math.cos(yaw), math.sin(yaw), 0.0)
        set_co(c, strand(c, pts, across=across, normal=(0, -1, 0), ws=P['tail_width'], taper=P['tail_taper']))
        edited.append(c)

    # ---- ahoge: ribbons rising from the crown and curling forward ------------------------------------
    while 0 < len(ahoge) < 3:
        ahoge.append(duplicate(ahoge[0]))
    for i, c in enumerate(ahoge[:3]):
        c.orient(down=False)
        f = (1.0, 0.85, 0.72)[i]
        L = P['ahoge_len'] * f
        base = np.array(P['ahoge_base']) + np.array([(-0.007, 0.0, 0.008)[i], (0.0, -0.004, 0.004)[i], 0.0])
        sv = np.linspace(0, 1, 25)
        th = P['ahoge_curl'] * f * sv ** 1.4
        tang = np.stack([np.zeros_like(sv), np.sin(th), np.cos(th)], 1)
        pos = np.vstack([np.zeros(3), np.cumsum(tang[:-1] + tang[1:], 0) * 0.5 * (L / 24)])
        # across = (1, 0.9, 0): the ribbon is twisted so it reads from the front AND the side. With (1, 0, 0) it
        # lies in the side-to-side plane and is a hairline seen from the side, which is where the curl shows.
        set_co(c, strand(c, base + pos, across=(1, 0.9, 0), normal=(0, 1, 0), ws=P['ahoge_width'] * f, taper=0.85))
        edited.append(c)
    for c in ahoge[3:]:
        bmesh.ops.delete(bm, geom=list(c.verts), context='VERTS')

    # ---- keep edited cards out of the head ----------------------------------------------------------
    probe = tree.find_nearest(Vector((0, 0.5, 1.80)))
    print('head normal check: %+.3f (must be > 0)' % ((Vector((0, 0.5, 1.80)) - probe[0]).dot(probe[1])))
    pushed = 0
    for c in edited:
        for v in c.verts:
            loc, nrm, idx, dist = tree.find_nearest(v.co)
            if loc is None:
                continue
            d = (v.co - loc).dot(nrm)
            if d < P['push_out'] and dist < 0.03:
                v.co = loc + nrm * P['push_out']
                pushed += 1
    print('pushed %d vertices out of the head' % pushed)

    # ---- normals: the imported custom normals no longer match the reshaped geometry ------------------
    bm.to_mesh(obj.data)
    bm.free()
    me = obj.data
    bpy.context.view_layer.objects.active = obj
    try:
        bpy.ops.mesh.customdata_custom_splitnormals_clear()
    except RuntimeError as e:
        print('WARNING could not clear custom normals:', e)
    for p in me.polygons:
        p.use_smooth = True
    me.update()

    if a.renders:
        render_preview(obj, head_objs, a.renders)
    for o in head_objs:
        bpy.data.objects.remove(o, do_unlink=True)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.out))
    print('saved', a.out)


def render_preview(obj, head_objs, outdir):
    os.makedirs(outdir, exist_ok=True)
    sc = bpy.context.scene
    for o in head_objs:
        keep = o.type == 'MESH' and o.name.endswith(('_Head_A_Mesh', '_Ears_Mesh'))
        o.hide_set(not keep)
        o.hide_render = not keep
        if o.type == 'MESH':
            o.color = (0.86, 0.72, 0.62, 1)
    obj.color = (0.25, 0.42, 0.85, 1)
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.render.resolution_x = sc.render.resolution_y = 560
    sh = sc.display.shading
    sh.light = 'STUDIO'
    sh.color_type = 'OBJECT'
    sh.show_cavity = True
    w = bpy.data.worlds.new('w')
    w.color = (0.93, 0.93, 0.93)
    sc.world = w
    cam_data = bpy.data.cameras.new('cam')
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = 0.62
    cam = bpy.data.objects.new('cam', cam_data)
    sc.collection.objects.link(cam)
    sc.camera = cam
    centre = Vector((0, -0.01, 1.74))
    views = {
        'front': Vector((0, 1, 0.05)), 'side': Vector((1, 0, 0.05)), 'back': Vector((0, -1, 0.05)),
        'front34': Vector((0.7, 0.7, 0.15)), 'back34': Vector((0.7, -0.7, 0.15)),
    }
    for name, d in views.items():
        d = d.normalized()
        cam.location = centre + d * 3
        cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(outdir, 'lloyd_%s.png' % name)
        bpy.ops.render.render(write_still=True)


main()
