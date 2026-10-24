# Hair 01 with Ponytail

Ellian's Hair "★ Hair 01" (`M_Hair_01`) with a low ponytail added at the nape. Nothing else about the hair changes:
untouched strand clumps keep their vertices, weights, UVs, vertex colours and custom normals.

**Requires Ellian's Hair** (`Ellian's Hair.pak`, folder `Hiji_Hair`). The visual refers to that mod's materials by id,
and `meta.lsx` declares the dependency so BG3 Mod Manager loads it first.

**Personal use.** The shipped mesh is derived from Hijimare's; do not upload it without their permission. The pak and
the derived meshes are git-ignored.

## What it registers

| Where | Rows | How |
|---|---|---|
| Human, Elf, Half-Elf, Drow, Tiefling, masculine, normal build | 5 `CharacterCreationAppearanceVisual` rows | same rows Ellian's Hair 01 uses |
| Dhaen Extended races (11 merge targets) | 1 `CharacterCreationSharedVisual` + 11 `Race` nodes with `MergedInto` | additive, copied from how `Dhaen_Hair-Merged` adds hair: the race's own hair list is kept |

Not registered: strong build (`MS_Hair_01`), feminine (`F_`/`FS_`), Gith, Dwarf, Gnome. Their meshes are different files.
Ask if you want them: it is the same steps on those meshes.

## Rebuild

```bash
python tools/hair_mod.py unpack items/hair01_ponytail            # Ellian's GR2 -> extracted/hair_base/M_Hair_01.glb
blender -b -P tools/hair_ponytail.py -- --base extracted/hair01/M_Hair_01.glb \
    --head extracted/head_hum_m_a/HUM_M_NKD_Head_A.glb \
    --out items/hair01_ponytail/art/out/hair01_ponytail.blend --renders build/hair01_renders   # ABSOLUTE paths
blender -b -P tools/hair_blender.py -- --in <that .blend> --out build/hair01_work/hair01_export.glb --tris 70000
python tools/hair_mod.py gr2 items/hair01_ponytail build/hair01_work/hair01_export.glb
python tools/hair_mod.py build items/hair01_ponytail && python tools/hair_mod.py pack items/hair01_ponytail
python tools/hair_mod.py check items/hair01_ponytail
```

The ponytail's parameters (tie height, length, flip, fullness) are at the top of `tools/hair_ponytail.py`.
Length 19-24 cm, tip about z 1.55: kept short because the head reference has no body, so shoulder clipping is untested.

## Bugs found on the way (fixed)

* `hair_retarget.py` copied Blender's 16-bit normalized vertex colours as raw 0..65535 floats, so Divine clamped every
  strand colour to white. Shipped colours now match the original (mean 0.247 vs 0.254).
* Divine `convert-model` fails on some GR2s with no `-e` flag (index out of bounds) and works with any; `unpack` passes
  `-e export-normals/-tangents/-uvs`.
* The preview renderer hid LOD1 and that state was saved, so the exporter skipped LOD1.

## Not verified

Nothing here has been loaded in game. Untested: how the tail sits against armour and shoulders, and the Dhaen
registration (structurally identical to `Dhaen_Hair-Merged`'s, but that mechanism has not been exercised by this pak).
