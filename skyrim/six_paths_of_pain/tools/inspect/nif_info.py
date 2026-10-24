"""Minimal SSE NIF (20.2.0.7, bsver 100) inspector: header, block list, names, texture paths, extra data.
Usage: nif_info.py file.nif"""
import struct, sys

b = open(sys.argv[1], 'rb').read()
nl = b.index(b'\n')
print('header line:', b[:nl].decode('latin1'))
o = nl + 1
ver, endian, user_ver, nblocks = struct.unpack_from('<IBII', b, o); o += 13
bsver = struct.unpack_from('<I', b, o)[0]; o += 4
def sstr8():
    global o
    n = b[o]; s = b[o+1:o+1+n].rstrip(b'\0').decode('latin1'); o += 1 + n; return s
author, proc, export = sstr8(), sstr8(), sstr8()
ntypes = struct.unpack_from('<H', b, o)[0]; o += 2
types = []
for _ in range(ntypes):
    n = struct.unpack_from('<I', b, o)[0]; types.append(b[o+4:o+4+n].decode('latin1')); o += 4 + n
btype = struct.unpack_from('<%dH' % nblocks, b, o); o += 2 * nblocks
bsize = struct.unpack_from('<%dI' % nblocks, b, o); o += 4 * nblocks
nstr, maxlen = struct.unpack_from('<II', b, o); o += 8
strings = []
for _ in range(nstr):
    n = struct.unpack_from('<I', b, o)[0]; strings.append(b[o+4:o+4+n].decode('latin1')); o += 4 + n
ngroups = struct.unpack_from('<I', b, o)[0]; o += 4 + 4 * ngroups
print(f'version {ver:#x} user {user_ver} bsver {bsver} blocks {nblocks} strings {nstr} author={author!r} export={export!r}')
starts = []
for i in range(nblocks):
    starts.append(o); o += bsize[i]
print('end of blocks at', o, 'file size', len(b))

def s(idx): return strings[idx] if 0 <= idx < len(strings) else None
for i in range(nblocks):
    t = types[btype[i] & 0x7FFF]; p = starts[i]; info = ''
    if t in ('NiNode', 'BSFadeNode', 'BSTriShape', 'BSDynamicTriShape', 'BSSubIndexTriShape', 'NiTriShape',
             'BSLightingShaderProperty', 'BSEffectShaderProperty', 'NiStringExtraData', 'NiIntegerExtraData',
             'BSXFlags', 'NiSkinInstance', 'BSDismemberSkinInstance', 'NiAlphaProperty'):
        name = struct.unpack_from('<i', b, p)[0]
        info = f'name={s(name)!r}'
        if t == 'NiStringExtraData':
            info += f' value={s(struct.unpack_from("<i", b, p + 4)[0])!r}'
        if t in ('BSTriShape', 'BSDynamicTriShape', 'NiNode', 'BSFadeNode'):
            nextra = struct.unpack_from('<I', b, p + 4)[0]
            extras = struct.unpack_from('<%di' % nextra, b, p + 8)
            info += f' extra={list(extras)}'
            q = p + 8 + 4 * nextra + 4                     # controller
            q += 4 + 12 + 36 + 4 + 4                       # flags(u32) trans rot scale collision
            if t == 'NiNode' or t == 'BSFadeNode':
                nch = struct.unpack_from('<I', b, q)[0]
                info += f' children={list(struct.unpack_from("<%di" % nch, b, q + 4))}'
            else:
                q += 16                                     # bounding sphere
                skin, shader, alpha = struct.unpack_from('<iii', b, q)
                info += f' skin={skin} shader={shader} alpha={alpha}'
    if t == 'BSShaderTextureSet':
        n = struct.unpack_from('<I', b, p)[0]; q = p + 4; tex = []
        for _ in range(n):
            ln = struct.unpack_from('<I', b, q)[0]; tex.append(b[q+4:q+4+ln].decode('latin1')); q += 4 + ln
        info = 'textures=' + repr([x for x in tex if x])
    print(f'{i:3} {t:28} {bsize[i]:8} {info}')
