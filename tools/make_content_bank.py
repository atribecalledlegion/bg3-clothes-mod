"""Generate the item's Content bank (_merged.lsx): texture + material resources.

Rather than hand-writing the XML, this clones the vanilla body material out of the
shipped banks -- keeping every ScalarParameter and the whole "02 Colour" slot set exactly
as Larian tuned them -- and rewires it:

  * SourceFile  CHAR_BASE_VertCut_VT.lsf  ->  CHAR_BASE_VertCut.lsf
    The _VT shader reads base/normal/physical out of a virtual tile set, which modders
    cannot easily rebuild. The non-VT sibling takes ordinary DDS inputs and is already
    used by real armour in the same bank, so this is a supported path, not a hack.
  * texture inputs wired to our own DDS. The non-VT shader's parameter names were read
    off a vanilla material that uses it (HUM_M_ARM_ChainShirt_A_0_Pants):
        basecolor / normalmap / physicalmap / MSKColor,  MaterialType 48.

All four texture inputs are wired. The garment's vanilla NM/PM are still inside the
virtual texture, so neutral stand-ins are used (tools/make_neutral_maps.py). An unbound
normalmap renders the whole garment black, so flat-but-present beats absent.

Usage:  python tools/make_content_bank.py <item>
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lsf import LSF
import item as itemlib

SHADER = 'Public/Shared/Assets/Materials/Characters/CHAR_BASE_VertCut.lsf'

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

def emit_param(lsf, idx, depth, neutral_slots):
    """Copy a ScalarParameters / Vector3Parameters node through.

    With neutral_slots ("neutral_slots": true in item.json) every "02 Colour" slot is
    forced to white (1,1,1). The shader multiplies the base colour by the slot colour selected through MSKColor, so white
    slots make the rendered surface equal the base texture exactly -- what you paint is
    what you get, with no tint shifting the artwork's colours.

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
            if neutral_slots and nm == 'Vector3Parameters' and k in ('Value', 'BaseValue'):
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
    it = itemlib.load()
    # Off by default: the in-game-verified build keeps Larian's slot colours in the
    # material and neutralises them with the item's white preset (make_preset.py).
    neutral_slots = it.get('neutral_slots', False)
    f = it.folder
    # Shared by both materials: neutral stand-ins, so one copy of each is enough.
    neutral = [(it.ids['nm'], f + '_NM', f + '_NM.DDS', 'normalmap'),
               (it.ids['pm'], f + '_PM', f + '_PM.DDS', 'physicalmap')]
    textures, materials = [], []
    for n, (tag, s, ids) in enumerate(list(it.sets()) + list(it.extra_materials())):
        size = s.get('size', 2048)
        lsf = LSF(open(s['bank'], 'rb').read())
        midx, mattr, mkids = find_material(lsf, s['vanilla_material'])
        bm = (ids['bm'], '%s_%s_BM' % (f, s['code']), s['bm'])
        msk = (ids['msk'], '%s_%s_MSKcloth' % (f, s['code']), s['msk'])

        entries = [bm, msk]
        if n == 0:                             # emit the shared neutrals once
            entries += [(u, nm, fn) for u, nm, fn, _ in neutral]
        for uid, name, fn in entries:
            srgb = 'True' if fn.endswith('_BM.DDS') else 'False'
            # the neutral maps are always 2048; this set's own textures may be smaller
            dim = 2048 if (uid, name, fn) in [(u, nm, f2) for u, nm, f2, _ in neutral] else size
            textures += ['\t\t\t\t<node id="Resource">',
                         attr('ID', 'FixedString', uid),
                         attr('Name', 'LSString', name),
                         attr('SourceFile', 'LSString', '%s/%s' % (it.texture_asset, fn)),
                         attr('Template', 'FixedString', name),
                         attr('Width', 'int32', dim),
                         attr('Height', 'int32', dim),
                         attr('Depth', 'int32', 1),
                         attr('Type', 'int32', 1),
                         attr('SRGB', 'bool', srgb),
                         attr('Streaming', 'bool', 'True'),
                         attr('Localized', 'bool', 'False'),
                         '\t\t\t\t</node>']

        body = ['\t\t\t\t<node id="Resource">',
                attr('ID', 'FixedString', ids['material']),
                attr('Name', 'LSString', '%s_%s_Body' % (f, s['code'])),
                attr('SourceFile', 'LSString', SHADER),
                attr('MaterialType', 'uint8', 48),
                attr('DiffusionProfileUUID', 'FixedString', ''),
                '\t\t\t\t\t<children>']
        kept = 0
        for c in mkids:
            if lsf.node_name(c) in ('ScalarParameters', 'Vector3Parameters'):
                body += emit_param(lsf, c, 6, neutral_slots)
                kept += 1
        params = [('basecolor', bm[0]), ('MSKColor', msk[0])]
        params += [(pn, u) for u, _, _, pn in neutral]
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
        print('%-10s cloned %d scalar/colour params from %s' % (tag, kept, s['vanilla_material']))

    doc = ['<?xml version="1.0" encoding="utf-8"?>', '<save>',
           '\t<version major="4" minor="0" revision="9" build="0" />']
    for region, rows in (('TextureBank', textures), ('MaterialBank', materials)):
        doc += ['\t<region id="%s">' % region, '\t\t<node id="%s">' % region, '\t\t\t<children>']
        doc += rows
        doc += ['\t\t\t</children>', '\t\t</node>', '\t</region>']
    doc.append('</save>')
    out = it.content + '/_merged.lsx'
    itemlib.write(out, '\n'.join(doc) + '\n')
    print('wrote', out)

if __name__ == '__main__':
    main()
