# Obito scars: head-texture pipeline

Edits the vanilla human-male head maps so a character has Obito's right-side scars.
**Approved by the user (2026-09-19): the "ear" version** (`--design v1ear`, the default): v1's 14 lines with the
outer rings turned into arms and the cheek, jaw and forehead lines carried out to the ear, grooves at depth 4 /
blur 1.5 (the composite defaults). Installed as `ObitoScarsScars.pak`; the running default commands below rebuild it
byte for byte. Older versions are kept as `ObitoScarsScars_v1.pak` (14 lines, stopped short of the ear) and
`_v2.pak`; `--design v2` / `v3` recreate the other layouts (v3 was traced from a close-up reference, not chosen).
It is still a replacement of Head A's normal map for everyone, and it needs BeastFolk disabled (see "What went
wrong first"). See "Not done".

Player-selectable heads are `A`–`I`. (`Oscar` is an NPC head and never appears in character
creation; the scripts accept it only for comparison.) Head A and Oscar share one UV unwrap
(nose tip on the same texel); the other heads have not been checked.

## Run

```bash
python items/obito_scars/art/fetch_vanilla.py A         # vanilla maps + mesh -> extracted/head_hum_m_a/
python items/obito_scars/art/draw_scar_layer.py         # -> out/head_a/scar_height.png + preview
python items/obito_scars/art/composite_head.py          # -> out/head_a/build_scars/dds/
```

`scar_height.png` is a plain 2048² grayscale image: white = groove, black = skin. Edit it in any
image editor and re-run the last command; the compositor doesn't care how it was drawn. The
head's UV sheet centreline is x = 1024.

## What the maps are (measured on the vanilla files)

| Map | DDS | Notes |
|---|---|---|
| `NM` | DXT5, 2048², 12 mips | `R` always 0, `B` ≈ 255. Normal in `A` (x) and `G` (y), neutral 128. There is no blue/purple RGB normal. |
| `CLEA` | DXT5 | `R` near white, darker in creases; `G` eyebrow-only mask; `A` broad face mask. Roles not identified. |
| `HMVY` | DXT5 | Four data channels, no colour; skin colour is computed. Likely hemoglobin / melanin / vein (from `ScarHemo/Melanin/VeinMultiplier`); 4th unknown. |

There is **no albedo** on the head. Re-encoding a vanilla map with the repo's ImageMagick
settings (`dds:compression=dxt5`, `dds:mipmaps=12`) reproduces the vanilla header and file
size exactly; the compositor checks this on every file it writes.

## Not established from the files (the marker test settles these)

1. ~~Which half of the sheet is the character's right.~~ **Settled by the marker test.** Marks drawn
   with `--half right` (u > 0.5) appeared on the character's LEFT, so the game is mirrored relative to
   the converted mesh. The character's right is `--half left` (u < 0.5), now the default.
2. **Whether a deeper `NM` deviation reads as a groove or a ridge** (`--invert`).
3. **Whether `A` is x and `G` is y** (`--swap`). A curl test on the vanilla map favours it
   (0.71 vs 0.37), which is not conclusive.
4. **What `CLEA` and `HMVY` channels control.** Probe with `--adjust`.

## Marker test

```bash
python items/obito_scars/art/draw_scar_layer.py --marker
python items/obito_scars/art/composite_head.py --tag marker \
    --layer items/obito_scars/art/out/head_a/marker_height.png --adjust HMVY.G=-90
```

The marker is four shapes on ONE half only: a horizontal bar on the forehead, a vertical bar
at the temple, a diagonal bar on the cheek, and a ring under the eye. `HMVY.G` is also pushed
down inside them. Put it on a head-A character, look at it face-on, in bright light:

| You see | Do |
|---|---|
| Marks (built with `--half right`) on the viewer's left | not mirrored: use `--half right` for the scars |
| Marks (built with `--half right`) on the viewer's right | **this is what happened.** The sheet is mirrored vs the mesh, so use `--half left` (now the default) to put marks on the character's right |
| Marks look like cuts | keep as is |
| Marks look raised | add `--invert` to `composite_head.py` |
| Horizontal bar smeared or missing while the vertical one is a clean crease (or the reverse) | add `--swap` |
| A pale or dark patch in the same places | `HMVY.G` reaches the skin. Note whether it is paler, darker or redder |
| No marks at all | the texture isn't loading; that is a wiring problem, not a paint problem |

Change **one** thing per build.

## Test mod

```bash
python items/obito_scars/build_test_mod.py             # -> ObitoScarsMarker.pak in the repo root
python items/obito_scars/build_test_mod.py --install   # also copies it to the BG3 Mods folder
```

**v1 (`--mode path`) did not show anything in game.** It only put the DDS files at the vanilla
texture path. Of the 230 paks in the Mods folder, only one overrides a vanilla-path DDS, and it also
ships its own bank, so that is not how installed mods do it. Not confirmed as the cause, but it was
the least-supported assumption.

**v2 (`--mode redefine`, default)** ships a TextureBank that redefines Head A's `NM` and `HMVY`
resources with the **same IDs as vanilla** (`73072022…`, `bb7bcb6b…`) pointing at DDS files under
`Public/ObitoScarsMarker/Assets/Textures/`. The head material keeps referencing those IDs. The script
converts the bank to `.lsf`, reads the pak back, and checks the IDs, paths and file contents.
If another installed mod redefines the same IDs, load order decides.

In game: enable the pak in BG3 Mod Manager, **Export Order to Game**, start a new character,
**Human**, Body Type 2, and pick the Head A face by its portrait (the interface shows no "Head 1"
names; the first regular-build Human male icon from the game's icon atlas is Head A). Look face-on in
bright light. Only ONE of the marker/scars paks may be enabled at a time: they redefine the same
resource IDs.

**What went wrong first, for next time:** the marker showed nothing because the enabled mod
**BeastFolk** redefines all 35 vanilla Human face entries (same UUIDs, `RaceUUID` changed to its own
race), so Humans were never offered Head A. Disabling BeastFolk fixed it. Disabling the other head mods
instead emptied the Human Face row, because they were the only Human faces left. The shipped mod must
add faces under NEW UUIDs so it works with BeastFolk on.

## Standalone face (`../build_face_mod.py` -> `ObitoScarsFace.pak`)

```bash
python items/obito_scars/build_face_mod.py --install     # after art/composite_head.py has built the normal map
```

A separate, selectable Human face (Body Type 0 = the regular male) that adds itself next to the vanilla ones. It
clones Head A's visual and the three skin materials that use the normal map, all under NEW ids, and points them
at the scarred normal map. Nothing vanilla is redefined (the script checks), so Head A stays unscarred for
everyone else, and it works with BeastFolk enabled. It also ships a name ("Obito Scars") and a thumbnail: Head
A's own portrait with the scar layout drawn on it, so it is recognisable in the Face list.

**Status: built and self-checked, not yet seen in game.** To test: enable `Obito Scars (Face)`, DISABLE
`Obito Scars: Scars (Head A)` (the old replace-Head-A mod) and the marker, export, start a Human on Body Type 2,
find the tile with the scarred thumbnail. The vanilla Head A tile (if BeastFolk is off) must look normal. Then
re-enable BeastFolk and check the tile is still there.

## Dhaen "HUM B" face (`../build_face_mod.py --head CHD_B` -> `ObitoScarsFaceDhaenHumB.pak`)

"HUM B" in Dhaen Extended is the game's own **human child head B** (`HUM_CHD_NKD_Head_B`, visual
`5f44ba45-820a-4f10-5078-e15860c36fee`): Dhaen builds on child-sized bodies and reuses the vanilla child heads. There is
no vanilla portrait for it and Dhaen ships none, so the thumbnail is rendered from the mesh.

```bash
python items/obito_scars/art/fetch_vanilla.py CHD_B
python items/obito_scars/art/draw_scar_layer.py --head CHD_B      # design scaled to the child head (x0.942 across, x0.760 up/down)
python items/obito_scars/art/composite_head.py --head CHD_B
python items/obito_scars/build_face_mod.py --head CHD_B --install
```

Same recipe as the Head A face: cloned visual + skin materials + new normal map, all under new ids. It adds a scarred
tile to every Dhaen face list that shows "HUM B": 26 entries across 7 races, both body types (icon keys `0_` and `1_`).
Dhaen also has "HUM B" entries for two more races (26ae3917, 7b1aacbf) that use OTHER head visuals; those are not
covered. Requires Dhaen Extended. Verified: same UV layout and left/right mirroring as Head A (nose texel, mesh -x side
= sheet-left). **Not yet seen in game.**

### The dense layout, as a separate mod (`--variant dense` -> `ObitoScarsFaceDhaenHumBDense.pak`)

User asked (12:30) for the forehead lines to reach the nose and the whole right half scarred like the reference pictures.

```bash
python items/obito_scars/art/draw_scar_layer.py --head CHD_B --design full        # 20 lines (default design is unchanged)
cp .../out/head_chd_b/scar_height.png .../out/head_chd_b/scar_height_dense.png
python items/obito_scars/art/composite_head.py --head CHD_B --layer .../scar_height_dense.png --tag dense
python items/obito_scars/build_face_mod.py --head CHD_B --variant dense --install
```

A second, independent mod so both can sit in the Mod Manager: its own folder (`ObitoScarsFaceDhaenHumBDense`), mod UUID,
resource ids and names (`ObitoScars_Dense_...`), entry UUIDs, name-text handle and tile name ("Obito Scars (dense)"). The script
checks the two share no resource id, name, entry UUID or handle. Enable ONE at a time (both add a tile to the same face lists).
The approved layout is `ObitoScarsFaceDhaenHumB.pak` (+ `_v1.pak` backup).

### The combined layout (`--variant combo` -> `ObitoScarsFaceDhaenHumBCombo.pak`)

User (12:40), comparing the dense mod in game: likes the new forehead lines but the approved layout "had more scars, which is more
accurate". `--design combo` (`design_combo()`): ALL 14 approved lines untouched + the new forehead lines FA/FB/FE (replacing the old three
forehead strokes) + any reference stroke that fits without touching a kept line (none did: iv, i1-i3, l1-l3, chin, S all clash with the
approved rings/arcs). 17 lines. Third independent mod (own folder/UUID/ids/names `ObitoScars_Combo_*`/tile "Obito Scars (combined)"); the
script checks all three Dhaen mods share no resource id, name, entry UUID or handle. Enable ONE at a time.

```bash
python items/obito_scars/art/draw_scar_layer.py --head CHD_B --design combo
cp .../out/head_chd_b/scar_height.png .../out/head_chd_b/scar_height_combo.png
python items/obito_scars/art/composite_head.py --head CHD_B --layer .../scar_height_combo.png --tag combo
python items/obito_scars/build_face_mod.py --head CHD_B --variant combo --install
```

NOTE: `draw_scar_layer.py` overwrites out/head_<x>/scar_height.png on every run; the per-layout copies (`_v1`, `_dense`, `_combo`) are the
ones the builds use.

### More visible on light skin (`--variant vis` -> `ObitoScarsFaceDhaenHumBVis.pak`)

User (12:55): likes the combined look, but the scars are less visible on lighter skin tones. Shading alone is softened by the game's
subsurface scattering on pale skin. MEASURED on the vanilla maps (child head B and Head A): **CLEA.R is the crease map** (corr +0.47 / +0.41
with pit-like features; ~-48 / -34 at the game's deepest creases, face mean ~240); HMVY channels show no consistent crease response.
So the fix darkens CLEA.R inside the scars like the game's own creases: same combined layout + `composite_head.py --adjust CLEA.R=-100`
(tag `vis`). `build_face_mod.py` now ships CLEA (and HMVY) too when the art build contains them: it clones those TextureBank entries under
new ids and repoints the cloned materials (base/LOD1/LOD2). Existing mods rebuild file-identical. Variant `vis`: folder
`ObitoScarsFaceDhaenHumBVis`, tile "Obito Scars (visible)", names `ObitoScars_Vis_*`. Strength (-100) is a first guess (game creases ~-48 at 2 sigma;
scars are much deeper); raise/lower `--adjust CLEA.R=` if too weak/strong. Untested in game.

## Not done

* ~~The shipped version: a separate selectable face with its own NEW-UUID Human entry.~~ Built, see above;
  untested in game. It needed a cloned visual, material and character-creation entry; `tools/make_visual_bank.py` and `make_content_bank.py`
  already do this for garments.
* Depth and softness (`--depth 4`, `--blur 1.5`) are guesses.
* `CLEA`/`HMVY` changes for the real scars: the default build touches `NM` only.
* Heads other than A.
