"""Emit a MaterialPresetBank holding an all-white colour preset.

Why this exists: the item sets ParentTemplateId to Gale's robe, so it INHERITS his
Equipment -- including VisualSet > MaterialOverrides > MaterialPresets, which applies the
preset "ARM_Robe_A_Purple_2" with ForcePresetValues=True. That preset writes every slot in
the "02 Colour" group and overrides whatever the material itself declares.

That is why neutralising the material's own slot values changed nothing: the inherited
preset was winning. The white half of the crest kept rendering orange because it was being
multiplied by an inherited tan slot.

The fix is to override the inherited preset with one of our own whose every slot is white,
so base x 1 = base and the texture renders exactly as painted.

Cloned from Gale's preset so the parameter list and flags match vanilla exactly; only the
values are replaced.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lspk import Pak
from lsf import LSF

DATA = r"C:\Program Files (x86)\Steam\steamapps\common\Baldurs Gate 3\Data"
SRC_PRESET = 'fb21807c-fb57-194d-e7c8-848b37a4fb24'          # ARM_Robe_A_Purple_2
OUT = 'src/Public/ObitoUchihaRobe/Content/Assets/Characters/[PAK]_ObitoUchihaRobe/_preset.lsx'
PRESET_ID = 'cd56b336-e7de-4c94-afba-40776b39e153'
PRESET_NAME = 'ObitoUchihaRobe_Neutral'

def main():
    p = Pak(os.path.join(DATA, 'Shared.pak'))
    f = LSF(p.read('Public/Shared/Content/Assets/Characters/[PAK]_Character_Presets/_merged.lsf'))
    kids = {}
    for i, (ni, fa, par) in enumerate(f.nodes):
        kids.setdefault(par, []).append(i)
    src = None
    for i in range(len(f.nodes)):
        if str(f.node_attrs(i).get('ID', ('', ''))[1]) == SRC_PRESET:
            src = i; break
    if src is None:
        raise SystemExit('source preset not found')
    presets = [c for c in kids.get(src, []) if f.node_name(c) == 'Presets'][0]

    rows = ['\t\t\t\t<node id="Resource">',
            '\t\t\t\t\t<attribute id="ID" type="FixedString" value="%s" />' % PRESET_ID,
            '\t\t\t\t\t<attribute id="Name" type="LSString" value="%s" />' % PRESET_NAME,
            '\t\t\t\t\t<children>',
            '\t\t\t\t\t\t<node id="Presets">',
            '\t\t\t\t\t\t\t<attribute id="MaterialResource" type="FixedString" value="" />',
            '\t\t\t\t\t\t\t<children>']
    n = 0
    for c in kids.get(presets, []):
        nm = f.node_name(c)
        a = f.node_attrs(c)
        if nm != 'Vector3Parameters':
            continue
        rows += ['\t\t\t\t\t\t\t\t<node id="Vector3Parameters">',
                 '\t\t\t\t\t\t\t\t\t<attribute id="Parameter" type="FixedString" value="%s" />' % a['Parameter'][1],
                 '\t\t\t\t\t\t\t\t\t<attribute id="Value" type="fvec3" value="1 1 1" />',
                 '\t\t\t\t\t\t\t\t\t<attribute id="Color" type="bool" value="%s" />' % ('True' if a['Color'][1] else 'False'),
                 '\t\t\t\t\t\t\t\t\t<attribute id="Custom" type="bool" value="%s" />' % ('True' if a['Custom'][1] else 'False'),
                 '\t\t\t\t\t\t\t\t\t<attribute id="Enabled" type="bool" value="True" />',
                 '\t\t\t\t\t\t\t\t</node>']
        n += 1
    rows += ['\t\t\t\t\t\t\t</children>', '\t\t\t\t\t\t</node>',
             '\t\t\t\t\t</children>', '\t\t\t\t</node>']

    doc = ['<?xml version="1.0" encoding="utf-8"?>', '<save>',
           '\t<version major="4" minor="0" revision="9" build="0" lslib_meta="v1,bswap_guids,lsf_adjacency" />',
           '\t<region id="MaterialPresetBank">', '\t\t<node id="MaterialPresetBank">', '\t\t\t<children>']
    doc += rows
    doc += ['\t\t\t</children>', '\t\t</node>', '\t</region>', '</save>']
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, 'w', encoding='utf-8', newline='\n').write('\n'.join(doc) + '\n')
    print('wrote %s  (%d slots, all white)' % (OUT, n))

if __name__ == '__main__':
    main()
