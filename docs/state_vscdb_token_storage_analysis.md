# VS Code state.vscdb 数据库 Token 存储机制完整分析

> **重要发现**：VS Code 的 SecretStorage API **实际上将加密数据存储在 state.vscdb SQLite 数据库中**，而不是独立的文件或系统密钥链。

---

## 一、实际存储位置

### 1. 数据库文件位置

**Windows 10**：
```
C:\Users\<用户名>\AppData\Roaming\Code\User\globalStorage\state.vscdb
```

**macOS**：
```
~/Library/Application Support/Code/User/globalStorage/state.vscdb
```

**Linux**：
```
~/.config/Code/User/globalStorage/state.vscdb
```

### 2. 验证信息

```
数据库路径: C:\Users\Administrator\AppData\Roaming\Code\User\globalStorage\state.vscdb
文件大小: 266,240 bytes
数据库类型: SQLite 3.x
```

---

## 二、数据库结构

### 1. 表结构

```sql
-- 主存储表
CREATE TABLE ItemTable (
    key TEXT PRIMARY KEY,
    value BLOB
);

-- 游标存储表
CREATE TABLE cursorDiskKV (
    key TEXT PRIMARY KEY,
    value BLOB
);
```

### 2. 存储统计

```
总记录数: 185+ 条
SecretStorage 记录数: 6 条（包含 GitHub, Microsoft, Augment, Tongyi Lingma, Verdent）
Verdent 相关记录数: 3 条
```

---

## 三、Verdent Token 实际存储格式

### 1. 数据库键（Key）

**SecretStorage 键格式**：
```
secret://{"extensionId":"verdentai.verdent","key":"verdent_ycAuthToken"}
```

**结构说明**：
- **协议前缀**：`secret://`
- **扩展ID**：`verdentai.verdent`
- **密钥名称**：`verdent_ycAuthToken`（带 `verdent_` 前缀）

### 2. 数据库值（Value）

**存储格式**：JSON 字符串（表示加密的 Buffer）

```json
{
  "type": "Buffer",
  "data": [118,49,48,227,53,177,180,234,135,59,100,12,89,197,198,35,245,126,149,46,...]
}
```

**值分析**：
- **总长度**：981 bytes（JSON 字符串长度）
- **实际数据**：`data` 数组包含加密后的字节
- **加密前缀**：`[118,49,48]` = `0x76 0x31 0x30` = ASCII `"v10"`

### 3. 加密数据结构

**十六进制表示**（前 64 字节）：
```
763130 e335b1b4ea873b640c59c5c62335f57e952e21157fd27484
5dc6a3a6802898424264aacc863db76969798b8b49ccef2992
6b4c6f1f99a9fdf3b8bb7faae5a9df4beefd0b8e2a...
```

**解析**：
```
76 31 30  →  'v' '1' '0'  →  版本标识 "v10"
e3 35 b1 b4 ea 87 3b 64...  →  加密数据（DPAPI 加密）
```

---

## 四、完整的存储流程

### 1. 扩展代码调用（TypeScript）

**保存 Token**：
```javascript
// extension/dist/extension.js:632960
async function Gi(t, e, i) {
  i ? await t.secrets.store(z_ + e, i)  // z_ = "verdent_"
    : await t.secrets.delete(z_ + e);
}

// 调用示例
await Gi(context, "ycAuthToken", tokenString);
```

### 2. VS Code SecretStorage API 处理

**内部流程**：
```
1. 接收参数: extensionId="verdentai.verdent", key="verdent_ycAuthToken", value=tokenString

2. 构造存储键:
   key = 'secret://{"extensionId":"verdentai.verdent","key":"verdent_ycAuthToken"}'

3. 加密值（Windows DPAPI）:
   - 调用 CryptProtectData API
   - 添加 "v10" 版本前缀
   - 生成加密字节数组

4. 序列化为 JSON:
   value = '{"type":"Buffer","data":[118,49,48,227,53,...]}'

5. 写入 state.vscdb:
   INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)
```

### 3. 数据库实际存储

**SQL 查询结果**：
```sql
SELECT key, value FROM ItemTable 
WHERE key = 'secret://{"extensionId":"verdentai.verdent","key":"verdent_ycAuthToken"}';
```

**结果**：
```
key   = secret://{"extensionId":"verdentai.verdent","key":"verdent_ycAuthToken"}
value = {"type":"Buffer","data":[118,49,48,227,53,177,180,234,...]} (981 bytes)
```

---

## 五、加密机制详解

### 1. v10 加密版本

**版本标识**：
- **前 3 字节**：`0x76 0x31 0x30` (ASCII "v10")
- **含义**：VS Code SecretStorage 加密格式版本 10

### 2. Windows DPAPI 加密

**Windows Data Protection API**：
```c
// Windows API 调用
BOOL CryptProtectData(
  DATA_BLOB *pDataIn,           // 原始 token 字符串
  LPCWSTR szDataDescr,          // 描述（可选）
  DATA_BLOB *pOptionalEntropy,  // 额外熵（可选）
  PVOID pvReserved,
  CRYPTPROTECT_PROMPTSTRUCT *pPromptStruct,
  DWORD dwFlags,                // CRYPTPROTECT_UI_FORBIDDEN
  DATA_BLOB *pDataOut           // 输出加密数据
);
```

**加密特性**：
- ✅ **用户级加密**：绑定到当前 Windows 用户账户
- ✅ **机器绑定**：绑定到当前计算机
- ✅ **自动密钥管理**：系统自动管理主密钥
- ❌ **不可迁移**：无法在不同机器或用户间迁移

### 3. 解密过程

**读取 Token**：
```javascript
// extension/dist/extension.js:632969
async function Zn(t, e) {
  return await t.secrets.get(z_ + e);
}

// 调用
let token = await Zn(context, "ycAuthToken");
```

**VS Code 内部处理**：
```
1. 从 state.vscdb 读取加密数据
   key = 'secret://{"extensionId":"verdentai.verdent","key":"verdent_ycAuthToken"}'
   
2. 解析 JSON 获取 Buffer 数组
   encryptedData = [118,49,48,227,53,177,180,234,...]
   
3. 移除 "v10" 前缀
   dpapi_data = encryptedData.slice(3)
   
4. 调用 Windows DPAPI 解密
   CryptUnprotectData(dpapi_data) → 原始 token 字符串
   
5. 返回给扩展
   return tokenString;
```

---

## 六、其他存储在 state.vscdb 中的 Verdent 数据

### 1. GlobalState 配置

**键**：`VerdentAI.verdent`

**值**：JSON 字符串（8,856 bytes）

**内容示例**：
```json
{
  "verdent-ai-agent-config": {
    "deviceId": "41746e3e-21df-47ff-9e39-5ac4f8f1cb1c",
    "projectId__f:\\Trace\\TEST\\test\\Datasette编辑器": "61cd52ae1c246ad353cfe6202b842261",
    "projectId__undefined": "d8e1ef2ee9f323..."
  }
}
```

**说明**：
- 非加密存储（明文 JSON）
- 包含设备 ID、项目 ID 等配置信息

### 2. UI 状态

**键**：`workbench.view.extension.verdent-ActivityBar.state.hidden`

**值**：
```json
[{"id":"verdent.SidebarProvider","isHidden":false}]
```

**说明**：
- 记录侧边栏视图的显示/隐藏状态

---

## 七、安全性分析

### 1. 加密强度

| 层级 | 机制 | 强度 |
|------|------|------|
| **操作系统层** | Windows DPAPI（AES-256） | ⭐⭐⭐⭐⭐ |
| **用户绑定** | 当前用户账户 | ⭐⭐⭐⭐⭐ |
| **机器绑定** | 当前计算机硬件 | ⭐⭐⭐⭐⭐ |
| **文件权限** | 仅当前用户可读写 | ⭐⭐⭐⭐ |
| **进程隔离** | VS Code 进程访问 | ⭐⭐⭐⭐ |

### 2. 安全优势

✅ **操作系统级加密**：
- Windows DPAPI 使用 AES-256 加密
- 主密钥由操作系统管理，存储在受保护的注册表中

✅ **用户账户绑定**：
- 加密数据绑定到当前 Windows 用户账户
- 其他用户即使访问文件也无法解密

✅ **机器绑定**：
- 加密数据包含机器特征信息
- 无法简单复制到另一台机器使用

✅ **透明管理**：
- 开发者无需手动管理密钥
- VS Code 自动处理加密/解密

### 3. 安全风险

⚠️ **本地管理员权限**：
- 拥有管理员权限的恶意软件可能访问 DPAPI 主密钥
- 需要物理访问 + 管理员权限

⚠️ **内存转储**：
- Token 解密后以明文存在于内存中
- 内存转储可能泄露 token

⚠️ **调试器附加**：
- 调试 VS Code 进程可能读取内存中的 token
- 需要用户权限 + 调试器

⚠️ **不可迁移性**：
- 换机器后需要重新登录
- 无法导出/导入加密的 token

### 4. 与其他存储方式对比

| 存储方式 | 加密 | 可迁移 | 跨平台 | 安全性 |
|---------|------|--------|--------|--------|
| **state.vscdb (DPAPI)** | ✅ AES-256 | ❌ | ✅ (API统一) | ⭐⭐⭐⭐⭐ |
| **macOS Keychain** | ✅ AES-256 | ❌ | ✅ | ⭐⭐⭐⭐⭐ |
| **Linux Secret Service** | ✅ (取决于后端) | ❌ | ✅ | ⭐⭐⭐⭐ |
| **JSON 文件（明文）** | ❌ | ✅ | ✅ | ⭐ |
| **环境变量** | ❌ | ✅ | ✅ | ⭐⭐ |

---

## 八、实际验证代码

### 1. 读取 state.vscdb 数据库

```python
import sqlite3
import os
import json

# 连接数据库
appdata = os.environ.get('APPDATA')
db_path = os.path.join(appdata, r'Code\User\globalStorage\state.vscdb')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 查询 Verdent token
cursor.execute("""
    SELECT key, value FROM ItemTable 
    WHERE key LIKE '%ycAuthToken%'
""")
result = cursor.fetchone()

if result:
    key, value = result
    print(f"Key: {key}")
    
    # 解析 JSON
    data = json.loads(value)
    encrypted_bytes = bytes(data['data'])
    
    print(f"加密版本: {encrypted_bytes[:3].decode('ascii')}")
    print(f"总长度: {len(encrypted_bytes)} bytes")
    print(f"十六进制: {encrypted_bytes.hex()}")

conn.close()
```

### 2. 解析加密数据结构

```python
# 假设 encrypted_bytes 是从数据库读取的数据
version = encrypted_bytes[:3].decode('ascii')  # "v10"
dpapi_data = encrypted_bytes[3:]               # 实际加密数据

print(f"版本: {version}")
print(f"DPAPI 数据长度: {len(dpapi_data)}")
print(f"DPAPI 数据（前32字节）: {dpapi_data[:32].hex()}")

# 注意：实际解密需要调用 Windows DPAPI
# Python 示例（需要 pywin32）:
# from win32crypt import CryptUnprotectData
# decrypted = CryptUnprotectData(dpapi_data, None, None, None, 0)[1]
# token = decrypted.decode('utf-8')
```

### 3. Windows DPAPI 解密（需要 pywin32）

```python
try:
    import win32crypt
    
    # encrypted_bytes 来自数据库
    version = encrypted_bytes[:3]  # b'v10'
    dpapi_data = encrypted_bytes[3:]
    
    # 解密（仅在原加密用户/机器上有效）
    decrypted_data = win32crypt.CryptUnprotectData(
        dpapi_data, 
        None,  # entropy
        None,  # reserved
        None,  # prompt_struct
        0      # flags
    )
    
    # decrypted_data 是元组: (description, decrypted_bytes)
    token_string = decrypted_data[1].decode('utf-8')
    print(f"解密成功: {token_string}")
    
except ImportError:
    print("需要安装 pywin32: pip install pywin32")
except Exception as e:
    print(f"解密失败: {e}")
```

---

## 九、关键发现总结

### 1. 核心事实

✅ **Token 确实存储在 state.vscdb 数据库中**  
✅ **使用 SQLite ItemTable 表存储**  
✅ **键格式为 JSON 字符串（带 secret:// 前缀）**  
✅ **值格式为 JSON 序列化的 Buffer 数组**  
✅ **加密使用 Windows DPAPI（v10 版本）**  
✅ **加密数据前 3 字节为版本标识 "v10"**  

### 2. 误解澄清

❌ **误解 1**：SecretStorage 使用独立的文件或密钥链  
✅ **真相**：Windows 上使用 state.vscdb 数据库，但通过 DPAPI 加密

❌ **误解 2**：Token 以明文存储在数据库中  
✅ **真相**：Token 以 DPAPI 加密后存储，需要系统解密

❌ **误解 3**：可以手动复制 state.vscdb 到其他机器使用  
✅ **真相**：DPAPI 加密绑定用户和机器，无法跨机器使用

❌ **误解 4**：VS Code 扩展可以访问其他扩展的 secrets  
✅ **真相**：键包含扩展 ID，VS Code 提供隔离保护

### 3. 实际路径映射

| 说法 | 实际路径（Windows） |
|------|---------------------|
| "SecretStorage" | `%APPDATA%\Code\User\globalStorage\state.vscdb` |
| "globalState" | `%APPDATA%\Code\User\globalStorage\state.vscdb` |
| "扩展存储目录" | `%APPDATA%\Code\User\globalStorage\verdentai.verdent\` |

---

## 十、对 Verdent 开发的影响

### 1. 用户体验影响

**换机器需重新登录**：
- Token 无法跨机器迁移
- 建议：提供友好的重新登录流程

**多用户共享机器**：
- 每个 Windows 用户有独立的加密 token
- 不会互相干扰

### 2. 开发建议

**读取 Token**：
```javascript
// 正确方式：使用 VS Code API
let token = await context.secrets.get("verdent_ycAuthToken");

// 错误方式：直接读取数据库（无法解密）
// ❌ 不要尝试直接读取 state.vscdb
```

**存储敏感数据**：
```javascript
// 敏感数据（API keys, tokens）
await context.secrets.store("verdent_apiKey", apiKey);

// 非敏感配置
await context.globalState.update("verdent_userPreferences", {...});
```

**清理数据**：
```javascript
// 删除 secret
await context.secrets.delete("verdent_ycAuthToken");

// 清理 globalState
await context.globalState.update("VerdentAI.verdent", undefined);
```

### 3. 调试建议

**查看存储的数据**：
```python
# 使用 Python 脚本查看数据库
python f:\Trace\TEST\Verdent\test\verify_state_vscdb.py
```

**监控存储变化**：
```javascript
// VS Code 扩展中监听 secrets 变化
context.secrets.onDidChange(e => {
  console.log('Secret changed:', e.key);
});
```

---

## 十一、参考资料

### 1. 代码位置

| 功能 | 文件 | 行号 |
|------|------|------|
| SecretStorage 保存 | `extension/dist/extension.js` | 632960-632968 |
| SecretStorage 读取 | `extension/dist/extension.js` | 632969-632971 |
| Token 保存调用 | `extension/dist/extension.js` | 630489 |
| Token 读取调用 | `extension/dist/extension.js` | 629106 |
| 验证脚本 | `test/verify_state_vscdb.py` | - |

### 2. 官方文档

- [VS Code SecretStorage API](https://code.visualstudio.com/api/references/vscode-api#SecretStorage)
- [Windows DPAPI 文档](https://docs.microsoft.com/en-us/windows/win32/api/dpapi/)
- [SQLite 数据库](https://www.sqlite.org/index.html)

### 3. 验证方法

```bash
# 查看数据库文件
dir "%APPDATA%\Code\User\globalStorage\state.vscdb"

# 运行验证脚本
python f:\Trace\TEST\Verdent\test\verify_state_vscdb.py

# 使用 SQLite 工具查看
sqlite3 "%APPDATA%\Code\User\globalStorage\state.vscdb" "SELECT key FROM ItemTable WHERE key LIKE '%verdent%';"
```

---

## 结论

**VS Code 的 SecretStorage API 在 Windows 上的实际实现**：

1. **存储位置**：`state.vscdb` SQLite 数据库
2. **加密方式**：Windows DPAPI (AES-256)
3. **密钥格式**：`secret://{"extensionId":"...","key":"..."}`
4. **值格式**：JSON 序列化的 Buffer 数组（包含 "v10" 前缀 + DPAPI 加密数据）
5. **安全性**：用户级 + 机器级绑定，无法跨机器迁移

这个机制提供了**高度安全**的 token 存储，同时保持了**跨平台 API 一致性**（Windows/macOS/Linux 使用相同的 API，但底层实现不同）。

---

**文档生成时间**：2025-11-15  
**数据库验证**：已完成  
**加密格式**：v10 (DPAPI)  
**扩展版本**：verdentai.verdent-1.0.9
