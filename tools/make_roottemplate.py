"""Generate the item's RootTemplates/_merged.lsx.

Usage:  python tools/make_roottemplate.py <item>     (garment items: after make_visuals_node.py)

Written whole each time rather than patched: the Visuals block is deeply nested, and a
regex splice against it is how the file got a duplicated fragment and unbalanced tags.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import item as itemlib

# The item inherits Equipment from the parent template, which for Gale's robe carries a
# MaterialPresets override applying "ARM_Robe_A_Purple_2" with ForcePresetValues=True.
# That preset writes every "02 Colour" slot and beats the material's own values -- which
# is why neutralising the material alone changed nothing and the Obito crest's white half
# kept rendering orange. Overriding it here with the item's all-white preset
# (make_preset.py) is what lets the base texture render as painted.

VISUALSET = '''								<node id="VisualSet">
									<attribute id="BodySetVisual" type="FixedString" value="" />
									<attribute id="ShowEquipmentVisuals" type="bool" value="False" />
									<children>
										<node id="MaterialOverrides">
											<attribute id="MaterialResource" type="FixedString" value="" />
											<children>
												<node id="MaterialPresets">
													<children>
														<node id="Object">
															<attribute id="MapKey" type="FixedString" value="02 Colour" />
															<attribute id="GroupName" type="FixedString" value="02 Colour" />
															<attribute id="MaterialPresetResource" type="FixedString" value="{preset}" />
															<attribute id="ForcePresetValues" type="bool" value="True" />
														</node>
													</children>
												</node>
											</children>
										</node>
										<node id="RealMaterialOverrides" />
									</children>
								</node>
'''

HEAD = '''<?xml version="1.0" encoding="utf-8"?>
<save>
	<version major="4" minor="0" revision="9" build="0" lslib_meta="v1,bswap_guids,lsf_adjacency" />
	<region id="Templates">
		<node id="Templates">
			<children>
				<node id="GameObjects">
					<attribute id="MapKey" type="FixedString" value="{item}" />
					<attribute id="Name" type="LSString" value="{stat}" />
					<attribute id="Type" type="FixedString" value="item" />
					<attribute id="Stats" type="FixedString" value="{stat}" />
					<attribute id="ParentTemplateId" type="FixedString" value="{parent}" />
					<attribute id="DisplayName" type="TranslatedString" handle="{nameh}" version="1" />
					<attribute id="Description" type="TranslatedString" handle="{desch}" version="1" />
					<attribute id="Icon" type="FixedString" value="{icon}" />
'''

EQUIPMENT_OPEN = '''					<children>
						<node id="Equipment">
							<children>
'''

EQUIPMENT_CLOSE = '''							</children>
						</node>
					</children>
'''

TAIL = '''				</node>
			</children>
		</node>
	</region>
</save>
'''

def main():
    it = itemlib.load()
    doc = HEAD.format(item=it.ids['item'], parent=it.base['parent_template'],
                      nameh=it.ids['name_handle'], desch=it.ids['desc_handle'],
                      stat=it.stat, icon=it.icon)
    if it.garment or it.custom:
        vis = open(os.path.join(it.work, 'visuals_node.xml'), encoding='utf-8').read().rstrip('\n')
        doc += EQUIPMENT_OPEN + VISUALSET.format(preset=it.ids['preset'])
        doc += vis + '\n' + EQUIPMENT_CLOSE
    # A base item (e.g. a ring) inherits its whole appearance from the parent template.
    doc += TAIL
    out = it.public + '/RootTemplates/_merged.lsx'
    itemlib.write(out, doc)
    n = doc.count('id="MapKey" type="guid"')
    # Parse it rather than counting tags: self-closing nodes such as
    # <node id="RealMaterialOverrides" /> are valid but make a naive open/close count
    # look unbalanced.
    import xml.etree.ElementTree as ET
    try:
        root = ET.fromstring(doc)
        nodes = sum(1 for _ in root.iter('node'))
        status = 'valid XML, %d nodes' % nodes
    except ET.ParseError as e:
        status = 'INVALID XML: %s' % e
    print('wrote %s' % out)
    print('  race MapKeys : %d' % n)
    print('  structure    : %s' % status)

if __name__ == '__main__':
    main()
