# Obito Uchiha Robe — original build log

> **Read this as a record, not instructions.** It was written while the first item was
> being built, before the repo became a multi-item template. Parts are superseded:
>
> * **Dye support was dropped.** Sections 2 and 7 describe a plan that was never shipped;
>   in game a black mask texel rendered the crest *black*, not untinted.
> * The icon, `normalmap` and `physicalmap` are all done now (the "still missing" tables
>   are out of date).
> * Paths have moved: this item lives in `items/obito_uchiha_robe/`, local Larian extracts in
>   `extracted/mesh/`, and the build is `python tools/build_item.py obito_uchiha_robe --art`
>   then `.\build.ps1 -Item obito_uchiha_robe`. See the top-level `README.md`.
>
> The crest measurements, UV placement and the debugging log are still accurate.

A new, standalone item based on Gale's starting robe (`UNI_GaleRobe`), carrying the Uchiha
crest. The robe is fully dyeable; the crest is masked out of the dye system so it keeps its
own colours whatever dye the player applies.

Everything in `reference/GALE_ROBE.md` was read straight out of your Patch 8 `.pak`
files — the UUIDs, paths and measurements there are real, not placeholders.

---

## What the investigation established

**Gale's robe is not a unique asset.** It is the shared `ARM_Robe_A` mesh and texture
set, plus one colour preset (`ARM_Robe_A_Purple_2`) applied by the root template. So:

* You do **not** need to touch meshes or Blender. The new root template inherits all 28
  body-type visuals from Gale's robe automatically.
* The only thing you actually author is artwork.

Two things do need decisions, and both are now settled by evidence.

### 1. The virtual-texture problem

The robe's base colour/normal/physical maps live in a **virtual tile set**
(`CHAR_BASE_VertCut_VT`, `GTexFileName d9da4c1dce75cfb2ddef0729e5572df9`), not in loose
DDS files. You cannot just open and repaint them.

**Take the non-VT route.** `CHAR_BASE_VertCut.lsf` — the non-virtual sibling of the
robe's shader — is already used by 5 materials in the very same human-male armour bank,
so this is a supported in-engine path, not a hack. Clone the robe material, point
`SourceFile` at the non-VT shader, and feed it ordinary DDS textures. This sidesteps
virtual-texture baking completely.

The colour mask is already a plain DDS and needs no such treatment.

### 2. Making the design dye-proof

BG3 dyes work by writing a **material preset** into the `"02 Colour"` parameter group.
The mask texture (`MSKColor`) is an **ID map**: each texel carries a saturated key colour
that selects which colour slot tints it. Measured on the vanilla robe mask:

| Mask colour | Share |
|---|---|
| `#FF8000` | 413,691 endpoints |
| `#0000FF` | 32,293 |
| `#8000FF` | 28,141 |
| `#FF0000` | 22,796 |
| `#00FF80` | 19,292 |
| `#FF8080` | 7,634 |

Six ID colours, six enabled colour slots.

**What does not work:** parking the design on `Custom_1` / `Custom_2` / `Accent_Color`.
Gale's own preset writes *every* slot including those, and dye presets are built the same
way. There is no slot a dye leaves alone.

**What to do instead — leave those texels unassigned in the mask.** Paint the design
region pure black (`#000000`) in `MSKColor`. Black is not one of the ID colours, so it
selects no slot and the texel renders straight from the base colour map, whatever dye is
applied.

> One caveat, stated plainly: **verify this before you commit to it.** The vanilla mask
> has *zero* black texels — 0 of 524,288 block endpoints — so every shipped mask fully
> assigns its surface, and the black-means-untinted behaviour could not be confirmed from
> the shipped data alone. Test it early (step 7) with a black patch and three different
> dyes before you paint the real artwork.
>
> **Fallback if black does tint.** Every `CHAR_BASE_*` armour shader carries an
> `MSKColor` input, so there is no mask-free shader to escape to — but the parameter has
> its own `Enabled` flag (the robe's own `VertexColor_MSK` ships disabled). Give the
> design its own submesh and its own material with `MSKColor` set `Enabled = False`.
> That material then has no tint driver at all and is dye-proof by construction. This
> costs a mesh split in Blender, which is why it is the fallback and not the plan.

---

## Steps

### 1. Tools

| Tool | Status | Why |
|---|---|---|
| **LSLib v1.20.4** | installed at `%USERPROFILE%\Tools\LSLib` | `.lsx` to `.lsf`, `.loca`, packing, virtual textures |
| **BG3 Toolkit** | installed | generating the material and texture resource banks |
| **.NET 8 Desktop runtime** | present | required by LSLib |
| **BG3 Mod Manager** | installed at `C:\games\tools` | enabling the mod |
| **ImageMagick 7.1.2** | installed at `C:\Program Files\ImageMagick-7.1.2-Q16-HDRI` | scripted/batch DDS encoding |
| **GIMP 3.2.6** | installed at `%LOCALAPPDATA%\Programs\GIMP 3` | painting the crest; DDS plug-in bundled |

Every tool is now in place.

Use whichever suits the step: GIMP for drawing and for eyeballing the mask against the UV
layout, ImageMagick for repeatable encoding in `build`-style scripts. GIMP's bundled
`file-dds` plug-in exports DXT1/DXT5 with mipmaps, so either can produce the final files.

One GIMP-specific caution for the **mask**: in the DDS export dialog set compression to
`BC1 / DXT1`, mipmaps to `Generate mipmaps`, and make sure you are not exporting with an
alpha channel the source did not have. When painting mask edges, turn **off** brush
anti-aliasing and use the pencil tool rather than the paintbrush — a soft edge there
becomes a tinted halo around the crest.

### DDS formats — ImageMagick covers everything this mod needs

Surveyed across the vanilla `HUM_ARM_*` texture set:

| Map | Vanilla format | ImageMagick |
|---|---|---|
| `_BM` base colour | DXT1 | writes |
| `_NM` normal | DXT5 | writes |
| `_PM` physical | DXT1 | writes |
| `_MSKcloth` | DXT1 (516 of 525 files) | writes |

Both write paths were tested against the real assets and produce **byte-identical file
sizes to Larian's own** — 2,796,344 for a 2048² DXT1 with 12 mips, 5,592,560 for DXT5.
A full decode/re-encode of the vanilla mask shifted the ID-colour histogram by under
0.01%, entirely at block edges, so the mask survives round-tripping intact.

ImageMagick cannot write BC5 or BC7, but nothing in this mod needs them — the handful of
vanilla BC5/BC7 masks are other armour sets.

**So GIMP is not required for format reasons.** The one thing ImageMagick is not is an
interactive painting program. Two ways round that:

* Draw the crest once, anywhere (Krita, Paint.NET, Inkscape, even an SVG), export a PNG
  with alpha, and composite it at exact pixel coordinates with ImageMagick.
* Or work fully from the command line — the crest is simple geometry.

Either way ImageMagick does the DDS encoding.

LSLib's two entry points:

* `%USERPROFILE%\Tools\LSLib\ConverterApp.exe` — the GUI, including the **Virtual Textures** tab
* `%USERPROFILE%\Tools\LSLib\Tools\Divine.exe` — the CLI that `build.ps1` drives

Verified working actions: `convert-resource`, `convert-loca`, `create-package`,
`extract-package`, `extract-single-file`, `list-package`, `convert-model`, `build-vt`.
Note that `convert-loca` takes **no** `-i`/`-o` flags — it infers direction from the
file extensions.

You do **not** need the Modder's Multitool — `tools/bg3extract.py` already reads the
`.pak` and `.lsf` files directly:

```bash
python tools/bg3extract.py list Textures.pak Robe_A
```

```bash
python tools/bg3extract.py find Shared.pak 92cca1dc-071f-1a40-6eb3-de8e16a38c25
```

### 2. Pull the source textures

The mask is already extracted to `extracted/HUM_M_ARM_Robe_A_MSKcloth.DDS`
(2048 square, DXT1, 12 mips, non-sRGB).

For the base colour you need the virtual tile set unpacked. Open
`%USERPROFILE%\Tools\LSLib\ConverterApp.exe`, go to the **Virtual Textures** tab, point it
at the game's `VirtualTextures*.pak`, and pull `d9da4c1dce75cfb2ddef0729e5572df9`
(`VirtualTextureLayerConfig 3`, so expect three layers out). Drop the results in
`art/source/`.

If you later decide you want to stay on the VT path instead of switching to the non-VT
shader, `Divine.exe -a build-vt` and `Tools\VTexTool.exe <build root> <config xml>` are
what rebuild a tile set. The non-VT route in section 1 is still the simpler option.

### 3. The crest artwork

`art/make_crest.sh` builds the Uchiha crest from scratch, reading its colours from
`art/palette.txt` so there is one place to change them:

```bash
sh items/obito_uchiha_robe/art/make_crest.sh
```

Outputs, both 1024x1280 sRGB with alpha:

| File | Use |
|---|---|
| `art/source/uchiha_crest.png` | the crest itself — composite into `_BM` |
| `art/source/uchiha_crest_maskstamp.png` | pure-black footprint incl. outline — composite into `_MSKcloth` |

The mask stamp is deliberately built from the **dilated** silhouette, so the black region
covers the ink outline as well as the coloured area. If it only covered the red and white,
the outline would sit on a dye slot and shift colour when the robe is dyed.

Two ImageMagick traps the script works around, both of which fail silently:

* **`PNG32:` on every output.** The PNG encoder downgrades any image whose pixels are all
  R=G=B to grayscale. Composite a colour layer onto a base that got downgraded and the
  result is desaturated with no warning — the crest comes out gray.
* **`+antialias` on the mask stamp.** A soft edge blends toward a dye ID colour and
  produces a tinted halo around the crest in game.

Colours and geometry are **measured** from your three reference images, not eyeballed —
see `reference/ARTWORK.md` for the full working. Headlines:

| Role | Value |
|---|---|
| robe purple | `#463E65` |
| crest red | `#E70102` |
| crest white | `#F6F6F6` |
| outline ink | `#251B23` |
| obi white | `#E5E5E5` |
| lining cream | `#B3ACA0` |

The red/white divide is **an arc, not a straight line** — radius `0.884 D` centred
`1.418 D` below the circle top, giving a domed white region. The handle is a narrow
parallel-sided stem, `0.082 D` wide. Both were fitted to the back reference to within 1px.

`reference/crest_vs_reference.png` shows the result beside the source.

### 4. Build the textures

```bash
sh items/obito_uchiha_robe/art/make_textures.sh
```

Composites the crest onto the vanilla masks at the derived UV positions and writes
game-ready DDS into `src/Public/ObitoUchihaRobe/Assets/Textures/Armor/`.

**Two texture sets are required, not one.** The masculine and feminine robes use different
meshes, materials and mask textures, and their back panels unwrap differently — the
masculine panel is rotated 90 degrees in UV space, the feminine one is upright. Dwarves
share the masculine set; halflings share the feminine one.

| | masculine | feminine |
|---|---|---|
| crest centre | (1695, 382) | (316, 411) |
| crest diameter | 160 px | 133 px |
| image rotation | 90 deg clockwise | none |

Placement was derived from the meshes themselves by `tools/crestplace.py`, then verified
by texture-mapping the result back onto HUM_M, DWR_M, HUM_F and HFL_F — see
`reference/UV_PLACEMENT.md` and `reference/crest_on_bodies.png`.

The base colour currently sits on flat robe purple, because the vanilla `_BM` is still
inside the virtual texture. Extract it (step 2), drop it in as
`art/source/base_masculine_BM.png` / `base_feminine_BM.png`, and re-run — nothing else
changes.

### 5. Paint the rest

Work at 2048 square against the robe's existing UV layout. Produce:

* `_BM` base colour — your artwork
* `_NM` normal — reuse vanilla unless you are adding sculpted detail
* `_PM` physical — reuse vanilla unless the design changes material response
* `_MSKcloth` — the vanilla mask with your design area filled pure black

Keep the mask **hard-edged**. Anti-aliased edges blend toward an ID colour and will
produce a halo of tinted pixels around the design.

Encoding commands (`magick` = `C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe`):

```bash
magick crest_mask.png -define dds:compression=dxt1 -define dds:mipmaps=12 out_MSKcloth.DDS
```

```bash
magick crest_bm.png -define dds:compression=dxt1 -define dds:mipmaps=12 out_BM.DDS
```

```bash
magick crest_nm.png -define dds:compression=dxt5 -define dds:mipmaps=12 out_NM.DDS
```

Compositing the crest onto the mask — note `+antialias`, which is what keeps the edges
hard:

```bash
magick base_MSKcloth.DDS crest_alpha.png -geometry +620+780 -composite +antialias -define dds:compression=dxt1 -define dds:mipmaps=12 out_MSKcloth.DDS
```

Avoid any `-colorspace` conversion on the mask — it is ID data, not colour, and the
vanilla resource is flagged `SRGB False`.

### 6. Resource banks — generated, not hand-written

Two scripts build the banks by **cloning the vanilla resources and rewiring them**, which
keeps every parameter Larian tuned instead of guessing at them:

```bash
python tools/make_content_bank.py && python tools/make_visual_bank.py && python tools/make_visuals_node.py
```

* `make_content_bank.py` → `Content/[PAK]_ObitoUchihaRobe/_merged.lsx`
  Four texture resources and two materials (masculine, feminine). Each material is cloned
  from the vanilla robe material, keeping its 7 scalar parameters and all 12 `"02 Colour"`
  dye slots, with the shader switched `CHAR_BASE_VertCut_VT.lsf` → `CHAR_BASE_VertCut.lsf`
  and the textures wired in. The non-VT parameter names (`basecolor`, `normalmap`,
  `physicalmap`, `MSKColor`, `MaterialType 48`) were read off a vanilla material that
  already uses that shader, not guessed.
* `make_visual_bank.py` → `_visuals.lsx`
  Twelve visual resources, cloned from vanilla with the body submesh's `MaterialID`
  swapped to ours. Bracers and Cloth keep their vanilla materials — they use separate
  textures, so swapping them would break them.
* `make_visuals_node.py` → splices the race→visual map into the root template.

**Why cloning rather than an override.** BG3 root templates expose `MaterialOverrides` and
`RealMaterialOverrides`, and the obvious move is to point one at a new material. A scan of
every shipped root template (Shared, Gustav, GustavDev) found **zero** items using either.
Larian's pattern is that an item carries its own visual resources referencing its own
materials, so that is what this reproduces.

**Verified**, not assumed: each clone was converted to `.lsf` and diffed node-by-node
against its vanilla original. All 12 came back identical apart from the three intended
changes (`ID`, `Name`, `MaterialID`).

Two gaps, both deliberate:

* `normalmap` / `physicalmap` are not emitted. The robe's vanilla NM and PM live in the
  virtual texture and have not been extracted, and a parameter left off falls back to the
  shader default — flat, but correct. Add them after step 2.
* **Dragonborn are not covered.** Their robe visuals use their own materials and textures
  rather than the shared human ones, so they keep the vanilla visual and show an
  unmodified robe. Covering them means a third texture set.

### 7. Test the dye behaviour early

Before painting anything real, test whether black really does mean "no dye".

**`art/test/HUM_M_ARM_Robe_A_MSKcloth_dyetest.DDS` is ready to use.** It is the vanilla
mask with a 500x500 pure-black square stamped at (400,600) — inside the large solid-orange
UV island, which is the main robe body, so it will land on visible fabric. Verified:
DXT1, 12 mips, 2,796,344 bytes, 31,501 pure-black blocks and no anti-aliased fringe.

Wire it in as the `MSKColor` texture, build, spawn the robe, and apply three different
dyes at camp.

* Square stays its base colour while the rest recolours → the plan holds, go and paint.
* Square recolours with everything else → switch to the fallback in section 2.

Regenerate it with different coordinates if you want to probe a specific UV region:

```bash
magick extracted/HUM_M_ARM_Robe_A_MSKcloth.DDS +antialias -fill "#000000" -draw "rectangle 400,600 900,1100" -define dds:compression=dxt1 -define dds:mipmaps=12 art/test/HUM_M_ARM_Robe_A_MSKcloth_dyetest.DDS
```

### 8. Icon and localization

`src/Localization/English/ObitoUchihaRobe.xml` already has the name and description
handles wired to the root template. The icon (`Item_UNI_ObitoUchihaRobe`) still needs a
DDS plus an atlas entry under `src/Public/ObitoUchihaRobe/GUI/` — without it the item
shows a blank placeholder.

### 9. Build and test

```powershell
.\build.ps1
```

Converts `.lsx` to `.lsf`, compiles localization, packs to
`%LOCALAPPDATA%\Larian Studios\Baldur's Gate 3\Mods\ObitoUchihaRobe.pak`.

Enable in BG3 Mod Manager, then spawn `UNI_ObitoUchihaRobe` with **SpawnAnyItem**
(already installed). Check at least one slim and one strong body type — the robe has 14
body-type variants and UVs differ.

---

## Layout

```
src/
  Mods/ObitoUchihaRobe/meta.lsx                    mod UUID d2f4984b-...
  Public/ObitoUchihaRobe/
    Stats/Generated/Data/Armor.txt                UNI_ObitoUchihaRobe, using UNI_GaleRobe
    RootTemplates/_merged.lsx                     item db53c125-..., parented to Gale's robe
    Content/[PAK]_ObitoUchihaRobe/                 Toolkit output goes here
    Assets/Textures/Armor/                        your DDS files
  Localization/English/ObitoUchihaRobe.xml
tools/       bg3extract.py + lspk.py / lsf.py  (pak and lsf readers)
reference/   GALE_ROBE.md  — the full traced asset chain
extracted/   vanilla mask DDS
art/source/  working files
```

### Reserved UUIDs

| Purpose | UUID |
|---|---|
| Mod | `d2f4984b-c5c7-4cd3-97a0-63bff6b561b7` |
| Item root template | `db53c125-9430-415a-aa2e-4899db9d4c24` |
| Colour preset | `cd56b336-e7de-4c94-afba-40776b39e153` |
| Material — body | `8b0f3491-d048-4989-82ef-afde63bdac5e` |
| Material — cloth | `36bbd37f-70d5-4ba6-ae67-41f99108bec3` |
| Material — bracers | `9d349444-629e-4b20-8fe0-c98950613576` |
| Texture — BM | `cf9179e0-a4e7-42ea-9c17-aa494d87bb5d` |
| Texture — NM | `005657b1-e9ae-40ce-ae86-afcc8b972030` |
| Texture — PM | `9effe3e4-73cd-49c4-8ec0-a9fff850077a` |
| Texture — MSK | `546f4b98-8505-4881-b7ce-dd66e32230c2` |

Use these rather than letting the Toolkit mint its own, or update the `.lsx` files to match.

---

## Can this be tested in game yet?

**Yes — the mod now builds complete.** `build.ps1` produces a 10-file pak wiring textures
→ materials → visuals → item.

```powershell
.\build.ps1 -Item obito_uchiha_robe -Install
```

Then enable *Obito Uchiha Robe* in BG3 Mod Manager. Two ways to get the robe:

* **Tutorial chest** on the nautiloid — the mod extends the chest's treasure table, so the
  robe is simply in it on a new run. You also have TutorialChestSummoning installed, which
  can summon that chest anywhere.
* **SpawnAnyItem**, spawning `UNI_ObitoUchihaRobe`, on an existing save.

Which chest, traced rather than assumed: the nautiloid chest is the level instance
`S_Chest_Potions` (template `CONT_MF_Chest_A`) in `TUT_Avernus_C`. Its contents come from
neither the root template nor a story script -- the instance carries
`InventoryList > InventoryItem > "TUT_Chest_Potions"`, so that is the table the mod
extends, with `CanMerge 1` so the vanilla healing potions survive.

What you should see: the robe in Obito purple with the Uchiha crest on the back, on any
body type except Dragonborn.

What is still missing:

| Gap | Effect |
|---|---|
| vanilla `_BM` still inside the virtual texture | base colour is flat purple, no fabric detail |
| `normalmap` / `physicalmap` not wired | lighting reads flat |
| no icon atlas under `GUI/` | blank inventory icon |
| Dragonborn not covered | shows the unmodified vanilla robe |

Separately, `build-masktest.ps1` builds a **replacer** that blacks out the crest area in
the vanilla robe masks. It settles whether black really is excluded from every dye slot.
Supporting evidence so far: 13 of 1049 vanilla masks use substantial near-black regions,
and on `HUM_M_CLT_Cape_Long_C` 19% of the mesh's own triangles land on near-black mask —
so black is used on real, visible geometry, not just unused UV gutter. That is strong but
not conclusive; the in-game check is one dye away.

### Packing note

Pack with `build.ps1`, never by calling `create-package` on `src/` directly. The game
reads `RootTemplates/_merged.**lsf**`; the repo holds `.lsx` and `build.ps1` stages and
converts first. A pak containing the `.lsx` loads without error and silently has no item
in it.

One PowerShell trap that bit here: the Content folder is named `[PAK]_ObitoUchihaRobe`,
and PowerShell reads `[...]` in a path as a wildcard character class. `Remove-Item
$_.FullName` therefore never matched the file, and the `.lsx` sources shipped inside the
pak. `-LiteralPath` fixes it.

---

## Debugging log — two silent failures

Both produced no error anywhere: no log line, no missing-asset warning, no crash. Recorded
because each cost real time and neither is guessable from the symptom.

### Symptom: item equips, character is naked

**Cause: guid byte order.** BG3 stores UUIDs with the last 8 bytes 16-bit-word-swapped
relative to the .NET layout. LSLib handles this and advertises it as `bswap_guids` in the
`lslib_meta` of every `.lsx` it writes. `tools/lsf.py` did not.

So every race `MapKey` in the item's `Visuals` map went vanilla bytes -> our parser ->
`.lsx` -> LSLib -> **different bytes**. The engine matched no race, found no visual, and
rendered nothing.

```
wrote  7d73f501-f65e-46af-3ba1-ac2c98f3055d
read   7d73f501-f65e-46af-a13b-2cacf3985d05    <- not a round-trip
```

Fixed in `guid()`. Note this is invisible to a structural diff of the visual resources:
those contain no UUID-typed attributes at all (every ID is a `FixedString`), so the
corruption lived entirely in the root template. "12/12 visuals faithful" was true and the
mod was still broken.

A second contributing risk, fixed at the same time: the VisualBank was in its own
`_visuals.lsf`. Vanilla ships every bank as regions inside ONE `_merged.lsf` per content
folder, and a separate file may simply never be loaded. Now merged.

### Symptom: robe renders, but pure black

**Cause: an unbound shader input.** The material wired only `basecolor` and `MSKColor`,
leaving `normalmap` unbound. An unbound texture samples as `(0, 0, 0)` -- a zero-length
normal -- so lighting evaluates to nothing and the surface is black no matter how correct
the base colour is.

Ruled out first, all of which were fine: the BM content (genuinely `#463E65`), the texture
resource attributes (identical to a vanilla `_BM` resource field for field), and
`MaterialType 48` (uniform across all five vanilla materials on that shader).

Fixed by wiring all four inputs with neutral stand-ins for the two still stuck in the
virtual texture (`art/make_neutral_maps.sh`). **Wire every texture input a shader expects,
even with a flat placeholder.** Leaving one off does not degrade gracefully.

### Symptom: robe renders as an ordinary purple Gale robe, artwork missing

**Cause: the content bank was in a folder the engine never scans.** Custom banks must live
under `Content/Assets/<Category>/[PAK]_<name>/`:

| | Path |
|---|---|
| vanilla | `Content/Assets/Characters/Humans/[PAK]_Male_Armor/` |
| a working mod (MadaraGunbai) | `Content/Assets/Weapons/[PAK]_MadaraGunbai/` |
| **broken** | `Content/[PAK]_ObitoUchihaRobe/` |

Dropping the `Assets/<Category>/` segment means the TextureBank, MaterialBank and
VisualBank never load. The root template's visual UUIDs then resolve to nothing and the
item silently falls back to its `ParentTemplateId` -- so an item parented to Gale's robe
renders as Gale's robe, purple and crest-free.

The misleading part: `#463E65` purple looks exactly like a correct base colour. Ruling it
out needed checking the material's own colour slots, which are tan/teal/white/brown/silver
-- none of them purple. The purple could not have come from this material, so it was not
this material rendering.

Also ruled out along the way, none of them the cause:

* the BM in the installed pak (crest present, correctly placed and rotated)
* the V-flip -- proven rather than assumed by exporting the mesh to glTF, whose V is
  image-space, and confirming `gltf_v == 1 - dae_v` across 3006 matched vertices
* occlusion -- all three submeshes rendered with depth; the Cloth submesh sits well below
  the crest

**When a modded item looks exactly like its parent template, suspect the content bank is
not loading, before suspecting the artwork.**
