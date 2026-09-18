"""Fit a static garment mesh onto a vanilla BG3 garment's skeleton (Blender, headless).

    "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b -P tools/blender_fit_garment.py -- \
        --vanilla work/pants_vanilla.gltf --mesh extracted/naruto-r/naruto_pants.obj \
        --out work/naruto_pants_rigged.gltf --tris 6000 \
        --translate 0 0.998 0 --scale 1.083 --post-translate 0 0.192 0

The imported model is a static scan: no skeleton, and in its own coordinate space. BG3
needs a mesh skinned to the garment's bones, so:

  1. import the vanilla garment exported from its GR2 (mesh + armature + bone weights)
  2. import the static mesh and move/scale it onto the same body
  3. decimate it to a game-sized triangle count
  4. copy the vanilla mesh's bone weights onto it (nearest-surface interpolation), which
     is what makes it bend with the character
  5. bind it to the armature and export glTF for Divine -a convert-model

Divine then writes the GR2, with --conform-path pointing at the vanilla GR2 so the
skeleton and bone bindings match what the game expects.
"""
import argparse, os, sys

import bpy


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument('--vanilla', required=True, help='vanilla garment .gltf (from its GR2)')
    ap.add_argument('--mesh', required=True, help='static mesh to fit (.obj)')
    ap.add_argument('--out', required=True, help='output .gltf')
    ap.add_argument('--tris', type=int, default=6000)
    ap.add_argument('--translate', nargs=3, type=float, default=[0, 0, 0],
                    help='applied to the static mesh BEFORE scaling')
    ap.add_argument('--scale', type=float, default=1.0)
    ap.add_argument('--scale-xz', type=float, default=1.0,
                    help='extra width/depth factor: imported characters are often stockier '
                         'than BG3 bodies, so a garment scaled to the right length is too baggy')
    ap.add_argument('--post-translate', nargs=3, type=float, default=[0, 0, 0])
    a = ap.parse_args(argv)

    clear()
    bpy.ops.import_scene.gltf(filepath=os.path.abspath(a.vanilla))
    vanilla = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
    armature = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
    print('vanilla mesh %s (%d tris), armature %s (%d bones)'
          % (vanilla.name, len(vanilla.data.polygons), armature.name, len(armature.data.bones)))

    before = set(bpy.context.scene.objects)
    bpy.ops.wm.obj_import(filepath=os.path.abspath(a.mesh))
    target = next(o for o in set(bpy.context.scene.objects) - before if o.type == 'MESH')
    target.name = 'Fitted'

    # Both importers already convert Y-up to Blender's Z-up, so all the fitting happens
    # in Blender space. --translate/--post-translate are given in the game's Y-up axes
    # (x, up, forward) and are mapped here; do NOT rotate the vertices by hand, or the
    # exporter's own Z-up -> Y-up conversion applies the rotation a second time.
    def to_blender(t):
        x, up, fwd = t
        return x, -fwd, up

    tx, ty, tz = to_blender(a.translate)
    px, py, pz = to_blender(a.post_translate)
    bpy.ops.object.select_all(action='DESELECT')
    target.select_set(True)
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for v in target.data.vertices:
        v.co = ((v.co[0] + tx) * a.scale * a.scale_xz + px,
                (v.co[1] + ty) * a.scale * a.scale_xz + py,
                (v.co[2] + tz) * a.scale + pz)

    def bbox(o):
        cos = [v.co for v in o.data.vertices]
        lo = [min(c[i] for c in cos) for i in range(3)]
        hi = [max(c[i] for c in cos) for i in range(3)]
        return '[%s] .. [%s]' % (', '.join('%.3f' % v for v in lo), ', '.join('%.3f' % v for v in hi))

    print('BBOX vanilla (blender space) %s' % bbox(vanilla))
    print('BBOX fitted  (blender space) %s' % bbox(target))

    tris = len(target.data.polygons)
    if tris > a.tris:
        m = target.modifiers.new('Decimate', 'DECIMATE')
        m.ratio = a.tris / tris
        bpy.ops.object.modifier_apply(modifier=m.name)
        print('decimated %d -> %d tris' % (tris, len(target.data.polygons)))

    # weights: nearest-surface interpolation from the vanilla garment
    bpy.ops.object.select_all(action='DESELECT')
    vanilla.select_set(True)
    target.select_set(True)
    bpy.context.view_layer.objects.active = vanilla
    bpy.ops.object.data_transfer(data_type='VGROUP_WEIGHTS', vert_mapping='POLYINTERP_NEAREST',
                                 layers_select_src='ALL', layers_select_dst='NAME')
    print('vertex groups on fitted mesh: %d' % len(target.vertex_groups))

    mod = target.modifiers.new('Armature', 'ARMATURE')
    mod.object = armature
    target.parent = armature

    bpy.data.objects.remove(vanilla, do_unlink=True)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=os.path.abspath(a.out), export_format='GLTF_SEPARATE',
                              export_yup=True, export_skins=True, export_normals=True,
                              export_tangents=True, export_materials='NONE',
                              export_apply=False)
    print('wrote', a.out)


if __name__ == '__main__':
    main()
