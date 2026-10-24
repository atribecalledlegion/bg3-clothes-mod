"""Ronin Purple FX, repoint pass: Vergil meshes that use a purple copy saved under textures\\RoninPurple\\ (textures
from the game's shared textures\\effects\\ folder) are pointed at the copy. Works on the mesh pass's output where it
exists, else copies the original NIF into the output first. Mods in lowest -> highest priority order.
usage: repoint_meshes.py <nif_util dir> <repoint json> <out mod dir> <mod dir>..."""
import json, os, struct, sys
sys.path.insert(0, sys.argv[1])
from nif_util import Nif

repoint = json.load(open(sys.argv[2]))
OUT = sys.argv[3]


def norm(p):
    p = p.replace('/', '\\').lower()
    i = p.find('textures\\')
    return p[i:] if i >= 0 else p


def strings(b):
    """Every sized string in the block that looks like a .dds path: (exact bytes)."""
    found = set()
    i = 0
    while True:
        j = b.lower().find(b'.dds', i)
        if j < 0:
            return found
        for start in range(j - 4, max(-1, j - 300), -1):
            n = struct.unpack_from('<I', b, start)[0]
            if n == j + 4 - (start + 4):
                found.add(bytes(b[start + 4:j + 4]))
                break
        i = j + 4


count = 0
for root in sys.argv[4:]:
    for dp, dn, fn in os.walk(root):
        for f in fn:
            if not f.lower().endswith('.nif'):
                continue
            rel = os.path.relpath(os.path.join(dp, f), root)
            dst = os.path.join(OUT, rel)
            nif = Nif(dst if os.path.exists(dst) else os.path.join(dp, f))
            hits = 0
            for i in nif.of_type('BSEffectShaderProperty'):
                for s in strings(nif.blocks[i]):
                    new = repoint.get(norm(s.decode('latin1')))
                    if new:
                        hits += nif.swap_string(i, s, new.encode('latin1'))
            if hits:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                nif.write(dst)
                count += 1
                print('  %s: %d' % (rel, hits))
print('repointed %d nifs' % count)
