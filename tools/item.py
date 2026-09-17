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
ID_KEYS = ['mod', 'item', 'name_handle', 'desc_handle', 'preset', 'nm', 'pm',
           'material_M', 'bm_M', 'msk_M', 'material_F', 'bm_F', 'msk_F']


class Item:
    def __init__(self, item_id):
        self.id = item_id
        self.dir = os.path.join('items', item_id)
        path = os.path.join(self.dir, 'item.json')
        if not os.path.exists(path):
            raise SystemExit('no item definition at %s' % path)
        self.cfg = json.load(open(path, encoding='utf-8'))
        missing = [k for k in ID_KEYS if k not in self.cfg.get('ids', {})]
        if missing:
            raise SystemExit('%s: ids missing %s' % (path, ', '.join(missing)))
        self.ids = self.cfg['ids']
        self.garment = GARMENTS[self.cfg['garment']]
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
        return 'Item_' + self.cfg['stat']

    def sets(self):
        """(tag, garment set, item-specific ids) per texture set."""
        for tag, s in self.garment['sets'].items():
            c = s['code']
            yield tag, s, dict(material=self.ids['material_' + c], bm=self.ids['bm_' + c],
                               msk=self.ids['msk_' + c])


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
