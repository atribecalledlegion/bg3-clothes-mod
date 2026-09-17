"""Flat stand-ins for the garment's normal and physical maps, which live in the virtual
texture and have not been extracted.

    python tools/make_neutral_maps.py <item>

All four shader inputs must be bound: with the normalmap unbound the whole garment
rendered pure black. Flat maps shade correctly, just without fabric detail.

  nm  #8080FF  flat tangent-space normal. DXT5, as vanilla normal maps are.
  pm  #06D4E6  measured from HUM_M_ARM_Padded_Body_A_PM -- the padded garment worn under
               Gale's robe -- averaged to one colour: metallic ~0, roughness high, AO high.
               DXT1, as vanilla physical maps are.
"""
import os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import item as itemlib


def main():
    it = itemlib.load()
    cols = it.get('neutral_maps', {})
    os.makedirs(it.textures, exist_ok=True)
    for key, default, fmt in (('nm', '#8080FF', 'dxt5'), ('pm', '#06D4E6', 'dxt1')):
        out = os.path.join(it.textures, '%s_%s.DDS' % (it.folder, key.upper()))
        subprocess.run([itemlib.MAGICK, '-size', '2048x2048', 'xc:' + cols.get(key, default),
                        '-define', 'dds:compression=' + fmt, '-define', 'dds:mipmaps=12', out],
                       check=True)
        print('wrote', out)


if __name__ == '__main__':
    main()
