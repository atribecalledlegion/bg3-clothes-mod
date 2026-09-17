"""Generate the mod's Content bank (_merged.lsx): texture + material resources.

Rather than hand-writing the XML, this clones the vanilla robe body material out of the
shipped banks -- keeping every ScalarParameter and the whole "02 Colour" slot set exactly
as Larian tuned them -- and rewires it:

  * SourceFile  CHAR_BASE_VertCut_VT.lsf  ->  CHAR_BASE_VertCut.lsf
    The _VT shader reads base/normal/physical out of a virtual tile set, which modders
    cannot easily rebuild. The non-VT sibling takes ordinary DDS inputs and is already
    used by real armour in the same bank, so this is a supported path, not a hack.
  * texture inputs wired to our own DDS. The non-VT shader's parameter names were read
    off a vanilla material that uses it (HUM_M_ARM_ChainShirt_A_0_Pants):
        basecolor / normalmap / physicalmap / MSKColor,  MaterialType 48.

All four texture inputs are wired. The robe's vanilla NM/PM are still inside the virtual
texture, so neutral stand-ins are used (art/make_neutral_maps.sh) -- flat normal, and a
physical map averaged from the padded garment worn under this robe. Leaving a shader input
off is a plausible cause of a material failing to render at all, so flat-but-present beats
absent. Swap in the extracted originals when the VT is unpacked.

Usage:  python tools/make_content_bank.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lsf import LSF

OUT = 'src/Public/ObitoUchihaRobe/Content/Assets/Characters/[PAK]_ObitoUchihaRobe/_merged.lsx'
ASSET = 'Public/ObitoUchihaRobe/Assets/Textures/Armor'
SHADER = 'Public/Shared/Assets/Materials/Characters/CHAR_BASE_VertCut.lsf'

# Shared by both materials: neutral stand-ins, so one copy of each is enough.
NEUTRAL = [
    ('005657b1-e9ae-40ce-ae86-afcc8b972030', 'ObitoUchihaRobe_NM', 'ObitoUchihaRobe_NM.DDS', 'normalmap'),
    ('9effe3e4-73cd-49c4-8ec0-a9fff850077a', 'ObitoUchihaRobe_PM', 'ObitoUchihaRobe_PM.DDS', 'physicalmap'),
]

SETS = [
    dict(tag='masculine',
         bank='art/source/mesh/HUM_M_Armor.lsf',
         vanilla_material='HUM_M_ARM_Robe_A_Body',
         material_id='8b0f3491-d048-4989-82ef-afde63bdac5e',
         material_name='ObitoUchihaRobe_M_Body',
         bm=('cf9179e0-a4e7-42ea-9c17-aa494d87bb5d', 'ObitoUchihaRobe_M_BM',
             'HUM_M_ARM_Robe_A_BM.DDS'),
         msk=('546f4b98-8505-4881-b7ce-dd66e32230c2', 'ObitoUchihaRobe_M_MSKcloth',
              'HUM_M_ARM_Robe_A_MSKcloth.DDS')),
    dict(tag='feminine',
         bank='art/source/mesh/HUM_F_Armor.lsf',
         vanilla_material='HUM_F_ARM_Robe_A_Body',
         material_id='5d271dbf-18a4-430d-b896-2a33532e9148',
         material_name='ObitoUchihaRobe_F_Body',
         bm=('ebe9b789-816e-492b-bbdc-d5b1fbb3b080', 'ObitoUchihaRobe_F_BM',
             'HUM_F_ARM_Robe_A_Body_BM.DDS'),
         msk=('4fbfa1c0-c50f-42dc-a89a-4d55add8ca3c', 'ObitoUchihaRobe_F_MSKcloth',
              'HUM_F_ARM_Robe_A_Body_MSKcloth.DDS')),
]

def esc(s):
    return (str(s).replace('&', '&amp;').replace('<', '&lt;')
            .replace('>', '&gt;').replace('"', '&quot;'))

def attr(i, t, v, d=5):
    return '%s<attribute id="%s" type="%s" value="%s" />' % ('\t'*d, i, t, esc(v))

def find_material(lsf, name):
    kids = {}
    for i, (ni, fa, par) in enumerate(lsf.nodes):
        kids.setdefault(par, []).append(i)
    for i in range(len(lsf.nodes)):
        a = lsf.node_attrs(i)
        if (lsf.node_name(i) == 'Resource' and str(a.get('Name', ('', ''))[1]) == name
                and str(a.get('SourceFile', ('', ''))[1]).endswith('.lsf')):
            return i, a, kids.get(i, [])
    raise SystemExit('material %r not found in %s' % (name, lsf))

TYPE_XML = {'Float': 'float', 'Bool': 'bool', 'FixedString': 'FixedString',
            'LSString': 'LSString', 'Int': 'int32', 'Byte': 'uint8',
            'Int64': 'int64', 'Vec3': 'fvec3'}

NEUTRAL_SLOTS = os.environ.get('NEUTRAL_SLOTS', '0') == '1'

def emit_param(lsf, idx, depth):
    """Copy a ScalarParameters / Vector3Parameters node through.

    With NEUTRAL_SLOTS=1 every "02 Colour" slot is forced to white (1,1,1). The shader
    multiplies the base colour by the slot colour selected through MSKColor, so white
    slots make the rendered surface equal the base texture exactly -- what you paint is
    what you get, with no tint shifting the crest's red and white.

    This gives up dye response: a dye works by overwriting these slots, and with the
    artwork carrying all the colour there is nothing meaningful left for it to change.
    That trade is deliberate -- dye support was dropped in favour of getting the
    appearance correct and predictable.
    """
    nm = lsf.node_name(idx)
    a = lsf.node_attrs(idx)
    out = ['%s<node id="%s">' % ('\t'*depth, nm)]
    for k in sorted(a):
        if k == '_OriginalFileVersion_':
            continue
        t, v = a[k]
        xt = TYPE_XML.get(t)
        if xt is None:
            continue
        if t == 'Vec3':
            if NEUTRAL_SLOTS and nm == 'Vector3Parameters' and k in ('Value', 'BaseValue'):
                v = (1.0, 1.0, 1.0)
            v = '%s %s %s' % tuple('%.9g' % c for c in v)
        elif t == 'Bool':
            v = 'True' if v else 'False'
        elif t == 'Float':
            v = '%.9g' % v
        out.append(attr(k, xt, v, depth + 1))
    out.append('%s</node>' % ('\t'*depth))
    return out

def main():
    textures, materials = [], []
    for s in SETS:
        lsf = LSF(open(s['bank'], 'rb').read())
        midx, mattr, mkids = find_material(lsf, s['vanilla_material'])

        entries = [s['bm'], s['msk']]
        if s is SETS[0]:                       # emit the shared neutrals once
            entries += [(u, n, f) for u, n, f, _ in NEUTRAL]
        for uid, name, fn in entries:
            srgb = 'True' if fn.endswith('_BM.DDS') else 'False'
            textures += ['\t\t\t\t<node id="Resource">',
                         attr('ID', 'FixedString', uid),
                         attr('Name', 'LSString', name),
                         attr('SourceFile', 'LSString', '%s/%s' % (ASSET, fn)),
                         attr('Template', 'FixedString', name),
                         attr('Width', 'int32', 2048),
                         attr('Height', 'int32', 2048),
                         attr('Depth', 'int32', 1),
                         attr('Type', 'int32', 1),
                         attr('SRGB', 'bool', srgb),
                         attr('Streaming', 'bool', 'True'),
                         attr('Localized', 'bool', 'False'),
                         '\t\t\t\t</node>']

        body = ['\t\t\t\t<node id="Resource">',
                attr('ID', 'FixedString', s['material_id']),
                attr('Name', 'LSString', s['material_name']),
                attr('SourceFile', 'LSString', SHADER),
                attr('MaterialType', 'uint8', 48),
                attr('DiffusionProfileUUID', 'FixedString', ''),
                '\t\t\t\t\t<children>']
        kept = 0
        for c in mkids:
            if lsf.node_name(c) in ('ScalarParameters', 'Vector3Parameters'):
                body += emit_param(lsf, c, 6)
                kept += 1
        params = [('basecolor', s['bm'][0]), ('MSKColor', s['msk'][0])]
        params += [(pn, u) for u, _, _, pn in NEUTRAL]
        for pname, uid in params:
            body += ['\t\t\t\t\t\t<node id="Texture2DParameters">',
                     attr('ParameterName', 'FixedString', pname, 7),
                     attr('ID', 'FixedString', uid, 7),
                     attr('GroupName', 'FixedString', '01 Texture Map', 7),
                     attr('Enabled', 'bool', 'True', 7),
                     attr('ExportAsPreset', 'bool', 'True', 7),
                     '\t\t\t\t\t\t</node>']
        body += ['\t\t\t\t\t</children>', '\t\t\t\t</node>']
        materials += body
        print('%-10s cloned %d scalar/colour params from %s' % (s['tag'], kept, s['vanilla_material']))

    doc = ['<?xml version="1.0" encoding="utf-8"?>', '<save>',
           '\t<version major="4" minor="0" revision="9" build="0" />']
    for region, rows in (('TextureBank', textures), ('MaterialBank', materials)):
        doc += ['\t<region id="%s">' % region, '\t\t<node id="%s">' % region, '\t\t\t<children>']
        doc += rows
        doc += ['\t\t\t</children>', '\t\t</node>', '\t</region>']
    doc.append('</save>')
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, 'w', encoding='utf-8', newline='\n').write('\n'.join(doc) + '\n')
    print('wrote', OUT)

if __name__ == '__main__':
    main()
