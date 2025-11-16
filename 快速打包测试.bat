@echo off
chcp 65001 >nul
echo ======================================================================
echo Verdent AI 账户管理器 - 快速打包测试
echo ======================================================================
echo.

echo [*] 步骤 1: 检查 Rust 编译
echo ======================================================================
cd Verdent_account_manger\src-tauri
cargo check
if errorlevel 1 (
    echo [×] Rust 编译检查失败
    cd ..\..
    pause
    exit /b 1
)
echo [✓] Rust 编译检查通过
cd ..\..
echo.

echo [*] 步骤 2: 检查前端构建
echo ======================================================================
cd Verdent_account_manger
call npm run build
if errorlevel 1 (
    echo [×] 前端构建失败
    cd ..
    pause
    exit /b 1
)
echo [✓] 前端构建成功
cd ..
echo.

echo [*] 步骤 3: 开始 Tauri 打包
echo ======================================================================
echo [!] 这可能需要几分钟时间,请耐心等待...
echo.
cd Verdent_account_manger
call npm run tauri build
if errorlevel 1 (
    echo.
    echo [×] Tauri 打包失败
    cd ..
    pause
    exit /b 1
)
cd ..
echo.

echo ======================================================================
echo [✓] 打包成功!
echo ======================================================================
echo.
echo 生成的文件位置:
echo   - MSI 安装包: Verdent_account_manger\src-tauri\target\release\bundle\msi\
echo   - NSIS 安装包: Verdent_account_manger\src-tauri\target\release\bundle\nsis\
echo   - 可执行文件: Verdent_account_manger\src-tauri\target\release\verdent-account-manager.exe
echo.
pause

