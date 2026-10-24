"""Asset pipeline for a custom hairstyle: unpack -> (Blender) -> gr2 -> build -> pack -> check -> install.

    python tools/hair_mod.py init    items/lloyd_hair        # fresh UUIDs, writes hair.json
    python tools/hair_mod.py unpack  items/lloyd_hair        # vanilla base hair -> extracted/hair_base/*.glb
    python tools/hair_mod.py gr2     items/lloyd_hair work/lloyd_export.glb   # retarget + Divine -> GR2
    python tools/hair_mod.py build   items/lloyd_hair        # generate the mod tree in src/
    python tools/hair_mod.py pack    items/lloyd_hair        # convert .lsx/.xml, create <Folder>.pak
    python tools/hair_mod.py check   items/lloyd_hair        # read the pak back and verify it
    python tools/hair_mod.py install items/lloyd_hair        # copy into the BG3 Mods folder

`hair.json` "mesh": null builds a CONTROL: a new selectable hair slot that reuses the vanilla base
hair's own GR2 (nothing of Larian's is shipped). Use it first to prove the registration works in
game, then set "mesh" to {"gr2": "art/out/<name>.GR2"} to ship your sculpt.

What one hair needs (learned from vanilla and from working hair mods, not from a spec):

  Mods/<Folder>/meta.lsx                       mod identity, its own UUID
  Public/<Folder>/CharacterCreation/CharacterCreationAppearanceVisuals.lsx
                                               one row per race x body type x body shape, slot "Hair"
  Public/<Folder>/Content/Assets/Characters/[PAK]_Hair/_merged.lsx -> .lsf
                                               VisualBank: the hair visual (GR2 path, per-mesh materials)
  Localization/English/<Folder>.xml -> .loca   the name shown on the tile
  Generated/Public/<Folder>/[PAK]_Hair/<stem>.GR2   only when you ship your own mesh

Materials, the scalp material and the hair preset are NOT shipped: the visual refers to the
vanilla ones by id, exactly as it does for the base hair it was cloned from.
There is no 'CharacterCreationHairStyles.lsx' in BG3; hair is a row with SlotName "Hair" in
CharacterCreationAppearanceVisuals.
"""
import argparse, copy, json, os, re, shutil, struct, subprocess, sys, tempfile, uuid
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
from lspk import Pak
from lsf import LSF

DIVINE = os.environ.get('DIVINE', os.path.join(os.environ.get('USERPROFILE', ''), 'Tools', 'LSLib', 'Tools', 'Divine.exe'))
DATA = r'C:\Program Files (x86)\Steam\steamapps\common\Baldurs Gate 3\Data'
MODS = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Larian Studios', "Baldur's Gate 3", 'Mods')
HAIR_DIR = 'Generated/Public/Shared/Assets/Characters/_Models/_Hair/Resources/'
SPRING_DIR = 'Public/Shared/Assets/Characters/_Models/_Hair/'
VANILLA_BANK = 'Public/Shared/Content/Assets/Characters/[PAK]_Hair/_merged.lsf'
LSLIB_META = 'v1,bswap_guids,lsf_adjacency'

# The five races that share the human-shaped head (vanilla gives each of them the same 64 hair rows).
RACES = {
    'Human': '0eb594cb-8820-4be6-a58d-8be7a1a98fba',
    'Elf': '6c038dcb-7eb5-431d-84f8-cecfaf1c0c5a',
    'HalfElf': '45f4ac10-3c89-4fb2-b37d-f973bb9110c0',
    'Drow': '4f5d1434-5175-4fa9-b7dc-ab24fba37929',
    'Tiefling': 'b6dccbed-30f3-424b-a181-c4540cf38197',
}
VERSION64 = 36028797018963968       # 1.0.0.0


def divine(*args):
    if not os.path.exists(DIVINE):
        raise SystemExit('Divine.exe not found at %s (set $DIVINE)' % DIVINE)
    r = subprocess.run([DIVINE, '-g', 'bg3', *args], capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip()
    if r.returncode != 0 or '[FATAL]' in out:
        raise SystemExit('Divine failed (%s):\n%s' % (' '.join(args[:2]), out[-1500:]))
    return out


def cfg_path(d):
    return os.path.join(d, 'hair.json')


def load(d):
    return json.load(open(cfg_path(d), encoding='utf-8'))


def new_handle():
    h = uuid.uuid4().hex
    return 'h%sg%sg%sg%sg%s' % (h[:8], h[8:12], h[12:16], h[16:20], h[20:])


def rowkey(race, bt, bs):
    return '%s/%d/%d' % (race, bt, bs)


# ---------------------------------------------------------------- init

def cmd_init(a):
    d = os.path.abspath(a.item)
    os.makedirs(d, exist_ok=True)
    if os.path.exists(cfg_path(d)) and not a.force:
        raise SystemExit('%s exists. Ids must never change once the hair has been played; pass --force '
                         'only for a hair nobody has loaded yet.' % cfg_path(d))
    races, bts, bss = list(RACES), [0, 1], [0, 1]
    cfg = {
        'folder': 'LloydHair',
        'name': 'Lloyd de Saloum Hair',
        'tile': 'Lloyd',
        'description': 'A short layered hairstyle with long face-framing bangs, an ahoge and a low ponytail.',
        'author': 'dawil',
        'base': 'HAIR_HUM_M_Straight_Short_H_Spring',
        'mesh': None,
        'races': {r: RACES[r] for r in races},
        'body_types': bts,
        'body_shapes': bss,
        'ids': {
            'mod': str(uuid.uuid4()),
            'visual': str(uuid.uuid4()),
            'name_handle': new_handle(),
            'rows': {rowkey(r, bt, bs): str(uuid.uuid4()) for r in races for bt in bts for bs in bss},
        },
    }
    json.dump(cfg, open(cfg_path(d), 'w', encoding='utf-8'), indent=2)
    print('wrote', cfg_path(d))
    print('  mod uuid    ', cfg['ids']['mod'])
    print('  visual uuid ', cfg['ids']['visual'])
    print('  %d character-creation rows (%d races x %d body types x %d shapes)'
          % (len(cfg['ids']['rows']), len(races), len(bts), len(bss)))


# ---------------------------------------------------------------- unpack

def base_dir():
    return os.path.join(ROOT, 'extracted', 'hair_base')


def cmd_unpack(a):
    cfg = load(os.path.abspath(a.item))
    names = [cfg['base']] + [n for n in a.extra if n != cfg['base']]
    out = base_dir()
    os.makedirs(out, exist_ok=True)
    models = Pak(os.path.join(DATA, 'Models.pak'))
    for n in names:
        # vanilla hairs do not all live in one folder (Short_M is under _Models/Humans/_Hair), so ask the bank
        own = n == cfg['base'] and cfg.get('source')          # the base may come from another mod's pak
        src = attrs(find_base(n, cfg if own else None))['SourceFile']
        pk = Pak(source_pak(cfg)) if own else models
        if src not in pk.entries:
            raise SystemExit('no hair %s in %s (looked for %s)' % (n, cfg['source']['pak'] if own else 'Models.pak', src))
        models_or = pk
        gr2 = os.path.join(out, n + '.GR2')
        open(gr2, 'wb').write(models_or.read(src))
        # explicit -e flags: with none, some GR2s fail glTF export (index out of bounds); with any flag they convert
        divine('-a', 'convert-model', '-s', gr2, '-d', os.path.join(out, n + '.glb'),
               '-e', 'export-normals', '-e', 'export-tangents', '-e', 'export-uvs')
        print('unpacked', n, '->', os.path.join(out, n + '.glb'))
        # the spring skeleton and its spring definition, when the hair has physics
        for ext in ('_Base.GR2', '.bin'):
            p = SPRING_DIR + n + ext
            if p in models.entries:
                open(os.path.join(out, n + ext), 'wb').write(models.read(p))
                print('   also', n + ext, '(spring skeleton / spring definition)')


# ---------------------------------------------------------------- gr2

def cmd_gr2(a):
    d = os.path.abspath(a.item)
    cfg = load(d)
    fitted = os.path.abspath(a.fitted)
    van = os.path.join(base_dir(), cfg['base'] + '.glb')
    if not os.path.exists(van):
        raise SystemExit('run unpack first (missing %s)' % van)
    stem = a.name or cfg['folder']
    outdir = os.path.join(d, 'art', 'out')
    os.makedirs(outdir, exist_ok=True)
    re_glb = os.path.join(outdir, stem + '_retargeted.glb')
    cmd = [sys.executable, os.path.join(HERE, 'hair_retarget.py'), van, fitted, re_glb]
    if a.lod_from_lod0:
        cmd.append('--lod-from-lod0')
    r = subprocess.run(cmd, capture_output=True, text=True)
    print((r.stdout + r.stderr).strip())
    if r.returncode:
        raise SystemExit('retarget failed')
    gr2 = os.path.join(outdir, stem + '.GR2')
    divine('-a', 'convert-model', '-s', re_glb, '-d', gr2,
           '-e', 'export-uvs', '-e', 'export-normals', '-e', 'export-tangents')
    print('wrote', gr2, '(%d bytes)' % os.path.getsize(gr2))
    print('now set "mesh": {"gr2": "art/out/%s.GR2"} in hair.json and run build' % stem)


def glb_mesh_names(path):
    raw = open(path, 'rb').read()
    pos = 12
    while pos < len(raw):
        ln, kind = struct.unpack('<II', raw[pos:pos + 8])
        if kind == 0x4E4F534A:
            g = json.loads(raw[pos + 8:pos + 8 + ln])
            return [n.get('name') or g['meshes'][n['mesh']].get('name') for n in g['nodes'] if 'mesh' in n]
        pos += 8 + ln
    return []


# ---------------------------------------------------------------- vanilla bank

def vanilla_bank():
    """The vanilla hair VisualBank as LSX (extracted from Shared.pak once, cached in extracted/)."""
    d = os.path.join(ROOT, 'extracted', 'vanilla_hair')
    os.makedirs(d, exist_ok=True)
    lsx = os.path.join(d, 'hair_merged.lsx')
    if not os.path.exists(lsx):
        lsf = os.path.join(d, 'hair_merged.lsf')
        open(lsf, 'wb').write(Pak(os.path.join(DATA, 'Shared.pak')).read(VANILLA_BANK))
        divine('-a', 'convert-resource', '-i', 'lsf', '-o', 'lsx', '-s', lsf, '-d', lsx)
    return lsx


def attrs(n):
    return {a.get('id'): (a.get('value') if a.get('value') is not None else a.get('handle')) for a in n.findall('attribute')}


def source_pak(cfg):
    return os.path.join(MODS, cfg['source']['pak'])


def find_base(base, cfg=None):
    """The VisualBank resource to clone: from another mod's pak when hair.json has a "source", else vanilla."""
    if cfg and cfg.get('source'):
        s = cfg['source']
        root = ET.fromstring(Pak(source_pak(cfg)).read(s['bank']).decode('utf-8-sig'))
    else:
        root = ET.parse(vanilla_bank()).getroot()
    for reg in root.iter('region'):
        if reg.get('id') != 'VisualBank':
            continue
        for n in reg.iter('node'):
            if n.get('id') == 'Resource':
                at = attrs(n)
                if at.get('Name') == base and at.get('SourceFile', '').endswith('.GR2'):
                    return n
    raise SystemExit('base hair %s not found in the vanilla VisualBank' % base)


def setattr_(node, key, value):
    for a in node.findall('attribute'):
        if a.get('id') == key:
            a.set('value', value)
            return
    raise KeyError(key)


# ---------------------------------------------------------------- build

META = '''<?xml version="1.0" encoding="UTF-8"?>
<save>
    <version major="4" minor="0" revision="9" build="331" />
    <region id="Config">
        <node id="root">
            <children>
{deps}
                <node id="ModuleInfo">
                    <attribute id="Author" type="LSString" value="{author}" />
                    <attribute id="CharacterCreationLevelName" type="FixedString" value="" />
                    <attribute id="Description" type="LSString" value="{desc}" />
                    <attribute id="Folder" type="LSString" value="{folder}" />
                    <attribute id="GMTemplate" type="FixedString" value="" />
                    <attribute id="LobbyLevelName" type="FixedString" value="" />
                    <attribute id="MD5" type="LSString" value="" />
                    <attribute id="MainMenuBackgroundVideo" type="FixedString" value="" />
                    <attribute id="MenuLevelName" type="FixedString" value="" />
                    <attribute id="Name" type="LSString" value="{name}" />
                    <attribute id="NumPlayers" type="uint8" value="4" />
                    <attribute id="PhotoBooth" type="FixedString" value="" />
                    <attribute id="StartupLevelName" type="FixedString" value="" />
                    <attribute id="Tags" type="LSString" value="" />
                    <attribute id="Type" type="FixedString" value="Add-on" />
                    <attribute id="UUID" type="FixedString" value="{uuid}" />
                    <attribute id="Version64" type="int64" value="{v64}" />
                    <children>
                        <node id="PublishVersion">
                            <attribute id="Version64" type="int64" value="{v64}" />
                        </node>
                        <node id="Scripts" />
                        <node id="TargetModes">
                            <children>
                                <node id="Target">
                                    <attribute id="Object" type="FixedString" value="Story" />
                                </node>
                            </children>
                        </node>
                    </children>
                </node>
            </children>
        </node>
    </region>
</save>
'''

CCAV_ROW = '''                <node id="CharacterCreationAppearanceVisual">
                    <attribute id="BodyShape" type="uint8" value="{bs}" />
                    <attribute id="BodyType" type="uint8" value="{bt}" />
                    <attribute id="DisplayName" type="TranslatedString" handle="{handle}" version="1" />
                    <attribute id="RaceUUID" type="guid" value="{race}" />
                    <attribute id="SlotName" type="FixedString" value="Hair" />
                    <attribute id="UUID" type="guid" value="{uuid}" />
                    <attribute id="VisualResource" type="guid" value="{visual}" />
                </node>
'''


def src_dir(d):
    return os.path.join(d, 'src')


def cmd_build(a):
    d = os.path.abspath(a.item)
    cfg = load(d)
    if getattr(a, 'no_deps', False):
        cfg = dict(cfg, requires=[])
        print('NO-DEPS build: Dependencies block omitted, Dhaen files kept')
    if getattr(a, 'minimal', False):
        # staged bisect: only CharacterCreationAppearanceVisuals rows + bank + loca + GR2, the structure the game accepted for Lloyd
        cfg = dict(cfg, requires=[], dhaen=None)
        print('MINIMAL build: no Dependencies block, no Dhaen shared visual / race merges')
    ids, folder = cfg['ids'], cfg['folder']
    src = src_dir(d)
    if os.path.isdir(src):
        shutil.rmtree(src)

    def w(rel, text, enc='utf-8'):
        p = os.path.join(src, *rel.split('/'))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'w', encoding=enc, newline='\n') as f:
            f.write(text)

    # meta. "requires" lists mods whose resources the visual refers to by id (materials, scalp material, preset):
    # without them the hair has no material. Declaring them also puts them ahead of this mod in the load order.
    deps = '                <node id="Dependencies" />'
    if cfg.get('requires'):
        deps = ('                <node id="Dependencies">\n                    <children>\n' + ''.join(
            '                        <node id="ModuleShortDesc">\n'
            '                            <attribute id="Folder" type="LSString" value="%s" />\n'
            '                            <attribute id="MD5" type="LSString" value="" />\n'
            '                            <attribute id="Name" type="LSString" value="%s" />\n'
            '                            <attribute id="PublishHandle" type="uint64" value="0" />\n'
            '                            <attribute id="UUID" type="guid" value="%s" />\n'
            '                            <attribute id="Version64" type="int64" value="%d" />\n'
            '                        </node>\n' % (escape(r['folder']), escape(r['name']), r['uuid'], r['version64'])
            for r in cfg['requires']) + '                    </children>\n                </node>')
    w('Mods/%s/meta.lsx' % folder, META.format(
        author=escape(cfg['author']), desc=escape(cfg['description']), folder=folder,
        name=escape(cfg['name']), uuid=ids['mod'], v64=VERSION64, deps=deps))

    # VisualBank: clone the source entry, new id
    res = copy.deepcopy(find_base(cfg['base'], cfg))
    setattr_(res, 'ID', ids['visual'])
    mesh = cfg.get('mesh')
    old_stem = os.path.splitext(os.path.basename(attrs(res)['SourceFile']))[0]
    if mesh:
        gr2 = os.path.join(d, mesh['gr2']) if not os.path.isabs(mesh['gr2']) else mesh['gr2']
        if not os.path.exists(gr2):
            raise SystemExit('mesh GR2 not found: %s' % gr2)
        stem = mesh.get('stem') or folder
        rel = 'Generated/Public/%s/[PAK]_Hair/%s.GR2' % (folder, stem)
        os.makedirs(os.path.dirname(os.path.join(src, *rel.split('/'))), exist_ok=True)
        shutil.copyfile(gr2, os.path.join(src, *rel.split('/')))
        setattr_(res, 'Name', cfg.get('visual_name', 'LLOYD_HAIR'))
        setattr_(res, 'SourceFile', rel)
        setattr_(res, 'Template', '%s.Dummy_Root.0' % rel[:-4])
        for o in res.iter('node'):
            if o.get('id') == 'Objects':
                oid = [x for x in o.findall('attribute') if x.get('id') == 'ObjectID'][0]
                oid.set('value', stem + oid.get('value')[len(old_stem):])
        # the meshes named in the bank must be the meshes in the GR2
        with tempfile.TemporaryDirectory() as t:
            tmp = os.path.join(t, 'x.glb')
            divine('-a', 'convert-model', '-s', gr2, '-d', tmp)
            have = set(glb_mesh_names(tmp))
        want = {o.findall("attribute[@id='ObjectID']")[0].get('value').split('.')[1]
                for o in res.iter('node') if o.get('id') == 'Objects'}
        if want - have:
            raise SystemExit('the GR2 lacks meshes the VisualBank names: %s (it has %s). Keep the vanilla '
                             'mesh names when sculpting.' % (sorted(want - have), sorted(have)))
        print('mesh: shipping %s (%s)' % (rel, ', '.join(sorted(have))))
    else:
        setattr_(res, 'Name', cfg.get('visual_name', 'LLOYD_HAIR') + '_CONTROL')
        print('mesh: CONTROL, reusing vanilla %s' % attrs(res)['SourceFile'])

    body = ET.tostring(res, encoding='unicode')
    bank = ('<?xml version="1.0" encoding="utf-8"?>\n<save>\n'
            '\t<version major="4" minor="0" revision="9" build="0" lslib_meta="%s" />\n'
            '\t<region id="VisualBank">\n\t\t<node id="VisualBank">\n\t\t\t<children>\n%s\n'
            '\t\t\t</children>\n\t\t</node>\n\t</region>\n</save>\n' % (LSLIB_META, body))
    w('Public/%s/Content/Assets/Characters/[PAK]_Hair/_merged.lsx' % folder, bank)

    # CharacterCreationAppearanceVisuals
    rows = []
    for r, rid in cfg['races'].items():
        for bt in cfg['body_types']:
            for bs in cfg['body_shapes']:
                rows.append(CCAV_ROW.format(bs=bs, bt=bt, handle=ids['name_handle'], race=rid,
                                            uuid=ids['rows'][rowkey(r, bt, bs)], visual=ids['visual']))
    w('Public/%s/CharacterCreation/CharacterCreationAppearanceVisuals.lsx' % folder,
      '<?xml version="1.0" encoding="UTF-8"?>\n<save>\n    <version major="4" minor="0" revision="9" build="331" />\n'
      '    <region id="CharacterCreationAppearanceVisuals">\n        <node id="root">\n            <children>\n'
      + ''.join(rows) + '            </children>\n        </node>\n    </region>\n</save>\n')

    # Dhaen Extended races get hair through SHARED visuals plus race entries that MERGE into the real race
    # (MergedInto): additive, the race's own hair list is kept. Same mechanism as Dhaen_Hair-Merged.
    dh = cfg.get('dhaen')
    if dh:
        sv = dh['shared_visual']
        w('Public/%s/CharacterCreation/CharacterCreationSharedVisuals.lsx' % folder,
          '<?xml version="1.0" encoding="utf-8"?>\n<save>\n  <version major="4" minor="0" revision="9" build="328" />\n'
          '  <region id="CharacterCreationSharedVisuals">\n    <node id="root">\n      <children>\n'
          '        <node id="CharacterCreationSharedVisual">\n'
          '          <attribute id="DisplayName" type="TranslatedString" handle="%s" version="1" />\n'
          '          <attribute id="SlotName" type="FixedString" value="Hair" />\n'
          '          <attribute id="UUID" type="guid" value="%s" />\n'
          '          <attribute id="VisualResource" type="guid" value="%s" />\n'
          '        </node>\n      </children>\n    </node>\n  </region>\n</save>\n' % (ids['name_handle'], sv, ids['visual']))
        races = ''.join(
            '        <node id="Race">\n'
            '          <attribute id="MergedInto" type="guid" value="%s" />\n'
            '          <attribute id="Name" type="FixedString" value="%s_%s_%d" />\n'
            '          <attribute id="UUID" type="guid" value="%s" />\n'
            '          <children>\n            <node id="Visuals">\n              <attribute id="Object" type="guid" value="%s" />\n'
            '            </node>\n          </children>\n        </node>\n' % (r['into'], folder, r['name'], i, r['uuid'], sv)
            for i, r in enumerate(dh['races']))
        w('Public/%s/Races/Races.lsx' % folder,
          '<?xml version="1.0" encoding="utf-8"?>\n<save>\n  <version major="4" minor="0" revision="9" build="328" />\n'
          '  <region id="Races">\n    <node id="root">\n      <children>\n' + races +
          '      </children>\n    </node>\n  </region>\n</save>\n')
        print('dhaen: 1 shared visual, %d race merges' % len(dh['races']))

    # localisation
    w('Localization/English/%s.xml' % folder,
      '<?xml version="1.0" encoding="utf-8"?>\n<contentList>\n  <content contentuid="%s" version="1">%s</content>\n</contentList>\n'
      % (ids['name_handle'], escape(cfg['tile'])))
    print('built', src, '(%d character-creation rows)' % len(rows))


# ---------------------------------------------------------------- pack / check / install

def pak_path(d, cfg):
    return os.path.join(ROOT, cfg['folder'] + '.pak')


def cmd_pack(a):
    d = os.path.abspath(a.item)
    cfg = load(d)
    src = src_dir(d)
    if not os.path.isdir(src):
        raise SystemExit('run build first')
    stage = os.path.join(ROOT, 'build', 'stage', os.path.basename(d))
    if os.path.isdir(stage):
        shutil.rmtree(stage)
    os.makedirs(os.path.dirname(stage), exist_ok=True)
    shutil.copytree(src, stage)
    for dp, _, fs in os.walk(stage):
        for f in fs:
            p = os.path.join(dp, f)
            rel = os.path.relpath(p, stage).replace('\\', '/')
            if f.endswith('.lsx') and '/Content/' in '/' + rel:        # banks -> LSF. meta.lsx and the CC table stay XML
                divine('-a', 'convert-resource', '-i', 'lsx', '-o', 'lsf', '-s', p, '-d', p[:-4] + '.lsf')
                os.remove(p)
                print('  convert ', rel)
            elif f.endswith('.xml') and rel.startswith('Localization/'):
                divine('-a', 'convert-loca', '-s', p, '-d', p[:-4] + '.loca')
                os.remove(p)
                print('  localize', rel)
    out = pak_path(d, cfg)
    divine('-a', 'create-package', '-s', stage, '-d', out, '-c', 'lz4')
    print('built %s (%d bytes)' % (out, os.path.getsize(out)))


def cmd_check(a):
    d = os.path.abspath(a.item)
    cfg = load(d)
    ids, folder = cfg['ids'], cfg['folder']
    p = pak_path(d, cfg)
    pk = Pak(p)
    names = list(pk.entries)
    bad = []
    need = ['Mods/%s/meta.lsx' % folder,
            'Public/%s/CharacterCreation/CharacterCreationAppearanceVisuals.lsx' % folder,
            'Public/%s/Content/Assets/Characters/[PAK]_Hair/_merged.lsf' % folder,
            'Localization/English/%s.loca' % folder]
    for n in need:
        if n not in pk.entries:
            bad.append('missing ' + n)
    for n in names:
        if n.endswith(('.lsx', '.xml')) and '/Content/' in n or n.startswith('Localization/') and n.endswith('.xml'):
            bad.append('unconverted source shipped: ' + n)
    if not bad:
        f = LSF(pk.read(need[2]))
        found = None
        for i in range(len(f.nodes)):
            at = f.node_attrs(i)
            if str(at.get('ID', ('', ''))[1]) == ids['visual']:
                found = {k: v[1] for k, v in at.items()}
        if not found:
            bad.append('visual %s not in the packed bank (GUID byte order?)' % ids['visual'])
        else:
            print('visual in bank:', found.get('Name'), '|', found.get('SourceFile'))
            sf = found.get('SourceFile', '')
            if cfg.get('mesh') and sf not in pk.entries:
                bad.append('bank points at %s but the pak does not contain it' % sf)
        ccav = pk.read(need[1]).decode('utf-8')
        if ids['visual'] not in ccav or ids['name_handle'] not in ccav:
            bad.append('character creation rows do not reference the visual / name handle')
        n_rows = ccav.count('<node id="CharacterCreationAppearanceVisual">')
        print('%d character-creation rows, mod uuid %s' % (n_rows, ids['mod']))
    print('%d files in %s' % (len(names), os.path.basename(p)))
    for b in bad:
        print('PROBLEM', b)
    if bad:
        raise SystemExit(1)
    print('CHECK OK (structure only; whether the hair renders can only be told in game)')


def cmd_install(a):
    d = os.path.abspath(a.item)
    cfg = load(d)
    p = pak_path(d, cfg)
    dest = os.path.join(MODS, os.path.basename(p))
    if os.path.exists(dest) and not a.overwrite:
        raise SystemExit('%s is already installed. Not replacing it without --overwrite '
                         '(and close BG3 first: a running game locks the pak).' % dest)
    os.makedirs(MODS, exist_ok=True)
    shutil.copyfile(p, dest)
    print('installed', dest)
    print('Enable "%s" in BG3 Mod Manager, then look for "%s" under Hair in character creation.'
          % (cfg['name'], cfg['tile']))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    for name, fn in (('init', cmd_init), ('unpack', cmd_unpack), ('gr2', cmd_gr2), ('build', cmd_build),
                     ('pack', cmd_pack), ('check', cmd_check), ('install', cmd_install)):
        p = sub.add_parser(name)
        p.add_argument('item', help='item folder, e.g. items/lloyd_hair')
        p.set_defaults(fn=fn)
        if name == 'build':
            p.add_argument('--minimal', action='store_true', help='omit the dependency block and the Dhaen race files')
            p.add_argument('--no-deps', action='store_true', help='omit only the dependency block')
        if name == 'init':
            p.add_argument('--force', action='store_true')
        if name == 'unpack':
            p.add_argument('extra', nargs='*', help='more vanilla hair names to unpack for reference')
        if name == 'gr2':
            p.add_argument('fitted', help='glb exported by tools/hair_blender.py')
            p.add_argument('--name', help='output GR2 stem (default: the mod folder name)')
            p.add_argument('--lod-from-lod0', action='store_true')
        if name == 'install':
            p.add_argument('--overwrite', action='store_true')
    a = ap.parse_args()
    a.fn(a)


if __name__ == '__main__':
    main()
