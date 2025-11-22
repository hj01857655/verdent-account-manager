# 多编辑器支持功能

## 概述

为"重置设备身份"和"完全清理"功能添加了多编辑器支持，允许用户自定义选择需要清理的编辑器数据。

## 支持的编辑器

| 编辑器 | 文件夹名称 | Windows 路径 | macOS 路径 | Linux 路径 |
|--------|-----------|--------------|------------|------------|
| VS Code | Code | %APPDATA%\Code | ~/Library/Application Support/Code | ~/.config/Code |
| Windsurf | Windsurf | %APPDATA%\Windsurf | ~/Library/Application Support/Windsurf | ~/.config/Windsurf |
| Cursor | Cursor | %APPDATA%\Cursor | ~/Library/Application Support/Cursor | ~/.config/Cursor |
| Trae | Trae | %APPDATA%\Trae | ~/Library/Application Support/Trae | ~/.config/Trae |

## 技术实现

### 1. 后端架构

#### 新增模块：`editor_config.rs`

定义了编辑器枚举和相关功能：

```rust
pub enum EditorType {
    VSCode,
    Windsurf,
    Cursor,
    Trae,
}
```

主要功能：
- `display_name()` - 获取编辑器显示名称
- `folder_name()` - 获取编辑器文件夹名称
- `get_global_storage_path()` - 获取 globalStorage 路径
- `get_state_db_path()` - 获取 state.vscdb 路径
- `get_verdent_storage_path()` - 获取 Verdent 扩展存储路径

#### 更新 `cleanup_utils.rs`

添加了多编辑器支持的函数：
- `get_cleanup_directories_for_editors(editors: &[EditorType])` - 获取指定编辑器的清理路径
- `clear_verdent_directories_for_editors(editors: &[EditorType])` - 清空指定编辑器的文件夹
- `reset_editor_device_id(editor: &EditorType, generate_new: bool)` - 重置单个编辑器的 deviceId
- `reset_editors_device_id(editors: &[EditorType], generate_new: bool)` - 批量重置多个编辑器的 deviceId

#### 更新 `commands.rs`

修改了两个主要命令：
- `reset_device_identity(generate_new_device_id: bool, selected_editors: Option<Vec<String>>)`
- `reset_all_storage(generate_new_device_id: bool, selected_editors: Option<Vec<String>>)`

新增了两个辅助命令：
- `get_all_editors_info()` - 获取所有编辑器信息
- `get_installed_editors()` - 获取已安装的编辑器列表

### 2. 前端实现

#### 更新 `App.vue`

##### 新增状态管理
```typescript
const availableEditors = ref<EditorInfo[]>([])
const selectedEditors = ref<string[]>(['VSCode'])
```

##### 编辑器选择 UI
```vue
<div class="editor-selection-section">
  <h4>选择要清理的编辑器</h4>
  <div class="editor-checkboxes">
    <div v-for="editor in availableEditors" :key="editor.editor_type">
      <input type="checkbox" v-model="selectedEditors" :value="editor.editor_type" />
      <label>{{ editor.display_name }}</label>
    </div>
  </div>
</div>
```

##### 样式设计
- 网格布局显示编辑器选项
- 未安装的编辑器显示灰色并禁用
- 已安装的编辑器显示绿色勾号

## 功能特性

### 1. 智能检测
- 自动检测已安装的编辑器
- 未安装的编辑器自动禁用选择框
- 显示每个编辑器的安装状态

### 2. 灵活选择
- 用户可以选择清理特定编辑器
- 默认只选中 VS Code
- 支持多选操作

### 3. 清理范围
对于每个选中的编辑器，将清理以下内容：

#### 设备身份重置
- Verdent 扩展的认证信息
- 编辑器的设备标识（telemetry IDs）
- 保留用户偏好设置

#### 完全清理
- 所有 Verdent 扩展数据
- 编辑器的设备标识
- Verdent 相关文件夹内容
- state.vscdb 中的 deviceId

## 使用流程

1. **打开应用**
   - 应用启动时自动检测已安装的编辑器

2. **选择编辑器**
   - 在"存储管理"标签页
   - 勾选要清理的编辑器

3. **选择清理选项**
   - 勾选"清理时生成新的设备ID"（可选）

4. **执行清理**
   - 点击"重置设备身份"或"完全清理"
   - 确认操作
   - 等待清理完成

## 注意事项

1. **权限要求**
   - 某些操作可能需要管理员权限
   - Windows 系统建议以管理员身份运行

2. **数据安全**
   - 清理操作不可恢复
   - 建议先备份重要数据

3. **兼容性**
   - 目前只有 VS Code 完全支持设备标识重置
   - 其他编辑器的设备标识重置功能待完善
   - 文件夹清理功能对所有编辑器都有效

4. **扩展性**
   - 架构设计支持轻松添加新编辑器
   - 只需在 `EditorType` 枚举中添加新成员

## 后续改进

### 待实现功能
1. 支持其他编辑器的设备标识重置（需要更新 VSCodeStorageManager）
2. 添加更多编辑器支持（如 Sublime Text、Atom 等）
3. 提供编辑器数据的选择性备份和恢复

### 已知问题
1. 非 VS Code 编辑器的 telemetry IDs 重置暂不支持
2. 需要更新 VSCodeStorageManager 以支持自定义路径

## 相关文件

- `src-tauri/src/editor_config.rs` - 编辑器配置模块
- `src-tauri/src/cleanup_utils.rs` - 清理工具（已更新）
- `src-tauri/src/commands.rs` - 命令处理（已更新）
- `src/App.vue` - 前端界面（已更新）
- `docs/multi-editor-support.md` - 本文档
