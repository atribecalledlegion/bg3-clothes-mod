"""Draw Obito's scars as a grayscale HEIGHT layer in the head's UV sheet.

  python items/obito_scars/art/draw_scar_layer.py                # the scars, head A
  python items/obito_scars/art/draw_scar_layer.py --marker       # asymmetric test marks
  python items/obito_scars/art/draw_scar_layer.py --head C       # another head (A-I)
  python items/obito_scars/art/draw_scar_layer.py --half left    # scars on the other half

White = groove centre, black = untouched skin. Lines are drawn on the FACE in millimetres and
warped into UV space with the local stretch compensated, so widths stay even on the curved
cheek. Writes out/head_<x>/scar_height.png (or marker_height.png) and a front-view preview.

Face coordinates: s = distance outward from the centreline, y = height in metres. The scarred
side is +x in the converted mesh; seen from the front that is the viewer's left, as in the
reference art. --half picks which half of the SHEET carries the marks.
MEASURED IN GAME (marker test, 2026-09-19): marks drawn with --half right (u > 0.5) appeared on the
character's LEFT, i.e. the game is mirrored relative to the converted mesh. So the character's
right is --half left (u < 0.5), which is the default. The front-view preview is in the mesh's frame
so the preview images are FLIPPED to the game's orientation: the character's right is the picture's left.
"""
import os, sys, argparse
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import headmesh as hm

A_EYE_S, A_EYE_Y, A_EYE_MOUTH = 0.0304, 1.8183, 0.0750      # Head A's measured eye and eye-to-mouth distance (the design's frame)
EYE_S, EYE_Y = 0.0306, 1.815                 # the design is laid out on this eye position (head 'Oscar');
                                             # other heads shift it to their own measured eye


# ---------------------------------------------------------------- curve building
def bez(p0, p1, p2, n=None):
    """Quadratic bezier through 3 control points (s, y) -> dense polyline."""
    p0, p1, p2 = map(np.asarray, (p0, p1, p2))
    L = np.linalg.norm(p1 - p0) + np.linalg.norm(p2 - p1)
    t = np.linspace(0, 1, max(int(L / 0.00025), 8))[:, None]
    return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t ** 2 * p2


def ring(r, a0, a1, cy=EYE_Y, cs=EYE_S, squash=0.85):
    """Arc of a ring around the eye; angles in degrees from outward (+s), counter-clockwise."""
    a = np.radians(np.linspace(a0, a1, max(int(abs(a1 - a0) / 180 * np.pi * r / 0.00025), 8)))
    return np.stack([cs + r * np.cos(a), cy + squash * r * np.sin(a)], 1)


def design():
    """The scar pattern, read off the reference art. (s, y) in metres; (points, width scale)."""
    c = []
    # a small crescent right under the eye, then concentric C-shapes around it, open toward
    # the nose. Their tops stop at y ~ 1.855 so they never reach the forehead strokes.
    # (v3: the inner ends stop ~20 degrees sooner, leaving the corner beside the nose to the short strokes
    # the reference has there)
    for r, a0, a1, w, sq in [(0.014, -165, -15, 0.7, 0.7), (0.021, -105, 70, 1.0, 0.85),
                             (0.029, -108, 68, 1.0, 0.85), (0.038, -110, 58, 0.95, 0.85),
                             (0.048, -72, 50, 0.9, 0.85), (0.059, -62, 45, 0.85, 0.85)]:   # v3: outer two keep only their outer-side arcs
        c.append((ring(r, a0, a1, squash=sq), w))
    # long cheek strokes: outer cheek sweeping up and in, ending short of the nose and of the
    # mouth-to-chin stroke (s >= 0.033) so nothing crosses
    for a, m, b, w in [((0.071, 1.756), (0.052, 1.741), (0.034, 1.758), 0.9),
                       ((0.069, 1.738), (0.050, 1.724), (0.034, 1.742), 0.9),
                       ((0.066, 1.720), (0.056, 1.712), (0.049, 1.714), 0.85)]:
        c.append((bez(a, m, b), w))
    # v2 additions, read off the reference art (2026-09-19): two lines between the cheek strokes.
    # (A steep stroke toward the chin, like the short ones beside the mouth in the close-up, was tried
    # and dropped: there is no room for it without touching the cheek strokes. Revisit with more photos.)
    for a, m, b, w in [((0.066, 1.747), (0.050, 1.733), (0.036, 1.750), 0.85),
                       ((0.062, 1.729), (0.048, 1.716), (0.036, 1.733), 0.8)]:
        c.append((bez(a, m, b), w))
    # v2: longer forehead lines that run down almost to the inner brow, as in the references
    for a, m, b, w in [((0.064, 1.866), (0.046, 1.860), (0.020, 1.845), 0.85),
                       ((0.058, 1.856), (0.042, 1.851), (0.018, 1.839), 0.8)]:
        c.append((bez(a, m, b), w))
    # jaw line, and the vertical stroke from the mouth corner down toward the chin
    c.append((bez((0.062, 1.703), (0.048, 1.697), (0.038, 1.699)), 0.8))
    c.append((bez((0.024, 1.736), (0.022, 1.718), (0.019, 1.704)), 0.9))
    # forehead: strokes running down toward the brow, inner ends short of the centreline
    for a, m, b, w in [((0.068, 1.892), (0.052, 1.885), (0.032, 1.868), 0.8),
                       ((0.066, 1.880), (0.050, 1.873), (0.030, 1.860), 0.8)]:
        c.append((bez(a, m, b), w))
    return c



# ---------------------------------------------------------------- v3: lines traced from a reference close-up
# Scar lines read off a sharp front-on close-up (750x1097 px, the character's right side is the picture's
# left), using a 50 px grid over the image. (x, y) are pixels of that image.
REF = {
    'f1': [(219, 135), (262, 179)], 'f2': [(216, 210), (269, 247)], 'f3': [(119, 210), (169, 260)],
    'f4': [(187, 279), (244, 322)],
    'i1': [(228, 476), (275, 447)], 'i2': [(241, 501), (284, 470)], 'i3': [(234, 551), (275, 513)],
    'iv': [(304, 429), (304, 522)],
    'S': [(97, 741), (137, 669), (206, 622), (245, 590)],           # inner tip trimmed so it clears the eye rings
    'l1': [(209, 675), (272, 588)], 'l2': [(137, 785), (187, 704)], 'l3': [(178, 841), (216, 751)],
    'chin': [(234, 897), (269, 819), (262, 772)],
}
REF_CX, REF_EYE_X, REF_EDGE_X = 343, 166, 44            # centreline, scarred eye, outer face edge (px)
REF_EYE_Y, REF_MOUTH_Y, REF_CHIN_Y = 391, 766, 950      # eye, lip line, chin (px)


def ref_to_face(px, py, eye, mouth_y, chin_y=1.694, edge_s=0.070):
    """Piecewise-linear map from the cartoon's landmarks to this head's measured ones."""
    s = float(np.interp(px, [REF_EDGE_X, REF_EYE_X, REF_CX], [edge_s, eye[0], 0.0]))
    y = float(np.interp(py, [-1e3, REF_EYE_Y, REF_MOUTH_Y, REF_CHIN_Y, 2e3],
                        [eye[1] + (REF_EYE_Y + 1e3) * 0.0002, eye[1], mouth_y, chin_y, chin_y - 1e3 * 0.0003]))
    return s, y


def spline(pts, step=0.00025):
    """Catmull-Rom through the points, sampled every 0.25 mm."""
    P = np.asarray(pts, float)
    if len(P) == 2:
        n = max(int(np.linalg.norm(P[1] - P[0]) / step), 4); t = np.linspace(0, 1, n)[:, None]
        return P[0] * (1 - t) + P[1] * t
    ext = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]]); out = []
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        n = max(int(np.linalg.norm(p2 - p1) / step), 4)
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t ** 2
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P[-1])
    return np.array(out)


def design_v3(eye, mouth_y, shift):
    """v2's lines plus the traced ones. Order = priority: a line is dropped if it would come within 4 mm of one
    already accepted. Kept first: the eye rings and the forehead lines. Then the traced lower-cheek and inner
    lines (the reference has diagonal strokes there, not horizontal arcs). Then v2's remaining cheek arcs."""
    v2 = [(pts + shift, w) for pts, w in design()]
    names = {i: n for i, n in enumerate(['ring1', 'ring2', 'ring3', 'ring4', 'ring5', 'ring6', 'cheekA', 'cheekB', 'cheekC',
                                         'fillM1', 'fillM2', 'foreheadFA', 'foreheadFB', 'jaw', 'chinV', 'forehead_old1',
                                         'forehead_old2'])}
    traced = {n: (spline([ref_to_face(x, y, eye, mouth_y) for x, y in pl]), 0.9) for n, pl in REF.items()}
    order = ([(names[i], v2[i]) for i in (0, 1, 2, 3, 4, 5, 11, 12, 15, 16)] +
             [(n, traced[n]) for n in ('S', 'l1', 'l2', 'l3', 'chin', 'i1', 'i2', 'i3', 'iv')] +
             [(names[i], v2[i]) for i in (6, 7, 9, 10, 8, 13, 14)])
    kept, dropped = [], []
    for name, (pts, w) in order:
        close = [k for k, (kp, _) in kept if np.sqrt(((pts[::4, None, :] - kp[None, ::4, :]) ** 2).sum(-1)).min() < 0.004]
        if close:
            dropped.append((name, close[0]))
        else:
            kept.append((name, (pts, w)))
    return kept, dropped



# ---------------------------------------------------------------- v1 + lines that run out to the ear
EAR_S = 0.12             # design distance (round the head from the centreline) at which the surface reaches the ear plane, eye level


def egg_ring(r, a0, a1, tip, squash=0.85, cs=EYE_S, cy=EYE_Y):
    """A ring around the eye whose outer bulge is stretched by `tip` toward the ear (a pointed oval)."""
    a = np.radians(np.linspace(a0, a1, max(int(abs(a1 - a0) / 180 * np.pi * (r + tip / 2) / 0.00025), 8)))
    c = np.clip(np.cos(a), 0, None) ** 2
    return np.stack([cs + r * np.cos(a) + tip * c, cy + squash * r * np.sin(a) * (1 - 0.35 * c)], 1)


def ring_arms(r, a0, a1, sq, y_lo, y_hi, cut=40, cs=EYE_S, cy=EYE_Y):
    """An outer ring as two arms that run on to the ear at different heights: one under the eye (from the ring's lower
    end), one over it (from its upper end). The outer bulge between +-cut degrees is replaced by the arms."""
    def bez3(p0, p1, p2):
        L = np.linalg.norm(p1 - p0) + np.linalg.norm(p2 - p1); t = np.linspace(0, 1, max(int(L / 0.00025), 8))[:, None]
        return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t ** 2 * p2
    arms = []
    for lo, ang, y_t in ((True, np.linspace(a0, -cut, 200), y_lo), (False, np.linspace(a1, cut, 200), y_hi)):
        a = np.radians(ang)
        arc = np.stack([cs + r * np.cos(a), cy + sq * r * np.sin(a)], 1)
        T = arc[-1] - arc[-6]; T = T / np.linalg.norm(T)                    # heading out toward the ear
        end = np.array([EAR_S + 0.012, y_t])
        arms.append(np.vstack([arc, bez3(arc[-1], arc[-1] + T * 0.024, end)[1:]]))
    return arms


def extend_outer(pts, length):
    """Continue a line past its outer end (the end with the larger s) along its own direction."""
    if pts[0, 0] > pts[-1, 0]:
        pts = pts[::-1]
    T = pts[-1] - pts[-13]; T = T / np.linalg.norm(T)
    n = int(length / 0.00025)
    return np.vstack([pts, pts[-1] + T * (np.arange(1, n + 1)[:, None] * 0.00025)])


def _v1ear_lines(inner_cut=False):
    """The v1 + ear layout as (name, pts, width, opts). inner_cut: the eye rings' inner ends stop ~20 degrees sooner,
    leaving the corner beside the nose free for the short strokes the reference has there."""
    import importlib.machinery
    v1 = importlib.machinery.SourceFileLoader('ds_v1', os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                                     'draw_scar_layer_v1.py.bak')).load_module()
    base = v1.design()                       # rings 0-5, cheek 6-8, jaw 9, chin 10, forehead 11-13
    out = []
    a0 = (-165, -90, -92, -80, -65, -55) if inner_cut else (-165, -125, -130, -130, -122, -110)
    rings = [(0.014, a0[0], -15, 0.7, 0.7), (0.021, a0[1], 70, 1.0, 0.85), (0.029, a0[2], 75, 1.0, 0.85),
             (0.038, a0[3], 72, 0.95, 0.85), (0.048, a0[4], 65, 0.9, 0.85), (0.059, a0[5], 55, 0.85, 0.85)]
    ear_y = {3: (1.810, 1.833), 4: (1.803, 1.845), 5: (1.797, 1.857)}    # where each outer ring's arms meet the ear (lower, upper)
    for i, (r, lo, a1, w, sq) in enumerate(rings):
        if i >= 3:                          # the outer three run on to the ear as two arms each
            for arm, side in zip(ring_arms(r, lo, a1, sq, *ear_y[i]), ('lo', 'hi')):
                out.append(('arm%d%s' % (i, side), arm, w, {'open_end': True}))
        else:
            pts = ring(r, lo, a1, squash=sq) if inner_cut else base[i][0]     # (unchanged from v1 unless the inner ends are cut)
            out.append((('crescent', 'ring1', 'ring2')[i], pts, base[i][1], {}))
    for i, nm in ((6, 'cheekA'), (7, 'cheekB'), (8, 'cheekC'), (9, 'jaw')):   # carried on along their own direction to the ear
        out.append((nm, extend_outer(base[i][0], 0.06), base[i][1], {'open_end': True}))
    for i, nm in ((11, 'fh1'), (12, 'fh2'), (13, 'fh3')):                      # forehead: only a short way (the hair covers the rest)
        out.append((nm, extend_outer(base[i][0], 0.03), base[i][1], {'open_end': True}))
    out.append(('chinV', base[10][0], base[10][1], {}))
    return out


def design_v1ear():
    """The approved v1 layout (14 lines), with the outer arcs and the lines that end at the cheek's edge carried on
    to the ear. Inner rings, the crescent and the chin line are untouched."""
    return [(p, w, o) for _, p, w, o in _v1ear_lines(False)]


def design_full():
    """The whole right half of the face, like the reference pictures. Returns lines in HEAD A's frame (scale afterwards
    for a smaller head). Built from the approved layout plus: forehead lines that run down to the nose bridge, and the
    reference close-up's inner-cheek strokes, S-sweep, steep lower strokes and chin line. Priority order; a line is dropped
    if it would come within 4 mm of one already kept."""
    shiftA = np.array([A_EYE_S - EYE_S, A_EYE_Y - EYE_Y])
    lines = {n: (p + shiftA, w, o) for n, p, w, o in _v1ear_lines(True)}
    eye, mouth_y = (A_EYE_S, A_EYE_Y), A_EYE_Y - A_EYE_MOUTH
    tr = {n: (spline([ref_to_face(x, y, eye, mouth_y) for x, y in pl]), 0.9, {}) for n, pl in REF.items()}
    def bz(a, m, b, w):
        return (bez(a, m, b), w, {})
    # forehead lines from the outer forehead down to the nose bridge (the reference's forehead lines end at the glabella)
    fh = {'FA': bz((0.060, 1.878), (0.040, 1.871), (0.010, 1.852), 0.85),
          'FB': bz((0.058, 1.890), (0.038, 1.884), (0.016, 1.870), 0.85),
          'FC': bz((0.034, 1.866), (0.024, 1.861), (0.006, 1.856), 0.8),
          'FE': bz((0.056, 1.860), (0.040, 1.854), (0.020, 1.846), 0.8)}
    order = (['crescent', 'ring1', 'ring2', 'FA', 'FB', 'FE'] +
             ['arm3lo', 'arm3hi', 'arm4lo', 'arm4hi', 'arm5lo', 'arm5hi'] +
             ['S', 'l1', 'l2', 'l3', 'chin', 'i1', 'i2', 'i3', 'iv', 'FC'] +
             ['cheekA', 'cheekB', 'cheekC', 'jaw', 'chinV'])
    pool = dict(lines); pool.update(tr); pool.update(fh)
    kept, dropped = [], []
    for name in order:
        pts, w, o = pool[name]
        close = [k for k, (kp, _, _) in kept if np.sqrt(((pts[::4, None, :] - kp[None, ::4, :]) ** 2).sum(-1)).min() < 0.004]
        (dropped if close else kept).append((name, close[0]) if close else (name, (pts, w, o)))
    return kept, dropped


def design_combo():
    """Everything in the approved layout, plus the new forehead lines that run down to the nose bridge (they replace the old
    forehead strokes), plus any of the reference close-up's extra strokes that fit WITHOUT touching a line already there.
    Approved lines have priority: nothing from the approved layout is dropped for a new one, so the new forehead lines
    are positioned to clear the arms to the ear. Returns lines in HEAD A's frame (scale afterwards for a smaller head)."""
    shiftA = np.array([A_EYE_S - EYE_S, A_EYE_Y - EYE_Y])
    lines = {n: (p + shiftA, w, o) for n, p, w, o in _v1ear_lines(False)}          # the approved layout, unchanged
    eye, mouth_y = (A_EYE_S, A_EYE_Y), A_EYE_Y - A_EYE_MOUTH
    tr = {n: (spline([ref_to_face(x, y, eye, mouth_y) for x, y in pl]), 0.9, {}) for n, pl in REF.items()}
    def bz(a, m, b, w):
        return (bez(a, m, b), w, {})
    fh = {'FA': bz((0.060, 1.878), (0.040, 1.871), (0.010, 1.852), 0.85),
          'FB': bz((0.058, 1.890), (0.038, 1.884), (0.016, 1.870), 0.85),
          'FE': bz((0.046, 1.862), (0.034, 1.857), (0.018, 1.849), 0.8)}
    keep = ['crescent', 'ring1', 'ring2', 'arm3lo', 'arm3hi', 'arm4lo', 'arm4hi', 'arm5lo', 'arm5hi',
            'cheekA', 'cheekB', 'cheekC', 'jaw', 'chinV']                            # (fh1-fh3, the old forehead strokes, are replaced)
    order = keep + ['FA', 'FB', 'FE'] + ['iv', 'i1', 'i2', 'i3', 'l1', 'l2', 'l3', 'chin', 'S']
    pool = dict(lines); pool.update(tr); pool.update(fh)
    kept, dropped = [], []
    for name in order:
        pts, w, o = pool[name]
        close = [k for k, (kp, _, _) in kept if np.sqrt(((pts[::4, None, :] - kp[None, ::4, :]) ** 2).sum(-1)).min() < 0.004]
        (dropped if close else kept).append((name, close[0]) if close else (name, (pts, w, o)))
    return kept, dropped


def check_crossings(curves, min_mm=4.0):
    """Names pairs of lines that come closer than min_mm anywhere (they would read as crossing)."""
    pts = [c[0][::4] for c in curves]                     # every 1 mm
    bad = []
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            d = np.sqrt(((pts[i][:, None, :] - pts[j][None, :, :]) ** 2).sum(-1)).min()
            if d < min_mm / 1000.0:
                bad.append((i, j, d * 1000))
    return bad


def marker():
    """Test marks on ONE half only: a horizontal bar, a vertical bar, a diagonal bar and a
    ring, in different places, so side, axis order and groove direction can be read in game."""
    def line(a, b):
        return bez(a, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), b)
    return [(line((0.030, 1.850), (0.056, 1.850)), 1.6),          # horizontal, forehead
            (line((0.062, 1.795), (0.062, 1.765)), 1.6),          # vertical, temple/cheek edge
            (line((0.034, 1.742), (0.054, 1.722)), 1.6),          # diagonal, cheek
            (ring(0.011, 0, 360, cy=1.795, cs=0.046, squash=1.0), 1.4)]   # ring, below the eye


# ---------------------------------------------------------------- stamping into UV
Z_STOP = -0.030          # nothing is drawn behind this plane on the side of the head: that is where the ear starts


def stamp(head, layer, pts, wscale, radius_m, sign, rng, gaps=True, open_end=False):
    P = head.P_uv
    size = head.size
    n = len(pts)
    t = np.linspace(0, 1, n)
    # taper both ends; an 'open' line (one that runs on to the ear) is tapered at its inner end only
    env = (np.clip(t / 0.15, 0, 1) ** 0.55) if open_end else (np.sin(np.pi * t) ** 0.55)
    if gaps and n > 60:
        for _ in range(rng.integers(0, 3)):
            g0 = rng.uniform(0.15, 0.85); gl = rng.uniform(0.02, 0.05)
            env *= 1 - np.exp(-((t - g0) / gl) ** 4) * 0.98        # short break, like the sketch
    wob = 1 + 0.10 * np.sin(2 * np.pi * (t * rng.uniform(2, 5) + rng.uniform()))
    r_all = radius_m * wscale * env * wob
    u, v, z = head.surface_uv(sign * pts[:, 0], pts[:, 1])
    for i in range(n):
        r = r_all[i]
        if not np.isfinite(u[i]) or r < 0.0003:
            continue
        ui, vi = int(u[i]), int(v[i])
        if not (2 <= ui < size - 2 and 2 <= vi < size - 2):
            continue
        Pu = (P[vi, ui + 1] - P[vi, ui - 1]) / 2; Pv = (P[vi + 1, ui] - P[vi - 1, ui]) / 2
        if not (np.isfinite(Pu).all() and np.isfinite(Pv).all()):
            continue
        guu, gvv, guv = Pu @ Pu, Pv @ Pv, Pu @ Pv
        wu = min(int(r / np.sqrt(guu)) + 2, 70); wv = min(int(r / np.sqrt(gvv)) + 2, 70)
        x0, x1 = max(ui - wu, 0), min(ui + wu + 1, size); y0, y1 = max(vi - wv, 0), min(vi + wv + 1, size)
        du, dv = np.meshgrid(np.arange(x0, x1) + 0.5 - u[i], np.arange(y0, y1) + 0.5 - v[i])
        d2 = guu * du * du + 2 * guv * du * dv + gvv * dv * dv
        w = np.clip(1 - d2 / (r * r), 0, 1) ** 2
        w *= np.isfinite(P[y0:y1, x0:x1, 0])                       # stay on the face's own UV island
        Pw = P[y0:y1, x0:x1]
        w *= ~((np.abs(Pw[..., 0]) > head.side_x) & (Pw[..., 2] > head.z_stop))   # ...and stop at the ear
        layer[y0:y1, x0:x1] = np.maximum(layer[y0:y1, x0:x1], w)


def render(head, curves, sign, radius_m, seed=7, gaps=True):
    rng = np.random.default_rng(seed)
    layer = np.zeros((head.size, head.size), dtype=np.float32)
    for c in curves:
        opts = c[2] if len(c) > 2 else {}
        stamp(head, layer, c[0], c[1], radius_m, sign, rng, gaps, **opts)
    return layer


# ---------------------------------------------------------------- preview
def preview(head, layer, path, nm_path, eye):
    """Front view: vanilla normal-map detail as the skin, the layer in red on top."""
    uv = head.front_uv[..., :2]
    ok = np.isfinite(uv[..., 0])
    ui = np.clip(np.nan_to_num(uv[..., 0]).astype(int), 0, head.size - 1)
    vi = np.clip(np.nan_to_num(uv[..., 1]).astype(int), 0, head.size - 1)
    base = np.full(ok.shape, 24.0)
    if os.path.exists(nm_path):
        nm = np.array(Image.open(nm_path).convert('RGBA')).astype(float)
        det = (nm[..., 1] - 128) + (nm[..., 3] - 128)
        base = np.where(ok, 168 + det[vi, ui] * 0.9, 24.0)
    rgb = np.stack([base, base * 0.93, base * 0.86], -1)
    a = np.where(ok, layer[vi, ui], 0)[..., None] ** 0.8
    rgb = rgb * (1 - a) + np.array([150, 20, 30]) * a
    img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))
    # centreline and eye markers
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    cx = int(hm.XMAX / hm.STEP)
    d.line([(cx, 0), (cx, hm.FH)], fill=(60, 120, 255), width=1)
    for sgn in (1, -1):
        ex = int((hm.XMAX - sgn * eye[0]) / hm.STEP); ey = int((hm.YTOP - eye[1]) / hm.STEP)
        d.ellipse([ex - 6, ey - 6, ex + 6, ey + 6], outline=(60, 120, 255), width=2)
    # the marker test showed the game is mirrored relative to the mesh frame, so flip to match what you see
    img.crop((40, 20, hm.FW - 40, 1330)).transpose(Image.FLIP_LEFT_RIGHT).save(path)



def preview_oblique(head, layer, path, nm_path, yaw=62):
    """A three-quarter view from the scarred side (game orientation), with the ear drawn, so you can see where the
    lines stop. A front view can't: everything past the cheek's edge is edge-on."""
    ph = np.radians(yaw)
    v = np.array([np.sin(ph), 0, np.cos(ph)]); rr = np.array([-np.cos(ph), 0, np.sin(ph)])
    P, UV, idx = head.meshes[head.info['skin']]
    E, _, EI = head.meshes[head.info['stem'] + '_Ears_Mesh']
    X0, W = -0.17, int(0.34 / hm.STEP)
    def proj(Pm, ii):
        T = Pm[ii]
        return np.stack([(T @ rr - X0) / hm.STEP, (hm.YTOP - T[..., 1]) / hm.STEP], -1), T @ v
    ts, ds_ = proj(P, idx); te, de = proj(E, EI)
    at_s = np.concatenate([UV[idx] * head.size, np.zeros(idx.shape + (1,))], 2)
    at_e = np.concatenate([np.full(EI.shape + (2,), -1.0), np.ones(EI.shape + (1,))], 2)
    R = hm.raster(np.concatenate([ts, te]), np.concatenate([at_s, at_e]).astype(np.float32), W, hm.FH, z=np.concatenate([ds_, de]))
    ok = np.isfinite(R[..., 0]); ear = ok & (R[..., 2] > 0.5); skin = ok & ~ear
    ui = np.clip(np.nan_to_num(R[..., 0]).astype(int), 0, head.size - 1); vi = np.clip(np.nan_to_num(R[..., 1]).astype(int), 0, head.size - 1)
    base = np.full(ok.shape, 24.0)
    if os.path.exists(nm_path):
        nm = np.array(Image.open(nm_path).convert('RGBA')).astype(float)
        base = np.where(skin, 168 + ((nm[..., 1] - 128) + (nm[..., 3] - 128))[vi, ui] * 0.9, 24.0)
    rgb = np.stack([base, base * 0.93, base * 0.86], -1)
    a = np.where(skin, layer[vi, ui], 0)[..., None] ** 0.8
    rgb = rgb * (1 - a) + np.array([190, 20, 30]) * a
    rgb[ear] = (105, 130, 175)
    img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))
    ys, xs = np.nonzero(skin)
    img = img.crop((xs.min() - 10, ys.min() - 10, xs.max() + 10, ys.max() + 10)).transpose(Image.FLIP_LEFT_RIGHT)
    img.resize((int(img.width * 0.75), int(img.height * 0.75)), Image.LANCZOS).save(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--head', default='A', choices=hm.HEADS, help='human-male head (A-I are player-selectable)')
    ap.add_argument('--design', choices=('v2', 'v3', 'v1ear', 'full', 'combo'), default='v1ear',
                    help='v1ear = the approved v1 layout with lines carried on to the ear (default); '
                         'v2 = hand-placed lines; v3 = v2 plus lines traced from a close-up reference')
    ap.add_argument('--yaw', type=float, default=62, help='angle of the three-quarter preview, degrees')
    ap.add_argument('--marker', action='store_true', help='draw the asymmetric test marks instead of scars')
    ap.add_argument('--half', choices=('right', 'left'), default='left',
                    help="which half of the SHEET carries the marks (left = u<0.5 = the character's right, "
                         "confirmed in game; right = u>0.5 = the character's left)")
    ap.add_argument('--radius', type=float, default=1.4, help='line radius in mm (default 1.4)')
    ap.add_argument('--seed', type=int, default=7, help='seed for the hand-drawn wobble and breaks')
    ap.add_argument('--no-gaps', action='store_true', help='draw unbroken lines')
    a = ap.parse_args()

    head = hm.Head(a.head)
    out = head.info['out']; os.makedirs(out, exist_ok=True)
    eye = head.landmarks()['eye']
    shift = np.array([eye[0] - EYE_S, eye[1] - EYE_Y])
    # a head of another size (the child head): lay the design out for Head A, then scale it about the eye
    mouth_y = head.landmarks()['mouth_y']
    kx, ky = (eye[0] / A_EYE_S, (eye[1] - mouth_y) / A_EYE_MOUTH) if head.info['head'] == 'CHD_B' else (1.0, 1.0)
    if (kx, ky) != (1.0, 1.0):
        print('head %s is smaller than Head A: design scaled x%.3f across, x%.3f up/down (about the eye)' % (a.head, kx, ky))
        shift = np.array([A_EYE_S - EYE_S, A_EYE_Y - EYE_Y])        # lay it out in Head A's frame first; scaled below
    sign = 1 if a.half == 'right' else -1
    if a.design in ('full', 'combo') and not a.marker:
        kept, dropped = design_full() if a.design == 'full' else design_combo()
        # design_full is in Head A's frame; a head at another position (not the child, which is scaled below) is moved to its own eye
        off = np.zeros(2) if (kx, ky) != (1.0, 1.0) or head.info['head'] == 'A' else np.array([eye[0] - A_EYE_S, eye[1] - A_EYE_Y])
        curves = [(c[0] + off, c[1], c[2]) for _, c in kept]
        print('%s: kept %d lines: %s' % (a.design, len(kept), ', '.join(n for n, _ in kept)))
        print('      dropped (would touch a line already kept): %s' % (', '.join('%s (by %s)' % d for d in dropped) or 'none'))
    elif a.design == 'v1ear' and not a.marker:
        curves = [(pts + shift, w, o) for pts, w, o in design_v1ear()]
        print('v1ear: %d lines (v1\'s 14; the outer 3 rings and 7 cheek/jaw/forehead lines run on to the ear)' % len(curves))
    elif a.design == 'v3' and not a.marker:
        kept, dropped = design_v3(eye, head.landmarks()['mouth_y'], shift)
        curves = [c for _, c in kept]
        print('v3: kept %d lines: %s' % (len(kept), ', '.join(n for n, _ in kept)))
        print('    dropped (would touch a line already kept): %s' % (', '.join('%s (by %s)' % d for d in dropped) or 'none'))
    else:
        curves = [(pts + shift, w) for pts, w in (marker() if a.marker else design())]
    if not a.marker:
        bad = check_crossings(curves)
        print('%d lines; %s' % (len(curves), 'no two come within 4 mm of each other' if not bad else
              'CLOSE PAIRS (line numbers in design() order): ' + ', '.join('%d-%d (%.1f mm)' % b for b in bad)))
    if (kx, ky) != (1.0, 1.0):
        eye_a = np.array([A_EYE_S, A_EYE_Y])
        curves = [((eye + (c[0] - eye_a) * np.array([kx, ky])),) + tuple(c[1:]) for c in curves]
    layer = render(head, curves, sign, a.radius / 1000.0 * (kx + ky) / 2, a.seed, gaps=not a.no_gaps and not a.marker)
    stem = 'marker_height' if a.marker else 'scar_height'
    Image.fromarray((layer * 255).astype(np.uint8)).save(os.path.join(out, stem + '.png'))
    nm = os.path.join(head.info['src'], head.info['stem'] + '_NM.DDS')
    preview(head, layer, os.path.join(out, stem + '_preview.png'), nm, eye)
    preview_oblique(head, layer, os.path.join(out, stem + '_preview_3q.png'), nm, a.yaw)
    print('wrote', os.path.join(out, stem + '_preview_3q.png'))
    print('head %s: eye at s=%.4f y=%.4f (design shifted by %.1f, %.1f mm)'
          % (a.head, eye[0], eye[1], shift[0] * 1000, shift[1] * 1000))
    print('wrote %s  (%d texels covered, half=%s)' % (os.path.join(out, stem + '.png'), int((layer > 0.05).sum()), a.half))
    print('wrote', os.path.join(out, stem + '_preview.png'))


if __name__ == '__main__':
    main()
