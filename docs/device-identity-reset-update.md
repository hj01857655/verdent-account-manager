# 设备身份重置功能更新

## 更新内容

"重置设备身份"功能现在也会清理 VS Code globalStorage 数据库中的 deviceId，与"完全清理"功能保持一致。

## 功能对比

### 之前的行为

**重置设备身份**：
1. 清理 Verdent 认证信息
2. 重置 storage.json 中的 telemetry IDs（sqmId、devDeviceId、machineId）

**完全清理**：
1. 清理 Verdent 认证信息
2. 重置 storage.json 中的 telemetry IDs
3. 删除所有账户
4. 清空 Verdent 相关文件夹
5. 重置 state.vscdb 中的 deviceId

### 更新后的行为

**重置设备身份**：
1. 清理 Verdent 认证信息
2. 重置 storage.json 中的 telemetry IDs（sqmId、devDeviceId、machineId）
3. **重置 state.vscdb 中的 deviceId** ✨ 新增

**完全清理**：
1. 清理 Verdent 认证信息
2. 重置 storage.json 中的 telemetry IDs
3. 删除所有账户
4. 清空 Verdent 相关文件夹
5. 重置 state.vscdb 中的 deviceId

## 技术实现

在 `commands.rs` 的 `reset_device_identity` 函数中添加了步骤 3：

```rust
// 3. 重置编辑器 state.vscdb 中的 deviceId
if generate_new_device_id {
    println!("[*] 步骤 3: 重置编辑器 state.vscdb 中的 deviceId...");
    use crate::cleanup_utils::reset_editors_device_id;
    
    // 使用与步骤2相同的编辑器列表
    let editors_for_db = if let Some(ref editor_names) = selected_editors {
        let mut editors = Vec::new();
        for name in editor_names {
            if let Some(editor) = EditorType::from_string(&name) {
                editors.push(editor);
            }
        }
        editors
    } else {
        vec![EditorType::VSCode]
    };
    
    let results = reset_editors_device_id(&editors_for_db, true);
    // ... 处理结果
}
```

## 影响范围

### 清理的数据

对于选中的每个编辑器，"重置设备身份"现在会清理：

1. **storage.json** 中的设备标识：
   - `telemetry.sqmId`
   - `telemetry.devDeviceId`
   - `telemetry.machineId`

2. **state.vscdb** 数据库中的设备标识：
   - `VerdentAI.verdent` 记录中的 `verdent-ai-agent-config.deviceId`

### 使用场景

这个更新使"重置设备身份"功能更加彻底，特别适用于：
- 需要完全重置设备标识以避免多账号关联检测
- 切换账号前的准备工作
- 解决设备标识相关的问题

## 注意事项

1. **数据不可恢复**：重置后的设备标识无法恢复到原始值
2. **需要勾选选项**：必须勾选"清理时生成新的设备ID"选项才会执行此操作
3. **编辑器支持**：目前完全支持 VS Code，其他编辑器的 state.vscdb 重置功能待完善

## 相关文件

- `src-tauri/src/commands.rs` - 更新了 `reset_device_identity` 函数
- `src-tauri/src/cleanup_utils.rs` - 使用 `reset_editors_device_id` 函数

## 更新日期

2024-11-22
