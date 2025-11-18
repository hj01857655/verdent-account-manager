@echo off
title Verdent Account Manager - 管理员启动

:: 检查是否有管理员权限
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ========================================
    echo   Verdent Account Manager 需要管理员权限
    echo ========================================
    echo.
    echo 即将请求管理员权限...
    echo.
    
    :: 使用 PowerShell 请求管理员权限并重新运行
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit
)

:: 已有管理员权限，启动应用
echo ========================================
echo   正在以管理员权限启动应用...
echo ========================================

cd /d "%~dp0"

:: 检查是否存在发布版本
if exist "src-tauri\target\release\verdent-account-manager.exe" (
    echo 启动发布版本...
    start "" "src-tauri\target\release\verdent-account-manager.exe"
) else if exist "src-tauri\target\debug\verdent-account-manager.exe" (
    echo 启动调试版本...
    start "" "src-tauri\target\debug\verdent-account-manager.exe"
) else (
    echo 错误：找不到可执行文件！
    echo.
    echo 请先运行以下命令编译项目：
    echo   npm run tauri build
    echo.
    pause
    exit /b 1
)

:: 等待一秒后退出
timeout /t 1 /nobreak >nul
exit
