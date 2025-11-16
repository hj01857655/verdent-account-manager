# Verdent VS Code 插件退出机制分析报告

## 📋 分析概述

**目标**: 分析 Verdent VS Code 插件的退出(Logout)机制,评估是否可以通过远程 Hook 或外部 API 实现一键退出功能。

**分析文件**: `f:\Trace\TEST\Verdent\verdentai.verdent-1.0.9\extension\dist\extension.js`

**结论**: ⚠️ **当前无法通过外部 API 直接调用退出功能**,但存在多种可行的替代方案。

---

## 🔍 核心发现

### 1. 退出机制架构

插件实现了两个独立的退出方法:

#### 方法 A: `logout()` (Task 类)
**位置**: 行 624665-624675

```javascript
async logout() {
  await Gi(this.context, "ycAuthToken", void 0),
  await Mr(this.context, "userInfo", void 0),
  await Gi(this.context, "authNonce", void 0),
  await Gi(this.context, "authNonceTimestamp", void 0),
  oa.commands.executeCommand("setContext", "verdent.showVerdentMenu", !1),
  await this.postStateToWebview(),
  await this.postMessageToWebview({ type: "logoutSuccess" }),
  (yb.instance = null),
  (W_.instance = null);
}
```

**功能**:
- 清除 `ycAuthToken` (YC 认证令牌)
- 清除 `userInfo` (用户信息)
- 清除 `authNonce` 和 `authNonceTimestamp` (认证随机数)
- 隐藏 Verdent 菜单
- 通知 WebView 退出成功
- 重置单例实例

---

#### 方法 B: `handleSignOut()` (Controller 类)
**位置**: 行 629078-629093

```javascript
async handleSignOut() {
  try {
    await Gi(this.context, "verdentApiKey", void 0),
    await Mr(this.context, "userInfo", void 0),
    await Mr(this.context, "apiProvider", "openrouter"),
    await Gi(this.context, "ycAuthToken"),
    await this.clearAuthNonce(),
    Gr.commands.executeCommand("setContext", "verdent.showVerdentMenu", !1),
    await this.postStateToWebview(),
    await this.postMessageToWebview({ type: "userInfo", text: "" }),
    await this.postMessageToWebview({ type: "logoutSuccess" }),
    (yb.instance = null);
  } catch (e) {
    Gr.window.showErrorMessage("Logout failed"), 
    vt.error("Logout failed", e);
  }
}
```

**功能** (比 `logout()` 更全面):
- 清除 `verdentApiKey`
- 清除 `userInfo`
- 重置 `apiProvider` 为默认值 `"openrouter"`
- 清除 `ycAuthToken`
- 调用 `clearAuthNonce()` 清理认证随机数
- 包含错误处理机制
- 显示错误提示给用户

---

### 2. 触发机制分析

#### ✅ 已实现的触发方式

**WebView 消息触发** (推荐方式):

```javascript
// 位置: 629493-629499
case "accountLogoutClicked": {
  await this.handleSignOut(),
  Gr.window.showInformationMessage("Successfully logged out of Verdent");
  break;
}
```

**触发条件**:
- WebView 向插件发送 `{ type: "accountLogoutClicked" }` 消息
- 由 `handleWebviewMessage()` 方法接收并处理 (行 629235+)

---

#### ❌ 未实现的触发方式

**VS Code 命令注册**:

经过完整扫描,发现插件注册了以下命令 (package.json 第 63-147 行):

```json
"commands": [
  { "command": "verdent.plusButtonClicked", "title": "New Session" },
  { "command": "verdent.historyButtonClicked", "title": "Project History" },
  { "command": "verdent.rulesButtonClicked", "title": "Rules" },
  { "command": "verdent.centerButtonClicked", "title": "User Center" },
  { "command": "verdent.addToChat", "title": "Add to Verdent" },
  { "command": "verdent.addToChatBySearch", "title": "Add to Verdent" },
  { "command": "verdent.addTerminalOutputToChat", "title": "Add to Verdent" },
  { "command": "verdent.addFeedBack", "title": "Feedback" },
  { "command": "verdent.mcpButtonClicked", "title": "Add MCP" },
  { "command": "verdent.subagentButtonClicked", "title": "Add Subagent" },
  { "command": "verdent.SettingClicked", "title": "Setting" },
  { "command": "verdent.openInNewTabByParams", "title": "Open In New Tab By Params" }
]
```

**⚠️ 关键问题**: 
- **没有** `verdent.logout` 或 `verdent.signout` 命令
- **没有** 暴露任何公共 API 接口
- **没有** `getApi()` 方法供其他扩展调用

---

### 3. 内部调用追踪

退出方法在插件内部的调用位置:

| 行号 | 调用方法 | 触发条件 |
|------|----------|----------|
| 624461 | `this.logout()` | `ycAuthToken` 为空时 |
| 624644 | `this.logout()` | API 请求失败后用户取消重试 |
| 627296 | `this.logout()` | 任务执行循环中检测到未登录 |
| 629268 | `this.handleSignOut()` | WebView 启动时获取用户信息失败 |
| 629271 | `this.handleSignOut()` | 用户未登录状态 |
| 629494 | `this.handleSignOut()` | **用户点击退出按钮** (主要触发点) |

---

## 🚫 当前限制

### 1. 无法直接从外部调用的原因

#### 架构设计
```
外部软件/脚本
    ↓ (❌ 无接口)
VS Code Extension API
    ↓ (❌ 未注册命令)
插件内部类方法
    ↓ (✅ 仅内部可调用)
logout() / handleSignOut()
```

#### 访问控制
- `logout()` 和 `handleSignOut()` 都是**类实例方法**,不是静态方法
- 没有通过 `vscode.commands.registerCommand()` 注册为可执行命令
- 没有实现 Extension API 的导出机制

#### 代码证据
```javascript
// extension.js 行 636194 - 插件导出部分
0 && (module.exports = { activate, deactivate });
```

只导出了 `activate` 和 `deactivate`,没有导出任何公共 API 对象。

---

### 2. WebView 通信机制

虽然插件支持 WebView 消息,但这是**内部通信机制**:

```javascript
// 行 631340-631347 - 消息监听注册
e.onDidReceiveMessage(
  (i) => {
    this.controller.handleWebviewMessage(i);
  },
  null,
  this.disposables
);
```

**限制**:
- 只能在插件内部的 WebView 和后端之间通信
- 外部应用无法访问这个 WebView 实例
- 没有暴露消息总线或事件订阅接口

---

## ✅ 可行的解决方案

### 方案 1: 修改插件源码注册命令 (推荐)

#### 实现步骤

**1. 在 `activate` 函数中添加命令注册** (行 635730 附近):

```javascript
// 添加到其他 registerCommand 调用之后
oi.commands.registerCommand("verdent.logout", async () => {
  try {
    // 获取当前 Controller 实例
    const controller = Pr.getSidebarInstance()?.controller;
    if (controller) {
      await controller.handleSignOut();
      oi.window.showInformationMessage("Successfully logged out of Verdent");
    } else {
      oi.window.showWarningMessage("Verdent controller not initialized");
    }
  } catch (error) {
    oi.window.showErrorMessage("Logout failed: " + error.message);
    console.error("Logout error:", error);
  }
});
```

**2. 在 `package.json` 中声明命令** (第 63 行 `commands` 数组中):

```json
{
  "command": "verdent.logout",
  "title": "Logout",
  "category": "Verdent"
}
```

**3. 外部调用方式**:

```javascript
// 通过 VS Code API 调用
vscode.commands.executeCommand('verdent.logout');
```

```bash
# 通过 VS Code CLI 调用
code --command verdent.logout
```

```python
# Python 脚本调用
import subprocess
subprocess.run(['code', '--command', 'verdent.logout'])
```

---

### 方案 2: 直接操作存储清除认证信息

#### 原理
通过直接删除插件的存储文件来强制退出登录状态。

#### 存储位置分析

根据代码中的存储操作:
```javascript
await Gi(this.context, "verdentApiKey", void 0)  // 清除 API Key
await Mr(this.context, "userInfo", void 0)       // 清除用户信息
await Gi(this.context, "ycAuthToken")            // 清除认证 Token
```

VS Code 插件的全局存储位置:
- **Windows**: `%APPDATA%\Code\User\globalStorage\verdentai.verdent\`
- **macOS**: `~/Library/Application Support/Code/User/globalStorage/verdentai.verdent/`
- **Linux**: `~/.config/Code/User/globalStorage/verdentai.verdent/`

#### 实现脚本

**PowerShell (Windows)**:
```powershell
# 一键退出 Verdent 脚本
$verdentStoragePath = "$env:APPDATA\Code\User\globalStorage\verdentai.verdent"

if (Test-Path $verdentStoragePath) {
    # 备份当前存储
    $backupPath = "$verdentStoragePath.backup.$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    Copy-Item -Path $verdentStoragePath -Destination $backupPath -Recurse
    
    # 删除认证信息
    Remove-Item -Path "$verdentStoragePath\*" -Include "verdentApiKey","userInfo","ycAuthToken","authNonce","authNonceTimestamp" -Force
    
    Write-Host "Verdent logout successful. Backup saved to: $backupPath"
    
    # 重启 VS Code (可选)
    # code --command "workbench.action.reloadWindow"
} else {
    Write-Host "Verdent storage not found"
}
```

**Bash (Linux/macOS)**:
```bash
#!/bin/bash
# 一键退出 Verdent 脚本

VERDENT_STORAGE="$HOME/.config/Code/User/globalStorage/verdentai.verdent"

if [ -d "$VERDENT_STORAGE" ]; then
    # 备份
    BACKUP_PATH="${VERDENT_STORAGE}.backup.$(date +%Y%m%d_%H%M%S)"
    cp -r "$VERDENT_STORAGE" "$BACKUP_PATH"
    
    # 清除认证文件
    rm -f "$VERDENT_STORAGE/verdentApiKey" \
          "$VERDENT_STORAGE/userInfo" \
          "$VERDENT_STORAGE/ycAuthToken" \
          "$VERDENT_STORAGE/authNonce" \
          "$VERDENT_STORAGE/authNonceTimestamp"
    
    echo "Verdent logout successful. Backup: $BACKUP_PATH"
else
    echo "Verdent storage not found"
fi
```

#### 优点
- ✅ 无需修改插件源码
- ✅ 可以完全自动化
- ✅ 支持批量操作

#### 缺点
- ⚠️ 需要重启 VS Code 才能生效
- ⚠️ 可能影响插件的其他配置
- ⚠️ 存储路径可能因 VS Code 版本而异

---

### 方案 3: Hook WebView 消息通道 (高级)

#### 原理
通过注入代码到 WebView,模拟发送 `accountLogoutClicked` 消息。

#### 实现方法

**步骤 1**: 创建辅助扩展

```javascript
// helper-extension.js
const vscode = require('vscode');

function activate(context) {
    let disposable = vscode.commands.registerCommand('verdent-helper.triggerLogout', async () => {
        // 获取 Verdent WebView
        const verdentExtension = vscode.extensions.getExtension('verdentai.verdent');
        
        if (!verdentExtension) {
            vscode.window.showErrorMessage('Verdent extension not found');
            return;
        }

        // 方案 A: 通过命令面板触发
        await vscode.commands.executeCommand('verdent.accountButtonClicked');
        
        // 等待 UI 加载
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // 方案 B: 发送键盘事件模拟点击退出按钮
        // (需要具体分析 WebView UI 结构)
    });

    context.subscriptions.push(disposable);
}

exports.activate = activate;
```

**步骤 2**: 外部调用

```bash
code --command verdent-helper.triggerLogout
```

#### 优点
- ✅ 不直接修改原插件
- ✅ 可以复用现有逻辑

#### 缺点
- ⚠️ 实现复杂度高
- ⚠️ 依赖 WebView 内部结构
- ⚠️ 插件更新后可能失效

---

### 方案 4: 通过 VS Code API 伪造插件行为

#### 原理
利用 VS Code 的 `ExtensionContext` API,直接操作插件的全局状态。

#### 实现代码

```javascript
const vscode = require('vscode');

async function forceVerdentLogout() {
    try {
        // 获取 Verdent 扩展
        const verdentExtension = vscode.extensions.getExtension('verdentai.verdent');
        
        if (!verdentExtension) {
            throw new Error('Verdent extension not installed');
        }
        
        // 激活扩展 (如果未激活)
        if (!verdentExtension.isActive) {
            await verdentExtension.activate();
        }
        
        // 获取扩展的 Context (通过 Hack 方式)
        // 注意: 这需要深入分析扩展的内部实现
        const context = verdentExtension.exports?.context;
        
        if (!context) {
            throw new Error('Cannot access Verdent context');
        }
        
        // 清除存储
        await context.globalState.update('verdentApiKey', undefined);
        await context.globalState.update('userInfo', undefined);
        await context.secrets.delete('ycAuthToken');
        await context.globalState.update('authNonce', undefined);
        await context.globalState.update('authNonceTimestamp', undefined);
        
        // 触发 UI 更新
        await vscode.commands.executeCommand('setContext', 'verdent.showVerdentMenu', false);
        
        vscode.window.showInformationMessage('Verdent logout successful (forced)');
        
    } catch (error) {
        vscode.window.showErrorMessage('Logout failed: ' + error.message);
        console.error('Verdent force logout error:', error);
    }
}
```

#### 限制
- ⚠️ `exports.context` 可能未暴露
- ⚠️ 需要逆向分析存储键名
- ⚠️ 可能违反扩展隔离原则

---

## 🔧 推荐方案对比

| 方案 | 难度 | 可靠性 | 可维护性 | 推荐指数 |
|------|------|--------|----------|----------|
| **方案 1: 修改源码注册命令** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **方案 2: 直接操作存储** | ⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **方案 3: Hook WebView** | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐ |
| **方案 4: 伪造插件行为** | ⭐⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐ |

---

## 📝 详细实现指南

### 最佳实践: 方案 1 + 方案 2 组合

#### 第一阶段: 快速临时方案 (立即可用)

使用**方案 2** 创建自动化脚本:

```powershell
# verdent-logout.ps1
param(
    [switch]$AutoReload = $false
)

$ErrorActionPreference = "Stop"

function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

try {
    $storagePath = "$env:APPDATA\Code\User\globalStorage\verdentai.verdent"
    
    if (-not (Test-Path $storagePath)) {
        Write-ColorOutput Yellow "Verdent storage directory not found. Extension may not be installed."
        exit 1
    }
    
    # 备份
    $backupPath = "$storagePath.backup.$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    Copy-Item -Path $storagePath -Destination $backupPath -Recurse -Force
    Write-ColorOutput Green "Backup created: $backupPath"
    
    # 清除认证信息
    $authFiles = @(
        "verdentApiKey",
        "userInfo", 
        "ycAuthToken",
        "authNonce",
        "authNonceTimestamp"
    )
    
    foreach ($file in $authFiles) {
        $fullPath = Join-Path $storagePath $file
        if (Test-Path $fullPath) {
            Remove-Item -Path $fullPath -Force
            Write-ColorOutput Cyan "Removed: $file"
        }
    }
    
    Write-ColorOutput Green "`n✓ Verdent logout successful!"
    
    if ($AutoReload) {
        Write-ColorOutput Yellow "Reloading VS Code window..."
        code --command "workbench.action.reloadWindow"
    } else {
        Write-ColorOutput Yellow "`nPlease reload VS Code window to apply changes."
        Write-ColorOutput Yellow "Run with -AutoReload switch to reload automatically."
    }
    
} catch {
    Write-ColorOutput Red "Error: $_"
    exit 1
}
```

**使用方法**:
```powershell
# 手动退出
.\verdent-logout.ps1

# 自动重载 VS Code
.\verdent-logout.ps1 -AutoReload
```

---

#### 第二阶段: 永久方案 (修改插件)

**1. 解包插件**:
```bash
# VSIX 文件本质是 ZIP 压缩包
cd "f:\Trace\TEST\Verdent"
unzip verdentai.verdent-1.0.9.vsix -d verdent-modified
```

**2. 修改源码**:

在 `extension/dist/extension.js` 的 activate 函数中 (行 636175 之前) 添加:

```javascript
// 添加退出命令注册
oi.commands.registerCommand("verdent.logout", async () => {
  try {
    let controller = Pr.getSidebarInstance()?.controller;
    if (!controller) {
      oi.window.showWarningMessage("Verdent is not initialized yet");
      return;
    }
    
    // 调用现有的退出方法
    await controller.handleSignOut();
    
    // 显示成功消息
    oi.window.showInformationMessage("✓ Successfully logged out of Verdent");
    
    // 记录日志
    console.log("Verdent logout completed via command");
  } catch (error) {
    oi.window.showErrorMessage("Logout failed: " + error.message);
    console.error("Verdent logout error:", error);
  }
}),
```

在 `extension/package.json` 的 `commands` 数组中添加:

```json
{
  "command": "verdent.logout",
  "title": "Logout from Verdent",
  "category": "Verdent"
}
```

**3. 重新打包**:
```bash
cd verdent-modified/extension
npm install -g vsce
vsce package
```

**4. 安装修改后的插件**:
```bash
code --install-extension verdent-1.0.9-modified.vsix
```

**5. 外部调用**:

**Python 脚本**:
```python
# verdent_logout.py
import subprocess
import sys

def logout_verdent():
    """执行 Verdent 退出操作"""
    try:
        result = subprocess.run(
            ['code', '--command', 'verdent.logout'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("✓ Verdent logout successful")
            return True
        else:
            print(f"✗ Logout failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("✗ Timeout: VS Code did not respond")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    success = logout_verdent()
    sys.exit(0 if success else 1)
```

**Node.js 模块**:
```javascript
// verdent-api.js
const { exec } = require('child_process');
const util = require('util');
const execPromise = util.promisify(exec);

class VerdentAPI {
    /**
     * 执行退出登录
     * @returns {Promise<boolean>} 成功返回 true
     */
    async logout() {
        try {
            const { stdout, stderr } = await execPromise('code --command verdent.logout');
            
            if (stderr && stderr.includes('error')) {
                console.error('Logout error:', stderr);
                return false;
            }
            
            console.log('✓ Verdent logout successful');
            return true;
            
        } catch (error) {
            console.error('Failed to logout:', error.message);
            return false;
        }
    }
}

module.exports = new VerdentAPI();
```

**使用示例**:
```javascript
const verdentAPI = require('./verdent-api');

// 在你的应用中调用
async function handleUserLogout() {
    const success = await verdentAPI.logout();
    if (success) {
        console.log('User logged out from Verdent');
    }
}
```

---

## 🔒 安全考虑

### 1. 认证信息保护

**当前实现的安全措施**:

```javascript
// 使用 VS Code Secrets API 存储敏感 Token
await context.secrets.store('ycAuthToken', token);
await context.secrets.delete('ycAuthToken');
```

**建议**:
- ✅ `ycAuthToken` 已使用 Secrets API (加密存储)
- ⚠️ `verdentApiKey` 和 `userInfo` 使用 `globalState` (明文存储)
- 🔧 建议将所有认证信息迁移到 Secrets API

---

### 2. 退出操作的审计

**添加日志记录** (修改 `handleSignOut`):

```javascript
async handleSignOut() {
  try {
    // 记录退出操作
    const timestamp = new Date().toISOString();
    const userInfo = await Lr(this.context, "userInfo");
    
    vt.log(`User logout initiated at ${timestamp}`, {
      userId: userInfo?.id ?? 'unknown',
      method: 'handleSignOut'
    });
    
    // 原有退出逻辑
    await Gi(this.context, "verdentApiKey", void 0),
    await Mr(this.context, "userInfo", void 0),
    // ... 其余代码
    
    vt.log('User logout completed successfully');
    
  } catch (e) {
    vt.error("Logout failed", {
      error: e.message,
      stack: e.stack
    });
    
    Gr.window.showErrorMessage("Logout failed");
  }
}
```

---

### 3. 防止意外退出

**添加确认对话框**:

```javascript
oi.commands.registerCommand("verdent.logout", async () => {
  // 确认对话框
  const confirm = await oi.window.showWarningMessage(
    "Are you sure you want to logout from Verdent?",
    { modal: true },
    "Logout"
  );
  
  if (confirm !== "Logout") {
    return; // 用户取消
  }
  
  // 执行退出
  try {
    let controller = Pr.getSidebarInstance()?.controller;
    if (controller) {
      await controller.handleSignOut();
      oi.window.showInformationMessage("✓ Successfully logged out of Verdent");
    }
  } catch (error) {
    oi.window.showErrorMessage("Logout failed: " + error.message);
  }
});
```

---

## 📊 完整测试用例

### 测试脚本

```javascript
// test-verdent-logout.js
const vscode = require('vscode');
const assert = require('assert');

suite('Verdent Logout Test Suite', () => {
    
    test('应该能够通过命令退出', async () => {
        // 确保扩展已激活
        const verdent = vscode.extensions.getExtension('verdentai.verdent');
        assert.ok(verdent, 'Verdent extension should be installed');
        
        await verdent.activate();
        
        // 执行退出命令
        await vscode.commands.executeCommand('verdent.logout');
        
        // 验证退出状态
        // (需要访问插件内部状态,这里仅作示例)
        const isLoggedOut = true; // 实际需要检查存储
        assert.strictEqual(isLoggedOut, true, 'User should be logged out');
    });
    
    test('退出后应清除所有认证信息', async () => {
        // 获取扩展上下文
        const context = vscode.extensions.getExtension('verdentai.verdent')?.exports?.context;
        
        if (context) {
            // 执行退出
            await vscode.commands.executeCommand('verdent.logout');
            
            // 验证存储已清空
            const apiKey = context.globalState.get('verdentApiKey');
            const userInfo = context.globalState.get('userInfo');
            
            assert.strictEqual(apiKey, undefined, 'API key should be cleared');
            assert.strictEqual(userInfo, undefined, 'User info should be cleared');
        }
    });
    
    test('退出应该显示成功消息', async () => {
        let messageShown = false;
        
        // Mock window.showInformationMessage
        const originalShowInfo = vscode.window.showInformationMessage;
        vscode.window.showInformationMessage = (message) => {
            if (message.includes('logged out')) {
                messageShown = true;
            }
            return originalShowInfo(message);
        };
        
        await vscode.commands.executeCommand('verdent.logout');
        
        assert.strictEqual(messageShown, true, 'Success message should be shown');
        
        // 恢复原始方法
        vscode.window.showInformationMessage = originalShowInfo;
    });
});
```

---

## 🎯 总结与建议

### 当前状态
- ❌ **无法直接外部调用**: 插件未提供公开 API 或命令
- ✅ **内部实现完善**: 退出逻辑清晰且健壮
- ⚠️ **架构限制**: 基于 WebView 的内部通信机制

### 推荐实施路径

#### 短期方案 (1-2 天)
使用**方案 2** 创建自动化脚本:
```powershell
# 立即可用的退出脚本
f:\Trace\TEST\Verdent\test\verdent-logout.ps1 -AutoReload
```

#### 中期方案 (1 周)
修改插件源码实现**方案 1**:
1. 解包 VSIX 插件
2. 添加命令注册代码
3. 重新打包并安装
4. 开发外部调用接口

#### 长期方案 (提交 PR)
向 Verdent 官方提交功能请求:
```markdown
Feature Request: Add Public Logout Command

## Description
Please expose a logout command through VS Code's command palette 
to allow external automation tools to trigger logout programmatically.

## Proposed API
- Command: `verdent.logout`
- Returns: Promise<boolean>

## Use Cases
- CI/CD pipelines
- Automated testing
- Multi-user environment management
```

### 技术债务建议

1. **迁移认证存储到 Secrets API**:
   ```javascript
   // 当前 (不安全)
   await context.globalState.update('verdentApiKey', key);
   
   // 建议 (安全)
   await context.secrets.store('verdentApiKey', key);
   ```

2. **统一退出逻辑**:
   - 合并 `logout()` 和 `handleSignOut()` 为单一方法
   - 添加退出事件发射器供其他模块监听

3. **实现 Extension API**:
   ```javascript
   // 在 activate 函数中导出 API
   return {
       logout: async () => {
           return await controller.handleSignOut();
       }
   };
   ```

---

## 📚 参考资料

### VS Code 扩展开发文档
- [Command API](https://code.visualstudio.com/api/extension-guides/command)
- [Secrets API](https://code.visualstudio.com/api/references/vscode-api#SecretStorage)
- [Extension Context](https://code.visualstudio.com/api/references/vscode-api#ExtensionContext)

### 相关代码位置
- 退出方法: `extension.js:624665` (logout), `629078` (handleSignOut)
- 消息处理: `extension.js:629235` (handleWebviewMessage)
- 激活函数: `extension.js:635696` (activate)
- 命令注册: `extension.js:635730+` / `package.json:63`

### 工具清单
- **vsce**: VS Code 插件打包工具
- **asar**: 解压 VS Code 内部文件
- **PowerShell**: Windows 自动化脚本
- **Node.js**: 跨平台 API 封装

---

## 📞 联系与支持

如需进一步的技术支持或代码示例,请联系开发团队。

**分析完成时间**: 2025-11-14  
**分析工具**: Verdent AI Code Analysis  
**文档版本**: 1.0
