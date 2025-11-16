# Token 登录问题修复报告

## 问题描述

在 Verdent_account_manager 项目中,使用 token 进行登录时遇到以下错误:

```
登录失败: invalid args `token` for command `login_with_token`: command login_with_token missing required key token
```

## 根本原因分析

### 1. 参数不匹配问题

**前端调用方式** (`App.vue` 第 93 行):
```typescript
const response = await invoke<LoginResponse>('login_with_token', { request })
```

前端传递的参数结构:
```json
{
  "request": {
    "token": "...",
    "device_id": "...",
    "app_version": "..."
  }
}
```

**后端原始定义** (`commands.rs` 第 138 行):
```rust
#[tauri::command]
pub async fn login_with_token(token: String) -> Result<Account, String> {
    Err("Not implemented yet".to_string())
}
```

后端期望的参数:
```json
{
  "token": "..."
}
```

### 2. 问题分析

- **前端传递**: `{ request: LoginRequest }` - 嵌套的对象结构
- **后端期望**: `token: String` - 直接的字符串参数
- **Tauri 错误**: 在参数中找不到 `token` 键,因为实际传递的顶层键是 `request`

## 修复方案

### 1. 添加请求/响应结构体

在 `commands.rs` 中添加了 `LoginRequest` 和 `LoginResponse` 结构体:

```rust
#[derive(Debug, Serialize, Deserialize)]
pub struct LoginRequest {
    pub token: String,
    pub device_id: Option<String>,
    pub app_version: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct LoginResponse {
    pub success: bool,
    pub access_token: Option<String>,
    pub error: Option<String>,
    pub callback_url: Option<String>,
}
```

### 2. 修改命令签名

将 `login_with_token` 命令的签名从:
```rust
pub async fn login_with_token(token: String) -> Result<Account, String>
```

修改为:
```rust
pub async fn login_with_token(request: LoginRequest) -> Result<LoginResponse, String>
```

### 3. 实现完整的登录逻辑

实现了完整的 PKCE 登录流程:

1. **生成 PKCE 参数**: 使用 `PkceParams::generate()` 生成 state、code_verifier 和 code_challenge
2. **请求授权码**: 使用 token 和 PKCE 参数调用 `VerdentApi::request_auth_code()`
3. **交换访问令牌**: 使用授权码和 code_verifier 调用 `VerdentApi::exchange_token()`
4. **构建回调 URL**: 生成 VS Code 回调链接
5. **保存到本地存储**: 将访问令牌、API 提供商、设备 ID 等信息保存到本地存储

### 4. 实现 VS Code 回调功能

实现了 `open_vscode_callback` 命令,支持跨平台打开 VS Code 回调链接:

- **Windows**: 使用 `cmd /C start`
- **macOS**: 使用 `open`
- **Linux**: 使用 `xdg-open`

## 修改的文件

### `Verdent_account_manger/src-tauri/src/commands.rs`

1. 添加导入:
   - `use crate::api::VerdentApi;`
   - `use crate::pkce::PkceParams;`

2. 添加结构体:
   - `LoginRequest`
   - `LoginResponse`

3. 完整实现 `login_with_token` 命令 (第 154-223 行)

4. 完整实现 `open_vscode_callback` 命令 (第 264-292 行)

## 测试建议

1. **基本登录测试**:
   - 在前端输入有效的 token
   - 验证是否成功获取访问令牌
   - 检查本地存储是否正确保存

2. **错误处理测试**:
   - 使用无效的 token
   - 验证错误消息是否正确返回

3. **VS Code 回调测试**:
   - 勾选"自动打开 VS Code"选项
   - 验证是否正确打开 VS Code 并触发回调

4. **可选参数测试**:
   - 测试带/不带 device_id 的情况
   - 测试带/不带 app_version 的情况

## 相关文件

- `Verdent_account_manger/src-tauri/src/commands.rs` - 命令实现
- `Verdent_account_manger/src-tauri/src/api.rs` - API 调用
- `Verdent_account_manger/src-tauri/src/pkce.rs` - PKCE 参数生成
- `Verdent_account_manger/src-tauri/src/storage.rs` - 本地存储管理
- `Verdent_account_manger/src/App.vue` - 前端界面

## 总结

问题的根本原因是前端和后端的参数结构不匹配。通过:
1. 添加正确的请求/响应结构体
2. 修改命令签名以接受 `LoginRequest` 参数
3. 实现完整的 PKCE 登录流程
4. 实现 VS Code 回调功能

成功修复了 token 登录功能,现在前端传递的 `{ request: LoginRequest }` 参数可以正确被后端接收和处理。

