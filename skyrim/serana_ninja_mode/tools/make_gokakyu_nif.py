"""Hyoton: Gokakyu mesh: naruto overhaul's fireballjutsu.nif with its fire palettes swapped for frost ones.

The ball's look is four BSEffectShaderProperty blocks: a greyscale shape texture coloured through a gradient palette
(GradFireCloak01 / GradFireExplosion). Swapping the palettes for vanilla frost ones (Ice Form, Ice Storm) and tinting
the emissive colour ice blue (brightness kept) turns the Gokakyu into a ball of freezing mist. Texture paths are inline sized strings in
the shader blocks, so a block grows or shrinks and its entry in the header's block size table is rewritten.

usage: make_gokakyu_nif.py <fireballjutsu.nif> <out.nif>
"""
import struct, sys

SRC, OUT = sys.argv[1], sys.argv[2]
SWAP = {b'textures\\effects\\gradients\\GradFireCloak01.dds': b'textures\\effects\\gradients\\GradFrostIceForm.dds',
        b'textures\\effects\\gradients\\GradFireExplosion.dds': b'textures\\effects\\gradients\\GradIceStorm.dds'}
ICE = (0.75, 0.9, 1.0)

d = open(SRC, 'rb').read()
o = d.index(b'\n') + 1
ver, endian, user, nblocks, bsver = struct.unpack_from('<IBIII', d, o); o += 17
assert ver == 0x14020007 and bsver == 100, (hex(ver), bsver)
for _ in range(3):                      # author, process script, export script
    o += 1 + d[o]
ntypes = struct.unpack_from('<H', d, o)[0]; o += 2
types = []
for _ in range(ntypes):
    n = struct.unpack_from('<I', d, o)[0]; types.append(d[o+4:o+4+n]); o += 4 + n
type_idx = struct.unpack_from('<%dH' % nblocks, d, o); o += 2 * nblocks
sizes_at = o
sizes = list(struct.unpack_from('<%dI' % nblocks, d, o)); o += 4 * nblocks
nstr = struct.unpack_from('<I', d, o)[0]; o += 8
strings = []
for _ in range(nstr):
    n = struct.unpack_from('<I', d, o)[0]; strings.append(d[o+4:o+4+n]); o += 4 + n
ngroups = struct.unpack_from('<I', d, o)[0]; o += 4 + 4 * ngroups
head, blocks = bytearray(d[:o]), []
for s in sizes:
    blocks.append(bytearray(d[o:o+s])); o += s
tail = d[o:]

swapped = tinted = 0
for i, b in enumerate(blocks):
    if types[type_idx[i] & 0x7FFF] != b'BSEffectShaderProperty':
        continue
    for old, new in SWAP.items():
        key = struct.pack('<I', len(old)) + old
        if key in b:
            b[:] = b.replace(key, struct.pack('<I', len(new)) + new); swapped += 1
    # NiObjectNET: name, extra data list, controller; then flags, uv offset/scale, source texture (sized string),
    # 4 bytes, falloff angles/opacities (4 f), emissive colour (4 f)
    p = 4
    p += 4 + 4 * struct.unpack_from('<I', b, p)[0]
    p += 4 + 8 + 16
    p += 4 + struct.unpack_from('<I', b, p)[0]
    p += 4 + 16
    old_col = struct.unpack_from('<4f', b, p)
    new_col = tuple(old_col[0] * c for c in ICE)    # keep each layer's brightness, tint it ice blue
    struct.pack_into('<3f', b, p, *new_col); tinted += 1
    print('  shader block %d: emissive %s -> %s' % (i, tuple(round(c, 2) for c in old_col[:3]), tuple(round(c, 2) for c in new_col)))
assert swapped == 4 and tinted == 4, (swapped, tinted)
struct.pack_into('<%dI' % nblocks, head, sizes_at, *[len(b) for b in blocks])
open(OUT, 'wb').write(bytes(head) + b''.join(bytes(b) for b in blocks) + tail)
print('wrote', OUT, '(%d palette swaps)' % swapped)
