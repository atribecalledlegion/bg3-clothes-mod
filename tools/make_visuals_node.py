"""Emit the root template's <Visuals> node: the parent template's race->visual map, with
the garment visual swapped for our clone. Body types we did not clone (Dragonborn, which
uses its own materials and textures) keep the vanilla visual and show the vanilla garment.

Usage:  python tools/make_visuals_node.py <item>     (after make_visual_bank.py)
Writes  build/work/<item>/visuals_node.xml
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lspk import Pak
from lsf import LSF
import item as itemlib

def main():
    it = itemlib.load()
    parent = it.garment['parent_template']
    vmap = json.load(open(os.path.join(it.work, 'visual_map.json')))
    swap = {v['old']: v['new'] for v in vmap.values()}
    pak = Pak(os.path.join(itemlib.DATA, 'Shared.pak'))
    f = LSF(pak.read('Public/Shared/RootTemplates/_merged.lsf'))
    kids = {}
    for i, (ni, fa, par) in enumerate(f.nodes): kids.setdefault(par, []).append(i)
    go = None
    for i in range(len(f.nodes)):
        a = f.node_attrs(i)
        if f.node_name(i) == 'GameObjects' and str(a.get('MapKey', ('', ''))[1]) == parent:
            go = i; break
    vis, parent_race = None, None
    for c in kids.get(go, []):
        if f.node_name(c) == 'Equipment':
            for g in kids.get(c, []):
                if f.node_name(g) == 'Visuals': vis = g
                if f.node_name(g) == 'ParentRace': parent_race = g
    # ParentRace: for a race that has a DefaultParent (Githyanki -> Human, Dragonborn ->
    # Human Strong, and every race a mod builds on another body), the game uses the PARENT
    # race's visuals unless the template lists the race here with a zero GUID, meaning "this
    # item has its own visuals for it". The vanilla robe lists exactly the four such races it
    # does supply visuals for. The child template's Equipment replaces the parent's, so the
    # block has to be written out again -- without it those races silently wear the parent
    # race's garment, and a race added by another mod (Dhaen, whose parent is Gnome Male)
    # gets a garment built for a different skeleton.
    ZERO = '00000000-0000-0000-0000-000000000000'
    pr = [(str(f.node_attrs(o)['MapKey'][1]), str(f.node_attrs(o)['MapValue'][1]))
          for o in kids.get(parent_race, [])]
    have_pr = {k for k, _ in pr}
    for v in vmap.values():
        for race in v.get('races', []):
            if race not in have_pr:
                pr.append((race, ZERO)); have_pr.add(race)
    rows = []
    if pr:
        rows += ['\t\t\t\t\t\t<node id="ParentRace">', '\t\t\t\t\t\t\t<children>']
        for k, val in pr:
            rows += ['\t\t\t\t\t\t\t\t<node id="Object">',
                     '\t\t\t\t\t\t\t\t\t<attribute id="MapKey" type="guid" value="%s" />' % k,
                     '\t\t\t\t\t\t\t\t\t<attribute id="MapValue" type="guid" value="%s" />' % val,
                     '\t\t\t\t\t\t\t\t</node>']
        rows += ['\t\t\t\t\t\t\t</children>', '\t\t\t\t\t\t</node>']
    rows += ['\t\t\t\t\t\t<node id="Visuals">', '\t\t\t\t\t\t\t<children>']
    n_swap = 0
    for obj in kids.get(vis, []):
        a = f.node_attrs(obj)
        rows += ['\t\t\t\t\t\t\t\t<node id="Object">',
                 '\t\t\t\t\t\t\t\t\t<attribute id="MapKey" type="guid" value="%s" />' % a['MapKey'][1],
                 '\t\t\t\t\t\t\t\t\t<children>']
        for mv in kids.get(obj, []):
            val = str(f.node_attrs(mv)['Object'][1])
            if val in swap:
                val = swap[val]; n_swap += 1
            rows += ['\t\t\t\t\t\t\t\t\t\t<node id="MapValue">',
                     '\t\t\t\t\t\t\t\t\t\t\t<attribute id="Object" type="FixedString" value="%s" />' % val,
                     '\t\t\t\t\t\t\t\t\t\t</node>']
        rows += ['\t\t\t\t\t\t\t\t\t</children>', '\t\t\t\t\t\t\t\t</node>']
    # Body types added by other mods ("mod_visuals" in item.json). The child template's
    # Visuals replaces the parent's wholesale, so entries another mod added to the parent
    # are not inherited and have to be listed here. Each race gets our clone first, then
    # the companion visuals that mod pairs with the garment (as it does for the vanilla one).
    have = {str(f.node_attrs(o)['MapKey'][1]) for o in kids.get(vis, [])}
    n_mod = 0
    for v in vmap.values():
        for race in v.get('races', []):
            if race in have:
                raise SystemExit('race %s is already mapped by the vanilla template' % race)
            have.add(race)
            n_mod += 1
            rows += ['\t\t\t\t\t\t\t\t<node id="Object">',
                     '\t\t\t\t\t\t\t\t\t<attribute id="MapKey" type="guid" value="%s" />' % race,
                     '\t\t\t\t\t\t\t\t\t<children>']
            for val in [v['new']] + v.get('companions', []):
                rows += ['\t\t\t\t\t\t\t\t\t\t<node id="MapValue">',
                         '\t\t\t\t\t\t\t\t\t\t\t<attribute id="Object" type="FixedString" value="%s" />' % val,
                         '\t\t\t\t\t\t\t\t\t\t</node>']
            rows += ['\t\t\t\t\t\t\t\t\t</children>', '\t\t\t\t\t\t\t\t</node>']
    rows += ['\t\t\t\t\t\t\t</children>', '\t\t\t\t\t\t</node>']
    print('body types: %d   visuals swapped to ours: %d   added for other mods: %d' % (
        len(kids.get(vis, [])), n_swap, n_mod))
    out = os.path.join(it.work, 'visuals_node.xml')
    itemlib.write(out, '\n'.join(rows) + '\n')
    print('wrote', out)

if __name__ == '__main__':
    main()
