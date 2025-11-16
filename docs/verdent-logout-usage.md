# Verdent 退出工具使用指南

## 📦 工具清单

| 工具 | 平台 | 描述 |
|------|------|------|
| `verdent-logout.ps1` | Windows | PowerShell 脚本 |
| `verdent-logout.sh` | Linux/macOS | Bash 脚本 |
| `verdent_logout.py` | 跨平台 | Python 脚本 (推荐) |

---

## 🚀 快速开始

### Windows (PowerShell)

```powershell
# 基本用法
.\verdent-logout.ps1

# 自动重载 VS Code
.\verdent-logout.ps1 -AutoReload

# 不创建备份
.\verdent-logout.ps1 -Backup:$false

# 详细模式
.\verdent-logout.ps1 -Verbose
```

### Linux/macOS (Bash)

```bash
# 赋予执行权限
chmod +x verdent-logout.sh

# 基本用法
./verdent-logout.sh

# 自动重载 VS Code
./verdent-logout.sh --auto-reload

# 强制退出 (跳过确认)
./verdent-logout.sh --force

# 组合选项
./verdent-logout.sh -f -r -v
```

### Python (跨平台)

```bash
# 命令行方式
python verdent_logout.py

# 自动重载
python verdent_logout.py --auto-reload

# 强制退出
python verdent_logout.py --force

# 查看帮助
python verdent_logout.py --help
```

---

## 📖 参数说明

### PowerShell 参数

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `-AutoReload` | Switch | `$false` | 自动重载 VS Code |
| `-Backup` | Switch | `$true` | 创建备份 |
| `-Verbose` | Switch | `$false` | 显示详细信息 |

### Bash/Python 参数

| 参数 | 别名 | 描述 |
|------|------|------|
| `--auto-reload` | `-r` | 自动重载 VS Code |
| `--no-backup` | `-n` | 不创建备份 |
| `--force` | `-f` | 强制执行,跳过确认 |
| `--verbose` | `-v` | 显示详细信息 |
| `--help` | `-h` | 显示帮助信息 |

---

## 💻 代码集成示例

### Python API 调用

```python
from verdent_logout import VerdentLogoutManager

# 创建管理器
manager = VerdentLogoutManager(verbose=True)

# 执行退出
success = manager.logout(
    auto_reload=True,   # 自动重载 VS Code
    backup=True,        # 创建备份
    force=True          # 跳过确认
)

if success:
    print("退出成功")
else:
    print("退出失败")
```

### Node.js 调用

```javascript
const { exec } = require('child_process');
const util = require('util');
const execPromise = util.promisify(exec);

async function logoutVerdent() {
    try {
        // 方式 1: 调用 Python 脚本
        const { stdout } = await execPromise('python verdent_logout.py --force');
        console.log(stdout);
        
        // 方式 2: 调用 PowerShell 脚本 (Windows)
        // const { stdout } = await execPromise('powershell -File verdent-logout.ps1 -AutoReload');
        
        return true;
    } catch (error) {
        console.error('退出失败:', error.message);
        return false;
    }
}

// 使用
logoutVerdent().then(success => {
    console.log(success ? '✓ 成功' : '✗ 失败');
});
```

### C# 调用

```csharp
using System;
using System.Diagnostics;
using System.Threading.Tasks;

public class VerdentAPI
{
    public static async Task<bool> LogoutAsync(bool autoReload = false)
    {
        try
        {
            var psi = new ProcessStartInfo
            {
                FileName = "powershell.exe",
                Arguments = $"-File verdent-logout.ps1 {(autoReload ? "-AutoReload" : "")}",
                RedirectStandardOutput = true,
                UseShellExecute = false,
                CreateNoWindow = true
            };
            
            using (var process = Process.Start(psi))
            {
                string output = await process.StandardOutput.ReadToEndAsync();
                await process.WaitForExitAsync();
                
                Console.WriteLine(output);
                return process.ExitCode == 0;
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"退出失败: {ex.Message}");
            return false;
        }
    }
}

// 使用
var success = await VerdentAPI.LogoutAsync(autoReload: true);
```

### Java 调用

```java
import java.io.BufferedReader;
import java.io.InputStreamReader;

public class VerdentAPI {
    public static boolean logout(boolean autoReload) {
        try {
            String command = System.getProperty("os.name").toLowerCase().contains("win")
                ? "powershell -File verdent-logout.ps1" + (autoReload ? " -AutoReload" : "")
                : "./verdent-logout.sh" + (autoReload ? " --auto-reload" : "");
            
            Process process = Runtime.getRuntime().exec(command);
            
            BufferedReader reader = new BufferedReader(
                new InputStreamReader(process.getInputStream())
            );
            
            String line;
            while ((line = reader.readLine()) != null) {
                System.out.println(line);
            }
            
            int exitCode = process.waitFor();
            return exitCode == 0;
            
        } catch (Exception e) {
            System.err.println("退出失败: " + e.getMessage());
            return false;
        }
    }
    
    public static void main(String[] args) {
        boolean success = logout(true);
        System.out.println(success ? "✓ 成功" : "✗ 失败");
    }
}
```

### Go 调用

```go
package main

import (
    "fmt"
    "os/exec"
    "runtime"
)

// LogoutVerdent 执行 Verdent 退出操作
func LogoutVerdent(autoReload bool) (bool, error) {
    var cmd *exec.Cmd
    
    if runtime.GOOS == "windows" {
        args := "-File verdent-logout.ps1"
        if autoReload {
            args += " -AutoReload"
        }
        cmd = exec.Command("powershell", args)
    } else {
        args := []string{"./verdent-logout.sh"}
        if autoReload {
            args = append(args, "--auto-reload")
        }
        cmd = exec.Command("bash", args...)
    }
    
    output, err := cmd.CombinedOutput()
    fmt.Println(string(output))
    
    if err != nil {
        return false, err
    }
    
    return true, nil
}

func main() {
    success, err := LogoutVerdent(true)
    
    if err != nil {
        fmt.Printf("✗ 退出失败: %v\n", err)
    } else if success {
        fmt.Println("✓ 退出成功")
    }
}
```

---

## 🔧 高级用法

### 1. 批量退出多个 VS Code 实例

```powershell
# Windows
Get-Process code | ForEach-Object {
    .\verdent-logout.ps1 -Backup:$false
    Start-Sleep -Seconds 1
}
```

```bash
# Linux/macOS
for pid in $(pgrep -f "code"); do
    ./verdent-logout.sh --no-backup --force
    sleep 1
done
```

### 2. 定时任务自动退出

**Windows 任务计划程序**:

```powershell
# 创建每天凌晨 2 点自动退出的任务
$action = New-ScheduledTaskAction -Execute 'powershell.exe' `
    -Argument '-File "f:\Trace\TEST\Verdent\test\verdent-logout.ps1" -AutoReload'

$trigger = New-ScheduledTaskTrigger -Daily -At 2am

Register-ScheduledTask -Action $action -Trigger $trigger `
    -TaskName "VerdentAutoLogout" -Description "自动退出 Verdent"
```

**Linux Cron**:

```bash
# 编辑 crontab
crontab -e

# 添加每天凌晨 2 点执行
0 2 * * * /path/to/verdent-logout.sh --force --auto-reload
```

### 3. 退出前自动备份工作区

```powershell
# 备份脚本
$workspaceBackupPath = "D:\Backups\Verdent\$(Get-Date -Format 'yyyyMMdd')"
New-Item -ItemType Directory -Path $workspaceBackupPath -Force

# 备份工作区文件
Copy-Item -Path "$env:USERPROFILE\workspace" -Destination $workspaceBackupPath -Recurse

# 执行退出
.\verdent-logout.ps1 -AutoReload
```

### 4. 退出后清理缓存

```python
import os
import shutil
from pathlib import Path
from verdent_logout import VerdentLogoutManager

def full_cleanup():
    """完整清理 Verdent 数据"""
    manager = VerdentLogoutManager(verbose=True)
    
    # 退出登录
    if not manager.logout(backup=True, force=True):
        return False
    
    # 清理缓存
    if manager.storage_path:
        cache_dirs = [
            manager.storage_path / "cache",
            manager.storage_path / "logs",
            manager.storage_path / "temp"
        ]
        
        for cache_dir in cache_dirs:
            if cache_dir.exists():
                shutil.rmtree(cache_dir)
                print(f"✓ 已清理: {cache_dir}")
    
    return True

if __name__ == "__main__":
    full_cleanup()
```

---

## 🛡️ 安全建议

### 1. 备份验证

```powershell
# 验证备份完整性
function Test-VerdentBackup {
    param([string]$BackupPath)
    
    $requiredFiles = @(
        "verdentApiKey",
        "userInfo",
        "ycAuthToken"
    )
    
    foreach ($file in $requiredFiles) {
        $path = Join-Path $BackupPath $file
        if (-not (Test-Path $path)) {
            Write-Warning "备份不完整: 缺少 $file"
            return $false
        }
    }
    
    Write-Host "✓ 备份验证通过" -ForegroundColor Green
    return $true
}
```

### 2. 加密敏感备份

```python
import shutil
import zipfile
from pathlib import Path
from cryptography.fernet import Fernet

def create_encrypted_backup(storage_path: Path, password: str):
    """创建加密备份"""
    # 创建临时 ZIP
    zip_path = Path(f"{storage_path}.backup.zip")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in storage_path.iterdir():
            zipf.write(file, file.name)
    
    # 加密 ZIP
    key = Fernet.generate_key()  # 实际应从密码派生
    cipher = Fernet(key)
    
    with open(zip_path, 'rb') as f:
        encrypted = cipher.encrypt(f.read())
    
    encrypted_path = Path(f"{storage_path}.backup.encrypted")
    with open(encrypted_path, 'wb') as f:
        f.write(encrypted)
    
    # 删除临时文件
    zip_path.unlink()
    
    print(f"✓ 加密备份已创建: {encrypted_path}")
    return encrypted_path
```

### 3. 退出日志记录

```python
import logging
from datetime import datetime
from verdent_logout import VerdentLogoutManager

# 配置日志
logging.basicConfig(
    filename='verdent_logout.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def logged_logout():
    """带日志记录的退出"""
    manager = VerdentLogoutManager(verbose=True)
    
    logging.info("开始退出操作")
    
    try:
        success = manager.logout(
            auto_reload=True,
            backup=True,
            force=False
        )
        
        if success:
            logging.info("退出成功")
        else:
            logging.warning("退出部分完成或失败")
            
        return success
        
    except Exception as e:
        logging.error(f"退出过程发生异常: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    logged_logout()
```

---

## 📊 故障排除

### 问题 1: 找不到存储目录

**原因**: Verdent 未安装或从未登录

**解决方案**:
```bash
# 手动查找
# Windows
dir %APPDATA%\Code\User\globalStorage /s /b | findstr verdent

# Linux/macOS
find ~ -path "*/globalStorage/verdentai.verdent" 2>/dev/null
```

### 问题 2: 权限不足

**原因**: 文件被锁定或权限不足

**解决方案**:
```powershell
# Windows - 以管理员身份运行
Start-Process powershell -Verb RunAs -ArgumentList "-File verdent-logout.ps1"
```

```bash
# Linux/macOS - 使用 sudo
sudo ./verdent-logout.sh --force
```

### 问题 3: VS Code 未响应重载

**原因**: VS Code 进程繁忙或崩溃

**解决方案**:
```powershell
# 强制重启 VS Code
Get-Process code | Stop-Process -Force
Start-Process code
```

### 问题 4: 备份失败

**原因**: 磁盘空间不足或路径过长

**解决方案**:
```powershell
# 检查磁盘空间
Get-PSDrive C | Select-Object Used,Free

# 使用短路径
.\verdent-logout.ps1 -Backup:$false
```

---

## 📞 技术支持

如遇问题,请提供以下信息:

1. **操作系统**: Windows/Linux/macOS 版本
2. **VS Code 版本**: 运行 `code --version`
3. **Verdent 版本**: 检查插件版本
4. **错误日志**: 脚本输出的完整错误信息
5. **存储路径**: 手动检查是否存在

**联系方式**:
- GitHub Issues: [项目仓库地址]
- Email: support@verdent.ai
- 文档: 参考 `verdent-logout-analysis.md`

---

## 📝 更新日志

### v1.0.0 (2025-11-14)
- ✅ 初始版本发布
- ✅ 支持 Windows/Linux/macOS
- ✅ 提供 PowerShell/Bash/Python 三种实现
- ✅ 自动备份功能
- ✅ 自动重载 VS Code
- ✅ 详细日志输出

---

## 📄 许可证

本工具遵循 Apache 2.0 许可证,与 Verdent 插件保持一致。
