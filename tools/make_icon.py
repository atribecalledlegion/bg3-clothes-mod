"""Render the inventory icon from the garment mesh and the item's built base colour.

    python tools/make_icon.py <item>        (needs build/work/<item>/built_masculine_BM.png)

Icon delivery: BG3 resolves an item's Icon key from the shared atlases first, then from
loose per-icon DDS files. Mods can use the loose route -- TutorialChestSummoning does
exactly this and its icon works -- which avoids having to build an atlas.
  Tooltips/Icons          380x380, no mip chain   (mouse/keyboard UI)
  ControllerUIIcons       144x144, no mip chain   (controller UI)
Vanilla ships the controller one as BC7, which ImageMagick cannot write; DXT5 is used
for both, and the engine reads the format from the DDS header.
"""
import os, subprocess, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import item as itemlib
from meshbake import mesh_arrays, render


def main():
    it = itemlib.load()
    s = it.garment['sets']['masculine']
    built = os.path.join(it.work, 'built_masculine_BM.png')
    if not os.path.exists(built):
        raise SystemExit('%s missing -- run the art step first' % built)
    tex = np.asarray(Image.open(built).convert('RGB')).astype(np.float32) / 255
    P, N, UV = mesh_arrays(*s['mesh'])
    col, alpha = render(P, UV, tex, it.get('icon_view', 'back'), size=900, pad_frac=0.0)

    # soft top-lit gradient, overlay-blended, so the silhouette reads with some depth
    g = np.linspace(0.82, 0.45, col.shape[0], dtype=np.float32)[:, None, None]
    shaded = np.where(col < 0.5, 2 * col * g, 1 - 2 * (1 - col) * (1 - g))
    # A near-black garment disappears on the dark inventory UI; "icon_lift" (0..1) blends
    # the whole icon toward white so the silhouette stays readable.
    lift = float(it.get('icon_lift', 0.0))
    shaded = shaded * (1 - lift) + lift
    rgba = np.dstack([np.clip(shaded, 0, 1), alpha])
    work = os.path.join(it.work, 'icon.png')
    Image.fromarray((rgba * 255 + 0.5).astype(np.uint8), 'RGBA').save(work)

    gui = '%s/Public/Game/GUI/Assets' % it.src
    for sub, inner, outer in (('Tooltips/Icons', 330, 380),
                              ('ControllerUIIcons/skills_png', 126, 144)):
        out = '%s/%s/%s.DDS' % (gui, sub, it.icon)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        subprocess.run([itemlib.MAGICK, work, '-trim', '+repage', '-resize', '%dx%d' % (inner, inner),
                        '-background', 'none', '-gravity', 'center', '-extent', '%dx%d' % (outer, outer),
                        '-define', 'dds:compression=dxt5', '-define', 'dds:mipmaps=0', out], check=True)
        print('wrote', out)


if __name__ == '__main__':
    main()
