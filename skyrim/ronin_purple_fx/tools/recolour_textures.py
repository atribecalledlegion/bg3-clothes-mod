"""Ronin Purple FX, texture pass: the blue textures the Vergil mods ship, turned Kamui purple.

Same hue rule as the mesh pass (blue 150-265 deg -> 282, saturation/brightness kept; whites, greys, reds, golds stay).
Output keeps the source's mip count and alpha; DXT1 stays DXT1, everything else is written DXT5 (Pillow cannot
write BC7), uncompressed stays uncompressed. Each mip level is encoded by Pillow and the chain is assembled here.
Textures under the game's shared textures\\effects\\ folder are written to textures\\RoninPurple\\ instead, so vanilla
spells keep their colours, and the Vergil meshes that use them are repointed (repoint.json, read by the mesh pass).

usage: recolour_textures.py <survey json> <out mod dir> [min blue share, default 0.2]
"""
import json, os, sys
import numpy as np
from PIL import Image

survey = json.load(open(sys.argv[1]))
OUT = sys.argv[2]
MIN = float(sys.argv[3]) if len(sys.argv) > 3 else 0.2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from purple_core import shift, dds_info, write_dds

repoint, done = {}, []
for rel, v in sorted(survey['mod'].items()):
    if v['blue'] < MIN:
        continue
    src = v['path']
    w, h, mips, fourcc = dds_info(src)
    img = Image.open(src).convert('RGBA')
    fmt = 'DXT1' if fourcc == b'DXT1' else ('RGBA' if fourcc == b'\0\0\0\0' else 'DXT5')
    out_rel = rel
    if rel.startswith('textures\\effects\\'):
        out_rel = 'textures\\RoninPurple\\' + rel.split('\\')[-1]
        repoint[rel] = out_rel
    purple = Image.fromarray(shift(np.array(img)), 'RGBA')
    write_dds(purple, mips, fmt, os.path.join(OUT, *out_rel.split('\\')))
    done.append((rel, out_rel, fmt, mips))
json.dump(repoint, open(os.path.join(os.path.dirname(OUT.rstrip('/\\')), 'repoint.json'), 'w'), indent=1)
for rel, out_rel, fmt, mips in done:
    print('  %-5s mips %2d  %s%s' % (fmt, mips, rel, '' if rel == out_rel else '  ->  ' + out_rel))
print('recoloured %d textures, %d repointed' % (len(done), len(repoint)))
