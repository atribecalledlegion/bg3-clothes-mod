"""Generate VisualBank entries: clones of the vanilla robe visuals, with the body
submesh's material swapped for ours.

Why cloning rather than an override: BG3 root templates expose MaterialOverrides and
RealMaterialOverrides, but a scan of every shipped root template (Shared, Gustav,
GustavDev) found ZERO items using either. Larian's pattern is that an item carries its
own visual resources referencing its own materials, so that is what this reproduces.

Only the robe Body visual is cloned per body type. Each visual also has Bracers and
Cloth submeshes that keep their vanilla materials -- they use separate textures, so
swapping them would break them.
"""
import sys, os, base64, uuid, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lspk import Pak
from lsf import LSF

DATA = r"C:\Program Files (x86)\Steam\steamapps\common\Baldurs Gate 3\Data"
OUT  = 'src/Public/ObitoUchihaRobe/Content/Assets/Characters/[PAK]_ObitoUchihaRobe/_visuals.lsx'
MAP  = 'art/source/visual_map.json'

MAT_M_VANILLA = '92cca1dc-071f-1a40-6eb3-de8e16a38c25'
MAT_F_VANILLA = '4bf29629-687c-5330-bce8-8d22432941c8'
MAT_M_NEW     = '8b0f3491-d048-4989-82ef-afde63bdac5e'
MAT_F_NEW     = '5d271dbf-18a4-430d-b896-2a33532e9148'

BANKS = [
    'Humans/[PAK]_Male_Armor', 'Humans/[PAK]_Female_Armor',
    'Humans/[PAK]_MaleStrong_Armor', 'Humans/[PAK]_FemaleStrong_Armor',
    'Githyanki/[PAK]_Male_Armor', 'Githyanki/[PAK]_Female_Armor',
    'Dwarves/[PAK]_Male_Armor', 'Dwarves/[PAK]_Female_Armor',
    'Halflings/[PAK]_Male_Armor', 'Halflings/[PAK]_Female_Armor',
    'Gnomes/[PAK]_Male_Armor', 'Gnomes/[PAK]_Female_Armor',
    'Dragonborn/[PAK]_Male_Armor', 'Dragonborn/[PAK]_Female_Armor',
]

XT = {'FixedString':'FixedString','LSString':'LSString','Bool':'bool','Byte':'uint8',
      'Int':'int32','Int64':'int64','Float':'float','Vec3':'fvec3','UInt':'uint32',
      'Int8':'int8','ScratchBuffer':'ScratchBuffer','UUID':'guid'}

def esc(s):
    return (str(s).replace('&','&amp;').replace('<','&lt;')
            .replace('>','&gt;').replace('"','&quot;'))

def fmt(t, v, raw):
    if t == 'ScratchBuffer': return base64.b64encode(raw).decode()
    if t == 'Bool':  return 'True' if v else 'False'
    if t == 'Float': return '%.9g' % v
    if t == 'Vec3':  return ' '.join('%.9g' % c for c in v)
    return str(v)

def emit(lsf, kids, i, depth, rewrite):
    a = lsf.node_attrs_raw(i)
    rows = ['%s<node id="%s">' % ('\t'*depth, lsf.node_name(i))]
    for k in sorted(a):
        if k == '_OriginalFileVersion_':
            continue
        t, v, raw = a[k]
        xt = XT.get(t)
        if xt is None:
            continue
        val = rewrite(lsf.node_name(i), k, fmt(t, v, raw))
        rows.append('%s<attribute id="%s" type="%s" value="%s" />' % ('\t'*(depth+1), k, xt, esc(val)))
    ch = kids.get(i, [])
    if ch:
        rows.append('%s<children>' % ('\t'*(depth+1)))
        for c in ch:
            rows += emit(lsf, kids, c, depth+2, rewrite)
        rows.append('%s</children>' % ('\t'*(depth+1)))
    rows.append('%s</node>' % ('\t'*depth))
    return rows

def main():
    pak = Pak(os.path.join(DATA, 'Shared.pak'))
    body, mapping = [], {}
    for bank in BANKS:
        path = 'Public/Shared/Content/Assets/Characters/%s/_merged.lsf' % bank
        if path not in pak.entries:
            print('  !! missing bank', bank); continue
        lsf = LSF(pak.read(path))
        kids = {}
        for i,(ni,fa,par) in enumerate(lsf.nodes): kids.setdefault(par,[]).append(i)
        hit = None
        for i in range(len(lsf.nodes)):
            a = lsf.node_attrs(i)
            nm = str(a.get('Name',('',''))[1])
            sf = str(a.get('SourceFile',('',''))[1])
            if nm.endswith('_ARM_Robe_A_Body') and sf.upper().endswith('.GR2'):
                hit = (i, a, nm); break
        if hit is None:
            print('  !! no robe visual in', bank); continue
        i, a, nm = hit
        old_id = str(a['ID'][1])
        new_id = str(uuid.uuid5(uuid.UUID('d2f4984b-c5c7-4cd3-97a0-63bff6b561b7'), old_id))
        fem = '_F_' in nm or 'Female' in bank
        old_mat, new_mat = (MAT_F_VANILLA, MAT_F_NEW) if fem else (MAT_M_VANILLA, MAT_M_NEW)
        swapped = [0]
        def rewrite(node, key, val, _o=old_id, _n=new_id, _om=old_mat, _nm=new_mat, _s=swapped):
            if node == 'Resource' and key == 'ID' and val == _o: return _n
            if node == 'Resource' and key == 'Name': return 'Obito_' + val
            if node == 'Objects' and key == 'MaterialID' and val == _om:
                _s[0] += 1; return _nm
            return val
        body += emit(lsf, kids, i, 4, rewrite)
        mapping[nm] = dict(old=old_id, new=new_id, material=new_mat, swaps=swapped[0])
        print('  %-34s %s -> %s  (%d material swaps)' % (nm, old_id[:8], new_id[:8], swapped[0]))

    doc = ['<?xml version="1.0" encoding="utf-8"?>', '<save>',
           '\t<version major="4" minor="0" revision="9" build="0" />',
           '\t<region id="VisualBank">', '\t\t<node id="VisualBank">', '\t\t\t<children>']
    doc += body
    doc += ['\t\t\t</children>', '\t\t</node>', '\t</region>', '</save>']
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT,'w',encoding='utf-8',newline='\n').write('\n'.join(doc)+'\n')
    json.dump(mapping, open(MAP,'w'), indent=2)
    print('\nwrote %s  (%d visuals)' % (OUT, len(mapping)))
    print('wrote %s' % MAP)

if __name__ == '__main__':
    main()
