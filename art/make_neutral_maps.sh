#!/bin/sh
# Flat stand-ins for the robe's normal and physical maps, which live in the virtual
# texture and have not been extracted. Wiring all four texture inputs is safer than
# leaving two off: a shader missing an expected input is a plausible cause of a material
# failing to render at all, and flat maps shade correctly, just without fabric detail.
# Replace with the extracted originals when available.
set -e
M="${MAGICK:-C:/Program Files/ImageMagick-7.1.2-Q16-HDRI/magick.exe}"
OUT=src/Public/ObitoUchihaRobe/Assets/Textures/Armor
mkdir -p "$OUT"
NM=$(sed -n 's/^neutral_nm *= *//p' art/palette.txt)
PM=$(sed -n 's/^neutral_pm *= *//p' art/palette.txt)
# NM matches vanilla normal maps: DXT5
"$M" -size 2048x2048 "xc:$NM" -define dds:compression=dxt5 -define dds:mipmaps=12 \
     "$OUT/ObitoUchihaRobe_NM.DDS"
# PM matches vanilla physical maps: DXT1
"$M" -size 2048x2048 "xc:$PM" -define dds:compression=dxt1 -define dds:mipmaps=12 \
     "$OUT/ObitoUchihaRobe_PM.DDS"
"$M" identify -format "%f  %wx%h  %b\n" "$OUT/ObitoUchihaRobe_NM.DDS" "$OUT/ObitoUchihaRobe_PM.DDS"
