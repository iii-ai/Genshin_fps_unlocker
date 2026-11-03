$ErrorActionPreference = "Stop"
Push-Location $PSScriptRoot
try {
    py -3.12 -m PyInstaller --noconfirm --clean --onefile --windowed --uac-admin --name "原神帧率解锁-v1.0.0" --icon icon.ico --add-data "icon.ico;." --distpath dist_ui --workpath build_ui --specpath build_ui app.py
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed ($LASTEXITCODE)" }
} finally {
    Pop-Location
}
