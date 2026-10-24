"""Load an item definition (items/<id>/item.json) and derive every path from it.

All generators take the item id as their only argument:

    python tools/make_content_bank.py akatsuki_cloak

and read what they need from here, so no tool hardcodes a mod name, a folder or a UUID.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from garment import GARMENTS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = r"C:\Program Files (x86)\Steam\steamapps\common\Baldurs Gate 3\Data"
MAGICK = os.environ.get('MAGICK', r"C:/Program Files/ImageMagick-7.1.2-Q16-HDRI/magick.exe")

# Every UUID an item needs. tools/new_item.py fills these with fresh random values; they
# must never change once an item has been played, or saves lose the item.
BASE_ID_KEYS = ['mod', 'item', 'name_handle', 'desc_handle']
# Only items with their own visuals (built on a garment) need these.
GARMENT_ID_KEYS = ['preset', 'nm', 'pm',
                   'material_M', 'bm_M', 'msk_M', 'material_F', 'bm_F', 'msk_F']
ID_KEYS = BASE_ID_KEYS + GARMENT_ID_KEYS


class Item:
    def __init__(self, item_id):
        self.id = item_id
        self.dir = os.path.join('items', item_id)
        path = os.path.join(self.dir, 'item.json')
        if not os.path.exists(path):
            raise SystemExit('no item definition at %s' % path)
        self.cfg = json.load(open(path, encoding='utf-8'))
        # Three kinds of item:
        #   "garment": "<key>"  new textures on a vanilla garment's meshes (banks, preset)
        #   "custom": {...}     our own imported meshes (GR2), one visual per body type
        #   "base": {...}       reuses a vanilla item's look as-is; only stats, template,
        #                       text and optional spells (e.g. a ring)
        self.garment = GARMENTS[self.cfg['garment']] if self.cfg.get('garment') else None
        self.custom = self.cfg.get('custom')
        self.base = self.garment or self.custom or self.cfg['base']
        if self.garment:
            needed = ID_KEYS
        elif self.custom:
            # one texture set per imported mesh, named by its set code
            needed = BASE_ID_KEYS + ['preset', 'nm', 'pm'] + [
                k + '_' + s['code'] for s in self.base['sets'].values()
                for k in ('material', 'bm', 'msk', 'visual')]
        else:
            needed = BASE_ID_KEYS
        missing = [k for k in needed if k not in self.cfg.get('ids', {})]
        if missing:
            raise SystemExit('%s: ids missing %s' % (path, ', '.join(missing)))
        self.ids = self.cfg['ids']
        f = self.folder = self.cfg['folder']

        self.src = os.path.join(self.dir, 'src')
        self.public = '%s/Public/%s' % (self.src, f)
        # PATH MATTERS -- see tools/merge_banks.py.
        self.content = '%s/Content/Assets/Characters/[PAK]_%s' % (self.public, f)
        self.textures = '%s/Assets/Textures/Armor' % self.public
        self.texture_asset = 'Public/%s/Assets/Textures/Armor' % f   # as the game sees it
        self.work = os.path.join('build', 'work', item_id)
        os.makedirs(self.work, exist_ok=True)

    def __getitem__(self, k):
        return self.cfg[k]

    def get(self, k, default=None):
        return self.cfg.get(k, default)

    @property
    def stat(self):
        return self.cfg['stat']

    @property
    def icon(self):
        # Garment items render their own icon; base items reuse the vanilla item's.
        return self.base.get('icon') or 'Item_' + self.cfg['stat']

    def sets(self):
        """(tag, set definition, item-specific ids) per texture set."""
        for tag, s in self.base['sets'].items():
            c = s['code']
            yield tag, s, dict(material=self.ids['material_' + c], bm=self.ids['bm_' + c],
                               msk=self.ids['msk_' + c], visual=self.ids.get('visual_' + c))

    def extra_materials(self):
        """(tag, definition, ids) for "mod_materials": materials cloned from a vanilla one
        and painted a flat colour, for meshes another mod pairs with the garment (the
        pants worn under a robe) that are not part of the garment's own texture sets."""
        for s in self.cfg.get('mod_materials', []):
            c = s['code']
            missing = [k for k in ('material_' + c, 'bm_' + c, 'msk_' + c) if k not in self.ids]
            if missing:
                raise SystemExit('%s: ids missing %s' % (self.id, ', '.join(missing)))
            yield s['tag'], s, dict(material=self.ids['material_' + c], bm=self.ids['bm_' + c],
                                    msk=self.ids['msk_' + c], visual=None)


def load(argv=None):
    argv = sys.argv if argv is None else argv
    if len(argv) < 2:
        items = sorted(d for d in os.listdir('items') if os.path.isdir(os.path.join('items', d)))
        raise SystemExit('usage: %s <item>   (items: %s)' % (os.path.basename(argv[0]), ', '.join(items)))
    os.chdir(ROOT)
    return Item(argv[1])


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w', encoding='utf-8', newline='\n').write(text)
