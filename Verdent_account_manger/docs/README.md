# Verdent账号管理器

一个使用Vue 3 + Rust + Tauri构建的跨平台桌面应用，用于一键自动登录Verdent AI并打开VS Code。

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)
![Version](https://img.shields.io/badge/version-1.0.0-green.svg)

## 📖 快速导航

- [功能特性](#功能特性)
- [快速开始](#快速开始)
- [使用说明](#使用说明)
- [开发指南](#开发指南)
- [文档](#文档)

## ✨ 功能特性

- 🔐 **一键登录**: 使用Token快速登录Verdent AI
- 🖥️ **跨平台支持**: Windows、macOS、Linux
- 🔄 **设备管理**: 重置设备身份，支持多账号切换
- 💾 **存储管理**: 查看和管理本地存储数据
- 🚀 **VS Code集成**: 自动打开VS Code回调链接
- 🎨 **现代UI**: 使用Vue 3构建的美观界面

## 🚀 快速开始

### Windows用户

1. **下载安装包**: `Verdent账号管理器-Setup.exe`
2. **运行安装程序**
3. **启动应用**

或使用开发模式:
```cmd
# 双击运行
start-dev.bat

# 或使用命令行
cd Verdent_account_manger
npm install
npm run tauri dev
```

### macOS/Linux用户

```bash
# 赋予执行权限
chmod +x start-dev.sh

# 运行开发服务器
./start-dev.sh
```

## 📚 使用说明

### 获取Token

1. 打开浏览器访问 `https://verdent.ai` 并登录
2. 按 `F12` 打开开发者工具
3. 切换到"应用程序/Application"标签
4. 找到 Cookie → `https://verdent.ai` → `token`
5. 复制token值

### 登录操作

1. 启动"Verdent账号管理器"
2. 在"Token"输入框粘贴token
3. (可选) 修改设备ID
4. 点击"登录"按钮
5. 等待成功提示

### 多账号切换

1. 切换到"存储管理"标签
2. 点击"重置设备身份"
3. 修改设备ID为新值
4. 使用新账号的token登录

详细说明请查看 [USER_GUIDE.md](USER_GUIDE.md)

## 🛠️ 技术栈

- **前端**: Vue 3 + TypeScript + Vite
- **后端**: Rust + Tauri 2.0
- **核心功能**:
  - PKCE认证流程
  - 本地存储管理
  - HTTP请求处理 (reqwest)
  - 加密哈希 (SHA256)

## 💻 开发指南

### 环境要求

- Node.js 18+
- Rust 1.70+
- Cargo

### 安装依赖

```bash
cd Verdent_account_manger
npm install
```

### 开发模式

```bash
# 方式1: 使用脚本
./start-dev.sh        # macOS/Linux
start-dev.bat         # Windows

# 方式2: 使用npm命令
npm run tauri dev
```

### 构建应用

```bash
# 方式1: 使用脚本
./build.sh            # macOS/Linux
build.bat             # Windows

# 方式2: 使用npm命令
npm run tauri build
```

构建产物位置:
- **Windows**: `src-tauri/target/release/bundle/msi/`
- **macOS**: `src-tauri/target/release/bundle/dmg/`
- **Linux**: `src-tauri/target/release/bundle/deb/`

## 📁 项目结构

```
Verdent_account_manger/
├── src/                    # Vue前端源码
│   ├── App.vue            # 主应用组件
│   ├── main.ts            # 应用入口
│   └── style.css          # 全局样式
├── src-tauri/             # Rust后端源码
│   ├── src/
│   │   ├── main.rs        # 程序入口
│   │   ├── lib.rs         # 库入口
│   │   ├── commands.rs    # Tauri命令
│   │   ├── api.rs         # API调用
│   │   ├── pkce.rs        # PKCE认证
│   │   └── storage.rs     # 存储管理
│   ├── Cargo.toml         # Rust依赖
│   └── tauri.conf.json    # Tauri配置
├── package.json           # NPM依赖
├── vite.config.ts         # Vite配置
├── start-dev.sh/bat       # 开发启动脚本
└── build.sh/bat           # 构建脚本
```

## 📄 文档

- **[SETUP.md](SETUP.md)** - 详细配置说明和开发指南
- **[USER_GUIDE.md](USER_GUIDE.md)** - 完整使用手册和常见问题
- **[COMPARISON.md](COMPARISON.md)** - Python脚本vs Tauri应用功能对比
- **[SUMMARY.md](SUMMARY.md)** - 项目重构总结

## 🔄 从Python脚本迁移的改进

相比原Python脚本(`verdent_auto_login.py`)的优势:

| 特性 | Python脚本 | Tauri应用 |
|------|-----------|----------|
| 用户界面 | ❌ 命令行 | ✅ 图形界面 |
| 运行环境 | 需要Python | 独立可执行文件 |
| 存储可视化 | ❌ | ✅ 实时显示 |
| 操作确认 | 命令行输入 | GUI对话框 |
| 跨平台 | Python依赖 | 原生应用 |
| 性能 | 解释执行 | 编译后原生 |

## 🔐 安全性

- ✅ Token仅存储在本地文件系统
- ✅ 使用PKCE流程防止授权码拦截
- ✅ 所有HTTP请求使用HTTPS
- ✅ 敏感数据不会发送到第三方

## 📞 支持

遇到问题?

1. 查看 [USER_GUIDE.md](USER_GUIDE.md) 常见问题部分
2. 查看 [SETUP.md](SETUP.md) 故障排除
3. 提交Issue到项目仓库

## 📜 License

Copyright © 2025 Verdent Team
