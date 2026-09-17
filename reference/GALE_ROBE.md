# Gale's robe — traced asset chain

Everything below was read directly out of the Patch 8 `.pak` files on this machine
(`Data/Shared.pak`, `Data/Gustav.pak`, `Data/Textures.pak`) using `tools/bg3extract.py`.

## Naming note

There is **no `CONT_Gale_Robe`** anywhere in the Patch 8 data — no file, no stat entry,
no root template. (`CONT_` is the prefix BG3 uses for containers, e.g. `CONT_GEN_Pouch_Leather_Gale_A`.)
The robe Gale wears when you recruit him is:

| | |
|---|---|
| Stat entry | `UNI_GaleRobe` (in `Public/Shared/Stats/Generated/Data/Armor.txt`) |
| Inherits from | `ARM_Robe_Body` |
| Root template | `9410a467-3e49-4b14-b067-ea8ad6a0d431` |
| Parent template | `168b9099-19f5-44e4-b55c-e64ceb60b71f` (`ARM_Robe_Body`) |

Confirmed via `ORIGIN_Gale` → `Equipment "EQ_Gale"` → `add equipment entry "UNI_GaleRobe"`
in `Public/Gustav/Stats/Generated/Equipment.txt`.

## The chain

```
UNI_GaleRobe (Armor.txt)
  └─ RootTemplate 9410a467-3e49-4b14-b067-ea8ad6a0d431
       ├─ Equipment > VisualSet > MaterialOverrides > MaterialPresets
       │     GroupName "02 Colour"
       │     MaterialPresetResource fb21807c-fb57-194d-e7c8-848b37a4fb24  ("ARM_Robe_A_Purple_2")
       │     ForcePresetValues True
       └─ Equipment > Visuals  — 14 body types x 2 visual resources each
```

**Gale's robe is not a unique mesh or a unique texture.** It is the shared `ARM_Robe_A`
mesh and texture set, plus a colour preset. That is very good news for this mod: the
artwork is the only thing you actually have to make.

## Visual resources (human male shown; 13 other body types follow the same pattern)

Defined in `Public/Shared/Content/Assets/Characters/Humans/[PAK]_Male_Armor/_merged.lsf`.

| Visual UUID | Name | GR2 |
|---|---|---|
| `55ac285b-cf5b-10ff-fb13-e15871509bc2` | `HUM_M_ARM_Robe_A_Body` | `Generated/Public/Shared/Assets/Characters/_Models/Humans/_Male/Resources/HUM_M_ARM_Robe_A_Body.GR2` |
| `f0d258d2-e455-8c1e-cd8d-90e32862c559` | `HUM_M_ARM_Padded_A_Pants` | `.../HUM_M_ARM_Padded_A_Pants.GR2` |

The robe visual contains three submeshes, each with its own material:

| Submesh | Material UUID |
|---|---|
| `HUM_M_ARM_Robe_A_Bracers_mesh.0` | `7b563708-ffb9-4b6b-0974-cc4c7459be4b` |
| `HUM_M_ARM_Robe_A_Body_mesh.1` | `92cca1dc-071f-1a40-6eb3-de8e16a38c25` |
| `HUM_M_ARM_Robe_A_Body_Cloth_mesh.2` | `9e2966c7-b61c-4bc1-bef1-a79cb5fde067` |

Each exists at LOD 0 and LOD 1.

### Full visual list (all body types)

| Body type | Visual 1 | Visual 2 |
|---|---|---|
| Human M | `f0d258d2-e455-8c1e-cd8d-90e32862c559` | `55ac285b-cf5b-10ff-fb13-e15871509bc2` |
| Human F | `4084d9c1-de9e-bb68-f0bc-0395ad80357b` | `c80e582d-0f68-62a3-bc89-5738d2000319` |
| Human MStrong | `2e258f47-67c9-95f0-363f-c43f6c71b848` | `db52dade-8e5b-06c4-fb5d-3b0e8fbfffff` |
| Human FStrong | `4ab5c8fc-50bc-5c8f-09b9-24f8087298c9` | `5773313e-0a86-61dc-0862-5bb582a543af` |
| Githyanki M | `20bc20ab-790c-c4e8-a767-624c7bd1fba5` | `cd54ff9e-8166-ed27-d017-36e5d6ce27cf` |
| Githyanki F | `4e5d0444-0534-5b25-63d5-c28ef4ebf9c4` | `122fa9ad-bef1-9025-72ad-2042945a173c` |
| Dwarf M | `bfad9105-bcb0-ba67-3118-bb98f755bfd7` | `64ab37be-810e-79c7-d54c-a3cb3add0ba8` |
| Dwarf F | `55eb99d6-5111-56ca-6d7f-1d13853b46c9` | `050b510a-1b1e-b51c-7cbd-092bf58497c1` |
| Halfling M | `606afe8d-0e23-4235-b030-aa4711cce78c` | `2403a22b-d5ba-76bf-f804-0c829d8ef88c` |
| Halfling F | `6e90521b-99a8-c6b2-9ee8-98c3d59dc810` | `6ae7dab9-20f3-c217-a4c9-bebdfbb3cdd5` |
| Gnome M | `c1ec9ec0-ee2b-4e84-05c2-42bc6f5ec678` | `9af60b2f-38a6-555e-b10e-53fb6889c338` |
| Gnome F | `a98bd41c-e546-7f8a-152f-5ee21c2fc356` | `7fa9cc42-d550-919d-7d17-6eb81af620ed` |
| Dragonborn M | `986e9f22-f472-e5f8-c3d7-3a2dc7e31c88` | `9d59c45a-a615-5509-9b58-85c4806f3b0b` |
| Dragonborn F | `c927e2f2-d419-5af4-db91-0e48d574990d` | `d3d9077b-2f03-35d3-8668-a93fffd774ab` |

Because the new root template sets `ParentTemplateId` to Gale's robe, **all of these are
inherited automatically** — you do not need to redeclare them.

## The body material — `HUM_M_ARM_Robe_A_Body` (`92cca1dc-…`)

Shader: `Public/Shared/Assets/Materials/Characters/CHAR_BASE_VertCut_VT.lsf`

`_VT` means **virtual texture**. This is the single most important technical fact in
this document — see "The virtual-texture problem" in the README.

### Texture inputs

| Parameter | Group | ID | Backing file |
|---|---|---|---|
| `virtualtexture` | Texture Map | `0add4504-6f30-f198-264c-0a915b0f0b02` | virtual tile set, `GTexFileName d9da4c1dce75cfb2ddef0729e5572df9`, `VirtualTextureLayerConfig 3` |
| `MSKColor` | 01 Texture Map | `daa331f2-e8dd-e70d-bdb1-66fcded6f7af` | `Generated/Public/Shared/Assets/Characters/_Models/Humans/HUM_ARM_Robes/Resources/HUM_M_ARM_Robe_A_MSKcloth.DDS` |
| `VertexColor_MSK` | — | `8f1f209a-dd37-4531-b1ee-5e81c1d169cc` | disabled on this material |

The base colour / normal / physical maps are **inside the virtual tile set** (layer config 3
= three layers). The colour mask is a **plain DDS** and is directly editable.

`HUM_M_ARM_Robe_A_MSKcloth.DDS` — 2048x2048, DXT1, 12 mips, `SRGB False`.
A copy is in `extracted/` for reference.

### Colour slots (`GroupName "02 Colour"`, Vector3, IsColor)

| Parameter | Enabled on vanilla robe |
|---|---|
| `Cloth_Primary` | yes |
| `Cloth_Secondary` | yes |
| `Cloth_Tertiary` | yes |
| `Leather_Primary` | yes |
| `Leather_Secondary` | yes |
| `Metal_Primary` | yes |
| `Accent_Color` | no |
| `Leather_Tertiary` | no |
| `Metal_Secondary` | no |
| `Metal_Tertiary` | no |
| `Custom_1` | no |
| `Custom_2` | no |

## How the mask encodes the slots — measured

Histogram of every DXT1 block endpoint across mip 0 of `HUM_M_ARM_Robe_A_MSKcloth.DDS`
(524,288 endpoints), snapped to the nearest 64:

| Mask colour | Share of endpoints |
|---|---|
| `#FF8000` orange | 413,691 |
| `#0000FF` blue | 32,293 |
| `#8000FF` violet | 28,141 |
| `#FF0000` red | 22,796 |
| `#00FF80` spring green | 19,292 |
| `#FF8080` salmon | 7,634 |
| (edge blends) | < 400 total |

**Six ID colours, six enabled colour slots.** The mask is an ID map: each texel is
tagged with a saturated key colour that selects which of the "02 Colour" vectors tints it.

**There is no black in the vanilla mask — 0 of 524,288 endpoints were near-black.**
Every texel is assigned to some slot. This matters for the dye-proofing plan; see the README.

## What a dye actually overrides

Gale's own preset `fb21807c-fb57-194d-e7c8-848b37a4fb24` (`ARM_Robe_A_Purple_2`),
in `Public/Shared/Content/Assets/Characters/[PAK]_Character_Presets/_merged.lsf`,
writes **every** colour slot — including the ones the material has disabled:

```
Accent_Color       (0.164, 0.130, 0.393)
Cloth_Primary      (0.123, 0.080, 0.215)
Cloth_Secondary    (0.205, 0.056, 0.056)
Cloth_Tertiary     (0.701, 0.680, 0.759)
Custom_1           (0.734, 0.515, 0.359)
Custom_2           (1.000, 1.000, 1.000)
Leather_Primary    (0.116, 0.079, 0.064)
Leather_Secondary  (0.157, 0.087, 0.033)
...
```

Dye items work the same way — e.g. `OBJ_Dye_Azure` → root template
`eedbd9cc-5072-47fd-90a6-36a24c435620` → `ColorPreset 85fc7553-b1ca-cb0c-0c60-0a2db41f6cc0`.

**Consequence:** you cannot protect artwork by parking it on `Custom_1` / `Custom_2` /
`Accent_Color`. Presets write those too. Protection has to happen in the mask.
