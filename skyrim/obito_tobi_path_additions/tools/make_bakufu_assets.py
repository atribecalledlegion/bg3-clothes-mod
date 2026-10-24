"""Fire-vortex assets for Katon: Bakufu Ranbu, from Elemental Destruction's tornado projectile.
usage: make_bakufu_assets.py <tornadoprojectile01.nif> <gradfireexplosion.dds> <gradfirestream02.dds> <out root> [scale]
The mesh's two colour ramps are swapped for fire ramps. The new ramp files get names of the same length
as the old ones, so the paths are replaced in place and no NIF block sizes change. Root node is scaled up."""
import struct, sys, os, re, shutil
src, g1, g2, out = sys.argv[1:5]; scale = float(sys.argv[5]) if len(sys.argv) > 5 else 1.6
d = bytearray(open(src, "rb").read())
SWAP = {b"gradbluebright": b"GradBakufuFire", b"gradicestorm": b"GradBakufu02"}
for old, new in SWAP.items():
    assert len(old) == len(new)
    hits = [m.start() for m in re.finditer(re.escape(old), bytes(d), re.I)]
    assert hits, old
    for h in hits: d[h:h+len(new)] = new
    print(f"{old.decode()} -> {new.decode()}: {len(hits)} reference(s)")
# root BSFadeNode: name, extra-data count + refs, controller, flags, translation, rotation, scale
nl = d.index(b"\n"); p = nl + 1 + 9; nblocks = struct.unpack_from("<I", d, p)[0]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util
root = None
spec = importlib.util.spec_from_file_location("nh", os.environ["NIFHDR"]); nh = importlib.util.module_from_spec(spec); spec.loader.exec_module(nh)
h = nh.parse(src); assert h["blocks"][0][1] in ("BSFadeNode", "NiNode")
o = h["blocks"][0][2]; nextra = struct.unpack_from("<I", d, o + 4)[0]
so = o + 4 + 4 + 4 * nextra + 4 + 4 + 12 + 36
print("root scale", struct.unpack_from("<f", d, so)[0], "->", scale); struct.pack_into("<f", d, so, scale)
# Optional: tip the vortex on its side (rotation about X) so it spins toward the target instead of
# standing upright. Projectiles fly along +Y; the tornado's axis is +Z. Only billboard children are
# animated, so the root transform is free to change.
import math
rot_x = float(os.environ.get("BAKUFU_ROT_X", "0"))
if rot_x:
    # The root's rotation is overwritten by the engine every frame (projectile heading), and the cloud
    # pieces are ROTATE_ABOUT_UP billboards, so tilt the particle-emitter group that makes the funnel.
    c, s = math.cos(math.radians(rot_x)), math.sin(math.radians(rot_x))
    target = None
    for i, t, off, size in h["blocks"]:
        if t == "NiNode" and h["strings"][struct.unpack_from("<i", d, off)[0]] == "PositionHelper02": target = off
    assert target is not None, "PositionHelper02 not found"
    ne2 = struct.unpack_from("<I", d, target + 4)[0]; ro2 = target + 4 + 4 + 4 * ne2 + 4 + 4 + 12
    struct.pack_into("<9f", d, ro2, 1, 0, 0, 0, c, -s, 0, s, c)
    print("PositionHelper02 rotated", rot_x, "deg about X")
# Colour: the tornado's shaders only use the ramps for alpha (palette colour off) and glow a flat grey.
# Turn palette colour on wherever a ramp is set (white emissive so the fire ramp shows through) and
# make the ramp-less glow cards orange.
RAMP_TINT = (1.0, 0.7, 0.45)    # warm tint on top of the fire ramps
GLOW_SCALE = float(os.environ.get('BAKUFU_GLOW', '0.35'))   # emissive multiplier scale
def sstr_end(o): return o + 4 + struct.unpack_from("<I", d, o)[0]
for i, t, off, size in h["blocks"]:
    if t != "BSEffectShaderProperty": continue
    o = off + 4; ne = struct.unpack_from("<I", d, o)[0]; o += 4 + 4 * ne + 4
    fo = o; f1 = struct.unpack_from("<I", d, fo)[0]; o += 8 + 16
    o = sstr_end(o) + 4 + 16
    co = o; o += 16 + 4 + 4
    n = struct.unpack_from("<I", d, o)[0]; grey = bytes(d[o+4:o+4+n])
    a = struct.unpack_from("<f", d, co + 12)[0]
    mult = struct.unpack_from("<f", d, co + 16)[0]
    # First try (white emissive at the tornado's x2-x5 glow) blew out to white: layers are additive.
    if grey:
        struct.pack_into("<I", d, fo, f1 | 0x10); struct.pack_into("<3f", d, co, *RAMP_TINT)
    else:
        struct.pack_into("<3f", d, co, 1.0, 0.45, 0.1)
    struct.pack_into("<f", d, co + 16, mult * GLOW_SCALE)
    print(f"shader #{i}: {'palette colour on, ramp ' + grey.decode().split(chr(92))[-1] if grey else 'glow -> orange'}, glow x{mult:.2f} -> x{mult * GLOW_SCALE:.2f}")
os.makedirs(os.path.join(out, "meshes/magic/ctob"), exist_ok=True); os.makedirs(os.path.join(out, "textures/effects/gradients"), exist_ok=True)
open(os.path.join(out, "meshes/magic/ctob/bakufuranbuprojectile.nif"), "wb").write(bytes(d))
shutil.copyfile(g1, os.path.join(out, "textures/effects/gradients/GradBakufuFire.dds"))
shutil.copyfile(g2, os.path.join(out, "textures/effects/gradients/GradBakufu02.dds"))
print("written")
