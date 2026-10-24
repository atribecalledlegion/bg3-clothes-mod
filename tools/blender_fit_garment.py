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
    ap.add_argument('--inflate', type=float, default=0.0,
                    help="push every vertex outward along its own normal by this many "
                         "model units after fitting -- gives clearance so the garment "
                         "doesn't clip into the body's curves (chest, glutes) once the "
                         "character leaves the bind pose. 0.01-0.02 is a reasonable start.")
    ap.add_argument('--weights', choices=['surface', 'auto'], default='surface',
                    help="surface: nearest-surface transfer from the vanilla garment (default). "
                         "auto: Blender's bone-heat automatic weights, computed from the armature's "
                         "own bones -- try this when the fitted mesh sits far from the vanilla "
                         "garment's surface (baggy/oversized clothing), where 'nearest surface' "
                         "picks up the wrong bone.")
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

    # The cutter scripts write explicit per-vertex v/vt/vn straight from the source
    # model, which can carry duplicate co-located vertices at seams (common in
    # game-exported meshes) into the OBJ. Weld them into one vertex per position BEFORE
    # weight transfer runs, while there is no skin data yet to disturb: if two duplicate
    # vertices at the same spot ever ended up with DIFFERENT weights (nearest-surface
    # transfer queries each independently), they would tear apart the instant the
    # character left the bind pose -- disconnected rigid fragments, not a shading issue.
    # glTF export re-splits vertices at UV/normal seams automatically regardless, so
    # welding first costs nothing and every split copy then inherits the same weight.
    # Recalculating outward normals here also matters for --inflate below, which pushes
    # each vertex along its own normal: a flipped face would get pushed inward instead.
    bpy.ops.object.select_all(action='DESELECT')
    target.select_set(True)
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    before_verts = len(target.data.vertices)
    bpy.ops.mesh.remove_doubles(threshold=0.0001)
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    print('welded %d -> %d vertices, unified face orientation' % (before_verts, len(target.data.vertices)))

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

    if a.inflate:
        m = target.modifiers.new('Inflate', 'DISPLACE')
        m.direction = 'NORMAL'
        m.mid_level = 0.0
        m.strength = a.inflate
        bpy.ops.object.modifier_apply(modifier=m.name)
        print('inflated by %.4f along vertex normals' % a.inflate)

    # The source model's normals are per-face flat (a cheap low-poly asset, never
    # smoothed), and this pipeline had been carrying them through untouched. A single
    # directional test light barely showed it, but BG3's fuller lighting (multiple
    # lights, specular, ambient occlusion) turns every facet boundary into a visible
    # light/dark seam -- confirmed by shipping a flat single-colour texture and seeing
    # the exact same "checkered" pattern in game, which rules out the texture/atlas as
    # the cause. Recomputing smooth normals (splitting only at genuinely sharp edges)
    # removes the per-facet lighting steps this was causing.
    #
    # Done BEFORE the armature is added: applying a modifier that is not first in the
    # stack forces Blender to implicitly bake everything before it too, and doing that
    # to an unapplied Armature modifier warns "result may not be as expected" -- it can
    # rebake the mesh's bind-pose coordinates out of sync with the inverse-bind matrices
    # this item later copies from vanilla in gltf_retarget.py, which reads as entire
    # regions rigidly bound to the wrong position reference (disconnected rigid chunks
    # in game), not the small per-vertex noise weight smoothing alone can fix.
    bpy.ops.object.select_all(action='DESELECT')
    target.select_set(True)
    bpy.context.view_layer.objects.active = target
    # The OBJ carries explicit per-vertex vn from the source model, which Blender loads
    # as baked Custom Split Normal data -- that data takes priority at export time and
    # can silently override the angle-based smoothing below. Clear it first so the
    # recompute actually takes effect.
    try:
        bpy.ops.mesh.customdata_custom_splitnormals_clear()
    except RuntimeError:
        pass
    before = set(target.modifiers.keys())
    bpy.ops.object.shade_auto_smooth()
    added = [m.name for m in target.modifiers if m.name not in before]
    for name in added:
        bpy.ops.object.modifier_apply(modifier=name)
    print('recomputed smooth normals (applied modifier: %s)' % added)

    if a.weights == 'surface':
        # nearest-surface interpolation from the vanilla garment
        bpy.ops.object.select_all(action='DESELECT')
        vanilla.select_set(True)
        target.select_set(True)
        bpy.context.view_layer.objects.active = vanilla
        bpy.ops.object.data_transfer(data_type='VGROUP_WEIGHTS', vert_mapping='POLYINTERP_NEAREST',
                                     layers_select_src='ALL', layers_select_dst='NAME')
        # Nearest-surface transfer copies each vertex's weights from whichever point on
        # the vanilla mesh happens to be geometrically closest -- a pure proximity lookup
        # with no notion of anatomical continuity. When our mesh's shape diverges a lot
        # from the thin vanilla reference (a baggy jacket vs. a fitted shirt), that
        # nearest-point correspondence can jump discontinuously as you move along the
        # surface, so adjacent vertices end up rigidly bound to different, non-blending
        # bones. Smoothing weights across the MESH'S OWN connectivity (not the vanilla
        # source) closes small local gaps -- it will not fix a whole region bound to a
        # flatly wrong bone, only disagreement between neighbours.
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.object.vertex_group_smooth(group_select_mode='ALL', factor=0.5, repeat=6)
        bpy.ops.object.mode_set(mode='OBJECT')
        print('smoothed vertex group weights across mesh connectivity')
        mod = target.modifiers.new('Armature', 'ARMATURE')
        mod.object = armature
        target.parent = armature
    else:
        # bone-heat automatic weights, straight from the armature -- ignores the vanilla
        # garment's shape entirely, so it does not matter how far our mesh bulges from it.
        # The heat-diffusion solver can fail outright when a bone has no nearby geometry
        # to enclose it -- e.g. a jacket that stops at the wrist has nothing anywhere near
        # the ~40 finger bones in BG3's 82-bone arm rig. Exclude bones the garment cannot
        # possibly cover from deformation first, so the solver only has to satisfy bones
        # that matter; restore the flags afterward since this is the shared vanilla
        # armature, reused for every item built against it.
        # Dummy_Root is a non-deforming helper bone sitting far from the body; a
        # topologically disconnected island in the source mesh (e.g. a leg not
        # vertex-welded to the rest of the pants) gets no useful heat diffusion from
        # nearby real bones and can land on it instead -- those vertices then never
        # move with the character at all, reading in-game as cloth that doesn't
        # follow the limb. Exclude it for the same reason as the finger bones.
        excluded, changed = ('Finger', 'Toes', 'Dummy_Root'), []
        for bone in armature.data.bones:
            if any(x in bone.name for x in excluded) and bone.use_deform:
                bone.use_deform = False
                changed.append(bone.name)
        bpy.ops.object.select_all(action='DESELECT')
        target.select_set(True)
        armature.select_set(True)
        bpy.context.view_layer.objects.active = armature
        bpy.ops.object.parent_set(type='ARMATURE_AUTO')
        for name in changed:
            armature.data.bones[name].use_deform = True
        print('excluded %d finger/toe bones from auto-weight solve' % len(changed))

        # Any vertex the heat solver left with zero total weight (typically a cuff/hem
        # that runs past where the deforming skeleton actually ends, e.g. our sleeve
        # extending beyond the Wrist bone into finger territory, or a decal-like patch
        # -- an ankle wrap, a pouch flap -- that sits close to the body but is its own
        # disconnected island the heat solver can't diffuse into) gets exported with a
        # synthetic "neutral_bone" placeholder by Blender's glTF exporter -- a bone
        # gltf_retarget.py's by-name remap cannot find in the vanilla skeleton.
        #
        # Copy the full multi-bone blend from the nearest vertex that DID solve
        # correctly, rather than picking a single nearest bone HEAD: a disconnected
        # patch usually sits right against the real surface, so its nearest solved
        # neighbour already carries the right blend (e.g. Knee_L/Hip_L mix at a
        # bending joint) -- a single nearest-bone-head guess can land on the wrong
        # bone (an ankle patch nearest to a Hip twist-helper bone's head, say) even
        # though the geometry it sits on is clearly Knee territory.
        solved = [v for v in target.data.vertices if sum(g.weight for g in v.groups) >= 1e-6]
        solved_pos = [target.matrix_world @ v.co for v in solved]
        unsolved = [v for v in target.data.vertices if sum(g.weight for g in v.groups) < 1e-6]
        fixed, by_group = 0, {}
        for v in unsolved:
            wp = target.matrix_world @ v.co
            nearest = min(range(len(solved)), key=lambda i: (solved_pos[i] - wp).length_squared)
            src = solved[nearest]
            for g in src.groups:
                name = target.vertex_groups[g.group].name
                vg = target.vertex_groups.get(name) or target.vertex_groups.new(name=name)
                vg.add([v.index], g.weight, 'REPLACE')
                by_group[name] = by_group.get(name, 0) + g.weight
            fixed += 1
        if fixed:
            print('copied weights onto %d zero-weight vertices from nearest solved vertex: %s' % (fixed, by_group))
    print('vertex groups on fitted mesh: %d' % len(target.vertex_groups))

    bpy.data.objects.remove(vanilla, do_unlink=True)
    bpy.ops.object.select_all(action='DESELECT')
    target.select_set(True)
    armature.select_set(True)
    bpy.ops.export_scene.gltf(filepath=os.path.abspath(a.out), export_format='GLTF_SEPARATE',
                              use_selection=True,
                              export_yup=True, export_skins=True, export_normals=True,
                              export_tangents=True, export_materials='NONE',
                              export_apply=False)
    print('wrote', a.out)


if __name__ == '__main__':
    main()
