"""Reshape the back of the Dhaen Extended robe's skirt so the legs stay covered in a run.

    python items/obito_uchiha_robe_dhaen/art/patch_dhaen_robe.py obito_uchiha_robe_dhaen
    python tools/build_item.py obito_uchiha_robe_dhaen

Dhaen Extended's robe (a refit of Gale's) binds the back of the skirt to the two legs with a
hard left/right step and lets it swing with each leg, so when the legs part in a run the
back opens and the calf comes through. This re-skins the back so it hangs mostly from the
pelvis (PELVIS of its weight, the rest still follows the legs), and moves it out by PUSH
metres toward the hem, so the legs swing inside it instead of through it. The change fades
out toward the sides (TAPER) so the back still joins the rest of the skirt.

ORIENTATION: in these files the character faces -z (toes at z=-0.13, the crest print at
z=+0.11), so the BACK of the skirt is the +z side. Builds 3-7 treated -z as the back and
reshaped the FRONT instead; that is why they changed nothing at the back.

The values come from tune_skirt.py, which scores variants by posing the Dhaen body and the
robe together (clip_check.py): 535 exposed back-of-leg vertices over four run poses as
shipped, ~135 with this.

THE OUTPUT IS A MODIFIED COPY OF THE DHAEN MOD'S MESH. It is written into this mod's own
asset folder and shipped in the pak, so a pak built with it must not be published without
the Dhaen Extended author's permission. Remove "patched_gr2" from the item's mod_visuals
entry and rebuild for a pak that only references their mesh (and keeps the clipping).
"""
import json, os, subprocess, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
import item as itemlib
import tune_skirt as ts
from lspk import Pak
from gltf_retarget import read

DIVINE = os.path.join(os.environ.get('USERPROFILE', ''), 'Tools', 'LSLib', 'Tools', 'Divine.exe')

# (ramp, pelvis, push, fat, taper) -- see tune_skirt.py. Override with DHAEN_SKIRT="r,p,u,f,t".
PARAMS = (0.0, 0.7, 0.09, 0.0, 0.12)
if os.environ.get('DHAEN_SKIRT'):
    PARAMS = tuple(float(v) for v in os.environ['DHAEN_SKIRT'].split(','))


HEM_FROM = 0.42       # skirt is left alone above this height (the knee is at 0.35)
HEM_TO = 0.07         # new lowest point of the hem (the ankle joint is at 0.05)


def divine(src, dst, extra=()):
    cmd = [DIVINE, '-g', 'bg3', '-a', 'convert-model', '-s', os.path.abspath(src), '-d', os.path.abspath(dst)]
    for e in extra:
        cmd += ['-e', e]
    subprocess.run(cmd, check=True, capture_output=True)


def patch(gltf_in, gltf_out):
    g = json.load(open(gltf_in))
    bin_path = os.path.join(os.path.dirname(gltf_in), g['buffers'][0]['uri'])
    buf = bytearray(open(bin_path, 'rb').read())
    p = g['meshes'][0]['primitives'][0]
    accs = g['accessors']
    ap, aj, aw = (accs[p['attributes'][k]] for k in ('POSITION', 'JOINTS_0', 'WEIGHTS_0'))
    bv = g['bufferViews'][ap['bufferView']]
    assert aj['bufferView'] == ap['bufferView'] == aw['bufferView'], 'attributes are not interleaved together'
    assert aj['componentType'] == 5121 and aw['componentType'] == 5126 and ap['componentType'] == 5126
    stride, base_off = bv['byteStride'], bv.get('byteOffset', 0)

    base = ts.load(gltf_in)
    pos2, J2, W2 = ts.variant(base, *PARAMS)
    pos, J, W, _ = base
    # Lengthen the skirt to the ankles. The visual hides the legs (item.json
    # "hide_body_parts"), so with the hem where Dhaen Extended put it (17 cm up, ~12 cm
    # above the ankle) there would be a gap under it with nothing in it. Everything below
    # HEM_FROM is stretched down; UVs are untouched, and the cloth there is one flat colour.
    low = pos2[:, 1] < HEM_FROM
    k = (HEM_FROM - HEM_TO) / (HEM_FROM - pos2[:, 1].min())
    pos2[low, 1] = HEM_FROM - (HEM_FROM - pos2[low, 1]) * k
    changed = 0
    for i in range(len(pos)):
        same = (np.allclose(pos[i], pos2[i], atol=1e-7) and (J[i] == J2[i]).all() and np.allclose(W[i], W2[i], atol=1e-6))
        if same:
            continue
        rec = base_off + i * stride
        o = rec + ap.get('byteOffset', 0)
        buf[o:o + 12] = pos2[i].astype(np.float32).tobytes()
        o = rec + aj.get('byteOffset', 0)
        buf[o:o + 4] = J2[i].astype(np.uint8).tobytes()
        o = rec + aw.get('byteOffset', 0)
        buf[o:o + 16] = W2[i].astype(np.float32).tobytes()
        changed += 1

    out_bin = os.path.splitext(gltf_out)[0] + '.bin'
    g['buffers'][0]['uri'] = os.path.basename(out_bin)
    open(out_bin, 'wb').write(bytes(buf))
    json.dump(g, open(gltf_out, 'w'), indent=1)
    # SharpGLTF (inside Divine) rejects data outside an accessor's recorded min/max
    _, acc2 = read(gltf_out)
    for key in ('POSITION', 'JOINTS_0', 'WEIGHTS_0'):
        a = acc2(p['attributes'][key]).astype(float)
        acc_json = accs[p['attributes'][key]]
        if 'min' in acc_json:
            cast = int if key == 'JOINTS_0' else float
            acc_json['min'] = [cast(v) for v in a.min(0)]
            acc_json['max'] = [cast(v) for v in a.max(0)]
    json.dump(g, open(gltf_out, 'w'), indent=1)
    return changed


def main():
    it = itemlib.load()
    mv = it['mod_visuals'][0]
    out_rel = mv.get('patched_gr2')
    if not out_rel:
        raise SystemExit('item.json mod_visuals[0] has no "patched_gr2"')
    work = os.path.abspath(os.path.join(it.work, 'dhaen_patch'))
    os.makedirs(work, exist_ok=True)

    raw = os.path.join(work, 'Dhaen_ARM_Robe_A_Body.GR2')
    open(raw, 'wb').write(Pak(mv['pak']).read(mv['mesh']))
    orig = os.path.join(work, 'original.gltf')
    divine(raw, orig)
    fixed = os.path.join(work, 'patched.gltf')
    n = patch(orig, fixed)
    out = os.path.join(it.src, out_rel)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    divine(fixed, out, ('export-uvs', 'export-normals', 'export-tangents'))
    divine(out, os.path.join(work, 'check.gltf'))
    print('params (ramp, pelvis, push, fat, taper) = %s' % (PARAMS,))
    print('changed %d vertices; wrote %s (%d bytes)' % (n, out, os.path.getsize(out)))


if __name__ == '__main__':
    main()
