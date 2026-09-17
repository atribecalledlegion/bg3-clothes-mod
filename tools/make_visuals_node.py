"""Emit the root template's <Visuals> node: Gale's race->visual map, with the robe body
visual swapped for our clone. Body types we did not clone (Dragonborn, which uses its own
materials and textures) keep the vanilla visual and simply show the vanilla robe."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lspk import Pak
from lsf import LSF

DATA = r"C:\Program Files (x86)\Steam\steamapps\common\Baldurs Gate 3\Data"
GALE = '9410a467-3e49-4b14-b067-ea8ad6a0d431'

def main():
    swap = {v['old']: v['new'] for v in json.load(open('art/source/visual_map.json')).values()}
    pak = Pak(os.path.join(DATA, 'Shared.pak'))
    f = LSF(pak.read('Public/Shared/RootTemplates/_merged.lsf'))
    kids = {}
    for i, (ni, fa, par) in enumerate(f.nodes): kids.setdefault(par, []).append(i)
    go = None
    for i in range(len(f.nodes)):
        a = f.node_attrs(i)
        if f.node_name(i) == 'GameObjects' and str(a.get('MapKey', ('', ''))[1]) == GALE:
            go = i; break
    vis = None
    for c in kids.get(go, []):
        if f.node_name(c) == 'Equipment':
            for g in kids.get(c, []):
                if f.node_name(g) == 'Visuals': vis = g
    rows = ['\t\t\t\t\t\t<node id="Visuals">', '\t\t\t\t\t\t\t<children>']
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
    rows += ['\t\t\t\t\t\t\t</children>', '\t\t\t\t\t\t</node>']
    print('body types: %d   visuals swapped to ours: %d' % (len(kids.get(vis, [])), n_swap))
    open('art/source/visuals_node.xml', 'w', encoding='utf-8', newline='\n').write('\n'.join(rows) + '\n')
    print('wrote art/source/visuals_node.xml')

if __name__ == '__main__':
    main()
