"""Ronin Purple FX, weapon pass: the Yamato restyled as Ronin Obito's katana.

The blade, hilt, guard and scabbard share one colour atlas (textures\\weapons\\Devil Sword Vergil\\Albedo.dds,
2048x4096); the rune glow is a white mask whose colour is the glow shader's emissive colour (0.02, 0.37, 0.96) in the
weapon meshes (Chaos2: the ones the Yamato weapon and scabbard records use). Using the part masks from
yamato_uv_map.py (sword triangles by position along the sword, scabbard triangles by position from its mouth):
- scabbard (saya): black lacquer, with two red cord bands near the mouth (the sageo)
- hilt wrap (sword 0.10-0.20 along, from the pommel): white, its dark diamond pattern kept (white ito over black)
- pommel ornaments (< 0.10) and guard (0.20-0.30): dark steel
- blade (> 0.30): Kamui purple with purple_core's rule, as before
Each recoloured part keeps its own shading (pixel brightness relative to the part's average). The glow shaders'
emissive goes purple. Meshes come from the out folder where the mesh pass already wrote them, else from the Yamato.

usage (from the MO2 mods folder): recolour_weapon.py <nif_util dir> <out mod dir> <yamato_uv_map out prefix>
"""
import os, struct, sys
sys.path.insert(0, sys.argv[1])
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from nif_util import Nif, lighting_emissive_offset
from purple_core import purple, shift, dds_info, write_dds

OUT, MAPS = sys.argv[2], sys.argv[3]
YAMATO = 'Vergil Yamato 5.7 (bundle)'
ATLAS = os.path.join('textures', 'weapons', 'Devil Sword Vergil', 'Albedo.dds')
MESHES = [os.path.join('meshes', 'Chaos2', f) for f in ('Yamato.nif', 'YamatoscbHDTM.nif', 'YamatoscbHDTF.nif')]
GLOW_SHADER = 2
LACQUER = np.array([26, 22, 30], float)     # near-black, a breath of purple
WRAP = np.array([226, 222, 212], float)     # off-white silk
STEEL = np.array([58, 56, 62], float)       # dark steel
CORD = np.array([170, 24, 30], float)       # the red sageo
CORD_BANDS = [(0.07, 0.095), (0.115, 0.14)]  # along the scabbard from the mouth
SWORD_PARTS = {'pommel': (0.0, 0.10, STEEL), 'wrap': (0.10, 0.20, WRAP), 'guard': (0.20, 0.30, STEEL)}


def tone(rgb, mask, colour, contrast=1.0):
    """The part's pixels -> colour, scaled by each pixel's brightness relative to the part's average."""
    lum = rgb.mean(-1)
    ref = max(lum[mask].mean(), 1.0)
    k = ((lum / ref) ** contrast)[..., None]
    return np.where(mask[..., None], np.clip(colour * k, 0, 255), rgb)


src = os.path.join(YAMATO, ATLAS)
w, h, mips, fourcc = dds_info(src)
img = np.array(Image.open(src).convert('RGBA'))
axis = np.load(MAPS + '_axis.npy')                 # sword: position from the pommel, -1 = not the sword
saya = np.load(MAPS + '_saya.npy') > 0
saya_axis = np.load(MAPS + '_saya_axis.npy')       # scabbard: position from the mouth
assert axis.shape == img.shape[:2], (axis.shape, img.shape)

rgb = shift(img)[..., :3].astype(float)            # blade and everything else: purple as before
orig = img[..., :3].astype(float)
for name, (lo, hi, colour) in SWORD_PARTS.items():
    m = (axis >= lo) & (axis < hi)
    rgb = np.where(m[..., None], tone(orig, m, colour, 1.2 if name == 'wrap' else 1.0), rgb)
    print('  %-6s %5.1f%% of the atlas' % (name, 100 * m.mean()))
sheath = saya & (axis < 0)
rgb = np.where(sheath[..., None], tone(orig, sheath, LACQUER), rgb)
cord = sheath & np.any([(saya_axis >= a) & (saya_axis < b) for a, b in CORD_BANDS], axis=0)
rgb = np.where(cord[..., None], tone(orig, cord, CORD), rgb)
print('  saya   %5.1f%% (cord %.2f%%)' % (100 * sheath.mean(), 100 * cord.mean()))
out = Image.fromarray(np.dstack([rgb, img[..., 3]]).astype(np.uint8), 'RGBA')
write_dds(out, mips, 'DXT5', os.path.join(OUT, ATLAS))
out.convert('RGB').resize((w // 4, h // 4)).save(os.path.join(os.path.dirname(OUT.rstrip('/\\')), 'yamato_atlas_preview.png'))
print('atlas %dx%d, %d mips -> Ronin katana' % (w, h, mips))

for rel in MESHES:
    dst = os.path.join(OUT, rel)
    nif = Nif(dst if os.path.exists(dst) else os.path.join(YAMATO, rel))
    for i in nif.of_type('BSLightingShaderProperty'):
        b = nif.blocks[i]
        if struct.unpack_from('<I', b, 0)[0] != GLOW_SHADER:
            continue
        p = lighting_emissive_offset(b)
        old = struct.unpack_from('<3f', b, p)
        new, moved = purple(old)
        if moved:
            struct.pack_into('<3f', b, p, *new)
            print('  %s glow %d: %s -> %s' % (rel, i, tuple(round(v, 2) for v in old), tuple(round(v, 2) for v in new)))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    nif.write(dst)
