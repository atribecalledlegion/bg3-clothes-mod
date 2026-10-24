"""Scale the root motion of Skyrim SE .hkx clips that carry it as 'animmotion x y z' annotations (read by Animation
Motion Revolution). Each annotation string is rewritten in place with one decimal, which never makes it longer than
the original two-decimal text, so no offsets move. usage: scale_animmotion.py <factor> <in.hkx> <out.hkx>"""
import sys, os, struct
sys.path.insert(0, sys.argv[4] if len(sys.argv) > 4 else os.path.dirname(os.path.abspath(__file__)))
from hkanno import Pack
k = float(sys.argv[1]); src, dst = sys.argv[2], sys.argv[3]
pk = Pack(src); d = pk.d; done = set(); n = 0
for anim in pk.animations():
    for t, name, anns in pk.tracks(anim):
        for a, time, text in anns:
            if not text.startswith('animmotion '): continue
            rel = pk.local[a + 8]
            if rel in done: continue
            done.add(rel)
            x, y, z = (float(v) for v in text.split()[1:4])
            new = 'animmotion %.1f %.1f %.1f' % (x * k, y * k, z)
            assert len(new) <= len(text), (text, new)
            o = pk.ds + rel
            d[o:o + len(text)] = (new + '\0' * (len(text) - len(new))).encode('latin1')
            n += 1
open(dst, 'wb').write(d)
print('%s: scaled %d animmotion keys by %.2f' % (os.path.basename(src), n, k))
