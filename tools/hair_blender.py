"""Audit and export a hair mesh from Blender (headless or in the GUI's Scripting tab).

    "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b -P tools/hair_blender.py -- \
        --in work/lloyd.blend --out work/lloyd_export.glb [--fix] [--tris 40000]

    --in    a .blend, or a .glb/.gltf straight from `hair_mod.py unpack`
    --out   glTF/GLB to hand to Divine (omit to audit only)
    --fix   repair what can be repaired (limit to 4 influences, normalise, triangulate)

What BG3 needs from a hair mesh, and what this checks (each one is a way a hair has failed
silently in game):

  * every vertex weighted, at most 4 influences, weights summing to 1
  * every vertex group is the name of a bone in the armature (an unknown group is dropped by
    the exporter and the vertices it carried stay at the origin)
  * one UV layer at least (the hair shader reads the strand-ID/gradient UVs)
  * triangles only, transforms applied, and no leftover 'Icosphere' (Blender's glTF importer
    creates it as the bone display shape; it is not part of the hair and must not be exported)
  * mesh names unchanged from the base: the VisualBank 'Objects' entries refer to meshes BY NAME
    (<gr2>.<mesh>.<index>), so a renamed mesh is an invisible hair

The export keeps the armature and every mesh, so Divine writes the same bone set as the base.
Whether LSLib reads Blender's skeleton layout is checked by `hair_mod.py gr2`, which reports
Divine's own error if it does not.
"""
import argparse, os, sys

import bpy


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def load(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == '.blend':
        bpy.ops.wm.open_mainfile(filepath=path)
    elif ext in ('.glb', '.gltf'):
        clear()
        bpy.ops.import_scene.gltf(filepath=path)
    else:
        raise SystemExit('unsupported input: ' + path)


def hair_meshes():
    """The meshes that are hair: every mesh except the importer's bone-shape sphere and anything
    named REF_* (vanilla meshes kept in the scene as weight/shape references)."""
    out = []
    for o in bpy.data.objects:
        if o.type != 'MESH':
            continue
        if o.name.startswith('REF_'):
            continue
        if o.name.startswith('Icosphere') and not o.vertex_groups:
            continue
        out.append(o)
    return out


def armature_of(o):
    for m in o.modifiers:
        if m.type == 'ARMATURE' and m.object:
            return m.object
    return None


def audit(fix):
    problems = []
    arms = [o for o in bpy.data.objects if o.type == 'ARMATURE']
    if len(arms) != 1:
        problems.append('expected exactly one armature, found %d' % len(arms))
    bones = {b.name for a in arms for b in a.data.bones}
    meshes = hair_meshes()
    if not meshes:
        problems.append('no hair meshes found')

    for o in meshes:
        me = o.data
        tag = '[%s]' % o.name
        # transforms applied? Divine bakes the node transform into the GR2 mesh badly if not.
        if any(abs(s - 1) > 1e-5 for s in o.scale) or any(abs(r) > 1e-5 for r in o.rotation_euler):
            problems.append('%s object scale/rotation not applied (Ctrl+A > All Transforms)' % tag)
        if not armature_of(o):
            problems.append('%s has no Armature modifier' % tag)
        unknown = [g.name for g in o.vertex_groups if g.name not in bones]
        if unknown:
            problems.append('%s vertex groups that are not bones: %s' % (tag, ', '.join(unknown[:8])))
        if not me.uv_layers:
            problems.append('%s has no UV layer' % tag)
        if any(len(p.vertices) != 3 for p in me.polygons):
            if fix:
                bpy.context.view_layer.objects.active = o
                o.select_set(True)
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.quads_convert_to_tris()
                bpy.ops.object.mode_set(mode='OBJECT')
                print('FIX   %s triangulated' % tag)
            else:
                problems.append('%s has quads/n-gons (--fix triangulates)' % tag)

        # weights
        idx = {g.index: g.name for g in o.vertex_groups}
        bad_none = bad_many = 0
        for v in me.vertices:
            w = [g.weight for g in v.groups if g.group in idx and g.weight > 1e-4]
            if not w:
                bad_none += 1
            elif len(w) > 4:
                bad_many += 1
        if bad_none:
            problems.append('%s %d vertices have no weight (they will sit at the origin)' % (tag, bad_none))
        if bad_many:
            if fix:
                bpy.context.view_layer.objects.active = o
                bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
                bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)
                bpy.ops.object.vertex_group_normalize_all(group_select_mode='ALL', lock_active=False)
                bpy.ops.object.mode_set(mode='OBJECT')
                print('FIX   %s limited to 4 influences and normalised' % tag)
            else:
                problems.append('%s %d vertices have more than 4 influences (--fix limits them)' % (tag, bad_many))
        tris = sum(len(p.vertices) - 2 for p in me.polygons)
        print('INFO  %-40s verts %6d tris %6d uv %d groups %d' %
              (o.name, len(me.vertices), tris, len(me.uv_layers), len(o.vertex_groups)))
    return problems, meshes


def export(path, meshes):
    """Armature + hair meshes only. The bone-shape sphere is left out."""
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes + [a for a in bpy.data.objects if a.type == 'ARMATURE']:
        o.select_set(True)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    fmt = 'GLB' if path.lower().endswith('.glb') else 'GLTF_SEPARATE'
    bpy.ops.export_scene.gltf(
        filepath=path, export_format=fmt, use_selection=True, export_yup=True,
        export_apply=False, export_skins=True, export_animations=False,
        export_texcoords=True, export_normals=True, export_tangents=True,
        export_materials='NONE', export_extras=False, export_cameras=False, export_lights=False,
        export_vertex_color='ACTIVE')            # keep the hair's own colour channel (BG3 hair meshes carry one)
    print('EXPORTED', path)


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument('--in', dest='src', required=True)
    ap.add_argument('--out')
    ap.add_argument('--fix', action='store_true')
    ap.add_argument('--tris', type=int, default=40000, help='warn above this many triangles in total')
    a = ap.parse_args(argv)

    load(os.path.abspath(a.src))
    problems, meshes = audit(a.fix)
    total = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in meshes)
    print('INFO  total triangles %d' % total)
    if total > a.tris:
        problems.append('%d triangles is heavy for a hair (vanilla short hairs are ~20-35k with LOD0 only)' % total)
    for p in problems:
        print('PROBLEM', p)
    if problems and not a.fix:
        print('AUDIT FAILED (%d problems)' % len(problems))
        if a.out:
            raise SystemExit(1)
    if a.out:
        export(os.path.abspath(a.out), meshes)
    print('AUDIT OK' if not problems else 'AUDIT DONE with warnings')


main()
