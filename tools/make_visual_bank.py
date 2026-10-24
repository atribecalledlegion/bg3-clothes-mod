"""Generate VisualBank entries: clones of the vanilla garment visuals, with the body
submesh's material swapped for the item's.

Why cloning rather than an override: BG3 root templates expose MaterialOverrides and
RealMaterialOverrides, but a scan of every shipped root template (Shared, Gustav,
GustavDev) found ZERO items using either. Larian's pattern is that an item carries its
own visual resources referencing its own materials, so that is what this reproduces.

Only the Body submesh's material is swapped. The Bracers submesh keeps its vanilla
material, and Body_Cloth is the invisible cloth-simulation proxy.

New visual IDs are uuid5(mod uuid, vanilla id): stable across regenerations, and unique
per item, so two items built on the same garment never collide.

Usage:  python tools/make_visual_bank.py <item>
Writes  <content>/_visuals.lsx (merged by merge_banks.py) and build/work/<item>/visual_map.json
"""
import sys, os, base64, uuid, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lspk import Pak
from lsf import LSF
import item as itemlib

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
    it = itemlib.load()
    g = it.garment
    sets = {s['code']: (s['vanilla_material_id'], ids['material']) for _, s, ids in it.sets()}
    sets.update({s['code']: (s['vanilla_material_id'], ids['material']) for _, s, ids in it.extra_materials()})
    namespace = uuid.UUID(it.ids['mod'])
    prefix = it['visual_prefix']

    pak = Pak(os.path.join(itemlib.DATA, 'Shared.pak'))
    body, mapping = [], {}
    for bank in g['visual_banks']:
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
            if nm.endswith(g['visual_suffix']) and sf.upper().endswith('.GR2'):
                hit = (i, a, nm); break
        if hit is None:
            print('  !! no garment visual in', bank); continue
        i, a, nm = hit
        old_id = str(a['ID'][1])
        new_id = str(uuid.uuid5(namespace, old_id))
        fem = '_F_' in nm or 'Female' in bank
        old_mat, new_mat = sets['F'] if fem else sets['M']
        swapped = [0]
        def rewrite(node, key, val, _o=old_id, _n=new_id, _om=old_mat, _nm=new_mat, _s=swapped):
            if node == 'Resource' and key == 'ID' and val == _o: return _n
            if node == 'Resource' and key == 'Name': return prefix + val
            if node == 'Objects' and key == 'MaterialID' and val == _om:
                _s[0] += 1; return _nm
            return val
        body += emit(lsf, kids, i, 4, rewrite)
        mapping[nm] = dict(old=old_id, new=new_id, material=new_mat, swaps=swapped[0])
        print('  %-34s %s -> %s  (%d material swaps)' % (nm, old_id[:8], new_id[:8], swapped[0]))

    # "mod_visuals": the same garment as fitted by ANOTHER mod for a body Larian never made
    # (e.g. a new race's skeleton). Cloned from that mod's own VisualBank exactly like the
    # vanilla ones -- new ID, our material in place of the vanilla one -- and keyed to that
    # mod's equipment-race IDs in the root template (make_visuals_node.py). SourceFile is
    # left pointing at the other mod's GR2, so it needs that mod loaded to show anything;
    # without it the race keys match nothing and the visual is never used.
    for mv in it.get('mod_visuals', []):
        mpak = Pak(mv['pak'])
        lsf = LSF(mpak.read(mv['bank']))
        kids = {}
        for i, (ni, fa, par) in enumerate(lsf.nodes): kids.setdefault(par, []).append(i)
        hit = next((i for i in range(len(lsf.nodes))
                    if str(lsf.node_attrs(i).get('Name', ('', ''))[1]) == mv['visual']), None)
        if hit is None:
            raise SystemExit('%s: no visual named %s in %s' % (mv['label'], mv['visual'], mv['bank']))
        a = lsf.node_attrs(hit)
        old_id = str(a['ID'][1])
        new_id = str(uuid.uuid5(namespace, old_id))
        old_mat, new_mat = sets[mv['set']]
        swapped = [0]
        # "patched_gr2": a modified copy of the other mod's mesh that ships in THIS mod's
        # own asset folder (e.g. fixed skin weights). The visual then points at it instead
        # of the other mod's file; everything inside the GR2 keeps its names, so the
        # ObjectIDs still resolve. Without it the visual only references the other mod.
        patched = mv.get('patched_gr2')
        def rewrite(node, key, val, _o=old_id, _n=new_id, _om=old_mat, _nm=new_mat, _s=swapped, _p=patched):
            if node == 'Resource' and key == 'ID' and val == _o: return _n
            if node == 'Resource' and key == 'Name': return prefix + val
            if node == 'Resource' and key == 'SourceFile' and _p: return _p
            if node == 'Resource' and key == 'Template' and _p:
                return _p[:-len('.GR2')] + '.' + val.rsplit('/', 1)[-1].split('.', 1)[1]
            if node == 'Objects' and key == 'MaterialID' and val == _om:
                _s[0] += 1; return _nm
            return val
        rows = emit(lsf, kids, hit, 4, rewrite)
        # "hide_body_parts": body regions to hide while this is worn (BG3's mask slots, the
        # same mechanism vanilla armour uses -- Thighs, knees, shins, ...). Added to the
        # cloned visual next to the ones it already has, so a robe whose legs clip through
        # the cloth can simply not show them.
        extra = [s for s in mv.get('hide_body_parts', [])]
        if extra:
            ins = []
            for slot in extra:
                ins += ['\t' * 6 + '<node id="VertexColorMaskSlots">',
                        '\t' * 7 + '<attribute id="Object" type="FixedString" value="%s" />' % slot,
                        '\t' * 6 + '</node>']
            rows[-2:-2] = ins            # before the Resource's closing </children>
        body += rows
        if not swapped[0]:
            raise SystemExit('%s: %s uses none of the vanilla material %s, so it would keep '
                             'the vanilla texture' % (mv['label'], mv['visual'], old_mat))
        # Companion visuals worn with the garment (the pants under a robe). A plain ID is
        # used as it is; {"visual", "bank", "material_code"} is cloned out of that bank with
        # its material swapped for one of the item's "mod_materials", like the garment itself.
        companions = []
        for comp in mv.get('companions', []):
            if isinstance(comp, str):
                companions.append(comp)
                continue
            clsf = LSF(mpak.read(comp['bank']))
            ckids = {}
            for i, (ni, fa, par) in enumerate(clsf.nodes): ckids.setdefault(par, []).append(i)
            chit = next((i for i in range(len(clsf.nodes))
                         if clsf.node_name(i) == 'Resource'
                         and str(clsf.node_attrs(i).get('ID', ('', ''))[1]) == comp['visual']), None)
            if chit is None:
                raise SystemExit('%s: companion visual %s not in %s' % (mv['label'], comp['visual'], comp['bank']))
            c_old = comp['visual']
            c_new = str(uuid.uuid5(namespace, c_old))
            c_om, c_nm = sets[comp['material_code']]
            c_swapped = [0]
            def crewrite(node, key, val, _o=c_old, _n=c_new, _om=c_om, _nm=c_nm, _s=c_swapped):
                if node == 'Resource' and key == 'ID' and val == _o: return _n
                if node == 'Resource' and key == 'Name': return prefix + val
                if node == 'Objects' and key == 'MaterialID' and val == _om:
                    _s[0] += 1; return _nm
                return val
            body += emit(clsf, ckids, chit, 4, crewrite)
            if not c_swapped[0]:
                raise SystemExit('companion %s uses none of material %s' % (c_old, c_om))
            print('  %-34s %s -> %s  (%d material swaps)  [companion of %s]' % (
                str(clsf.node_attrs(chit).get('Name', ('', ''))[1]), c_old[:8], c_new[:8], c_swapped[0], mv['visual']))
            companions.append(c_new)
        mapping[mv['visual']] = dict(old=old_id, new=new_id, material=new_mat, swaps=swapped[0],
                                     mod=mv['label'], races=mv['races'], companions=companions)
        print('  %-34s %s -> %s  (%d material swaps)  [%s]' % (
            mv['visual'], old_id[:8], new_id[:8], swapped[0], mv['label']))

    doc = ['<?xml version="1.0" encoding="utf-8"?>', '<save>',
           '\t<version major="4" minor="0" revision="9" build="0" />',
           '\t<region id="VisualBank">', '\t\t<node id="VisualBank">', '\t\t\t<children>']
    doc += body
    doc += ['\t\t\t</children>', '\t\t</node>', '\t</region>', '</save>']
    out = it.content + '/_visuals.lsx'
    itemlib.write(out, '\n'.join(doc)+'\n')
    vmap = os.path.join(it.work, 'visual_map.json')
    json.dump(mapping, open(vmap,'w'), indent=2)
    print('\nwrote %s  (%d visuals)' % (out, len(mapping)))
    print('wrote %s' % vmap)

if __name__ == '__main__':
    main()
