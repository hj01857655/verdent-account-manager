@echo off
chcp 65001 >nul 2>&1
cls
echo ========================================
echo  Verdent Account Manager - Build
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] Checking dependencies...
if not exist "node_modules\" (
    echo Installing dependencies...
    call npm install
    if errorlevel 1 (
        echo Error: Failed to install dependencies
        pause
        exit /b 1
    )
) else (
    echo Dependencies already installed
)

echo.
echo [2/3] Building frontend...
call npm run build
if errorlevel 1 (
    echo Error: Frontend build failed
    pause
    exit /b 1
)

echo.
echo [3/3] Building Tauri application...
echo This may take a few minutes, please wait...
echo.

call npm run tauri build

if errorlevel 1 (
    echo.
    echo Error: Build failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo  Build successful!
echo ========================================
echo.
echo Build output location:
echo   src-tauri\target\release\bundle\
echo.
echo Installer packages:
echo   - MSI: src-tauri\target\release\bundle\msi\
echo   - NSIS: src-tauri\target\release\bundle\nsis\
echo.
pause
