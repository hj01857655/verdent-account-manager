@echo off
chcp 65001 >nul
echo ======================================================================
echo Verdent AI 账户管理器 - 一键打包工具
echo ======================================================================
echo.
echo 此脚本将依次执行:
echo   1. Python 脚本打包 (verdent_auto_register.py → exe)
echo   2. Tauri 应用打包 (生成安装包)
echo.
echo 按任意键开始,或关闭窗口取消...
pause >nul
echo.

REM 步骤 1: 打包 Python 脚本
echo ======================================================================
echo 步骤 1/2: 打包 Python 脚本
echo ======================================================================
call build_python.bat
if errorlevel 1 (
    echo.
    echo [×] Python 打包失败,终止流程
    pause
    exit /b 1
)

echo.
echo.

REM 步骤 2: 打包 Tauri 应用
echo ======================================================================
echo 步骤 2/2: 打包 Tauri 应用
echo ======================================================================
call build_tauri.bat
if errorlevel 1 (
    echo.
    echo [×] Tauri 打包失败
    pause
    exit /b 1
)

echo.
echo.
echo ======================================================================
echo [✓] 所有打包任务完成!
echo ======================================================================
echo.
echo 生成的文件:
echo   1. Python exe: Verdent_account_manger\resources\verdent_auto_register.exe
echo   2. Tauri 安装包: Verdent_account_manger\src-tauri\target\release\bundle\
echo.
echo 下一步:
echo   - 在没有 Python 环境的机器上测试安装包
echo   - 验证自动注册功能是否正常工作
echo.
pause

