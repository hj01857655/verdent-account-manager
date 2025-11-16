# VS Code 插件 Token 存储机制 - 快速参考

## 核心发现：Token 存储在 state.vscdb 数据库中

### 一、实际存储位置

```
Windows: C:\Users\<用户名>\AppData\Roaming\Code\User\globalStorage\state.vscdb
macOS:   ~/Library/Application Support/Code/User/globalStorage/state.vscdb
Linux:   ~/.config/Code/User/globalStorage/state.vscdb
```

**数据库类型**：SQLite 3.x  
**文件大小**：~266 KB  
**表结构**：`ItemTable (key TEXT, value BLOB)`

---

### 二、Token 存储格式

#### 1. 数据库键（Key）
```
secret://{"extensionId":"verdentai.verdent","key":"verdent_ycAuthToken"}
```

#### 2. 数据库值（Value）
```json
{
  "type": "Buffer",
  "data": [118, 49, 48, 227, 53, 177, 180, 234, ...]
}
```
- **总长度**：981 bytes（JSON字符串）
- **data数组**：加密后的字节数组
- **前3字节**：`[118,49,48]` = `"v10"`（加密版本标识）

#### 3. 加密数据结构
```
十六进制: 763130e335b1b4ea873b640c59c5c623...
解析:     v  1  0  [DPAPI加密数据...]
```

---

### 三、加密方法

#### Windows DPAPI (Data Protection API)
- **算法**：AES-256
- **绑定**：当前用户账户 + 当前机器
- **特性**：
  - ✅ 操作系统级加密
  - ✅ 自动密钥管理
  - ✅ 用户隔离
  - ❌ **无法跨机器迁移**

#### 加密流程
```
原始Token字符串
    ↓
调用 CryptProtectData (Windows API)
    ↓
生成加密字节数组
    ↓
添加 "v10" 版本前缀 (3字节)
    ↓
序列化为 JSON Buffer 格式
    ↓
存入 state.vscdb 数据库
```

---

### 四、Token 读写流程

#### 保存流程
```javascript
// 1. 扩展代码调用 (extension.js:632960)
await context.secrets.store("verdent_ycAuthToken", tokenString);

// 2. VS Code 内部处理
//    - 构造键: secret://{"extensionId":"verdentai.verdent","key":"verdent_ycAuthToken"}
//    - 加密值: Windows DPAPI → [v10 + encrypted_data]
//    - 序列化: {"type":"Buffer","data":[...]}
//    - 写入: state.vscdb ItemTable
```

#### 读取流程
```javascript
// 1. 扩展代码调用 (extension.js:632969)
let token = await context.secrets.get("verdent_ycAuthToken");

// 2. VS Code 内部处理
//    - 从 state.vscdb 读取加密数据
//    - 解析 JSON Buffer
//    - 移除 "v10" 前缀
//    - 调用 CryptUnprotectData (Windows API)
//    - 返回原始 token 字符串
```

#### HTTP 请求使用
```javascript
// extension.js:629106
let token = await context.secrets.get("verdent_ycAuthToken");
headers: { Cookie: `token=${token}` }
```

---

### 五、数据库查询验证

#### SQL 查询
```sql
-- 查看所有 Verdent 相关数据
SELECT key, length(value) FROM ItemTable 
WHERE key LIKE '%verdent%';

-- 结果：
-- 1. secret://{"extensionId":"verdentai.verdent","key":"verdent_ycAuthToken"} | 981 bytes
-- 2. VerdentAI.verdent | 8856 bytes (GlobalState配置)
-- 3. workbench.view.extension.verdent-ActivityBar.state.hidden | 51 bytes
```

#### Python 验证脚本
```bash
python f:\Trace\TEST\Verdent\test\verify_state_vscdb.py
```

---

### 六、安全性分析

| 特性 | 评分 | 说明 |
|------|------|------|
| **加密强度** | ⭐⭐⭐⭐⭐ | AES-256 (DPAPI) |
| **用户隔离** | ⭐⭐⭐⭐⭐ | 绑定到Windows用户账户 |
| **机器绑定** | ⭐⭐⭐⭐⭐ | 绑定到当前计算机 |
| **文件权限** | ⭐⭐⭐⭐ | 仅当前用户可读写 |
| **可迁移性** | ❌ | 无法跨机器/用户迁移 |

**安全优势**：
- ✅ 操作系统级加密（DPAPI）
- ✅ 其他用户无法访问
- ✅ 复制文件到其他机器无法解密
- ✅ 自动密钥管理

**安全风险**：
- ⚠️ 本地管理员权限可能访问DPAPI主密钥
- ⚠️ 内存转储可能泄露解密后的token
- ⚠️ 调试VS Code进程可读取内存

---

### 七、与之前认知的对比

| 之前认为 | 实际情况 |
|---------|---------|
| SecretStorage 使用独立文件 | ❌ 存储在 state.vscdb 数据库中 |
| Windows 使用 Credential Manager | ❌ 使用 DPAPI 加密后存入数据库 |
| macOS 使用独立 Keychain | ❌ 也存储在 state.vscdb（但使用Keychain加密） |
| Token 明文存储 | ❌ 使用 v10 加密格式（DPAPI） |
| 可以复制数据库迁移 | ❌ DPAPI 绑定用户+机器，无法迁移 |

---

### 八、关键代码位置

| 功能 | 文件 | 行号 |
|------|------|------|
| SecretStorage 保存函数 | extension/dist/extension.js | 632960-632968 |
| SecretStorage 读取函数 | extension/dist/extension.js | 632969-632971 |
| 登录回调保存Token | extension/dist/extension.js | 630489 |
| 获取用户信息读取Token | extension/dist/extension.js | 629106 |
| PKCE生成（SHA256） | extension/dist/extension.js | 630365-630402 |
| URI回调处理 | extension/dist/extension.js | 635994-636029 |

---

### 九、实用命令

#### 查看数据库文件
```bash
# Windows
dir "%APPDATA%\Code\User\globalStorage\state.vscdb"

# 查看大小
dir "%APPDATA%\Code\User\globalStorage\state.vscdb" | findstr vscdb
```

#### SQLite 查询
```bash
# 安装 SQLite3
# 查询所有Verdent密钥
sqlite3 "%APPDATA%\Code\User\globalStorage\state.vscdb" ^
  "SELECT key FROM ItemTable WHERE key LIKE '%verdent%';"
```

#### Python 解密（需要 pywin32）
```python
import win32crypt
import sqlite3
import json
import os

# 读取数据库
db_path = os.path.join(os.environ['APPDATA'], 
                       r'Code\User\globalStorage\state.vscdb')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 查询token
cursor.execute("""
    SELECT value FROM ItemTable 
    WHERE key = 'secret://{"extensionId":"verdentai.verdent","key":"verdent_ycAuthToken"}'
""")
value = cursor.fetchone()[0]

# 解析JSON
data = json.loads(value)
encrypted_bytes = bytes(data['data'])

# 移除 "v10" 前缀
dpapi_data = encrypted_bytes[3:]

# 解密（仅在原加密机器+用户有效）
decrypted = win32crypt.CryptUnprotectData(dpapi_data, None, None, None, 0)
token = decrypted[1].decode('utf-8')

print(f"Token: {token}")
conn.close()
```

---

### 十、对多账号管理工具的影响

#### ✅ 可以做的
- 读取 `VerdentAI.verdent` 中的非加密配置
- 修改 `storage.json` 中的全局配置
- 管理 `verdentai.verdent\` 目录下的文件

#### ❌ 无法做的
- 直接读取/修改 state.vscdb 中的加密 token（无法解密）
- 将 token 复制到其他机器使用
- 绕过 VS Code API 访问 SecretStorage

#### 💡 解决方案
- **方案1**：通过 VS Code 扩展 API 间接操作
- **方案2**：使用 Python + pywin32 在同一机器/用户下解密
- **方案3**：让用户重新登录获取新 token

---

### 十一、完整认证流程

```
1. 用户点击登录
    ↓
2. 生成 PKCE 参数
   - authNonce = randomBytes(32).hex()
   - code_challenge = base64url(sha256(authNonce))
    ↓
3. 保存 nonce 到 SecretStorage
   - verdent_authNonce
   - verdent_authNonceTimestamp
    ↓
4. 打开浏览器登录页
   URL: https://verdent.ai/auth?challenge=...
    ↓
5. 用户登录并授权
    ↓
6. 浏览器回调 VS Code
   vscode://verdentai.verdent/auth?code=...&state=...
    ↓
7. VS Code URI Handler 捕获
    ↓
8. 交换 token
   POST https://login.verdent.ai/passport/pkce/callback
   Body: { code, codeVerifier: authNonce }
    ↓
9. 保存 token 到 SecretStorage
   await context.secrets.store("verdent_ycAuthToken", token)
    ↓
10. VS Code 加密并存入 state.vscdb
    Key: secret://{"extensionId":"verdentai.verdent","key":"verdent_ycAuthToken"}
    Value: {"type":"Buffer","data":[118,49,48,...]}  (v10 + DPAPI加密)
    ↓
11. 后续请求使用 Cookie
    Headers: { Cookie: `token=${token}` }
```

---

### 十二、总结

**核心答案**：

1. **保存位置**：`state.vscdb` SQLite 数据库（不是独立文件）
2. **保存方式**：JSON Buffer 格式（`{"type":"Buffer","data":[...]}`）
3. **加密方法**：Windows DPAPI (v10版本, AES-256)
4. **读取方式**：VS Code SecretStorage API → DPAPI解密 → 返回明文token
5. **安全级别**：⭐⭐⭐⭐⭐（用户+机器绑定，无法迁移）

**关键发现**：
- ✅ Token 确实在 `state.vscdb` 中
- ✅ 使用强加密（DPAPI）保护
- ✅ 跨平台 API 一致（底层实现不同）
- ❌ 无法简单复制到其他机器

---

**参考文档**：
- 完整分析：`f:/Trace/TEST/Verdent/docs/state_vscdb_token_storage_analysis.md`
- 验证脚本：`f:/Trace/TEST/Verdent/test/verify_state_vscdb.py`
- 项目路径：`f:\Trace\TEST\Verdent\verdentai.verdent-1.0.9\`

**生成时间**：2025-11-15  
**验证状态**：✅ 已通过数据库查询验证
