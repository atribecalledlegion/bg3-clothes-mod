"""Parse a COLLADA mesh exported from a BG3 GR2 and report / render its UV layout."""
import sys, xml.etree.ElementTree as ET
NS = {'c': 'http://www.collada.org/2005/11/COLLADASchema'}
Q = '{http://www.collada.org/2005/11/COLLADASchema}'

def load(path, geom_name):
    root = ET.parse(path).getroot()
    for g in root.iter(Q + 'geometry'):
        if (g.get('name') or g.get('id')) != geom_name:
            continue
        m = g.find('c:mesh', NS)
        src = {}
        for s in m.findall('c:source', NS):
            fa = s.find('c:float_array', NS)
            acc = s.find('c:technique_common/c:accessor', NS)
            stride = int(acc.get('stride'))
            vals = [float(x) for x in fa.text.split()]
            src[s.get('id')] = [vals[i:i+stride] for i in range(0, len(vals), stride)]
        tri = m.find('c:triangles', NS)
        if tri is None:
            tri = m.find('c:polylist', NS)
        inputs = {}
        for i in tri.findall('c:input', NS):
            inputs[i.get('semantic')] = (i.get('source')[1:], int(i.get('offset')))
        stride = max(o for _, o in inputs.values()) + 1
        p = [int(x) for x in tri.find('c:p', NS).text.split()]
        n = int(tri.get('count'))
        # VERTEX input points at <vertices>, resolve to the positions source
        vsrc = inputs['VERTEX'][0]
        for v in m.findall('c:vertices', NS):
            if v.get('id') == vsrc:
                vsrc = v.find('c:input', NS).get('source')[1:]
        pos = src[vsrc]
        nrm = src[inputs['NORMAL'][0]] if 'NORMAL' in inputs else None
        uv  = src[inputs['TEXCOORD'][0]]
        tris = []
        for t in range(n):
            vt = []
            for k in range(3):
                base = (t*3 + k) * stride
                vt.append((
                    pos[p[base + inputs['VERTEX'][1]]],
                    nrm[p[base + inputs['NORMAL'][1]]] if nrm else None,
                    uv[p[base + inputs['TEXCOORD'][1]]],
                ))
            tris.append(vt)
        return tris
    raise SystemExit('geometry %r not found' % geom_name)

if __name__ == '__main__':
    tris = load(sys.argv[1], sys.argv[2])
    print('triangles:', len(tris))
    ax = list(zip(*[v[0] for t in tris for v in t]))
    for i, nm in enumerate('XYZ'):
        print('  %s %8.3f .. %8.3f' % (nm, min(ax[i]), max(ax[i])))
    us = [v[2][0] for t in tris for v in t]
    vs = [v[2][1] for t in tris for v in t]
    print('  U %8.3f .. %8.3f' % (min(us), max(us)))
    print('  V %8.3f .. %8.3f' % (min(vs), max(vs)))
