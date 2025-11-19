# 端口配置说明

## 当前配置
- **开发服务器端口**: `53252`
- **生产环境**: 不需要端口（使用 Tauri 内置的文件协议）

## 配置文件位置

### 1. Vite 配置
**文件**: `Verdent_account_manger/vite.config.ts`
```typescript
server: {
  port: 53252,
  strictPort: false,  // 如果端口被占用，自动尝试下一个可用端口
  host: 'localhost',
}
```

### 2. Tauri 配置
**文件**: `Verdent_account_manger/src-tauri/tauri.conf.json`
```json
"build": {
  "devUrl": "http://localhost:53252",
  "frontendDist": "../dist"
}
```

## 更改端口步骤

如果需要更改端口，请修改以下文件：

1. **vite.config.ts** - 更改 `server.port` 值
2. **src-tauri/tauri.conf.json** - 更改 `build.devUrl` 中的端口号
3. **start-dev.sh** - 更新提示信息中的端口号（可选）
4. **start-dev.bat** - 更新提示信息中的端口号（可选）

## 端口选择建议

- 避免使用常用端口（80, 443, 3000, 8080 等）
- 建议使用 49152-65535 范围内的端口（动态/私有端口）
- 当前使用 `53252` 是一个不常用的高位端口，减少冲突可能性

## 故障排查

### 端口被占用
如果启动时提示端口被占用：

**Windows:**
```cmd
# 查看端口占用
netstat -ano | findstr :53252

# 结束占用进程（PID 为上一步查到的进程ID）
taskkill /PID <PID> /F
```

**macOS/Linux:**
```bash
# 查看端口占用
lsof -i :53252

# 结束占用进程
kill -9 <PID>
```

### 自动切换端口
由于配置了 `strictPort: false`，如果 53252 端口被占用，Vite 会自动尝试下一个可用端口（53253, 53254...）

## 注意事项

1. **开发环境**: 端口配置只影响开发环境
2. **生产构建**: 打包后的应用不需要端口，使用 Tauri 的文件协议
3. **防火墙**: 确保防火墙允许该端口的本地访问
4. **代理软件**: 某些代理软件可能会占用高位端口，注意避免冲突

## 更新历史

- **2024-11-19**: 端口从 5173 更改为 53252
  - 原因：使用更独特的端口号，避免与其他开发工具冲突
