# Builds ObitoUchihaRobe.pak.
#
#   .\build.ps1            -> builds into the project folder
#   .\build.ps1 -Install   -> also copies it into the BG3 Mods folder
#
# Staging matters: the repo keeps resources as .lsx because they are readable and
# diffable, but the game only reads .lsf. Converting in place and packing the folder
# would ship both, so this copies to build\ first, converts there, and drops the sources.
param([switch]$Install)

$ErrorActionPreference = 'Stop'
$Divine  = Join-Path $env:USERPROFILE "Tools\LSLib\Tools\Divine.exe"
$ModName = "ObitoUchihaRobe"
$Src     = Join-Path $PSScriptRoot "src"
$Stage   = Join-Path $PSScriptRoot "build"
$Pak     = Join-Path $PSScriptRoot "$ModName.pak"

if (-not (Test-Path $Divine)) { throw "divine.exe not found at $Divine" }

if (Test-Path $Stage) { Remove-Item $Stage -Recurse -Force }
Copy-Item $Src $Stage -Recurse

# 1. resource .lsx -> .lsf  (meta.lsx must stay .lsx: the game reads it as XML)
Get-ChildItem -Path $Stage -Recurse -Filter "*.lsx" |
    Where-Object { $_.FullName -notlike "*\Mods\*" } |
    ForEach-Object {
        $lsf = [IO.Path]::ChangeExtension($_.FullName, ".lsf")
        Write-Host "  convert  $($_.Name) -> $(Split-Path $lsf -Leaf)"
        & $Divine -g bg3 -a convert-resource -i lsx -o lsf -s $_.FullName -d $lsf
        if ($LASTEXITCODE -ne 0) { throw "convert-resource failed on $($_.Name)" }
        # -LiteralPath is required: the Content folder is named [PAK]_ObitoUchihaRobe,
        # and PowerShell reads [...] in a path as a wildcard character class, so a plain
        # -Path never matches the real file and the .lsx source ships inside the pak.
        Remove-Item -LiteralPath $_.FullName
    }

# 2. localization .xml -> .loca  (convert-loca infers direction from the extensions;
#    passing -i/-o here is rejected)
Get-ChildItem -Path (Join-Path $Stage "Localization") -Recurse -Filter "*.xml" -ErrorAction SilentlyContinue |
    ForEach-Object {
        $loca = [IO.Path]::ChangeExtension($_.FullName, ".loca")
        Write-Host "  localize $($_.Name)"
        & $Divine -g bg3 -a convert-loca -s $_.FullName -d $loca
        if ($LASTEXITCODE -ne 0) { throw "convert-loca failed on $($_.Name)" }
        # -LiteralPath is required: the Content folder is named [PAK]_ObitoUchihaRobe,
        # and PowerShell reads [...] in a path as a wildcard character class, so a plain
        # -Path never matches the real file and the .lsx source ships inside the pak.
        Remove-Item -LiteralPath $_.FullName
    }

# 3. pack
& $Divine -g bg3 -a create-package -s $Stage -d $Pak -c lz4
if ($LASTEXITCODE -ne 0) { throw "create-package failed" }
Write-Host ("built $Pak ({0:N0} bytes)" -f (Get-Item $Pak).Length)

if ($Install) {
    $dest = Join-Path $env:LOCALAPPDATA "Larian Studios\Baldur's Gate 3\Mods"
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    Copy-Item $Pak $dest -Force
    Write-Host "installed to $dest"
    Write-Host "Enable '$ModName' in BG3 Mod Manager, then spawn UNI_ObitoUchihaRobe with SpawnAnyItem."
} else {
    Write-Host "not installed. Re-run with -Install, or copy the pak into:"
    Write-Host "  $(Join-Path $env:LOCALAPPDATA "Larian Studios\Baldur's Gate 3\Mods")"
}
