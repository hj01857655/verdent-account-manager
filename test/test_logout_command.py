#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Verdent 插件 logout 功能
支持多种触发方式: 命令行、直接操作数据库、清除文件
"""

import sqlite3
import subprocess
import sys
import time
import os
from pathlib import Path

def check_vscode_process():
    """检查 VS Code 进程是否运行"""
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq Code.exe"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return "Code.exe" in result.stdout
    except Exception:
        return False

def logout_via_command():
    """方法 1: 通过命令行调用 verdent.logout"""
    print("[方法 1] 通过 code 命令调用 verdent.logout...")
    
    # 查找 code 命令
    code_paths = [
        r"D:\Programs\Microsoft VS Code\bin\code.cmd",
        r"C:\Program Files\Microsoft VS Code\bin\code.cmd",
        os.path.join(os.environ.get('LOCALAPPDATA', ''), r"Programs\Microsoft VS Code\bin\code.cmd"),
    ]
    
    code_cmd = None
    for path in code_paths:
        if os.path.exists(path):
            code_cmd = path
            break
    
    if not code_cmd:
        # 尝试使用 where 命令查找
        try:
            result = subprocess.run(
                ["where", "code"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                code_cmd = result.stdout.strip().split('\n')[0]
        except Exception:
            pass
    
    if not code_cmd:
        print("  [X] 未找到 code 命令")
        return False
    
    print(f"  [i] 使用命令: {code_cmd}")
    
    try:
        result = subprocess.run(
            [code_cmd, "--command", "verdent.logout"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("  [OK] 命令执行成功")
            return True
        else:
            print(f"  [X] 命令执行失败 (退出码: {result.returncode})")
            if result.stderr:
                print(f"  错误: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("  [X] 命令执行超时")
        return False
    except Exception as e:
        print(f"  [X] 错误: {e}")
        return False

def logout_via_database():
    """方法 2: 直接操作 state.vscdb 数据库"""
    print("[方法 2] 直接清除 state.vscdb 数据库中的数据...")
    
    db_path = Path(os.environ.get('APPDATA', '')) / r'Code\User\globalStorage\state.vscdb'
    
    if not db_path.exists():
        print(f"  [X] 数据库不存在: {db_path}")
        return False
    
    # 检查 VS Code 是否运行
    if check_vscode_process():
        print("  [!] VS Code 正在运行,数据库可能被锁定")
        print("  [i] 建议关闭 VS Code 后再操作数据库")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 查询要删除的记录
        cursor.execute("""
            SELECT key FROM ItemTable 
            WHERE key LIKE '%verdent%ycAuthToken%'
               OR key LIKE '%verdent%authNonce%'
               OR key LIKE '%verdent%verdentApiKey%'
               OR key LIKE 'verdentai.verdent.verdent_userInfo%'
               OR key LIKE 'verdentai.verdent.verdent_apiProvider%'
        """)
        
        records = cursor.fetchall()
        count = len(records)
        
        if count == 0:
            print("  [i] 没有找到需要清除的数据")
            conn.close()
            return True
        
        print(f"  [i] 找到 {count} 条记录:")
        for record in records:
            key = record[0]
            if 'secret://' in key:
                print(f"    - Secret: {key[9:60]}...")
            else:
                print(f"    - State: {key}")
        
        # 删除记录
        cursor.execute("""
            DELETE FROM ItemTable 
            WHERE key LIKE '%verdent%ycAuthToken%'
               OR key LIKE '%verdent%authNonce%'
               OR key LIKE '%verdent%verdentApiKey%'
               OR key LIKE 'verdentai.verdent.verdent_userInfo%'
               OR key LIKE 'verdentai.verdent.verdent_apiProvider%'
        """)
        
        conn.commit()
        conn.close()
        
        print(f"  [OK] 已清除 {count} 条记录")
        return True
        
    except sqlite3.OperationalError as e:
        print(f"  [X] 数据库被锁定: {e}")
        print("  [i] 请关闭 VS Code 后重试")
        return False
    except Exception as e:
        print(f"  [X] 清除失败: {e}")
        return False

def logout_via_files():
    """方法 3: 清除扩展文件目录"""
    print("[方法 3] 清除 Verdent 扩展文件目录...")
    
    base_path = Path(os.environ.get('APPDATA', '')) / r'Code\User\globalStorage\verdentai.verdent'
    
    if not base_path.exists():
        print(f"  [i] 目录不存在: {base_path}")
        return True
    
    try:
        import shutil
        shutil.rmtree(base_path)
        print(f"  [OK] 已删除目录: {base_path}")
        return True
    except Exception as e:
        print(f"  [X] 删除失败: {e}")
        return False

def verify_logout():
    """验证 logout 是否成功"""
    print("\n[验证] 检查登出状态...")
    
    db_path = Path(os.environ.get('APPDATA', '')) / r'Code\User\globalStorage\state.vscdb'
    
    if not db_path.exists():
        print("  [X] 数据库不存在")
        return False
    
    if check_vscode_process():
        print("  [!] VS Code 正在运行,无法验证数据库")
        print("  [i] 请手动检查 VS Code 中的 Verdent 侧边栏")
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) FROM ItemTable 
            WHERE key LIKE '%verdent%ycAuthToken%'
               OR key LIKE '%verdent%authNonce%'
               OR key LIKE '%verdent%verdentApiKey%'
               OR key LIKE 'verdentai.verdent.verdent_userInfo%'
        """)
        
        count = cursor.fetchone()[0]
        conn.close()
        
        if count == 0:
            print("  [OK] 数据已清除,登出成功")
            return True
        else:
            print(f"  [X] 仍有 {count} 条记录未清除")
            return False
            
    except Exception as e:
        print(f"  [X] 验证失败: {e}")
        return False

def test_logout():
    """测试 logout 功能"""
    
    print("=" * 70)
    print("测试 Verdent Logout 功能")
    print("=" * 70)
    print()
    
    # 检查 VS Code 是否运行
    print("[检查] VS Code 进程状态...")
    is_running = check_vscode_process()
    if is_running:
        print("  [OK] VS Code 正在运行")
    else:
        print("  [!] VS Code 未运行")
    print()
    
    # 尝试方法 1: 命令行
    success1 = logout_via_command()
    print()
    
    # 如果方法 1 失败,尝试方法 2: 数据库
    if not success1:
        success2 = logout_via_database()
        print()
        
        # 如果方法 2 也失败,尝试方法 3: 文件
        if not success2:
            success3 = logout_via_files()
            print()
    
    # 验证结果
    if is_running:
        print("=" * 70)
        print("[OK] Logout 操作已执行")
        print("=" * 70)
        print()
        print("[i] 请手动检查 VS Code 窗口:")
        print("  - 打开 Verdent 侧边栏")
        print("  - 应显示登录界面")
        print("  - 用户信息应已清空")
        print()
    else:
        verify_result = verify_logout()
        print()
        print("=" * 70)
        if verify_result:
            print("[OK] 测试完成 - Logout 成功")
        else:
            print("[!] 测试完成 - 请启动 VS Code 验证")
        print("=" * 70)
    
    return True

if __name__ == "__main__":
    try:
        test_logout()
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n\n[X] 用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[X] 未预期的错误: {e}")
        sys.exit(1)
