@echo off
REM ========================================================
REM PcClean Windows Build Script (Batch)
REM Compiles standalone standalone executable via PyInstaller
REM ========================================================

echo [1/3] Verifying Python and PyInstaller...
python --version
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not installed or not in PATH.
    exit /b 1
)

echo [2/3] Installing dependencies...
python -m pip install -r requirements.txt

echo [3/3] Compiling PcClean executable...
pyinstaller --noconfirm --clean PcClean.spec

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================
    echo Build Successful!
    echo Output directory: dist\PcClean\PcClean.exe
    echo ========================================================
) else (
    echo Error: PyInstaller build failed.
    exit /b %ERRORLEVEL%
)
