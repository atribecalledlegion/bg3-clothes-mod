"""Sword model layout for the Copied blade vs the Leaf / Fire Dai-Katana (2026-10-20). Run after restore_katana_meshes.

Mitsunari's sword rig only switches poses when loaded from his own path (tested: his untouched nif copied under
meshes\\HKO\\copied\\ ignored the pose events; a version with stripped root children broke too). So:
  - his untouched BladesAkaviriDaiKatana.nif goes to its own path in <out mod> (the Hokage mod outranks Katana
    Crafting), for the Copied blade; his scabbard props are only in his mod, so they need nothing here
  - the plain restored model (restore_katana_meshes) moves to BladesAkaviriDaiKatanaLeaf.nif in the same folder for
    the Leaf / Fire record override (under meshes\\HKO\\leaf\\ it showed for a frame on equip, then vanished)
Never edit these nifs.

usage: fix_mitsunari_rigs.py <Mitsunari mod folder> <out mod folder>
"""
import os, shutil, sys

MITSU, OUT = sys.argv[1], sys.argv[2]
SWORD = r'meshes\Weapons\akaviri\BladesAkaviriDaiKatana.nif'
LEAF = os.path.join(OUT, r'meshes\Weapons\akaviri\BladesAkaviriDaiKatanaLeaf.nif')   # HKO\leaf\ vanished in game

plain = open(os.path.join(OUT, SWORD), 'rb').read()
if plain != open(os.path.join(MITSU, SWORD), 'rb').read():         # first run after restore_katana_meshes
    open(LEAF, 'wb').write(plain)
assert os.path.isfile(LEAF), 'run restore_katana_meshes first (plain model needed)'
shutil.copyfile(os.path.join(MITSU, SWORD), os.path.join(OUT, SWORD))
for old in (r'meshes\HKO\copied', r'meshes\HKO\leaf'):
    if os.path.isdir(os.path.join(OUT, old)):
        shutil.rmtree(os.path.join(OUT, old))
print('Leaf model -> BladesAkaviriDaiKatanaLeaf.nif, Mitsunari sword at its own path')
