# macOS 系统自动注册权限错误解决方案

## 错误描述
```
自动注册失败: Permission denied (os error 13)
```

## 问题原因
在 macOS 系统上执行 Verdent 自动注册功能时，由于以下原因导致权限被拒绝：

1. **Python 脚本缺少执行权限**
2. **macOS 安全机制阻止**（Gatekeeper、SIP等）
3. **Python 命令差异**（macOS 使用 `python3` 而非 `python`）
4. **文件系统权限限制**

## 解决方案

### 方案 1：添加执行权限（推荐）

在终端中执行以下命令：

```bash
# 进入 Verdent 项目目录
cd /path/to/Verdent

# 给 Python 脚本添加执行权限
chmod +x verdent_auto_register.py

# 确认权限已添加
ls -la verdent_auto_register.py
# 应该看到类似：-rwxr-xr-x
```

### 方案 2：检查 Python 环境

```bash
# 检查 Python 是否安装
python3 --version

# 如果未安装，使用 Homebrew 安装
brew install python3

# 安装必需的 Python 包
pip3 install DrissionPage requests
```

### 方案 3：macOS 系统安全设置

1. **允许终端完全磁盘访问**：
   - 打开"系统偏好设置" → "安全性与隐私"
   - 选择"隐私"标签页
   - 左侧选择"完全磁盘访问权限"
   - 点击左下角的锁图标解锁
   - 点击 "+" 添加终端应用（Terminal.app 或 iTerm.app）

2. **如果使用 VS Code**：
   - 同样添加 VS Code 到"完全磁盘访问权限"列表

3. **临时禁用 Gatekeeper**（仅用于测试）：
   ```bash
   # 允许任何来源的应用运行（谨慎使用）
   sudo spctl --master-disable
   
   # 测试完成后重新启用
   sudo spctl --master-enable
   ```

### 方案 4：代码层面的修复（已实施）

已经在 `commands.rs` 中修改了代码，自动检测操作系统：

```rust
// macOS 使用 python3，Windows 使用 python
let python_cmd = if cfg!(target_os = "macos") { 
    "python3" 
} else { 
    "python" 
};
```

### 方案 5：使用绝对路径执行

如果上述方法都不行，可以尝试使用 Python 的完整路径：

```bash
# 查找 python3 的完整路径
which python3
# 例如：/usr/local/bin/python3

# 临时修改 commands.rs 使用绝对路径
let python_cmd = "/usr/local/bin/python3";
```

## 验证修复

### 1. 手动测试 Python 脚本

```bash
# 在 Verdent 目录下执行
python3 verdent_auto_register.py --count 1 --output test.json
```

如果能够正常运行，说明 Python 环境没有问题。

### 2. 在 Tauri 应用中测试

```bash
# 进入账户管理器目录
cd Verdent_account_manger

# 重新编译运行
npm run tauri dev
```

然后在应用中：
1. 切换到"账户管理"标签页
2. 点击"➕ 自动注册"
3. 设置参数并点击"开始注册"
4. 查看控制台输出

## 常见问题

### Q1：修改权限后仍然报错
**答**：可能需要重启 Tauri 应用或重新编译：
```bash
# 清理并重新编译
cargo clean
npm run tauri dev
```

### Q2：提示 Python 模块未找到
**答**：安装必需的依赖：
```bash
pip3 install DrissionPage requests
```

### Q3：浏览器无法启动
**答**：DrissionPage 需要 Chrome 或 Chromium：
```bash
# 使用 Homebrew 安装 Chrome
brew install --cask google-chrome
```

### Q4：在生产环境中如何处理
**答**：生产环境应该：
1. 将 Python 脚本打包成可执行文件（使用 PyInstaller）
2. 对可执行文件进行代码签名
3. 在安装时请求必要的权限

## 长期解决方案

为了避免此类问题，建议：

1. **使用 PyInstaller 打包**：
   ```bash
   pip3 install pyinstaller
   pyinstaller --onefile verdent_auto_register.py
   ```

2. **代码签名**（需要 Apple 开发者账号）：
   ```bash
   codesign --sign "Developer ID" verdent_auto_register
   ```

3. **在 Tauri 配置中声明权限**：
   修改 `tauri.conf.json` 添加必要的权限声明

## 联系支持

如果问题仍未解决，请提供以下信息：
- macOS 版本（`sw_vers`）
- Python 版本（`python3 --version`）
- 完整的错误日志
- 执行 `ls -la verdent_auto_register.py` 的输出
