"""Hang the two-handed katanas at the left hip, where Sam draws from (2026-10-20).

Katana Crafting's one-handed katanas and Dai-Katanas are built the same way (same node layout, same axes); the only
difference is the sheathed parent node in the root's "Prn" string: WeaponSword (left hip) vs WeaponBack. This rewrites
that string table entry WeaponBack -> WeaponSword in every two-handed katana nif under <mod>/meshes (run it after
restore_katana_meshes.py). Blocks reference strings by index, so only the header's string table changes.

usage: make_hip_katanas.py <mod folder>
"""
import os, struct, sys

MOD = sys.argv[1]


def to_hip(path):
    d = open(path, 'rb').read()
    o = d.index(b'\n') + 1
    _v, _e, _u, nb, _bs = struct.unpack_from('<IBIII', d, o); o += 17
    for _ in range(3): o += 1 + d[o]
    nt = struct.unpack_from('<H', d, o)[0]; o += 2
    for _ in range(nt): o += 4 + struct.unpack_from('<I', d, o)[0]
    o += 2 * nb + 4 * nb
    ns_at = o
    ns, maxlen = struct.unpack_from('<II', d, o); o += 8
    out = bytearray(d[:o]); hit = False
    for _ in range(ns):
        n = struct.unpack_from('<I', d, o)[0]; s = d[o+4:o+4+n]; o += 4 + n
        if s == b'WeaponBack':
            s = b'WeaponSword'; hit = True
        out += struct.pack('<I', len(s)) + s
    if not hit:
        return False
    struct.pack_into('<I', out, ns_at + 4, max(maxlen, len(b'WeaponSword')))
    open(path, 'wb').write(bytes(out) + d[o:])
    return True


n = 0
for root, _d, files in os.walk(os.path.join(MOD, 'meshes')):
    for f in files:
        if f.lower().endswith('.nif') and 'daikatana' in f.lower():
            if to_hip(os.path.join(root, f)):
                n += 1
print(n, 'two-handed katanas moved to the hip (Prn WeaponBack -> WeaponSword)')
