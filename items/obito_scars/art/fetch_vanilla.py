"""Pull a vanilla human-male head out of the game: its four texture maps as DDS and its
mesh as .glb, into extracted/head_hum_m_<x>/ (local only).

  python items/obito_scars/art/fetch_vanilla.py [A|B|...|I|Oscar|CHD_B]   # default A; CHD_B = the child head Dhaen calls "HUM B" 

Needs Divine.exe (LSLib) for the mesh, at the path build.ps1 uses or $DIVINE.
"""
import os, sys, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from lspk import Pak
import item as itemlib
sys.path.insert(0, HERE)
import headmesh as hm

DIVINE = os.environ.get('DIVINE', os.path.join(os.environ.get('USERPROFILE', ''), 'Tools', 'LSLib', 'Tools', 'Divine.exe'))

def main():
    i = hm.info(sys.argv[1] if len(sys.argv) > 1 else 'A')
    out = i['src']
    os.makedirs(out, exist_ok=True)
    tex = Pak(os.path.join(itemlib.DATA, 'Textures.pak'))
    for m in ('NM', 'CLEA', 'HMVY', 'MSK'):
        name = '%s_%s.DDS' % (i['stem'], m)
        path = i['tex_res'] + name
        if path not in tex.entries:                     # not every head ships every map (e.g. Head A has no MSK)
            print('%-32s not in the game files (skipped)' % name)
            continue
        data = tex.read(path)
        open(os.path.join(out, name), 'wb').write(data)
        print('%-32s %d bytes' % (name, len(data)))
    gr2 = os.path.join(out, i['stem'] + '.GR2')
    open(gr2, 'wb').write(Pak(os.path.join(itemlib.DATA, 'Models.pak')).read(i['gr2_path']))
    glb = os.path.join(out, i['stem'] + '.glb')
    subprocess.run([DIVINE, '-g', 'bg3', '-a', 'convert-model', '-s', gr2, '-d', glb, '-l', 'warn'], check=True)
    print('mesh ->', glb)

if __name__ == '__main__':
    main()
