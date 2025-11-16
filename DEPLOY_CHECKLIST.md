# ✅ 部署检查清单

## 📋 发布前检查

### 1. 版本号更新
- [ ] `Verdent_account_manger/package.json` - version 字段
- [ ] `Verdent_account_manger/src-tauri/tauri.conf.json` - version 字段
- [ ] `Verdent_account_manger/src-tauri/Cargo.toml` - version 字段

### 2. 代码质量
- [ ] 所有功能测试通过
- [ ] 无控制台错误输出
- [ ] 移除所有调试代码
- [ ] 代码格式化完成

### 3. 文档更新
- [ ] README.md 更新
- [ ] CHANGELOG.md 更新（如有）
- [ ] 版本发布说明准备

### 4. 资源文件
- [ ] 图标文件正确命名（使用 x 不是 ×）
- [ ] 所有必需图标存在
- [ ] 资源文件路径正确

### 5. 构建测试
- [ ] Windows 本地构建成功
- [ ] 安装包测试通过
- [ ] 卸载测试通过

---

## 🚀 发布流程

### 步骤 1: 本地验证
```powershell
# 运行设置检查
.\setup_github_actions.ps1

# 本地构建测试
.\build_all.ps1
```

### 步骤 2: 提交代码
```bash
# 确保所有更改已提交
git status
git add .
git commit -m "chore: prepare for v1.0.0 release"
git push origin main
```

### 步骤 3: 创建发布标签
```bash
# 创建版本标签
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

### 步骤 4: 监控 CI/CD
1. 访问 GitHub Actions 页面
2. 查看构建进度
3. 确认所有平台构建成功

### 步骤 5: 发布 Release
1. 进入 GitHub Releases 页面
2. 编辑自动创建的草稿
3. 添加发布说明
4. 发布正式版本

---

## 📦 产物验证

### Windows
- [ ] `.msi` 安装包可正常安装
- [ ] `.exe` NSIS 安装程序工作正常
- [ ] 应用可以正常启动
- [ ] 卸载过程无残留

### macOS
- [ ] `.dmg` 文件可以打开
- [ ] 应用可以拖入 Applications
- [ ] 首次启动安全提示正常
- [ ] 签名状态（如果有）

### Linux
- [ ] `.deb` 包可以安装
- [ ] `.AppImage` 可以直接运行
- [ ] 依赖项正确声明
- [ ] 桌面快捷方式创建

---

## 📊 发布后监控

### 第 1 天
- [ ] 检查 Issues 反馈
- [ ] 监控下载统计
- [ ] 收集用户反馈

### 第 3 天
- [ ] 分析使用数据
- [ ] 整理改进建议
- [ ] 准备热修复（如需要）

### 第 7 天
- [ ] 发布总结
- [ ] 规划下个版本
- [ ] 更新路线图

---

## 🔧 常见问题处理

### 构建失败
```bash
# 清理缓存重试
npm cache clean --force
cargo clean
npm install
npm run tauri build
```

### 签名问题
- Windows: 使用自签名证书或购买代码签名证书
- macOS: 需要 Apple Developer 账号
- Linux: 通常不需要签名

### 版本冲突
确保三个地方版本号一致：
1. package.json
2. tauri.conf.json
3. Cargo.toml

---

## 📝 发布说明模板

```markdown
# 🎉 Verdent v1.0.0 发布

## ✨ 新功能
- 功能1描述
- 功能2描述

## 🐛 修复
- 修复了...
- 解决了...

## 💡 改进
- 优化了...
- 提升了...

## 📦 下载
- Windows: [MSI](link) | [EXE](link)
- macOS: [DMG](link)
- Linux: [DEB](link) | [AppImage](link)

## 🙏 感谢
感谢所有贡献者！
```

---

## 🎯 质量目标

- **安装成功率**: > 99%
- **启动成功率**: > 99%
- **崩溃率**: < 0.1%
- **用户满意度**: > 4.5/5

---

<div align="center">
  <strong>📌 使用此清单确保每次发布都完美无缺！</strong>
</div>
