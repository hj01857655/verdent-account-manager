# 跨平台存储路径和回调命令差异

## 目录

- [VS Code 回调命令](#vs-code-回调命令)
- [账户数据存储](#账户数据存储)
- [用户设置存储](#用户设置存储)
- [VS Code 扩展存储](#vs-code-扩展存储)
- [临时文件存储](#临时文件存储)
- [存储结构对比表](#存储结构对比表)

## VS Code 回调命令

### URL Scheme（所有平台相同）
```
vscode://verdentai.verdent/auth?code={auth_code}&state={state}
```

### 打开方式（平台不同）

| 平台 | 命令 | 方式 |
|------|------|------|
| **Windows** | `rundll32 url.dll,FileProtocolHandler {url}` | 使用系统 URL 处理器 |
| **macOS** | `open {url}` | 使用系统默认打开方式 |
| **Linux** | `xdg-open {url}` | 使用 XDG 标准打开方式 |

### Windsurf 和 Cursor 支持
```
windsurf://verdentai.verdent/auth?code={auth_code}&state={state}
cursor://verdentai.verdent/auth?code={auth_code}&state={state}
```

## 账户数据存储

### 存储位置
所有平台都使用 `~/.verdent_accounts/` 目录，但实际路径不同：

| 平台 | 实际路径 | 环境变量 |
|------|---------|---------|
| **Windows** | `C:\Users\{username}\.verdent_accounts\` | `%USERPROFILE%` |
| **macOS** | `/Users/{username}/.verdent_accounts/` | `$HOME` |
| **Linux** | `/home/{username}/.verdent_accounts/` | `$HOME` |

### 文件结构
```
.verdent_accounts/
├── accounts.json           # 账户列表
├── accounts.backup         # 账户备份（自动创建）
├── user_settings.json      # 用户设置
└── user_settings.backup    # 设置备份
```

### accounts.json 示例
```json
{
  "accounts": [
    {
      "id": "uuid-here",
      "email": "user@example.com",
      "password": "encrypted",
      "token": "jwt-token",
      "register_time": "2024-01-01T00:00:00Z",
      "last_updated": "2024-01-01T00:00:00Z"
    }
  ],
  "last_sync": "2024-01-01T00:00:00Z"
}
```

## 用户设置存储

### 存储位置（与账户数据相同目录）

| 平台 | 路径 |
|------|------|
| **Windows** | `C:\Users\{username}\.verdent_accounts\user_settings.json` |
| **macOS** | `/Users/{username}/.verdent_accounts/user_settings.json` |
| **Linux** | `/home/{username}/.verdent_accounts/user_settings.json` |

### user_settings.json 示例
```json
{
  "auto_login": true,
  "remember_last_account": true,
  "theme": "dark",
  "language": "zh-CN",
  "auto_refresh_interval": 300,
  "show_notifications": true
}
```

## VS Code 扩展存储

### globalStorage 位置

| 平台 | 路径 | 说明 |
|------|------|------|
| **Windows** | `%APPDATA%\Code\User\globalStorage\storage.json` | AppData\Roaming 目录 |
| **macOS** | `~/Library/Application Support/Code/User/globalStorage/storage.json` | 应用支持目录 |
| **Linux** | `~/.config/Code/User/globalStorage/storage.json` | XDG 配置目录 |

### 扩展安装位置

| 平台 | 路径 |
|------|------|
| **Windows** | `%USERPROFILE%\.vscode\extensions\` |
| **macOS** | `~/.vscode/extensions/` |
| **Linux** | `~/.vscode/extensions/` |

### Verdent 扩展数据
```
verdentai.verdent-{version}/
├── package.json
├── extension.js
└── resources/
```

## 临时文件存储

### 自动注册输出文件

| 平台 | 临时目录 | 示例路径 |
|------|---------|---------|
| **Windows** | `%TEMP%` | `C:\Users\{user}\AppData\Local\Temp\verdent_register_{uuid}.json` |
| **macOS** | `/var/folders/...` | `/var/folders/xx/xxx/T/verdent_register_{uuid}.json` |
| **Linux** | `/tmp` | `/tmp/verdent_register_{uuid}.json` |

## 存储结构对比表

| 功能 | Windows | macOS | Linux | 备注 |
|------|---------|-------|-------|------|
| **账户数据** | `~\.verdent_accounts\` | `~/.verdent_accounts/` | `~/.verdent_accounts/` | 相对路径相同 |
| **用户设置** | 同账户目录 | 同账户目录 | 同账户目录 | 统一管理 |
| **VS Code 配置** | `%APPDATA%\Code\` | `~/Library/Application Support/Code/` | `~/.config/Code/` | 系统标准不同 |
| **扩展目录** | `~\.vscode\` | `~/.vscode/` | `~/.vscode/` | 相对路径相同 |
| **临时文件** | `%TEMP%` | `/var/folders/` | `/tmp/` | 系统临时目录 |

## 权限要求

### Windows
- 用户主目录：读写权限
- AppData：读写权限
- 注册表：无需（URL scheme 由安装程序处理）

### macOS
- 用户主目录：读写权限
- Library：读写权限
- 系统偏好设置：可能需要"完全磁盘访问权限"

### Linux
- 用户主目录：读写权限（755）
- .config 目录：读写权限
- /tmp：读写权限（通常是 1777）

## 迁移和备份

### 备份账户数据
```bash
# Windows
xcopy /E /I "%USERPROFILE%\.verdent_accounts" "D:\Backup\verdent"

# macOS/Linux
cp -r ~/.verdent_accounts ~/backup/verdent/
```

### 迁移到新系统
1. 复制 `.verdent_accounts` 整个目录
2. 保持相同的目录结构
3. 确保文件权限正确（特别是 Linux/macOS）

### 清理数据
```bash
# Windows
rmdir /S /Q "%USERPROFILE%\.verdent_accounts"
del "%APPDATA%\Code\User\globalStorage\storage.json"

# macOS/Linux
rm -rf ~/.verdent_accounts
rm -f ~/.config/Code/User/globalStorage/storage.json  # Linux
rm -f ~/Library/Application\ Support/Code/User/globalStorage/storage.json  # macOS
```

## 故障排查

### 常见问题

#### 1. Windows: 找不到存储文件
- 检查隐藏文件是否显示
- 使用 `dir /a` 查看所有文件

#### 2. macOS: 权限被拒绝
- 检查文件权限：`ls -la ~/.verdent_accounts`
- 修复权限：`chmod -R 755 ~/.verdent_accounts`

#### 3. Linux: 文件损坏
- 检查文件系统：`fsck`
- 恢复备份：`cp ~/.verdent_accounts/accounts.backup ~/.verdent_accounts/accounts.json`

### 调试命令

```bash
# 检查所有存储位置（跨平台）
# Windows PowerShell
Get-ChildItem "$env:USERPROFILE\.verdent_accounts" -Force
Get-ChildItem "$env:APPDATA\Code\User\globalStorage" -Force

# macOS/Linux
ls -la ~/.verdent_accounts/
ls -la ~/.config/Code/User/globalStorage/  # Linux
ls -la ~/Library/Application\ Support/Code/User/globalStorage/  # macOS
```

## 安全建议

1. **不要**将存储目录提交到版本控制
2. **定期**备份账户数据
3. **加密**敏感信息（密码、Token）
4. **限制**文件权限（特别是 Linux/macOS）
5. **清理**临时文件
