"""Flatten the robe's back panel to a single mask slot.

The vanilla MSKcloth splits the back panel across four ID colours (blue 46%, orange 40%,
violet 7%, red 6%). Those are not just colours: the slots are grouped Cloth_/Leather_/
Metal_, and the shader gives each a different surface response. So even with every colour
forced to white, the boundaries still show as seams -- the vanilla robe's trim -- and two
of them run right across the top of the crest.

Painting the whole back panel one slot removes them. The region painted is the back
panel's own UV triangles, rasterised from the mesh, so nothing outside the panel changes.

-alpha off before encoding matters: DXT1 has a 1-bit alpha punch-through mode, and letting
ImageMagick choose it introduced ~2700 black block endpoints on a previous attempt. Black
texels match no slot and render the surface black.
"""
import sys, os, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uvmap import load

M = os.environ.get('MAGICK', r"C:/Program Files/ImageMagick-7.1.2-Q16-HDRI/magick.exe")
S = 2048
FILL = '#0000FF'          # the slot the crest already sits on

def panel_tris(dae, geom):
    tris = load(dae, geom)
    def c(t, i): return sum(v[0][i] for v in t)/3
    def nz(t):  return sum(v[1][2] for v in t)/3
    ys = [v[0][1] for t in tris for v in t]
    lo, hi = min(ys), max(ys)
    sel = [t for t in tris if nz(t) > 0.5 and c(t,2) > 0.03
           and lo + 0.55*(hi-lo) <= c(t,1) <= lo + 0.99*(hi-lo)]
    parent = list(range(len(sel)))
    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a
    seen = {}
    for i, t in enumerate(sel):
        for _, _, uv in t:
            k = (round(uv[0],5), round(uv[1],5))
            if k in seen:
                ra, rb = find(i), find(seen[k])
                if ra != rb: parent[ra] = rb
            else: seen[k] = i
    groups = {}
    for i in range(len(sel)): groups.setdefault(find(i), []).append(sel[i])
    return max(groups.values(), key=len)

def raster(tris):
    buf = bytearray(S*S)
    for t in tris:
        p = [(v[2][0]*(S-1), (1.0-v[2][1])*(S-1)) for v in t]
        ys = [q[1] for q in p]
        for y in range(max(0,int(min(ys))), min(S-1,int(max(ys))+1)+1):
            xs = []
            for i in range(3):
                (xa,ya),(xb,yb) = p[i], p[(i+1)%3]
                if (ya <= y < yb) or (yb <= y < ya):
                    xs.append(xa + (y-ya)*(xb-xa)/(yb-ya))
            if len(xs) < 2: continue
            for x in range(max(0,int(min(xs))), min(S-1,int(max(xs)))+1):
                buf[y*S+x] = 255
    return buf

def main():
    dae, geom, vmask, out = sys.argv[1:5]
    tris = panel_tris(dae, geom)
    open('art/source/_panel.gray','wb').write(bytes(raster(tris)))
    # dilate so UV seams at the panel edge are covered too
    subprocess.run([M, '-size', '%dx%d' % (S,S), '-depth', '8', 'GRAY:art/source/_panel.gray',
                    '-morphology', 'Dilate', 'Disk:3', '-threshold', '50%',
                    'PNG24:art/source/_panel.png'], check=True)
    subprocess.run([M, vmask,
                    '(', '-size', '%dx%d' % (S,S), 'xc:'+FILL, ')',
                    'art/source/_panel.png',
                    '-compose', 'Over', '-composite',
                    '-alpha', 'off',
                    '-define', 'dds:compression=dxt1', '-define', 'dds:mipmaps=12', out], check=True)
    os.remove('art/source/_panel.gray'); os.remove('art/source/_panel.png')
    print('patched %s  (%d back-panel triangles flattened to %s)' % (out, len(tris), FILL))

if __name__ == '__main__':
    main()
