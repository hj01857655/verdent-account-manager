# GitHub Actions 跨平台打包环境设置脚本
# 编码: UTF-8

$ErrorActionPreference = "Stop"

function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-Host "======================================================================" -ForegroundColor Cyan
    Write-Host $Text -ForegroundColor Cyan
    Write-Host "======================================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Success {
    param([string]$Text)
    Write-Host "[✓] $Text" -ForegroundColor Green
}

function Write-Info {
    param([string]$Text)
    Write-Host "[*] $Text" -ForegroundColor Yellow
}

function Write-Error-Custom {
    param([string]$Text)
    Write-Host "[×] $Text" -ForegroundColor Red
}

Write-Header "GitHub Actions 跨平台打包环境设置"

# 1. 检查图标文件
Write-Info "检查图标文件..."
$iconsDir = "Verdent_account_manger\src-tauri\icons"

$requiredIcons = @(
    "32x32.png",
    "128x128.png",
    "128x128@2x.png",
    "icon.icns",
    "icon.ico"
)

$iconFiles = Get-ChildItem -Path $iconsDir -File
Write-Info "当前图标文件:"
$iconFiles | ForEach-Object { Write-Host "  - $($_.Name)" }

# 重命名错误的图标文件名
Write-Info "修正图标文件名..."
if (Test-Path "$iconsDir\128×128.png") {
    Rename-Item "$iconsDir\128×128.png" -NewName "128x128.png" -Force
    Write-Success "已重命名: 128×128.png -> 128x128.png"
}

if (Test-Path "$iconsDir\128×128.2x.png") {
    Rename-Item "$iconsDir\128×128.2x.png" -NewName "128x128@2x.png" -Force
    Write-Success "已重命名: 128×128.2x.png -> 128x128@2x.png"
}

if (Test-Path "$iconsDir\32×32.png") {
    Rename-Item "$iconsDir\32×32.png" -NewName "32x32.png" -Force
    Write-Success "已重命名: 32×32.png -> 32x32.png"
}

# 2. 检查必需文件
Write-Info "检查必需文件..."
$missingIcons = @()
foreach ($icon in $requiredIcons) {
    if (-not (Test-Path "$iconsDir\$icon")) {
        $missingIcons += $icon
    }
}

if ($missingIcons.Count -gt 0) {
    Write-Error-Custom "缺少以下图标文件:"
    $missingIcons | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
    Write-Host ""
    Write-Host "请运行 Tauri 图标生成命令:" -ForegroundColor Yellow
    Write-Host "  cd Verdent_account_manger" -ForegroundColor Cyan
    Write-Host "  npm run tauri icon path/to/your/icon.png" -ForegroundColor Cyan
} else {
    Write-Success "所有必需的图标文件都存在"
}

# 3. 检查 Git 配置
Write-Info "检查 Git 配置..."
try {
    $gitRemote = git remote get-url origin 2>$null
    if ($gitRemote) {
        Write-Success "Git 远程仓库: $gitRemote"
    } else {
        Write-Error-Custom "未配置 Git 远程仓库"
        Write-Host "请运行:" -ForegroundColor Yellow
        Write-Host "  git remote add origin https://github.com/用户名/仓库名.git" -ForegroundColor Cyan
    }
} catch {
    Write-Error-Custom "Git 未初始化或未安装"
}

# 4. 验证配置文件
Write-Info "验证配置文件..."
if (Test-Path ".github\workflows\build.yml") {
    Write-Success "GitHub Actions 工作流配置存在"
} else {
    Write-Error-Custom "缺少 .github\workflows\build.yml"
}

if (Test-Path "Verdent_account_manger\src-tauri\tauri.conf.json") {
    Write-Success "Tauri 配置文件存在"
    
    # 检查配置是否正确
    $config = Get-Content "Verdent_account_manger\src-tauri\tauri.conf.json" -Raw | ConvertFrom-Json
    if ($config.bundle.targets -eq "all") {
        Write-Success "Tauri 配置支持所有平台"
    } else {
        Write-Info "Tauri 配置: $($config.bundle.targets)"
    }
} else {
    Write-Error-Custom "缺少 tauri.conf.json"
}

# 5. 显示下一步操作
Write-Header "下一步操作"
Write-Host "1. 确保所有更改已提交到 Git:" -ForegroundColor Green
Write-Host "   git add ." -ForegroundColor Cyan
Write-Host "   git commit -m 'Setup GitHub Actions for cross-platform builds'" -ForegroundColor Cyan
Write-Host ""

Write-Host "2. 推送代码到 GitHub:" -ForegroundColor Green
Write-Host "   git push origin main" -ForegroundColor Cyan
Write-Host ""

Write-Host "3. 创建并推送版本标签以触发构建:" -ForegroundColor Green
Write-Host "   git tag v1.0.0" -ForegroundColor Cyan
Write-Host "   git push origin v1.0.0" -ForegroundColor Cyan
Write-Host ""

Write-Host "4. 或者在 GitHub 上手动触发构建:" -ForegroundColor Green
Write-Host "   - 访问仓库的 Actions 标签" -ForegroundColor Cyan
Write-Host "   - 选择 'Build and Release' 工作流" -ForegroundColor Cyan
Write-Host "   - 点击 'Run workflow' 按钮" -ForegroundColor Cyan
Write-Host ""

Write-Host "5. 查看详细文档:" -ForegroundColor Green
Write-Host "   docs\GitHub_Actions_跨平台打包指南.md" -ForegroundColor Cyan
Write-Host ""

Write-Success "设置检查完成!"
