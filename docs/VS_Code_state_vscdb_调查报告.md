# VS Code state.vscdb 数据库存储机制调查报告 
 
## 1. 数据库位置 
 
### 1.1 GlobalStorage 
- **路径**: `%C:\Users\Administrator\AppData\Roaming%\Code\User\globalStorage\state.vscdb` 
- **完整路径**: `C:\Users\Administrator\AppData\Roaming\Code\User\globalStorage\state.vscdb` 
- **大小**: 266,240 bytes 
- **备份**: state.vscdb.backup 
 
### 1.2 WorkspaceStorage 
- **路径**: `%C:\Users\Administrator\AppData\Roaming%\Code\User\workspaceStorage\<workspace-hash>\state.vscdb` 
- **示例**: `C:\Users\Administrator\AppData\Roaming\Code\User\workspaceStorage\7476a1a055604ef7636d79ce08179d1f\state.vscdb` 
- **大小**: 77,824 bytes 
 
### 1.3 其他相关目录 
- **globalStorage扩展目录**: `%C:\Users\Administrator\AppData\Roaming%\Code\User\globalStorage\verdentai.verdent\` 
  - `settings\subagent_settings.json` 
  - `checkpoints\` 
  - `tasks\` 
- **storage.json**: `%C:\Users\Administrator\AppData\Roaming%\Code\User\globalStorage\storage.json` (纯JSON格式) 
 
## 2. 数据库结构 
 
### 2.1 表结构 
``` 
表名: ItemTable 
- key: TEXT (主键) 
- value: BLOB (存储值) 
 
表名: cursorDiskKV 
- key: TEXT 
- value: BLOB 
``` 
 
### 2.2 记录统计 
- GlobalStorage ItemTable: 185 条记录 
- 包含 6 个加密的 Secret 条目 
 
## 3. SecretStorage API 实现 
 
### 3.1 存储格式 
Secret数据在ItemTable中的Key格式: 
``` 
secret://{\"extensionId\":\"^<extension-id^>\",\"key\":\"^<key-name^>\"} 
``` 
 
示例: 
``` 
secret://{\"extensionId\":\"verdentai.verdent\",\"key\":\"verdent_ycAuthToken\"} 
``` 
 
### 3.2 Value格式 
Value以JSON字符串存储,结构为: 
```json 
{ 
  \"type\": \"Buffer\", 
  \"data\": [118, 49, 48, 227, 53, ...] 
} 
``` 
 
### 3.3 加密机制 
- **加密版本**: v10 (前3字节为ASCII "v10") 
- **加密方式**: 使用操作系统原生加密 
  - Windows: DPAPI (Data Protection API) / Windows Credential Manager 
  - macOS: Keychain 
  - Linux: libsecret 
- **数据长度**: 266 bytes (对于verdent_ycAuthToken) 
 
## 4. Verdent扩展的存储数据 
 
### 4.1 GlobalStorage中的Verdent数据 
``` 
1. VerdentAI.verdent (普通状态) 
2. secret://{\"extensionId\":\"verdentai.verdent\",\"key\":\"verdent_ycAuthToken\"} (加密) 
3. workbench.view.extension.verdent-ActivityBar.state.hidden 
``` 
 
### 4.2 WorkspaceStorage中的Verdent数据 
``` 
1. VerdentAI.verdent 
2. memento/webviewView.verdent.SidebarProvider 
3. workbench.view.extension.verdent-ActivityBar.numberOfVisibleViews 
4. workbench.view.extension.verdent-ActivityBar.state 
``` 
 
## 5. 所有发现的Secret Keys 
``` 
1. secret://{\"extensionId\":\"alibaba-cloud.tongyi-lingma\",\"key\":\"cosyAuthSecret\"} 
2. secret://{\"extensionId\":\"alibaba-cloud.tongyi-lingma\",\"key\":\"secret.local.machine.variables\"} 
3. secret://{\"extensionId\":\"augment.vscode-augment\",\"key\":\"augment.sessions\"} 
4. secret://{\"extensionId\":\"verdentai.verdent\",\"key\":\"verdent_ycAuthToken\"} 
5. secret://{\"extensionId\":\"vscode.github-authentication\",\"key\":\"github.auth\"} 
6. secret://{\"extensionId\":\"vscode.microsoft-authentication\",\"key\":\"publicClients-AzureCloud\"} 
``` 
 
## 6. 加密数据分析 
 
### 6.1 Verdent Token加密数据详情 
``` 
Total Length: 266 bytes 
Version: v10 
Hex (前64字节): 
763130e335b1b4ea873b640c59c5c623f57e952e21157fd274845dc6a3a68028 
984246a4aacc863db7696979878b49cce1fcce1917a7b4322db6e32073947dcf 
``` 
 
### 6.2 加密特征 
- 无法直接UTF-8解码 
- 使用操作系统级加密,只能被当前用户在当前机器上解密 
- 数据格式不是标准的base64或hex编码 
 
## 7. globalState vs SecretStorage区别 
 
### 7.1 globalState 
- 存储在: ItemTable中,key为普通字符串 
- 加密: 否 
- 用途: 一般配置、UI状态、缓存数据 
- 示例: `VerdentAI.verdent`, `chat.currentLanguageModel.panel` 
 
### 7.2 SecretStorage 
- 存储在: ItemTable中,key以 `secret://` 开头 
- 加密: 是 (OS级加密) 
- 用途: 敏感信息(token、密码、API密钥) 
- 示例: `secret://{\"extensionId\":\"verdentai.verdent\",\"key\":\"verdent_ycAuthToken\"}` 
 
## 8. storage.json vs state.vscdb 
 
### 8.1 storage.json 
- **格式**: 纯JSON文本文件 
- **内容**: 窗口状态、主题、遥测ID等 
- **大小**: 7,391 bytes 
- **可读性**: 可直接阅读和编辑 
 
### 8.2 state.vscdb 
- **格式**: SQLite数据库 
- **内容**: 扩展状态、UI状态、加密的secrets 
- **大小**: 266,240 bytes (global) / 77,824 bytes (workspace) 
- **可读性**: 需要SQLite工具读取,secrets已加密 
 
## 9. 关键发现 
 
1. **SecretStorage不是独立的数据库或文件**,而是存储在state.vscdb的ItemTable中 
2. **Key格式特殊**: 使用 `secret://` URI scheme + JSON格式的元数据 
3. **加密版本v10**: 所有secrets都使用v10加密格式 
4. **平台相关加密**: 
   - Windows: DPAPI 
   - macOS: Keychain 
   - Linux: libsecret 
5. **两级存储**: 
   - globalStorage: 跨工作区的全局状态 
   - workspaceStorage: 特定工作区的状态 
6. **Verdent扩展的文件存储**: 除了数据库,还使用 `globalStorage\verdentai.verdent\` 目录存储文件 
 
## 10. 实际路径总结 
 
```plaintext 
%C:\Users\Administrator\AppData\Roaming%\Code\ 
├── User\ 
│   ├── globalStorage\ 
│   │   ├── state.vscdb          (主数据库,包含所有secrets) 
│   │   ├── state.vscdb.backup   (备份) 
│   │   ├── storage.json         (JSON格式的状态) 
│   │   └── verdentai.verdent\   (扩展文件存储) 
│   │       ├── settings\ 
│   │       ├── checkpoints\ 
│   │       └── tasks\ 
│   └── workspaceStorage\ 
│       └── <workspace-hash>\ 
│           ├── state.vscdb      (工作区数据库) 
│           └── workspace.json  (工作区配置) 
``` 
 
## 11. 数据库访问示例 (Python) 
 
```python 
import sqlite3 
import json 
 
# 连接数据库 
conn = sqlite3.connect(r'C:\Users\Administrator\AppData\Roaming\Code\User\globalStorage\state.vscdb') 
cursor = conn.cursor() 
 
# 查询所有secrets 
cursor.execute('SELECT key FROM ItemTable WHERE key LIKE \"secret://%%\"') 
for row in cursor.fetchall(): 
    print(row[0]) 
 
# 查询特定扩展的secret 
cursor.execute('SELECT value FROM ItemTable WHERE key LIKE \"secret://%%verdentai.verdent%%\"') 
row = cursor.fetchone() 
if row: 
    value_json = json.loads(row[0]) 
    data_bytes = bytes(value_json['data']) 
    # data_bytes 是加密的,需要OS解密API 
 
conn.close() 
``` 
 
## 12. 结论 
 
- VS Code的SecretStorage API使用state.vscdb数据库存储加密数据 
- 加密依赖操作系统原生API,安全性较高 
- 数据只能在同一用户、同一机器上解密 
- Verdent扩展正确使用了SecretStorage API存储ycAuthToken 
- 如需迁移或备份,需要特殊处理加密数据
