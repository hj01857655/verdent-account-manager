@echo off
chcp 65001 >nul 2>&1
cls
echo ========================================
echo  Verdent Account Manager - Dev Start
echo ========================================
echo.

cd /d "%~dp0"

if not exist "node_modules\" (
    echo [1/2] Installing dependencies...
    call npm install
    if errorlevel 1 (
        echo Error: Failed to install dependencies
        pause
        exit /b 1
    )
) else (
    echo [1/2] Dependencies already installed
)

echo.
echo [2/2] Starting development server...
echo.
echo Tips: 
echo   - Frontend will start at http://localhost:5173
echo   - Tauri window will open automatically
echo   - Vue code changes will hot reload
echo   - Rust code changes require restart
echo.
echo Press Ctrl+C to stop the server
echo ----------------------------------------
echo.

call npm run tauri dev

if errorlevel 1 (
    echo.
    echo Error: Failed to start
    echo.
    echo Common issues:
    echo   1. Make sure Rust is installed: https://rustup.rs
    echo   2. Make sure Node.js 18+ is installed
    echo   3. Check firewall settings
    echo   4. Check error messages above
    echo.
    pause
    exit /b 1
)
