# UV placement — derived from the meshes

Resolved by converting the robe's GR2 meshes to COLLADA and reading their UVs.
`tools/crestplace.py` reproduces every number here.

## Getting the meshes out

`Divine.exe -a convert-model` fails on BG3 GR2s with
*"Granny2.dll is required for compressed GR2 files"*. LSLib ships `granny2.dll` in its
**root**, but `Divine.exe` lives in `Tools\` and looks beside itself. Copy it across:

```bash
cp ~/Tools/LSLib/granny2.dll ~/Tools/LSLib/Tools/granny2.dll
```

Then:

```bash
~/Tools/LSLib/Tools/Divine.exe -g bg3 -a convert-model -s HUM_M_ARM_Robe_A_Body.GR2 -d robe.dae
```

## Orientation

**V is inverted.** COLLADA's UV origin is bottom-left, the texture's is top-left, so
`v_image = 1 - v_uv`. Established by sampling the vanilla mask at every triangle's
vertices and centroid and counting how often a triangle lands entirely inside one mask
region — a wrong flip cuts across region boundaries:

| | triangles uniform in mask |
|---|---|
| no flip | 65.5% |
| **flipped** | **84.3%** |

**The back faces +Z.** Rendering the −Z and +Z facing triangles separately, the −Z side
carries the robe's V-neck opening and the +Z side is a plain panel under a high collar.

## The back panel unwrap

Selecting back-facing outer triangles in the upper body and keeping the largest
UV-connected island gives a single clean panel. Fitting affine `(worldX, worldY) → (u,v)`
over the **flat central patch only**:

| Mesh | fit RMS | isotropy | scale |
|---|---|---|---|
| HUM_M | 1.2 px | 0.998 | 1322 px/unit |
| HUM_F | 2.9 px | 1.003 | 1472 px/unit |
| DWR_M | 3.1 px | 1.206 | 1020 px/unit |
| HFL_F | 6.1 px | 0.985 | 1568 px/unit |

Restricting to the flat patch matters: fitting the whole panel, shoulders and collar
included, takes the residual from **1.2 px to 165 px**. The unwrap is conformal locally,
so a circle in texture space stays a circle on the surface — confirmed by measuring the
rendered crest, which came out at 0.94 of its unforeshortened height against a surface
tilted only 2.6° from straight-back.

## Two texture sets, not one

The masculine and feminine robes use **different meshes, different materials and
different mask textures**, and unwrap differently:

| | masculine | feminine |
|---|---|---|
| back island (px) | x 1347–1995, y 59–704 | x 74–557, y 125–672 |
| orientation | **rotated 90°** — garment "up" runs along texture **+u** | upright |
| mask texture | `HUM_M_ARM_Robe_A_MSKcloth.DDS` | `HUM_F_ARM_Robe_A_Body_MSKcloth.DDS` |
| body material | `92cca1dc-071f-1a40-6eb3-de8e16a38c25` | `4bf29629-687c-5330-bce8-8d22432941c8` |
| shared with | dwarves (confirmed: `DWR_M_ARM_Robe_A_Body` carries material `92cca1dc`) | halflings |

Because the masculine panel is rotated, the crest image is rotated **90° clockwise**
before compositing; the feminine one is pasted upright.

## Landmarks and the placement

From `obito_uchiha_robe_back_profile.jpg`: collar top y=223, obi top y=483, crest centre
y=348.5, crest diameter 73 px. So the crest sits **0.483 of the way from collar to waist**
with a diameter of **0.281** of that span.

A useful cross-check: in the reference the collar-to-obi span (260 px) and the back panel
width (261 px) are equal, and the same near-equality holds in the masculine UV island
(644 vs 645 px).

| | crest centre | diameter |
|---|---|---|
| HUM_M | (1680, 382) | 168 px |
| DWR_M | (1725, 382) | 143 px |
| **masculine, used** | **(1695, 382)** | **160 px** |
| HUM_F | (316, 404) | 137 px |
| HFL_F | (316, 418) | 130 px |
| **feminine, used** | **(316, 411)** | **133 px** |

The feminine pair agree to 14 px, so the average is exact enough. The masculine pair
differ by 45 px because dwarf proportions occupy the shared texture differently; the value
used is weighted 2:1 toward the human male, which has both the better fit and the commoner
body. Dwarves get the crest a few percent low — not visible in the render.

## Verified

`items/obito_uchiha_robe/art/make_textures.sh` builds both sets; the crest was then texture-mapped back onto
HUM_M, DWR_M, HUM_F and HFL_F and renders upright, centred and correctly sized on all
four. See `items/obito_uchiha_robe/reference/crest_on_bodies.png`.
