"""Ronin Purple FX, shared-palette pass: blue palettes the Vergil effects use but do not ship (base-game paths, with
whatever mod the game currently takes them from), copied purple into textures\\RoninPurple\\ and added to
repoint.json so repoint_meshes.py points only the Vergil meshes at the copies (vanilla spells keep their colours).

PALETTES maps the game path to the file the game actually loads (the highest-priority loose copy; check MO2).
2026-10-19: gradreanimate.dds = the drawn Yamato's blade glow (YamatoFxARTO.nif), loaded from VAE2.

usage (from the MO2 mods folder): recolour_shared_palettes.py <out mod dir> <repoint json>
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from purple_core import shift, dds_info, write_dds

OUT, REPOINT = sys.argv[1], sys.argv[2]
PALETTES = {
    'textures\\effects\\gradients\\gradreanimate.dds':
        'Visual Animated Enchants 2-023 AKA VAE2/textures/effects/gradients/gradreanimate.dds',
}
repoint = json.load(open(REPOINT)) if os.path.exists(REPOINT) else {}
for game_path, src in PALETTES.items():
    w, h, mips, fourcc = dds_info(src)
    fmt = 'DXT1' if fourcc == b'DXT1' else ('RGBA' if fourcc == b'\0\0\0\0' else 'DXT5')
    out_rel = 'textures\\RoninPurple\\' + game_path.split('\\')[-1]
    write_dds(Image.fromarray(shift(np.array(Image.open(src).convert('RGBA'))), 'RGBA'), mips, fmt,
              os.path.join(OUT, *out_rel.split('\\')))
    repoint[game_path] = out_rel
    print('  %s (%dx%d, %d mips, %s) -> %s' % (game_path, w, h, mips, fmt, out_rel))
json.dump(repoint, open(REPOINT, 'w'), indent=1)
print('repoint.json now has %d entries' % len(repoint))
