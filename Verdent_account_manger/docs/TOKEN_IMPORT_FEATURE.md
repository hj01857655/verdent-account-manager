# Token 导入功能文档

## 功能概述

Token 导入功能允许用户通过已有的 Verdent Token 快速导入账户,无需手动注册。系统会自动从 API 获取账户的完整信息,包括邮箱、订阅类型、额度等。

## 功能特性

### 1. 批量导入
- 支持一次导入多个 Token
- 每行一个 Token,自动解析
- 显示导入进度和结果统计

### 2. 智能处理
- 如果邮箱已存在,自动更新账户信息
- 如果邮箱不存在,创建新账户
- 自动获取并保存完整的账户信息

### 3. 完整信息获取
从 Verdent API 自动获取:
- 邮箱地址
- 订阅类型 (Free/Starter/Pro/Max)
- 额度信息 (已消耗/剩余/总计)
- 订阅周期结束时间
- 自动续订状态
- 试用天数
- 过期时间

## 使用方法

### 前端操作

1. **打开导入对话框**
   - 点击账户管理页面头部的 "📥 导入 Token" 按钮

2. **输入 Token**
   - 在文本框中粘贴 Token
   - 支持多行,每行一个 Token
   - 自动过滤空行

3. **开始导入**
   - 点击 "开始导入" 按钮
   - 系统显示 loading 状态
   - 逐个处理 Token

4. **查看结果**
   - 导入完成后显示统计信息
   - 成功数量和失败数量
   - 失败的详细错误信息

### 后端 API

**命令名称**: `import_account_by_token`

**输入参数**:
```typescript
{
  token: string  // Verdent Token
}
```

**返回结果**:
```typescript
{
  success: boolean
  account?: Account
  error?: string
}
```

## 实现细节

### 后端实现 (Rust)

**文件**: `src-tauri/src/commands.rs`

**核心流程**:
1. 验证 Token 格式
2. 调用 `VerdentApi::fetch_user_info()` 获取用户信息
3. 提取邮箱、额度、订阅等信息
4. 检查账户是否已存在
5. 更新现有账户或创建新账户
6. 保存到 `accounts.json`

**关键代码**:
```rust
#[tauri::command]
pub async fn import_account_by_token(token: String) -> Result<ImportAccountResponse, String>
```

### 前端实现 (Vue 3)

**文件**: `src/components/AccountManager.vue`

**核心功能**:
- `showImportDialog`: 控制对话框显示
- `importTokens`: 存储用户输入的 Token
- `handleImportTokens()`: 处理批量导入逻辑

**UI 组件**:
- 导入按钮 (绿色渐变)
- 模态对话框
- 多行文本输入框
- 使用说明提示

## 错误处理

### 常见错误

1. **Token 为空**
   - 错误信息: "Token 不能为空"
   - 解决方法: 确保输入有效的 Token

2. **Token 无效或已过期**
   - 错误信息: "获取用户信息失败: HTTP错误: 401"
   - 解决方法: 使用有效的 Token

3. **网络错误**
   - 错误信息: "获取用户信息失败: 网络连接失败"
   - 解决方法: 检查网络连接

4. **API 响应缺少邮箱**
   - 错误信息: "API 响应中缺少邮箱信息"
   - 解决方法: 确保 Token 对应的账户有效

### 错误日志

后端会输出详细的日志信息:
```
[*] ========== 导入 Token 账户 ==========
[*] Token 长度: 123 字符
[*] 使用 Token 获取用户信息...
[✓] 成功获取用户信息
[*] 账户邮箱: user@example.com
[*] 额度信息:
    已消耗: 1.23
    总额度: 100.00
    剩余: 98.77
[*] 订阅信息:
    类型: Some("Pro")
    周期结束: Some(1234567890)
    自动续订: true
[✓] Token 导入成功: user@example.com
======================================
```

## 注意事项

1. **密码字段为空**
   - 通过 Token 导入的账户没有密码
   - 如需使用"测试登录"功能,需手动设置密码

2. **Token 安全**
   - Token 是敏感信息,请妥善保管
   - 不要在公共场合分享 Token

3. **导入速度**
   - 批量导入时,每个 Token 之间有 500ms 延迟
   - 避免请求过快导致 API 限流

4. **账户更新**
   - 如果邮箱已存在,会覆盖原有信息
   - 建议在导入前备份重要数据

## 相关文件

- **后端命令**: `src-tauri/src/commands.rs` (第 977-1156 行)
- **前端组件**: `src/components/AccountManager.vue`
- **API 模块**: `src-tauri/src/api.rs`
- **账户管理**: `src-tauri/src/account_manager.rs`

