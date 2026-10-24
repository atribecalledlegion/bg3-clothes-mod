"""PK Hair Collection "Hair 19" for the Dhaen Extended races.

No mesh, no bank, no textures: the mod only registers PK_Hair_Collection's own visual(s) for the Dhaen races, the way
Dhaen_Hair-Merged does for Ellian's hair (CharacterCreationSharedVisual + one Race node per Dhaen race with MergedInto).

    python items/pk_hair19_dhaen/build.py --f     # the normal-build mesh (Hair_19_F)      -> build/variants/PKHair19Dhaen_f.pak
    python items/pk_hair19_dhaen/build.py --fs    # the strong-build mesh (Hair_19_FS)     -> build/variants/PKHair19Dhaen_fs.pak
    python items/pk_hair19_dhaen/build.py --ab    # both, as two labelled test tiles       -> build/variants/PKHair19Dhaen_ab.pak
    python items/pk_hair19_dhaen/build.py --remap # clones PK's two visuals with NeedsSkeletonRemap=True (as Ellian's have)
    python items/pk_hair19_dhaen/refit.py         # once: scale PK's strong-build mesh to the Dhaen head -> art/out/*.GR2
    python items/pk_hair19_dhaen/build.py --final # SHIPPING BUILD: the remapped, refitted strong-build mesh, labelled plain "Hair 19"
    add --install to copy the result into the BG3 Mods folder as PKHair19Dhaen.pak (refuses to overwrite)

The Dependencies block is ALWAYS empty. Declaring PK_Hair_Collection there made the game reset modsettings.lsx to
GustavX on boot (also happened with Hair01Ponytail); Dhaen_Hair-Merged has an empty node and loads fine. Load order
already puts PK before this mod. Confirmed in game 2026-09-20.

Why NeedsSkeletonRemap: PK's visuals have it False (fine on vanilla skeletons), Ellian's have it True. On Dhaen the
unremapped PK hair drew only its scalp (bald). With the flag True the strong-build mesh (FS) sits correctly on a Dhaen
human; the normal-build mesh (F) renders but hangs low like a ring around the neck (its sockets sit ~0.1 lower). So
the shipping build uses FS only.
"""
import json, os, shutil, sys, uuid
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import hair_mod
from lspk import Pak

FOLDER = 'PKHair19Dhaen'
MOD_UUID = '2d484bbf-3064-4988-b6b8-cf31b1425651'
PK_NAME_HANDLE = 'h08e7f9f5g4e69g49e3g88e2g0409c2117ebe'      # "Hair 19" in PK's own localisation
# PK visuals (Meshes bank): Hair_19_F is BodyShape 0, Hair_19_FS is BodyShape 1; both feminine
VISUALS = {
    'f': ('76f49ee3-e0a0-4925-88d5-c6a8daf946ea', 'bf356afa-fcf3-4083-9334-4ca76336245a', 'Hair 19 TEST normal mesh'),
    'fs': ('5ea91e7e-bfd6-4aec-85f3-282272b82703', '79b7b981-8230-4dfc-bef3-475e6b276930', 'Hair 19 TEST strong mesh'),
}
# Dhaen races (merge targets) as listed in items/hair01_ponytail/hair.json
DHAEN = json.load(open(os.path.join(ROOT, 'items', 'hair01_ponytail', 'hair.json')))['dhaen']['races']

mode = next((a[2:] for a in sys.argv if a in ('--f', '--fs', '--ab', '--remap', '--final', '--ctl', '--ctl2')), None)
if not mode:
    raise SystemExit(__doc__)
keys = ['f', 'fs'] if mode in ('ab', 'remap') else ['fs'] if mode == 'final' else ['c1', 'c2', 'c3', 'c4'] if mode == 'ctl' else ['t2', 't4', 't5', 't6', 't7'] if mode == 'ctl2' else [mode]
# a lone tile keeps PK's own "Hair 19" label; the A/B test needs two distinguishable labels (shipped loca)
own_names = mode in ('ab', 'remap', 'ctl', 'ctl2')
# tiles that ship their own GR2 instead of pointing at PK's: key -> file in art/out (made by refit.py)
GR2S = {'fs': ('PKHair19_FS_Dhaen.GR2', 'Hair_19_FS_Mesh')} if mode == 'final' else {}
REMAP = {}                                    # key -> False to leave NeedsSkeletonRemap as PK has it

src = os.path.join(HERE, 'src')
if os.path.isdir(src):
    shutil.rmtree(src)


def w(rel, text):
    p = os.path.join(src, *rel.split('/'))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)


if mode in ('remap', 'final'):
    # new visuals (cloned from PK's, flag flipped) get their own ids; the tiles say what they are
    VISUALS = {k: (v[0], str(uuid.uuid5(uuid.UUID(MOD_UUID), 'visual-' + k)), v[2].replace('TEST normal', 'REMAP normal')
                   .replace('TEST strong', 'REMAP strong')) for k, v in VISUALS.items()}
    PK_IDS = {'f': 'bf356afa-fcf3-4083-9334-4ca76336245a', 'fs': '79b7b981-8230-4dfc-bef3-475e6b276930'}


if mode == 'ctl':
    # control pak: four tiles, all clones of PK's strong-build visual with the remap flag, differing only in the GR2
    LABELS = {'c1': 'Hair 19 CTL1 PK original GR2', 'c2': 'Hair 19 CTL2 roundtrip x1.0',
              'c3': 'Hair 19 CTL3 refit x0.85', 'c4': 'Hair 19 CTL4 refit x0.85 conformed'}
    VISUALS = {k: (str(uuid.uuid5(uuid.UUID(MOD_UUID), 'shared-' + k)), str(uuid.uuid5(uuid.UUID(MOD_UUID), 'visual-' + k)),
                   LABELS[k]) for k in keys}
    PK_IDS = {k: '79b7b981-8230-4dfc-bef3-475e6b276930' for k in keys}
    GR2S = {'c2': ('PKHair19_ctl_roundtrip.GR2', 'Hair_19_FS_Mesh'), 'c3': ('PKHair19_FS_Dhaen.GR2', 'Hair_19_FS_Mesh'),
            'c4': ('PKHair19_ctl_conformed.GR2', 'Hair_19_FS_Mesh')}


if mode == 'ctl2':
    # control 2: what makes the game refuse the GR2 files Divine wrote? (PK's own file renders; every re-written one is bald)
    VM = 'HAIR_HUM_M_Straight_Short_M_Mesh'
    LABELS = {'t2': 'Hair 19 T2 PK bytes, our path', 't4': 'Hair 19 T4 roundtrip x0.85 NO remap',
              't5': 'Hair 19 T5 vanilla-skel x1.0', 't6': 'Hair 19 T6 vanilla-skel x0.85', 't7': 'Hair 19 T7 vanilla-skel x1.0 NO remap'}
    VISUALS = {k: (str(uuid.uuid5(uuid.UUID(MOD_UUID), 'shared-' + k)), str(uuid.uuid5(uuid.UUID(MOD_UUID), 'visual-' + k)),
                   LABELS[k]) for k in keys}
    PK_IDS = {k: '79b7b981-8230-4dfc-bef3-475e6b276930' for k in keys}
    GR2S = {'t2': ('PKHair19_ctl_orig_copy.GR2', None), 't4': ('PKHair19_FS_Dhaen.GR2', 'Hair_19_FS_Mesh'),
            't5': ('PKHair19_van_x100.GR2', VM), 't6': ('PKHair19_van_x085.GR2', VM), 't7': ('PKHair19_van_x100.GR2', VM)}
    REMAP = {'t4': False, 't7': False}


def handle(k):
    return 'h' +str(uuid.uuid5(uuid.UUID(MOD_UUID), 'name-' + k)).replace('-', 'g') if own_names else PK_NAME_HANDLE


w('Mods/%s/meta.lsx' % FOLDER, hair_mod.META.format(
    author='dawil', desc="PK Hair Collection's Hair 19 for the Dhaen Extended races. Load it after PK Hair Collection.",
    folder=FOLDER, name='PK Hair 19 for Dhaen', uuid=MOD_UUID, v64=hair_mod.VERSION64,
    deps='                <node id="Dependencies" />'))

w('Public/%s/CharacterCreation/CharacterCreationSharedVisuals.lsx' % FOLDER,
  '<?xml version="1.0" encoding="utf-8"?>\n<save>\n  <version major="4" minor="0" revision="9" build="328" />\n'
  '  <region id="CharacterCreationSharedVisuals">\n    <node id="root">\n      <children>\n' + ''.join(
      '        <node id="CharacterCreationSharedVisual">\n'
      '          <attribute id="DisplayName" type="TranslatedString" handle="%s" version="1" />\n'
      '          <attribute id="SlotName" type="FixedString" value="Hair" />\n'
      '          <attribute id="UUID" type="guid" value="%s" />\n'
      '          <attribute id="VisualResource" type="guid" value="%s" />\n'
      '        </node>\n' % (handle(k), VISUALS[k][0], VISUALS[k][1]) for k in keys) +
  '      </children>\n    </node>\n  </region>\n</save>\n')

races = ''.join(
    '        <node id="Race">\n'
    '          <attribute id="MergedInto" type="guid" value="%s" />\n'
    '          <attribute id="Name" type="FixedString" value="%s_%s_%d" />\n'
    '          <attribute id="UUID" type="guid" value="%s" />\n'
    '          <children>\n%s          </children>\n        </node>\n'
    % (r['into'], FOLDER, r['name'], i, uuid.uuid5(uuid.UUID(MOD_UUID), r['into'] + r['name'] + str(i)),
       ''.join('            <node id="Visuals">\n              <attribute id="Object" type="guid" value="%s" />\n'
               '            </node>\n' % VISUALS[k][0] for k in keys))
    for i, r in enumerate(DHAEN))
w('Public/%s/Races/Races.lsx' % FOLDER,
  '<?xml version="1.0" encoding="utf-8"?>\n<save>\n  <version major="4" minor="0" revision="9" build="328" />\n'
  '  <region id="Races">\n    <node id="root">\n      <children>\n' + races + '      </children>\n    </node>\n  </region>\n</save>\n')

if own_names:
    w('Localization/English/%s.xml' % FOLDER,
      '<?xml version="1.0" encoding="utf-8"?>\n<contentList>\n' + ''.join(
          '  <content contentuid="%s" version="1">%s</content>\n' % (handle(k), VISUALS[k][2]) for k in keys) +
      '</contentList>\n')

if mode in ('remap', 'final', 'ctl', 'ctl2'):
    import copy, tempfile
    import xml.etree.ElementTree as ET
    with tempfile.TemporaryDirectory() as t:
        lsf, lsx = os.path.join(t, 'pk.lsf'), os.path.join(t, 'pk.lsx')
        open(lsf, 'wb').write(Pak(os.path.join(hair_mod.MODS, 'PK_Hair_Collection.pak')).read(
            'Public/PK_Hair_Collection/Content/Assets/Characters/[PAK]_Hair/PK_Hair_Collection_Meshes.lsf'))
        hair_mod.divine('-a', 'convert-resource', '-i', 'lsf', '-o', 'lsx', '-s', lsf, '-d', lsx)
        root = ET.parse(lsx).getroot()
    body = ''
    for k in keys:
        node = next(n for n in root.iter('node') if n.get('id') == 'Resource'
                    and hair_mod.attrs(n).get('ID') == PK_IDS[k])
        res = copy.deepcopy(node)
        hair_mod.setattr_(res, 'ID', VISUALS[k][1])
        hair_mod.setattr_(res, 'Name', 'PKHair19_%s_Remap' % k.upper())
        hair_mod.setattr_(res, 'NeedsSkeletonRemap', 'True' if REMAP.get(k, True) else 'False')
        assert hair_mod.attrs(res)['SourceFile'].startswith('Generated/Public/PK_Hair_Collection/')
        if k in GR2S:
            # ship a refitted mesh (refit.py / refit_vanilla.py) instead of pointing at PK's own GR2
            fname, mesh = GR2S[k]
            stem = fname[:-4]
            rel = 'Generated/Public/%s/[PAK]_Hair/%s' % (FOLDER, fname)
            gr2 = os.path.join(HERE, 'art', 'out', fname)
            if not os.path.exists(gr2):
                raise SystemExit('missing %s (run refit.py / refit_vanilla.py first)' % gr2)
            dst = os.path.join(src, *rel.split('/'))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if not os.path.exists(dst):
                shutil.copyfile(gr2, dst)
            hair_mod.setattr_(res, 'SourceFile', rel)
            hair_mod.setattr_(res, 'Template', rel[:-4] + '.Dummy_Root.0')
            if mesh:
                for o in res.iter('node'):
                    if o.get('id') == 'Objects':
                        oid = [x for x in o.findall('attribute') if x.get('id') == 'ObjectID'][0]
                        oid.set('value', '%s.%s.0' % (stem, mesh))
        body += ET.tostring(res, encoding='unicode') + '\n'
    w('Public/%s/Content/Assets/Characters/[PAK]_Hair/_merged.lsx' % FOLDER,
      '<?xml version="1.0" encoding="utf-8"?>\n<save>\n\t<version major="4" minor="0" revision="9" build="0" lslib_meta="%s" />\n'
      '\t<region id="VisualBank">\n\t\t<node id="VisualBank">\n\t\t\t<children>\n%s'
      '\t\t\t</children>\n\t\t</node>\n\t</region>\n</save>\n' % (hair_mod.LSLIB_META, body))

stage = os.path.join(ROOT, 'build', 'stage', 'pk_hair19_dhaen')
if os.path.isdir(stage):
    shutil.rmtree(stage)
os.makedirs(os.path.dirname(stage), exist_ok=True)
shutil.copytree(src, stage)
bank = os.path.join(stage, 'Public', FOLDER, 'Content', 'Assets', 'Characters', '[PAK]_Hair', '_merged.lsx')
if os.path.exists(bank):
    hair_mod.divine('-a', 'convert-resource', '-i', 'lsx', '-o', 'lsf', '-s', bank, '-d', bank[:-4] + '.lsf')
    os.remove(bank)
xml = os.path.join(stage, 'Localization', 'English', FOLDER + '.xml')
if os.path.exists(xml):
    hair_mod.divine('-a', 'convert-loca', '-s', xml, '-d', xml[:-4] + '.loca')
    os.remove(xml)
out = os.path.join(ROOT, 'build', 'variants', '%s_%s.pak' % (FOLDER, mode))
os.makedirs(os.path.dirname(out), exist_ok=True)
hair_mod.divine('-a', 'create-package', '-s', stage, '-d', out, '-c', 'lz4')

pk = Pak(out)
print('built %s: %d files' % (out, len(pk.entries)))
for n in sorted(pk.entries):
    print('  ', n)
sv = pk.read('Public/%s/CharacterCreation/CharacterCreationSharedVisuals.lsx' % FOLDER)
assert sv.count(b'CharacterCreationSharedVisual"') == len(keys)
assert pk.read('Public/%s/Races/Races.lsx' % FOLDER).count(b'<node id="Race">') == len(DHAEN)
assert b'ModuleShortDesc' not in pk.read('Mods/%s/meta.lsx' % FOLDER)

if '--install' in sys.argv:
    dest = os.path.join(hair_mod.MODS, FOLDER + '.pak')
    if os.path.exists(dest):
        raise SystemExit('%s already installed; not replacing it.' % dest)
    shutil.copyfile(out, dest)
    print('installed', dest)
