# Yugito face: RaceMenu sculpt guide

The goal is an anime-leaning, feminine Yugito on the High Poly Head (HPH) female Nord head. You sculpt; Claude turns the export into her in-game face.

Slider names differ a little between RaceMenu versions. Treat the numbers as starting points (−1 … +1 scale) and judge by eye against the reference screenshots.

## 1. Test character (keeps your Obito save safe)

1. Start a **New Game**. Alternate Start opens character creation straight away.
2. Pick **Nord**, **Female**.
3. **Weight: 40%.** This must match Yugito's weight in the plugin, or she gets a neck seam.
4. Don't save this character when you're done. Just quit back to the menu.

## 2. Parts

| Part | What to pick |
|---|---|
| Head | The HPH female head. It's normally the default for a female Nord while High Poly Head is active. |
| Eyes | The Uchiha female split eye: right Sharingan, left Rinnegan (`…HMixed_Sharingan3R_Rinnegan`). **Leave every Iris slider at 0.** Iris Height/Spread made Obito's split eyes go cross-eyed. |
| Hair | Browse the **Anime style Hair** pack (VRoid hairs) for **side-swept bangs + a long ponytail**. Colour: pale blonde (e.g. RGB ≈ 230, 215, 160). **Note the hair's name.** |
| Brows | Thin, lightly arched, pale blonde. HPH brows (`00KLH_FemaleBrows…`) fit the HPH head best. **Note the name.** |
| Scars / beard / marks | None. |

## 3. Face shape (anime-leaning targets)

| Area | Direction | Start at |
|---|---|---|
| Head size | slightly smaller | 0.95 if there's a slider |
| Jaw width | narrower | −0.6 |
| Jaw forward | back | −0.3 |
| Chin width | narrow | −0.5 |
| Chin length | shorter | −0.2 |
| Cheekbones | higher, less wide | height +0.3, width −0.4 |
| Eye size / width | **bigger** (most important) | +0.6 … +1.0 |
| Eye height | slightly up | +0.2 |
| Eye depth | less sunken | −0.3 |
| Eye shape | rounder almond, outer corner slightly up | — |
| Nose | small, short, "button" | length −0.6, height +0.2, smallest nose type |
| Mouth | small | width −0.3 |
| Lips | soft, slightly full | — |
| Brows | high, flat to the face | height +0.2, forward −0.5 |

## 4. Skin and makeup

- **Skin tone:** pale/fair. **Complexion, age, dirt, scars: none.** Smooth skin is half of the anime look.
- **Lipstick:** red (as in the screenshots), high opacity.
- **Eyeliner:** dark upper liner. Anime eyes read as strongly outlined.
- **Eyeshadow:** none or very light.

## 5. Export

1. **Save Preset** (backup: lets you reload and tweak later).
2. Use RaceMenu's **Export Head** option. The key is shown in the bar along the bottom of RaceMenu.
3. Quit the game **without saving**.
4. Tell Claude the hair and brow names you picked. Claude finds the export (MO2 puts it in **Overwrite**, under `SKSE/Plugins/CharGen/Exported`), converts it into Yugito's face files, and matches her plugin record to the same parts.
