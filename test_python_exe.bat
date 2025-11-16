@echo off
chcp 65001 >nul
echo ======================================================================
echo 测试 Python 打包的 exe 文件
echo ======================================================================
echo.

REM 检查 exe 文件是否存在
if not exist "dist\verdent_auto_register.exe" (
    echo [×] 错误: 未找到 dist\verdent_auto_register.exe
    echo [*] 请先运行 build_python.bat 进行打包
    pause
    exit /b 1
)

echo [✓] 找到 exe 文件: dist\verdent_auto_register.exe
echo.

REM 获取文件信息
for %%A in ("dist\verdent_auto_register.exe") do (
    set /a sizeMB=%%~zA/1024/1024
    echo [*] 文件大小: %sizeMB% MB
    echo [*] 修改时间: %%~tA
)
echo.

REM 测试 exe 文件 - 显示帮助信息
echo [*] 测试 1: 显示帮助信息
echo ======================================================================
dist\verdent_auto_register.exe
echo.
echo.

REM 测试 exe 文件 - 注册 1 个账号(使用随机密码)
echo [*] 测试 2: 注册 1 个账号(使用随机密码)
echo ======================================================================
echo [!] 此测试将实际执行注册流程,需要几分钟时间
echo [?] 是否继续? (Y/N)
choice /c YN /n
if errorlevel 2 (
    echo [*] 跳过实际注册测试
    goto :end
)

echo.
echo [*] 开始注册测试...
dist\verdent_auto_register.exe --count 1 --random-password --output test_output.json

if errorlevel 1 (
    echo.
    echo [×] 注册测试失败
) else (
    echo.
    echo [✓] 注册测试成功
    
    if exist "test_output.json" (
        echo [*] 输出文件已生成: test_output.json
        echo [*] 文件内容:
        type test_output.json
        echo.
        del /f /q test_output.json
    )
)

:end
echo.
echo ======================================================================
echo 测试完成
echo ======================================================================
pause

