# 机器码重置功能集成

## 功能更新

机器码重置功能现已集成到"重置设备身份"和"完全清理"功能中。

## 功能说明

### 什么是机器码（MachineGuid）

在 Windows 系统中，机器码（MachineGuid）是存储在注册表中的唯一标识符：
- 路径：`HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Cryptography\MachineGuid`
- 用途：被各种软件用来识别设备的唯一性
- 格式：UUID 格式（如：3840DC62-7506-4F6C-A70F-79D5FC150433）

### 为什么要重置机器码

一些软件和服务通过机器码来：
- 识别和追踪设备
- 检测多账号关联
- 限制设备授权数量

重置机器码可以让系统被识别为"全新设备"。

## 功能集成

### 重置设备身份

现在执行以下步骤：
1. **步骤 1**：清理 Verdent 认证信息
2. **步骤 2**：重置编辑器 storage.json 设备标识
3. **步骤 3**：重置编辑器 state.vscdb 中的 deviceId
4. **步骤 4**：重置 Windows 机器码 ✨ **新增**

### 完全清理

现在执行以下步骤：
1. **步骤 1**：清理 Verdent 认证信息
2. **步骤 2**：重置编辑器 storage.json 设备标识
3. **步骤 3**：删除所有账户
4. **步骤 4**：清空 Verdent 相关文件夹
5. **步骤 5**：重置编辑器 state.vscdb 中的 deviceId
6. **步骤 6**：重置 Windows 机器码 ✨ **新增**

## 技术实现

### 代码更新

在 `commands.rs` 的两个函数中添加了机器码重置步骤：

```rust
// 重置机器码（仅 Windows）
if generate_new_device_id && cfg!(target_os = "windows") {
    println!("[*] 步骤 X: 重置机器码...");
    use crate::machine_guid::MachineGuidManager;
    
    match MachineGuidManager::new() {
        Ok(manager) => {
            match manager.reset_to_new_guid() {
                Ok(new_guid) => {
                    deleted_keys.push(format!("Windows MachineGuid (重置为: {})", new_guid));
                    deleted_count += 1;
                    println!("[✓] 机器码已重置: {}", new_guid);
                }
                Err(e) => {
                    eprintln!("[!] 重置机器码失败: {}", e);
                    println!("[!] 提示: 可能需要管理员权限");
                }
            }
        }
        Err(e) => {
            eprintln!("[!] 创建 MachineGuidManager 失败: {}", e);
            println!("[!] 跳过机器码重置");
        }
    }
}
```

### 执行条件

机器码重置仅在以下条件下执行：
1. 用户勾选了"清理时生成新的设备ID"
2. 系统为 Windows（Linux 和 macOS 不支持）
3. 程序有足够的权限（通常需要管理员权限）

## 权限要求

### Windows 系统

重置机器码需要管理员权限，因为需要修改注册表：
- 如果没有权限，操作会失败但不影响其他清理操作
- 建议以管理员身份运行应用程序

### 其他系统

- Linux 和 macOS 不支持机器码重置
- 在非 Windows 系统上会自动跳过此步骤

## 清理效果

成功执行后，系统会被识别为全新设备：

### 重置的标识

1. **应用层**：Verdent 认证信息
2. **编辑器层**：
   - storage.json（telemetry IDs）
   - state.vscdb（deviceId）
3. **系统层**：Windows MachineGuid ✨ **新增**

### 使用场景

特别适用于：
- 需要完全重置设备身份以避免多账号检测
- 解决设备授权限制问题
- 切换到新账号时确保无关联

## 注意事项

1. **不可恢复**：机器码重置后无法恢复到原始值（除非有备份）
2. **影响范围**：可能影响其他依赖机器码的软件
3. **权限要求**：Windows 需要管理员权限
4. **备份功能**：应用支持机器码备份和恢复功能

## 相关功能

应用还提供独立的机器码管理功能：
- 查看当前机器码
- 备份机器码
- 恢复备份的机器码
- 手动重置机器码

## 修改的文件

- `src-tauri/src/commands.rs`：
  - `reset_device_identity` - 添加步骤 4
  - `reset_all_storage` - 添加步骤 6
- `docs/machine-guid-reset-integration.md` - 本文档

## 更新日期

2024-11-22
