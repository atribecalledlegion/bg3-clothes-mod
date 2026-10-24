"""Copies of the Blades Samurai kimono meshes (male, both weights, 1st person, ground) pointed at Ronin
Obito's purple kimono texture (textures\\ROM\\ronin_kimono.dds) instead of kimono_blue.dds, so the ROM_Kimono
ARMA needs no alternate-texture record from SamuraiBlades.esp. The normal map stays the Blades one.

usage: make_kimono_meshes.py <nif_util dir> <Blades meshes\\clothes\\kimono dir> <out dir>
"""
import os, re, sys
sys.path.insert(0, sys.argv[1])
from nif_util import Nif

SRC, OUT = sys.argv[2], sys.argv[3]
NEW = b'textures\\ROM\\ronin_kimono.dds'
OLD = re.compile(rb'(?i)[ -~]*clothes\\kimono\\kimono_blue\.dds')
FILES = ['kimono_0.nif', 'kimono_1.nif', '1stpersonkimono_0.nif', '1stpersonkimono_1.nif', 'kimono_gnd.nif']
# female meshes use another texture layout (kimono_last.dds): the ARMA's female slot keeps the Blades mesh
os.makedirs(OUT, exist_ok=True)
for f in FILES:
    n = Nif(os.path.join(SRC, f))
    hits = 0
    for i in n.of_type('BSShaderTextureSet'):
        for m in set(OLD.findall(bytes(n.blocks[i]))):
            hits += n.swap_string(i, m, NEW)
    assert hits, f
    n.write(os.path.join(OUT, f))
    print('%-26s retextured %d' % (f, hits))
