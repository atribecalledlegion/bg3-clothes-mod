#!/bin/sh
# DIAGNOSTIC BUILD -- not for release.
#
# Replaces the robe's base colour with an unmistakable pattern so one look in game answers
# the question that every remaining theory depends on: is the item using OUR material, or
# still falling back to Gale's vanilla robe?
#
#   bright green + magenta grid + the crest
#
#   robe is GREEN with a crest   -> our material and UVs are live; everything works
#   robe is GREEN, no crest      -> our material is live, the crest placement is wrong
#   robe is still PURPLE         -> our material is NOT being used; it is still Gale's robe
#
# Restore with:  sh art/make_textures.sh && ./build.ps1 -Install
set -e
M="${MAGICK:-C:/Program Files/ImageMagick-7.1.2-Q16-HDRI/magick.exe}"
OUT=src/Public/ObitoUchihaRobe/Assets/Textures/Armor
W=200; H=266; OFFX=1529; OFFY=282     # same crest placement as the real build

"$M" -size 2048x2048 xc:"#00C400" \
     -fill "#FF00C8" \
     \( -size 2048x2048 xc:none -fill "#FF00C8" \
        -draw "rectangle 0,0 2047,24" -draw "rectangle 0,1024 2047,1048" \
        -draw "rectangle 0,0 24,2047" -draw "rectangle 1024,0 1048,2047" \) \
     -compose Over -composite \
     "PNG24:art/source/diag_base.png"

"$M" art/source/diag_base.png \
     \( art/source/uchiha_crest.png -resize ${W}x${H}! -rotate 90 \) \
     -geometry +${OFFX}+${OFFY} -compose Over -composite \
     -define dds:compression=dxt1 -define dds:mipmaps=12 \
     "$OUT/HUM_M_ARM_Robe_A_BM.DDS"

"$M" art/source/diag_base.png \
     \( art/source/uchiha_crest.png -resize 151x201! \) \
     -geometry +240+335 -compose Over -composite \
     -define dds:compression=dxt1 -define dds:mipmaps=12 \
     "$OUT/HUM_F_ARM_Robe_A_Body_BM.DDS"

"$M" identify -format "%f  %wx%h  avg=%[fx:int(255*mean.r)],%[fx:int(255*mean.g)],%[fx:int(255*mean.b)]\n" \
     "$OUT/HUM_M_ARM_Robe_A_BM.DDS" "$OUT/HUM_F_ARM_Robe_A_Body_BM.DDS"
