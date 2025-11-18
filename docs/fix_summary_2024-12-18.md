# 修复总结 - 2024-12-18

## 🎯 修复的核心问题

### 问题 1：确认对话框在操作后显示

**问题描述**：
用户反馈确认对话框在机器码重置操作**之后**才显示，而不是之前，失去了确认的意义。

**根本原因**：
- 代码逻辑本身是正确的（确认框在 `invoke` 之前）
- 但在递归调用时（第489行），会再次触发整个流程，包括确认框
- 用户可能混淆了文件选择对话框和确认对话框

**修复方案**：
1. 为 `handleLoginVerdentClient` 函数添加 `skipConfirm` 参数
2. 首次调用时显示确认框
3. 递归调用时（选择路径后重试）跳过确认框
4. 改进确认对话框文案，更清晰地说明操作内容和风险

**修改文件**：
- `Verdent_account_manger/src/components/AccountCard.vue`

---

### 问题 2：Windows 凭据管理器写入的凭据格式不正确 ⚠️ 核心问题

**问题描述**：
通过十六进制对比发现，软件写入的凭据数据与正确的凭据数据不一致：
- 正确凭据的数据长度：`0x01DC`（476 字节）
- 软件写入的数据长度：`0x00C8`（200 字节）
- JSON 数据被截断，只有 `{` 字符

**根本原因**：
- 旧实现使用 PowerShell 的 `cmdkey` 命令写入凭证
- `cmdkey` 命令会对密码进行编码转换（可能是 UTF-16 或其他编码）
- 导致 JSON 数据被截断或损坏
- Python 参考脚本使用 Windows API `CredWriteW` 直接写入 UTF-8 字节

**修复方案**：
1. 添加 `windows` crate 依赖（版本 0.58）
2. 完全重写 `write_token_windows` 方法
3. 使用 Windows API `CredWriteW` 直接写入凭证
4. 凭证数据以 UTF-8 字节格式写入，确保 JSON 数据完整性
5. 添加详细的调试日志（JSON 数据、长度、目标名称）

**修改文件**：
- `Verdent_account_manger/src-tauri/Cargo.toml` - 添加 Windows API 依赖
- `Verdent_account_manger/src-tauri/src/verdent_client.rs` - 重写凭证写入逻辑

**技术对比**：

| 实现方式 | 旧实现（PowerShell cmdkey） | 新实现（Windows API） | Python 参考 |
|---------|---------------------------|---------------------|------------|
| 调用方式 | PowerShell 脚本 | 直接调用 Windows API | ctypes 调用 API |
| 数据编码 | 自动转换（可能损坏） | UTF-8 字节 | UTF-8 字节 |
| 数据完整性 | ❌ 截断 | ✅ 完整 | ✅ 完整 |
| 性能 | 慢（启动 PowerShell） | 快（直接调用） | 快（直接调用） |

---

## 📝 代码变更详情

### 1. Cargo.toml 添加依赖

```toml
[target.'cfg(windows)'.dependencies]
windows = { version = "0.58", features = [
    "Win32_Foundation",
    "Win32_Security_Credentials",
] }
```

### 2. verdent_client.rs 重写凭证写入

**旧实现**（100行 PowerShell 脚本）：
```rust
let ps_script = format!(r#"
    # 使用 cmdkey 添加凭证
    cmdkey /generic:"$target" /user:"$username" /pass:"$password"
"#);
Command::new("powershell").args(&["-Command", &ps_script]).output()?;
```

**新实现**（70行 Windows API）：
```rust
use windows::Win32::Security::Credentials::{CredWriteW, CREDENTIALW};

let password_bytes = password_json.as_bytes();
let mut cred = CREDENTIALW {
    Type: CRED_TYPE_GENERIC,
    TargetName: PCWSTR::from_raw(target_name_wide.as_ptr()),
    CredentialBlob: password_bytes.as_ptr() as *mut u8,
    CredentialBlobSize: password_bytes.len() as u32,
    UserName: PCWSTR::from_raw(username_wide.as_ptr()),
    Persist: CRED_PERSIST_ENTERPRISE,
    // ... 其他字段
};
unsafe { CredWriteW(&mut cred, 0)? };
```

### 3. AccountCard.vue 优化确认逻辑

```typescript
// 添加参数
async function handleLoginVerdentClient(skipConfirm = false) {
  // ...
  
  // 显示确认对话框（除非是递归调用）
  if (!skipConfirm) {
    const confirmLogin = confirm('⚠️ 登录到 Verdent 客户端\n\n...')
    if (!confirmLogin) {
      return
    }
  }
  
  // 执行登录...
  
  // 递归调用时跳过确认
  await handleLoginVerdentClient(true)
}
```

---

## ✅ 验证清单

### 编译验证
- [x] Cargo.toml 依赖正确
- [x] verdent_client.rs 无编译错误
- [x] AccountCard.vue 无 TypeScript 错误

### 功能验证
- [ ] 确认对话框在操作**之前**显示
- [ ] 点击"取消"不执行任何操作
- [ ] 递归调用时不重复显示确认框
- [ ] 凭证数据完整写入（长度正确）
- [ ] Verdent 客户端成功登录
- [ ] 不再出现 Permission IPC 错误

### 数据验证
- [ ] Windows 凭据管理器中凭证存在
- [ ] 凭证数据长度与 JSON 长度一致
- [ ] JSON 数据完整（包含 accessToken 和 expireAt）
- [ ] 机器码格式正确（大写无花括号）

---

## 🚀 下一步

1. **编译测试**：
   ```bash
   cd Verdent_account_manger
   npm run tauri build
   ```

2. **功能测试**：
   - 以管理员身份运行应用
   - 测试 Verdent 客户端登录功能
   - 验证凭证数据完整性

3. **如果仍有问题**：
   - 查看控制台日志中的 JSON 数据和长度
   - 使用 PowerShell 读取凭证验证数据
   - 对比十六进制数据确认格式

---

## 📚 参考资料

- Python 参考脚本：`Verdent协议注册\token_changer_gui.py`
- Windows API 文档：[CredWriteW function](https://learn.microsoft.com/en-us/windows/win32/api/wincred/nf-wincred-credwritew)
- Rust Windows crate：[windows-rs](https://github.com/microsoft/windows-rs)

