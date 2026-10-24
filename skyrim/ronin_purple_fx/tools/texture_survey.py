"""Which textures the Vergil effects use carry blue in the pixels themselves (palettes and coloured sources).
Reads the vfx inventory JSON, resolves each referenced texture to the highest-priority Vergil mod that ships it,
and reports the share of saturated blue pixels. Vanilla-path textures not shipped by a Vergil mod are listed apart.
usage: texture_survey.py <inventory json> <out json> <mod dir, highest priority first>..."""
import colorsys, json, os, sys
from PIL import Image

rows = json.load(open(sys.argv[1]))
mods = sys.argv[3:]


def norm(p):
    p = p.replace('/', '\\').lower()
    i = p.find('textures\\')
    return p[i:] if i >= 0 else ('textures\\' + p if p else '')


refs = {}
for r in rows:
    for s in r.get('shaders', []):
        for key, kind in (('palette', 'palette'), ('src', 'source')):
            t = norm(s.get(key, ''))
            if t and (kind == 'source' or s.get('pal_colour')):
                refs.setdefault(t, set()).add(kind)

index = {}
for m in mods:
    for dp, dn, fn in os.walk(m):
        for f in fn:
            if f.lower().endswith('.dds'):
                rel = os.path.relpath(os.path.join(dp, f), m).replace('/', '\\').lower()
                index.setdefault(rel, os.path.join(dp, f))


def blue_share(path):
    im = Image.open(path).convert('RGBA')
    im.thumbnail((64, 64))
    px = [p for p in im.getdata() if p[3] > 8 and max(p[:3]) > 24]
    if not px:
        return 0.0, 0
    blue = 0
    for r, g, b, a in px:
        h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        if s > 0.25 and 150 <= h * 360 <= 265:
            blue += 1
    return blue / len(px), len(px)


out = {'mod': {}, 'vanilla': sorted(t for t in refs if t not in index)}
for t, kinds in sorted(refs.items()):
    if t in index:
        try:
            share, n = blue_share(index[t])
        except Exception as e:
            share, n = -1, str(e)[:40]
        out['mod'][t] = {'path': index[t], 'kinds': sorted(kinds), 'blue': round(share, 2)}
json.dump(out, open(sys.argv[2], 'w'), indent=1)
blue = {t: v for t, v in out['mod'].items() if v['blue'] >= 0.2}
print('referenced %d, shipped by Vergil mods %d (%d blue), vanilla paths %d' % (len(refs), len(out['mod']), len(blue), len(out['vanilla'])))
for t, v in sorted(blue.items(), key=lambda kv: -kv[1]['blue']):
    print('  %.2f %-8s %s' % (v['blue'], '/'.join(v['kinds']), t))
print('vanilla-path:', ', '.join(out['vanilla']))
