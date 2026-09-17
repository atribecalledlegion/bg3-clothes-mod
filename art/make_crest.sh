#!/bin/sh
# Builds the Uchiha crest artwork and its mask stamp from art/palette.txt.
#
# Geometry is measured from obito_uchiha_robe_back_profile.jpg (crest diameter 73px there)
# and expressed as ratios of the circle diameter D:
#   * fan face  : circle of diameter D
#   * red/white : NOT a straight split. An arc of radius 0.884*D centred 1.418*D below the
#                 circle top, so the white region is domed -- 0.534*D deep at the centre,
#                 0.65*D at the edges. Fitted to the reference to within 1px.
#   * handle    : parallel-sided stem, 0.082*D wide, running 0.35*D below the circle.
#
# Two ImageMagick gotchas are worked around, both silent if you get them wrong:
#   * PNG32: on every output. The PNG encoder downgrades images whose pixels are all
#     R=G=B to grayscale; compositing colour onto such a base desaturates it with no error.
#   * +antialias on the mask stamp. A soft edge in MSKcloth blends toward a dye ID colour
#     and haloes the crest in game.
set -e
M="${MAGICK:-C:/Program Files/ImageMagick-7.1.2-Q16-HDRI/magick.exe}"
OUT=art/source
mkdir -p "$OUT"

RED=$(sed -n 's/^crest_red *= *//p'   art/palette.txt)
WHT=$(sed -n 's/^crest_white *= *//p' art/palette.txt)
INK=$(sed -n 's/^outline *= *//p'     art/palette.txt)

D=900; PAD=62; CX=512; W=1024; H=1360
CTOP=$PAD
CCY=$((CTOP + D/2))              # circle centre y = 512
CBOT=$((CTOP + D))               # 962
ARC_R=796                        # 0.884 * D
ARC_CY=$((CTOP + 1276))          # 1.418 * D below circle top
STEM_HW=37                       # half of 0.082 * D
STEM_BOT=$((CBOT + 315))         # 0.35 * D
# Outline thickness, in SOURCE pixels (the source circle is 900px wide).
# The crest is ~192px in the final 2048 texture, so source pixels shrink by ~4.7x.
# DXT1 stores only two colour endpoints per 4x4 block, so a dark outline thinner than one
# block cannot be represented between purple and white: it breaks up and smears, which
# reads in game as the crest bleeding at the edges when the camera turns.
# 20 source px -> ~4.3px final, just over one block.
DILATE=20

# 1. silhouette: fan face + handle
"$M" -size ${W}x${H} xc:black +antialias -fill white \
     -draw "circle ${CX},${CCY} ${CX},${CTOP}" \
     -draw "rectangle $((CX-STEM_HW)),$((CBOT-40)) $((CX+STEM_HW)),${STEM_BOT}" \
     -alpha off "$OUT/crest_silhouette.png"

# 2. the arc that separates red from white
"$M" -size ${W}x${H} xc:black +antialias -fill white \
     -draw "circle ${CX},${ARC_CY} ${CX},$((ARC_CY-ARC_R))" \
     -alpha off "$OUT/crest_arc.png"

# 3. white region = silhouette AND arc ; red region = the rest of the silhouette
"$M" "$OUT/crest_silhouette.png" "$OUT/crest_arc.png" -compose Multiply -composite \
     -alpha off "$OUT/crest_white_mask.png"

# 4. layers
"$M" "$OUT/crest_silhouette.png" -morphology Dilate Disk:${DILATE} "$OUT/crest_outline_mask.png"
"$M" -size ${W}x${H} xc:"$INK" "$OUT/crest_outline_mask.png" -alpha off \
     -compose CopyOpacity -composite "PNG32:$OUT/l_ink.png"
"$M" -size ${W}x${H} xc:"$RED" "$OUT/crest_silhouette.png" -alpha off \
     -compose CopyOpacity -composite "PNG32:$OUT/l_red.png"
"$M" -size ${W}x${H} xc:"$WHT" "$OUT/crest_white_mask.png" -alpha off \
     -compose CopyOpacity -composite "PNG32:$OUT/l_white.png"

"$M" "$OUT/l_ink.png" "$OUT/l_red.png" -compose Over -composite \
                      "$OUT/l_white.png" -compose Over -composite \
     "PNG32:$OUT/uchiha_crest.png"

# 5. mask stamp: pure black over the whole footprint, outline included, so no part of the
#    crest -- not even its outline -- sits on a dye slot.
"$M" -size ${W}x${H} xc:"#000000" "$OUT/crest_outline_mask.png" -alpha off \
     -compose CopyOpacity -composite "PNG32:$OUT/uchiha_crest_maskstamp.png"

rm -f "$OUT/l_ink.png" "$OUT/l_red.png" "$OUT/l_white.png" "$OUT/crest_arc.png"
"$M" identify -format "%f  %wx%h  %[colorspace]\n" \
     "$OUT/uchiha_crest.png" "$OUT/uchiha_crest_maskstamp.png"
