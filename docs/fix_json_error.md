# JSON Error 快速修复指南

## 错误描述
```
JSON error: trailing characters at line 149 column 2
```

## 问题原因
批量注册时多个线程同时写入 `accounts.json` 文件，导致文件内容损坏。

## 快速修复方案

### 方案 1：删除损坏的文件（推荐）

#### Windows PowerShell
```powershell
# 方法1：使用环境变量路径
Remove-Item "$env:APPDATA\ai.verdent.account-manager\accounts.json" -Force

# 方法2：直接指定路径（替换 YourUsername 为你的用户名）
Remove-Item "C:\Users\YourUsername\AppData\Roaming\ai.verdent.account-manager\accounts.json" -Force
```

#### Windows 命令提示符 (CMD)
```batch
del "%APPDATA%\ai.verdent.account-manager\accounts.json"
```

#### 手动删除
1. 按 `Win + R` 打开运行对话框
2. 输入 `%APPDATA%\ai.verdent.account-manager`
3. 删除 `accounts.json` 文件
4. 重新打开应用即可

### 方案 2：恢复备份文件

如果存在备份文件，可以恢复：

```powershell
# 检查是否有备份文件
Get-ChildItem "$env:APPDATA\ai.verdent.account-manager\*.backup"

# 如果有备份，恢复它
Copy-Item "$env:APPDATA\ai.verdent.account-manager\accounts.backup" -Destination "$env:APPDATA\ai.verdent.account-manager\accounts.json" -Force
```

### 方案 3：手动修复 JSON 文件

1. 打开文件：
   ```powershell
   notepad "$env:APPDATA\ai.verdent.account-manager\accounts.json"
   ```

2. 查看第 149 行附近的内容

3. 常见问题和修复方法：
   - **多余的逗号**：删除最后一个元素后的逗号
   - **不完整的记录**：删除不完整的账户记录
   - **重复的大括号**：删除多余的 `}` 或 `{`

4. 确保 JSON 格式正确：
   ```json
   {
     "accounts": [
       {
         "id": "xxx",
         "email": "xxx@xxx.com",
         "password": "xxx"
       }
     ],
     "last_sync": "2024-01-01T00:00:00Z"
   }
   ```

## 预防措施

### 已实施的代码修复
1. **文件锁机制**：防止多线程同时写入
2. **原子写入**：先写临时文件，再重命名
3. **自动备份**：每次写入前创建备份
4. **错误恢复**：自动从备份恢复

### 使用建议
1. **批量注册时降低并发数**：使用 1-2 个线程而不是 5 个
2. **分批注册**：一次注册 1-3 个账号，而不是一次注册很多
3. **定期备份**：手动备份 accounts.json 文件

## 验证修复

修复后，打开应用检查是否正常：

```powershell
# 查看文件内容（PowerShell）
Get-Content "$env:APPDATA\ai.verdent.account-manager\accounts.json" | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

如果能正常显示 JSON 内容，说明修复成功。

## 更新说明

最新版本已修复此问题，包含以下改进：
- ✅ 文件锁防止并发写入
- ✅ 原子写入防止文件损坏
- ✅ 自动备份和恢复机制
- ✅ JSON 格式验证

请更新到最新版本以避免此问题。
