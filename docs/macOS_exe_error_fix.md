# macOS 无法运行 .exe 文件错误修复

## 错误描述
```
运行模式: 生产模式
可执行文件: /Applications/Verdent账号管理器.app/Contents/Resources/_up_/resources/verdent_auto_register.exe
启动 Python 进程失败: Permission denied (os error 13)
```

## 问题原因
在 macOS 系统上错误地尝试运行 Windows 的 `.exe` 可执行文件。macOS 不支持运行 Windows 可执行文件。

## 解决方案

### 代码修复（已完成）

修改了 `commands.rs` 中的文件查找逻辑：

1. **平台检测**：
   - Windows：查找 `.exe` 文件
   - macOS/Linux：查找 `.py` Python 脚本

2. **资源配置更新**：
   在 `tauri.conf.json` 中同时包含两种资源：
   ```json
   "resources": [
     "../resources/verdent_auto_register.exe",  // Windows 使用
     "../../verdent_auto_register.py"           // macOS/Linux 使用
   ]
   ```

3. **执行逻辑修改**：
   - Windows：直接运行 `.exe`
   - macOS：使用 `python3` 运行 `.py` 脚本

### 临时解决方案

如果已经安装了包含错误的版本，可以手动修复：

1. **复制 Python 脚本到应用资源目录**：
   ```bash
   # 查找应用资源目录
   cd /Applications/Verdent账号管理器.app/Contents/Resources
   
   # 下载或复制 Python 脚本
   curl -o verdent_auto_register.py https://raw.githubusercontent.com/your-repo/Verdent/main/verdent_auto_register.py
   
   # 添加执行权限
   chmod +x verdent_auto_register.py
   ```

2. **使用开发模式运行**：
   ```bash
   # 直接在项目目录运行
   cd /path/to/Verdent
   python3 verdent_auto_register.py --count 1
   ```

### 重新构建应用

修复代码后，重新构建 macOS 应用：

```bash
# 进入项目目录
cd Verdent_account_manger

# 清理旧构建
cargo clean

# 为 macOS 构建
npm run tauri build -- --target universal-apple-darwin

# 或者只为当前架构构建
npm run tauri build
```

### 验证修复

1. **检查资源文件**：
   ```bash
   ls -la /Applications/Verdent账号管理器.app/Contents/Resources/
   # 应该看到 verdent_auto_register.py 而不是 .exe
   ```

2. **测试运行**：
   打开应用，尝试自动注册功能

## 相关配置

### commands.rs 关键代码
```rust
if cfg!(target_os = "macos") || cfg!(target_os = "linux") {
    // macOS/Linux: 查找 Python 脚本
    let script_candidates = vec![
        resource_path.join("verdent_auto_register.py"),
        // ...
    ];
}
```

### Python 依赖安装
```bash
# macOS 需要安装 Python 和依赖
brew install python3
pip3 install DrissionPage requests
```

## 注意事项

1. **Python 版本**：macOS 使用 `python3` 命令，不是 `python`
2. **Chrome 浏览器**：DrissionPage 需要 Chrome 浏览器
3. **权限问题**：Python 脚本需要执行权限

## 长期解决方案

考虑使用 PyInstaller 为 macOS 创建原生可执行文件：

```bash
# 安装 PyInstaller
pip3 install pyinstaller

# 创建 macOS 可执行文件
pyinstaller --onefile --windowed verdent_auto_register.py

# 生成的文件在 dist/ 目录下
```

这样可以避免依赖 Python 环境。
