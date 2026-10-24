"""Build the STANDALONE scarred face: its own selectable Human face, alongside the vanilla ones.

  python items/obito_scars/build_face_mod.py              # -> ObitoScarsFace.pak in the repo root
  python items/obito_scars/build_face_mod.py --install    # also copy it into the BG3 Mods folder

Unlike ObitoScarsScars.pak (which REPLACES Head A's normal map for everyone), this adds a new face and touches
nothing vanilla. Everything it defines has a NEW id, so it works with mods (BeastFolk) that take over the vanilla
Human face entries, and Head A stays unscarred for everyone else.

What it ships (all read from / derived from the game's own Head A data by this script):
  * a cloned head VISUAL (same mesh, skeleton, animations; only the skin materials differ)
  * four cloned skin MATERIALS (base + LOD1/2/4) that point at our normal map, and otherwise at vanilla textures
  * one new TEXTURE: the scarred normal map (art/out/head_a/build_scars/dds/..._NM.DDS)
  * a CHARACTER CREATION entry (Human, body type 0, slot Head) pointing at the new visual
  * a display NAME (Localization) and a thumbnail ICON atlas (GUI/CC_Icons.lsx + Icons/CC_Icons.dds)

Same Divine settings as build.ps1: resource .lsx -> .lsf, loca .xml -> .loca, create-package -c lz4. The character
creation and icon .lsx files stay text (the game reads those as XML).
"""
import os, sys, re, copy, uuid, shutil, argparse, subprocess
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, 'art'))
from lspk import Pak
import item as itemlib
import headmesh as hm
import build_test_mod as btm                 # META template, Divine path, Mods folder, escape()

FOLDER = 'ObitoScarsFace'                 # set from CONFIG in main()
NAME = 'Obito Scars (Face)'
HEAD = 'A'
VARIANT = ''                              # '' = the approved layout; 'dense' = the denser one (its own mod: own ids, folder, tile name)
TILE = 'Obito Scars'                      # the name shown on the tile
VARIANTS = {'dense': dict(folder='Dense', name=', dense', tile='Obito Scars (dense)'),
            'combo': dict(folder='Combo', name=', combined', tile='Obito Scars (combined)'),
            'vis': dict(folder='Vis', name=', combined, more visible', tile='Obito Scars (visible)')}
CONFIG = {
    'A': dict(folder='ObitoScarsFace', name='Obito Scars (Face)',
              desc="A selectable Human face with Obito Uchiha's right-side facial scars. Adds a new face; changes nothing vanilla."),
    'CHD_B': dict(folder='ObitoScarsFaceDhaenHumB', name='Obito Scars (Dhaen HUM B)',
                  desc="A selectable face for Dhaen Extended races: the 'HUM B' head with Obito Uchiha's right-side facial scars. "
                       "Requires Dhaen Extended. Adds a new face; changes nothing vanilla."),
}
HUMAN = '0eb594cb-8820-4be6-a58d-8be7a1a98fba'
NS = uuid.UUID('6d1b9c1e-4a52-4e4e-9a51-0b17f0a5c0de')       # fixed: the same ids on every rebuild
ATLAS = 512                                                    # icon atlas is 512x512 with one 150x150 icon
ICON = 150


def res_prefix():
    """Prefix for the names of the cloned resources. A variant gets its own so two of these mods never share a name
    (the plain ones keep 'ObitoScars_', exactly as already tested in game)."""
    return 'ObitoScars_' + (VARIANT.capitalize() + '_' if VARIANT else '')


def gid(*parts):
    # Head A keeps the ids it was first built with (already tested in game); other heads get their own
    return str(uuid.uuid5(NS, 'obito-scars-face.' + ('' if HEAD == 'A' else HEAD + '.') + (VARIANT + '.' if VARIANT else '') + '.'.join(parts)))


def find_maps(dds_dir, stem):
    """The normal map is required; the crease map (CLEA) and skin-data map (HMVY) are shipped too if the art build changed them."""
    return [m for m in ('NM', 'CLEA', 'HMVY') if os.path.exists(os.path.join(dds_dir, '%s_%s.DDS' % (stem, m)))]


def divine(*args):
    subprocess.run([btm.DIVINE, '-g', 'bg3'] + list(args) + ['-l', 'warn'], check=True)


def attrs(node):
    return {a.get('id'): a for a in node.findall('attribute')}


def set_attr(node, key, value):
    attrs(node)[key].set('value', value)


def region(root, name):
    return [r for r in root.findall('region') if r.get('id') == name][0]


def bank_children(root, name):
    return region(root, name).find('node').find('children')


# ------------------------------------------------------------------ 1. clone the vanilla Head A bank
def vanilla_bank(i, work):
    path = 'Public/Shared/Content/Assets/Characters/Humans/Heads/[PAK]_%s/_merged.lsf' % i['bank_name']
    lsf = os.path.join(work, 'vanilla_bank.lsf'); lsx = os.path.join(work, 'vanilla_bank.lsx')
    open(lsf, 'wb').write(Pak(os.path.join(itemlib.DATA, 'Shared.pak')).read(path))
    divine('-a', 'convert-resource', '-i', 'lsf', '-o', 'lsx', '-s', lsf, '-d', lsx)
    return ET.parse(lsx).getroot()


def build_banks(src, i, atlas_id, maps=('NM',)):
    """Returns (xml root for the new bank, ids dict). Only the pieces that must differ are cloned."""
    stem = i['stem']
    vis = [v for v in bank_children(src, 'VisualBank') if attrs(v)['Name'].get('value') == stem][0]
    mats = [m for m in bank_children(src, 'MaterialBank')]
    old_tex = {m: [t for t in bank_children(src, 'TextureBank') if attrs(t)['Name'].get('value') == stem + '_' + m][0] for m in maps}
    nm = old_tex['NM']
    old_nm = attrs(nm)['ID'].get('value')
    old_ids = {m: attrs(t)['ID'].get('value') for m, t in old_tex.items()}

    ids = {'visual': gid('visual'), 'nm': gid('tex.nm'), 'atlas': atlas_id, 'cc': gid('cc.entry'),
           'tex': {m: (gid('tex.nm') if m == 'NM' else gid('tex', m.lower())) for m in maps}}
    mat_map = {}
    new_mats = []
    for m in mats:
        a = attrs(m); old = a['ID'].get('value'); name = a['Name'].get('value')
        uses = [t for t in m.findall('children/node')
                if t.get('id') == 'Texture2DParameters' and attrs(t)['ID'].get('value') == old_nm]
        if not uses:                     # e.g. the lowest LOD has no normal map: nothing to change, keep the vanilla material
            print('  material %-28s does not use the normal map -> stays vanilla' % name)
            continue
        if len(uses) != 1:
            raise SystemExit('material %s references the normal map %d times (expected 1)' % (name, len(uses)))
        new = gid('mat', name); mat_map[old] = new
        c = copy.deepcopy(m)
        set_attr(c, 'ID', new); set_attr(c, 'Name', res_prefix() + name)
        swapped_maps = []
        for t in c.findall('children/node'):
            if t.get('id') == 'Texture2DParameters':
                for m, old in old_ids.items():
                    if attrs(t)['ID'].get('value') == old:
                        set_attr(t, 'ID', ids['tex'][m]); swapped_maps.append(m)
        print('  material %-28s cloned, textures -> ours: %s' % (name, ', '.join(sorted(set(swapped_maps)))))
        new_mats.append(c)

    v = copy.deepcopy(vis)
    set_attr(v, 'ID', ids['visual']); set_attr(v, 'Name', res_prefix() + stem)
    swapped = 0
    for o in v.findall('children/node'):
        if o.get('id') == 'Objects':
            mid = attrs(o)['MaterialID'].get('value')
            if mid in mat_map:
                set_attr(o, 'MaterialID', mat_map[mid]); swapped += 1
    print('  %d mesh objects re-pointed at the cloned skin materials' % swapped)
    if swapped < 3:
        raise SystemExit('only %d skin objects were re-pointed at the cloned materials' % swapped)

    texes = []
    for m, old in old_tex.items():
        tex = copy.deepcopy(old)
        set_attr(tex, 'ID', ids['tex'][m]); set_attr(tex, 'Name', res_prefix() + stem + '_' + m)
        set_attr(tex, 'Template', res_prefix() + stem + '_' + m)
        set_attr(tex, 'SourceFile', 'Public/%s/Assets/Textures/%s_%s.DDS' % (FOLDER, stem, m))
        texes.append(tex)

    atlas = ET.Element('node', id='Resource')
    for k, t, val in (('ID', 'FixedString', atlas_id), ('Name', 'LSString', FOLDER + '_CCIcons'),
                      ('SourceFile', 'LSString', 'Public/%s/Assets/Textures/Icons/CC_Icons.dds' % FOLDER),
                      ('Template', 'FixedString', FOLDER + '_CCIcons'), ('Streaming', 'bool', 'True'),
                      ('Type', 'int32', '1'), ('SRGB', 'bool', 'False'), ('Width', 'int32', str(ATLAS)),
                      ('Height', 'int32', str(ATLAS)), ('Depth', 'int32', '1')):
        ET.SubElement(atlas, 'attribute', id=k, type=t, value=val)

    out = ET.Element('save')
    out.append(copy.deepcopy(src.find('version')))
    for name, kids in (('TextureBank', texes + [atlas]), ('MaterialBank', new_mats), ('VisualBank', [v])):
        r = copy.deepcopy(region(src, name))
        ch = r.find('node').find('children')
        for c in list(ch):
            ch.remove(c)
        for k in kids:
            ch.append(k)
        out.append(r)
    ids['old_visual'] = attrs(vis)['ID'].get('value')
    ids['mat_map'] = mat_map
    return out, ids


# ------------------------------------------------------------------ 2. the thumbnail
def make_icon(ids, work):
    """Head A's own thumbnail, cut from the game's icon atlas, in a small atlas of our own."""
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    gust = Pak(os.path.join(itemlib.DATA, 'Gustav.pak')).read('Public/GustavDev/CharacterCreation/Generated_CCIcons.lsx').decode('utf-8')
    m = re.search(r'MapKey" type="FixedString" value="0_Head_%s"/>(.*?)</node>' % ids['old_visual'], gust, re.S)
    u1, u2, v1, v2 = (float(re.search(r'id="%s" type="float" value="([^"]+)"' % k, m.group(1)).group(1)) for k in ('U1', 'U2', 'V1', 'V2'))
    p = os.path.join(work, 'vanilla_icons.dds')
    open(p, 'wb').write(Pak(os.path.join(itemlib.DATA, 'Icons.pak')).read(
        'Public/GustavDev/Assets/Textures/Icons/Generated_28ac9ce2-2aba-8cda-b3b5-6e922f71b6b8_CCIcons.dds'))
    big = Image.open(p).convert('RGBA'); W, H = big.size
    icon = big.crop((round(u1 * W), round(v1 * H), round(u2 * W), round(v2 * H))).resize((ICON, ICON), Image.LANCZOS)
    return icon


# Landmarks in Head A's 150 px thumbnail (read off the picture): where the face features are, so the scar layout
# can be drawn on it. The thumbnail is a slightly turned portrait, so this is approximate.
ICON_CX = 83                                           # centreline
ICON_PX_PER_M = 690.0                                  # sideways: eye at s = 30 mm lands at x = 62
ICON_Y = ([1.694, 1.7433, 1.7808, 1.8183, 1.870], [135, 106, 80, 57, 20])    # chin, mouth, nose tip, eye, above the brow


def scar_icon(icon):
    """Draw the scar layout onto the thumbnail so the tile is recognisable next to vanilla Head A."""
    import numpy as np
    from PIL import Image, ImageDraw
    import draw_scar_layer as ds
    head = hm.Head('A')
    eye = head.landmarks()['eye']
    shift = np.array([eye[0] - ds.EYE_S, eye[1] - ds.EYE_Y])
    K = 6                                              # draw large, then shrink, for smooth thin lines
    layer = Image.new('RGBA', (ICON * K, ICON * K), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    for c in ds.design_v1ear():
        pts = c[0] + shift
        u, v, z = head.face_to_uv(-pts[:, 0], pts[:, 1])                  # mesh -x = the character's right
        ok = np.isfinite(u) & (pts[:, 0] < head.edge_ax[np.clip(((hm.YTOP - pts[:, 1]) / hm.STEP).astype(int), 0, hm.FH - 1), 1])
        px = (ICON_CX - pts[:, 0] * ICON_PX_PER_M) * K
        py = np.interp(pts[:, 1], *ICON_Y) * K
        ok &= py > 38 * K                                                # above this the thumbnail is hair
        run = []
        for j in range(len(pts)):
            if ok[j]:
                run.append((px[j], py[j]))
            if (not ok[j] or j == len(pts) - 1) and len(run) > 3:
                d.line(run, fill=(88, 30, 26, 200), width=int(1.35 * K), joint='curve'); run = []
            elif not ok[j]:
                run = []
    layer = layer.resize((ICON, ICON), Image.LANCZOS)
    return Image.alpha_composite(icon, layer)


def render_icon(i, nm_dds):
    """A thumbnail drawn from the head mesh: front view, lit, with the SCARRED normal map's detail, on a dark background."""
    import numpy as np
    from PIL import Image
    head = hm.Head(i['head'])
    nm = np.array(Image.open(nm_dds).convert('RGBA')).astype(float)
    uv = head.front_uv[..., :2]; ok = np.isfinite(uv[..., 0])
    ui = np.clip(np.nan_to_num(uv[..., 0]).astype(int), 0, head.size - 1); vi = np.clip(np.nan_to_num(uv[..., 1]).astype(int), 0, head.size - 1)
    z = head.front_uv[..., 2]; zf = np.where(np.isnan(z), np.nanmax(z), z)
    gy, gx = np.gradient(zf / hm.STEP * 0.0002 * 40)
    lam = np.clip(0.62 + 0.9 * (-gx * 0.4 - gy * 0.7), 0.25, 1.05)                       # broad lighting from the head's shape
    det = ((nm[..., 1] - 128) + (nm[..., 3] - 128))[vi, ui] * 0.011                       # fine detail, incl. the scar grooves
    shade = np.clip(lam + det, 0.15, 1.2)
    skin = np.array([206, 150, 118], float)
    rgb = np.where(ok[..., None], skin * shade[..., None], np.array([38, 36, 34], float))
    img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).transpose(Image.FLIP_LEFT_RIGHT)   # the game's orientation
    W, H = img.size
    img = img.crop((0, 200, W, 200 + W)).resize((ICON, ICON), Image.LANCZOS)                # a square around the face
    return img.convert('RGBA')


def write_icon_atlas(icon, dst_dds, work):
    from PIL import Image
    atlas = Image.new('RGBA', (ATLAS, ATLAS), (0, 0, 0, 0)); atlas.paste(icon, (0, 0))
    png = os.path.join(work, 'CC_Icons.png'); atlas.save(png)
    subprocess.run([itemlib.MAGICK, png, '-define', 'dds:compression=dxt5', '-define', 'dds:mipmaps=0', dst_dds], check=True)


# ------------------------------------------------------------------ 3. text files
def cc_file(ids, entries):
    """entries: dicts with race, body_type, body_shape, skin, uuid."""
    node = '''                <node id="CharacterCreationAppearanceVisual">
                    <attribute id="BodyShape" type="uint8" value="%(body_shape)s"/>
                    <attribute id="BodyType" type="uint8" value="%(body_type)s"/>
                    <attribute id="DefaultSkinColor" type="guid" value="%(skin)s"/>
                    <attribute id="DisplayName" type="TranslatedString" handle="%(handle)s" version="1"/>
                    <attribute id="RaceUUID" type="guid" value="%(race)s"/>
                    <attribute id="SlotName" type="FixedString" value="Head"/>
                    <attribute id="UUID" type="guid" value="%(uuid)s"/>
                    <attribute id="VisualResource" type="guid" value="%(visual)s"/>
                </node>
'''
    body = ''.join(node % dict(e, handle=ids['handle'], visual=ids['visual']) for e in entries)
    return '''<?xml version="1.0" encoding="UTF-8"?>
<save>
    <version major="4" minor="0" revision="9" build="328"/>
    <region id="CharacterCreationAppearanceVisuals">
        <node id="root">
            <children>
''' + body + '''            </children>
        </node>
    </region>
</save>
'''


def dhaen_entries(visual_id, handle='h6fbd1b4dg54f8g4774g9c26ge12037f4292c'):
    """Every Dhaen Extended character-creation entry named "HUM B" that uses THIS head visual (the human child head B):
    race, body type/shape, skin. Dhaen also has "HUM B" entries for two races that use other head visuals; those are
    left alone, because pointing them at this head would change their head shape."""
    local = os.path.join(ROOT, 'extracted', 'dhaen', 'pak', 'Public', 'Dhaen_Extended', 'CharacterCreation',
                         'CharacterCreationAppearanceVisuals.lsx')
    if os.path.exists(local):
        t = open(local, encoding='utf-8').read()
    else:
        t = Pak(os.path.join(btm.MODS, 'Dhaen_Extended_2.5.pak')).read(
            'Public/Dhaen_Extended/CharacterCreation/CharacterCreationAppearanceVisuals.lsx').decode('utf-8')
    out = []
    for m in re.finditer(r'<node id="CharacterCreationAppearanceVisual">(.*?)</node>', t, re.S):
        b = m.group(1)
        if handle not in b:
            continue
        d = dict(re.findall(r'<attribute id="([^"]+)" type="[^"]*" (?:value|handle)="([^"]*)"', b))
        if d['VisualResource'] != visual_id:
            continue
        out.append(dict(race=d['RaceUUID'], body_type=d['BodyType'], body_shape=d['BodyShape'],
                        skin=d['DefaultSkinColor'], uuid=gid('cc.entry', d['UUID'])))
    return out


def icons_file(ids, prefixes=('0',)):
    half = 0.5 / ATLAS
    uv = '''                <node id="IconUV">
                    <attribute id="MapKey" type="FixedString" value="%s_Head_''' + ids['visual'] + '''"/>
                    <attribute id="U1" type="float" value="''' + '%.8f' % half + '''"/>
                    <attribute id="U2" type="float" value="''' + '%.8f' % ((ICON - 0.5) / ATLAS) + '''"/>
                    <attribute id="V1" type="float" value="''' + '%.8f' % half + '''"/>
                    <attribute id="V2" type="float" value="''' + '%.8f' % ((ICON - 0.5) / ATLAS) + '''"/>
                </node>
'''
    return '''<?xml version="1.0" encoding="UTF-8"?>
<save>
    <version major="4" minor="7" revision="1" build="3"/>
    <region id="IconUVList">
        <node id="root">
            <children>
''' + ''.join(uv % p for p in prefixes) + '''            </children>
        </node>
    </region>
    <region id="TextureAtlasInfo">
        <node id="root">
            <children>
                <node id="TextureAtlasIconSize">
                    <attribute id="Height" type="int32" value="%d"/>
                    <attribute id="Width" type="int32" value="%d"/>
                </node>
                <node id="TextureAtlasPath">
                    <attribute id="Path" type="string" value="Assets/Textures/Icons/CC_Icons.dds"/>
                    <attribute id="UUID" type="FixedString" value="%s"/>
                </node>
                <node id="TextureAtlasTextureSize">
                    <attribute id="Height" type="int32" value="%d"/>
                    <attribute id="Width" type="int32" value="%d"/>
                </node>
            </children>
        </node>
    </region>
</save>
''' % (ICON, ICON, ids['atlas'], ATLAS, ATLAS)


LOCA = '''<?xml version="1.0" encoding="utf-8"?>
<contentList>
    <content contentuid="%s" version="1">%s</content>
</contentList>
'''


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--head', default='A', choices=sorted(CONFIG), help="A = the adult Head A; CHD_B = Dhaen's 'HUM B'")
    ap.add_argument('--dds', help='directory holding the scarred NM DDS (default: art/out/head_<x>/build_scars/dds, or build_<variant>)')
    ap.add_argument('--variant', default='', choices=[''] + sorted(VARIANTS),
                    help="'' = the approved layout; 'dense' = the denser layout, packaged as a SEPARATE mod (own ids, folder and tile name)")
    ap.add_argument('--install', action='store_true', help='copy the pak into the BG3 Mods folder')
    a = ap.parse_args()
    global FOLDER, NAME, HEAD, VARIANT, TILE
    HEAD, VARIANT = a.head, a.variant
    FOLDER, NAME = CONFIG[a.head]['folder'], CONFIG[a.head]['name']
    if a.variant:
        v = VARIANTS[a.variant]
        FOLDER += v['folder']; NAME = NAME[:-1] + v['name'] + ')'; TILE = v['tile']

    i = hm.info(a.head)
    dds_dir = a.dds or os.path.join(i['out'], 'build_' + (a.variant or 'scars'), 'dds')
    nm_dds = os.path.join(dds_dir, i['stem'] + '_NM.DDS')
    if not os.path.exists(nm_dds):
        raise SystemExit('missing %s -- run art/composite_head.py first' % nm_dds)

    stage = os.path.join(ROOT, 'build', 'stage', 'obito_scars_face')
    work = os.path.join(ROOT, 'build', 'work', 'obito_scars_face')
    for d in (stage, work):
        if os.path.exists(d):
            shutil.rmtree(d)
        os.makedirs(d)

    print('reading the vanilla %s bank ...' % i['stem'])
    src = vanilla_bank(i, work)
    maps = find_maps(dds_dir, i['stem'])
    print('  textures shipped: %s' % ', '.join(maps))
    bank, ids = build_banks(src, i, gid('tex.atlas'), maps)
    ids['handle'] = 'h' + gid('loca.name').replace('-', 'g')
    if a.head == 'A':
        # the vanilla Head A entry's default skin colour, so the new face starts with the same skin
        cc = Pak(os.path.join(itemlib.DATA, 'Shared.pak')).read('Public/Shared/CharacterCreation/CharacterCreationAppearanceVisuals.lsx').decode('utf-8')
        entry = [m for m in re.finditer(r'<node id="CharacterCreationAppearanceVisual">(.*?)</node>', cc, re.S)
                 if 'value="%s"' % ids['old_visual'] in m.group(1)][0].group(1)
        entries = [dict(race=HUMAN, body_type='0', body_shape='0', uuid=ids['cc'],
                        skin=re.search(r'DefaultSkinColor" type="guid" value="([^"]+)"', entry).group(1))]
    else:
        entries = dhaen_entries(ids['old_visual'])
        print('  %d Dhaen "HUM B" entries that use this head -> %d scarred entries (%d races)' % (len(entries), len(entries), len({e['race'] for e in entries})))

    # ---- stage the mod
    pub = os.path.join(stage, 'Public', FOLDER)
    os.makedirs(os.path.join(pub, 'Assets', 'Textures', 'Icons')); os.makedirs(os.path.join(pub, 'GUI'))
    os.makedirs(os.path.join(pub, 'CharacterCreation')); os.makedirs(os.path.join(stage, 'Mods', FOLDER))
    os.makedirs(os.path.join(stage, 'Localization', 'English'))
    for m in maps:
        shutil.copy2(os.path.join(dds_dir, '%s_%s.DDS' % (i['stem'], m)), os.path.join(pub, 'Assets', 'Textures', '%s_%s.DDS' % (i['stem'], m)))
    icon = scar_icon(make_icon(ids, work)) if a.head == 'A' else render_icon(i, nm_dds)
    icon.resize((450, 450)).save(os.path.join(work, 'icon_preview.png'))
    write_icon_atlas(icon, os.path.join(pub, 'Assets', 'Textures', 'Icons', 'CC_Icons.dds'), work)

    content = os.path.join(pub, 'Content', 'Assets', 'Characters', '[PAK]_' + FOLDER); os.makedirs(content)
    lsx, lsf = os.path.join(content, '_merged.lsx'), os.path.join(content, '_merged.lsf')
    ET.indent(bank, space='\t'); ET.ElementTree(bank).write(lsx, encoding='utf-8', xml_declaration=True)
    divine('-a', 'convert-resource', '-i', 'lsx', '-o', 'lsf', '-s', lsx, '-d', lsf)
    os.remove(lsx)

    open(os.path.join(pub, 'CharacterCreation', 'CharacterCreationAppearanceVisuals.lsx'), 'w', encoding='utf-8', newline='\n').write(cc_file(ids, entries))
    open(os.path.join(pub, 'GUI', 'CC_Icons.lsx'), 'w', encoding='utf-8', newline='\n').write(icons_file(ids, ('0',) if a.head == 'A' else ('0', '1')))
    xml = os.path.join(stage, 'Localization', 'English', FOLDER + '.xml')
    open(xml, 'w', encoding='utf-8', newline='\n').write(LOCA % (ids['handle'], TILE))
    divine('-a', 'convert-loca', '-s', xml, '-d', xml[:-4] + '.loca')
    os.remove(xml)

    mod_uuid = gid('mod')
    q = {'"': '&quot;'}
    meta = btm.META.format(desc=btm.escape(CONFIG[a.head]['desc'], q),
                           folder=FOLDER, name=btm.escape(NAME, q), uuid=mod_uuid, v64=btm.V64)
    ET.fromstring(meta)
    open(os.path.join(stage, 'Mods', FOLDER, 'meta.lsx'), 'w', encoding='utf-8', newline='\n').write(meta)

    pak = os.path.join(ROOT, FOLDER + '.pak')
    if os.path.exists(pak):
        os.remove(pak)
    divine('-a', 'create-package', '-s', stage, '-d', pak, '-c', 'lz4')

    verify(pak, ids, nm_dds, src, maps, dds_dir)
    print('\nbuilt %s (%s bytes), mod UUID %s' % (pak, format(os.path.getsize(pak), ','), mod_uuid))
    if a.install:
        os.makedirs(btm.MODS, exist_ok=True); shutil.copy2(pak, btm.MODS); print('installed to', btm.MODS)
    else:
        print('not installed. Re-run with --install, or copy the pak into:\n  ' + btm.MODS)


def verify(pak, ids, nm_dds, src, maps=('NM',), dds_dir=None):
    """Read the pak back and check the pieces agree with each other and with nothing vanilla."""
    from lsf import LSF
    p = Pak(pak); ok = True
    print('\npak contents:')
    for n in sorted(p.entries):
        print('  ', n)
    bank = 'Public/%s/Content/Assets/Characters/[PAK]_%s/_merged.lsf' % (FOLDER, FOLDER)
    L = LSF(p.read(bank))
    res = {}
    for n in range(len(L.nodes)):
        if L.node_name(n) == 'Resource':
            a = {k: v[1] for k, v in L.node_attrs(n).items()}
            res[str(a['ID'])] = str(a['Name'])
    vanilla_ids = set()
    for reg in ('VisualBank', 'MaterialBank', 'TextureBank'):
        for c in bank_children(src, reg):
            vanilla_ids.add(attrs(c)['ID'].get('value'))
    clash = set(res) & vanilla_ids
    print('\nbank defines %d resources: %s' % (len(res), ', '.join(sorted(res.values()))))
    print('  redefines a vanilla id: %s' % ('NONE (good)' if not clash else 'YES ' + str(clash))); ok &= not clash
    need = [ids['visual'], ids['atlas']] + list(ids['tex'].values()) + list(ids['mat_map'].values())
    missing = [x for x in need if x not in res]
    print('  every new id present: %s' % ('yes' if not missing else 'MISSING ' + str(missing))); ok &= not missing
    # the visual must use the new skin materials and none of the old ones
    for n in range(len(L.nodes)):
        if L.node_name(n) == 'Objects':
            m = str(L.node_attrs(n)['MaterialID'][1])
            if m in ids['mat_map']:
                print('  !! an object still uses a vanilla skin material'); ok = False
    for m in maps:
        f = '%s_%s.DDS' % (os.path.basename(nm_dds).rsplit('_NM.DDS', 1)[0], m)
        same = p.read('Public/%s/Assets/Textures/%s' % (FOLDER, f)) == open(os.path.join(dds_dir or os.path.dirname(nm_dds), f), 'rb').read()
        print('  %s map inside the pak identical to the art build: %s' % (m, same)); ok &= same
    cc = p.read('Public/%s/CharacterCreation/CharacterCreationAppearanceVisuals.lsx' % FOLDER).decode('utf-8')
    ET.fromstring(cc)
    print('  character-creation entry points at the new visual: %s' % (ids['visual'] in cc)); ok &= ids['visual'] in cc
    ic = p.read('Public/%s/GUI/CC_Icons.lsx' % FOLDER).decode('utf-8'); ET.fromstring(ic)
    print('  icon key matches the new visual: %s ; atlas id matches the bank: %s' % ('0_Head_' + ids['visual'] in ic, ids['atlas'] in ic))
    ok &= ('0_Head_' + ids['visual'] in ic) and (ids['atlas'] in ic)
    loca = [e for e in p.entries if e.endswith('.loca')]
    print('  localization: %s' % (loca or 'MISSING')); ok &= bool(loca)
    if not ok:
        raise SystemExit('verification failed; do not install')


if __name__ == '__main__':
    main()
