# Artwork reference — measured from the supplied images

Source files in the project root:

| File | Actual format | Size | Used for |
|---|---|---|---|
| `obito_uchiha_robe_front_profile.jpg` | **PNG** | 828x1721 | robe / obi / lining colours |
| `obito_uchiha_robe_side_angle_profile.jpg` | **PNG** | 6368x8896 | robe / obi / lining colours |
| `obito_uchiha_robe_back_profile.jpg` | JPEG | 1192x670 | crest colours, geometry, placement |

> Two of the three are PNGs carrying a `.jpg` extension. Nothing here cares, but it is why
> an earlier attempt to read one of them failed — decoders that trust the extension choke.

## Palette

Taken from a 14-colour quantised histogram of the front and side views, which agree to the
byte on the robe colour.

| Role | Value | Notes |
|---|---|---|
| robe purple | `#463E65` | identical in front and side views |
| robe shadow | `#323646` | fold/shade tone |
| lining cream | `#B3ACA0` | inner edge of the front opening, sleeve cuffs |
| obi white | `#E5E5E5` | |
| obi stripe | `#8B7E95` | lavender band through the obi |
| undergarment | `#212229` | |
| crest red | `#E70102` | from back view |
| crest white | `#F6F6F6` | from back view |
| outline ink | `#251B23` | from back view |

**The back view disagrees on the robe colour** — it renders it `#7C618E`, a lighter, flatter
lilac. The front and side are the more detailed pieces and agree exactly with each other,
so `#463E65` is taken as canonical and the back view is used only for the crest.

## Crest geometry

Measured against the back view, where the crest circle is 73px across. Everything is
expressed as a ratio of the circle diameter **D** so it scales to any texture resolution.

| Feature | Value |
|---|---|
| fan face | circle, diameter `D` |
| red/white divide | arc of radius `0.884 D`, centred `1.418 D` below the circle top |
| — depth at centre | `0.534 D` below circle top |
| — depth at edges | `0.65 D` below circle top |
| handle width | `0.082 D` |
| handle length | `0.35 D` below the circle |

**The divide is not a straight line.** It is a shallow arc bowing upward, so the white
region is domed — deepest at the sides, shallowest in the middle. A horizontal split looks
noticeably wrong next to the reference. The fitted arc reproduces the measured boundary to
within 1px at every sampled column:

| dx from centre | measured | fitted |
|---|---|---|
| −0.88 R | 0.644 D | 0.645 D |
| −0.49 R | 0.562 D | 0.570 D |
| 0.00 R | 0.534 D | 0.534 D |
| +0.47 R | 0.562 D | 0.570 D |
| +0.85 R | 0.658 D | 0.652 D |

## Placement on the garment

From the back view, at the crest's own height:

| Measure | Value |
|---|---|
| back panel width at crest height | 261 px |
| crest diameter | 73 px |
| **crest / back panel width** | **0.28** |
| horizontal position | centred (49% across) |
| vertical position | crest centre `0.22 D` below the shoulder line — high on the back |

These are proportions of the *illustration*, not of the UV map. They set the crest's size
and position relative to the back panel; the actual pixel rectangle still has to come from
the robe's UVs. See the open question in the README.

## Rebuilding

```bash
sh art/make_crest.sh
```

Reads `art/palette.txt`, writes `art/source/uchiha_crest.png` and
`art/source/uchiha_crest_maskstamp.png`. Change a colour in the palette file and re-run;
nothing else needs touching.
