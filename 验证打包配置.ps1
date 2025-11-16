# 验证 Tauri 打包配置
# 编码: UTF-8

$ErrorActionPreference = "Stop"

function Write-Check {
    param([string]$Text, [bool]$Pass)
    if ($Pass) {
        Write-Host "[✓] $Text" -ForegroundColor Green
    } else {
        Write-Host "[×] $Text" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "Tauri 打包配置验证" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# 1. 检查图标文件
Write-Host "1. 检查图标文件" -ForegroundColor Yellow
$iconExists = Test-Path "Verdent_account_manger\src-tauri\icons\icon.ico"
Write-Check "图标文件存在: Verdent_account_manger\src-tauri\icons\icon.ico" $iconExists

# 2. 检查 Python exe
Write-Host ""
Write-Host "2. 检查 Python 可执行文件" -ForegroundColor Yellow
$pythonExeExists = Test-Path "Verdent_account_manger\resources\verdent_auto_register.exe"
Write-Check "Python exe 存在: Verdent_account_manger\resources\verdent_auto_register.exe" $pythonExeExists

if ($pythonExeExists) {
    $exeSize = (Get-Item "Verdent_account_manger\resources\verdent_auto_register.exe").Length / 1MB
    Write-Host "    文件大小: $([math]::Round($exeSize, 2)) MB" -ForegroundColor Gray
}

# 3. 检查 tauri.conf.json
Write-Host ""
Write-Host "3. 检查 Tauri 配置文件" -ForegroundColor Yellow
$configExists = Test-Path "Verdent_account_manger\src-tauri\tauri.conf.json"
Write-Check "配置文件存在: Verdent_account_manger\src-tauri\tauri.conf.json" $configExists

if ($configExists) {
    $config = Get-Content "Verdent_account_manger\src-tauri\tauri.conf.json" -Raw | ConvertFrom-Json
    
    # 检查 bundle.active
    $bundleActive = $config.bundle.active
    Write-Check "bundle.active = true" $bundleActive
    
    # 检查 icon 配置
    $hasIcon = $config.bundle.icon.Count -gt 0
    Write-Check "bundle.icon 已配置" $hasIcon
    if ($hasIcon) {
        Write-Host "    图标路径: $($config.bundle.icon -join ', ')" -ForegroundColor Gray
    }
    
    # 检查 resources 配置
    $hasResources = $config.bundle.resources.Count -gt 0
    Write-Check "bundle.resources 已配置" $hasResources
    if ($hasResources) {
        Write-Host "    资源路径: $($config.bundle.resources -join ', ')" -ForegroundColor Gray
    }
}

# 4. 检查前端构建
Write-Host ""
Write-Host "4. 检查前端构建" -ForegroundColor Yellow
$distExists = Test-Path "Verdent_account_manger\dist"
Write-Check "前端构建目录存在: Verdent_account_manger\dist" $distExists

# 5. 检查 Rust 编译
Write-Host ""
Write-Host "5. 检查 Rust 编译" -ForegroundColor Yellow
Write-Host "    运行 cargo check..." -ForegroundColor Gray
Set-Location "Verdent_account_manger\src-tauri"
$cargoCheck = cargo check 2>&1
$cargoSuccess = $?
Set-Location "..\..\"
Write-Check "Rust 编译检查通过" $cargoSuccess

# 总结
Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "验证总结" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

$allChecks = $iconExists -and $pythonExeExists -and $configExists -and $bundleActive -and $hasIcon -and $cargoSuccess

if ($allChecks) {
    Write-Host ""
    Write-Host "[✓] 所有检查通过,可以开始打包!" -ForegroundColor Green
    Write-Host ""
    Write-Host "运行以下命令开始打包:" -ForegroundColor Cyan
    Write-Host "    .\build_tauri.ps1" -ForegroundColor Yellow
    Write-Host "或:" -ForegroundColor Cyan
    Write-Host "    cd Verdent_account_manger" -ForegroundColor Yellow
    Write-Host "    npm run tauri build" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "[×] 存在配置问题,请先修复上述错误" -ForegroundColor Red
    
    if (-not $pythonExeExists) {
        Write-Host ""
        Write-Host "修复建议:" -ForegroundColor Yellow
        Write-Host "    运行 .\build_python.ps1 打包 Python 脚本" -ForegroundColor Gray
    }
}

Write-Host ""
Read-Host "按 Enter 键退出"

