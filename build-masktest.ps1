# Builds the dye-behaviour test pak.
#
# This is a REPLACER, not the mod: it overwrites the vanilla robe colour masks at their
# original paths, so every ARM_Robe_A in the game (Gale's included) gets the crest area
# blacked out in its mask. Nothing else changes -- no new item, no new artwork.
#
# Purpose: prove or disprove the one assumption the whole design rests on, that a texel
# left black in MSKcloth is excluded from every dye slot. Wear any ARM_Robe_A robe, dye
# it, and watch the crest-shaped patch.
#   patch keeps its colour while the rest recolours -> the plan holds
#   patch recolours with everything else            -> use the fallback in README section 2
#
# Remove this pak before playing normally.
$Divine = Join-Path $env:USERPROFILE "Tools\LSLib\Tools\Divine.exe"
$Src    = Join-Path $PSScriptRoot "testpak"
$Pak    = Join-Path $PSScriptRoot "ObitoCrestMaskTest.pak"
if (-not (Test-Path $Divine)) { throw "divine.exe not found at $Divine" }
& $Divine -g bg3 -a create-package -s $Src -d $Pak -c lz4
if ($LASTEXITCODE -ne 0) { throw "create-package failed" }
Write-Host "built $Pak"
Write-Host "To test: copy it to `"$env:LOCALAPPDATA\Larian Studios\Baldur's Gate 3\Mods`" and enable 'Obito Crest Mask Test' in BG3 Mod Manager."
