# Token 自动提取功能

## 📋 功能概述

在 `verdent_auto_register.py` 脚本中添加了自动提取 token Cookie 的功能,在注册成功后自动从浏览器中获取 JWT token。

## ✨ 新增功能

### 1. Token 提取逻辑

注册成功并跳转到 dashboard 页面后,脚本会自动尝试以下三种方法提取 token:

#### 方法 1: 直接获取 token cookie (推荐)
```python
token_cookie = page.get_cookie('token')
if isinstance(token_cookie, dict):
    token = token_cookie.get('value')
```

#### 方法 2: 从所有 cookies 中查找
```python
all_cookies = page.cookies()
for cookie in all_cookies:
    if cookie.get('name') == 'token':
        token = cookie.get('value')
        break
```

#### 方法 3: 从 document.cookie 字符串解析
```python
cookie_str = page.run_js('return document.cookie')
# 解析: "token=xxx; other=yyy"
for cookie_part in cookie_str.split(';'):
    if cookie_part.strip().startswith('token='):
        token = cookie_part.split('=', 1)[1]
        break
```

### 2. 返回数据结构

修改后的账号信息包含完整的字段:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "test@mailto.plus",
  "password": "VerdentAI@2024",
  "register_time": "2024-01-15T10:30:00.123456",
  "status": "active",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "quota_remaining": null,
  "quota_total": null,
  "subscription_type": null,
  "expire_time": null,
  "last_updated": "2024-01-15T10:30:00.123456"
}
```

### 3. 日志输出

执行时会看到详细的 token 提取日志:

```
[*] 步骤 11: 提取 token Cookie...
[✓] Token (前50字符): eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2...
Token 长度: 234 字符
```

如果提取失败:
```
[!] 警告: 未找到 token cookie,尝试其他方法...
[!] 警告: 无法提取 token,可能需要手动登录获取
```

## 🔧 修改的文件

### `verdent_auto_register.py`

**修改位置**: `register_account` 方法,第 379-467 行

**主要改动**:

1. **添加导入** (第 13 行):
   ```python
   import uuid
   ```

2. **添加 token 提取逻辑** (第 388-430 行):
   - 三种提取方法的容错处理
   - 详细的日志输出
   - 异常处理

3. **完善返回数据** (第 433-448 行):
   - 添加 `id` 字段(UUID)
   - 添加 `token` 字段(提取的 JWT token)
   - 添加 `quota_total`、`subscription_type`、`last_updated` 字段
   - 保持与 Rust Account 结构体一致

4. **改进日志输出** (第 450-462 行):
   - 显示账号 ID
   - 显示 token 前 50 字符
   - 显示 token 长度

## 📊 Token 格式说明

### JWT Token 结构

提取的 token 是标准的 JWT (JSON Web Token) 格式:

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo3NDk0NjI5MDcyMjIzOTI4MzIsInZlcnNpb24iOjAsInRva2VuX3R5cGUiOiJhY2Nlc3MiLCJleHAiOjE3NjU3MTI1NzksImlhdCI6MTc2MzEyMDU3OSwibmJmIjoxNzYzMTIwNTc5fQ.iIqF7QZD9sFuRg6ijehnQYfq0a1hbEmLXKZlIQ-pcZA
```

**组成部分**:
1. **Header** (头部): `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9`
2. **Payload** (载荷): `eyJ1c2VyX2lkIjo3NDk0NjI5MDcyMjIzOTI4MzIsInZlcnNpb24iOjAsInRva2VuX3R5cGUiOiJhY2Nlc3MiLCJleHAiOjE3NjU3MTI1NzksImlhdCI6MTc2MzEyMDU3OSwibmJmIjoxNzYzMTIwNTc5fQ`
3. **Signature** (签名): `iIqF7QZD9sFuRg6ijehnQYfq0a1hbEmLXKZlIQ-pcZA`

**Payload 解码后的内容**:
```json
{
  "user_id": 7494629072223928320,
  "version": 0,
  "token_type": "access",
  "exp": 1765712579,
  "iat": 1763120579,
  "nbf": 1763120579
}
```

## 🎯 使用场景

### 1. 自动登录

提取的 token 可以直接用于 Verdent AI 的 API 认证:

```python
headers = {
    "Cookie": f"token={extracted_token}",
    "Authorization": f"Bearer {extracted_token}"
}
```

### 2. 账号管理

保存的 token 可以用于:
- 自动登录 VS Code 扩展
- 查询账号配额信息
- 刷新账号状态
- 验证账号有效性

### 3. 批量注册

批量注册时,每个账号都会自动提取并保存 token:

```bash
python verdent_auto_register.py --count 5 --output accounts.json
```

生成的 `accounts.json`:
```json
[
  {
    "id": "uuid-1",
    "email": "user1@mailto.plus",
    "token": "eyJhbGci..."
  },
  {
    "id": "uuid-2",
    "email": "user2@mailto.plus",
    "token": "eyJhbGci..."
  }
]
```

## ⚠️ 注意事项

### 1. Token 有效期

- JWT token 包含过期时间 (`exp` 字段)
- 通常有效期为 30 天
- 过期后需要重新登录获取新 token

### 2. 安全性

- Token 相当于账号密码,需要妥善保管
- 不要在公共场所或日志中明文显示完整 token
- 建议只显示前 50 字符用于调试

### 3. 提取失败处理

如果 token 提取失败:
- 账号仍然注册成功
- `token` 字段为 `null`
- 可以后续手动登录获取 token

## 🧪 测试方法

### 单个账号注册测试

```bash
python verdent_auto_register.py --count 1 --output test.json
```

检查 `test.json` 中是否包含 token 字段:
```bash
cat test.json | grep "token"
```

### 批量注册测试

```bash
python verdent_auto_register.py --count 3 --workers 2 --output batch.json
```

验证所有账号都有 token:
```python
import json
with open('batch.json') as f:
    accounts = json.load(f)
    for acc in accounts:
        print(f"{acc['email']}: {'有token' if acc['token'] else '无token'}")
```

## 📝 相关文件

- Python 脚本: `verdent_auto_register.py`
- Rust Account 结构: `Verdent_account_manger/src-tauri/src/account_manager.rs`
- 前端组件: `Verdent_account_manger/src/components/AccountManager.vue`

