# Verdent账号管理器 - 项目配置说明

## 快速开始

### 1. 安装依赖

```bash
cd Verdent_account_manger
npm install
```

### 2. 开发模式运行

```bash
npm run tauri dev
```

### 3. 构建发布版本

```bash
npm run tauri build
```

## 配置文件说明

### src-tauri/tauri.conf.json

Tauri应用的主配置文件，包含:
- 应用名称、版本、标识符
- 窗口配置(大小、标题等)
- 构建配置
- 打包配置

### src-tauri/Cargo.toml

Rust依赖配置，核心依赖:
- `tauri`: 应用框架
- `reqwest`: HTTP客户端
- `serde`: 序列化/反序列化
- `sha2`: SHA256哈希
- `base64`: Base64编码
- `rand`: 随机数生成

### package.json

前端NPM依赖，核心依赖:
- `vue`: 前端框架
- `@tauri-apps/api`: Tauri JS API
- `vite`: 构建工具
- `typescript`: 类型支持

## 核心功能模块

### Rust后端 (src-tauri/src/)

1. **pkce.rs** - PKCE认证参数生成
   - 生成state、code_verifier、code_challenge
   - SHA256哈希和Base64编码

2. **api.rs** - Verdent API调用
   - 请求授权码
   - 交换访问令牌

3. **storage.rs** - 本地存储管理
   - 保存/读取/删除存储项
   - 重置设备身份
   - 完全清理存储

4. **commands.rs** - Tauri命令
   - `login_with_token` - 登录
   - `reset_device_identity` - 重置设备
   - `reset_all_storage` - 完全清理
   - `get_storage_info` - 获取存储信息
   - `open_vscode_callback` - 打开VS Code

5. **lib.rs** - 库入口
   - 注册所有Tauri命令
   - 配置插件

6. **main.rs** - 程序入口

### Vue前端 (src/)

1. **App.vue** - 主应用组件
   - 登录表单
   - 存储管理界面
   - 调用Rust命令

2. **main.ts** - 应用入口
3. **style.css** - 全局样式

## 存储位置

本地存储路径: `~/.verdent_account_manager/`

存储项格式: `{key}.json`

### 存储项说明

**认证相关**:
- `secrets_ycAuthToken` - 核心认证令牌
- `secrets_verdentApiKey` - API密钥
- `secrets_authNonce` - 认证随机数
- `secrets_authNonceTimestamp` - 随机数时间戳

**用户信息**:
- `globalState_userInfo` - 用户信息
- `globalState_apiProvider` - API提供商
- `globalState_taskHistory` - 任务历史

**工作区状态**:
- `workspaceState_isPlanMode` - 计划模式
- `workspaceState_thinkLevel` - 思考级别
- `workspaceState_selectModel` - 选择的模型

## 开发注意事项

1. **修改Rust代码后**: 需要重启`npm run tauri dev`
2. **修改Vue代码**: 支持热重载，无需重启
3. **修改tauri.conf.json**: 需要重启开发服务器
4. **调试**: 打开开发者工具 `Ctrl+Shift+I` (Windows/Linux) 或 `Cmd+Option+I` (macOS)

## 构建产物

执行 `npm run tauri build` 后:

- **Windows**: `src-tauri/target/release/bundle/msi/` 或 `nsis/`
- **macOS**: `src-tauri/target/release/bundle/dmg/` 或 `app/`
- **Linux**: `src-tauri/target/release/bundle/deb/` 或 `appimage/`

## 故障排除

### 问题: 编译错误

解决方案:
```bash
cd src-tauri
cargo clean
cargo build
```

### 问题: 依赖安装失败

解决方案:
```bash
rm -rf node_modules package-lock.json
npm install
```

### 问题: Tauri命令调用失败

检查:
1. 命令是否在`lib.rs`中注册
2. 参数类型是否匹配
3. 查看控制台错误信息

## API端点

- **授权码获取**: `https://login.verdent.ai/passport/pkce/auth`
- **令牌交换**: `https://login.verdent.ai/passport/pkce/callback`
- **授权页面**: `https://verdent.ai/auth`
- **VS Code回调**: `vscode://verdentai.verdent/auth`

## 安全性

1. Token仅存储在本地文件系统
2. 使用PKCE流程防止授权码拦截
3. 所有HTTP请求使用HTTPS
4. 敏感数据不会发送到第三方服务器
