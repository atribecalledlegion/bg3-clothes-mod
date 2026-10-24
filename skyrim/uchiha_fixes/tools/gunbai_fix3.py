"""gunbai_fix3.py <orig.nif> <out.nif> <scale> <pole_stretch>
Alternative gunbai (SSE BSTriShape, 28-byte vertices: pos 3f + bitangentX f | uv 2h | normal 3ub + bitangentY b |
tangent 3ub + bitangentZ b; then triangles 3H):
- splits the mesh into connected parts; the pole (x extent < 2.5) is left round, and the handle (the pole below the
  gourd) is lengthened by pole_stretch;
- on the other parts, the two broad faces get normals exactly +-Y and a consistent tangent frame recomputed from the
  UVs (the original frames were scrambled - rotated/mirrored per patch - which drew a lighting square);
- scales the whole shape (shape scale + translation)."""
import struct, sys, math
src, out, scale, stretch = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
exec(open(__file__.replace('gunbai_fix3.py', 'gunbai_mesh.py')).read().split("print('tris'")[0].replace("src = sys.argv[1]", "pass"))
def dec(b): return b / 255.0 * 2.0 - 1.0
def enc(x): return max(0, min(255, int(round((x + 1.0) / 2.0 * 255.0))))
def half(o): return struct.unpack_from('<e', d, o)[0]
P = [list(struct.unpack_from('<3f', d, vstart + k * vsize)) for k in range(nv)]
UV = [(half(vstart + k * vsize + 16), half(vstart + k * vsize + 18)) for k in range(nv)]
N = [[dec(d[vstart + k * vsize + 20 + a]) for a in range(3)] for k in range(nv)]
tri_o = vstart + nv * vsize
T = [struct.unpack_from('<3H', d, tri_o + 6 * t) for t in range(ntri)]
# connected parts
parent = list(range(nv))
def find(a):
    while parent[a] != a:
        parent[a] = parent[parent[a]]; a = parent[a]
    return a
for a, b, c in T:
    for u, v in ((a, b), (b, c)):
        ru, rv = find(u), find(v)
        if ru != rv: parent[ru] = rv
parts = {}
for k in range(nv):
    parts.setdefault(find(k), []).append(k)
pole = set()
for root, ks in parts.items():
    xs = [P[k][0] for k in ks]; zs = [P[k][2] for k in ks]
    kind = 'pole' if max(xs) - min(xs) < 2.5 else 'body'
    print('part', len(ks), 'verts x', round(min(xs), 1), round(max(xs), 1), 'z', round(min(zs), 1), round(max(zs), 1), '->', kind)
    if kind == 'pole': pole.update(ks)
# lengthen only the handle: the pole below the gourd (body bottom z ~ -14.4) is stretched away from the body
body_min = min(P[k][2] for k in range(nv) if k not in pole)
for k in pole:
    if P[k][2] < body_min:
        P[k][2] = body_min + (P[k][2] - body_min) * stretch
        struct.pack_into('<f', d, vstart + k * vsize + 8, P[k][2])
print('handle below z', round(body_min, 1), 'now reaches', round(min(P[k][2] for k in pole), 1))
# tangent frames from the UVs, face by face, on the broad faces of the body
acc_t = [[0.0, 0.0, 0.0] for _ in range(nv)]
acc_b = [[0.0, 0.0, 0.0] for _ in range(nv)]
for a, b, c in T:
    if a in pole: continue
    e1 = [P[b][i] - P[a][i] for i in range(3)]; e2 = [P[c][i] - P[a][i] for i in range(3)]
    du1, dv1 = UV[b][0] - UV[a][0], UV[b][1] - UV[a][1]
    du2, dv2 = UV[c][0] - UV[a][0], UV[c][1] - UV[a][1]
    r = du1 * dv2 - du2 * dv1
    if abs(r) < 1e-12: continue
    r = 1.0 / r
    tv = [(e1[i] * dv2 - e2[i] * dv1) * r for i in range(3)]     # direction of +U
    bv = [(e2[i] * du1 - e1[i] * du2) * r for i in range(3)]     # direction of +V
    for v in (a, b, c):
        for i in range(3):
            acc_t[v][i] += tv[i]; acc_b[v][i] += bv[i]
def norm(v):
    l = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / l for x in v]
def dot(a, b): return sum(a[i] * b[i] for i in range(3))
# Skyrim stores the frame with tangent/bitangent swapped against the textbook convention; learn the mapping from
# the vertices whose original frame agrees with the UV-derived one
votes = {}
cand = []
for k in range(nv):
    if k in pole or abs(N[k][1]) < 0.9: continue
    o = vstart + k * vsize
    st = [dec(d[o + 24]), dec(d[o + 25]), dec(d[o + 26])]
    sb = [struct.unpack_from('<f', d, o + 12)[0], dec(d[o + 23]), dec(d[o + 27])]
    tu, tvv = norm(acc_t[k]), norm(acc_b[k])
    for name, vec in (('st=U', dot(st, tu)), ('st=V', dot(st, tvv)), ('sb=U', dot(sb, tu)), ('sb=V', dot(sb, tvv))):
        votes[name] = votes.get(name, 0.0) + vec
    cand.append(k)
print('frame votes', {k: round(v, 1) for k, v in votes.items()})
st_is_v = abs(votes['st=V']) > abs(votes['st=U'])
st_sign = 1.0 if (votes['st=V'] if st_is_v else votes['st=U']) >= 0 else -1.0
sb_sign = 1.0 if (votes['sb=U'] if st_is_v else votes['sb=V']) >= 0 else -1.0
print('stored tangent = %s%s, stored bitangent = %s%s' % ('+' if st_sign > 0 else '-', 'V' if st_is_v else 'U',
                                                          '+' if sb_sign > 0 else '-', 'U' if st_is_v else 'V'))
fixed = 0
for k in range(nv):
    if k in pole or abs(N[k][1]) < 0.6: continue
    o = vstart + k * vsize
    n = [0.0, 1.0 if N[k][1] > 0 else -1.0, 0.0]
    tu, tvv = norm(acc_t[k]), norm(acc_b[k])
    a_vec = tvv if st_is_v else tu
    b_vec = tu if st_is_v else tvv
    a_vec = norm([a_vec[i] - n[i] * dot(a_vec, n) for i in range(3)])
    b_vec = norm([b_vec[i] - n[i] * dot(b_vec, n) for i in range(3)])
    st = [x * st_sign for x in a_vec]; sb = [x * sb_sign for x in b_vec]
    d[o + 20] = enc(n[0]); d[o + 21] = enc(n[1]); d[o + 22] = enc(n[2])
    d[o + 24] = enc(st[0]); d[o + 25] = enc(st[1]); d[o + 26] = enc(st[2])
    struct.pack_into('<f', d, o + 12, sb[0]); d[o + 23] = enc(sb[1]); d[o + 27] = enc(sb[2])
    fixed += 1
t0 = struct.unpack_from('<3f', d, tr_off)
struct.pack_into('<3f', d, tr_off, *(c * scale for c in t0))
struct.pack_into('<f', d, sc_off, scale)
open(out, 'wb').write(d)
print('wrote', out, 'scale', scale, 'pole stretch', stretch, 'pole verts', len(pole), 'face frames rebuilt', fixed)
