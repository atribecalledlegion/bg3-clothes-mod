"""VisualBank entries for an item whose meshes we imported ourselves (GR2 files).

    python tools/make_custom_visual.py <item>

Writes <content>/_visuals.lsx and build/work/<item>/visuals_node.xml, and copies each GR2
into the item's src tree.

A visual resource is cloned from the vanilla garment the mesh was conformed to, and only
three things change: the ID, the SourceFile/Template paths (to our GR2) and the submesh
MaterialID (to our material). Everything else -- LOD distances, cloth flags, the object
list -- stays exactly as Larian had it.

The ObjectID strings inside a visual name the model and mesh INSIDE the GR2
("HUM_M_CLT_Pants_H_Short.HUM_M_CLT_Pants_H_Short_Mesh.0"). tools/gltf_retarget.py keeps
the vanilla mesh name, and the GR2 is written under the vanilla file name, so those
strings still resolve. Rename either and the visual silently references nothing.

Body types without their own mesh are left out of the map: they show no garment at all
rather than the wrong body's mesh.
"""
import json, os, re, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lspk import Pak
from lsf import LSF
import item as itemlib
from make_visual_bank import emit


def main():
    it = itemlib.load()
    c = it.custom
    if not c:
        raise SystemExit('%s is not a custom-mesh item' % it.id)

    pak = Pak(os.path.join(itemlib.DATA, 'Shared.pak'))
    body, mapping = [], {}
    for tag, s, ids in it.sets():
        lsf = LSF(pak.read(s['visual_bank']))
        kids = {}
        for i, (ni, fa, par) in enumerate(lsf.nodes):
            kids.setdefault(par, []).append(i)
        src = None
        for i in range(len(lsf.nodes)):
            if str(lsf.node_attrs(i).get('ID', ('', ''))[1]) == s['vanilla_visual']:
                src = i; break
        if src is None:
            raise SystemExit('vanilla visual %s not found in %s' % (s['vanilla_visual'], s['visual_bank']))

        # "vanilla_mesh": true keeps Larian's own mesh: no GR2 is shipped, SourceFile and
        # Template stay as the vanilla visual has them, every LOD stays, and only the
        # material is swapped -- a retexture, like the robe items.
        vanilla_mesh = s.get('vanilla_mesh', False)
        if vanilla_mesh:
            gr2 = asset = '(vanilla mesh)'
        else:
            gr2 = s.get('gr2_as') or os.path.basename(s['gr2'])
            asset = '%s/%s' % (c['asset_dir'], gr2)
            dst = '%s/%s/%s' % (it.src, c['asset_dir'], gr2)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(s['gr2'], dst)

        # Keep only the LODs our GR2 actually contains. A cloned visual that still lists
        # the vanilla LOD1..LOD4 objects points at meshes that do not exist in our file.
        keep = set(s.get('keep_lods', [0]))
        # VertexColorMaskSlots name the body regions this garment hides underneath it
        # (e.g. Torso, upperarm, wrists, lowerarm, Shoulders for a shirt). Omitting the
        # whole list (hide_body_parts: false) leaves the ENTIRE body always visible --
        # including regions the mesh actually covers, which showed up as bare skin and
        # even the character's underwear colour bleeding through the torso and glutes at
        # runtime (confirmed: those colours do not exist anywhere in our own texture).
        # Keeping the whole list (true) is wrong the other way when the imported mesh is
        # SHORTER than the vanilla donor: e.g. our jacket's sleeves end mid-forearm, so
        # inheriting "wrists"/"lowerarm" hides skin our mesh never draws over, leaving
        # invisible forearms with the hands floating.
        # hide_body_parts can be True (keep every slot), False (drop every slot), or a
        # list of slot names to DROP -- keeping every other slot the donor declares. List
        # the regions this item's mesh does NOT actually cover.
        hide = s.get('hide_body_parts', True)
        hide_exclude = set(hide) if isinstance(hide, list) else set()
        dropped = 0
        for parent, ch in kids.items():
            keep_ch = []
            for child in ch:
                at = lsf.node_attrs(child)
                name = lsf.node_name(child)
                if name == 'Objects' and not vanilla_mesh and int(at.get('LOD', ('', 0))[1]) not in keep:
                    dropped += 1
                    continue
                if name == 'VertexColorMaskSlots':
                    if hide is False:
                        continue
                    if str(at.get('Object', ('', ''))[1]) in hide_exclude:
                        continue
                keep_ch.append(child)
            kids[parent] = keep_ch
        if dropped:
            print('  %-10s dropped %d LOD objects the GR2 does not have' % (tag, dropped))

        old_mat = s['vanilla_material_id']
        swaps = [0]
        def rewrite(node, key, val, _m=old_mat, _n=ids['material'], _s=swaps):
            if node == 'Resource' and key == 'ID':
                return ids['visual']
            if node == 'Resource' and key == 'Name':
                return '%s_%s' % (it.folder, tag)
            if node == 'Resource' and key == 'SourceFile' and not vanilla_mesh:
                return asset
            if node == 'Resource' and key == 'Template' and not vanilla_mesh:
                # "<same path without .GR2>.<root node>.<n>", e.g.
                # Generated/Public/<Mod>/.../Foo.Dummy_Root.0 (matches Uchiha Weapons, a
                # working mod with its own GR2). Leaving the vanilla path here makes the
                # item load nothing: the legs are hidden by the equipped item and no
                # garment appears in their place.
                return '%s/%s' % (c['asset_dir'], val.rsplit('/', 1)[-1])
            if node == 'Objects' and key == 'MaterialID' and val == _m:
                _s[0] += 1
                return _n
            return val
        body += emit(lsf, kids, src, 4, rewrite)
        mapping[tag] = dict(visual=ids['visual'], gr2=asset, body_types=s['body_types'], swaps=swaps[0])
        print('  %-10s %s -> %s  (%d material swaps)' % (tag, gr2, ids['visual'][:8], swaps[0]))

    doc = ['<?xml version="1.0" encoding="utf-8"?>', '<save>',
           '\t<version major="4" minor="0" revision="9" build="0" />',
           '\t<region id="VisualBank">', '\t\t<node id="VisualBank">', '\t\t\t<children>']
    doc += body
    doc += ['\t\t\t</children>', '\t\t</node>', '\t</region>', '</save>']
    out = it.content + '/_visuals.lsx'
    itemlib.write(out, '\n'.join(doc) + '\n')

    # One Object per body type, listing every visual that body type wears (jacket AND
    # trousers). Emitting one Object per visual repeats the MapKey, and a map with
    # duplicate keys keeps only one of them -- so half the outfit goes missing.
    by_body = {}
    for tag, m in mapping.items():
        for key in m['body_types']:
            by_body.setdefault(key, []).append(m['visual'])
    rows = ['\t\t\t\t\t\t<node id="Visuals">', '\t\t\t\t\t\t\t<children>']
    for key, visuals in by_body.items():
        rows += ['\t\t\t\t\t\t\t\t<node id="Object">',
                 '\t\t\t\t\t\t\t\t\t<attribute id="MapKey" type="guid" value="%s" />' % key,
                 '\t\t\t\t\t\t\t\t\t<children>']
        for v in visuals:
            rows += ['\t\t\t\t\t\t\t\t\t\t<node id="MapValue">',
                     '\t\t\t\t\t\t\t\t\t\t\t<attribute id="Object" type="FixedString" value="%s" />' % v,
                     '\t\t\t\t\t\t\t\t\t\t</node>']
        rows += ['\t\t\t\t\t\t\t\t\t</children>', '\t\t\t\t\t\t\t\t</node>']
    n = sum(len(v) for v in by_body.values())
    rows += ['\t\t\t\t\t\t\t</children>', '\t\t\t\t\t\t</node>']
    itemlib.write(os.path.join(it.work, 'visuals_node.xml'), '\n'.join(rows) + '\n')
    json.dump(mapping, open(os.path.join(it.work, 'visual_map.json'), 'w'), indent=2)
    print('wrote %s  (%d visuals, %d body types)' % (out, len(mapping), n))


if __name__ == '__main__':
    main()
