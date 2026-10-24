"""Copy an SSE .nif, replacing a substring in its texture paths (BSShaderTextureSet blocks only).

Usage: nif_retexture.py <in.nif> <out.nif> <old substring> <new substring>
Case-insensitive match; every other byte is copied unchanged (only the touched blocks and their
header block-size entries change).
"""
import re, struct, sys

src, dst, old, new = sys.argv[1:5]
pat = re.compile(re.escape(old.encode('latin1')), re.I)
b = open(src, 'rb').read()
o = b.index(b'\n') + 1
ver, endian, user_ver, nblocks = struct.unpack_from('<IBII', b, o); o += 13
o += 4
for _ in range(3): o += 1 + b[o]
ntypes = struct.unpack_from('<H', b, o)[0]; o += 2; types = []
for _ in range(ntypes):
    n = struct.unpack_from('<I', b, o)[0]; types.append(b[o+4:o+4+n].decode('latin1')); o += 4 + n
btype = struct.unpack_from('<%dH' % nblocks, b, o); o += 2 * nblocks
size_off = o
bsize = list(struct.unpack_from('<%dI' % nblocks, b, o)); o += 4 * nblocks
nstr = struct.unpack_from('<I', b, o)[0]; o += 8
for _ in range(nstr): o += 4 + struct.unpack_from('<I', b, o)[0]
o += 4 + 4 * struct.unpack_from('<I', b, o)[0]
blocks_start = o
blocks, p = [], o
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
    repl = new.encode('latin1')
    new_tex = [pat.sub(lambda m: repl, t) for t in tex]           # literal replacement (paths contain backslashes)
    if new_tex != tex:
        changed += sum(a != c for a, c in zip(tex, new_tex))
        blocks[i] = struct.pack('<I', n) + b''.join(struct.pack('<I', len(t)) + t for t in new_tex) + blk[q:]
        bsize[i] = len(blocks[i])
out = b[:size_off] + struct.pack('<%dI' % nblocks, *bsize) + b[size_off + 4 * nblocks:blocks_start] + b''.join(blocks) + footer
open(dst, 'wb').write(out)
print(f'{src} -> {dst}: {changed} texture path(s) changed')
