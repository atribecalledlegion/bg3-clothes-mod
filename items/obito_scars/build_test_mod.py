"""Pack a head-texture build into a small test mod: ObitoScars<Tag>.pak.

  python items/obito_scars/build_test_mod.py                     # marker build, head A, mode 'redefine'
  python items/obito_scars/build_test_mod.py --tag scars         # the real scars (once the marker test has set the flags)
  python items/obito_scars/build_test_mod.py --install           # also copy into the BG3 Mods folder
  python items/obito_scars/build_test_mod.py --mode path         # v1: DDS at the vanilla path, no bank

Two ways to get the art in front of the game's head material:

  redefine (default)  The pak defines the head's texture resources (a TextureBank) with the SAME
                      resource IDs as vanilla but pointing at DDS files under Public/<Mod>/. The
                      material keeps referencing those IDs, so it loads ours. This is the pattern
                      installed mods use (e.g. unique_tav redirects vanilla materials) and the one
                      this repo's items use. If two mods redefine the same ID, load order decides.
  path                Only the DDS files, at the vanilla path. Relies on the game preferring a mod's
                      file over Textures.pak at the same path; not how installed mods do it.

Either way it replaces that head's maps for EVERY character using the head (NPCs included) and adds
nothing to character creation. Marker and scars paks use different folders and UUIDs; enable only
ONE at a time. Same Divine settings as build.ps1 (convert-resource for the bank, create-package, lz4).
"""
import os, sys, uuid, shutil, argparse, subprocess
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.path.insert(0, os.path.join(HERE, 'art'))
from lspk import Pak
from lsf import LSF
import item as itemlib
import headmesh as hm

DIVINE = os.environ.get('DIVINE', os.path.join(os.environ.get('USERPROFILE', ''), 'Tools', 'LSLib', 'Tools', 'Divine.exe'))
MODS = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Larian Studios', "Baldur's Gate 3", 'Mods')
TEX = 'Generated/Public/Shared/Assets/Characters/_Models/Humans/HUM_M_NKD/%s/Resources/'
V64 = 36028797018963968                                  # 1.0.0.0

META = '''<?xml version="1.0" encoding="UTF-8"?>
<save>
    <version major="4" minor="0" revision="9" build="331" />
    <region id="Config">
        <node id="root">
            <children>
                <node id="Dependencies" />
                <node id="ModuleInfo">
                    <attribute id="Author" type="LSString" value="dawil" />
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


BANK_HEAD = ('<?xml version="1.0" encoding="utf-8"?>\n<save>\n'
             '\t<version major="4" minor="0" revision="9" build="0" lslib_meta="v1,bswap_guids,lsf_adjacency" />\n'
             '\t<region id="TextureBank">\n\t\t<node id="TextureBank">\n\t\t\t<children>\n')
BANK_TAIL = '\t\t\t</children>\n\t\t</node>\n\t</region>\n</save>\n'


def vanilla_textures(i, files):
    """The vanilla TextureBank resources for these DDS files: name -> attribute dict."""
    bank = 'Public/Shared/Content/Assets/Characters/Humans/Heads/[PAK]_%s/_merged.lsf' % (
        'HUM_M_Oscar' if i['head'] == 'Oscar' else 'HUM_M_Head_' + i['head'])
    L = LSF(Pak(os.path.join(itemlib.DATA, 'Shared.pak')).read(bank))
    want = {os.path.splitext(f)[0]: f for f in files}
    found = {}
    for n in range(len(L.nodes)):
        if L.node_name(n) != 'Resource':
            continue
        a = {k: v[1] for k, v in L.node_attrs(n).items()}
        if str(a.get('Name')) in want and str(a.get('SourceFile', '')).upper().endswith('.DDS'):
            found[str(a['Name'])] = a
    missing = set(want) - set(found)
    if missing:
        raise SystemExit('no vanilla TextureBank entry for %s in %s' % (sorted(missing), bank))
    return found


def bank_lsx(res, folder):
    def attr(k, t, v):
        return '\t\t\t\t\t<attribute id="%s" type="%s" value="%s" />\n' % (k, t, v)
    b = lambda v: 'True' if v else 'False'
    out = BANK_HEAD
    for name, a in sorted(res.items()):
        out += '\t\t\t\t<node id="Resource">\n'
        out += attr('ID', 'FixedString', a['ID']) + attr('Name', 'LSString', a['Name'])
        out += attr('SourceFile', 'LSString', 'Public/%s/Assets/Textures/%s.DDS' % (folder, name))
        out += attr('Template', 'FixedString', a.get('Template', name))
        out += attr('Width', 'int32', a['Width']) + attr('Height', 'int32', a['Height'])
        out += attr('Depth', 'int32', a.get('Depth', 1)) + attr('Type', 'int32', a.get('Type', 1))
        out += attr('SRGB', 'bool', b(a.get('SRGB', False))) + attr('Streaming', 'bool', b(a.get('Streaming', True)))
        out += attr('Localized', 'bool', b(a.get('Localized', False)))
        out += '\t\t\t\t</node>\n'
    return out + BANK_TAIL


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--head', default='A', choices=hm.HEADS)
    ap.add_argument('--tag', default='marker', help='which art build to pack: out/head_<x>/build_<tag>/ (default: marker)')
    ap.add_argument('--mode', choices=('redefine', 'path'), default='redefine', help='see the docstring (default: redefine)')
    ap.add_argument('--install', action='store_true', help='copy the pak into the BG3 Mods folder')
    a = ap.parse_args()

    i = hm.info(a.head)
    src = os.path.join(i['out'], 'build_' + a.tag, 'dds')
    if not os.path.isdir(src) or not os.listdir(src):
        raise SystemExit('no DDS files in %s -- run art/composite_head.py first' % src)
    if not os.path.exists(DIVINE):
        raise SystemExit('Divine.exe not found at %s (set $DIVINE)' % DIVINE)

    folder = 'ObitoScars' + a.tag.capitalize() + ('' if a.head == 'A' else 'Head' + a.head)
    mod_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, 'obito-scars-test.%s.%s' % (a.head.lower(), a.tag)))
    what = 'Marker test' if a.tag == 'marker' else 'Scars'
    desc = ('TEST ONLY. Replaces the normal map%s of human male Head %s (character creation: "Head 1") for every '
            'character using it. Enable only one Obito Scars test mod at a time.'
            % (' and a skin-data map' if a.tag == 'marker' else '', a.head))

    stage = os.path.join(ROOT, 'build', 'stage', 'obito_scars_' + a.tag + '_' + a.head.lower())
    if os.path.exists(stage):
        shutil.rmtree(stage)
    os.makedirs(os.path.join(stage, 'Mods', folder))
    files = sorted(os.listdir(src))
    if a.mode == 'path':
        tex_dst = os.path.join(stage, *(TEX % i['tex_dir']).strip('/').split('/'))
    else:
        tex_dst = os.path.join(stage, 'Public', folder, 'Assets', 'Textures')
    os.makedirs(tex_dst)
    for f in files:
        shutil.copy2(os.path.join(src, f), os.path.join(tex_dst, f))
    res = {}
    if a.mode == 'redefine':
        res = vanilla_textures(i, files)
        content = os.path.join(stage, 'Public', folder, 'Content', 'Assets', 'Characters', '[PAK]_' + folder)
        os.makedirs(content)
        lsx, lsf = os.path.join(content, '_merged.lsx'), os.path.join(content, '_merged.lsf')
        open(lsx, 'w', encoding='utf-8', newline='\n').write(bank_lsx(res, folder))
        subprocess.run([DIVINE, '-g', 'bg3', '-a', 'convert-resource', '-i', 'lsx', '-o', 'lsf', '-s', lsx, '-d', lsf, '-l', 'warn'], check=True)
        os.remove(lsx)                                     # the game reads .lsf; don't ship both
    q = {'"': '&quot;'}
    meta = META.format(desc=escape(desc, q), folder=folder, name=escape('Obito Scars: %s (Head %s)' % (what, a.head), q),
                       uuid=mod_uuid, v64=V64)
    ET.fromstring(meta)                                    # must be well-formed XML
    open(os.path.join(stage, 'Mods', folder, 'meta.lsx'), 'w', encoding='utf-8', newline='\n').write(meta)

    pak = os.path.join(ROOT, folder + '.pak')
    if os.path.exists(pak):
        os.remove(pak)
    subprocess.run([DIVINE, '-g', 'bg3', '-a', 'create-package', '-s', stage, '-d', pak, '-c', 'lz4', '-l', 'warn'], check=True)

    # ---- verify: read the pak back and compare every file to its source
    p = Pak(pak)
    print('built %s (%s bytes), mod UUID %s' % (pak, format(os.path.getsize(pak), ','), mod_uuid))
    ok = True
    for n in sorted(p.entries):
        data = p.read(n)
        if n.lower().endswith('.dds'):
            same = data == open(os.path.join(src, os.path.basename(n)), 'rb').read()
            ok &= same
            print('  %-110s %s' % (n, 'identical to art build' if same else 'MISMATCH'))
        else:
            print('  %-110s %d bytes' % (n, len(data)))
    if 'Mods/%s/meta.lsx' % folder not in p.entries:
        ok = False
        print('  MISSING meta.lsx')
    if a.mode == 'path':
        want = (TEX % i['tex_dir']) + i['stem'] + '_NM.DDS'
        if want not in p.entries:
            ok = False
            print('  MISSING expected path', want)
    else:
        bank = 'Public/%s/Content/Assets/Characters/[PAK]_%s/_merged.lsf' % (folder, folder)
        if bank not in p.entries:
            ok = False
            print('  MISSING', bank)
        else:
            L = LSF(p.read(bank)); got = {}
            for n in range(len(L.nodes)):
                if L.node_name(n) == 'Resource':
                    at = {k: v[1] for k, v in L.node_attrs(n).items()}
                    got[str(at['Name'])] = (str(at['ID']), str(at['SourceFile']))
            for name, at in res.items():
                gid, gsf = got.get(name, (None, None))
                good = gid == str(at['ID']) and gsf in p.entries
                ok &= good
                print('  bank: %-26s id %s (vanilla %s) -> %s  %s' % (
                    name, (gid or '?')[:8], str(at['ID'])[:8], gsf, 'OK' if good else 'BAD'))
    if not ok:
        raise SystemExit('pak verification failed')

    if a.install:
        os.makedirs(MODS, exist_ok=True)
        shutil.copy2(pak, MODS)
        print('installed to', MODS)
    else:
        print('not installed. Re-run with --install, or copy the pak into:\n  ' + MODS)


if __name__ == '__main__':
    main()
