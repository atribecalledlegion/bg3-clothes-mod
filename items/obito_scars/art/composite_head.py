"""Composite a scar height layer into the vanilla human-male head maps and write the DDS files.

  python items/obito_scars/art/composite_head.py                                # NM only, head A
  python items/obito_scars/art/composite_head.py --head C                        # another head
  python items/obito_scars/art/composite_head.py --tag marker \\
        --layer items/obito_scars/art/out/head_a/marker_height.png --adjust HMVY.G=-90   # marker test
  python items/obito_scars/art/composite_head.py --adjust CLEA.R=-40 --adjust HMVY.G=-30

Reads  extracted/head_hum_m_<x>/HUM_M_NKD_Head_<X>_{NM,CLEA,HMVY}.DDS  (fetch_vanilla.py)
and a grayscale layer (white = groove). Writes out/head_<x>/build_<tag>/dds/ with the SAME file names,
and only the maps that changed; .../png/ holds the same maps as PNG for inspection.

NM  is DXT5 with the tangent-space normal in A (x) and G (y), R = 0, B ~ 255 (measured on the
    vanilla map). The layer is turned into a small height field, its slope is added to the
    vanilla normal, and R and B are left alone.
    Two facts are NOT established from the files and are what the marker test settles:
      --invert   flips groove <-> ridge
      --swap     swaps which of A / G carries x and which y
--adjust MAP.CH=delta adds delta (0-255 units) x the soft mask to one channel of CLEA or HMVY.
    What those channels do is not identified; change one at a time, exaggerated, to find out.
"""
import os, sys, struct, argparse, subprocess
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import item as itemlib

sys.path.insert(0, HERE)
import headmesh as hm
I = {}                                                      # the chosen head's names and folders (set in main)
FMT = {'NM': 'dxt5', 'CLEA': 'dxt5', 'HMVY': 'dxt5'}       # vanilla formats (measured)
CH = {'R': 0, 'G': 1, 'B': 2, 'A': 3}


def fname(m):
    return '%s_%s.DDS' % (I['stem'], m)


def blur(a, sigma):
    if sigma <= 0:
        return a
    r = int(3 * sigma) + 1
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2); k /= k.sum()
    a = np.apply_along_axis(lambda v: np.convolve(np.pad(v, r, mode='edge'), k, mode='valid'), 1, a)
    return np.apply_along_axis(lambda v: np.convolve(np.pad(v, r, mode='edge'), k, mode='valid'), 0, a)


def header(path):
    d = open(path, 'rb').read(128)
    h, w, _, _, mips = struct.unpack_from('<5I', d, 12)
    return dict(w=w, h=h, mips=mips, fourcc=d[84:88].decode('latin1'), size=os.path.getsize(path))


def load(m):
    return np.array(Image.open(os.path.join(I['src'], fname(m))).convert('RGBA')).astype(np.float32)


def write_dds(arr, m, tag):
    d = os.path.join(I['out'], 'build_' + tag)
    os.makedirs(os.path.join(d, 'png'), exist_ok=True); os.makedirs(os.path.join(d, 'dds'), exist_ok=True)
    png = os.path.join(d, 'png', '%s_%s.png' % (I['stem'], m))
    dds = os.path.join(d, 'dds', fname(m))
    Image.fromarray(np.clip(np.rint(arr), 0, 255).astype(np.uint8), 'RGBA').save(png)
    subprocess.run([itemlib.MAGICK, png, '-define', 'dds:compression=' + FMT[m],
                    '-define', 'dds:mipmaps=12', dds], check=True)
    return dds


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--head', default='A', choices=hm.HEADS, help='human-male head (A-I are player-selectable)')
    ap.add_argument('--layer', help='height layer PNG (default: out/head_<x>/scar_height.png)')
    ap.add_argument('--tag', default='scars', help='output goes to out/head_<x>/build_<tag>/ (default: scars)')
    ap.add_argument('--depth', type=float, default=4.0, help='groove depth in texels (0.1 mm each); default 4 (the approved look; 6 was tried and set aside)')
    ap.add_argument('--blur', type=float, default=1.5, help='softening of the height layer, texels; default 1.5 (the approved look; 1.0 was tried)')
    ap.add_argument('--mask-blur', type=float, default=3.0, help='softening of the CLEA/HMVY mask, texels')
    ap.add_argument('--invert', action='store_true', help='flip groove <-> ridge')
    ap.add_argument('--swap', action='store_true', help='swap the roles of A and G in the normal map')
    ap.add_argument('--adjust', action='append', default=[], metavar='MAP.CH=DELTA',
                    help='e.g. HMVY.G=-60 or CLEA.R=-40 (repeatable)')
    a = ap.parse_args()
    I.update(hm.info(a.head))
    layer_path = a.layer or os.path.join(I['out'], 'scar_height.png')

    h = np.array(Image.open(layer_path).convert('L')).astype(np.float32) / 255.0
    if h.shape != (2048, 2048):
        raise SystemExit('layer must be 2048x2048, got %s' % (h.shape,))
    hb = blur(h, a.blur)
    mask = np.clip(blur(h, a.mask_blur), 0, 1)

    # ---- NM: add the layer's slope to the vanilla tangent-space normal
    nm = load('NM')
    H = -a.depth * hb                                   # groove = lower
    gy, gx = np.gradient(H)                             # per texel; rows = y, cols = x
    dx, dy = -gx, -gy
    if a.invert:
        dx, dy = -dx, -dy
    ix, iy = (1, 3) if a.swap else (3, 1)               # channel carrying x, y (default: x=A, y=G)
    X = (nm[..., ix] - 127.5) / 127.5 + dx
    Y = (nm[..., iy] - 127.5) / 127.5 + dy
    L = np.sqrt(X * X + Y * Y); over = L > 0.98
    X[over] *= 0.98 / L[over]; Y[over] *= 0.98 / L[over]
    new_nm = nm.copy()
    new_nm[..., ix] = 127.5 + 127.5 * X
    new_nm[..., iy] = 127.5 + 127.5 * Y                 # R (=0) and B (~255) untouched
    maps = {'NM': new_nm}

    # ---- CLEA / HMVY channel adjustments
    for spec in a.adjust:
        key, val = spec.split('=')
        m, c = key.split('.')
        if m not in ('CLEA', 'HMVY') or c not in CH:
            raise SystemExit('--adjust wants CLEA|HMVY . R|G|B|A = number, got %r' % spec)
        arr = maps.get(m)
        if arr is None:
            arr = maps[m] = load(m)
        arr[..., CH[c]] = np.clip(arr[..., CH[c]] + float(val) * mask, 0, 255)

    # ---- write, then check every file against the vanilla one
    print('layer %s: %d texels lit  | NM depth %.1f  blur %.1f  invert=%s swap=%s'
          % (os.path.basename(layer_path), int((h > 0.05).sum()), a.depth, a.blur, a.invert, a.swap))
    ok = True
    for m, arr in maps.items():
        dds = write_dds(arr, m, a.tag)
        hv, hn = header(os.path.join(I['src'], fname(m))), header(dds)
        same = hv == hn
        ok &= same
        dec = np.array(Image.open(dds).convert('RGBA')).astype(np.float32)
        van = load(m)
        diff = np.abs(dec - van).mean(-1)
        on, off = mask > 0.3, mask < 0.001
        print('%-5s %s %dx%d mips=%d %d bytes  header %s vanilla | mean change: on scar %.1f, elsewhere %.2f (encoding noise)'
              % (m, hn['fourcc'], hn['w'], hn['h'], hn['mips'], hn['size'],
                 'MATCHES' if same else 'DIFFERS FROM', diff[on].mean() if on.any() else 0, diff[off].mean()))
    print('%s :' % os.path.join(I['out'], 'build_' + a.tag, 'dds'),
          ', '.join(sorted(os.listdir(os.path.join(I['out'], 'build_' + a.tag, 'dds')))))
    if not ok:
        raise SystemExit('a DDS header differs from vanilla; do not ship these')


if __name__ == '__main__':
    main()
