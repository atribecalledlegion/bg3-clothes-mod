"""Base garments an item can be built on.

Everything here is a property of the VANILLA garment -- its parent template, its meshes,
its materials, the texture file names its material slots expect. None of it changes from
one item to the next, which is what lets a new item be only an item.json and some art.

An item picks a garment with "garment": "<key>" in its item.json.

Mesh and bank paths point into extracted/, which is local only (Larian's files, not
redistributed). Re-extract with tools/bg3extract.py and Divine convert-model; see
reference/UV_PLACEMENT.md.
"""

GARMENTS = {
    'gale_robe': dict(
        label="Gale's starting robe",
        stat_parent='UNI_GaleRobe',
        parent_template='9410a467-3e49-4b14-b067-ea8ad6a0d431',
        # "ARM_Robe_A_Purple_2" -- the preset Gale's template forces onto "02 Colour".
        # Cloned (all white) so the item can override it; see tools/make_preset.py.
        colour_preset='fb21807c-fb57-194d-e7c8-848b37a4fb24',
        # Suffix of the vanilla visual resource names to clone, one per body type.
        visual_suffix='_ARM_Robe_A_Body',
        # Two texture sets. Each vanilla material is shared by several body types:
        # masculine -> HUM_M, HUM_MS, DWR_M, GNO_M, GTY_M, HFL_M
        # feminine  -> HUM_F, HUM_FS, DWR_F, GNO_F, GTY_F, HFL_F
        # Dragonborn uses its own materials and is not covered.
        #
        # The visual's other submeshes are left alone: Bracers keep their vanilla
        # material, and Body_Cloth is the invisible cloth-simulation proxy (its material
        # 9e2966c7 is an engine placeholder shared by test chains and reference weapons).
        sets=dict(
            masculine=dict(
                code='M',
                vanilla_material='HUM_M_ARM_Robe_A_Body',
                vanilla_material_id='92cca1dc-071f-1a40-6eb3-de8e16a38c25',
                bank='extracted/mesh/HUM_M_Armor.lsf',
                mesh=('extracted/mesh/robe.dae', 'HUM_M_ARM_Robe_A_Body_mesh'),
                vanilla_mask='extracted/mesh/HUM_M_ARM_Robe_A_MSKcloth.DDS',
                bm='HUM_M_ARM_Robe_A_BM.DDS',
                msk='HUM_M_ARM_Robe_A_MSKcloth.DDS',
            ),
            feminine=dict(
                code='F',
                vanilla_material='HUM_F_ARM_Robe_A_Body',
                vanilla_material_id='4bf29629-687c-5330-bce8-8d22432941c8',
                bank='extracted/mesh/HUM_F_Armor.lsf',
                mesh=('extracted/mesh/HUM_F.dae', 'HUM_F_ARM_Robe_A_Body_Mesh'),
                vanilla_mask='extracted/mesh/HUM_F_ARM_Robe_A_Body_MSKcloth.DDS',
                bm='HUM_F_ARM_Robe_A_Body_BM.DDS',
                msk='HUM_F_ARM_Robe_A_Body_MSKcloth.DDS',
            ),
        ),
        visual_banks=[
            'Humans/[PAK]_Male_Armor', 'Humans/[PAK]_Female_Armor',
            'Humans/[PAK]_MaleStrong_Armor', 'Humans/[PAK]_FemaleStrong_Armor',
            'Githyanki/[PAK]_Male_Armor', 'Githyanki/[PAK]_Female_Armor',
            'Dwarves/[PAK]_Male_Armor', 'Dwarves/[PAK]_Female_Armor',
            'Halflings/[PAK]_Male_Armor', 'Halflings/[PAK]_Female_Armor',
            'Gnomes/[PAK]_Male_Armor', 'Gnomes/[PAK]_Female_Armor',
            'Dragonborn/[PAK]_Male_Armor', 'Dragonborn/[PAK]_Female_Armor',
        ],
    ),
}
