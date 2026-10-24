"""Rebuild the game's modsettings.lsx from a BG3 Mod Manager order file.

    python tools/restore_modsettings.py              # dry run: report what would be written
    python tools/restore_modsettings.py --write      # back up the current file, then write

Why: the game only loads mods listed in PlayerProfiles/Public/modsettings.lsx. If that file is reset to the base game
(GustavX only) every mod is "uninstalled" although every .pak is still in the Mods folder.

Source of the order: BG3 Mod Manager's Orders/LastExported.json (a list of UUID + Name, in load order). For each entry
the Folder, Name and Version64 come from the mod's own installed pak (Mods/<Folder>/meta.lsx), so the entry matches what
is on disk now. An entry with no installed pak is skipped and reported, not written. Close the game first, and do not
press Export in BG3 Mod Manager until you have refreshed it (it would write its in-memory list over this file).
"""
import argparse, json, os, re, shutil, sys, time
import xml.etree.ElementTree as ET
from xml.sax.saxutils import quoteattr

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from lspk import Pak

LOCAL = os.path.join(os.environ['LOCALAPPDATA'], 'Larian Studios', "Baldur's Gate 3")
MODS = os.path.join(LOCAL, 'Mods')
PUBLIC = os.path.join(LOCAL, 'PlayerProfiles', 'Public')
CURRENT = os.path.join(PUBLIC, 'modsettings.lsx')
ORDER = os.path.join(os.path.expanduser('~'), 'Downloads', 'BG3 Mod Manager', 'Orders', 'LastExported.json')


def attrs(n):
    return {a.get('id'): a.get('value') for a in n.findall('attribute')}


def installed():
    """{uuid: dict(folder, name, version64, pak)} read from every pak's meta.lsx."""
    out = {}
    for f in sorted(os.listdir(MODS)):
        if not f.lower().endswith('.pak'):
            continue
        try:
            pk = Pak(os.path.join(MODS, f))
        except Exception:
            continue
        for n in pk.entries:
            if re.fullmatch(r'Mods/[^/]+/meta\.lsx', n):
                try:
                    root = ET.fromstring(pk.read(n).decode('utf-8-sig'))
                except Exception:
                    continue
                for m in root.iter('node'):
                    if m.get('id') == 'ModuleInfo':
                        a = attrs(m)
                        if a.get('UUID'):
                            out[a['UUID'].lower()] = dict(folder=a.get('Folder', ''), name=a.get('Name', ''),
                                                          version64=a.get('Version64', '36028797018963968'), pak=f)
    return out


def entry(folder, md5, name, uuid, v64):
    return ('            <node id="ModuleShortDesc">\n'
            '              <attribute id="Folder" type="LSString" value=%s />\n'
            '              <attribute id="MD5" type="LSString" value=%s />\n'
            '              <attribute id="Name" type="LSString" value=%s />\n'
            '              <attribute id="PublishHandle" type="uint64" value="0" />\n'
            '              <attribute id="UUID" type="guid" value=%s />\n'
            '              <attribute id="Version64" type="int64" value=%s />\n'
            '            </node>\n') % (quoteattr(folder), quoteattr(md5), quoteattr(name), quoteattr(uuid), quoteattr(v64))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true')
    ap.add_argument('--order', default=ORDER)
    ap.add_argument('--exclude', action='append', default=[], help='leave this mod out of the list (Name or UUID); repeatable')
    a = ap.parse_args()

    order = json.load(open(a.order, encoding='utf-8-sig'))['Order']
    inst = installed()
    print('order file: %s (%d entries); %d installed mods have a meta.lsx' % (a.order, len(order), len(inst)))

    # The base game's own entry. Written directly, not copied from the current file: after the game resets the list it
    # rewrites the file in its own layout (4-space indent) with placeholder MD5/Version; these are the real values that
    # BG3 Mod Manager and every earlier working modsettings.lsx carry.
    gustav = type('G', (), {'group': staticmethod(lambda i: entry('GustavX', 'ef3fcba3f3684b3088ad1f9874d4957c', 'GustavX',
                                                                  'cb555efe-2d9e-131f-8195-a89329d218ea', '145241946983300916'))})

    body, kept, missing, seen = [gustav.group(1)], 0, [], set()
    for e in order:
        u = e['UUID'].lower()
        if u in seen or u == 'cb555efe-2d9e-131f-8195-a89329d218ea':
            continue
        seen.add(u)
        m = inst.get(u)
        if any(x.lower() in (u, e['Name'].lower()) for x in a.exclude):
            print('   excluded by request:', e['Name'])
            continue
        if not m:
            missing.append(e['Name'])
            continue
        body.append(entry(m['folder'], '', m['name'], u, m['version64']))
        kept += 1
    print('will write GustavX + %d mods; skipped (no installed pak): %d' % (kept, len(missing)))
    for n in missing:
        print('   skipped:', n)
    listed = {inst[u]['pak'] for u in seen if u in inst}
    extra = sorted(m['pak'] for u, m in inst.items() if u not in seen)
    print('installed but not in the order (left inactive): %d' % len(extra))
    for p in extra:
        print('   inactive:', p)

    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<save>\n  <version major="4" minor="8" revision="0" build="100" />\n'
           '  <region id="ModuleSettings">\n    <node id="root">\n      <children>\n        <node id="Mods">\n          <children>\n'
           + ''.join(body) + '          </children>\n        </node>\n      </children>\n    </node>\n  </region>\n</save>\n')
    ET.fromstring(xml)                                  # must be well-formed
    if not a.write:
        print('dry run only; nothing written. Re-run with --write.')
        return
    bak = CURRENT + '.reset-to-gustavx-' + time.strftime('%Y%m%d-%H%M%S')
    shutil.copyfile(CURRENT, bak)
    with open(CURRENT, 'w', encoding='utf-8', newline='\n') as f:
        f.write(xml)
    print('backed up the reset file to', bak)
    print('wrote', CURRENT, '(%d bytes, %d mods)' % (os.path.getsize(CURRENT), kept))


if __name__ == '__main__':
    main()
