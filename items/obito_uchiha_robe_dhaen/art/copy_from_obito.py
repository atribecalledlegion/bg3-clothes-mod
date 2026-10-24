"""Give this mod the Obito robe's artwork.

    python items/obito_uchiha_robe_dhaen/art/copy_from_obito.py obito_uchiha_robe_dhaen
    python tools/make_neutral_maps.py obito_uchiha_robe_dhaen
    python tools/build_item.py obito_uchiha_robe_dhaen        (no --art: see below)

The robe is the same garment with the same UV layout (the Dhaen mesh lies inside the vanilla
robe's UV islands), so the Obito robe's finished textures and inventory icon are reused as
they are instead of being baked a second time. Only the neutral normal/physical maps are
regenerated, because their file names carry this mod's folder.

Build without --art: the garment art step would also run tools/make_icon.py, which needs
the vanilla robe meshes extracted, and the icon here is copied rather than rendered.
"""
import os, shutil, subprocess, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
import item as itemlib

SOURCE = 'obito_uchiha_robe'


def main():
    it = itemlib.load()
    src = itemlib.Item(SOURCE)
    os.makedirs(it.textures, exist_ok=True)
    for s in it.garment['sets'].values():
        for name in (s['bm'], s['msk']):
            shutil.copyfile(os.path.join(src.textures, name), os.path.join(it.textures, name))
            print('texture', name)
    # flat-colour textures for the extra materials (the pants worn under the robe)
    for s in it.get('mod_materials', []):
        dim = '%dx%d' % (s.get('size', 2048), s.get('size', 2048))
        for name, colour, mips in ((s['bm'], s['colour'], '12'), (s['msk'], '#0000FF', '1')):
            subprocess.run([itemlib.MAGICK, '-size', dim, 'xc:' + colour, '-alpha', 'off',
                            '-define', 'dds:compression=dxt1', '-define', 'dds:mipmaps=' + mips,
                            os.path.join(it.textures, name)], check=True)
            print('flat   ', name, colour)
    for sub in ('Tooltips/Icons', 'ControllerUIIcons/skills_png'):
        a = '%s/Public/Game/GUI/Assets/%s/%s.DDS' % (src.src, sub, src.icon)
        b = '%s/Public/Game/GUI/Assets/%s/%s.DDS' % (it.src, sub, it.icon)
        os.makedirs(os.path.dirname(b), exist_ok=True)
        shutil.copyfile(a, b)
        print('icon   ', os.path.basename(b))


if __name__ == '__main__':
    main()
