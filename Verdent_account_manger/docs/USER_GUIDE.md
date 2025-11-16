# Verdent账号管理器 - 使用指南

## 目录
1. [安装](#安装)
2. [获取Token](#获取token)
3. [登录操作](#登录操作)
4. [存储管理](#存储管理)
5. [多账号切换](#多账号切换)
6. [常见问题](#常见问题)

---

## 安装

### Windows
1. 下载 `Verdent账号管理器-Setup.exe`
2. 双击运行安装程序
3. 按照向导完成安装
4. 在开始菜单找到"Verdent账号管理器"启动

### macOS
1. 下载 `Verdent账号管理器.dmg`
2. 打开DMG文件
3. 拖动应用到"应用程序"文件夹
4. 在启动台找到应用启动

### Linux
1. 下载 `.deb` 或 `.AppImage` 文件
2. DEB安装: `sudo dpkg -i verdent-account-manager_1.0.0_amd64.deb`
3. AppImage使用: `chmod +x verdent-account-manager.AppImage && ./verdent-account-manager.AppImage`

---

## 获取Token

### 方法一: 浏览器开发者工具

1. **打开Verdent AI网站**
   - 访问 `https://verdent.ai`
   - 确保已登录

2. **打开开发者工具**
   - Windows/Linux: 按 `F12` 或 `Ctrl+Shift+I`
   - macOS: 按 `Cmd+Option+I`

3. **查看Cookie**
   - 切换到"应用程序"(Application)或"存储"(Storage)标签
   - 在左侧找到"Cookie" → `https://verdent.ai`
   - 找到名为 `token` 的Cookie
   - 复制它的值

4. **Token格式示例**
   ```
   eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiIxMjM0NTY3ODkwIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
   ```

### 方法二: 浏览器扩展

某些浏览器扩展(如EditThisCookie)可以更方便地查看和复制Cookie。

---

## 登录操作

### 基本登录流程

1. **启动应用**
   - 打开"Verdent账号管理器"

2. **进入登录管理**
   - 确保在"登录管理"标签页

3. **输入Token**
   - 在"Token"输入框粘贴从浏览器获取的token
   - 可以多行粘贴，系统会自动去除多余空格

4. **配置选项(可选)**
   - **设备ID**: 默认为 `tauri-desktop-app`
     - 建议: 切换账号时修改此值，如 `device-account1`, `device-account2`
   - **应用版本**: 默认为 `1.0.0`
     - 通常无需修改
   - **自动打开VS Code**: 勾选后登录成功会自动触发VS Code回调

5. **点击登录**
   - 点击"登录"按钮
   - 等待处理(通常2-5秒)

6. **查看结果**
   - 成功: 显示绿色提示和访问令牌
   - 失败: 显示红色错误信息

### 登录成功后

- ✅ 访问令牌已保存到本地存储
- ✅ VS Code可以使用该令牌
- ✅ 如果勾选了"自动打开VS Code"，会尝试打开回调链接

---

## 存储管理

### 查看存储信息

1. 切换到"存储管理"标签页
2. 滚动到底部的"📦 存储信息"区域
3. 可以看到:
   - **存储路径**: 数据保存的位置
   - **存储项数量**: 当前保存的数据项数
   - **存储项列表**: 所有存储项的名称

### 存储项说明

**认证相关**:
- `secrets_ycAuthToken` - 登录令牌(最重要)
- `secrets_verdentApiKey` - API密钥
- `secrets_authNonce` - 随机数
- `secrets_authNonceTimestamp` - 时间戳

**用户信息**:
- `globalState_userInfo` - 用户资料
- `globalState_apiProvider` - API提供商设置
- `globalState_taskHistory` - 任务历史

**工作区设置**:
- `workspaceState_isPlanMode` - 计划模式
- `workspaceState_thinkLevel` - 思考级别
- `workspaceState_selectModel` - 模型选择

### 重置设备身份

**用途**: 清除账户认证信息，保留用户偏好设置

**适用场景**:
- ✅ 切换到另一个账号
- ✅ 重新登录当前账号
- ✅ 解决登录问题

**操作步骤**:
1. 点击"重置设备身份"按钮
2. 阅读警告信息
3. 点击"是"确认
4. 等待清理完成
5. 查看清理结果

**清理内容**:
- ✅ 删除所有认证令牌
- ✅ 删除用户信息缓存
- ✅ 删除任务历史
- ✅ 重置API提供商为默认值
- ❌ 保留用户偏好设置(计划模式、思考级别等)

### 完全清理

**用途**: 删除所有存储数据，恢复到初始状态

**适用场景**:
- ⚠️ 完全卸载前
- ⚠️ 解决严重的存储问题
- ⚠️ 重置所有设置

**操作步骤**:
1. 点击"完全清理"按钮(红色)
2. 阅读警告对话框
3. 点击"确定"
4. 在弹出的提示框输入 `YES`
5. 等待清理完成

**清理内容**:
- ✅ 删除所有认证信息
- ✅ 删除所有用户信息
- ✅ 删除所有配置信息
- ✅ 删除所有用户偏好
- ⚠️ 不可恢复!

---

## 多账号切换

### 推荐流程

**从账号A切换到账号B**:

1. **重置设备身份**
   - 切换到"存储管理"
   - 点击"重置设备身份"
   - 确认操作

2. **修改设备ID(可选但推荐)**
   - 回到"登录管理"
   - 将设备ID改为新值,如:
     - 账号A: `device-accountA`
     - 账号B: `device-accountB`

3. **获取账号B的Token**
   - 在浏览器登录账号B
   - 按照[获取Token](#获取token)步骤获取

4. **使用账号B登录**
   - 粘贴账号B的Token
   - 点击"登录"

5. **验证**
   - 查看存储信息
   - 确认登录成功

### 注意事项

⚠️ **为什么要重置设备身份?**
- Verdent AI会检测同一设备的多账号登录
- 不重置可能被识别为违规行为
- 重置后系统认为是"新设备首次登录"

⚠️ **设备ID的作用**
- 进一步区分不同账号
- 避免设备关联
- 建议每个账号使用不同的设备ID

---

## 常见问题

### Q1: 登录失败: "获取授权码失败"

**可能原因**:
- Token已过期
- Token格式错误
- 网络问题

**解决方案**:
1. 重新从浏览器获取Token
2. 确保复制完整的Token(没有截断)
3. 检查网络连接
4. 确保Token没有多余的空格或换行

---

### Q2: 登录失败: "获取访问令牌失败"

**可能原因**:
- PKCE验证失败
- 服务器问题

**解决方案**:
1. 重试登录
2. 重置设备身份后再登录
3. 检查系统时间是否正确

---

### Q3: VS Code没有自动打开

**可能原因**:
- VS Code未安装
- 系统权限问题

**解决方案**:
1. 手动复制回调链接
2. 在浏览器地址栏粘贴并回车
3. 浏览器会询问是否打开VS Code，点击"打开"

---

### Q4: 切换账号后仍然显示旧账号

**可能原因**:
- 未重置设备身份
- 浏览器缓存

**解决方案**:
1. 点击"重置设备身份"
2. 修改设备ID
3. 重新登录新账号
4. 清除VS Code中的Verdent扩展缓存

---

### Q5: 存储路径在哪里?

**Windows**:
```
C:\Users\{你的用户名}\.verdent_account_manager\
```

**macOS**:
```
/Users/{你的用户名}/.verdent_account_manager/
```

**Linux**:
```
/home/{你的用户名}/.verdent_account_manager/
```

你可以在"存储管理"标签页的"📦 存储信息"区域查看确切路径。

---

### Q6: 如何完全卸载?

**步骤**:
1. 打开应用
2. 切换到"存储管理"
3. 点击"完全清理"并确认
4. 关闭应用
5. 在系统中卸载应用:
   - **Windows**: 设置 → 应用 → 卸载
   - **macOS**: 从"应用程序"文件夹删除
   - **Linux**: `sudo dpkg -r verdent-account-manager`

---

### Q7: Token在哪里存储?是否安全?

**存储位置**:
- 本地文件系统: `~/.verdent_account_manager/secrets_ycAuthToken.json`

**安全性**:
- ✅ 仅存储在本地,不上传到任何服务器
- ✅ 使用文件系统权限保护
- ✅ 只有当前用户可以访问
- ⚠️ 如果他人能访问你的电脑,可能读取文件
- 💡 建议: 不要在共享电脑上使用

---

### Q8: 能否同时运行多个实例?

- ❌ 不建议同时运行多个实例
- 多个实例会共享同一个存储路径
- 可能导致数据冲突
- 建议: 一次只运行一个实例

---

### Q9: 应用更新怎么办?

**自动更新** (计划中):
- 应用启动时检查更新
- 提示下载新版本

**手动更新**:
1. 下载最新版本
2. 数据自动保留(存储在用户目录)
3. 安装新版本覆盖旧版本

---

### Q10: 如何反馈问题?

1. 记录错误信息截图
2. 记录操作步骤
3. 提交issue到项目仓库
4. 或联系Verdent团队

---

## 高级技巧

### 技巧1: 命令行查看存储

**Windows**:
```powershell
dir $env:USERPROFILE\.verdent_account_manager
```

**macOS/Linux**:
```bash
ls -la ~/.verdent_account_manager
```

### 技巧2: 备份存储

```bash
# 备份
cp -r ~/.verdent_account_manager ~/.verdent_account_manager.backup

# 恢复
cp -r ~/.verdent_account_manager.backup ~/.verdent_account_manager
```

### 技巧3: 查看Token内容

打开 `secrets_ycAuthToken.json`:
```json
{
  "value": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 技巧4: 快速切换账号脚本

创建脚本保存不同账号的Token和设备ID,实现一键切换。

---

## 安全建议

1. ✅ 定期更换Token
2. ✅ 不要分享Token给他人
3. ✅ 在公共电脑使用后进行"完全清理"
4. ✅ 保护好你的电脑密码
5. ❌ 不要在截图或录屏中暴露Token
6. ❌ 不要将Token提交到代码仓库

---

## 支持

如有问题,请:
- 查看 [SETUP.md](SETUP.md) 了解技术细节
- 查看 [COMPARISON.md](COMPARISON.md) 了解功能对比
- 提交issue到项目仓库
- 联系Verdent支持团队
