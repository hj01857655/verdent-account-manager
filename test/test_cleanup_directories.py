#!/usr/bin/env python3
"""
测试完全清理功能的新增清理项
验证文件夹清理和 state.vscdb deviceId 重置功能
"""

import os
import sqlite3
import json
from pathlib import Path
from datetime import datetime

def get_user_home():
    """获取用户主目录"""
    return Path.home()

def get_cleanup_directories():
    """获取需要清理的文件夹列表"""
    home = get_user_home()
    appdata_roaming = os.environ.get('APPDATA', str(home / 'AppData' / 'Roaming'))
    
    directories = [
        # .verdent 目录下的文件夹
        home / '.verdent' / 'projects',
        home / '.verdent' / 'logs',
        home / '.verdent' / 'checkpoints' / 'checkpoints',
        
        # VS Code globalStorage 下的文件夹
        Path(appdata_roaming) / 'Code' / 'User' / 'globalStorage' / 'verdentai.verdent' / 'tasks',
        Path(appdata_roaming) / 'Code' / 'User' / 'globalStorage' / 'verdentai.verdent' / 'checkpoints',
    ]
    
    return directories

def check_directory_status():
    """检查各个文件夹的状态"""
    print("=" * 60)
    print("检查清理目标文件夹状态")
    print("=" * 60)
    
    directories = get_cleanup_directories()
    
    for dir_path in directories:
        print(f"\n[文件夹] {dir_path}")
        if dir_path.exists():
            if dir_path.is_dir():
                # 统计文件和子文件夹数量
                file_count = 0
                dir_count = 0
                total_size = 0
                
                try:
                    for item in dir_path.rglob('*'):
                        if item.is_file():
                            file_count += 1
                            total_size += item.stat().st_size
                        elif item.is_dir():
                            dir_count += 1
                    
                    print(f"  ✓ 存在")
                    print(f"  - 文件数: {file_count}")
                    print(f"  - 子文件夹数: {dir_count}")
                    print(f"  - 总大小: {total_size / 1024:.2f} KB")
                except Exception as e:
                    print(f"  ! 访问错误: {e}")
            else:
                print(f"  × 不是文件夹")
        else:
            print(f"  - 不存在")

def check_vscode_state_db():
    """检查 VS Code state.vscdb 数据库中的 deviceId"""
    print("\n" + "=" * 60)
    print("检查 VS Code state.vscdb")
    print("=" * 60)
    
    appdata_roaming = os.environ.get('APPDATA', str(get_user_home() / 'AppData' / 'Roaming'))
    db_path = Path(appdata_roaming) / 'Code' / 'User' / 'globalStorage' / 'state.vscdb'
    
    print(f"\n数据库路径: {db_path}")
    
    if not db_path.exists():
        print("× 数据库文件不存在")
        return
    
    try:
        # 连接数据库
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 查询 VerdentAI.verdent 记录
        cursor.execute("SELECT value FROM ItemTable WHERE key = 'VerdentAI.verdent'")
        row = cursor.fetchone()
        
        if row:
            value_str = row[0]
            try:
                value_json = json.loads(value_str)
                
                print("✓ 找到 VerdentAI.verdent 记录")
                
                # 查找 deviceId
                if 'verdent-ai-agent-config' in value_json:
                    config = value_json['verdent-ai-agent-config']
                    if 'deviceId' in config:
                        device_id = config['deviceId']
                        print(f"  当前 deviceId: {device_id}")
                    else:
                        print("  × 未找到 deviceId 字段")
                else:
                    print("  × 未找到 verdent-ai-agent-config 字段")
                
                # 显示其他可能的配置
                print("\n  其他配置项:")
                for key in value_json.keys():
                    if key != 'verdent-ai-agent-config':
                        print(f"    - {key}")
                        
            except json.JSONDecodeError as e:
                print(f"× JSON 解析错误: {e}")
                print(f"  原始值: {value_str[:100]}...")
        else:
            print("- 未找到 VerdentAI.verdent 记录")
        
        # 查看表中其他 Verdent 相关的键
        cursor.execute("SELECT key FROM ItemTable WHERE key LIKE '%verdent%' OR key LIKE '%Verdent%'")
        other_keys = cursor.fetchall()
        
        if other_keys:
            print("\n其他 Verdent 相关的键:")
            for key in other_keys[:10]:  # 最多显示10个
                print(f"  - {key[0]}")
            if len(other_keys) > 10:
                print(f"  ... 还有 {len(other_keys) - 10} 个")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"× 数据库访问错误: {e}")
    except Exception as e:
        print(f"× 未知错误: {e}")

def create_test_files():
    """创建一些测试文件用于验证清理功能"""
    print("\n" + "=" * 60)
    print("创建测试文件")
    print("=" * 60)
    
    test_dirs = [
        get_user_home() / '.verdent' / 'projects',
        get_user_home() / '.verdent' / 'logs',
    ]
    
    for dir_path in test_dirs:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"✓ 创建目录: {dir_path}")
        
        # 创建测试文件
        test_file = dir_path / f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        test_file.write_text(f"测试文件 - {datetime.now()}")
        print(f"✓ 创建文件: {test_file}")

def verify_cleanup():
    """验证清理后的状态"""
    print("\n" + "=" * 60)
    print("验证清理结果")
    print("=" * 60)
    
    print("\n期望的清理结果:")
    print("1. 所有指定文件夹内容已清空（文件夹本身保留）")
    print("2. state.vscdb 中的 deviceId 已重置为新值")
    print("3. 其他 VS Code 配置保持不变")
    
    print("\n请运行应用并执行'完全清理'功能，然后再次运行此脚本验证结果。")

def main():
    """主函数"""
    print("Verdent 完全清理功能测试工具")
    print("版本: 1.0.0")
    print("-" * 60)
    
    while True:
        print("\n请选择操作:")
        print("1. 检查文件夹状态")
        print("2. 检查 state.vscdb")
        print("3. 创建测试文件")
        print("4. 验证清理结果")
        print("5. 全部执行")
        print("0. 退出")
        
        choice = input("\n请输入选项 (0-5): ").strip()
        
        if choice == '0':
            break
        elif choice == '1':
            check_directory_status()
        elif choice == '2':
            check_vscode_state_db()
        elif choice == '3':
            create_test_files()
        elif choice == '4':
            verify_cleanup()
        elif choice == '5':
            check_directory_status()
            check_vscode_state_db()
            create_test_files()
            verify_cleanup()
        else:
            print("无效选项，请重试")
    
    print("\n测试完成！")

if __name__ == "__main__":
    main()
