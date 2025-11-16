# Windsurf 一键登录脚本使用指南

## 概述

`windsurf_direct_login.py` 是一个自动化登录脚本，可以通过 PKCE (Proof Key for Code Exchange) 流程直接获取授权码并启动 Windsurf 应用完成登录。

## 工作原理

脚本完整实现了 OAuth 2.0 PKCE 认证流程，**直接调用 API 获取访问令牌，不依赖扩展的回调验证**：

```
1. 生成 PKCE 参数
   ├─ code_verifier: 随机32字节十六进制字符串
   └─ code_challenge: SHA256(code_verifier) 的 Base64URL 编码

2. 请求授权码
   └─ POST https://login.verdent.ai/passport/pkce/auth
      ├─ Headers: Cookie (包含token)
      └─ Body: {"codeChallenge": "..."}

3. 交换访问令牌
   └─ POST https://login.verdent.ai/passport/pkce/callback
      ├─ Body: {"code": "...", "codeVerifier": "..."}
      └─ 返回: {"token": "..."}

4. 显示结果
   └─ 输出访问令牌供后续使用
```

### 为什么不直接触发扩展回调？

扩展会验证回调 URL 中的 `state` 参数必须与本地存储的 `authNonce` 匹配。由于脚本无法访问扩展的本地存储，直接触发 `windsurf://` 回调会导致验证失败并提示 "Authentication link is no longer valid"。

因此，本脚本采用**完整的 API 流程**直接获取访问令牌，绕过扩展的回调验证机制。

## 前置要求

### 1. Python 环境
- Python 3.7+
- 安装依赖包：
  ```bash
  pip install requests
  ```

### 2. 获取 Verdent Token

#### 方法一：从浏览器 Cookie 获取

1. 在浏览器中登录 [https://www.verdent.ai](https://www.verdent.ai)
2. 打开浏览器开发者工具 (F12)
3. 进入 **Application** (Chrome) 或 **存储** (Firefox) 标签
4. 找到 **Cookies** → `https://www.verdent.ai`
5. 复制 `token` 字段的值

示例 token 格式：
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo3NDk0NjAyMjQwNDMxODgyMjQsInZlcnNpb24iOjAsInRva2VuX3R5cGUiOiJhY2Nlc3MiLCJleHAiOjE3NjU1NDg3NjcsImlhdCI6MTc2Mjk1Njc2NywibmJmIjoxNzYyOTU2NzY3fQ.OitLM-5WcUtpKho115HqLXsk9x6OXr4qLrEh5IfYioM
```

#### 方法二：从网络请求中获取

1. 打开浏览器开发者工具 (F12)
2. 进入 **Network** (网络) 标签
3. 访问 Verdent 网站的任意页面
4. 查看请求头中的 `Cookie` 字段
5. 提取 `token=` 后面的值

## 使用方法

### 基本使用

```bash
cd f:\Trace\TEST\Verdent\verdentai.verdent-1.0.9\test
python windsurf_direct_login.py
```

按提示输入 token 即可。

### 高级使用 - 脚本集成

```python
from windsurf_direct_login import WindsurfDirectLogin

# 使用你的 token
token = "your_verdent_token_here"

# 创建登录处理器
login = WindsurfDirectLogin(token)

# 执行登录
success = login.login()

if success:
    print("登录成功!")
else:
    print("登录失败!")
```

### 自定义配置

```python
from windsurf_direct_login import WindsurfDirectLogin

class CustomLogin(WindsurfDirectLogin):
    def __init__(self, token: str):
        super().__init__(token)
        # 自定义认证服务器
        self.auth_url = "https://custom-auth-server.com/auth"
        # 自定义回调 scheme
        self.callback_scheme = "vscode://verdentai.verdent/auth"

# 使用自定义配置
login = CustomLogin(token)
login.login()
```

## 输出示例

成功执行时的输出：

```
============================================================
Windsurf 一键登录
============================================================

[1/4] 生成PKCE参数...
  Code Verifier: a1b2c3d4e5f6g7h8i9j0...
  Code Challenge: u_XntJU3a0PG-vqBew0lKFlfUnqhPKJ7gEmJNN67lZ8

[2/4] 请求授权码...
✓ 成功获取授权码: 893579761421287424

[3/4] 交换访问令牌...
✓ 成功获取访问令牌!

[4/4] 登录完成!

============================================================
访问令牌 (Access Token):
============================================================
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo3NDk0NjAy...
============================================================

✓ 登录成功!

说明:
  此脚本直接调用API获取访问令牌，不依赖扩展的回调验证。
  你可以使用这个 token 配置其他工具或进行 API 调用。

注意:
  如需在 Windsurf 扩展中使用，请通过扩展的登录界面操作。

============================================================
登录流程已完成!
============================================================
```

## 常见问题

### Q1: 提示 "✗ API返回错误"

**原因**: Token 无效或已过期

**解决方案**:
1. 重新从浏览器获取最新的 token
2. 确保 token 完整复制，没有多余的空格
3. 检查 token 是否已过期（通常有效期为30天）

### Q2: 提示 "✗ HTTP请求失败: 401"

**原因**: 认证失败

**解决方案**:
1. 确认 token 格式正确
2. 检查网络连接
3. 尝试在浏览器中重新登录获取新 token

### Q3: 获取到 token 后如何使用？

**回答**: 
脚本获取的是访问令牌（access token），你可以：

1. **用于 API 调用**:
   ```python
   import requests
   
   headers = {
       'Cookie': f'token={access_token}'
   }
   response = requests.get('https://agent.verdent.ai/api/endpoint', headers=headers)
   ```

2. **配置其他工具**: 
   将 token 配置到需要 Verdent 认证的其他工具中

3. **在扩展中使用**:
   注意：此脚本获取的 token 无法直接导入到 Windsurf 扩展中，因为扩展有自己的存储机制。如需在扩展中使用，请通过扩展的登录界面操作。

### Q4: 提示 "✗ 请求异常: Connection Error"

**原因**: 网络连接问题

**解决方案**:
1. 检查网络连接
2. 如果使用代理，确保代理配置正确
3. 尝试关闭 VPN 或代理

### Q5: 输入的 Token 和输出的 Token 有什么区别？

**回答**: 
- **输入的 Token**: 从浏览器 Cookie 获取的认证 token，用于验证你的身份
- **输出的 Access Token**: 通过 PKCE 流程交换得到的新访问令牌，可用于 API 调用

脚本不会存储任何 token，每次运行都需要重新输入。

## 安全注意事项

⚠️ **重要提示**:

1. **Token 保护**: Token 是敏感信息，不要分享给他人
2. **不要提交到版本控制**: 确保 token 不会被提交到 Git 仓库
3. **定期更换**: 建议定期重新登录获取新 token
4. **使用环境变量**: 在生产环境中使用环境变量存储 token

```python
import os

# 从环境变量读取 token
token = os.environ.get('VERDENT_TOKEN')
if not token:
    raise ValueError("请设置 VERDENT_TOKEN 环境变量")

login = WindsurfDirectLogin(token)
login.login()
```

## 技术细节

### PKCE 流程

1. **Code Verifier**: 
   - 长度: 64个字符 (32字节十六进制)
   - 生成方式: `secrets.token_hex(32)`

2. **Code Challenge**:
   - 算法: SHA256
   - 编码: Base64URL (无填充)
   - 计算: `BASE64URL(SHA256(code_verifier))`
   - **重要**: 必须先用标准 Base64 编码，然后手动替换字符：
     ```python
     # 正确方式（与扩展一致）
     challenge = base64.b64encode(sha256_hash).decode('ascii')
     challenge = challenge.replace('+', '-').replace('/', '_').rstrip('=')
     
     # 错误方式（会导致验证失败）
     challenge = base64.urlsafe_b64encode(sha256_hash).decode('ascii').rstrip('=')
     ```

3. **授权码交换**:
   - 扩展会使用 code 和 code_verifier (state) 向服务器交换 access token
   - 服务器验证: `SHA256(state) == challenge`

### API 端点

- **认证服务器**: `https://login.verdent.ai`
- **授权端点**: `/passport/pkce/auth`
- **Token 交换端点**: `/passport/pkce/callback` (由扩展调用)

### 回调 URL 格式

```
windsurf://verdentai.verdent/auth?code={auth_code}&state={code_verifier}
```

参数说明：
- `code`: 授权码（从 API 获取）
- `state`: PKCE code_verifier（用于后续 token 交换）

## 扩展阅读

- [OAuth 2.0 PKCE 规范](https://tools.ietf.org/html/rfc7636)
- [VS Code URI Handler API](https://code.visualstudio.com/api/references/vscode-api#window.registerUriHandler)
- [Verdent 认证流程文档](./verdent_auth_flow.md)

## 许可证

本脚本仅供学习和测试使用。
