"""Render hair meshes from four sides and report what is in them (Blender, headless).

    "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b -P tools/hair_render.py -- \
        --out build/hair_renders  a.glb b.dae ...

For each input (.glb / .gltf / .dae / .obj) it writes <out>/<stem>_<view>.png for the views
front, side, back and top, and prints one "STAT" block per file: triangle counts, the
bounding box, and the armature bones / vertex groups the mesh is weighted to.

Orientation: Divine's glTF export of a BG3 GR2 faces -Z in glTF space. Blender's glTF importer
maps glTF (x, y, z) to Blender (x, -z, y), so the character faces +Y in Blender and the
"front" camera sits on the +Y side. A DAE import can differ, so check a render before
trusting a view name (the fringe and face side make it obvious).

Renders use the Workbench engine (flat, fast, no textures) because the aim is silhouette.
"""
import argparse, math, os, sys

import bpy
from mathutils import Vector

VIEWS = {
    # name: (camera direction FROM the model centre, Euler rotation of a camera looking back at it)
    'front': (Vector((0, 1, 0)), (math.radians(90), 0, math.radians(180))),
    'back': (Vector((0, -1, 0)), (math.radians(90), 0, 0)),
    'side': (Vector((1, 0, 0)), (math.radians(90), 0, math.radians(90))),
    'top': (Vector((0, 0, 1)), (0, 0, 0)),
    # three-quarter views: camera direction from the centre, looking back at it (rotation filled in by render())
    'front34': (Vector((0.75, 0.66, 0.18)).normalized(), None),
    'back34': (Vector((0.75, -0.66, 0.18)).normalized(), None),
}


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def import_any(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in ('.glb', '.gltf'):
        bpy.ops.import_scene.gltf(filepath=path)
    elif ext == '.dae':
        bpy.ops.wm.collada_import(filepath=path)
    elif ext == '.obj':
        bpy.ops.wm.obj_import(filepath=path)
    else:
        raise SystemExit('unsupported: ' + path)


def world_bounds(objs):
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    for o in objs:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            lo = Vector((min(lo[i], w[i]) for i in range(3)))
            hi = Vector((max(hi[i], w[i]) for i in range(3)))
    return lo, hi


def report(path, meshes, lo, hi):
    print('STAT', os.path.basename(path))
    print('STAT   bbox min %.3f %.3f %.3f  max %.3f %.3f %.3f  (size %.3f %.3f %.3f)'
          % (*lo, *hi, *(hi - lo)))
    for o in meshes:
        me = o.data
        tris = sum(len(p.vertices) - 2 for p in me.polygons)
        groups = [g.name for g in o.vertex_groups]
        print('STAT   mesh %-28s verts %6d tris %6d uv %d mats %s'
              % (o.name, len(me.vertices), tris, len(me.uv_layers),
                 [m.name for m in me.materials if m]))
        print('STAT     vertex groups (%d): %s' % (len(groups), ', '.join(groups[:24])
                                                   + (' ...' if len(groups) > 24 else '')))
    for a in [o for o in bpy.data.objects if o.type == 'ARMATURE']:
        names = [b.name for b in a.data.bones]
        print('STAT   armature %s: %d bones: %s' % (a.name, len(names), ', '.join(names[:30])
                                                    + (' ...' if len(names) > 30 else '')))


def render(path, out, res, refs=(), views=None):
    clear()
    import_any(path)
    hair_objs = {o.name for o in bpy.data.objects}
    for r in refs:
        import_any(r)
    ref_objs = [o for o in bpy.data.objects if o.name not in hair_objs]
    # Blender's glTF importer adds a 42-vertex 'Icosphere' as the armature's bone-display shape.
    # It has no material and no weights, is not part of the hair, and must never be exported.
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name.startswith('Icosphere') and not o.vertex_groups:
            o.hide_render = True
            o.hide_viewport = True
    for o in ref_objs:
        # reference head: skin and ears only, no LODs, eyes, mouth or lashes
        if o.type == 'MESH' and (('LOD' in o.name) or any(k in o.name for k in ('Eye', 'Mouth', 'Tear', 'Lash', 'Scalp'))):
            o.hide_render = True
            o.hide_viewport = True
    meshes = [o for o in bpy.data.objects if o.type == 'MESH' and not o.hide_render and o not in ref_objs]
    if not meshes:
        print('STAT no mesh in', path)
        return
    lo, hi = world_bounds(meshes)
    report(path, meshes, lo, hi)
    centre = (lo + hi) / 2
    span = max((hi - lo)[i] for i in range(3)) * 1.25

    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.render.resolution_x = sc.render.resolution_y = res
    sc.render.film_transparent = False
    sh = sc.display.shading
    sh.light = 'STUDIO'
    sh.color_type = 'OBJECT'
    sh.show_cavity = True
    sc.view_settings.view_transform = 'Standard'
    w = bpy.data.worlds.new('w')
    w.color = (0.92, 0.92, 0.92)
    sc.world = w

    cam_data = bpy.data.cameras.new('cam')
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = span
    cam = bpy.data.objects.new('cam', cam_data)
    sc.collection.objects.link(cam)
    sc.camera = cam

    for o in bpy.data.objects:
        o.color = (0.86, 0.72, 0.62, 1) if o in ref_objs else (0.25, 0.42, 0.85, 1)
    stem = os.path.splitext(os.path.basename(path))[0]
    for name, (direction, rot) in VIEWS.items():
        if views and name not in views:
            continue
        cam.location = centre + direction * 3.0
        if rot is None:
            cam.rotation_euler = (-direction).to_track_quat('-Z', 'Y').to_euler()
        else:
            cam.rotation_euler = rot
        sc.render.filepath = os.path.join(out, '%s_%s.png' % (stem, name))
        bpy.ops.render.render(write_still=True)


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--res', type=int, default=360)
    ap.add_argument('--ref', action='append', default=[], help='extra .glb drawn in skin colour (e.g. a head)')
    ap.add_argument('--views', nargs='*', help='subset of: ' + ', '.join(VIEWS))
    ap.add_argument('files', nargs='+')
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    for f in a.files:
        render(os.path.abspath(f), a.out, a.res, [os.path.abspath(r) for r in a.ref], a.views)


main()
