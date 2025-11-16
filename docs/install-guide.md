# Verdent 修改版插件安装和使用指南

## 📦 修改内容

### 1. 添加的命令

在插件中添加了 `verdent.logout` 命令,可以通过外部程序调用实现一键退出。

**修改文件**:
- `extension/dist/extension.js` (行 635980 后)
- `extension/package.json` (commands 部分)

### 2. 实现原理

```javascript
// 注册命令
oi.commands.registerCommand("verdent.logout", async () => {
  try {
    let controller = Pr.getSidebarInstance()?.controller;
    if (!controller) {
      oi.window.showWarningMessage("Verdent is not initialized yet");
      return;
    }
    
    // 调用内部退出方法
    await controller.handleSignOut();
    
    oi.window.showInformationMessage("Successfully logged out of Verdent");
  } catch (error) {
    oi.window.showErrorMessage("Logout failed: " + error.message);
  }
});
```

## 🚀 安装步骤

### 方法 1: 直接安装修改后的插件 (推荐)

由于插件已经是解压后的状态,需要重新打包:

```powershell
# 进入插件目录
cd "f:\Trace\TEST\Verdent\verdentai.verdent-1.0.9\extension"

# 安装 vsce (如果没有)
npm install -g @vscode/vsce

# 打包插件
vsce package

# 安装到 VS Code
code --install-extension verdent-1.0.9.vsix
```

### 方法 2: 手动替换现有插件文件

```powershell
# 找到已安装的 Verdent 插件目录
$extensionPath = "$env:USERPROFILE\.vscode\extensions\verdentai.verdent-1.0.9"

# 备份原文件
Copy-Item "$extensionPath\dist\extension.js" "$extensionPath\dist\extension.js.bak"
Copy-Item "$extensionPath\package.json" "$extensionPath\package.json.bak"

# 替换修改后的文件
Copy-Item "f:\Trace\TEST\Verdent\verdentai.verdent-1.0.9\extension\dist\extension.js" "$extensionPath\dist\extension.js" -Force
Copy-Item "f:\Trace\TEST\Verdent\verdentai.verdent-1.0.9\extension\package.json" "$extensionPath\package.json" -Force

# 重载 VS Code
code --command "workbench.action.reloadWindow"
```

## 💻 使用方法

### 1. 通过命令面板

1. 打开 VS Code
2. 按 `Ctrl+Shift+P` (或 `Cmd+Shift+P` on Mac)
3. 输入 `Verdent: Logout`
4. 按 Enter 执行

### 2. 通过外部脚本调用

#### Python API

```python
from verdent_api import VerdentAPI

# 创建 API 实例
api = VerdentAPI()

# 执行退出
success = api.logout()

if success:
    print("✓ 退出成功")
else:
    print("✗ 退出失败")
```

#### 命令行直接调用

```bash
# Windows PowerShell
code --command verdent.logout

# Linux/macOS
code --command verdent.logout
```

#### Node.js

```javascript
const { exec } = require('child_process');

exec('code --command verdent.logout', (error, stdout, stderr) => {
    if (error) {
        console.error(`退出失败: ${error}`);
        return;
    }
    console.log('✓ 退出成功');
});
```

#### C#

```csharp
using System.Diagnostics;

var psi = new ProcessStartInfo
{
    FileName = "code",
    Arguments = "--command verdent.logout",
    UseShellExecute = false
};

using (var process = Process.Start(psi))
{
    process.WaitForExit();
    
    if (process.ExitCode == 0)
        Console.WriteLine("✓ 退出成功");
    else
        Console.WriteLine("✗ 退出失败");
}
```

## 🧪 测试

运行测试脚本验证功能:

```bash
python f:\Trace\TEST\Verdent\test\test_logout_command.py
```

**预期输出**:

```
======================================================================
测试 Verdent Logout 命令
======================================================================

[1/3] 检查 VS Code...
  ✓ VS Code 版本: 1.95.0

[2/3] 执行 verdent.logout 命令...
  ✓ 命令执行成功

[3/3] 验证退出状态...
  ⏳ 等待 2 秒...
  ℹ 请检查 VS Code 窗口:
    - Verdent 侧边栏应显示登录界面
    - 用户信息应已清空

======================================================================
✓ 测试完成
======================================================================
```

## 🔍 验证退出效果

执行 logout 命令后,应该观察到:

1. **VS Code 通知**: 显示 "Successfully logged out of Verdent"
2. **Verdent 侧边栏**: 显示登录界面,而不是聊天界面
3. **菜单栏**: Verdent 菜单项消失 (showVerdentMenu = false)
4. **数据库清空**: state.vscdb 中的 token 和配置被删除

### 手动验证数据库

```python
import sqlite3
import os

db_path = os.path.join(
    os.environ['APPDATA'],
    r'Code\User\globalStorage\state.vscdb'
)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 查询 Verdent secrets
cursor.execute("""
    SELECT key FROM ItemTable 
    WHERE key LIKE '%verdent%ycAuthToken%'
""")

results = cursor.fetchall()

if len(results) == 0:
    print("✓ Token 已清除")
else:
    print("✗ Token 仍然存在")

conn.close()
```

## 📊 对比:修改前 vs 修改后

| 功能 | 修改前 | 修改后 |
|------|--------|--------|
| **命令面板可见** | ❌ 无 logout 命令 | ✅ 有 `Verdent: Logout` |
| **外部调用** | ❌ 无法调用 | ✅ `code --command verdent.logout` |
| **退出效果** | ⚠️ 删除文件需重启 | ✅ 立即生效 |
| **用户体验** | ⚠️ 需要手动操作 | ✅ 一键退出 |
| **API 集成** | ❌ 无法集成 | ✅ 完全支持 |

## 🛠️ 故障排除

### 问题 1: 命令不存在

**症状**: 执行 `code --command verdent.logout` 提示命令未找到

**解决**:
1. 检查插件是否安装: `code --list-extensions | findstr verdent`
2. 重新加载窗口: `code --command workbench.action.reloadWindow`
3. 检查 package.json 是否包含命令定义

### 问题 2: 执行后仍然登录

**症状**: 执行命令后侧边栏仍显示聊天界面

**原因**: Controller 未初始化或实例获取失败

**解决**:
1. 打开 Verdent 侧边栏确保插件已激活
2. 查看 VS Code 开发者控制台 (Help > Toggle Developer Tools)
3. 检查错误日志

### 问题 3: 权限错误

**症状**: 修改文件时提示权限不足

**解决**:
```powershell
# 以管理员身份运行 PowerShell
Start-Process powershell -Verb RunAs

# 然后执行替换命令
```

## 🔐 安全说明

1. **不影响原有功能**: 仅添加新命令,不修改现有逻辑
2. **安全退出**: 调用官方 `handleSignOut()` 方法,与手动退出完全一致
3. **数据清理**: 清除所有敏感信息 (token, userInfo, apiKey)
4. **日志记录**: 记录退出操作到日志,便于审计

## 📞 技术支持

如遇问题,请提供:

1. VS Code 版本: `code --version`
2. Verdent 插件版本: 检查扩展面板
3. 错误信息: 开发者控制台 Console 标签页
4. 操作系统: Windows 10/11

---

**修改版本**: v1.0.9-logout  
**修改日期**: 2025-11-14  
**修改内容**: 添加 verdent.logout 命令支持外部调用
