@echo off
chcp 65001 >nul
echo ======================================================================
echo Verdent AI 自动注册脚本 - Python 打包工具
echo ======================================================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [×] 错误: 未找到 Python 环境
    echo [*] 请先安装 Python 3.8 或更高版本
    pause
    exit /b 1
)

echo [✓] Python 环境检测成功
echo.

REM 检查并安装 PyInstaller
echo [*] 检查 PyInstaller...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [*] 安装 PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo [×] PyInstaller 安装失败
        pause
        exit /b 1
    )
)
echo [✓] PyInstaller 已就绪
echo.

REM 检查依赖包
echo [*] 检查 Python 依赖包...
pip show DrissionPage >nul 2>&1
if errorlevel 1 (
    echo [!] 警告: DrissionPage 未安装
    echo [*] 安装 DrissionPage...
    pip install DrissionPage
)

pip show requests >nul 2>&1
if errorlevel 1 (
    echo [!] 警告: requests 未安装
    echo [*] 安装 requests...
    pip install requests
)
echo [✓] 依赖包检查完成
echo.

REM 清理旧的构建文件
echo [*] 清理旧的构建文件...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "verdent_auto_register.exe" del /f /q "verdent_auto_register.exe"
echo [✓] 清理完成
echo.

REM 使用 PyInstaller 打包
echo [*] 开始打包 Python 脚本...
echo [*] 使用配置文件: verdent_auto_register.spec
pyinstaller --clean verdent_auto_register.spec

if errorlevel 1 (
    echo.
    echo [×] 打包失败!
    pause
    exit /b 1
)

REM 检查生成的 exe 文件
if not exist "dist\verdent_auto_register.exe" (
    echo.
    echo [×] 错误: 未找到生成的 exe 文件
    pause
    exit /b 1
)

echo.
echo [✓] 打包成功!
echo [*] 生成的文件: dist\verdent_auto_register.exe

REM 获取文件大小
for %%A in ("dist\verdent_auto_register.exe") do (
    set size=%%~zA
    set /a sizeMB=%%~zA/1024/1024
)
echo [*] 文件大小: %sizeMB% MB

REM 复制到 Tauri 资源目录
echo.
echo [*] 复制到 Tauri 资源目录...
if not exist "Verdent_account_manger\resources" mkdir "Verdent_account_manger\resources"
copy /y "dist\verdent_auto_register.exe" "Verdent_account_manger\resources\verdent_auto_register.exe"

if errorlevel 1 (
    echo [!] 警告: 复制到 Tauri 资源目录失败
) else (
    echo [✓] 已复制到: Verdent_account_manger\resources\verdent_auto_register.exe
)

echo.
echo ======================================================================
echo [✓] Python 脚本打包完成!
echo ======================================================================
echo.
echo 下一步:
echo   1. 测试 exe 文件: dist\verdent_auto_register.exe --count 1
echo   2. 运行 Tauri 打包: build_tauri.bat
echo   3. 或运行一键打包: build_all.bat
echo.
pause

