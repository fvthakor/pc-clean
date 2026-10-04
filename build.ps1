# ========================================================
# PcClean Windows Build Script (PowerShell)
# Compiles standalone executable via PyInstaller
# ========================================================

param(
    [switch]$OneFile = $false
)

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host " Building PcClean for Windows x64" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

# 1. Check Python
Write-Host "`n[1/3] Checking Python installation..." -ForegroundColor Yellow
$pyVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "Python not found in system PATH."
    exit 1
}
Write-Host "Found: $pyVersion" -ForegroundColor Green

# 2. Check dependencies
Write-Host "`n[2/3] Checking dependencies..." -ForegroundColor Yellow
python -m pip install -r requirements.txt --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Could not update dependencies automatically. Proceeding..."
}

# 3. Build executable
Write-Host "`n[3/3] Compiling standalone Windows executable..." -ForegroundColor Yellow
if ($OneFile) {
    Write-Host "Building single-file bundle (--onefile)..." -ForegroundColor Cyan
    pyinstaller --noconfirm --clean --windowed `
        --name PcClean `
        --icon resources/icons/pcclean.ico `
        --add-data "resources;resources" `
        --add-data "database/schema.sql;database" `
        --onefile `
        main.py
} else {
    Write-Host "Building production directory bundle (--onedir)..." -ForegroundColor Cyan
    pyinstaller --noconfirm --clean PcClean.spec
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n========================================================" -ForegroundColor Green
    Write-Host " Build Complete!" -ForegroundColor Green
    if ($OneFile) {
        Write-Host " Output executable: dist\PcClean.exe" -ForegroundColor Green
    } else {
        Write-Host " Output directory:  dist\PcClean\PcClean.exe" -ForegroundColor Green
    }
    Write-Host "========================================================`n" -ForegroundColor Green
} else {
    Write-Error "PyInstaller build failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}
