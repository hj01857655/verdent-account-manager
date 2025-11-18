@echo off
title Verdent Account Manager - 开发模式（管理员）

:: 检查是否有管理员权限
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ========================================
    echo   开发模式需要管理员权限
    echo ========================================
    echo.
    echo 即将请求管理员权限...
    echo.
    
    :: 使用 PowerShell 请求管理员权限并重新运行
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit
)

:: 已有管理员权限
echo ========================================
echo   正在以管理员权限启动开发服务器...
echo ========================================
echo.
echo 按 Ctrl+C 停止服务器
echo.

cd /d "%~dp0"

:: 启动 Tauri 开发服务器
npm run tauri dev
