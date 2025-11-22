#!/usr/bin/env python3
"""
测试机器码重置功能集成
测试"重置设备身份"和"完全清理"功能中的机器码重置
"""

import subprocess
import winreg
import uuid
import sys
import time
from pathlib import Path

def is_admin():
    """检查是否以管理员权限运行"""
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def get_machine_guid():
    """获取当前机器码"""
    try:
        key_path = r"SOFTWARE\Microsoft\Cryptography"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, "MachineGuid")
            return value
    except Exception as e:
        print(f"获取机器码失败: {e}")
        return None

def backup_machine_guid():
    """备份当前机器码"""
    guid = get_machine_guid()
    if guid:
        backup_file = Path("machine_guid_backup.txt")
        backup_file.write_text(guid)
        print(f"已备份机器码到 {backup_file}: {guid}")
        return guid
    return None

def test_reset_device_identity():
    """测试重置设备身份功能中的机器码重置"""
    print("\n" + "="*60)
    print("测试: 重置设备身份 - 机器码重置")
    print("="*60)
    
    # 1. 获取原始机器码
    original_guid = get_machine_guid()
    print(f"原始机器码: {original_guid}")
    
    # 2. 执行重置设备身份（需要实际运行 Tauri 应用）
    print("\n请手动执行以下操作：")
    print("1. 运行 Verdent Account Manager")
    print("2. 切换到'存储管理'标签")
    print("3. 勾选'清理时生成新的设备ID'")
    print("4. 点击'重置设备身份'")
    print("5. 确认操作")
    
    input("\n按 Enter 键继续（执行完上述操作后）...")
    
    # 3. 获取新的机器码
    new_guid = get_machine_guid()
    print(f"\n新机器码: {new_guid}")
    
    # 4. 验证结果
    if original_guid != new_guid:
        print("✓ 测试通过: 机器码已成功重置")
        return True
    else:
        print("✗ 测试失败: 机器码未改变")
        return False

def test_reset_all_storage():
    """测试完全清理功能中的机器码重置"""
    print("\n" + "="*60)
    print("测试: 完全清理 - 机器码重置")
    print("="*60)
    
    # 1. 获取原始机器码
    original_guid = get_machine_guid()
    print(f"原始机器码: {original_guid}")
    
    # 2. 执行完全清理（需要实际运行 Tauri 应用）
    print("\n请手动执行以下操作：")
    print("1. 运行 Verdent Account Manager")
    print("2. 切换到'存储管理'标签")
    print("3. 勾选'清理时生成新的设备ID'")
    print("4. 点击'完全清理'")
    print("5. 确认所有对话框")
    
    input("\n按 Enter 键继续（执行完上述操作后）...")
    
    # 3. 获取新的机器码
    new_guid = get_machine_guid()
    print(f"\n新机器码: {new_guid}")
    
    # 4. 验证结果
    if original_guid != new_guid:
        print("✓ 测试通过: 机器码已成功重置")
        return True
    else:
        print("✗ 测试失败: 机器码未改变")
        return False

def test_skip_without_flag():
    """测试不勾选'生成新的设备ID'时是否跳过机器码重置"""
    print("\n" + "="*60)
    print("测试: 不勾选选项时跳过机器码重置")
    print("="*60)
    
    # 1. 获取原始机器码
    original_guid = get_machine_guid()
    print(f"原始机器码: {original_guid}")
    
    # 2. 执行重置但不勾选选项
    print("\n请手动执行以下操作：")
    print("1. 运行 Verdent Account Manager")
    print("2. 切换到'存储管理'标签")
    print("3. 取消勾选'清理时生成新的设备ID'")
    print("4. 点击'重置设备身份'")
    print("5. 确认操作")
    
    input("\n按 Enter 键继续（执行完上述操作后）...")
    
    # 3. 获取当前机器码
    current_guid = get_machine_guid()
    print(f"\n当前机器码: {current_guid}")
    
    # 4. 验证结果
    if original_guid == current_guid:
        print("✓ 测试通过: 机器码未改变（符合预期）")
        return True
    else:
        print("✗ 测试失败: 机器码不应该改变")
        return False

def main():
    """主测试函数"""
    print("机器码重置功能集成测试")
    print("=" * 60)
    
    # 检查系统
    if sys.platform != "win32":
        print("此测试仅支持 Windows 系统")
        return
    
    # 检查权限
    if not is_admin():
        print("警告: 未以管理员权限运行")
        print("某些测试可能会失败")
        print("建议以管理员身份运行此脚本")
        response = input("\n是否继续? (y/n): ")
        if response.lower() != 'y':
            return
    
    # 备份原始机器码
    print("\n备份原始机器码...")
    original_backup = backup_machine_guid()
    if not original_backup:
        print("无法备份机器码，测试中止")
        return
    
    # 运行测试
    tests = []
    
    print("\n开始测试...")
    
    # 测试1: 重置设备身份
    test1 = test_reset_device_identity()
    tests.append(("重置设备身份 - 机器码重置", test1))
    
    # 测试2: 完全清理
    test2 = test_reset_all_storage()
    tests.append(("完全清理 - 机器码重置", test2))
    
    # 测试3: 不勾选选项时跳过
    test3 = test_skip_without_flag()
    tests.append(("跳过机器码重置（未勾选）", test3))
    
    # 显示测试结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    for test_name, result in tests:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, r in tests if r)
    total = len(tests)
    print(f"\n总计: {passed}/{total} 测试通过")
    
    # 询问是否恢复原始机器码
    print("\n" + "="*60)
    response = input("是否恢复原始机器码? (y/n): ")
    if response.lower() == 'y':
        print("请使用应用的'机器码管理'功能恢复备份")
        print(f"原始机器码: {original_backup}")

if __name__ == "__main__":
    main()
