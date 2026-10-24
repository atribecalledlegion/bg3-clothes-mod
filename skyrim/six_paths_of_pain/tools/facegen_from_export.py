"""Turn a RaceMenu "Export Head" .nif/.dds pair into an NPC's FaceGen files.

Usage: facegen_from_export.py <export.nif> <export.dds> <plugin name> <object id hex> <mod folder>

Writes
  <mod>/meshes/actors/character/FaceGenData/FaceGeom/<plugin>/<00000xxx>.nif
  <mod>/textures/actors/character/FaceGenData/FaceTint/<plugin>/<00000xxx>.dds
and fixes two things RaceMenu's export gets wrong for an NPC:
  * the head's tint-texture slot points at the export file (Data\\SKSE\\Plugins\\CharGen\\...) ->
    rewritten to the FaceTint path;
  * SMP physics-hair bones carry FSMP's runtime prefix ("hdtSSEPhysics_AutoRename_Head_00000004 Traveler B 1")
    -> renamed back to the hair's own bone names ("Traveler B 1"), which is what FSMP looks for on NPC
    FaceGen. With the prefix the bones are never simulated and the hair skins to bones at the origin.
Everything else is copied byte for byte.
"""
import os, shutil, struct, sys

src_nif, src_dds, plugin, obj_hex, mod = sys.argv[1:6]
name = '%08X' % int(obj_hex, 16)
tint_path = 'Actors\\Character\\FaceGenData\\FaceTint\\%s\\%s.dds' % (plugin, name)

b = open(src_nif, 'rb').read()
o = b.index(b'\n') + 1
ver, endian, user_ver, nblocks = struct.unpack_from('<IBII', b, o); o += 13
assert ver == 0x14020007 and user_ver == 12
o += 4                                                    # bsver
for _ in range(3): o += 1 + b[o]                          # author / process / export strings
ntypes = struct.unpack_from('<H', b, o)[0]; o += 2
types = []
for _ in range(ntypes):
    n = struct.unpack_from('<I', b, o)[0]; types.append(b[o+4:o+4+n].decode('latin1')); o += 4 + n
btype = struct.unpack_from('<%dH' % nblocks, b, o); o += 2 * nblocks
size_off = o
bsize = list(struct.unpack_from('<%dI' % nblocks, b, o)); o += 4 * nblocks
strings_off = o
nstr = struct.unpack_from('<I', b, o)[0]; o += 8
strings = []
for _ in range(nstr):
    n = struct.unpack_from('<I', b, o)[0]; strings.append(b[o+4:o+4+n]); o += 4 + n
strings_end = o
o += 4 + 4 * struct.unpack_from('<I', b, o)[0]           # groups
blocks_start = o

SMP_PREFIX = b'hdtSSEPhysics_AutoRename_'
renamed = 0
for k, st in enumerate(strings):
    if st.startswith(SMP_PREFIX) and b' ' in st:
        strings[k] = st.split(b' ', 1)[1]                 # "..._Head_00000004 Traveler B 1" -> "Traveler B 1"
        print(f'bone string {k}: {st.decode("latin1")} -> {strings[k].decode("latin1")}')
        renamed += 1
string_table = (struct.pack('<II', nstr, max(len(st) for st in strings)) +
                b''.join(struct.pack('<I', len(st)) + st for st in strings))

blocks, p = [], blocks_start
for i in range(nblocks):
    blocks.append(b[p:p+bsize[i]]); p += bsize[i]
footer = b[p:]

changed = 0
for i in range(nblocks):
    if types[btype[i] & 0x7FFF] != 'BSShaderTextureSet':
        continue
    blk = blocks[i]; n = struct.unpack_from('<I', blk, 0)[0]; q = 4; tex = []
    for _ in range(n):
        ln = struct.unpack_from('<I', blk, q)[0]; tex.append(blk[q+4:q+4+ln]); q += 4 + ln
    hit = [k for k, t in enumerate(tex) if b'SKSE\\Plugins\\CharGen' in t]
    if not hit:
        continue
    for k in hit:
        print(f'block {i} slot {k}: {tex[k].decode("latin1")} -> {tint_path}')
        tex[k] = tint_path.encode('latin1')
    blocks[i] = struct.pack('<I', n) + b''.join(struct.pack('<I', len(t)) + t for t in tex)
    bsize[i] = len(blocks[i]); changed += len(hit)
assert changed == 1, f'expected exactly one export tint path, found {changed}'

out = (bytearray(b[:size_off]) + struct.pack('<%dI' % nblocks, *bsize) + b[size_off + 4 * nblocks:strings_off] +
       string_table + b[strings_end:blocks_start])
out += b''.join(blocks) + footer
print(f'{renamed} SMP bone name(s) restored')

geom = os.path.join(mod, 'meshes', 'actors', 'character', 'FaceGenData', 'FaceGeom', plugin)
tint = os.path.join(mod, 'textures', 'actors', 'character', 'FaceGenData', 'FaceTint', plugin)
os.makedirs(geom, exist_ok=True); os.makedirs(tint, exist_ok=True)
open(os.path.join(geom, name + '.nif'), 'wb').write(out)
shutil.copyfile(src_dds, os.path.join(tint, name + '.dds'))
print('wrote', os.path.join(geom, name + '.nif'), len(out), 'bytes (was', len(b), ')')
print('wrote', os.path.join(tint, name + '.dds'))
