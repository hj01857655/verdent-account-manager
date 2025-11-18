# Bug 修复验证指南（2024-12-18 更新）

## 最新修复的问题

### 问题 1：确认对话框在操作后显示

**修复内容**：
1. 优化了 `handleLoginVerdentClient` 函数的确认对话框逻辑
2. 确认对话框现在在调用后端命令**之前**显示
3. 添加了 `skipConfirm` 参数，避免递归调用时重复显示确认框
4. 改进了确认对话框的文案，更清晰地说明操作内容和风险

**验证步骤**：
1. 打开应用，选择一个有 Token 的账号
2. 点击"Verdent 客户端登录"按钮（Verdent 图标）
3. **预期结果**：
   - **立即**弹出确认对话框，显示详细的操作说明和警告
   - 对话框内容包括：写入 Token、重置机器码、重启客户端等步骤
   - 点击"取消"后不执行任何操作，显示"已取消登录操作"
   - 点击"确定"后才开始执行后端命令
4. 如果首次使用需要选择 Verdent.exe 路径：
   - 选择路径后**不会**再次显示确认框
   - 直接执行登录操作

### 问题 2：Windows 凭据管理器写入的凭据格式不正确

**修复内容**：
1. **完全重写**了 `write_token_windows` 方法
2. 不再使用 PowerShell 的 `cmdkey` 命令
3. 直接使用 Windows API `CredWriteW` 写入凭证（与 Python 脚本一致）
4. 凭证数据以 UTF-8 字节格式写入，确保 JSON 数据完整性
5. 添加了详细的调试日志，显示 JSON 数据和长度

**验证步骤**：
1. 确保以**管理员身份**运行应用
2. 选择一个有效的账号，点击"Verdent 客户端登录"按钮
3. 在确认对话框中点击"确定"
4. 观察控制台日志，应该显示：
   ```
   [*] 凭证 JSON 数据: {"accessToken":"eyJ...","expireAt":1766054472000}
   [*] JSON 长度: XXX 字节
   [*] 写入凭证到: LegacyGeneric:target=ai.verdent.deck/access-token
   [✓] 凭证已写入: LegacyGeneric:target=ai.verdent.deck/access-token
   [*] 写入凭证到: LegacyGeneric:target=ai.verdent/access-token
   [✓] 凭证已写入: LegacyGeneric:target=ai.verdent/access-token
   [✓] Token 已写入 Windows Credential Manager
   ```
5. 打开 Windows 凭据管理器验证：
   - 打开"控制面板" → "凭据管理器" → "Windows 凭据"
   - 查找 `LegacyGeneric:target=ai.verdent.deck/access-token`
   - 确认凭证存在且数据完整
6. 使用十六进制编辑器验证凭据数据：
   - 凭据数据长度应该与 JSON 长度一致（偏移 0x00C0 处）
   - 应该包含完整的 JSON 数据：`{"accessToken":"eyJ...","expireAt":...}`
7. 启动 Verdent 客户端验证登录：
   - 客户端应该成功启动，不再出现 `[Permission IPC] Server error`
   - 客户端显示已登录状态
   - 可以正常使用 AI 功能

---

## 之前修复的问题

### 问题 3：机器码格式问题

**修复内容**：
1. 机器码格式从 `{3840DC62-7506-4F6C-A70F-79D5FC150433}` 改为 `3840DC62-7506-4F6C-A70F-79D5FC150433`（去掉花括号）
2. 统一使用大写格式

**验证步骤**：
1. 打开应用，进入"存储管理"标签页
2. 点击"重置机器码"按钮
3. **预期结果**：
   - 立即弹出确认对话框，显示警告信息
   - 点击"确定"后才执行重置操作
   - 重置后的机器码格式为 `XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX`（无花括号，大写）

---

### 问题 4：Verdent 客户端路径未持久化保存

**修复内容**：
1. 添加了详细的调试日志，帮助诊断路径保存和读取问题
2. 当自定义路径无效时会输出警告信息

**验证步骤**：
1. 打开应用，点击任意账号的"Verdent 客户端登录"按钮
2. 如果未找到 Verdent.exe，选择文件位置
3. 查看控制台日志，应该显示：`[✓] 路径已保存到设置`
4. 关闭应用并重新打开
5. 再次点击"Verdent 客户端登录"按钮
6. **预期结果**：
   - 不再弹出文件选择对话框
   - 控制台日志显示：`[✓] 使用用户自定义 Verdent 客户端: {路径}`
   - 如果路径无效，显示：`[!] 自定义路径无效 (不存在或不是文件): {路径}`

**检查保存的路径**：
- 打开文件：`C:\Users\{用户名}\.verdent_accounts\user_settings.json`
- 查看 `verdent_exe_path` 字段是否包含正确的路径

---

### 问题 5：其他优化

**修复内容**：
1. 机器码格式统一为大写无花括号
2. 重启等待时间从2秒增加到3秒（与 Python 脚本一致）
3. 在重启前清理 `%TEMP%\verdent-sockets\` 文件夹，解决权限错误

---

## 技术细节

### Windows API 凭据写入

**新实现**（使用 Windows API）：
```rust
use windows::Win32::Security::Credentials::{CredWriteW, CREDENTIALW};

// 直接调用 Windows API 写入凭证
let mut cred = CREDENTIALW {
    Type: CRED_TYPE_GENERIC,
    TargetName: "LegacyGeneric:target=ai.verdent.deck/access-token",
    CredentialBlob: password_bytes.as_ptr(),
    CredentialBlobSize: password_bytes.len() as u32,
    // ... 其他字段
};
CredWriteW(&mut cred, 0)?;
```

**旧实现**（使用 PowerShell cmdkey）：
- 问题：`cmdkey` 命令会对密码进行编码转换，导致 JSON 数据被截断
- 现象：凭证数据长度从 `0x01DC` 变成 `0x00C8`，JSON 数据不完整

**对比 Python 实现**：
```python
# Python 使用 ctypes 调用 Windows API
cred = CREDENTIAL()
cred.Type = CRED_TYPE_GENERIC
cred.TargetName = target_name
cred.CredentialBlob = ctypes.cast(
    ctypes.create_string_buffer(password_bytes),
    wintypes.LPBYTE
)
cred.CredentialBlobSize = len(password_bytes)
advapi32.CredWriteW(ctypes.byref(cred), 0)
```

现在 Rust 实现与 Python 实现完全一致，都是直接调用 Windows API。

---

## 调试技巧

### 查看控制台日志
- 在开发模式下：按 `F12` 打开开发者工具
- 在生产模式下：查看应用的日志输出
- 新增日志：凭证 JSON 数据和长度

### 检查设置文件
- 用户设置：`C:\Users\{用户名}\.verdent_accounts\user_settings.json`
- 机器码备份：`C:\Users\{用户名}\.verdent_accounts\machine_guid_backup.json`

### 检查 Windows 凭证管理器
1. 打开"控制面板" → "凭据管理器" → "Windows 凭据"
2. 查找 `LegacyGeneric:target=ai.verdent.deck/access-token`
3. 确认凭证是否正确写入
4. **新增**：可以使用 `cmdkey /list` 命令查看所有凭证

### 检查凭据数据完整性（高级）
1. 使用 PowerShell 读取凭证：
   ```powershell
   $cred = [Windows.Security.Credentials.PasswordVault]::new()
   # 或使用 CredRead API
   ```
2. 验证 JSON 数据是否完整
3. 检查数据长度是否与日志中的长度一致

### 检查注册表
1. 打开注册表编辑器 (`regedit`)
2. 导航到 `HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Cryptography`
3. 查看 `MachineGuid` 的值
4. 确认格式为大写无花括号（如：`3840DC62-7506-4F6C-A70F-79D5FC150433`）

---

## 已知限制

1. **管理员权限**：修改机器码和写入凭证需要管理员权限
2. **Windows 平台**：机器码管理功能仅支持 Windows
3. **Verdent 客户端**：必须先安装 Verdent 桌面应用才能使用客户端登录功能
4. **依赖项**：需要 `windows` crate 0.58 或更高版本

---

## 修复历史

### 2024-12-18
- ✅ 修复确认对话框在操作后显示的问题
- ✅ 使用 Windows API 直接写入凭证，解决数据截断问题
- ✅ 改进确认对话框文案，更清晰地说明操作内容
- ✅ 添加详细的调试日志

### 2024-12-17
- ✅ 修复机器码格式问题（去掉花括号）
- ✅ 添加路径持久化调试日志
- ✅ 优化重启等待时间
- ✅ 清理临时 socket 文件

