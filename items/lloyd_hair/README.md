# Lloyd de Saloum hair

A selectable hairstyle for Human, Elf, Half-Elf, Drow and Tiefling (both body types and shapes):
short, heavily layered hair; a heavy centre bang and shorter side bangs; side locks framing the face;
wild spikes flaring back over the ears; one ahoge on the crown; a low ponytail tied with a ribbon.

## Status

| Step | State |
|---|---|
| Registration (new hair slot, fresh UUIDs, meta, loca) | **works in game**: the control pak was installed 2026-09-20 and "Lloyd" appeared in the hair list (tile icon is a "?" placeholder; no icon atlas shipped yet) |
| The Lloyd mesh, v1 | **built** (`art/make_lloyd.py`, route A, rigid): vanilla `Short_M` cards reshaped, see "How v1 was made". Read back from the shipped GR2 and rendered against the Head A mesh |
| Blender -> GR2 chain | **proven**: audit, export, retarget, Divine to GR2, pack, check, and the GR2 read back out of the pak |
| Lloyd mesh in game | **not tested.** The installed pak is still the control; v1 is built in the repo root but NOT installed |

Sequence used: control first (proved registration), then the mesh. If v1 does not show up or looks wrong in game, the
control already rules registration out.

## How v1 was made (`art/make_lloyd.py`)

Not hand-sculpted. Vanilla `HAIR_HUM_M_Straight_Short_M` is 684 separate strand ribbons on one material, one UV set,
all weighted to `Head_M` (7-bone skeleton: the simplest rig of any vanilla hair). The script lays whole cards along new
centrelines, so every card keeps its UVs, weights and material. The bangs and side locks are ray-cast against the Head A
mesh so they follow the skin.

| Part | Built from | Notes |
|---|---|---|
| Ahoge | the 2 tallest cards (+1 copy) | 3 ribbons rising from the crown, curling forward |
| Ponytail | 71 low-back cards + copies (150 strands) | bundle tied at y=1.76 (nape), hangs about 22 cm, flips out at the tip. **Rigid**, no swing |
| Bangs | 55 front cards | hug the forehead; centre strand to eye level (z 1.812), the ones either side stop at 1.872 |
| Side locks | 44 temple cards (22 per side) | in front of the ear, to z 1.66 (mid-neck) |
| Spikes | 117 cards over the ears | tips splay outward and backward |
| Everything else | 375 cards, untouched | vanilla layered cap |

Re-run with different numbers: parameters are at the top of `make_lloyd.py`.
Renders go to `build/lloyd_renders/`. Rebuild: `make_lloyd.py` -> `hair_blender.py` -> `hair_mod.py gr2 ... --lod-from-lod0`
-> `build` -> `pack` -> `check`. LOD1 is a copy of LOD0 (about 31,700 triangles at every distance).

## Corrections to the brief (things the game does differently)

* **There is no `CharacterCreationHairStyles.lsx`.** A hair is a row with `SlotName "Hair"` in
  `CharacterCreationAppearanceVisuals.lsx`, pointing at a *visual* in a VisualBank (`_merged.lsf`) that names the GR2.
  Checked against vanilla (`Shared.pak`) and against `Elgoth's hair.pak`, a working single-hair mod.
* **Hair is not skinned to `Head_M`.** Vanilla hair meshes are weighted to about 34 rigid `Socket_Hair_*` bones
  (Crown, CrownTop, Top1/2, Forehead, Temple, Ear, Sideburn, LowerEar, Back, Neck1...). Measured on
  `Short_H_Spring`: 100% of its weight is on sockets. That is the "rigid, no physics" behaviour you want for the crown.
* **Physics is one chain, and it is not authorable.** A spring hair has a skeleton entry in the SkeletonBank
  and a `SpringResourceID` pointing at a binary `.bin` (magic `SEBD`) with the stiffness/constraints. LSLib has
  no tool for that format. The vanilla `Long_G_Spring` bin defines exactly one chain:
  `Socket_Hair_Crown_M -> Hair_Ponytail_00_M -> 01 -> 02 -> 03`. So: **a ponytail can swing, using vanilla's tuning; side
  locks cannot** (no vanilla hair has a side-lock chain in the same skeleton). Side locks stay rigid.
* **No hair collider exists to configure.** `ClothColliderResourceID` and `SoftbodyResourceID` are empty on every
  vanilla hair I checked. Torso/armour clipping is managed by keeping the tail short, not by a collision setting.
* **Blender's glTF cannot go straight to Divine.** LSLib crashes on Blender's armature (`ImportBone`, null
  reference; reproduced here). `tools/hair_retarget.py` rebuilds the file around the vanilla skeleton.
* **Colour channels are not UV-authored.** Primary/secondary/graying come from the vanilla hair material and the colour
  the player picks; the visual just refers to the vanilla material, scalp material and hair preset by id.

## Which base mesh

Rendered and measured, not guessed (`tools/hair_render.py`):

| Vanilla hair | Use it for | Weighting |
|---|---|---|
| `HAIR_HUM_M_Straight_Short_H_Spring` | **crown, bangs, side locks, flared spikes**: layered short cap with long face-framing locks and a ponytail curl | 100% sockets (rigid) |
| `HAIR_HUM_M_Straight_Long_G_Spring` | **the ponytail and the skeleton** if you want it to swing | sockets + `Hair_Ponytail_00..02_M` |
| `Short_F`, `Short_E`, `Short_J`, `Tav's Emo/Rat/Githkid` | not suitable: bob/fringe shapes, no tail | - |

Only two of the 34 bones `Short_H` uses are missing from `Long_G`'s skeleton: `Socket_Hair_Neck_L/R`. Fold them into
`Socket_Hair_Neck1_M` when you merge the two.

Third-party packs (Tav's Hairpack etc.) are not used: their meshes are rearranged Larian meshes, and shipping
someone else's file is not yours to redistribute. Build from the vanilla ones.

**Two build routes** (set `"base"` in `hair.json`):

* **A, rigid (recommended first): base `Short_H_Spring`.** Everything on sockets, ponytail included, tied at the nape
  using `Socket_Hair_Neck1_M`/`Neck2_M`. Zero physics risk. This is what you can be sure will work.
* **B, swinging ponytail: base `Long_G_Spring`.** The visual keeps vanilla's `SkeletonResource`, so the vanilla
  spring is used with no extra files.

### Where a swinging ponytail can start (measured from the vanilla bind pose)

glTF space, metres; the character faces **-Z**, so the back is **+Z**.

| Bone / socket | y | z |
|---|---|---|
| `Socket_Hair_Forehead_M` (bang root) | 1.877 | -0.120 |
| `Socket_Hair_Top_M` | 1.933 | -0.025 |
| `Socket_Hair_CrownTop_M` (ahoge root) | 1.921 | +0.030 |
| `Socket_Hair_Crown_M` (chain root) | 1.895 | +0.060 |
| `Socket_Hair_Back_M` | 1.841 | +0.081 |
| `Socket_Hair_Neck1_M` (nape) | 1.775 | +0.059 |
| `Socket_Hair_Neck2_M` | 1.740 | +0.047 |
| `Hair_Ponytail_00_M` | 1.882 | +0.103 |
| `Hair_Ponytail_01_M` | 1.785 | +0.120 |
| `Hair_Ponytail_02_M` | 1.687 | +0.121 |
| `Hair_Ponytail_03_M` | 1.596 | +0.156 |

The vanilla chain starts at crown height, about 10 cm above a nape tie, so **a true nape-rooted swinging ponytail
would need a moved skeleton and a new spring `.bin`, which cannot be authored here.** The workable compromise for
route B: sculpt the tie at the nape (y about 1.78) and weight the tail to `Hair_Ponytail_01..03_M` only, since `01`
already sits at nape height. The tail then pivots as if hung from the crown, a slightly long arm, which reads as a
looser swing. **That is a hypothesis, not something I have seen in game.** If it looks wrong, fall back to route A.

## Layers (per your specification)

| Layer | Geometry | Bones | Behaviour |
|---|---|---|---|
| Base / cap | vanilla scalp cap, kept | Crown/Back/Top sockets | rigid |
| Crown spikes | layered pointed cards, radial from the crown; sides flare back over the ears | `Socket_Hair_Crown_*`, `CrownTop_*`, `Top1/2_*`, `Back_*`, `Ear_*` | rigid (100% sockets), so the silhouette stays sharp |
| Bangs | one heavy centre bang (M-notch or pointed, see the wig photo), two shorter side bangs | `Socket_Hair_Forehead_M/L/R`, `Temple_L/R` | rigid |
| Side locks | two flat strands from the temples, in front of the ear, past the jaw to mid-neck | `Temple`, `Sideburn`, `Ear`, `LowerEar` (L/R) | rigid, weights fade toward `LowerEar`; **no sway** (see above) |
| Ahoge | 2-3 thin strips curling up and forward from the crown, about a third of head height | `Socket_Hair_CrownTop_M` / `Top_M` | rigid |
| Ponytail | tail bundle from the nape tie, hanging straight, tip flipped out | route A: `Neck1_M`/`Neck2_M`; route B: `Hair_Ponytail_01..03_M` | route A rigid; route B swings |
| Tie / bow | the `Accessories` mesh | as its vanilla weights | uses a different vanilla material (`656fe152...`) than the hair (`8be8da2c...`); what it looks like is unverified. A mint bow cannot come from the hair material, which tints with the player's colour |

Ponytail weights (route B): tie vertices 1.0 on `01`; ramp to `02` over the first third; `02`->`03` over the last
third; nothing on `Chest_M`/`Spine`. Keep the tip above about y = 1.55 to stay clear of the shoulders.

## Blender workflow

Blender 5.2 here. **The character faces +Y in Blender** (glTF -Z becomes Blender +Y), so numpad-1 (front view)
shows the *back* of the head. Use Ctrl+numpad-1 for the face side.

1. Unpack the bases to glTF:
   ```bash
   python tools/hair_mod.py unpack items/lloyd_hair HAIR_HUM_M_Straight_Long_G_Spring
   ```
   -> `extracted/hair_base/HAIR_HUM_M_Straight_Short_H_Spring.glb` (+ Long_G, its skeleton and spring `.bin`).
2. New file. File > Import > glTF 2.0 the base. Ignore the extra `Icosphere`: it is Blender's bone display shape;
   the audit and the export skip it.
3. Import the other base too if you are combining. Rename every vanilla mesh you keep as a reference to `REF_...`
   (the audit ignores `REF_*`). Hide them, or use them as sculpt targets.
4. Keep exactly one armature. **Do not rename the meshes you will ship**: the VisualBank finds them by name
   (`<gr2>.<mesh>.<index>`). Ship `..._Spring_Mesh` and `..._Accessories_Mesh`; delete the `_LOD1` objects
   (step 8 rebuilds them from LOD0).
5. Sculpt/edit the LOD0 mesh: pull the cards with proportional editing (O), or model new cards for the spikes,
   bangs and ahoge. Anchor points are in the table above. Cards, not solid hair: vanilla is 20-35k triangles.
6. Weights: select your mesh, then the `REF_` mesh (active). Object > Link/Transfer Data > Transfer Mesh Data >
   Vertex Groups, mapping *Nearest Face Interpolated*, layers *By Name*. Then hand-paint the ponytail, ahoge and
   side locks per the layer table, and Weights > Normalize All.
7. Normals: for a clean cell-shaded look on the spikes, add a Data Transfer modifier, Face Corner Data > Custom
   Normals, from a smooth head-shaped sphere, and apply. Export writes normals and tangents.
8. Apply transforms (Ctrl+A > All Transforms), then audit and export:
   ```bash
   "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b -P tools/hair_blender.py -- \
       --in work/lloyd.blend --out work/lloyd_export.glb --fix
   python tools/hair_mod.py gr2 items/lloyd_hair work/lloyd_export.glb --lod-from-lod0
   ```
   The audit refuses unweighted vertices, more than 4 influences, groups that are not bones, missing UVs and
   un-applied transforms; `--fix` repairs the first two. `gr2` retargets onto the vanilla skeleton and asks Divine
   for `art/out/LloydHair.GR2`.
9. Set `"mesh": {"gr2": "art/out/LloydHair.GR2"}` in `hair.json`, then build/pack/check/install (below).

Render any of it to look at silhouettes: `blender -b -P tools/hair_render.py -- --out build/hair_renders x.glb`.

## Pipeline

```bash
python tools/hair_mod.py init    items/lloyd_hair      # done: fresh UUIDs are in hair.json (never change them once played)
python tools/hair_mod.py unpack  items/lloyd_hair      # vanilla base -> glb (Models.pak, via Divine)
python tools/hair_mod.py gr2     items/lloyd_hair work/lloyd_export.glb --lod-from-lod0
python tools/hair_mod.py build   items/lloyd_hair      # meta, character-creation rows, VisualBank, loca -> src/
python tools/hair_mod.py pack    items/lloyd_hair      # .lsx -> .lsf, .xml -> .loca, create-package -c lz4 -> LloydHair.pak
python tools/hair_mod.py check   items/lloyd_hair      # read the pak back: files, visual id in the LSF, rows, mesh path
python tools/hair_mod.py install items/lloyd_hair      # copy to Mods; refuses to overwrite one already installed
```

Divine calls used: `convert-model` (GR2 <-> glTF), `convert-resource -i lsx -o lsf`, `convert-loca`,
`create-package -c lz4`. Divine needs **absolute paths**. Close BG3 before `install`: a running game locks the pak.
Enable the mod in BG3 Mod Manager.

## Configuration

`hair.json` (ids generated once):

| Field | Meaning |
|---|---|
| `folder` | mod folder and pak name (`LloydHair`) |
| `base` | vanilla hair to clone: route A or B |
| `mesh` | `null` = control (vanilla GR2); `{"gr2": ...}` = ship yours |
| `races` | race UUIDs; these five are the vanilla races with the human-shaped head |
| `body_types`, `body_shapes` | 0/1 each; rows are races x types x shapes = 20 |
| `ids.mod` | `199bf092-4a67-4f99-9745-98e814911117` |
| `ids.visual` | `d77036ea-d5fb-4c5b-8c0d-1f0a3498e687` |
| `ids.name_handle` | `hbb8b7117g64c7g4192gaa76gad922b640a09` (tile text in the loca) |
| `ids.rows` | one UUID per character-creation row |

Generated tree (`src/`, packed by `pack`):

```
Mods/LloydHair/meta.lsx
Public/LloydHair/CharacterCreation/CharacterCreationAppearanceVisuals.lsx   (stays XML)
Public/LloydHair/Content/Assets/Characters/[PAK]_Hair/_merged.lsx           (-> .lsf)
Localization/English/LloydHair.xml                                          (-> .loca)
Generated/Public/LloydHair/[PAK]_Hair/LloydHair.GR2                         (only when "mesh" is set)
```

A character-creation row (one of 20):

```xml
<node id="CharacterCreationAppearanceVisual">
    <attribute id="BodyShape" type="uint8" value="0" />
    <attribute id="BodyType" type="uint8" value="0" />
    <attribute id="DisplayName" type="TranslatedString" handle="hbb8b7117g64c7g4192gaa76gad922b640a09" version="1" />
    <attribute id="RaceUUID" type="guid" value="0eb594cb-8820-4be6-a58d-8be7a1a98fba" />
    <attribute id="SlotName" type="FixedString" value="Hair" />
    <attribute id="UUID" type="guid" value="(unique per row)" />
    <attribute id="VisualResource" type="guid" value="d77036ea-d5fb-4c5b-8c0d-1f0a3498e687" />
</node>
```

Nothing vanilla is overwritten: every id is new and nothing shares a path with Larian's files.

## Not verified / open

* Nothing has been loaded in game. Start with the control pak.
* **Feminine body type and strong body shape** reuse the same mesh. Vanilla ships separate `HUM_F`/`HUM_MS` fits; expect
  some clipping, and split the visuals per body type if it shows.
* Dhaen Extended and other modded races are not registered; add their race UUIDs to `races` in `hair.json`.
* The route-B swing, the accessory mesh's appearance and the two UV sets are unverified. Keep the vanilla UV sets
  (the weight transfer does not touch UVs) rather than repainting them.
* The bow is not mint: hair takes the player's colour.
* Larian's `Short_H`/`Long_G` are the base; a shipped mesh derived from them stays out of git (see `.gitignore`).
