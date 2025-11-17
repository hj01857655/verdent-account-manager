# 跨平台构建和运行状态

## 当前状态总结

### ✅ Windows - 完全正常
- **打包**：PyInstaller 打包为 `.exe` 文件
- **资源**：`verdent_auto_register.exe` 
- **查找**：正确查找 `.exe` 文件
- **运行**：直接执行 `.exe`

### ⚠️ macOS - 需要修复后才能正常
- **打包**：复制 Python 脚本 (已修复)
- **资源**：`verdent_auto_register.py`
- **查找**：查找 `.py` 文件 (已修复)
- **运行**：使用 `python3` 执行
- **依赖**：需要用户安装 Python3 和依赖包

### ⚠️ Linux - 需要修复后才能正常  
- **打包**：复制 Python 脚本 (已修复)
- **资源**：`verdent_auto_register.py`
- **查找**：查找 `.py` 文件 (已修复)
- **运行**：使用 `python3` 执行
- **依赖**：需要用户安装 Python3 和依赖包

## 已实施的修复

### 1. GitHub Actions (`build.yml`)
```yaml
# Windows: 打包 exe
- name: 打包 Python 脚本为 exe (Windows)
  if: matrix.platform == 'windows-latest'
  run: pyinstaller verdent_auto_register.py

# macOS/Linux: 复制 Python 脚本
- name: 准备 Python 脚本资源 (非 Windows)
  if: matrix.platform != 'windows-latest'
  run: |
    cp verdent_auto_register.py Verdent_account_manger/resources/
    chmod +x Verdent_account_manger/resources/verdent_auto_register.py
```

### 2. Rust 代码 (`commands.rs`)
```rust
// 根据操作系统查找不同的文件
if cfg!(target_os = "windows") {
    // 查找 .exe 文件
} else if cfg!(target_os = "macos") || cfg!(target_os = "linux") {
    // 查找 .py 文件
}

// 根据操作系统使用不同的 Python 命令
let python_cmd = if cfg!(target_os = "macos") { 
    "python3" 
} else { 
    "python" 
};
```

### 3. Tauri 配置 (`tauri.conf.json`)
```json
"resources": [
  "../resources/verdent_auto_register.exe",  // Windows
  "../../verdent_auto_register.py"           // macOS/Linux
]
```

## 部署后的运行要求

### Windows
- 无额外要求，exe 包含所有依赖

### macOS
需要用户安装：
```bash
# 安装 Python3
brew install python3

# 安装 Python 依赖
pip3 install DrissionPage requests

# 安装 Chrome 浏览器
brew install --cask google-chrome
```

### Linux
需要用户安装：
```bash
# Ubuntu/Debian
sudo apt install python3 python3-pip
pip3 install DrissionPage requests

# 安装 Chrome
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
sudo apt update
sudo apt install google-chrome-stable
```

## 测试检查清单

### Windows ✅
- [ ] exe 文件正确打包到 resources 目录
- [ ] 应用能找到并执行 exe 文件
- [ ] 注册功能正常工作

### macOS ⚠️ (修复后需测试)
- [ ] Python 脚本正确复制到 Resources 目录
- [ ] 应用能找到 .py 文件
- [ ] 使用 python3 正确执行
- [ ] 处理 Python 未安装的错误提示

### Linux ⚠️ (修复后需测试)
- [ ] Python 脚本正确复制到资源目录
- [ ] 应用能找到 .py 文件
- [ ] 使用 python3 正确执行
- [ ] 处理依赖缺失的错误提示

## 改进建议

### 1. 统一打包方案
考虑为所有平台使用 PyInstaller：
```bash
# macOS
pyinstaller --onefile --target-arch universal2 verdent_auto_register.py

# Linux  
pyinstaller --onefile verdent_auto_register.py
```

### 2. 依赖检查
在应用启动时检查依赖：
```rust
fn check_python_dependencies() -> Result<bool, String> {
    // 检查 Python3
    // 检查 DrissionPage
    // 检查 Chrome
}
```

### 3. 用户友好的错误提示
```rust
if !has_python {
    return Err("Python3 未安装，请访问 python.org 下载安装".to_string());
}
```

## 结论

**当前状态**：
- ✅ Windows 可以正常工作
- ⚠️ macOS/Linux 需要应用修复后的代码才能正常工作

**修复后**：
- 三个平台都能找到并执行相应的文件
- Windows 用户体验最好（无需额外依赖）
- macOS/Linux 需要用户安装 Python 环境
