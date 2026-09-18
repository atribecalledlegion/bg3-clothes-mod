"""Textures for the imported Naruto meshes.

    python items/naruto_outfit/art/make_textures.py naruto_outfit

The model ships one 2048 colour atlas covering the whole character, and the imported
meshes keep their original UVs, so the atlas IS the base colour map -- no painting needed.
The atlas is used AS-IS. It looked for a while as though the game sampled v the other way
round, because an early build shipped a mesh whose UVs were flipped (the OBJ cut wrote v
in the wrong convention) -- flipping the texture as well only swapped one wrong result for
another. With the mesh right, the atlas is right: rendering the packed GR2 against the
packed DDS reproduces exactly what the game draws, and is the way to check this offline.

The mask is one flat slot, as for the cloak: the shader tints by mask slot, and a single
slot with the item's all-white preset leaves the atlas rendering exactly as it looks.
"""
import os, subprocess, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
import item as itemlib

ATLAS = 'extracted/naruto-r/gltf_embedded_0.jpeg'
MASK_SLOT = '#0000FF'


def main():
    it = itemlib.load()
    if not os.path.exists(ATLAS):
        raise SystemExit('%s missing: extract naruto-r.zip into extracted/naruto-r/' % ATLAS)
    os.makedirs(it.textures, exist_ok=True)
    for tag, s, _ in it.sets():
        bm = os.path.join(it.textures, s['bm'])
        subprocess.run([itemlib.MAGICK, ATLAS, '-alpha', 'off',
                        '-define', 'dds:compression=dxt1', '-define', 'dds:mipmaps=12', bm], check=True)
        msk = os.path.join(it.textures, s['msk'])
        subprocess.run([itemlib.MAGICK, '-size', '2048x2048', 'xc:' + MASK_SLOT, '-alpha', 'off',
                        '-define', 'dds:compression=dxt1', '-define', 'dds:mipmaps=12', msk], check=True)
        print('%-8s wrote %s, %s' % (tag, s['bm'], s['msk']))


if __name__ == '__main__':
    main()
