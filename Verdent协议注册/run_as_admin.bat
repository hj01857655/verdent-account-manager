@echo off
:: Verdent Token 更改器管理员启动脚本
:: 自动请求管理员权限并启动程序

:: 检查是否已经以管理员权限运行
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"

:: 如果没有管理员权限，请求提升
if '%errorlevel%' NEQ '0' (
    echo 正在请求管理员权限...
    goto UACPrompt
) else ( goto gotAdmin )

:UACPrompt
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    echo UAC.ShellExecute "%~s0", "", "", "runas", 1 >> "%temp%\getadmin.vbs"
    "%temp%\getadmin.vbs"
    del "%temp%\getadmin.vbs"
    exit /B

:gotAdmin
    pushd "%CD%"
    CD /D "%~dp0"

:checkPython
    :: 检查Python是否安装
    python --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo 错误: 未检测到Python安装
        echo 请先安装Python 3.7或更高版本
        pause
        exit /B
    )

:installDeps
    :: 检查并安装依赖
    echo 检查依赖库...
    pip show psutil >nul 2>&1
    if %errorlevel% neq 0 (
        echo 正在安装 psutil...
        pip install psutil
    )
    
    pip show pywin32 >nul 2>&1
    if %errorlevel% neq 0 (
        echo 正在安装 pywin32...
        pip install pywin32
    )

:runProgram
    :: 启动主程序
    echo.
    echo ================================
    echo   Verdent Token 更改器 (增强版)
    echo ================================
    echo.
    echo 正在以管理员权限启动程序...
    echo.
    
    :: 运行Python脚本
    python token_changer_gui.py
    
    if %errorlevel% neq 0 (
        echo.
        echo 程序运行出错，错误代码: %errorlevel%
        pause
    )
    
    exit
