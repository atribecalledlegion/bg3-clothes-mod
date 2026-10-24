"""Ronin Purple FX: the shared colour rule and DDS writing used by every pass.

Blue hues (HUE_LO..HUE_HI deg) move to Kamui purple (PURPLE, keeping SPREAD of the original variety); saturation and
brightness are kept, and whites, greys, reds and golds stay. purple() works on one colour (HDR allowed), shift() on
an RGBA pixel array. write_dds() keeps the source's mip count (Pillow writes one level; the chain is assembled here).
"""
import colorsys, io, os, struct
import numpy as np
from PIL import Image

HUE_LO, HUE_HI = 150.0, 265.0        # cyan .. blue-violet
PURPLE = 282.0                        # Kamui purple
SPREAD = 0.3
MIN_SAT = 0.15


def purple(c):
    """One colour (3 floats, may exceed 1.0) -> (new colour, moved?)."""
    m = max(c)
    if m <= 0:
        return c, False
    h, l, s = colorsys.rgb_to_hls(*[max(v, 0.0) / m for v in c])
    deg = h * 360.0
    if s < MIN_SAT or not (HUE_LO <= deg <= HUE_HI):
        return c, False
    nh = (PURPLE + (deg - 215.0) * SPREAD) % 360.0
    r, g, b = colorsys.hls_to_rgb(nh / 360.0, l, s)
    return (r * m, g * m, b * m), True


def shift(rgba):
    """uint8 RGBA array -> the same with blue pixels turned purple (alpha untouched)."""
    a = rgba.astype(np.float32) / 255.0
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx = np.max(a[..., :3], axis=-1); mn = np.min(a[..., :3], axis=-1); d = mx - mn
    l = (mx + mn) / 2
    s = np.where(d == 0, 0, d / np.maximum(1e-6, 1 - np.abs(2 * l - 1)))
    m = d > 0
    sd = np.maximum(d, 1e-6)
    rc = np.where(m & (mx == r), ((g - b) / sd) % 6, 0)
    gc = np.where(m & (mx == g) & (mx != r), (b - r) / sd + 2, 0)
    bc = np.where(m & (mx == b) & (mx != r) & (mx != g), (r - g) / sd + 4, 0)
    h = (rc + gc + bc) * 60.0
    move = (s >= MIN_SAT) & (h >= HUE_LO) & (h <= HUE_HI)
    nh = np.where(move, (PURPLE + (h - 215.0) * SPREAD) % 360.0, h)
    c = (1 - np.abs(2 * l - 1)) * s
    x = c * (1 - np.abs((nh / 60.0) % 2 - 1))
    mm = l - c / 2
    seg = (nh // 60).astype(int) % 6
    segs = [seg == k for k in range(6)]
    rr = np.select(segs, [c, x, 0, 0, x, c])
    gg = np.select(segs, [x, c, c, x, 0, 0])
    bb = np.select(segs, [0, 0, x, c, c, x])
    out = a.copy()
    out[..., 0] = np.where(move, rr + mm, r)
    out[..., 1] = np.where(move, gg + mm, g)
    out[..., 2] = np.where(move, bb + mm, b)
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)


def dds_info(path):
    h = open(path, 'rb').read(148)
    flags, height, width = struct.unpack_from('<III', h, 8)
    mips = struct.unpack_from('<I', h, 28)[0] if flags & 0x20000 else 1
    return width, height, max(1, mips), h[84:88]


def _encode(img, fmt):
    buf = io.BytesIO()
    if fmt == 'RGBA':
        img.save(buf, format='DDS')
    else:
        img.save(buf, format='DDS', pixel_format=fmt)
    return buf.getvalue()


def write_dds(img, mips, fmt, dst):
    """fmt: 'DXT1', 'DXT5' or 'RGBA' (uncompressed). Writes `mips` levels like the source."""
    levels = [img]
    while len(levels) < mips and max(levels[-1].size) > 1:
        w, h = levels[-1].size
        levels.append(levels[-1].resize((max(1, w // 2), max(1, h // 2)), Image.LANCZOS))
    blobs = [_encode(lv, fmt) for lv in levels]
    extra = 20 if blobs[0][84:88] == b'DX10' else 0
    head = bytearray(blobs[0][:128 + extra])
    if len(levels) > 1:
        struct.pack_into('<I', head, 8, struct.unpack_from('<I', head, 8)[0] | 0x20000)       # DDSD_MIPMAPCOUNT
        struct.pack_into('<I', head, 28, len(levels))
        struct.pack_into('<I', head, 108, struct.unpack_from('<I', head, 108)[0] | 0x400008)  # COMPLEX | MIPMAP
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, 'wb').write(bytes(head) + b''.join(b[128 + extra:] for b in blobs))
