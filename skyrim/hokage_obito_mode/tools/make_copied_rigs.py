"""Copied blade + scabbard props as their own nifs, following Mitsunari's author's custom-model process (2026-10-23).
Replaces fix_mitsunari_rigs.py. Run after restore_katana_meshes (Leaf / Fire keep the plain model at its own path).

The author's tutorial (custom katana for his rig): put the model inside his rig nif, rename any of the model's nodes
that clash ("if it's scb, rename it, anything"), save under NEW file names in a weapons folder
(weapons\\rtrabkatana\\katana.nif, katanahand.nif, katanamouth.nif), then a new WEAP with his KatanaScarbbardScript
pointing at new copies of the hand / mouth scabbard ARMO+ARMA using those nifs. His note: "model residue cause: model
name". Our earlier copy under meshes\\HKO\\copied\\ kept his file names and node names, which are the same as Katana
Crafting's plain model (1stPersonBladesAkaviriDaiKatana:*, Scb:0_2) - and failed.

Here his three rig nifs (the model inside is already his own katana) get the model's node names renamed in the string
table (every reference is by string index, so the file stays consistent; the rig nodes his controllers and the
autoplay graph use - myweaponroot, yamatoBlade, yamatoSCB, Blade, katanaScb, mBegin, IshidaState1-5 - are untouched)
and are written under new names in meshes\\Weapons\\HKOCopied\\. Nothing else in the files changes.

usage: make_copied_rigs.py <Mitsunari mod folder> <out mod folder>
"""
import os, shutil, struct, sys

MITSU, OUT = sys.argv[1], sys.argv[2]
RIGS = {r'meshes\Weapons\akaviri\BladesAkaviriDaiKatana.nif': 'HKOCopiedKatana.nif',
        r'meshes\Weapons\Scabbard\Blade_scb_handA.nif': 'HKOCopiedKatanaHand.nif',
        r'meshes\Weapons\Scabbard\Blade_scb_MouthA.nif': 'HKOCopiedKatanaMouth.nif'}
OUT_DIR = os.path.join(OUT, r'meshes\Weapons\HKOCopied')
RENAME = {'1stPersonBladesAkaviriDaiKatana:Tsuba': 'HKOCopied:Tsuba',
          '1stPersonBladesAkaviriDaiKatana:Blade': 'HKOCopied:Blade',
          '1stPersonBladesAkaviriDaiKatana:Hilt': 'HKOCopied:Hilt',
          '1stPersonBladesAkaviriDaiKatana:0': 'HKOCopied:0',
          'Scb:0_2': 'HKOCopiedScb:0_2',
          'Scb': 'HKOCopiedScb'}
RIG_NODES = {'myweaponroot', 'yamatoBlade', 'yamatoSCB', 'Blade', 'katanaScb', 'mBegin'}


def rename_strings(b):
    """SSE nif (20.2.0.7): rewrite the header string table; blocks refer to strings by index only."""
    i = b.index(b'\n') + 1
    nblocks = struct.unpack_from('<I', b, i + 9)[0]; i += 17
    for _ in range(3): i += 1 + b[i]                                  # export info
    ntypes = struct.unpack_from('<H', b, i)[0]; i += 2
    for _ in range(ntypes): i += 4 + struct.unpack_from('<I', b, i)[0]
    i += 6 * nblocks                                                  # type indices + block sizes
    start = i
    nstr = struct.unpack_from('<I', b, i)[0]; i += 8
    strs = []
    for _ in range(nstr):
        n = struct.unpack_from('<I', b, i)[0]; strs.append(b[i+4:i+4+n].decode('latin1')); i += 4 + n
    assert RIG_NODES <= set(strs), 'not a Mitsunari rig: ' + ', '.join(sorted(RIG_NODES - set(strs)))
    new = [RENAME.get(s, s) for s in strs]
    table = struct.pack('<II', nstr, max(len(s) for s in new))
    table += b''.join(struct.pack('<I', len(s)) + s.encode('latin1') for s in new)
    return b[:start] + table + b[i:], sum(a != c for a, c in zip(strs, new))


os.makedirs(OUT_DIR, exist_ok=True)
for src, name in RIGS.items():
    data, n = rename_strings(open(os.path.join(MITSU, src), 'rb').read())
    open(os.path.join(OUT_DIR, name), 'wb').write(data)
    print(name, '-', n, 'model names renamed')
for old in (r'meshes\HKO\copied', r'meshes\HKO\leaf'):
    if os.path.isdir(os.path.join(OUT, old)):
        shutil.rmtree(os.path.join(OUT, old))
leaf = os.path.join(OUT, r'meshes\Weapons\akaviri\BladesAkaviriDaiKatanaLeaf.nif')
if os.path.isfile(leaf): os.remove(leaf)
