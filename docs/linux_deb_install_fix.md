# Linux .deb 包安装错误解决方案

## 错误描述
```bash
dpkg: 处理归档 /home/wwvl/Downloads/Verdent_1.2.0_amd64.deb (--unpack)时出错：
在解析文件 '/var/lib/dpkg/tmp.ci/control' 第 1 行附近时：
无效的软件包名存在于 'Package' 字段：不允许出现字符 '◆'（只能使用字母、数字和 '-+._'）
Sub-process /usr/bin/dpkg returned an error code (1)
```

## 错误原因
Debian 包的 Package 字段包含了中文字符或其他非 ASCII 字符，违反了 Debian 包命名规范。

### Debian 包命名规范
- **只允许**：小写字母 (a-z)、数字 (0-9)、加号 (+)、减号 (-)、点号 (.)
- **不允许**：大写字母、中文字符、空格、其他特殊字符

## 问题根源
在 `tauri.conf.json` 中配置了中文产品名：
```json
"productName": "Verdent账号管理器"  // ❌ 包含中文字符
```

Tauri 在构建 .deb 包时会使用 `productName` 作为包名，导致生成的包不符合 Debian 规范。

## 解决方案

### 已实施的修复
修改 `Verdent_account_manger/src-tauri/tauri.conf.json`：

```json
{
  "productName": "Verdent Account Manager",  // ✅ 改为英文
  "app": {
    "windows": [{
      "title": "Verdent Account Manager"     // ✅ 窗口标题也改为英文
    }]
  }
}
```

### 重新构建
修复配置后，需要重新构建 .deb 包：

```bash
# 进入项目目录
cd Verdent_account_manger

# 清理旧的构建文件
cargo clean

# 重新构建 Linux 包
npm run tauri build -- --target x86_64-unknown-linux-gnu
```

## 验证修复

### 1. 检查生成的 .deb 包名
```bash
ls src-tauri/target/release/bundle/deb/
# 应该看到类似：verdent-account-manager_1.2.0_amd64.deb
```

### 2. 查看包信息
```bash
dpkg-deb -I verdent-account-manager_1.2.0_amd64.deb
```

### 3. 安装测试
```bash
sudo apt install ./verdent-account-manager_1.2.0_amd64.deb
```

## 中文显示支持

虽然包名不能使用中文，但应用内部仍可以显示中文：

### 1. 在应用内显示中文名称
可以在应用的 UI 中继续使用 "Verdent账号管理器"

### 2. 创建中文 .desktop 文件
创建 `verdent-account-manager.desktop`：
```ini
[Desktop Entry]
Name=Verdent Account Manager
Name[zh_CN]=Verdent账号管理器
Comment=Manage Verdent AI accounts
Comment[zh_CN]=管理 Verdent AI 账号
Exec=verdent-account-manager
Icon=verdent-account-manager
Type=Application
Categories=Utility;
```

### 3. 在包描述中使用中文
修改 `Cargo.toml`：
```toml
[package]
name = "verdent-account-manager"
description = "Verdent AI Account Manager - 账号管理器"
```

## 其他 Linux 发行版

### AppImage（推荐）
AppImage 格式对文件名没有严格限制，可以包含中文：
```bash
# 构建 AppImage
npm run tauri build -- --bundles appimage
```

### Snap 包
Snap 包名也需要遵循类似规则，使用英文名：
```yaml
name: verdent-account-manager
title: Verdent账号管理器  # 标题可以用中文
```

## 预防措施

### 1. 命名约定
- **包名/标识符**：使用英文、小写、连字符
- **显示名称**：可以使用中文或其他语言
- **文件名**：遵循目标平台的规范

### 2. CI/CD 验证
在 GitHub Actions 中添加验证步骤：
```yaml
- name: Validate package name
  run: |
    if [[ ! "$PRODUCT_NAME" =~ ^[a-z0-9+.-]+$ ]]; then
      echo "Error: Product name contains invalid characters"
      exit 1
    fi
```

### 3. 多语言支持
使用 i18n 系统，将显示名称与包名分离：
```json
{
  "package": {
    "name": "verdent-account-manager",
    "displayName": {
      "en": "Verdent Account Manager",
      "zh": "Verdent账号管理器"
    }
  }
}
```

## 相关文件
- 配置文件：`Verdent_account_manger/src-tauri/tauri.conf.json`
- 构建脚本：`.github/workflows/build.yml`
- Cargo 配置：`Verdent_account_manger/src-tauri/Cargo.toml`
