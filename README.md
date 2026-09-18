# BG3 clothes mods

Custom Baldur's Gate 3 clothing, built on vanilla garments by a shared, config-driven
pipeline. Each item is a folder under `items/`; the tools are shared.

| Item | Look | Art step |
|---|---|---|
| [`obito_uchiha_robe`](items/obito_uchiha_robe) | purple robe, Uchiha crest on the back | crest composited in UV space (`art/make_textures.sh`) |
| [`akatsuki_cloak`](items/akatsuki_cloak) | black robe, red clouds front, back and sleeves | decals baked in 3D (`tools/bake_decals.py`) |
| [`hashirama_cells`](items/hashirama_cells) | vanilla gold gem ring granting six nature spells | none: reuses the vanilla ring's look |
| [`naruto_outfit`](items/naruto_outfit) | orange jacket and trousers, imported from a 3D model | meshes cut, fitted and rigged (`tools/cut_static_mesh.py` -> `tools/make_custom_visual.py`) |

The robes are built on Gale's starting robe (`UNI_GaleRobe`) and cover every body type
except Dragonborn. The Naruto outfit is its own imported mesh and covers **human male
only**; it is unfinished (see its folder). Every item appears in the nautiloid tutorial
chest. They are separate mods and can be enabled together.

**Three kinds of item.**

* A *garment* item (`"garment": "gale_robe"`) paints new textures onto a vanilla garment's
  meshes, and gets its own banks, preset and icon.
* A *base* item (`"base": {...}`) keeps a vanilla item's appearance and only adds stats, a
  template, text and spells (the ring). Scaffold with
  `python tools/new_item.py <id> <Folder> "<Name>" none`.
* A *custom* item (`"custom": {...}`) ships **our own meshes** (GR2) for one or more body
  types, fitted and rigged to a vanilla garment's skeleton. See
  [importing a model](#importing-a-model).

**Spells.** List them under `"spells"`, e.g.
`{"spell": "Target_Entangle", "use_costs": "ActionPoint:1", "cooldown": "OncePerTurn"}`.
Each becomes a copy of the vanilla spell with no spell-slot cost, granted through
`UnlockSpell`, which is the same pattern vanilla magic items use.

---

## Build an item

```bash
python tools/build_item.py akatsuki_cloak --art
```

```powershell
.\build.ps1 -Item akatsuki_cloak -Install
```

Then enable the mod in BG3 Mod Manager. The item is in the tutorial chest on a new run
(TutorialChestSummoning can summon that chest), or spawn `UNI_AkatsukiCloak` with
SpawnAnyItem.

`--art` regenerates textures, neutral maps and the icon. Leave it off to regenerate only
the resources (banks, root template, text files); the committed DDS files are the result
that was checked in game, and should not change unless you mean them to.

**Close BG3 before `-Install`.** A running game locks the pak and the copy fails.

## Make a new item

```bash
python tools/new_item.py <item_id> <Folder> "<Display Name>"
```

This writes `items/<item_id>/item.json` with fresh UUIDs. Fill in the descriptions, then
either:

* **Decals** (recommended): put transparent PNGs in `items/<item_id>/art/source/`, list
  them under `bake.images`, and place them under `bake.decals`. Coordinates are relative
  to the garment, so one layout fits both body types. See the docstring of
  `tools/bake_decals.py` for every field.
* **Custom script**: set `"art": ["sh", "items/<item_id>/art/your_script.sh"]`. It must
  write the four texture-set DDS files and `build/work/<item_id>/built_masculine_BM.png`.

Iterate on a layout without writing textures:

```bash
python tools/bake_decals.py <item_id> --preview-only
```

This renders front/back/side views of both body types to
`build/work/<item_id>/preview_*.png`.

Never change an item's `ids` once it has been played: saves refer to the item by UUID.

Items are `Unique` by default. A unique item is only generated while none exists in
the game, so it appears in the first summoned tutorial chest and never again. Set
`"unique": false` (as the Akatsuki cloak does) to get one in every chest.

## Importing a model

An external model (a scan, or something generated) arrives as one fused static mesh with no
skeleton, so it cannot just be dropped in. The chain, each step a tool that can be re-run:

```bash
python tools/cut_static_mesh.py <model.glb> out.obj --texture <atlas> --y LO HI --drop-skin [--flip-v]
python tools/repose_sleeves.py out.obj posed.obj --shoulder X Y Z --target DX DY DZ --torso-half W
"…/blender.exe" -b -P tools/blender_fit_garment.py -- --vanilla <vanilla.gltf> --mesh posed.obj --out rigged.gltf
python tools/gltf_retarget.py <vanilla.gltf> rigged.gltf OUT.gltf
"…/Divine.exe" -g bg3 -a convert-model -s OUT.gltf -d OUT.GR2 -e export-uvs -e export-normals -e export-tangents
```

1. **Cut** the garment out by texture colour and height; whole pieces that are mostly skin
   (the hands) are dropped.
2. **Repose** sleeves onto the target skeleton's arm direction. BG3 rests with the arms 58
   degrees out; a model posed with arms down takes its bone weights from the chest and
   deforms into the body. Legs usually need no reposing.
3. **Fit** in Blender: scale onto the body, decimate to a game-sized triangle count, and
   copy bone weights from the vanilla garment.
4. **Retarget**, because LSLib's glTF importer crashes on Blender's skeleton layout: the
   vanilla file's nodes and bind matrices are kept and only the vertex data is swapped,
   with bones remapped by name.
5. **Convert** to GR2, then declare it with `tools/make_custom_visual.py`.

Then the item's `"custom"` block names, per body type, the vanilla visual to clone, the
material to replace and the GR2 to ship. Notes worth having:

* `--conform-path` binds to a vanilla skeleton but matches meshes BY NAME and copies the
  donor's LODs; it can also write the mesh twice. Not required, and the models here are
  built without it.
* The GR2 must ship under `Generated/Public/<Mod>/...` and the visual's `SourceFile` **and**
  `Template` must both point at it.
* `"hide_body_parts": false` unless the imported mesh really covers what the donor covered:
  a jacket with shorter sleeves otherwise leaves invisible arms and floating hands.
* A model's UV layout is often cut into many small islands. A grid test texture then looks
  like confetti in game **and** in an offline render -- that is correct, not a bug. Check by
  rendering the packed GR2 against the packed DDS, which reproduces what the game draws.

## Layout

```
items/<item>/
  item.json            names, stats, IDs, art step, decal layout
  art/                 item artwork and its scripts
  src/                 generated mod tree (committed; packed by build.ps1)
tools/
  build_item.py        runs every generator below, in order
  garment.py           per-garment facts: parent template, meshes, materials, texture names
  item.py              loads item.json, derives every path
  new_item.py          scaffolds an item with fresh UUIDs
  bake_decals.py       3D decal baking -> base colour + flat mask DDS, previews
  meshbake.py          UV rasteriser, decal projector, preview renderer (numpy)
  make_content_bank.py TextureBank + MaterialBank (clones the vanilla material)
  make_visual_bank.py  VisualBank (clones the 12 vanilla body visuals)
  make_visuals_node.py race -> visual map for the root template
  make_preset.py       all-white MaterialPresetBank (overrides the inherited dye preset)
  merge_banks.py       merges the banks into one _merged.lsx
  make_roottemplate.py the item's root template
  make_mod_files.py    meta.lsx, localisation, Armor.txt, TreasureTable.txt
  make_neutral_maps.py flat normal / physical maps
  make_icon.py         inventory icons, rendered from the mesh
  cut_static_mesh.py   cut a garment out of a fused imported model
  repose_sleeves.py    rotate sleeves onto the target skeleton's arm direction
  blender_fit_garment.py  fit, decimate and transfer bone weights (Blender, headless)
  gltf_retarget.py     rebuild a fitted mesh around a vanilla skeleton for LSLib
  make_custom_visual.py   VisualBank entries for our own GR2 meshes
  lspk.py, lsf.py, bg3extract.py   pak / LSF readers
reference/             garment research: GALE_ROBE.md, UV_PLACEMENT.md
extracted/             LOCAL ONLY -- Larian meshes and masks, reference downloads (ignored)
build/                 staging, intermediates, previews (ignored)
```

`extracted/mesh/` must hold the robe meshes (`robe.dae`, `HUM_F.dae`), the armour banks
(`HUM_M_Armor.lsf`, `HUM_F_Armor.lsf`) and the vanilla masks. They are Larian's files and
are not redistributed; `reference/UV_PLACEMENT.md` shows how to extract them.

---

## What has to be true for an item to render

Each of these failed silently at some point: no error, no log line. The generators now
handle all of them, and the comments where each is handled explain the cause.

| Requirement | What happens without it |
|---|---|
| GUIDs written with LSLib's `bswap_guids` byte order (`lsf.py`) | item equips, character is **naked** |
| every bank as a region of ONE `_merged.lsf` | naked, or banks ignored |
| banks under `Content/Assets/<Category>/[PAK]_<Folder>/` | item looks exactly like **Gale's purple robe** |
| all four shader inputs bound, even with flat maps | garment renders **pure black** |
| the item's own all-white colour preset, forced | artwork tinted by Gale's inherited preset (the crest's white half went **orange**) |
| one mask slot under the artwork | Cloth/Leather/Metal slot boundaries show as **lines** through it |
| outlines at least one DXT1 block (4 texels) wide | DXT1 smears them into the fill; the crest's edges "bled" as the camera turned |
| `TreasureTable.txt` in `Stats/Generated/`, not `Data/` | chest is empty |
| `CanMerge 1` on the treasure table | the chest's vanilla potions disappear |
| pack via `build.ps1`, never `src/` directly | `.lsx` ships unconverted, and there is no item |

A black mask texel does **not** mean "untinted": it renders the surface black. That is
why dye-proofing by masking did not work and dye support was dropped.

## Facts about Gale's robe that shape the art

* **Two texture sets.** The masculine material serves HUM_M, HUM_MS, DWR_M, GNO_M, GTY_M
  and HFL_M; the feminine one serves the female equivalents. Their UV layouts differ.
* **Three submeshes.** `Body` carries everything visible, skirt included. `Bracers` keep
  their vanilla material. `Body_Cloth` is the invisible cloth-simulation proxy: its
  material `9e2966c7` is an engine placeholder that also appears on test chains and
  reference weapons.
* **The front wrap opens on opposite sides.** It is on the viewer's right on the
  masculine mesh and the left on the feminine one, so front skirt decals are placed per
  body type (`"only"` in a decal).
* **The robe is double-sided.** The inner surface repeats the outer one with flipped
  normals and the same UVs, so a sliver of the back print shows inside the front
  opening. In game the character's legs cover most of it.
* **The base colour, normal and physical maps are in a virtual texture** and have not
  been extracted, so items paint a flat ground colour and use flat normal/physical maps.
  The robe reads flat, without fabric detail.

`items/obito_uchiha_robe/README.md` is the full original investigation, including the
debugging log behind the table above.
