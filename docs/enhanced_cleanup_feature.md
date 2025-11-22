# 增强的完全清理功能

## 概述

在 "完全清理" 功能中新增了两个重要的清理操作：
1. 清空 Verdent 相关文件夹内容
2. 重置 VS Code state.vscdb 中的 deviceId

## 新增功能详情

### 1. 清空文件夹内容

清理以下文件夹中的所有内容（保留文件夹本身）：

| 文件夹路径 | 用途说明 |
|-----------|---------|
| `~/.verdent/projects` | Verdent 项目文件 |
| `~/.verdent/logs` | Verdent 日志文件 |
| `~/.verdent/checkpoints/checkpoints` | Verdent 检查点数据 |
| `%APPDATA%/Code/User/globalStorage/verdentai.verdent/tasks` | VS Code 任务数据 |
| `%APPDATA%/Code/User/globalStorage/verdentai.verdent/checkpoints` | VS Code 检查点数据 |

**特点：**
- 递归删除所有文件和子文件夹
- 保留目标文件夹本身
- 如果文件夹不存在，静默跳过
- 记录清理的文件/文件夹数量

### 2. 重置 state.vscdb 中的 deviceId

操作 SQLite 数据库文件：`%APPDATA%/Code/User/globalStorage/state.vscdb`

**处理逻辑：**
1. 查找 `ItemTable` 表中 key 为 `"VerdentAI.verdent"` 的记录
2. 解析 value 字段中的 JSON 数据
3. 修改 `verdent-ai-agent-config.deviceId` 字段
4. 根据 `generate_new_device_id` 参数：
   - `true`: 生成新的随机 UUID
   - `false`: 跳过此步骤

**错误处理：**
- 数据库不存在：记录警告，继续执行
- JSON 解析失败：记录警告，继续执行
- 记录不存在：创建新记录

## 技术实现

### 依赖项

在 `Cargo.toml` 中添加：
```toml
rusqlite = { version = "0.32", features = ["bundled"] }
```

### 核心模块

**文件：** `src-tauri/src/cleanup_utils.rs`

主要函数：
- `clear_directory_contents(path: &Path)` - 清空单个文件夹
- `get_cleanup_directories()` - 获取需要清理的文件夹列表
- `clear_all_verdent_directories()` - 清空所有指定文件夹
- `reset_vscode_device_id(generate_new: bool)` - 重置 deviceId

### 集成到命令

在 `reset_all_storage` 命令中添加了两个新步骤：

```rust
// 步骤 4: 清空 Verdent 相关文件夹
let (dir_count, cleaned_paths) = clear_all_verdent_directories();

// 步骤 5: 重置 VS Code state.vscdb 中的 deviceId
if generate_new_device_id {
    match reset_vscode_device_id(true) {
        Ok(new_device_id) => { /* ... */ }
        Err(e) => { /* ... */ }
    }
}
```

## 执行流程

完全清理功能现在包含 5 个步骤：

1. **清除应用存储** - Verdent 扩展的本地存储
2. **重置 VS Code 设备标识** - storage.json 中的 telemetry IDs
3. **删除所有账户** - 账户管理器中的账户数据
4. **清空文件夹内容** - Verdent 相关文件夹（新增）
5. **重置 state.vscdb deviceId** - VS Code 数据库中的设备ID（新增）

## 测试验证

### 测试脚本

运行测试脚本：
```bash
python test/test_cleanup_directories.py
```

功能选项：
1. 检查文件夹状态 - 显示各文件夹的文件数和大小
2. 检查 state.vscdb - 显示当前的 deviceId
3. 创建测试文件 - 在目标文件夹创建测试文件
4. 验证清理结果 - 确认清理是否成功

### 手动验证步骤

1. **准备测试环境**
   ```bash
   # 创建测试文件
   echo "test" > ~/.verdent/projects/test.txt
   echo "log" > ~/.verdent/logs/test.log
   ```

2. **检查清理前状态**
   - 运行测试脚本，选择选项 1 和 2
   - 记录文件数量和 deviceId

3. **执行完全清理**
   - 运行 Verdent Account Manager
   - 切换到"存储管理"标签
   - 勾选"清理时生成新的设备ID"
   - 点击"完全清理"按钮
   - 确认操作

4. **验证清理结果**
   - 再次运行测试脚本
   - 确认文件夹已清空
   - 确认 deviceId 已更新

## 注意事项

1. **路径兼容性**
   - 使用 `dirs` crate 动态获取用户目录
   - 支持 Windows、macOS 和 Linux
   - 不硬编码用户名

2. **错误容错**
   - 每个清理步骤独立执行
   - 单个步骤失败不影响其他步骤
   - 所有错误都记录但不中断流程

3. **数据安全**
   - 只清理 Verdent 相关数据
   - 保留文件夹结构
   - 不影响其他 VS Code 扩展

4. **性能考虑**
   - 文件删除采用批量处理
   - SQLite 操作使用事务
   - 避免阻塞主线程

## 相关文件

- `src-tauri/src/cleanup_utils.rs` - 清理工具模块
- `src-tauri/src/commands.rs` - 命令处理更新
- `src-tauri/Cargo.toml` - 依赖项配置
- `test/test_cleanup_directories.py` - 测试脚本
- `docs/enhanced_cleanup_feature.md` - 本文档
