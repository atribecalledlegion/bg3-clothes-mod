"""Render a hair on the Dhaen head from front / side / back / top (Blender, headless, Workbench: silhouette only).

    blender -b -P items/pk_hair19_dhaen/fit_preview.py -- --head <head.glb> --hair <hair.glb> \
        --offset dx dy dz --scale sx sy sz --out <dir> --tag <name>

Offsets/scales are in glTF (Divine) space, the character faces -Z; --scale is applied about the head bone (0, y0, z0)
given by --pivot. Blender maps glTF (x, y, z) to (x, -z, y), so the character faces +Y in Blender.
"""
import argparse, math, os, sys
import bpy
from mathutils import Vector

ap = argparse.ArgumentParser()
ap.add_argument('--head'); ap.add_argument('--hair'); ap.add_argument('--out'); ap.add_argument('--tag', default='fit')
ap.add_argument('--offset', nargs=3, type=float, default=[0, 0, 0])
ap.add_argument('--scale', nargs=3, type=float, default=[1, 1, 1])
ap.add_argument('--pivot', nargs=3, type=float, default=[0, 0, 0])
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
os.makedirs(a.out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)


def imp(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    return [o for o in bpy.data.objects if o not in before]


def to_bl(v):  # glTF -> Blender
    return Vector((v[0], -v[2], v[1]))


head_names = [o.name for o in imp(a.head)]
hair_names = [o.name for o in imp(a.hair)]
for o in list(bpy.data.objects):
    if o.type != 'MESH' or 'Icosphere' in o.name or 'LOD1' in o.name:
        bpy.data.objects.remove(o, do_unlink=True)
meshes_h = [bpy.data.objects[n] for n in head_names if n in bpy.data.objects]
meshes_r = [bpy.data.objects[n] for n in hair_names if n in bpy.data.objects]
# hair: freeze the pose, drop armature modifiers, then scale about the pivot and move
piv = to_bl(a.pivot); off = to_bl(a.offset)
sc = Vector((a.scale[0], a.scale[2], a.scale[1]))
for o in meshes_r:
    for m in list(o.modifiers):
        o.modifiers.remove(m)
    mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    me = o.data
    for v in me.vertices:
        p = mw @ v.co
        p = piv + Vector((sc.x * (p.x - piv.x), sc.y * (p.y - piv.y), sc.z * (p.z - piv.z))) + off
        v.co = p
    o.matrix_world = o.matrix_world.Identity(4)
for o in meshes_h:
    mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw

def mat(name, col):
    m = bpy.data.materials.new(name); m.diffuse_color = col; return m
skin, dark = mat('skin', (0.55, 0.36, 0.28, 1)), mat('hair', (0.10, 0.09, 0.09, 1))
for o in meshes_h:
    o.data.materials.clear(); o.data.materials.append(skin)
for o in meshes_r:
    o.data.materials.clear(); o.data.materials.append(dark)

# head centre for the camera
pts = [o.matrix_world @ v.co for o in meshes_h for v in o.data.vertices]
c = sum(pts, Vector()) / len(pts)
sc_ = bpy.context.scene
sc_.render.engine = 'BLENDER_WORKBENCH'
sc_.display.shading.light = 'STUDIO'; sc_.display.shading.color_type = 'MATERIAL'
sc_.render.resolution_x = 700; sc_.render.resolution_y = 700
sc_.world = bpy.data.worlds.new('w'); sc_.world.color = (0.8, 0.85, 0.9)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc_.collection.objects.link(cam); sc_.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 0.75
VIEWS = {'front': Vector((0, 1, 0)), 'back': Vector((0, -1, 0)), 'side': Vector((1, 0, 0)), 'top': Vector((0, 0, 1))}
for name, d in VIEWS.items():
    cam.location = c + d * 2
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc_.render.filepath = os.path.abspath(os.path.join(a.out, '%s_%s.png' % (a.tag, name)))
    bpy.ops.render.render(write_still=True)
print('rendered', a.tag)
