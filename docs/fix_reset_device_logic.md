# 修复：设备身份重置逻辑问题

## 问题描述

在原始实现中，"重置设备身份"和"完全清理"功能存在严重的逻辑错误：

### 错误的行为

1. **重置设备身份** 按钮：
   - ❌ 没有处理 VS Code 的设备 ID
   - ❌ 忽略了 `generateNewDeviceId` 参数
   - ❌ 只清理了应用存储，没有重置设备标识

2. **完全清理** 按钮：
   - ❌ 调用 `clear()` 方法删除了设备 ID
   - ❌ 应该调用 `reset_telemetry_ids()` 来生成新的设备 ID
   - ❌ 忽略了 `generateNewDeviceId` 参数

## 修复内容

### 1. 修改 `reset_device_identity` 函数

**文件**: `src-tauri/src/commands.rs`

**修改内容**：
- 添加 `VSCodeStorageManager` 的导入
- 根据 `generate_new_device_id` 参数决定是否重置设备 ID
- 调用 `reset_telemetry_ids()` 而不是 `clear()`
- 在日志中显示新生成的设备 ID

### 2. 修改 `reset_all_storage` 函数

**文件**: `src-tauri/src/commands.rs`

**修改内容**：
- 将 `vscode_storage.clear()` 改为 `vscode_storage.reset_telemetry_ids()`
- 根据 `generate_new_device_id` 参数决定是否重置设备 ID
- 在日志中显示新生成的设备 ID

### 3. 修正 `generate_sqm_id` 函数

**文件**: `src-tauri/src/vscode_storage.rs`

**修改内容**：
- 移除生成的 UUID 外层的花括号
- 从 `format!("{{{}}}", uuid)` 改为 `uuid.to_string().to_uppercase()`

## 关键方法说明

### VSCodeStorageManager 方法

- **`clear()`**: 从 storage.json 中**删除**设备 ID 键
  ```rust
  storage.data.remove("telemetry.sqmId");
  storage.data.remove("telemetry.devDeviceId");
  storage.data.remove("telemetry.machineId");
  ```

- **`reset_telemetry_ids()`**: 生成并**写入新的**设备 ID
  ```rust
  let sqm_id = Self::generate_sqm_id();
  let device_id = Self::generate_device_id();
  let machine_id = Self::generate_machine_id();
  storage.data.insert("telemetry.sqmId", Value::String(sqm_id));
  // ...
  ```

## 正确的行为流程

### 重置设备身份 (`generate_new_device_id = true`)
1. 清理 Verdent 认证信息（tokens、userInfo 等）
2. **重置** VS Code 设备 ID（生成新值）
3. 返回新生成的 ID 信息

### 重置设备身份 (`generate_new_device_id = false`)
1. 清理 Verdent 认证信息（tokens、userInfo 等）
2. **保持** VS Code 设备 ID 不变
3. 不修改 storage.json 中的设备标识

### 完全清理 (`generate_new_device_id = true`)
1. 清理所有 Verdent 插件的本地存储数据
2. **重置** VS Code 设备 ID（生成新值）
3. 删除所有账户数据
4. 返回新生成的 ID 信息

### 完全清理 (`generate_new_device_id = false`)
1. 清理所有 Verdent 插件的本地存储数据
2. **保持** VS Code 设备 ID 不变
3. 删除所有账户数据

## 测试验证

### 验证步骤

1. **运行测试脚本**
   ```bash
   python test/test_reset_logic.py
   ```

2. **手动验证**
   - 运行应用程序
   - 点击"重置设备身份"按钮（勾选"生成新设备ID"）
   - 检查 `%APPDATA%\Code\User\globalStorage\storage.json`
   - 确认 `telemetry.sqmId` 等值已更新

3. **检查日志输出**
   ```
   [✓] VS Code 设备标识已重置
       新 sqmId: ED1D4676-F054-47EE-B3F9-926A96E4DE53
       新 deviceId: 12345678-1234-1234-1234-123456789012
       新 machineId: abc123def456...
   ```

## 影响范围

- **用户体验**：设备身份重置功能现在能正确工作
- **数据一致性**：设备 ID 不会被意外删除
- **兼容性**：与 VS Code 的设备识别机制保持一致

## 注意事项

1. 生成的 `sqmId` 现在不包含花括号，格式为：
   - ✅ `ED1D4676-F054-47EE-B3F9-926A96E4DE53`
   - ❌ `{ED1D4676-F054-47EE-B3F9-926A96E4DE53}`

2. 设备 ID 重置是**可选的**，由用户通过界面复选框控制

3. 即使重置失败，其他清理操作仍会继续执行

## 相关文件

- `src-tauri/src/commands.rs` - 命令处理逻辑
- `src-tauri/src/vscode_storage.rs` - VS Code 存储管理
- `test/test_reset_logic.py` - 测试验证脚本
