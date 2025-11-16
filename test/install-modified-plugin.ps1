# Verdent 修改版插件自动安装脚本
# 用途: 自动替换现有 Verdent 插件文件,添加 logout 命令支持

param(
    [switch]$Backup = $true,
    [switch]$Reload = $true
)

$ErrorActionPreference = "Stop"

function Write-ColorOutput {
    param(
        [ConsoleColor]$ForegroundColor,
        [string]$Message
    )
    $originalColor = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    Write-Output $Message
    $host.UI.RawUI.ForegroundColor = $originalColor
}

Write-ColorOutput Cyan "======================================================================"
Write-ColorOutput Cyan "  Verdent 修改版插件安装脚本"
Write-ColorOutput Cyan "======================================================================"
Write-Output ""

# 1. 检查 VS Code
Write-ColorOutput Cyan "[1/5] 检查 VS Code..."
try {
    $codeVersion = & code --version 2>&1 | Select-Object -First 1
    Write-ColorOutput Green "  ✓ VS Code 版本: $codeVersion"
} catch {
    Write-ColorOutput Red "  ✗ 未找到 VS Code"
    exit 1
}

# 2. 查找已安装的 Verdent 插件
Write-Output ""
Write-ColorOutput Cyan "[2/5] 查找已安装的 Verdent 插件..."

$extensionPath = $null
$possiblePaths = @(
    "$env:USERPROFILE\.vscode\extensions\verdentai.verdent-1.0.9",
    "$env:USERPROFILE\.vscode-insiders\extensions\verdentai.verdent-1.0.9"
)

foreach ($path in $possiblePaths) {
    if (Test-Path $path) {
        $extensionPath = $path
        break
    }
}

if (-not $extensionPath) {
    Write-ColorOutput Yellow "  ⚠ 未找到已安装的 Verdent 插件"
    Write-ColorOutput Yellow "  请先通过 VS Code 安装 Verdent 插件"
    exit 1
}

Write-ColorOutput Green "  ✓ 找到插件: $extensionPath"

# 3. 备份原文件
if ($Backup) {
    Write-Output ""
    Write-ColorOutput Cyan "[3/5] 备份原文件..."
    
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupDir = "$extensionPath\.backup.$timestamp"
    
    try {
        New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
        
        Copy-Item "$extensionPath\dist\extension.js" "$backupDir\extension.js" -Force
        Copy-Item "$extensionPath\package.json" "$backupDir\package.json" -Force
        
        Write-ColorOutput Green "  ✓ 备份已保存: $backupDir"
    } catch {
        Write-ColorOutput Red "  ✗ 备份失败: $_"
        
        $continue = Read-Host "是否继续安装? (y/N)"
        if ($continue -ne "y" -and $continue -ne "Y") {
            Write-ColorOutput Yellow "安装已取消"
            exit 1
        }
    }
} else {
    Write-Output ""
    Write-ColorOutput Yellow "[3/5] 跳过备份 (使用 -Backup 参数启用)"
}

# 4. 替换文件
Write-Output ""
Write-ColorOutput Cyan "[4/5] 替换修改后的文件..."

$sourceDir = "f:\Trace\TEST\Verdent\verdentai.verdent-1.0.9\extension"

if (-not (Test-Path $sourceDir)) {
    Write-ColorOutput Red "  ✗ 未找到源文件目录: $sourceDir"
    exit 1
}

try {
    # 替换 extension.js
    Copy-Item "$sourceDir\dist\extension.js" "$extensionPath\dist\extension.js" -Force
    Write-ColorOutput Green "  ✓ 已替换: dist\extension.js"
    
    # 替换 package.json
    Copy-Item "$sourceDir\package.json" "$extensionPath\package.json" -Force
    Write-ColorOutput Green "  ✓ 已替换: package.json"
    
} catch {
    Write-ColorOutput Red "  ✗ 文件替换失败: $_"
    
    if ($Backup -and $backupDir) {
        Write-ColorOutput Yellow "  正在恢复备份..."
        Copy-Item "$backupDir\extension.js" "$extensionPath\dist\extension.js" -Force
        Copy-Item "$backupDir\package.json" "$extensionPath\package.json" -Force
        Write-ColorOutput Green "  ✓ 已恢复原文件"
    }
    
    exit 1
}

# 5. 重载 VS Code
if ($Reload) {
    Write-Output ""
    Write-ColorOutput Cyan "[5/5] 重载 VS Code..."
    
    try {
        & code --command "workbench.action.reloadWindow"
        Start-Sleep -Seconds 2
        Write-ColorOutput Green "  ✓ VS Code 已重载"
    } catch {
        Write-ColorOutput Yellow "  ⚠ 自动重载失败,请手动重载 (Ctrl+R)"
    }
} else {
    Write-Output ""
    Write-ColorOutput Yellow "[5/5] 跳过重载 (使用 -Reload 参数启用)"
}

# 完成
Write-Output ""
Write-ColorOutput Cyan "======================================================================"
Write-ColorOutput Green "✓ 安装完成!"
Write-ColorOutput Cyan "======================================================================"
Write-Output ""
Write-ColorOutput White "现在可以使用以下方式退出 Verdent:"
Write-Output ""
Write-ColorOutput Gray "  1. 命令面板: Ctrl+Shift+P > Verdent: Logout"
Write-ColorOutput Gray "  2. 命令行: code --command verdent.logout"
Write-ColorOutput Gray "  3. Python API: VerdentAPI().logout()"
Write-Output ""

if (-not $Reload) {
    Write-ColorOutput Yellow "⚠ 请重载 VS Code 窗口以应用更改 (Ctrl+R)"
}
