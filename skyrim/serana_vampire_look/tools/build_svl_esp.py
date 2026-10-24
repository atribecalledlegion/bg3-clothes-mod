"""Build Serana Vampire Look.esp (ESL) - additions on top of Serana DF Edit (SkyPatcher version).

Usage: build_svl_esp.py <SeranaDFE.esp> <ValericaDFE.esp> <out.esp>

Records (append-only object IDs):
  0x800 ARMA SVL_ToenailsAA   black toenails (meshes/SVL/toenails_0/_1.nif: the RedP toenail mesh shipped with
                              Jinxxed's Hachishaku follower, texture footblackW) on slot 57: on the feet slot (37) it
                              REPLACED her feet, since only one part per slot is drawn; race data from SDF's SDFFeet
  0x801 ARMO SVL_SeranaSkin   SDF's SDFSkin (SeranaDFE.esp 0x828) + 0x800, slots + 57. SkyPatcher gives it to Serana
                              through the copy of SDF's SkyPatcher ini this mod ships (same path, replaces the author's).
  0x802-0x808 HDPT SVL_<name> Valerica DF Edition's Wendigo hair (copies of ValericaDFE.esp 0x708, 0x829-0x82E; RNAM =
                              a Skyrim.esm list). Facegen-only like SDF's own parts: MODL is a placeholder and the
                              geometry is the SVL_ shapes put in her facegen by transplant_hair.py (names must match).
                              0x808 SVL_WendigoNoHorn = main hair, the other six its extras (flags exactly as VDF).
  SeranaDFE.esp 0x82C NPC_    override: SDF hair parts 0x701, 0x708, 0x829-0x82B out, 0x802-0x808 in (2026-10-16).
"""
import struct, sys, zlib

SDF, VDF, OUT = sys.argv[1:4]
NAIL_SLOT = 1 << (57 - 30)
MASTERS = ['Skyrim.esm', 'Dawnguard.esm', 'SeranaDFE.esp']    # SDF's own records keep index 2
OWN = len(MASTERS) << 24
FID = {'SVL_ToenailsAA': OWN | 0x800, 'SVL_SeranaSkin': OWN | 0x801}
VDF_HAIR = [(0x802, 0x708), (0x803, 0x829), (0x804, 0x82A), (0x805, 0x82B), (0x806, 0x82C), (0x807, 0x82D),
            (0x808, 0x82E)]                                   # (our ID, ValericaDFE.esp ID); 0x82E = main hair

def sub(t, data): return t.encode() + struct.pack('<H', len(data)) + data
def z(s): return s.encode('cp1252') + b'\0'
def rec(t, fid, subs, flags=0, ver=44):
    body = b''.join(subs)
    return t.encode() + struct.pack('<IIIIHH', len(body), flags, fid, 0, ver, 0) + body
def grup(label, body):
    return b'GRUP' + struct.pack('<I', 24 + len(body)) + label.encode() + struct.pack('<IHHI', 0, 0, 0, 0) + body
def subs_of(d):
    i = 0
    while i < len(d):
        t = d[i:i+4].decode('latin1'); n = struct.unpack_from('<H', d, i+4)[0]
        yield t, d[i+6:i+6+n]; i += 6 + n

def load(path):
    buf = open(path, 'rb').read(); hsize = struct.unpack_from('<I', buf, 4)[0]
    masters = [d.rstrip(b'\0').decode() for t, d in subs_of(buf[24:24 + hsize]) if t == 'MAST']
    assert masters == MASTERS[:2], masters                  # local IDs are index 2 in both files and in ours
    R = {}
    def walk(o, e):
        while o < e:
            t = buf[o:o+4].decode('latin1'); n = struct.unpack_from('<I', buf, o+4)[0]
            if t == 'GRUP': walk(o + 24, o + n); o += n; continue
            fl, fid = struct.unpack_from('<II', buf, o+8)
            b = buf[o+24:o+24+n]
            if fl & 0x40000: b = zlib.decompress(b[4:])
            R[fid & 0xFFFFFF] = (t, list(subs_of(b)), fl & ~0x40000); o += 24 + n
    walk(24 + hsize, len(buf))
    return R
SDF_R = load(SDF)
R = {k: v[:2] for k, v in SDF_R.items()}
V = load(VDF)

feet_t, feet = R[0x827]; assert feet_t == 'ARMA'
nails = []
for t, d in feet:
    if t == 'EDID': d = z('SVL_ToenailsAA')
    elif t in ('MO2T', 'MO3T', 'NAM0', 'NAM1', 'NAM2', 'NAM3'): continue      # skin texture swaps / old hashes
    elif t == 'BODT': d = struct.pack('<I', NAIL_SLOT) + d[4:]
    elif t == 'MOD2': d = z(r'SVL\toenails_1.nif')
    elif t == 'MOD3': d = z(r'SVL\toenails_1.nif')
    nails.append(sub(t, d))
toenails = rec('ARMA', FID['SVL_ToenailsAA'], nails)

# 2026-10-15: the toenail mesh never sat cleanly on her toes; the nails are now painted on the body texture
# (tools/paint_toenails.py), so the skin no longer carries 0x800 (record kept, unused: IDs are append-only)
NAILS_MESH = False
skin_t, skin = R[0x828]; assert skin_t == 'ARMO'
out = []
for t, d in skin:
    if t == 'EDID': d = z('SVL_SeranaSkin')
    elif t == 'BOD2' and NAILS_MESH: d = struct.pack('<I', struct.unpack_from('<I', d)[0] | NAIL_SLOT) + d[4:]
    out.append(sub(t, d))
    if NAILS_MESH and t == 'MODL' and struct.unpack('<I', d)[0] == 0x02000827:  # after SDF's feet
        out.append(sub('MODL', struct.pack('<I', FID['SVL_ToenailsAA'])))
assert sum(1 for s in out if s[:4] == b'MODL') == (4 if NAILS_MESH else 3)
skin_rec = rec('ARMO', FID['SVL_SeranaSkin'], out)

# Wendigo hair head parts. ValericaDFE.esp's local IDs are index 2 (= SeranaDFE.esp in our masters): remap to ours.
vmap = {(2 << 24) | v: OWN | o for o, v in VDF_HAIR}
hair = b''
for own_id, vid in VDF_HAIR:
    t, subs, _ = V[vid]; assert t == 'HDPT'
    name = dict(subs)['EDID'].rstrip(b'\0').decode()
    out = []
    for st, d in subs:
        if st == 'EDID': d = z('SVL_' + name)
        elif st == 'FULL': d = z('SVL ' + name)
        elif st == 'HNAM': d = struct.pack('<I', vmap[struct.unpack('<I', d)[0]])
        elif st == 'RNAM': assert struct.unpack('<I', d)[0] >> 24 == 0       # Skyrim.esm list, index unchanged
        out.append(sub(st, d))
    hair += rec('HDPT', OWN | own_id, out)

# Serana: SDF's NPC record with the hair swapped
npc_t, npc = R[0x82C]; assert npc_t == 'NPC_'
# DF records list every hair part directly in PNAM, extras included (SDF: 0x701 + 0x708, 0x829-0x82B; VDF: 0x708,
# 0x829-0x82E). v2 swapped only 0x701, so SDF's four hair extras stayed on her with no shapes in the facegen -> the
# engine rejected the whole facegen again (invisible head, floating teeth). Now: all SDF hair parts out, all 7 in.
SDF_HAIR = [(2 << 24) | x for x in (0x701, 0x708, 0x829, 0x82A, 0x82B)]
pnams = [struct.unpack('<I', d)[0] for t, d in npc if t == 'PNAM']
assert all(h in pnams for h in SDF_HAIR), [hex(x) for x in pnams]
npc_out, done = [], False
for t, d in npc:
    if t == 'PNAM' and struct.unpack('<I', d)[0] in SDF_HAIR:
        if not done:
            npc_out += [sub('PNAM', struct.pack('<I', OWN | o)) for o, _ in VDF_HAIR]
            done = True
        continue
    npc_out.append(sub(t, d))
serana = rec('NPC_', (2 << 24) | 0x82C, npc_out, flags=SDF_R[0x82C][2])

hdr = [sub('HEDR', struct.pack('<fII', 1.7, 10, 0x809)), sub('CNAM', z('Claude')), sub('SNAM', z('Serana Vampire Look'))]
for m in MASTERS: hdr += [sub('MAST', z(m)), sub('DATA', bytes(8))]
open(OUT, 'wb').write(rec('TES4', 0, hdr, flags=0x200) + grup('HDPT', hair) + grup('ARMO', skin_rec) +
                      grup('NPC_', serana) + grup('ARMA', toenails))
print('wrote', OUT)
