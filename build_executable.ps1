$ErrorActionPreference = 'Stop'

$SaveToolsCommit = '790e0bcf7bacef47b048e110066617a8fbb40041'
$PyOozCommit = '9af53d1faaa2f9a7dafe6d6caea117c762dc71d9'

function Assert-NativeSuccess {
    param([string]$Step)
    if ($LASTEXITCODE -ne 0) {
        throw "$Step failed with exit code $LASTEXITCODE"
    }
}

function Get-PythonCommand {
    foreach ($cmd in @('python3', 'python')) {
        try {
            $version = & $cmd --version 2>&1
            if ($version -match '^Python 3\.') { return $cmd }
        } catch { continue }
    }
    throw 'Python 3.11 or newer is required.'
}

if (-not (Get-Command corepack -ErrorAction SilentlyContinue)) {
    throw 'Node.js 20 or newer with Corepack is required.'
}

$PythonCommand = Get-PythonCommand
$versionOutput = & $PythonCommand --version 2>&1
$versionNumbers = ($versionOutput -replace 'Python ', '') -split '\.'
if ([int]$versionNumbers[0] -lt 3 -or ([int]$versionNumbers[0] -eq 3 -and [int]$versionNumbers[1] -lt 11)) {
    throw 'Python 3.11 or newer is required.'
}
Write-Host "Using $PythonCommand ($versionOutput)"

Push-Location '.\frontend'
try {
    corepack pnpm install --frozen-lockfile
    Assert-NativeSuccess 'frontend dependency installation'
    corepack pnpm test
    Assert-NativeSuccess 'frontend tests'
    corepack pnpm build
    Assert-NativeSuccess 'frontend build'
} finally {
    Pop-Location
}

$WebUiPath = '.\src\palworld_save_studio\webui'
if (Test-Path $WebUiPath) { Remove-Item $WebUiPath -Recurse -Force }
New-Item -Path $WebUiPath -ItemType Directory | Out-Null
Copy-Item -Path '.\frontend\dist\*' -Destination $WebUiPath -Recurse -Force

if (Test-Path '.\venv') { Remove-Item '.\venv' -Recurse -Force }
& $PythonCommand -m venv venv
Assert-NativeSuccess 'virtual environment creation'
$VenvPython = '.\venv\Scripts\python.exe'
& $VenvPython -m pip install --upgrade pip
Assert-NativeSuccess 'pip upgrade'

$RuntimeRequirements = [IO.Path]::GetTempFileName()
try {
    Get-Content '.\requirements.txt' |
        Where-Object { $_ -notmatch 'palworld-save-tools' } |
        Set-Content -Path $RuntimeRequirements -Encoding ascii

    & $VenvPython -m pip install -r $RuntimeRequirements
    Assert-NativeSuccess 'runtime dependency installation'
    & $VenvPython -m pip install 'loguru==0.7.3' 'orjson==3.11.8'
    Assert-NativeSuccess 'save-tools dependency installation'
    & $VenvPython -m pip install --no-deps "pyooz @ git+https://github.com/oMaN-Rod/pyooz.git@$PyOozCommit"
    Assert-NativeSuccess 'pinned pyooz installation'
    & $VenvPython -m pip install --no-deps "palworld-save-tools @ git+https://github.com/oMaN-Rod/palworld-save-tools.git@$SaveToolsCommit"
    Assert-NativeSuccess 'pinned palworld-save-tools installation'
} finally {
    Remove-Item $RuntimeRequirements -Force -ErrorAction SilentlyContinue
}

$env:PYTHONPATH = '.\src'
& $VenvPython -m unittest discover -s tests -v
Assert-NativeSuccess 'Palworld 1.0 regression tests'

if (Test-Path '.\dist') { Remove-Item '.\dist' -Recurse -Force }

& $VenvPython -m PyInstaller `
    --clean `
    --onefile `
    --icon '.\icon.ico' `
    --add-data 'src/palworld_save_studio/assets;assets' `
    --add-data 'src/palworld_save_studio/webui;webui' `
    --hidden-import 'ooz' `
    --hidden-import 'pkg_resources.extern' `
    --paths '.\src' `
    --name 'Palworld-Save-Studio' `
    --log-level INFO `
    '.\src\palworld_save_studio\__main__.py'
Assert-NativeSuccess 'PyInstaller build'

$Executable = '.\dist\Palworld-Save-Studio.exe'
if (-not (Test-Path $Executable)) { throw "Built executable not found: $Executable" }

& $Executable --help | Out-Null
Assert-NativeSuccess 'Windows executable smoke test'

$Hash = (Get-FileHash -Algorithm SHA256 $Executable).Hash.ToLowerInvariant()
Set-Content -Path '.\dist\Palworld-Save-Studio.exe.sha256' -Value "$Hash  Palworld-Save-Studio.exe" -Encoding ascii
Write-Host "Built $Executable"
Write-Host "SHA-256: $Hash"
