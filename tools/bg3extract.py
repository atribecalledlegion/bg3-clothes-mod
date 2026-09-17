"""Read BG3 .pak archives and .lsf resource files without LSLib.

  python tools/bg3extract.py list   <pak> [substr ...]
  python tools/bg3extract.py get    <pak> <path-in-pak> <outfile>
  python tools/bg3extract.py dump   <file.lsf> [uuid-or-name ...]
  python tools/bg3extract.py find   <pak> <uuid>      # which .lsf defines this resource
"""
import sys, os, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lspk import Pak
from lsf import LSF

DATA = r"C:\Program Files (x86)\Steam\steamapps\common\Baldurs Gate 3\Data"

def _pak(name):
    if os.path.exists(name):
        return Pak(name)
    return Pak(os.path.join(DATA, name if name.endswith('.pak') else name + '.pak'))

def cmd_list(pak, *pats):
    p = _pak(pak)
    pats = [x.lower() for x in pats]
    hits = [n for n in p.entries if all(x in n.lower() for x in pats)]
    print('%d files, %d matches' % (len(p.entries), len(hits)))
    for h in sorted(hits)[:400]:
        print('  %-10d %s' % (p.entries[h][4], h))

def cmd_get(pak, path, out):
    d = _pak(pak).read(path)
    open(out, 'wb').write(d)
    print('%d bytes -> %s' % (len(d), out))

def _children(f):
    kids = {}
    for i, (ni, fa, par) in enumerate(f.nodes):
        kids.setdefault(par, []).append(i)
    return kids

def cmd_dump(path, *keys):
    f = LSF(open(path, 'rb').read())
    kids = _children(f)
    keys = [k.lower() for k in keys]
    def show(i, d=0):
        a = f.node_attrs(i)
        print('  ' * d + '<' + f.node_name(i) + '>')
        for k in sorted(a):
            print('  ' * d + '   %-26s %s' % (k, a[k][1]))
        for c in kids.get(i, []):
            show(c, d + 1)
    if not keys:
        print('nodes=%d attrs=%d' % (len(f.nodes), len(f.attrs)))
        return
    for i in range(len(f.nodes)):
        vals = [str(v[1]).lower() for v in f.node_attrs(i).values()]
        if any(k in vals for k in keys):
            show(i)

def cmd_find(pak, uuid):
    p = _pak(pak)
    for n in p.entries:
        if not n.lower().endswith('.lsf'):
            continue
        try:
            d = p.read(n)
        except Exception:
            continue
        if uuid.encode() not in d:
            continue
        try:
            f = LSF(d)
        except Exception:
            print('  (references, unparsed)', n); continue
        for i in range(len(f.nodes)):
            a = f.node_attrs(i)
            if str(a.get('ID', ('', ''))[1]) == uuid:
                print('DEFINED IN %s  <%s>' % (n, f.node_name(i)))
                for k in sorted(a):
                    print('   %-24s %s' % (k, a[k][1]))
                return
        print('  references:', n)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__); raise SystemExit(1)
    {'list': cmd_list, 'get': cmd_get, 'dump': cmd_dump, 'find': cmd_find}[sys.argv[1]](*sys.argv[2:])
