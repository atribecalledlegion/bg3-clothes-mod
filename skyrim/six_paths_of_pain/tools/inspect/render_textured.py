"""Front + back view of SSE .nif meshes with their diffuse texture sampled per pixel (flat-lit, no shading).
For checking where texture regions land on a garment.

Usage: render_textured.py out.png mesh.nif=texture.png [mesh2.nif=texture2.png ...]
  The texture is used for every shape of that mesh (only shapes whose UVs cover it make sense).
"""
import os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
import render_nif as R, uv_masks as U

S, W, H = 6, 70, 140                        # pixels per unit; view window (units) centred on x, z 0..140
out = sys.argv[1]
views = []
for back in (False, True):
    img = np.full((H * S, W * S, 3), 235, np.uint8); zb = np.full((H * S, W * S), -1e9)
    for arg in sys.argv[2:]:
        mesh, tex = arg.split('=')
        T = np.asarray(Image.open(tex).convert('RGB')); th, tw = T.shape[:2]
        uvs = {n: u for n, u, t in U.shape_uvs(mesh)}
        for name, pos, tris, _ in R.shapes_of(mesh):
            if name not in uvs or len(uvs[name]) != len(pos): continue
            uv = uvs[name]
            x = (pos[:, 0] * (1 if back else -1) + W / 2) * S; y = (H - pos[:, 2]) * S
            d = pos[:, 1] * (-1 if back else 1)
            for t in tris:
                sx, sy = x[t], y[t]
                x0, x1 = int(max(sx.min(), 0)), int(min(sx.max() + 1, W * S)); y0, y1 = int(max(sy.min(), 0)), int(min(sy.max() + 1, H * S))
                if x0 >= x1 or y0 >= y1: continue
                a = np.array([[sx[1] - sx[0], sx[2] - sx[0]], [sy[1] - sy[0], sy[2] - sy[0]]])
                if abs(np.linalg.det(a)) < 1e-9: continue
                ia = np.linalg.inv(a)
                gx, gy = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
                b1 = ia[0, 0] * (gx - sx[0]) + ia[0, 1] * (gy - sy[0]); b2 = ia[1, 0] * (gx - sx[0]) + ia[1, 1] * (gy - sy[0])
                b0 = 1 - b1 - b2; inside = (b0 >= 0) & (b1 >= 0) & (b2 >= 0)
                if not inside.any(): continue
                dd = b0 * d[t[0]] + b1 * d[t[1]] + b2 * d[t[2]]
                zs = zb[y0:y1, x0:x1]; m = inside & (dd > zs)
                if not m.any(): continue
                u = b0 * uv[t[0], 0] + b1 * uv[t[1], 0] + b2 * uv[t[2], 0]; v = b0 * uv[t[0], 1] + b1 * uv[t[1], 1] + b2 * uv[t[2], 1]
                px = np.clip((u % 1) * tw, 0, tw - 1).astype(int); py = np.clip((v % 1) * th, 0, th - 1).astype(int)
                zs[m] = dd[m]; img[y0:y1, x0:x1][m] = T[py[m], px[m]]
    views.append(img)
Image.fromarray(np.concatenate(views, 1)).save(out); print('wrote', out)
