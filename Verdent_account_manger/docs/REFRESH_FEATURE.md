# 账户信息刷新功能

## 🎯 功能概述

实现了账户信息刷新功能,允许用户手动刷新单个账户或批量刷新所有账户的信息,包括额度、订阅类型、过期时间等。

---

## ✨ 功能特性

### 1. 单个账户刷新

- ✅ 每个账户卡片右上角有 🔄 刷新按钮
- ✅ 点击后调用 Verdent API 获取最新账户信息
- ✅ 自动更新并保存到 `accounts.json`
- ✅ 刷新成功后立即显示最新数据

### 2. 批量刷新所有账户

- ✅ 账户管理页面顶部有 "🔄 全部刷新" 按钮
- ✅ 一键刷新所有账户信息
- ✅ 显示刷新进度和结果统计
- ✅ 自动处理失败情况并显示详细错误信息

### 3. 刷新的信息

刷新功能会更新以下账户信息:
- ✅ **总额度** (`quota_total`) - 账户的总可用额度
- ✅ **已消耗额度** (`quota_used`) - 已使用的额度
- ✅ **剩余额度** (`quota_remaining`) - 计算得出的剩余额度
- ✅ **订阅类型** (`subscription_type`) - Free/Pro/Enterprise 等
- ✅ **试用天数** (`trial_days`) - 剩余试用天数
- ✅ **过期时间** (`expire_time`) - 账户过期时间
- ✅ **最后更新时间** (`last_updated`) - 记录刷新时间

---

## 🔧 技术实现

### 后端 (Rust)

#### 1. API 模块 (`src-tauri/src/api.rs`)

**新增数据结构**:
```rust
#[derive(Debug, Serialize, Deserialize)]
pub struct TokenInfo {
    #[serde(rename = "tokenConsumed")]
    pub token_consumed: Option<f64>,
    #[serde(rename = "tokenFree")]
    pub token_free: Option<f64>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct UserInfo {
    pub email: Option<String>,
    #[serde(rename = "tokenInfo")]
    pub token_info: Option<TokenInfo>,
    #[serde(rename = "subscriptionType")]
    pub subscription_type: Option<String>,
    #[serde(rename = "trialDays")]
    pub trial_days: Option<i32>,
    #[serde(rename = "expireTime")]
    pub expire_time: Option<String>,
}
```

**新增方法**:
```rust
pub async fn fetch_user_info(&self, token: &str) -> Result<UserInfo, Box<dyn std::error::Error>>
```

调用 Verdent API 的 `/user/center/info` 端点获取用户信息。

#### 2. 命令模块 (`src-tauri/src/commands.rs`)

**新增命令**:
```rust
#[tauri::command]
pub async fn refresh_account_info(account_id: String) -> Result<RefreshAccountResponse, String>
```

**执行流程**:
1. 加载账户管理器
2. 查找指定账户
3. 检查账户是否有 Token
4. 调用 API 获取用户信息
5. 计算额度信息 (剩余 = 总额度 - 已消耗)
6. 更新账户数据
7. 保存到 `accounts.json`
8. 返回更新后的账户信息

### 前端 (Vue 3 + TypeScript)

#### 1. 单个账户刷新 (`AccountCard.vue`)

**已有按钮**:
```vue
<button class="action-btn" @click="handleRefresh" title="刷新">
  🔄
</button>
```

**事件触发**:
```typescript
function handleRefresh() {
  emit('refresh', props.account.id)
}
```

#### 2. 刷新处理 (`AccountManager.vue`)

**单个刷新**:
```typescript
async function handleRefresh(id: string) {
  const result = await invoke('refresh_account_info', { accountId: id })
  if (result.success) {
    await loadAccounts() // 重新加载账户列表
  }
}
```

**批量刷新**:
```typescript
async function handleRefreshAll() {
  // 逐个刷新所有账户
  for (const account of accounts.value) {
    await invoke('refresh_account_info', { accountId: account.id })
    await new Promise(resolve => setTimeout(resolve, 500)) // 延迟避免请求过快
  }
  await loadAccounts()
}
```

---

## 📊 API 调用详情

### Verdent API 端点

**URL**: `https://agent.verdent.ai/user/center/info`

**方法**: `GET`

**请求头**:
```
Accept: application/json, text/plain, */*
Cookie: token={用户Token}
Origin: https://www.verdent.ai
Referer: https://www.verdent.ai/
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
```

**响应格式**:
```json
{
  "errCode": 0,
  "errMsg": null,
  "data": {
    "email": "user@example.com",
    "tokenInfo": {
      "tokenConsumed": 1.11,
      "tokenFree": 100.00
    },
    "subscriptionType": "Free",
    "trialDays": 14,
    "expireTime": "2024-12-31T23:59:59Z"
  }
}
```

---

## 🎨 用户界面

### 单个账户刷新

1. 每个账户卡片右上角有三个按钮:
   - 🔄 刷新
   - ✏️ 编辑
   - 🗑️ 删除

2. 点击 🔄 按钮后:
   - 调用 API 获取最新信息
   - 自动更新卡片显示
   - 无需手动刷新页面

### 批量刷新

1. 账户管理页面顶部:
   ```
   📦 账户管理    [🔄 全部刷新]  [➕ 自动注册]
   ```

2. 点击 "🔄 全部刷新" 后:
   - 显示确认对话框
   - 逐个刷新所有账户
   - 显示进度和结果统计

---

## ⚠️ 错误处理

### 可能的错误情况

1. **账户没有 Token**:
   ```
   刷新失败: 账户没有 Token,无法刷新
   ```

2. **Token 已过期**:
   ```
   刷新失败: API错误: Token 已过期
   ```

3. **网络错误**:
   ```
   刷新失败: HTTP错误: 网络连接失败
   ```

4. **API 错误**:
   ```
   刷新失败: API错误: 服务器内部错误
   ```

### 批量刷新结果

```
刷新完成!

成功: 8 个
失败: 2 个

失败详情:
user1@example.com: Token 已过期
user2@example.com: 网络连接失败
```

---

## 🚀 使用方法

### 刷新单个账户

1. 找到要刷新的账户卡片
2. 点击右上角的 🔄 按钮
3. 等待刷新完成
4. 查看更新后的信息

### 刷新所有账户

1. 点击页面顶部的 "🔄 全部刷新" 按钮
2. 在确认对话框中点击 "确定"
3. 等待所有账户刷新完成
4. 查看刷新结果统计

---

## ✅ 测试建议

1. **正常刷新**: 使用有效 Token 的账户测试刷新功能
2. **Token 过期**: 测试 Token 过期时的错误处理
3. **无 Token**: 测试没有 Token 的账户刷新行为
4. **批量刷新**: 测试多个账户的批量刷新功能
5. **网络错误**: 测试网络断开时的错误处理

---

## 🎉 总结

账户信息刷新功能已完整实现,包括:
- ✅ 单个账户刷新
- ✅ 批量刷新所有账户
- ✅ 完善的错误处理
- ✅ 友好的用户界面
- ✅ 实时数据更新
- ✅ 持久化保存

现在用户可以随时刷新账户信息,确保显示的数据始终是最新的! 🚀

