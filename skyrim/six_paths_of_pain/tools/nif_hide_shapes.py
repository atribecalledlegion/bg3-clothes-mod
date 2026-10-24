"""Hide shapes of an SSE .nif by name (sets the NiAVObject 'hidden' flag; geometry stays in the file).

Usage: nif_hide_shapes.py <in.nif> <out.nif> <shape name> [<shape name> ...]
"""
import os, struct, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'inspect'))
import render_nif as R

src, dst, names = sys.argv[1], sys.argv[2], set(sys.argv[3:])
b, blocks, strings, bsver = R.read_nif(src)
b = bytearray(b); hit = set()
for t, p, n in blocks:
    if t not in ('BSTriShape', 'BSDynamicTriShape', 'BSSubIndexTriShape', 'NiTriShape'): continue
    name = struct.unpack_from('<i', b, p)[0]; name = strings[name] if name >= 0 else ''
    if name not in names: continue
    ne = struct.unpack_from('<I', b, p + 4)[0]; q = p + 8 + 4 * ne + 4          # name, extra data, controller
    struct.pack_into('<I', b, q, struct.unpack_from('<I', b, q)[0] | 1); hit.add(name)
assert hit == names, names - hit
open(dst, 'wb').write(b); print(f'{src} -> {dst}: hid {sorted(hit)}')
