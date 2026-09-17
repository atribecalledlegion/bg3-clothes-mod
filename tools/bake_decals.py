"""Bake an item's base colour and mask textures from decals placed on the garment in 3D.

    python tools/bake_decals.py <item> [--preview-only]

Reads the "bake" block of items/<item>/item.json:

    "bake": {
      "ground": "#141416",            base colour of the whole garment
      "mask":   "#0000FF",            one MSKcloth slot for the whole garment (see below)
      "supersample": 2,               bake at 2x and box-filter down: anti-aliased edges
      "images": { "cloud": "items/.../akatsuki_cloud.png" },
      "decals": [
        { "image": "cloud", "face": "back", "x": 0.0, "y": 0.78, "size": 0.26, "rot": 0 }
      ]
    }

Decal coordinates are relative to the garment, so one layout fits both body types:
  face   "back" or "front" -- which way the projector points
  x      -1 .. 1 across the garment, as the viewer of that face sees it (-1 = viewer's left)
  y       0 .. 1 from hem to collar
  size   decal width as a fraction of garment height
  rot    degrees, clockwise as seen by the viewer
  mirror flip horizontally
  only   "masculine" or "feminine": one texture set only. The robe's front wrap opens on
         the viewer's right on the masculine mesh and the left on the feminine one, so
         front skirt clouds have to dodge a different slit on each.

Writes, per texture set:
  <textures>/<bm>.DDS and <msk>.DDS          game textures
  build/work/<item>/built_<set>_BM.png        for the icon
  build/work/<item>/preview_<set>.png         front / back / side renders to check layout

The mask is one flat slot. The vanilla MSKcloth splits the garment across Cloth_/Leather_/
Metal_ slots, and the shader gives each a different surface response, so their boundaries
show as seams even with every slot colour white (the lines through the Obito crest). A
cloak printed edge to edge has nowhere to hide those, so the whole garment is one slot.
"""
import os, subprocess, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import item as itemlib
from meshbake import mesh_arrays, raster_uv, garment_frame, apply_decals, pad, render

S = 2048


def hexrgb(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def load_image(path):
    im = np.asarray(Image.open(path).convert('RGBA')).astype(np.float32) / 255
    # Premultiplied: bilinear sampling of straight alpha drags the transparent pixels'
    # (meaningless) colour into the decal's edge.
    im[..., :3] *= im[..., 3:4]
    return im


def downsample(img, k):
    if k == 1:
        return img
    h, w = img.shape[0] // k, img.shape[1] // k
    return img[:h * k, :w * k].reshape(h, k, w, k, -1).mean((1, 3))


def dds(png, out, fmt='dxt1'):
    subprocess.run([itemlib.MAGICK, png, '-alpha', 'off', '-define', 'dds:compression=' + fmt,
                    '-define', 'dds:mipmaps=12', out], check=True)


def preview(P, N, UV, tex, path):
    views = []
    for face in ('front', 'back', 'side'):
        o, a = render(P, UV, tex, face, size=700, N=N)
        o[a == 0] = 0.55
        views.append(o)
    Image.fromarray((np.concatenate(views, 1) * 255 + 0.5).astype(np.uint8)).save(path)


def main():
    it = itemlib.load()
    cfg = it['bake']
    preview_only = '--preview-only' in sys.argv
    k = int(cfg.get('supersample', 2))
    ground = hexrgb(cfg.get('ground', '#141416'))
    images = {n: load_image(p) for n, p in cfg['images'].items()}
    os.makedirs(it.textures, exist_ok=True)

    for tag, s, _ in it.sets():
        dae, geom = s['mesh']
        P, N, UV = mesh_arrays(dae, geom)
        frame = garment_frame(P)
        HS = S * k
        pos, nrm, cov, shared = raster_uv(P, N, UV, HS)
        base = np.empty((HS, HS, 3), np.float32)
        base[:] = ground
        decals = [d for d in cfg['decals'] if d.get('only', tag) == tag]
        apply_decals(base, pos, nrm, cov, frame, decals, images,
                     min_facing=cfg.get('min_facing', 0.35))
        base = pad(base, cov, iterations=8 * k)
        del pos, nrm
        base = downsample(base, k)
        print('%-10s %s  coverage %.0f%%  shared-UV texels %d  %d decals'
              % (tag, geom, cov.mean() * 100, shared.sum() // (k * k), len(decals)))

        built = os.path.join(it.work, 'built_%s_BM.png' % tag)
        Image.fromarray((np.clip(base, 0, 1) * 255 + 0.5).astype(np.uint8)).save(built)
        preview(P, N, UV, base, os.path.join(it.work, 'preview_%s.png' % tag))
        if preview_only:
            continue

        dds(built, os.path.join(it.textures, s['bm']))
        mask = os.path.join(it.work, 'mask_%s.png' % tag)
        subprocess.run([itemlib.MAGICK, '-size', '%dx%d' % (S, S), 'xc:' + cfg.get('mask', '#0000FF'),
                        'PNG24:' + mask], check=True)
        dds(mask, os.path.join(it.textures, s['msk']))
        print('           wrote %s, %s' % (s['bm'], s['msk']))


if __name__ == '__main__':
    main()
