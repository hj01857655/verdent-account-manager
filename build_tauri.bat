@echo off
chcp 65001 >nul
echo ======================================================================
echo Verdent AI 账户管理器 - Tauri 打包工具
echo ======================================================================
echo.

REM 检查 Node.js 是否安装
node --version >nul 2>&1
if errorlevel 1 (
    echo [×] 错误: 未找到 Node.js 环境
    echo [*] 请先安装 Node.js
    pause
    exit /b 1
)
echo [✓] Node.js 环境检测成功
echo.

REM 检查 Rust 是否安装
rustc --version >nul 2>&1
if errorlevel 1 (
    echo [×] 错误: 未找到 Rust 环境
    echo [*] 请先安装 Rust (https://rustup.rs/)
    pause
    exit /b 1
)
echo [✓] Rust 环境检测成功
echo.

REM 检查 Python 打包的 exe 文件是否存在
if not exist "Verdent_account_manger\resources\verdent_auto_register.exe" (
    echo [!] 警告: 未找到 Python 打包的 exe 文件
    echo [*] 位置: Verdent_account_manger\resources\verdent_auto_register.exe
    echo.
    echo [?] 是否先运行 Python 打包? (Y/N)
    choice /c YN /n
    if errorlevel 2 (
        echo [*] 跳过 Python 打包,继续 Tauri 打包...
    ) else (
        echo [*] 运行 Python 打包脚本...
        call build_python.bat
        if errorlevel 1 (
            echo [×] Python 打包失败
            pause
            exit /b 1
        )
    )
)
echo [✓] Python exe 文件已就绪
echo.

REM 进入 Tauri 项目目录
cd Verdent_account_manger

REM 检查 node_modules 是否存在
if not exist "node_modules" (
    echo [*] 安装 npm 依赖...
    call npm install
    if errorlevel 1 (
        echo [×] npm 依赖安装失败
        cd ..
        pause
        exit /b 1
    )
)
echo [✓] npm 依赖已就绪
echo.

REM 执行 Tauri 打包
echo [*] 开始 Tauri 打包...
echo [*] 这可能需要几分钟时间,请耐心等待...
echo.
call npm run tauri build

if errorlevel 1 (
    echo.
    echo [×] Tauri 打包失败!
    cd ..
    pause
    exit /b 1
)

cd ..

echo.
echo ======================================================================
echo [✓] Tauri 打包完成!
echo ======================================================================
echo.
echo 生成的安装包位置:
echo   - MSI 安装包: Verdent_account_manger\src-tauri\target\release\bundle\msi\
echo   - NSIS 安装包: Verdent_account_manger\src-tauri\target\release\bundle\nsis\
echo   - 可执行文件: Verdent_account_manger\src-tauri\target\release\verdent-account-manager.exe
echo.
pause

