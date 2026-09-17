"""Write the item's small text files from item.json:

    Mods/<Folder>/meta.lsx
    Localization/English/<Folder>.xml
    Public/<Folder>/Stats/Generated/Data/Armor.txt
    Public/<Folder>/Stats/Generated/TreasureTable.txt

Usage:  python tools/make_mod_files.py <item>
"""
import sys, os
from xml.sax.saxutils import escape
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import item as itemlib

META = '''<?xml version="1.0" encoding="UTF-8"?>
<save>
    <version major="4" minor="0" revision="9" build="331" />
    <region id="Config">
        <node id="root">
            <children>
                <node id="Dependencies" />
                <node id="ModuleInfo">
                    <attribute id="Author" type="LSString" value="{author}" />
                    <attribute id="CharacterCreationLevelName" type="FixedString" value="" />
                    <attribute id="Description" type="LSString" value="{description}" />
                    <attribute id="Folder" type="LSString" value="{folder}" />
                    <attribute id="GMTemplate" type="FixedString" value="" />
                    <attribute id="LobbyLevelName" type="FixedString" value="" />
                    <attribute id="MD5" type="LSString" value="" />
                    <attribute id="MainMenuBackgroundVideo" type="FixedString" value="" />
                    <attribute id="MenuLevelName" type="FixedString" value="" />
                    <attribute id="Name" type="LSString" value="{name}" />
                    <attribute id="NumPlayers" type="uint8" value="4" />
                    <attribute id="PhotoBooth" type="FixedString" value="" />
                    <attribute id="StartupLevelName" type="FixedString" value="" />
                    <attribute id="Tags" type="LSString" value="" />
                    <attribute id="Type" type="FixedString" value="Add-on" />
                    <attribute id="UUID" type="FixedString" value="{uuid}" />
                    <attribute id="Version64" type="int64" value="36028797018963968" />
                    <children>
                        <node id="PublishVersion">
                            <attribute id="Version64" type="int64" value="36028797018963968" />
                        </node>
                        <node id="Scripts" />
                        <node id="TargetModes">
                            <children>
                                <node id="Target">
                                    <attribute id="Object" type="FixedString" value="Story" />
                                </node>
                            </children>
                        </node>
                    </children>
                </node>
            </children>
        </node>
    </region>
</save>
'''

LOCA = '''<?xml version="1.0" encoding="utf-8"?>
<contentList>
    <content contentuid="{nameh}" version="1">{name}</content>
    <content contentuid="{desch}" version="1">{desc}</content>
</contentList>
'''

ARMOR = '''// {name} -- based on {garment} ({parent}).
// "using" inherits ArmorClass / Weight / slot / proficiency from the vanilla entry,
// so only the differences need to be stated here.

new entry "{stat}"
type "Armor"
using "{parent}"
data "RootTemplate" "{item}"
data "Rarity" "{rarity}"
data "ValueLevel" "{value}"
data "Unique" "1"
'''

TREASURE_HEAD = '''// PATH MATTERS: this file must live at Stats/Generated/TreasureTable.txt, NOT in the
// Stats/Generated/Data/ subfolder where Armor.txt goes. Vanilla splits them exactly that
// way (Data/Armor.txt, Data/Object.txt, but Generated/TreasureTable.txt and
// Generated/Equipment.txt). Put it under Data/ and the game ignores it silently -- the
// mod loads, the item exists, and the chest is simply empty.
//
// TUT_Chest_Potions puts the item in the tutorial chest on the nautiloid.
//
// Traced rather than guessed: the chest placed in TUT_Avernus_C is the level instance
// "S_Chest_Potions" (template CONT_MF_Chest_A, 813c005f-72ab-4806-ad7e-2e3135e41d27).
// Its contents are not set on the root template or by story script -- the instance
// carries InventoryList > InventoryItem > "TUT_Chest_Potions", so extending that table
// is what reaches the chest.
//
// CanMerge 1 is essential, and is a real Larian directive (see DEN_Entrance_Trade,
// DEN_Ethel, FOR_Spiders_SpiderQueen in GustavDev). Without it this REPLACES the vanilla
// table and the chest's healing potions disappear.
//
// The subtable weighting "1,1" means one roll, guaranteed, so exactly one item appears.
'''

TREASURE = '''
new treasuretable "{table}"
CanMerge 1
new subtable "1,1"
object category "I_{stat}",1,0,0,0,0,0,0,0
'''

def main():
    it = itemlib.load()
    f, g = it.folder, it.garment
    files = {
        '%s/Mods/%s/meta.lsx' % (it.src, f): META.format(
            author=escape(it['author'], {'"': '&quot;'}),
            description=escape(it['mod_description'], {'"': '&quot;'}),
            folder=f, name=escape(it['name'], {'"': '&quot;'}), uuid=it.ids['mod']),
        '%s/Localization/English/%s.xml' % (it.src, f): LOCA.format(
            nameh=it.ids['name_handle'], desch=it.ids['desc_handle'],
            name=escape(it['display_name']), desc=escape(it['description'])),
        '%s/Stats/Generated/Data/Armor.txt' % it.public: ARMOR.format(
            name=it['name'], garment=g['label'], parent=g['stat_parent'], stat=it.stat,
            item=it.ids['item'], rarity=it.get('rarity', 'Rare'), value=it.get('value_level', 5)),
    }
    tables = it.get('treasure_tables', [])
    if tables:
        files['%s/Stats/Generated/TreasureTable.txt' % it.public] = TREASURE_HEAD + ''.join(
            TREASURE.format(table=t, stat=it.stat) for t in tables)
    for path, text in files.items():
        itemlib.write(path, text)
        print('wrote', path)

if __name__ == '__main__':
    main()
