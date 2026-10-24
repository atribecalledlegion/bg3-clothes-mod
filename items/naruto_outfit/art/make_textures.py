"""Textures for the imported Naruto meshes.

    python items/naruto_outfit/art/make_textures.py naruto_outfit

Source: extracted/naruto-rigged/ ("Naruto Rigged" by SniperAmbush, extracted from Ultimate
Ninja Storm 4, CC-BY-4.0 -- credit required if this mod is shared). Replaces the original
naruto-r download: that model's atlas was a fragmented, unpadded mosaic of tiny UV islands
that bled into "checkered" garbage under BG3's real lighting no matter what we did on the
mesh/normals side (confirmed by shipping a flat single-colour texture and seeing the same
pattern). This source's texture is a small set of large, flat, deliberately-laid-out colour
regions -- the kind a real shipped game needs for its own texture budget -- so there is
nothing fragmented for filtering to bleed across.

The mask is one flat slot, as for the cloak: the shader tints by mask slot, and a single
slot with the item's all-white preset leaves the atlas rendering exactly as it looks.
"""
import os, subprocess, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
import item as itemlib

ATLAS = 'extracted/naruto-rigged/textures/Naruto_Uzumaki_NarutoPart2_baseColor.png'
MASK_SLOT = '#0000FF'


def main():
    it = itemlib.load()
    if not os.path.exists(ATLAS):
        raise SystemExit('%s missing' % ATLAS)
    os.makedirs(it.textures, exist_ok=True)
    for tag, s, _ in it.sets():
        bm = os.path.join(it.textures, s['bm'])
        subprocess.run([itemlib.MAGICK, ATLAS, '-resize', '2048x2048', '-alpha', 'off',
                        '-define', 'dds:compression=dxt1', '-define', 'dds:mipmaps=1', bm], check=True)
        msk = os.path.join(it.textures, s['msk'])
        subprocess.run([itemlib.MAGICK, '-size', '2048x2048', 'xc:' + MASK_SLOT, '-alpha', 'off',
                        '-define', 'dds:compression=dxt1', '-define', 'dds:mipmaps=1', msk], check=True)
        print('%-8s wrote %s, %s' % (tag, s['bm'], s['msk']))


if __name__ == '__main__':
    main()
