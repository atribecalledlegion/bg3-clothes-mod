"""Scaffold a new item with fresh UUIDs.

    python tools/new_item.py <item_id> <Folder> "<Display Name>" [garment]

    python tools/new_item.py akatsuki_cloak AkatsukiCloak "Akatsuki Cloak"

Writes items/<item_id>/item.json. Fill in the descriptions and the "bake" block (or an
"art" command), then run tools/build_item.py.

Every item needs its own IDs -- mod, item template, localisation handles, materials,
textures, preset. Reusing another item's would make the two mods overwrite each other's
resources when both are enabled. Never change them after an item has been played: a save
refers to the item template by UUID.
"""
import json, os, sys, uuid
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from item import ID_KEYS, ROOT
from garment import GARMENTS


def handle():
    # Larian localisation handles: 'h' + a UUID with 'g' in place of '-'
    return 'h' + str(uuid.uuid4()).replace('-', 'g')


def main():
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)
    item_id, folder, name = sys.argv[1:4]
    garment = sys.argv[4] if len(sys.argv) > 4 else 'gale_robe'
    if garment not in GARMENTS:
        raise SystemExit('unknown garment %r (have: %s)' % (garment, ', '.join(GARMENTS)))
    path = os.path.join(ROOT, 'items', item_id, 'item.json')
    if os.path.exists(path):
        raise SystemExit('%s already exists -- not overwriting its IDs' % path)
    ids = {k: (handle() if k.endswith('_handle') else str(uuid.uuid4())) for k in ID_KEYS}
    cfg = {
        'name': name,
        'folder': folder,
        'author': 'dawil',
        'mod_description': '',
        'garment': garment,
        'stat': 'UNI_' + folder,
        'display_name': name,
        'description': '',
        'rarity': 'Rare',
        'value_level': 5,
        'treasure_tables': ['TUT_Chest_Potions'],
        'visual_prefix': folder + '_',
        'neutral_maps': {'nm': '#8080FF', 'pm': '#06D4E6'},
        'icon_view': 'back',
        'bake': {'ground': '#141416', 'mask': '#0000FF', 'supersample': 2,
                 'images': {}, 'decals': []},
        'ids': ids,
    }
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(cfg, f, indent=2)
        f.write('\n')
    print('wrote', path)


if __name__ == '__main__':
    main()
