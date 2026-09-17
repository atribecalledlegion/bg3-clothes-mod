"""Generate the item's RootTemplates/_merged.lsx.

Written whole each time rather than patched: the Visuals block is deeply nested, and a
regex splice against it is how the file got a duplicated fragment and unbalanced tags.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

OUT = 'src/Public/ObitoUchihaRobe/RootTemplates/_merged.lsx'
VIS = 'art/source/visuals_node.xml'

ITEM_UUID   = 'db53c125-9430-415a-aa2e-4899db9d4c24'
GALE_ROBE   = '9410a467-3e49-4b14-b067-ea8ad6a0d431'
NAME_HANDLE = 'h9a7fd611g3175g4107gbfcbgf05c931ea2b3'
DESC_HANDLE = 'h964ecfbeg7de6g48d3ga62fg4b71f54728a7'

# The item inherits Equipment from Gale's robe, which carries a MaterialPresets override
# applying "ARM_Robe_A_Purple_2" with ForcePresetValues=True. That preset writes every
# "02 Colour" slot and beats the material's own values -- which is why neutralising the
# material alone changed nothing and the crest's white half kept rendering orange.
# Overriding it here with an all-white preset is what lets the base texture render as
# painted.
PRESET_UUID = 'cd56b336-e7de-4c94-afba-40776b39e153'

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
					<attribute id="Name" type="LSString" value="UNI_ObitoUchihaRobe" />
					<attribute id="Type" type="FixedString" value="item" />
					<attribute id="Stats" type="FixedString" value="UNI_ObitoUchihaRobe" />
					<attribute id="ParentTemplateId" type="FixedString" value="{gale}" />
					<attribute id="DisplayName" type="TranslatedString" handle="{nameh}" version="1" />
					<attribute id="Description" type="TranslatedString" handle="{desch}" version="1" />
					<attribute id="Icon" type="FixedString" value="Item_UNI_ObitoUchihaRobe" />
					<children>
						<node id="Equipment">
							<children>
'''

TAIL = '''							</children>
						</node>
					</children>
				</node>
			</children>
		</node>
	</region>
</save>
'''

def main():
    vis = open(VIS, encoding='utf-8').read().rstrip('\n')
    doc = HEAD.format(item=ITEM_UUID, gale=GALE_ROBE, nameh=NAME_HANDLE, desch=DESC_HANDLE)
    doc += VISUALSET.format(preset=PRESET_UUID)
    doc += vis + '\n' + TAIL
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, 'w', encoding='utf-8', newline='\n').write(doc)
    n = doc.count('id="MapKey" type="guid"')
    # Parse it rather than counting tags: self-closing nodes such as
    # <node id="RealMaterialOverrides" /> are valid but make a naive open/close count
    # look unbalanced.
    import xml.etree.ElementTree as ET
    try:
        root = ET.fromstring(doc)
        nodes = len(root.iter('node'))if False else sum(1 for _ in root.iter('node'))
        status = 'valid XML, %d nodes' % nodes
    except ET.ParseError as e:
        status = 'INVALID XML: %s' % e
    print('wrote %s' % OUT)
    print('  race MapKeys : %d' % n)
    print('  structure    : %s' % status)

if __name__ == '__main__':
    main()
