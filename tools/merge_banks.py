"""Combine the generated bank files into a single content bank _merged.lsx.

PATH MATTERS. The bank must live under Content/Assets/<Category>/[PAK]_<name>/, e.g.
  Public/<Mod>/Content/Assets/Characters/[PAK]_<Mod>/_merged.lsf
Vanilla does this (Content/Assets/Characters/Humans/[PAK]_Male_Armor/) and so does every
working mod that ships visuals (MadaraGunbai uses Content/Assets/Weapons/[PAK]_...).
Dropping the Assets/<Category>/ segment means the engine never scans the folder: the bank
silently does not load, the root template's visual UUIDs resolve to nothing, and the item
falls back to its ParentTemplateId's appearance -- so a robe parented to Gale's shows up
as an ordinary purple Gale robe with none of your artwork.

Vanilla ships every bank -- TextureBank, MaterialBank, VisualBank, and the rest -- as
regions inside ONE _merged.lsf per content folder. Splitting the VisualBank into its own
_visuals.lsf risks the engine never loading it, which leaves the root template pointing at
visual UUIDs that do not exist: the item equips, and the character renders with no robe.
"""
import os, re, sys

D = 'src/Public/ObitoUchihaRobe/Content/Assets/Characters/[PAK]_ObitoUchihaRobe'
MAIN = os.path.join(D, '_merged.lsx')
EXTRAS = [os.path.join(D, f) for f in ('_visuals.lsx', '_preset.lsx')]

def regions(path):
    s = open(path, encoding='utf-8').read()
    return re.findall(r'\t<region id=".*?</region>\n', s, re.S)

def main():
    extras = [e for e in EXTRAS if os.path.exists(e)]
    if not extras:
        print('nothing to merge'); return
    regs = regions(MAIN)
    for e in extras:
        regs += regions(e)
    doc = ['<?xml version="1.0" encoding="utf-8"?>', '<save>',
           '\t<version major="4" minor="0" revision="9" build="0" lslib_meta="v1,bswap_guids,lsf_adjacency" />']
    out = '\n'.join(doc) + '\n' + ''.join(regs) + '</save>\n'
    open(MAIN, 'w', encoding='utf-8', newline='\n').write(out)
    for e in extras:
        os.remove(e)
    names = re.findall(r'<region id="([^"]+)"', out)
    print('merged into %s' % MAIN)
    print('  regions: %s' % ', '.join(names))
    print('  removed %s' % ', '.join(os.path.basename(e) for e in extras))

if __name__ == '__main__':
    main()
