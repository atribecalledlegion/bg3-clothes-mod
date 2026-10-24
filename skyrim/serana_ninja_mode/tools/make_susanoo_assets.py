"""Black-ice Susanoo ribcage: The Uchiha Clan's Sasuke ribcage (armor\\The Uchiha Clan\\Sasuke\\susanoo.nif + its
particles, and his Susanoo arrow), recoloured from Sasuke's purple to Serana's black ice, for her flash Susanoo
(Ninja Mode: the ribcage at mastery 55, the spectral bow's arrow at 65).

Where the purple lives, and what each becomes:
- susanoo.dds (flat translucent lavender with dark line work) and susanoomembraneshader.dds (white -> purple ramp):
  remapped by brightness onto a black-ice ramp (near black -> deep steel blue -> ice white), alpha kept.
- the ribcage's emissive colour (0.49, 0, 0.6) and the colour controller keys that pulse it (NiPosData), the
  particles' emissive colours and BSPSysSimpleColorModifier colours: re-hued to ice blue, brightness kept.
- the particle flames' palettes (GradPurpleFlame01, GradVioBright): vanilla frost palettes.
Texture paths are pointed at textures\\SNJ\\susanoo\\, meshes are written to meshes\\SNJ\\susanoo\\.

usage: make_susanoo_assets.py <dir with susanoo.nif, susanooparticles.nif and their .dds> <mod root>
"""
import os, struct, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nif_util import Nif, lighting_emissive_offset, effect_emissive_offset

SRC, ROOT = sys.argv[1], sys.argv[2]
ICE = (0.45, 0.75, 1.0)                                   # hue of her ice glow (max channel 1)
GLOW = 0.45                                               # v2: darker (v1 read bright blue, not black ice)
FX_MULT = 0.6                                             # effect shaders' emissive multiple, scaled
RAMP = [(0.0, (3, 4, 8)), (0.45, (12, 22, 38)), (0.75, (30, 56, 86)), (1.0, (150, 190, 220))]
OLD_TEX, NEW_TEX = b'textures\\armor\\the uchiha clan\\sasuke\\', b'textures\\SNJ\\susanoo\\'
PALETTES = {b'textures\\effects\\gradients\\GradPurpleFlame01.dds': b'textures\\effects\\gradients\\GradFrostIceForm.dds',
            b'textures\\effects\\gradients\\GradVioBright.dds': b'textures\\effects\\gradients\\GradIceSparkle.dds'}


def ramp(t):
    for (t0, c0), (t1, c1) in zip(RAMP, RAMP[1:]):
        if t <= t1:
            k = (t - t0) / (t1 - t0) if t1 > t0 else 0.0
            return tuple(round(a + (b - a) * k) for a, b in zip(c0, c1))
    return RAMP[-1][1]


def recolour(name):
    im = Image.open(os.path.join(SRC, name)).convert('RGBA')
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
            px[x, y] = ramp(min(1.0, lum ** 1.3)) + (a,)
    os.makedirs(os.path.join(ROOT, 'textures', 'SNJ', 'susanoo'), exist_ok=True)
    im.save(os.path.join(ROOT, 'textures', 'SNJ', 'susanoo', name), format='DDS')
    print('  texture', name)


glow = GLOW                                               # per mesh: the arrow glows brighter than the ribs


def ice(c):
    """Same brightness (strongest channel), ice-blue hue."""
    m = max(c[:3]) * glow
    return tuple(m * h for h in ICE)


def tint_at(b, p, label):
    old = struct.unpack_from('<3f', b, p)
    struct.pack_into('<3f', b, p, *ice(old))
    print('  %s %s -> %s' % (label, tuple(round(v, 2) for v in old), tuple(round(v, 2) for v in ice(old))))


def pos_data_keys(b):
    """NiPosData: num keys, key type (1 linear, 2 quadratic, 3 TBC), keys of time + vec3 (+ 2 tangents / tbc)."""
    n, kind = struct.unpack_from('<II', b, 0)
    step = {1: 16, 2: 40, 3: 28}[kind] if n else 0
    return [4 + 4 + i * step + 4 for i in range(n)]       # offset of each key's value


def fix(nif_name, out_name, brightness=GLOW):
    global glow
    glow = brightness
    n = Nif(os.path.join(SRC, nif_name))
    print(nif_name)
    for i in n.of_type('BSShaderTextureSet'):
        for name in ('susanoo.dds', 'susanoo_n.dds', 'susanoo_g.dds', 'susanoo_b.dds', 'susanoomembraneshader.dds'):
            n.swap_string(i, OLD_TEX + name.encode(), NEW_TEX + name.encode())
    for i in n.of_type('BSLightingShaderProperty'):
        tint_at(n.blocks[i], lighting_emissive_offset(n.blocks[i]), 'lit %d emissive' % i)
    for i in n.of_type('BSEffectShaderProperty'):
        for old, new in PALETTES.items():
            if n.swap_string(i, old, new):
                print('  fx %d palette %s' % (i, new.decode().rsplit('\\', 1)[1]))
        p = effect_emissive_offset(n.blocks[i])
        tint_at(n.blocks[i], p, 'fx %d emissive' % i)
        struct.pack_into('<f', n.blocks[i], p + 16, struct.unpack_from('<f', n.blocks[i], p + 16)[0] * FX_MULT)
    for i in n.of_type('NiPosData'):                       # the emissive colour pulse
        for p in pos_data_keys(n.blocks[i]):
            tint_at(n.blocks[i], p, 'colour key %d' % i)
    for i in n.of_type('NiPoint3Interpolator'):            # its resting value
        b = n.blocks[i]
        if all(abs(v) < 1e30 for v in struct.unpack_from('<3f', b, 0)):    # -FLT_MAX = no resting value
            tint_at(b, 0, 'colour default %d' % i)
    for i in n.of_type('BSPSysSimpleColorModifier'):       # ends with three RGBA colours
        b = n.blocks[i]
        for k in range(3):
            tint_at(b, len(b) - 48 + 16 * k, 'particle colour %d.%d' % (i, k))
    out = os.path.join(ROOT, 'meshes', 'SNJ', 'susanoo', out_name)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    n.write(out)
    print('  wrote', out)


for t in ('susanoo.dds', 'susanoomembraneshader.dds'):
    recolour(t)
for t in ('susanoo_n.dds', 'susanoo_g.dds'):                # shape and (black) glow: unchanged copies
    open(os.path.join(ROOT, 'textures', 'SNJ', 'susanoo', t), 'wb').write(open(os.path.join(SRC, t), 'rb').read())
fix('susanoo.nif', 'ribcage.nif')
fix('susanooparticles.nif', 'ribcageparticles.nif')
fix('aaasasukearrowprojectile.nif', 'arrow.nif', brightness=1.0)    # the spectral bow's arrow (mastery 65): bright, so the shot reads
