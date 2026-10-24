"""transplant_hair.py <serana_facegen.nif> <valerica_facegen.nif> <out.nif>
Puts Valerica DF Edition's hair (Wendigo: blocks 24-67 = WendigoNoHorn, VWendigo3, VWendigo4, VWendigo4HL, VWendigoHL,
VWendigoSC, VDFHairline with their skin/shader/alpha blocks) onto Serana DF's FaceGen head, replacing Serana's hair
(blocks 24-55 = SDFHair, SDFHairline, SweetteaHL, Sweettea2HL, Sweettea2). Serana's face (blocks 0-23) and her lashes,
eyes, brows and glow lens (blocks 56-81) are kept byte for byte, except for block references that move.
Both files come from the same FaceGen layout (checked): root 0, bone nodes 1-3, face 4-23. Differences handled:
 - the bone nodes are in the opposite order (Valerica 1=Head 2=Spine2, Serana 1=Spine2 2=Head) -> hair bone refs 1<->2
 - Serana's tail blocks move up by 12 -> their internal refs +12
 - shape names come from Valerica's string table -> appended to Serana's, renamed SVL_<name>
2026-10-16: v1 (Valerica's own names) broke her whole head in game: SeranaDFE's hair head part SDFHair and its extras
had no shapes left, so the engine dropped the facegen (only the mouth showed). Serana Vampire Look.esp now gives her
SVL_ head parts with these names (build_svl_esp.py).
SSE nif (20.2.0.7, bs 100)."""
import struct, sys

def read(path):
    d = open(path, 'rb').read()
    o = d.index(b'\n') + 1
    head_start = o
    ver, endian, user, nblocks = struct.unpack_from('<IBII', d, o); o += 13
    bsver = struct.unpack_from('<I', d, o)[0]; o += 4
    for _ in range(3):
        o += 1 + d[o]
    pre = d[:o]                                   # everything up to the block type table (incl. nblocks field)
    ntypes = struct.unpack_from('<H', d, o)[0]; o += 2
    types = []
    for _ in range(ntypes):
        n = struct.unpack_from('<I', d, o)[0]; types.append(d[o+4:o+4+n].decode()); o += 4 + n
    tidx = list(struct.unpack_from('<%dH' % nblocks, d, o)); o += 2 * nblocks
    sizes = struct.unpack_from('<%dI' % nblocks, d, o); o += 4 * nblocks
    nstr, maxlen = struct.unpack_from('<II', d, o); o += 8
    strings = []
    for _ in range(nstr):
        n = struct.unpack_from('<I', d, o)[0]; strings.append(d[o+4:o+4+n].decode('latin1')); o += 4 + n
    ngroups = struct.unpack_from('<I', d, o)[0]; groups = d[o:o+4+4*ngroups]; o += 4 + 4 * ngroups
    blocks = []
    for i in range(nblocks):
        blocks.append([types[tidx[i]], bytearray(d[o:o+sizes[i]])]); o += sizes[i]
    footer = d[o:]
    return dict(pre=pre, head_start=head_start, types=types, blocks=blocks, strings=strings, groups=groups, footer=footer)

def write(path, f):
    pre = bytearray(f['pre'])
    hs = f['head_start']
    struct.pack_into('<I', pre, hs + 9, len(f['blocks']))      # version(4) endian(1) user(4) -> nblocks
    out = bytearray(pre)
    out += struct.pack('<H', len(f['types']))
    for t in f['types']:
        out += struct.pack('<I', len(t)) + t.encode()
    out += struct.pack('<%dH' % len(f['blocks']), *[f['types'].index(t) for t, _ in f['blocks']])
    out += struct.pack('<%dI' % len(f['blocks']), *[len(b) for _, b in f['blocks']])
    out += struct.pack('<II', len(f['strings']), max(len(s) for s in f['strings']))
    for s in f['strings']:
        out += struct.pack('<I', len(s)) + s.encode('latin1')
    out += f['groups']
    for _, b in f['blocks']:
        out += b
    out += f['footer']
    open(path, 'wb').write(out)

def ref(b, off, fn):
    v = struct.unpack_from('<i', b, off)[0]
    if v >= 0:
        struct.pack_into('<i', b, off, fn(v))

def shape_offsets(b):
    """BSTriShape / BSDynamicTriShape: offsets of the name, skin, shader and alpha refs."""
    ne = struct.unpack_from('<I', b, 4)[0]
    q = 8 + 4 * ne + 4 + 4 + 52 + 4 + 16    # controller, flags, transform, collision, bounding sphere
    return 0, q, q + 4, q + 8

def fix_block(t, b, fn, bonefn=None, strfn=None):
    if t in ('BSTriShape', 'BSDynamicTriShape'):
        name, sk, sh, al = shape_offsets(b)
        if strfn:
            ref(b, name, strfn)
        ref(b, sk, fn); ref(b, sh, fn); ref(b, al, fn)
    elif t in ('NiSkinInstance', 'BSDismemberSkinInstance'):
        ref(b, 0, fn); ref(b, 4, fn)                        # data, partition (skeleton root 3 is shared)
        nb = struct.unpack_from('<I', b, 12)[0]
        if bonefn:
            for k in range(nb):
                ref(b, 16 + 4 * k, bonefn)
    elif t == 'BSLightingShaderProperty':
        ne = struct.unpack_from('<I', b, 8)[0]                # shader type, name, nExtra
        if strfn:
            ref(b, 4, strfn)
        q = 12 + 4 * ne
        ref(b, q, fn)                                         # controller
        ref(b, q + 4 + 4 + 4 + 8 + 8, fn)                     # texture set (after flags1, flags2, uv offset, uv scale)
    elif t == 'NiAlphaProperty':
        if strfn:
            ref(b, 0, strfn)

def bone_names(f):
    out = []
    for i in (1, 2):
        nm = struct.unpack_from('<i', f['blocks'][i][1], 0)[0]
        out.append(f['strings'][nm])
    return out

ser = read(sys.argv[1]); val = read(sys.argv[2])
assert [t for t, _ in ser['blocks'][:24]] == [t for t, _ in val['blocks'][:24]], 'face layouts differ'
sb, vb = bone_names(ser), bone_names(val)
print('bones serana', sb, 'valerica', vb)
bone_map = {1: 1 + sb.index(vb[0]), 2: 1 + sb.index(vb[1]), 3: 3, 0: 0}
HAIR_V = range(24, 68)        # Valerica hair + hairline
TAIL_S = range(56, 82)        # Serana lashes, eyes, brows, glow lens
shift = len(HAIR_V) - (56 - 24)
new_blocks = [list(x) for x in ser['blocks'][:24]]
strings = list(ser['strings'])
# shape names become SVL_ head part names (Serana Vampire Look.esp 0x802-0x808): the engine finds each facegen shape by
# the editor ID of a head part on the NPC, so these must match the plugin, and must not clash with ValericaDFE.esp's
RENAME = {n: 'SVL_' + n for n in ('WendigoNoHorn', 'VWendigo3', 'VWendigo4', 'VWendigo4HL', 'VWendigoHL', 'VWendigoSC',
                                   'VDFHairline')}
def str_map(i):
    s = val['strings'][i]
    s = RENAME.get(s, s)
    if s not in strings:
        strings.append(s)
    return strings.index(s)
# hair colour: hair-tint shaders (type 6) end with the tint RGB, baked per NPC; Valerica's is light (0.66, 0.65, 0.64,
# drew blonde on Serana) -> use Serana's own (SDFHair's shader, block 28: 0.11, 0.11, 0.13). Valerica's file is untouched.
SER_TINT = ser['blocks'][28][1][-12:]
assert ser['blocks'][28][0] == 'BSLightingShaderProperty' and struct.unpack_from('<I', ser['blocks'][28][1], 0)[0] == 6
for i in HAIR_V:
    t, b = val['blocks'][i]
    b = bytearray(b)
    fix_block(t, b, lambda v: v, bonefn=lambda v: bone_map.get(v, v), strfn=str_map)
    if t == 'BSLightingShaderProperty' and struct.unpack_from('<I', b, 0)[0] == 6:
        b[-12:] = SER_TINT
    new_blocks.append([t, b])
for i in TAIL_S:
    t, b = ser['blocks'][i]
    b = bytearray(b)
    fix_block(t, b, lambda v: v + shift if v >= 24 else v)
    new_blocks.append([t, b])
# root children (block 3 = BSFaceGenNiNodeSkinned): face shapes, the new hair shapes, the moved tail shapes
shape_types = ('BSTriShape', 'BSDynamicTriShape')
children = [i for i, (t, _) in enumerate(new_blocks) if t in shape_types]
b3 = ser['blocks'][3][1]
ne = struct.unpack_from('<I', b3, 4)[0]
q = 8 + 4 * ne + 4 + 4 + 52 + 4
nc = struct.unpack_from('<I', b3, q)[0]
rest = b3[q + 4 + 4 * nc:]
new_b3 = bytearray(b3[:q]) + struct.pack('<I', len(children)) + struct.pack('<%di' % len(children), *children) + rest
new_blocks[3] = ['NiNode', new_b3]
for t, _ in new_blocks:
    assert t in ser['types'], t
out = dict(ser); out['blocks'] = new_blocks; out['strings'] = strings
write(sys.argv[3], out)
print('wrote', sys.argv[3], 'blocks', len(new_blocks), 'shapes', children)
