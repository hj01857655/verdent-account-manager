# 跨平台自动依赖检测和安装解决方案

## 概述
创建了一个智能包装脚本 `verdent_auto_register_wrapper.py`，可以在各平台自动检测、安装依赖并运行主脚本。

## 功能特性

### ✅ 自动检测
1. **Python 版本检查**：确保 Python 3.7+
2. **pip 检查**：检测并自动安装 pip
3. **依赖包检查**：自动安装缺失的包
4. **Chrome 浏览器检查**：检测浏览器安装位置

### ✅ 自动安装
1. **pip 自动安装**：如果缺失，自动下载并安装
2. **依赖包自动安装**：自动运行 `pip install`
3. **错误恢复**：提供详细的手动安装指引

### ✅ 跨平台支持
- **Windows**：支持多种 pip 命令格式
- **macOS**：使用 python3 和 pip3
- **Linux**：兼容各种发行版

## 实现细节

### 1. 包装脚本 (verdent_auto_register_wrapper.py)

```python
# 主要功能模块

def check_python_version():
    """检查 Python 版本是否 >= 3.7"""
    
def check_pip():
    """检查 pip 是否安装，未安装则自动安装"""
    
def check_and_install_package(package_name):
    """检查并自动安装 Python 包"""
    
def check_chrome():
    """检查 Chrome 浏览器安装位置"""
    
def install_dependencies():
    """安装所有必需的依赖"""
    
def run_main_script():
    """运行主脚本，传递所有参数"""
```

### 2. 构建配置更新

#### build.yml
```yaml
# Windows: 打包为 exe
- name: 打包 Python 脚本为 exe (Windows)
  run: pyinstaller verdent_auto_register.py

# macOS/Linux: 复制两个脚本
- name: 准备 Python 脚本资源 (非 Windows)
  run: |
    cp verdent_auto_register.py Verdent_account_manger/resources/
    cp verdent_auto_register_wrapper.py Verdent_account_manger/resources/
```

#### tauri.conf.json
```json
"resources": [
  "../resources/verdent_auto_register.exe",       // Windows
  "../../verdent_auto_register.py",               // 主脚本
  "../../verdent_auto_register_wrapper.py"        // 包装脚本
]
```

### 3. 查找逻辑更新 (commands.rs)
```rust
// 优先查找包装脚本
1. 查找 verdent_auto_register_wrapper.py
2. 如果没有，查找 verdent_auto_register.py
3. Windows 仍然使用 .exe
```

## 运行流程

### Windows
```
用户点击注册
  ↓
运行 verdent_auto_register.exe
  ↓
直接执行（所有依赖已打包）
```

### macOS/Linux
```
用户点击注册
  ↓
运行 python3 verdent_auto_register_wrapper.py
  ↓
检查 Python 版本
  ↓
检查并安装 pip (如需要)
  ↓
检查并安装 requests (如需要)
  ↓
检查并安装 DrissionPage (如需要)
  ↓
检查 Chrome 浏览器
  ↓
运行主脚本 verdent_auto_register.py
```

## 错误处理

### 场景 1：Python 未安装
```
❌ Python 版本过低: 2.7.18
需要 Python 3.7 或更高版本
请访问 https://www.python.org 下载最新版本
```

### 场景 2：pip 未安装
```
❌ pip 未安装
尝试安装 pip...
✓ pip 安装成功
```

### 场景 3：依赖包未安装
```
⚠ DrissionPage 未安装，尝试自动安装...
执行: python3 -m pip install DrissionPage
✓ DrissionPage 安装成功
```

### 场景 4：Chrome 未安装
```
⚠ 未找到 Chrome 浏览器
请安装 Chrome 浏览器:
macOS: brew install --cask google-chrome
Linux: sudo apt install google-chrome-stable
```

## 测试验证

### Windows 测试
```powershell
# 直接运行
python verdent_auto_register_wrapper.py --count 1
```

### macOS 测试
```bash
# 清理环境
pip3 uninstall requests DrissionPage -y

# 运行包装脚本（会自动安装依赖）
python3 verdent_auto_register_wrapper.py --count 1
```

### Linux 测试
```bash
# 在干净的 Docker 容器中测试
docker run -it ubuntu:22.04 bash
apt update && apt install python3
python3 verdent_auto_register_wrapper.py --count 1
```

## 优势

### ✅ 用户体验
1. **零配置**：用户无需手动安装依赖
2. **自动恢复**：依赖缺失时自动安装
3. **友好提示**：清晰的错误信息和解决方案

### ✅ 可靠性
1. **多重检测**：多种方式查找 pip 和 Chrome
2. **错误处理**：每步都有错误处理和回退方案
3. **超时保护**：安装过程有超时限制

### ✅ 兼容性
1. **Python 2/3**：正确处理版本差异
2. **pip 变体**：支持 pip、pip3、python -m pip
3. **系统差异**：适配不同系统的路径和命令

## 限制和注意事项

### 限制
1. **网络依赖**：需要网络连接来下载包
2. **权限要求**：可能需要管理员权限安装依赖
3. **Chrome 依赖**：无法自动安装 Chrome 浏览器

### 注意事项
1. **首次运行较慢**：需要下载和安装依赖
2. **代理设置**：企业环境可能需要配置代理
3. **虚拟环境**：在虚拟环境中可能有不同行为

## 未来改进

1. **离线支持**：打包依赖的 wheel 文件
2. **进度显示**：安装过程的进度条
3. **并行安装**：同时安装多个包
4. **Chrome 自动下载**：自动下载便携版 Chrome
5. **缓存机制**：缓存已安装的包信息

## 总结

通过包装脚本方案，实现了：
- ✅ **Windows**：完全打包，开箱即用
- ✅ **macOS**：自动检测和安装依赖
- ✅ **Linux**：自动检测和安装依赖

用户在任何平台上都能获得良好的体验，即使没有预装依赖也能自动完成配置。
