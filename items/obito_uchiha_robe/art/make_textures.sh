#!/bin/sh
# Composites the Uchiha crest onto the robe textures at the derived UV positions and
# writes game-ready DDS files.
#
# TWO texture sets are required. The masculine and feminine robes have different meshes,
# different materials and different mask textures, and their back panels are unwrapped
# differently -- the masculine panel is rotated 90 degrees in UV space, the feminine one
# is upright. Dwarves share the masculine set; halflings share the feminine one.
#
# Placement derived by tools/crestplace.py from the meshes themselves.
# Run from the repo root. See reference/UV_PLACEMENT.md for the method and the numbers.
set -e
M="${MAGICK:-C:/Program Files/ImageMagick-7.1.2-Q16-HDRI/magick.exe}"
I=items/obito_uchiha_robe
OUT=$I/src/Public/ObitoUchihaRobe/Assets/Textures/Armor
SRC=$I/art/source         # crest artwork (committed)
WORK=build/work/obito_uchiha_robe   # intermediates (ignored)
mkdir -p "$OUT" "$WORK"

ROBE=$(sed -n 's/^robe_purple *= *//p' $I/art/palette.txt)

# --- placement -------------------------------------------------------------------------
# Expressed as crest CENTRE and DIAMETER in texture pixels; the paste rectangle and offset
# are derived, so changing size needs one number and the crest stays centred.
#
# Verified in game with a UV-probe build: the back panel samples exactly the predicted
# region and the crest lands where intended.
#
# masculine: rotated 90 deg (garment "up" runs along texture +u).
#   HUM_M alone wants centre (1680,382) and DWR_M wants (1725,382); they share one texture,
#   so this is weighted 2:1 toward the human male -- the better fit (1.2px rms vs 3.1) and
#   the commoner body. Dwarves get the crest ~3% low, which is not visible.
M_CX=1695; M_CY=382; M_ROT=90
# feminine: upright. HUM_F and HFL_F agree to 14px.
F_CX=316;  F_CY=411; F_ROT=0
# Base diameters from tools/crestplace.py, times CREST_SCALE.
M_D_BASE=160; F_D_BASE=133
CREST_SCALE="${CREST_SCALE:-1.20}"
# ---------------------------------------------------------------------------------------

# geom <diameter> <centre-x> <centre-y> <rot> -> "W H OFFX OFFY"
# The source crest is 1024x1360 with its 900px circle centred at (512,512).
geom() {
    python -c "
import sys
D, cx, cy, rot = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4])
SW, SH, SD, SCX, SCY = 1024, 1360, 900.0, 512.0, 512.0
s = D / SD
w, h = round(SW*s), round(SH*s)
ccx, ccy = SCX*s, SCY*s
if rot == 90:            # 90 deg clockwise: (x,y) -> (h-1-y, x)
    rcx, rcy = (h-1-ccy), ccx
else:
    rcx, rcy = ccx, ccy
print('%d %d %d %d' % (w, h, round(cx-rcx), round(cy-rcy)))
" "$1" "$2" "$3" "$4"
}

set -- $(geom "$(python -c "print(round($M_D_BASE*$CREST_SCALE))")" $M_CX $M_CY $M_ROT)
M_W=$1; M_H=$2; M_OFFX=$3; M_OFFY=$4
set -- $(geom "$(python -c "print(round($F_D_BASE*$CREST_SCALE))")" $F_CX $F_CY $F_ROT)
F_W=$1; F_H=$2; F_OFFX=$3; F_OFFY=$4
echo "crest scale ${CREST_SCALE}:  masculine ${M_W}x${M_H} @ +${M_OFFX}+${M_OFFY}   feminine ${F_W}x${F_H} @ +${F_OFFX}+${F_OFFY}"

place() {   # place <crest> <base> <out> <w> <h> <rot> <offx> <offy> <hard|soft>
    if [ "$9" = hard ]; then
        # Mask stamps must stay hard-edged: point sampling plus an alpha re-threshold,
        # or the rescaled edge blends toward a dye ID colour and haloes the crest.
        "$M" "$2" \( "$1" -filter point -resize "$4"x"$5"! -rotate "$6" \
             -channel A -threshold 50% +channel \) \
             -geometry +"$7"+"$8" -compose Over -composite +antialias "PNG24:$3"
    else
        "$M" "$2" \( "$1" -resize "$4"x"$5"! -rotate "$6" \) \
             -geometry +"$7"+"$8" -compose Over -composite "PNG24:$3"
    fi
}

build() {   # build <tag> <vanilla-mask> <mask-out> <bm-out> <w> <h> <rot> <offx> <offy> <dae> <geom>
    tag=$1; vmask=$2; mout=$3; bout=$4; w=$5; h=$6; rot=$7; ox=$8; oy=$9
    shift 9; dae=$1; geom=$2

    # Colour mask. MASK_CREST=1 stamps the crest footprint black; default is off.
    #
    # Black does NOT mean "untinted". Verified in game with a UV-probe build: the crest
    # rendered SOLID BLACK on an otherwise correct red panel. The shader treats a texel
    # matching no colour slot as tint (0,0,0) and multiplies the base colour to zero.
    # Leaving the vanilla mask alone gives the crest the same slot as the rest of the back
    # panel, so it renders normally.
    #
    # Dye-proofing cannot be done this way; see README section 2 for the separate-material
    # fallback, which needs a mesh split.
    if [ "${MASK_CREST:-0}" = 1 ]; then
        place "$SRC/uchiha_crest_maskstamp.png" "$vmask" "$WORK/built_${tag}_MSK.png" \
              "$w" "$h" "$rot" "$ox" "$oy" hard
        "$M" "$WORK/built_${tag}_MSK.png" -define dds:compression=dxt1 -define dds:mipmaps=12 \
              "$OUT/$mout"
    elif [ "${FLATTEN_PANEL:-1}" = 1 ]; then
        # The vanilla mask splits the back panel across four slots (blue 46%, orange 40%,
        # violet 7%, red 6%). Those slots are grouped Cloth_/Leather_/Metal_ and the shader
        # gives each a different surface response, so their boundaries show as seams even
        # with every colour forced white -- two of them run straight across the top of the
        # crest. Flattening the panel to one slot removes them.
        python tools/make_mask_patch.py "$dae" "$geom" "$vmask" "$OUT/$mout" "$WORK"
    else
        # Copied byte for byte, not re-encoded. Round-tripping the vanilla mask through
        # ImageMagick introduced ~2700 black block endpoints the original does not have,
        # and black texels are exactly what renders a surface black.
        cp "$vmask" "$OUT/$mout"
    fi

    # base colour. Until the vanilla virtual texture is extracted this sits on a flat
    # robe-purple ground; drop the extracted _BM in as build/work/obito_uchiha_robe/base_${tag}_BM.png and
    # re-run, nothing else changes.
    base="$WORK/base_${tag}_BM.png"
    [ -f "$base" ] || "$M" -size 2048x2048 xc:"$ROBE" "PNG24:$base"
    place "$SRC/uchiha_crest.png" "$base" "$WORK/built_${tag}_BM.png" \
          "$w" "$h" "$rot" "$ox" "$oy" soft
    "$M" "$WORK/built_${tag}_BM.png" -define dds:compression=dxt1 -define dds:mipmaps=12 \
          "$OUT/$bout"
}

build masculine extracted/mesh/HUM_M_ARM_Robe_A_MSKcloth.DDS \
      HUM_M_ARM_Robe_A_MSKcloth.DDS HUM_M_ARM_Robe_A_BM.DDS \
      $M_W $M_H $M_ROT $M_OFFX $M_OFFY \
      extracted/mesh/robe.dae HUM_M_ARM_Robe_A_Body_mesh

build feminine  extracted/mesh/HUM_F_ARM_Robe_A_Body_MSKcloth.DDS \
      HUM_F_ARM_Robe_A_Body_MSKcloth.DDS HUM_F_ARM_Robe_A_Body_BM.DDS \
      $F_W $F_H $F_ROT $F_OFFX $F_OFFY \
      extracted/mesh/HUM_F.dae HUM_F_ARM_Robe_A_Body_Mesh

"$M" identify -format "%f  %wx%h  %b\n" "$OUT"/*.DDS
