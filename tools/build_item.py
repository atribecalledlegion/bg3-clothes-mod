"""Generate everything for one item, in order.

    python tools/build_item.py <item>            resources only (banks, template, text files)
    python tools/build_item.py <item> --art      also textures, neutral maps and icon

Then pack with:   .\\build.ps1 -Item <item> [-Install]

Textures are a separate switch because they are slow, and because an item's committed
DDS files are the verified-in-game result -- regenerating resources must not silently
replace them.

Art step, from item.json:
  "art":  [command...]   the item's own script (Obito: its crest compositor)
  "bake": {...}          or tools/bake_decals.py, placing decals on the mesh in 3D
"""
import os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import item as itemlib

RESOURCES = ['make_content_bank', 'make_visual_bank', 'make_visuals_node', 'make_preset',
             'merge_banks', 'make_roottemplate', 'make_mod_files']


def run(cmd):
    print('\n>> ' + ' '.join(cmd))
    subprocess.run(cmd, check=True)


def main():
    it = itemlib.load()
    py = sys.executable
    if '--art' in sys.argv:
        if it.get('art'):
            run(it['art'])
        elif it.get('bake'):
            run([py, 'tools/bake_decals.py', it.id])
        else:
            raise SystemExit('%s has neither "art" nor "bake"' % it.id)
        run([py, 'tools/make_neutral_maps.py', it.id])
        run([py, 'tools/make_icon.py', it.id])
    for step in RESOURCES:
        run([py, 'tools/%s.py' % step, it.id])
    print('\ndone: %s.  Pack with  .\\build.ps1 -Item %s -Install' % (it.id, it.id))


if __name__ == '__main__':
    main()
