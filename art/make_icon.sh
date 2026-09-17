#!/bin/sh
# Renders the inventory icon from the actual robe mesh + the built base colour texture,
# so the icon shows the real item rather than a stand-in graphic.
#
# Icon delivery: BG3 resolves an item's Icon key from the shared atlases first, then from
# loose per-icon DDS files. Mods can use the loose route -- TutorialChestSummoning does
# exactly this and its icon works -- which avoids having to build an atlas.
#   Tooltips/Icons          380x380, no mip chain   (mouse/keyboard UI)
#   ControllerUIIcons       144x144, no mip chain   (controller UI)
# Vanilla ships the controller one as BC7, which ImageMagick cannot write; DXT5 is used
# for both, and the engine reads the format from the DDS header.
set -e
M="${MAGICK:-C:/Program Files/ImageMagick-7.1.2-Q16-HDRI/magick.exe}"
T=art/source/_iconwork
mkdir -p "$T"
ICON=Item_UNI_ObitoUchihaRobe
TIP=src/Public/Game/GUI/Assets/Tooltips/Icons
CTL=src/Public/Game/GUI/Assets/ControllerUIIcons/skills_png
mkdir -p "$TIP" "$CTL"

"$M" art/source/built_masculine_BM.png -depth 8 "RGB:$T/i_bm.raw"
"$M" -size 2048x2048 xc:white -depth 8 "RGB:$T/i_white.raw"
python tools/texview.py art/source/mesh/robe.dae HUM_M_ARM_Robe_A_Body_mesh "$T/i_bm.raw"    2048 "$T/i_col.raw"  900 back
python tools/texview.py art/source/mesh/robe.dae HUM_M_ARM_Robe_A_Body_mesh "$T/i_white.raw" 2048 "$T/i_mask.raw" 900 back

"$M" -size 900x900 -depth 8 "RGB:$T/i_col.raw"  "PNG24:$T/i_col.png"
"$M" -size 900x900 -depth 8 "RGB:$T/i_mask.raw" -colorspace gray -threshold 1% "PNG24:$T/i_mask.png"

# flat render + a soft top-lit gradient, so the silhouette reads with some depth
"$M" "$T/i_col.png" \
     \( -size 900x900 gradient:"gray82"-"gray45" \) -compose Overlay -composite \
     "$T/i_shaded.png"
"$M" "$T/i_shaded.png" "$T/i_mask.png" -alpha off -compose CopyOpacity -composite \
     "PNG32:$T/i_rgba.png"

"$M" "$T/i_rgba.png" -trim +repage -resize 330x330 -background none -gravity center \
     -extent 380x380 -define dds:compression=dxt5 -define dds:mipmaps=0 "$TIP/$ICON.DDS"
"$M" "$T/i_rgba.png" -trim +repage -resize 126x126 -background none -gravity center \
     -extent 144x144 -define dds:compression=dxt5 -define dds:mipmaps=0 "$CTL/$ICON.DDS"

"$M" identify -format "%f  %wx%h  %b\n" "$TIP/$ICON.DDS" "$CTL/$ICON.DDS"
rm -rf "$T"
