# 多编辑器 storage.json 支持

## 更新内容

现在支持 Windsurf、Cursor 和 Trae 编辑器的 `storage.json` 设备ID重置，与 VS Code 具有相同的功能。

## 技术实现

### 1. VSCodeStorageManager 增强

添加了 `new_with_editor` 方法，支持自定义编辑器文件夹名称：

```rust
pub fn new_with_editor(editor_folder: &str) -> Result<Self, std::io::Error>
```

该方法可以处理不同编辑器的路径：
- Windows: `%APPDATA%\{editor_folder}\User\globalStorage\storage.json`
- macOS: `~/Library/Application Support/{editor_folder}/User/globalStorage/storage.json`
- Linux: `~/.config/{editor_folder}/User/globalStorage/storage.json`

### 2. 命令函数更新

#### reset_device_identity
现在支持重置选中编辑器的：
1. **storage.json** 中的 telemetry IDs（步骤 2）
2. **state.vscdb** 中的 deviceId（步骤 3）

#### reset_all_storage
现在支持：
1. 重置选中编辑器的 **storage.json** telemetry IDs（步骤 2）
2. 清空选中编辑器的文件夹（步骤 4）
3. 重置选中编辑器的 **state.vscdb** deviceId（步骤 5）

## 功能对比

### 之前
- 只有 VS Code 支持 storage.json 设备ID重置
- 其他编辑器显示"暂不支持"消息

### 现在
所有编辑器都支持：
- ✅ VS Code - storage.json + state.vscdb
- ✅ Windsurf - storage.json + state.vscdb
- ✅ Cursor - storage.json + state.vscdb
- ✅ Trae - storage.json + state.vscdb

## 清理的数据

对于每个选中的编辑器：

### storage.json（JSON文件）
- `telemetry.sqmId` - 生成新的UUID
- `telemetry.devDeviceId` - 生成新的UUID
- `telemetry.machineId` - 生成新的机器ID

### state.vscdb（SQLite数据库）
- `ItemTable` 表中的 `VerdentAI.verdent` 记录
- `verdent-ai-agent-config.deviceId` 字段

### 文件夹清理（仅完全清理）
- `~/.verdent/projects`
- `~/.verdent/logs`
- `~/.verdent/checkpoints/checkpoints`
- `{编辑器}/User/globalStorage/verdentai.verdent/tasks`
- `{编辑器}/User/globalStorage/verdentai.verdent/checkpoints`

## 使用效果

当用户选择 Windsurf、Cursor 或 Trae 时：

1. **重置设备身份**
   - 清理 Verdent 认证信息
   - 重置编辑器的 storage.json telemetry IDs
   - 重置编辑器的 state.vscdb deviceId

2. **完全清理**
   - 执行"重置设备身份"的所有操作
   - 删除所有账户
   - 清空编辑器相关的 Verdent 文件夹

## 修改的文件

- `src-tauri/src/vscode_storage.rs` - 添加 `new_with_editor` 方法
- `src-tauri/src/commands.rs` - 更新使用 `new_with_editor` 处理所有编辑器

## 注意事项

1. 所有编辑器使用相同的存储结构（storage.json 和 state.vscdb）
2. 扩展文件夹名称遵循 `.{editor_name_lowercase}` 格式
3. 如果编辑器未安装，操作会跳过并显示错误信息

## 更新日期

2024-11-22
