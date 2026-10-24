"""flatten_skeleton.py <in.nif> <out.nif>
Naruto Wardrobe SE (converted from LE by CAO): every armour nif carries a whole embedded skeleton (NPC > NPC Root >
... ~570 NiNodes, plus CME Camera3rd / CharacterBumper) and its skin instances bind to those embedded nodes. In game
(2026-10-17) the Leaf Jonin vest stayed frozen in its bind (T) pose while the head/hands animated ("bobble head"),
although the skin weights are intact. This rewrites the file the way Outfit Studio saves SSE armour:
  root NiNode -> [extra data (BSX ...)] + the bones the skins use (flat, world bind transforms, no children) + shapes
  and drops every other node. Shapes keep their skin/shader/alpha/texture blocks; all refs are remapped.
SSE nif 20.2.0.7 / bsver 100. Block types handled: NiNode, BSXFlags, NiStringExtraData, BSTriShape,
BSDismemberSkinInstance, NiSkinInstance, NiSkinData, NiSkinPartition, BSLightingShaderProperty, BSShaderTextureSet,
NiAlphaProperty (anything else -> error, nothing written)."""
import struct, sys

def read(path):
    d = open(path, 'rb').read()
    o = d.index(b'\n') + 1
    head_start = o
    ver, endian, user, nblocks = struct.unpack_from('<IBII', d, o); o += 13
    o += 4                                      # bs version
    for _ in range(3):
        o += 1 + d[o]
    pre = d[:o]
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
    return dict(pre=pre, head_start=head_start, types=types, blocks=blocks, strings=strings, groups=groups,
                footer=d[o:])

def write(path, f):
    pre = bytearray(f['pre'])
    struct.pack_into('<I', pre, f['head_start'] + 9, len(f['blocks']))
    used = []
    for t, _ in f['blocks']:
        if t not in used:
            used.append(t)
    out = bytearray(pre)
    out += struct.pack('<H', len(used))
    for t in used:
        out += struct.pack('<I', len(t)) + t.encode()
    out += struct.pack('<%dH' % len(f['blocks']), *[used.index(t) for t, _ in f['blocks']])
    out += struct.pack('<%dI' % len(f['blocks']), *[len(b) for _, b in f['blocks']])
    out += struct.pack('<II', len(f['strings']), max(len(s) for s in f['strings']))
    for s in f['strings']:
        out += struct.pack('<I', len(s)) + s.encode('latin1')
    out += f['groups']
    for _, b in f['blocks']:
        out += b
    out += struct.pack('<Ii', 1, 0)             # footer: one root, block 0
    open(path, 'wb').write(out)

# ---- NiNode layout (bsver 100): name, nExtra, extras, controller, flags, T(12) R(36) S(4), collision, children,
# nEffects, effects
def node_parts(b):
    ne = struct.unpack_from('<I', b, 4)[0]
    q0 = 8 + 4 * ne
    nc = struct.unpack_from('<I', b, q0 + 64)[0]
    kids = list(struct.unpack_from('<%di' % nc, b, q0 + 68))
    e0 = q0 + 68 + 4 * nc
    neff = struct.unpack_from('<I', b, e0)[0]
    assert e0 + 4 + 4 * neff == len(b), 'unexpected NiNode layout'
    extras = list(struct.unpack_from('<%di' % ne, b, 8))
    t = struct.unpack_from('<3f', b, q0 + 8)
    r = struct.unpack_from('<9f', b, q0 + 20)
    s = struct.unpack_from('<f', b, q0 + 56)[0]
    flags = struct.unpack_from('<I', b, q0 + 4)[0]
    return dict(name=struct.unpack_from('<i', b, 0)[0], extras=extras, flags=flags, t=t, r=r, s=s, kids=kids)

def make_node(name, extras, flags, t, r, s, kids):
    return bytearray(struct.pack('<iI', name, len(extras)) + struct.pack('<%di' % len(extras), *extras)
                     + struct.pack('<iI', -1, flags) + struct.pack('<3f', *t) + struct.pack('<9f', *r)
                     + struct.pack('<f', s) + struct.pack('<i', -1) + struct.pack('<I', len(kids))
                     + struct.pack('<%di' % len(kids), *kids) + struct.pack('<I', 0))

def mat_mul(a, b):
    return [sum(a[3 * i + k] * b[3 * k + j] for k in range(3)) for i in range(3) for j in range(3)]

def mat_vec(a, v):
    return [sum(a[3 * i + k] * v[k] for k in range(3)) for i in range(3)]

def compose(p, c):     # world = parent o local
    pt, pr, ps = p
    ct, cr, cs = c
    rv = mat_vec(pr, ct)
    return ([pt[i] + ps * rv[i] for i in range(3)], mat_mul(pr, cr), ps * cs)

def flatten(src, dst):
    f = read(src)
    B = f['blocks']
    allowed = {'NiNode', 'BSXFlags', 'NiStringExtraData', 'BSTriShape', 'BSDismemberSkinInstance', 'NiSkinInstance',
               'NiSkinData', 'NiSkinPartition', 'BSLightingShaderProperty', 'BSShaderTextureSet', 'NiAlphaProperty'}
    bad = {t for t, _ in B} - allowed
    assert not bad, 'unhandled block types %s' % bad
    assert B[0][0] == 'NiNode'
    # parents and world transforms of every node
    parent = {}
    for i, (t, b) in enumerate(B):
        if t == 'NiNode':
            for k in node_parts(b)['kids']:
                if k >= 0:
                    parent[k] = i
    world = {}
    def wt(i):
        if i in world:
            return world[i]
        n = node_parts(B[i][1])
        local = (list(n['t']), list(n['r']), n['s'])
        w = local if i == 0 or i not in parent else compose(wt(parent[i]), local)
        world[i] = w
        return w
    root = node_parts(B[0][1])
    root_w = ([0.0, 0.0, 0.0], [1, 0, 0, 0, 1, 0, 0, 0, 1], 1.0)
    world[0] = root_w           # the root's own transform stays on the root; bones are expressed under it
    shapes = [i for i, (t, _) in enumerate(B) if t == 'BSTriShape']
    for i in shapes:
        assert parent.get(i) == 0, 'shape %d is not a child of the root - not handled' % i
    bones = []
    deps = []
    def dep(i):
        if i >= 0 and i not in deps:
            deps.append(i)
    for i in shapes:
        b = B[i][1]
        ne = struct.unpack_from('<I', b, 4)[0]
        for e in struct.unpack_from('<%di' % ne, b, 8):
            dep(e)
        q = 8 + 4 * ne + 4 + 4 + 52 + 4 + 16
        sk, sh, al = struct.unpack_from('<3i', b, q)
        dep(sk); dep(sh); dep(al)
        if sk >= 0:
            s = B[sk][1]
            dep(struct.unpack_from('<i', s, 0)[0]); dep(struct.unpack_from('<i', s, 4)[0])
            nb = struct.unpack_from('<I', s, 12)[0]
            for x in struct.unpack_from('<%di' % nb, s, 16):
                assert B[x][0] == 'NiNode'
                if x not in bones:
                    bones.append(x)
        if sh >= 0:
            s = B[sh][1]
            sne = struct.unpack_from('<I', s, 8)[0]
            dep(struct.unpack_from('<i', s, 12 + 4 * sne + 28)[0])          # texture set
    for x in deps:
        assert B[x][0] not in ('NiNode', 'BSTriShape'), (x, B[x][0])
    # new order: root, root extras, bones, shapes, their dependents
    order = [0] + [e for e in root['extras'] if e >= 0] + bones + shapes + deps
    remap = {old: new for new, old in enumerate(order)}
    R = lambda v: remap[v] if v >= 0 else -1
    new = []
    for old in order:
        t, b = B[old]
        b = bytearray(b)
        if old == 0:
            b = make_node(root['name'], [R(e) for e in root['extras'] if e >= 0], root['flags'], root['t'], root['r'],
                          root['s'], [remap[x] for x in bones] + [remap[x] for x in shapes])
        elif old in bones:
            n = node_parts(b)
            wt_ = wt(old)
            b = make_node(n['name'], [], n['flags'], wt_[0], wt_[1], wt_[2], [])
        elif t == 'BSTriShape':
            ne = struct.unpack_from('<I', b, 4)[0]
            for k in range(ne):
                struct.pack_into('<i', b, 8 + 4 * k, R(struct.unpack_from('<i', b, 8 + 4 * k)[0]))
            q0 = 8 + 4 * ne
            struct.pack_into('<i', b, q0, -1)                                # controller
            struct.pack_into('<i', b, q0 + 4 + 4 + 52, -1)                   # collision
            q = q0 + 4 + 4 + 52 + 4 + 16
            for k in range(3):
                struct.pack_into('<i', b, q + 4 * k, R(struct.unpack_from('<i', b, q + 4 * k)[0]))
        elif t in ('BSDismemberSkinInstance', 'NiSkinInstance'):
            for off in (0, 4, 8):
                struct.pack_into('<i', b, off, R(struct.unpack_from('<i', b, off)[0]))
            nb = struct.unpack_from('<I', b, 12)[0]
            for k in range(nb):
                struct.pack_into('<i', b, 16 + 4 * k, R(struct.unpack_from('<i', b, 16 + 4 * k)[0]))
        elif t == 'BSLightingShaderProperty':
            ne = struct.unpack_from('<I', b, 8)[0]
            for k in range(ne):
                struct.pack_into('<i', b, 12 + 4 * k, R(struct.unpack_from('<i', b, 12 + 4 * k)[0]))
            q = 12 + 4 * ne
            struct.pack_into('<i', b, q, -1)
            struct.pack_into('<i', b, q + 28, R(struct.unpack_from('<i', b, q + 28)[0]))
        elif t == 'NiAlphaProperty':
            ne = struct.unpack_from('<I', b, 4)[0]
            for k in range(ne):
                struct.pack_into('<i', b, 8 + 4 * k, R(struct.unpack_from('<i', b, 8 + 4 * k)[0]))
            struct.pack_into('<i', b, 8 + 4 * ne, -1)
        new.append([t, b])
    f['blocks'] = new
    write(dst, f)
    return len(B), len(new), len(bones), len(shapes)

def validate(path):
    f = read(path)
    B = f['blocks']
    def chk(v, types):
        assert v == -1 or (0 <= v < len(B) and B[v][0] in types), (v, B[v][0] if 0 <= v < len(B) else None, types)
    for i, (t, b) in enumerate(B):
        if t == 'NiNode':
            n = node_parts(b)
            for k in n['kids']:
                chk(k, ('NiNode', 'BSTriShape'))
        elif t == 'BSTriShape':
            ne = struct.unpack_from('<I', b, 4)[0]
            q = 8 + 4 * ne + 4 + 4 + 52 + 4 + 16
            sk, sh, al = struct.unpack_from('<3i', b, q)
            chk(sk, ('BSDismemberSkinInstance', 'NiSkinInstance')); chk(sh, ('BSLightingShaderProperty',))
            chk(al, ('NiAlphaProperty',))
        elif t in ('BSDismemberSkinInstance', 'NiSkinInstance'):
            chk(struct.unpack_from('<i', b, 0)[0], ('NiSkinData',)); chk(struct.unpack_from('<i', b, 4)[0], ('NiSkinPartition',))
            chk(struct.unpack_from('<i', b, 8)[0], ('NiNode',))
            nb = struct.unpack_from('<I', b, 12)[0]
            for x in struct.unpack_from('<%di' % nb, b, 16):
                chk(x, ('NiNode',))
        elif t == 'BSLightingShaderProperty':
            ne = struct.unpack_from('<I', b, 8)[0]
            chk(struct.unpack_from('<i', b, 12 + 4 * ne + 28)[0], ('BSShaderTextureSet',))
    return len(B)

if __name__ == '__main__':
    print(flatten(sys.argv[1], sys.argv[2]), 'validated blocks', validate(sys.argv[2]))
