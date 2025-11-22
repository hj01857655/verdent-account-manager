#!/usr/bin/env python3
"""
测试重置设备身份和完全清理功能的逻辑
验证是否正确重置（而不是删除）VS Code 设备标识
"""

import json
import os
from pathlib import Path
import shutil
from datetime import datetime

def get_vscode_storage_path():
    """获取 VS Code storage.json 的路径"""
    appdata = os.environ.get('APPDATA', '')
    if not appdata:
        appdata = os.path.expanduser('~')
    return Path(appdata) / 'Code' / 'User' / 'globalStorage' / 'storage.json'

def backup_storage():
    """备份 storage.json"""
    storage_path = get_vscode_storage_path()
    if storage_path.exists():
        backup_path = storage_path.with_suffix('.json.backup_test')
        shutil.copy2(storage_path, backup_path)
        print(f"[✓] 已备份 storage.json 到: {backup_path}")
        return backup_path
    else:
        print(f"[!] storage.json 不存在: {storage_path}")
        return None

def restore_storage(backup_path):
    """恢复 storage.json"""
    if backup_path and backup_path.exists():
        storage_path = get_vscode_storage_path()
        shutil.copy2(backup_path, storage_path)
        print(f"[✓] 已恢复 storage.json")
        backup_path.unlink()
        print(f"[✓] 已删除备份文件")

def read_telemetry_ids():
    """读取当前的设备标识"""
    storage_path = get_vscode_storage_path()
    if not storage_path.exists():
        return None, None, None
    
    try:
        with open(storage_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            sqm_id = data.get('telemetry.sqmId')
            dev_device_id = data.get('telemetry.devDeviceId')
            machine_id = data.get('telemetry.machineId')
            return sqm_id, dev_device_id, machine_id
    except Exception as e:
        print(f"[×] 读取 storage.json 失败: {e}")
        return None, None, None

def test_reset_logic():
    """测试重置逻辑"""
    print("=" * 60)
    print("测试 VS Code 设备标识重置逻辑")
    print("=" * 60)
    
    # 1. 读取当前的设备标识
    print("\n[1] 读取当前设备标识...")
    sqm_id_before, device_id_before, machine_id_before = read_telemetry_ids()
    
    if sqm_id_before:
        print(f"    sqmId: {sqm_id_before}")
        print(f"    devDeviceId: {device_id_before}")
        print(f"    machineId: {machine_id_before[:20]}..." if machine_id_before else "    machineId: None")
    else:
        print("    [!] 没有找到设备标识")
    
    print("\n[2] 测试场景说明:")
    print("    - reset_device_identity(true): 应该重置设备ID为新值")
    print("    - reset_device_identity(false): 应该保持设备ID不变")
    print("    - reset_all_storage(true): 应该重置设备ID为新值")
    print("    - reset_all_storage(false): 应该保持设备ID不变")
    
    print("\n[3] 预期行为:")
    print("    ✓ 调用 reset_telemetry_ids() - 生成新的设备ID")
    print("    × 不调用 clear() - 那会删除设备ID")
    
    print("\n[4] 验证步骤:")
    print("    1. 运行应用，点击'重置设备身份'按钮（勾选'生成新设备ID'）")
    print("    2. 检查 storage.json，确认设备ID已更新为新值")
    print("    3. 再次点击'重置设备身份'按钮（不勾选'生成新设备ID'）")
    print("    4. 检查 storage.json，确认设备ID保持不变")
    
    print("\n[5] 手动验证命令:")
    storage_path = get_vscode_storage_path()
    print(f"    查看设备ID: notepad \"{storage_path}\"")
    print(f"    搜索关键字: telemetry.sqmId")
    
    # 显示storage.json的前几行作为参考
    if storage_path.exists():
        print("\n[6] storage.json 示例内容:")
        try:
            with open(storage_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # 查找并显示telemetry相关的行
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if 'telemetry' in line.lower():
                        # 显示前后各一行
                        start = max(0, i-1)
                        end = min(len(lines), i+2)
                        for j in range(start, end):
                            print(f"    {j+1:4}: {lines[j][:100]}")
                        break
        except Exception as e:
            print(f"    [×] 读取失败: {e}")

def main():
    """主函数"""
    print("VS Code 设备标识重置逻辑测试工具")
    print("-" * 60)
    
    # 备份当前的storage.json
    backup_path = backup_storage()
    
    try:
        # 执行测试
        test_reset_logic()
        
        print("\n" + "=" * 60)
        print("测试说明完成")
        print("请按照上述步骤手动验证功能是否正确")
        print("=" * 60)
        
    finally:
        # 询问是否恢复备份
        if backup_path:
            response = input("\n是否恢复原始的 storage.json? (y/n): ")
            if response.lower() == 'y':
                restore_storage(backup_path)

if __name__ == "__main__":
    main()
