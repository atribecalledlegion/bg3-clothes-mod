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
{dependencies}
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
                    <attribute id="Version64" type="int64" value="{version64}" />
                    <children>
                        <node id="PublishVersion">
                            <attribute id="Version64" type="int64" value="{version64}" />
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
data "Unique" "{unique}"
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

SPELL_HEAD = '''// Spells granted by the item (Boosts UnlockSpell in Armor.txt).
//
// Each is a copy of a vanilla spell ("using") with only its cost and cooldown replaced.
// Removing SpellSlotsGroup from UseCosts is what makes the cast free; the action or bonus
// action it needs is kept. Vanilla does the same for item spells, e.g.
// Target_MAG_Druid_Armor_PlantGrowth: using Target_PlantGrowth, UseCosts ActionPoint:1,
// Cooldown OncePerShortRestPerItem.
//
// Copies are granted rather than the originals: unlocking Target_Entangle itself would
// cast from the wearer's spell slots, and a character with none could not use it.
'''

SPELL = '''
new entry "{name}"
type "SpellData"
data "SpellType" "{type}"
using "{base}"
data "UseCosts" "{costs}"
data "Cooldown" "{cooldown}"
'''

DEPENDENCY = '''                        <node id="ModuleShortDesc">
                            <attribute id="Folder" type="FixedString" value="{folder}" />
                            <attribute id="MD5" type="LSString" value="" />
                            <attribute id="Name" type="FixedString" value="{name}" />
                            <attribute id="UUID" type="FixedString" value="{uuid}" />
                            <attribute id="Version64" type="int64" value="{version64}" />
                        </node>
'''


def dependencies_xml(it):
    """item.json "dependencies": [{"name", "folder", "uuid", "version64"}] -> the meta.lsx
    Dependencies node. A dependency makes the game and BG3 Mod Manager load that mod first
    and warn when it is missing -- right for an add-on that only works with another mod."""
    deps = it.get('dependencies', [])
    if not deps:
        return '                <node id="Dependencies" />'
    rows = ''.join(DEPENDENCY.format(folder=d['folder'], name=escape(d['name'], {'"': '&quot;'}),
                                     uuid=d['uuid'], version64=d['version64']) for d in deps)
    return ('                <node id="Dependencies">\n                    <children>\n' + rows +
            '                    </children>\n                </node>')


def version64(it):
    """Pack major.minor.revision.build into the Version64 Larian's own tools use.

    "build" in item.json is a plain counter: bump it by hand each time a changed pak
    is rebuilt, so BG3 Mod Manager (and the game, which keys a save's mod list by this
    number) sees a new version instead of silently keeping the old pak's data cached.
    """
    major, minor, revision = it.get('major', 1), it.get('minor', 0), it.get('revision', 0)
    build = it.get('build', 1)
    return (major << 55) | (minor << 47) | (revision << 31) | build


def spell_entry(folder, s):
    """item.json spell -> (new spell name, stats text).
    {"spell": "Target_Entangle", "use_costs": "ActionPoint:1", "cooldown": "OncePerTurn"}"""
    kind, rest = s['spell'].split('_', 1)          # the prefix is the SpellType
    name = '%s_%s_%s' % (kind, folder, rest)
    return name, SPELL.format(name=name, type=kind, base=s['spell'],
                              costs=s['use_costs'], cooldown=s.get('cooldown', 'OncePerTurn'))

def main():
    it = itemlib.load()
    f, g = it.folder, it.base
    spells = [spell_entry(f, s) for s in it.get('spells', [])]
    boosts = ''
    if spells:
        # UnlockSpell(Spell, ChildSelection, Resource, Cooldown, Ability): the fifth argument
        # fixes the ability behind the spell's save DC and attack rolls, instead of the
        # wearer's class spellcasting ability. Vanilla: UnlockSpell(Target_TrueStrike,,,,Wisdom).
        # Set "spell_ability" on the item, or "ability" on one spell.
        def unlock(name, s):
            ability = s.get('ability', it.get('spell_ability'))
            return 'UnlockSpell(%s,,,,%s)' % (name, ability) if ability else 'UnlockSpell(%s)' % name
        boosts = 'data "Boosts" "%s"\n' % ';'.join(
            unlock(name, s) for (name, _), s in zip(spells, it.get('spells')))
    files = {
        '%s/Mods/%s/meta.lsx' % (it.src, f): META.format(
            author=escape(it['author'], {'"': '&quot;'}),
            description=escape(it['mod_description'], {'"': '&quot;'}),
            folder=f, name=escape(it['name'], {'"': '&quot;'}), uuid=it.ids['mod'],
            version64=version64(it), dependencies=dependencies_xml(it)),
        '%s/Localization/English/%s.xml' % (it.src, f): LOCA.format(
            nameh=it.ids['name_handle'], desch=it.ids['desc_handle'],
            name=escape(it['display_name']), desc=escape(it['description'])),
        '%s/Stats/Generated/Data/Armor.txt' % it.public: ARMOR.format(
            name=it['name'], garment=g['label'], parent=g['stat_parent'], stat=it.stat,
            item=it.ids['item'], rarity=it.get('rarity', 'Rare'), value=it.get('value_level', 5),
            # A Unique item is generated by treasure tables only while none exists in
            # the game. TutorialChestSummoning spawns a fresh chest that re-rolls
            # TUT_Chest_Potions on every cast, so a unique item appears in the first
            # chest and never again. Set "unique": false to get one per chest.
            unique='1' if it.get('unique', True) else '0') + boosts,
    }
    if spells:
        files['%s/Stats/Generated/Data/Spell_%s.txt' % (it.public, f)] = SPELL_HEAD + ''.join(
            text for _, text in spells)
    tables = it.get('treasure_tables', [])
    if tables:
        files['%s/Stats/Generated/TreasureTable.txt' % it.public] = TREASURE_HEAD + ''.join(
            TREASURE.format(table=t, stat=it.stat) for t in tables)
    for path, text in files.items():
        itemlib.write(path, text)
        print('wrote', path)
    print('version %d.%d.%d build %d' % (it.get('major', 1), it.get('minor', 0),
                                          it.get('revision', 0), it.get('build', 1)))

if __name__ == '__main__':
    main()
