# Build a *separate* PyInstaller one-folder Windows candidate.
# Use absolute asset and entry-point paths because --specpath is outside
# the project root (relative --add-data paths resolve from the spec directory).
# It does not commit, push, tag, upload, delete the existing one-file EXE,
# or modify application source. Requires Python/PyInstaller dependencies.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$ProjectRoot
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$project = (Resolve-Path -LiteralPath $ProjectRoot -ErrorAction Stop).ProviderPath
$python = Join-Path $project 'venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'Project Python venv was not found.' }
Push-Location $project
try {
    $version = (& $python -c 'from src.app_info import APP_VERSION; print(APP_VERSION)')
    if ($LASTEXITCODE -ne 0 -or @($version).Count -ne 1 -or $version.Trim() -ne '1.0.0') {
        throw "Expected app version 1.0.0, found '$version'."
    }
    $name = ((& $python -c 'from src.app_info import APP_TITLE; print(APP_TITLE)') -join '').Trim() + ' v1.0.0'
    if ($LASTEXITCODE -ne 0) { throw 'Unable to read APP_TITLE.' }
    $ico = Join-Path $project 'src\resources\icons\icon.ico'
    if (-not (Test-Path -LiteralPath $ico -PathType Leaf)) { throw "Missing release icon: $ico" }
    if (@(Get-ChildItem -LiteralPath 'src/resources/guides' -Filter '*.png' -File).Count -ne 8) {
        throw 'Exactly eight Dimension Guide images are required.'
    }
    foreach ($f in @('src/main.py','src/ui/forms/main_window.ui','src/ui/forms/settings_dialog.ui',
        'src/ui/forms/inspect_results.ui','src/resources/data/as568_reference.json')) {
        if (-not (Test-Path -LiteralPath $f -PathType Leaf)) { throw "Missing required file $f" }
    }
    & $python -m PyInstaller --version
    if ($LASTEXITCODE -ne 0) { throw 'PyInstaller is not available in the project venv.' }

    $specpath = Join-Path $project 'build\release_onedir_spec'
    $workpath = Join-Path $project 'build\release_onedir_work'
    $distpath = Join-Path $project 'dist'
    foreach ($p in @($specpath,$workpath,$distpath)) {
        New-Item -ItemType Directory -Force -Path $p | Out-Null
    }
    # Explicit absolute source paths are essential because the spec file is
    # written to build/release_onedir_spec, NOT the project root.
    $pyiArgs = @(
        '--noconfirm', '--clean', '--onedir', '--windowed',
        '--paths', $project, '--name', $name,
        '--specpath', $specpath, '--workpath', $workpath, '--distpath', $distpath,
        '--icon', $ico
    )
    $resources = @(
        [pscustomobject]@{ Relative = 'src\ui\forms\main_window.ui'; Target = 'src/ui/forms' }
        [pscustomobject]@{ Relative = 'src\ui\forms\settings_dialog.ui'; Target = 'src/ui/forms' }
        [pscustomobject]@{ Relative = 'src\ui\forms\inspect_results.ui'; Target = 'src/ui/forms' }
        [pscustomobject]@{ Relative = 'src\resources\data\as568_reference.json'; Target = 'src/resources/data' }
        [pscustomobject]@{ Relative = 'src\resources\guides'; Target = 'src/resources/guides' }
        [pscustomobject]@{ Relative = 'src\resources\icons'; Target = 'src/resources/icons' }
    )
    foreach ($resource in $resources) {
        $source = Join-Path $project $resource.Relative
        if (-not (Test-Path -LiteralPath $source)) {
            throw "Missing required resource: $source"
        }
        $pyiArgs += @('--add-data', "$source;$($resource.Target)")
    }
    $optionalImages = Join-Path $project 'src\resources\images'
    if (Test-Path -LiteralPath $optionalImages -PathType Container) {
        $pyiArgs += @('--add-data', "$optionalImages;src/resources/images")
    }
    $entryPoint = Join-Path $project 'src\main.py'
    Write-Host "Building separate one-folder portable candidate: $name" -ForegroundColor Cyan
    & $python -m PyInstaller @pyiArgs $entryPoint
    if ($LASTEXITCODE -ne 0) { throw 'PyInstaller build failed.' }
    $out = Join-Path (Join-Path $distpath $name) "$name.exe"
    if (-not (Test-Path -LiteralPath $out -PathType Leaf)) { throw "Packaged EXE not found: $out" }
    $dlls = @(Get-ChildItem -LiteralPath (Join-Path $distpath $name) -File -Recurse -Filter 'Qt6*.dll')
    Write-Host "`nBUILD COMPLETE (one-folder candidate)" -ForegroundColor Green
    Write-Host "Executable: $out"
    Write-Host "EXE SHA-256: $((Get-FileHash -LiteralPath $out -Algorithm SHA256).Hash.ToLowerInvariant())"
    Write-Host "Qt6 DLLs detected: $($dlls.Count)"
    Write-Host 'Keep the entire distribution folder together. The EXE alone is not a portable deployment.'
    Write-Host 'No Git operation or publication was performed.'
} finally { Pop-Location }
