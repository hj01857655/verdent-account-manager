# 测试登录功能

## 🎯 功能概述

实现了"测试登录"功能,允许用户使用账户的邮箱和密码直接登录 Verdent,自动获取并更新 Token,同时刷新账户的额度、订阅类型等信息。

---

## ✨ 功能特性

### 1. 一键测试登录

- ✅ 每个账户卡片底部有 "🔑 测试登录" 按钮
- ✅ 使用账户的邮箱和密码调用 Verdent 登录 API
- ✅ 自动获取新的 Token 并保存
- ✅ 同时刷新账户的额度、订阅类型、过期时间等信息
- ✅ 无需手动复制粘贴 Token

### 2. 与刷新功能的区别

| 功能 | 测试登录 | 刷新账户信息 |
|------|---------|------------|
| **触发按钮** | 🔑 测试登录 | 🔄 刷新 |
| **需要条件** | 邮箱 + 密码 | Token |
| **主要用途** | 获取/更新 Token | 更新额度信息 |
| **适用场景** | Token 过期/缺失 | Token 有效 |
| **额外功能** | 更新过期时间 | - |

### 3. 使用场景

**场景 1: 新注册的账户**
- 注册后可能没有 Token
- 点击 "🔑 测试登录" 获取 Token
- 自动填充所有账户信息

**场景 2: Token 已过期**
- 刷新功能失败 (Token 无效)
- 点击 "🔑 测试登录" 重新获取 Token
- 恢复账户的正常使用

**场景 3: 验证账户有效性**
- 测试邮箱和密码是否正确
- 确认账户是否被封禁
- 检查账户状态

---

## 🔧 技术实现

### 后端 (Rust)

#### 1. API 模块 (`src-tauri/src/api.rs`)

**新增数据结构**:
```rust
#[derive(Debug, Serialize, Deserialize)]
pub struct LoginData {
    pub token: String,
    #[serde(rename = "expireTime")]
    pub expire_time: Option<i64>,
    #[serde(rename = "accessToken")]
    pub access_token: Option<String>,
    #[serde(rename = "refreshToken")]
    pub refresh_token: Option<String>,
    #[serde(rename = "accessTokenExpiresAt")]
    pub access_token_expires_at: Option<i64>,
    #[serde(rename = "refreshTokenExpiresAt")]
    pub refresh_token_expires_at: Option<i64>,
    #[serde(rename = "needBindInviteCode")]
    pub need_bind_invite_code: Option<bool>,
}
```

**新增方法**:
```rust
pub async fn login(&self, email: &str, password: &str) -> Result<LoginData, Box<dyn std::error::Error>>
```

调用 Verdent 登录 API: `https://login.verdent.ai/passport/login`

#### 2. 命令模块 (`src-tauri/src/commands.rs`)

**新增命令**:
```rust
#[tauri::command]
pub async fn test_login_and_update(account_id: String) -> Result<TestLoginResponse, String>
```

**执行流程**:
1. 加载账户管理器
2. 查找指定账户
3. 使用邮箱和密码调用登录 API
4. 获取 Token 并更新账户
5. 使用新 Token 获取用户信息
6. 更新额度、订阅类型、过期时间等
7. 保存到 `accounts.json`
8. 返回更新后的账户信息

### 前端 (Vue 3 + TypeScript)

#### 1. 账户卡片 (`AccountCard.vue`)

**新增按钮**:
```vue
<div class="action-buttons">
  <!-- 测试登录按钮 -->
  <button
    class="test-login-btn"
    @click="handleTestLogin"
    :disabled="testLoginLoading"
  >
    <span v-if="testLoginLoading">⏳ 测试中...</span>
    <span v-else>🔑 测试登录</span>
  </button>

  <!-- 一键登录按钮 -->
  <button
    class="login-btn"
    @click="handleLogin"
    :disabled="!account.token || loginLoading"
  >
    <span v-if="loginLoading">⏳ 登录中...</span>
    <span v-else>🚀 登录到 VS Code</span>
  </button>
</div>
```

**新增函数**:
```typescript
async function handleTestLogin() {
  const result = await invoke('test_login_and_update', { accountId: props.account.id })
  if (result.success) {
    emit('refresh', props.account.id) // 触发刷新以显示最新数据
  }
}
```

---

## 📊 API 调用详情

### Verdent 登录 API

**URL**: `https://login.verdent.ai/passport/login`

**方法**: `POST`

**请求头**:
```
Accept: application/json, text/plain, */*
Content-Type: application/json
Origin: https://www.verdent.ai
Referer: https://www.verdent.ai/
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
```

**请求体**:
```json
{
  "email": "user@example.com",
  "password": "VerdentAI@2024"
}
```

**响应格式**:
```json
{
  "errCode": 0,
  "errMsg": "",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expireTime": 1765726718,
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "accessTokenExpiresAt": 1765726718,
    "refreshTokenExpiresAt": 1766590718,
    "needBindInviteCode": false
  }
}
```

**Token 有效期**:
- `accessToken`: 约 30 天 (2592000 秒)
- `refreshToken`: 约 40 天 (3456000 秒)

---

## 🎨 用户界面

### 按钮布局

每个账户卡片底部有两个并排的按钮:

```
┌─────────────────────────────────────────┐
│  [🔑 测试登录]  [🚀 登录到 VS Code]    │
└─────────────────────────────────────────┘
```

### 按钮样式

- **测试登录按钮**: 橙色渐变 (#f59e0b → #d97706)
- **登录到 VS Code 按钮**: 绿色渐变 (#10b981 → #059669)
- **悬停效果**: 向上移动 2px,阴影加深
- **禁用状态**: 半透明,灰色背景

---

## ⚠️ 错误处理

### 可能的错误情况

1. **邮箱或密码错误**:
   ```
   登录失败: 邮箱或密码错误
   ```

2. **账户被封禁**:
   ```
   登录失败: 账户已被封禁
   ```

3. **网络错误**:
   ```
   登录失败: HTTP错误: 网络连接失败
   ```

4. **API 错误**:
   ```
   登录失败: 服务器内部错误
   ```

---

## 🚀 使用方法

### 测试登录并更新 Token

1. 找到需要更新 Token 的账户卡片
2. 点击底部的 "🔑 测试登录" 按钮
3. 等待登录完成 (显示 "⏳ 测试中...")
4. 登录成功后自动刷新显示最新信息
5. 查看更新后的 Token、额度、过期时间等

### 登录到 VS Code

1. 确保账户有有效的 Token
2. 点击 "🚀 登录到 VS Code" 按钮
3. VS Code 自动打开并完成登录

---

## 🎉 总结

测试登录功能已完整实现:
- ✅ **一键获取 Token** - 使用邮箱密码自动登录
- ✅ **自动更新信息** - 同时刷新额度、订阅类型等
- ✅ **友好的界面** - 清晰的按钮和加载状态
- ✅ **完善的错误处理** - 详细的错误提示
- ✅ **持久化保存** - 自动保存到 `accounts.json`

现在用户可以轻松测试账户的有效性,并自动获取最新的 Token! 🚀

