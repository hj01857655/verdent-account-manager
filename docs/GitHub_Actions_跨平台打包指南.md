# GitHub Actions 跨平台自动化打包指南

## 📋 概述

通过 GitHub Actions，你可以在云端自动构建 Windows、macOS 和 Linux 三个平台的应用程序，无需本地配置多个操作系统环境。

## 🚀 快速开始

### 1. 推送代码到 GitHub

```bash
# 初始化 Git 仓库（如果还没有）
git init
git add .
git commit -m "Initial commit"

# 添加远程仓库
git remote add origin https://github.com/你的用户名/你的仓库名.git

# 推送代码
git push -u origin main
```

### 2. 创建版本标签触发构建

```bash
# 创建标签（版本号格式：v主版本.次版本.修订号）
git tag v1.0.0

# 推送标签到 GitHub（这将触发自动构建）
git push origin v1.0.0
```

### 3. 或者手动触发构建

1. 进入 GitHub 仓库页面
2. 点击 **Actions** 标签
3. 选择 **Build and Release** 工作流
4. 点击 **Run workflow** 按钮
5. 选择分支后点击 **Run workflow**

## 📦 构建产物

构建完成后，你将获得以下安装包：

### Windows
- `*.msi` - Windows Installer 安装包
- `*.exe` - NSIS 安装程序

### macOS
- `*.dmg` - macOS 磁盘镜像（推荐）
- `*.app` - macOS 应用程序包

### Linux
- `*.deb` - Debian/Ubuntu 安装包
- `*.AppImage` - 通用 Linux 可执行文件

## 🔍 查看构建状态

### 在 Actions 页面
1. 进入仓库的 **Actions** 标签
2. 查看最新的工作流运行状态
3. 点击具体的运行记录查看详细日志

### 下载构建产物
1. 在工作流运行详情页面
2. 滚动到底部的 **Artifacts** 部分
3. 下载对应平台的构建产物

## 📝 配置说明

### 工作流配置文件
位置：`.github/workflows/build.yml`

### 触发条件
```yaml
on:
  push:
    tags:
      - 'v*'  # 推送 v 开头的标签时自动触发
  workflow_dispatch:  # 允许手动触发
```

### 构建矩阵
```yaml
matrix:
  include:
    - platform: windows-latest      # Windows
    - platform: macos-latest        # macOS Intel & Apple Silicon
    - platform: ubuntu-22.04        # Linux
```

## 🔧 自定义配置

### 修改支持的平台

编辑 `.github/workflows/build.yml`：

```yaml
# 只构建 Windows 和 Linux
matrix:
  include:
    - platform: windows-latest
      target: x86_64-pc-windows-msvc
    - platform: ubuntu-22.04
      target: x86_64-unknown-linux-gnu
```

### 修改 Node.js 版本

```yaml
- name: 安装 Node.js
  uses: actions/setup-node@v4
  with:
    node-version: '20'  # 修改为你需要的版本
```

### 修改 Rust 版本

```yaml
- name: 安装 Rust (稳定版)
  uses: dtolnay/rust-toolchain@stable  # 可改为 nightly 或具体版本号
```

## 🎯 Release 发布

当推送标签时，工作流会自动创建 GitHub Release：

1. **Draft Release** - 草稿状态，需要手动发布
2. **自动附加所有构建产物**
3. **自动生成发布说明**

### 手动发布 Release

1. 进入仓库的 **Releases** 页面
2. 找到草稿状态的 Release
3. 编辑发布说明（可选）
4. 点击 **Publish release** 发布

## 🐛 常见问题

### Q1: 构建失败怎么办？

**A:** 
1. 查看 Actions 页面的详细日志
2. 检查是否缺少必要的图标文件
3. 确认 `package.json` 和 `tauri.conf.json` 配置正确

### Q2: macOS 构建显示签名错误

**A:** 
工作流已配置跳过代码签名。如需签名：
1. 申请 Apple 开发者账号
2. 创建签名证书
3. 在 GitHub 仓库设置中添加 Secrets：
   - `APPLE_CERTIFICATE`
   - `APPLE_CERTIFICATE_PASSWORD`
   - `APPLE_ID`
   - `APPLE_PASSWORD`

### Q3: Linux 构建缺少依赖

**A:** 
在 `.github/workflows/build.yml` 的 Linux 步骤中添加：
```yaml
- name: 安装 Linux 依赖
  if: matrix.platform == 'ubuntu-22.04'
  run: |
    sudo apt-get update
    sudo apt-get install -y 你需要的包名
```

### Q4: 如何只构建特定平台？

**A:** 
临时禁用某个平台：
1. 编辑 `.github/workflows/build.yml`
2. 在对应平台的配置前添加 `#` 注释掉

### Q5: 构建时间太长

**A:** 
优化建议：
- 启用了 Rust 和 npm 缓存，后续构建会更快
- 首次构建通常需要 15-30 分钟
- 后续构建通常 5-10 分钟

## 📊 构建时间参考

| 平台 | 首次构建 | 后续构建 |
|------|---------|---------|
| Windows | 15-20 分钟 | 5-8 分钟 |
| macOS | 20-25 分钟 | 8-12 分钟 |
| Linux | 10-15 分钟 | 4-6 分钟 |

## 🔐 安全建议

1. **不要在代码中硬编码敏感信息**
2. **使用 GitHub Secrets 存储密钥**
3. **定期更新依赖版本**
4. **启用分支保护规则**

## 📚 相关资源

- [Tauri 官方文档](https://tauri.app/v1/guides/)
- [GitHub Actions 文档](https://docs.github.com/actions)
- [Rust 工具链文档](https://rust-lang.github.io/rustup/)

## 🎓 进阶用法

### 自动发布到其他平台

可以扩展工作流，将构建产物自动发布到：
- npm 仓库
- Homebrew（macOS）
- Snapcraft（Linux）
- Microsoft Store（Windows）

### 添加测试步骤

在构建前添加自动化测试：
```yaml
- name: 运行测试
  working-directory: Verdent_account_manger
  run: npm test
```

### 多版本构建

支持不同的 Node.js 或 Rust 版本构建：
```yaml
matrix:
  node-version: [18, 20, 22]
  rust-version: [stable, nightly]
```

## 💡 提示

- **首次推送**：建议先用 `workflow_dispatch` 手动触发测试
- **版本管理**：遵循语义化版本规范（Semantic Versioning）
- **发布节奏**：建议每次重大更新才发布新版本
- **测试充分**：在本地充分测试后再推送标签

## 🆘 获取帮助

如果遇到问题：
1. 查看 Actions 日志的详细错误信息
2. 搜索 Tauri 社区讨论
3. 查阅本项目的其他文档
4. 提交 Issue 到项目仓库

---

**最后更新**: 2024年11月16日
