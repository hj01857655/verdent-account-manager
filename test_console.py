#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试脚本 - 用于在Python控制台中直接测试凭证更改器功能
"""

import sys
import os
import time

# 添加当前目录到路径，以便导入credential_changer模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from credential_changer import CredentialChanger


def test_get_credential():
    """测试获取凭证功能"""
    print("=== 测试获取凭证功能 ===")
    
    # 创建凭证更改器实例
    changer = CredentialChanger()
    
    # 测试获取您提供的凭证
    target_name = "LegacyGeneric:target=ai.verdent.deck/access-token"
    print(f"尝试获取凭证: {target_name}")
    
    try:
        # 获取凭证信息
        cred = changer.cred_manager.get_credential(target_name)
        
        if cred:
            print("成功获取凭证信息:")
            print(f"  条目名称: {cred.get('entry_name', '')}")
            print(f"  用户名: {cred.get('user_name', '')}")
            print(f"  条目类型: {cred.get('entry_type', '')}")
            print(f"  持久性: {cred.get('persist', '')}")
            print(f"  修改时间: {cred.get('modified_time', '')}")
            print(f"  密码: {cred.get('password', '')}")
            print(f"  完整路径: {cred.get('full_path', '')}")
        else:
            print(f"未找到凭证: {target_name}")
    except Exception as e:
        print(f"获取凭证时出错: {str(e)}")
    
    print("\n")


def test_list_credentials():
    """测试列出所有凭证功能"""
    print("=== 测试列出所有凭证功能 ===")
    
    # 创建凭证更改器实例
    changer = CredentialChanger()
    
    try:
        # 列出所有凭证
        credentials = changer.cred_manager.list_credentials()
        
        if credentials:
            print(f"找到 {len(credentials)} 个凭证:")
            print(f"{'条目名称':<50} {'用户名':<30} {'类型':<20} {'持久性':<12}")
            print("-" * 112)
            
            for cred in credentials:
                entry_name = cred.get('entry_name', '') or ''
                username = cred.get('user_name', '') or ''
                entry_type = cred.get('entry_type', '') or ''
                persist = cred.get('persist', '') or ''
                
                print(f"{entry_name:<50} {username:<30} {entry_type:<20} {persist:<12}")
        else:
            print("没有找到凭证")
    except Exception as e:
        print(f"列出凭证时出错: {str(e)}")
    
    print("\n")


def test_update_token():
    """测试更新令牌功能"""
    print("=== 测试更新令牌功能 ===")
    
    # 创建凭证更改器实例
    changer = CredentialChanger()
    
    target_name = "LegacyGeneric:target=ai.verdent.deck/access-token"
    new_token = "test_token_" + str(int(time.time()))
    
    print(f"尝试更新令牌: {target_name}")
    
    try:
        # 检查凭证是否存在
        existing_cred = changer.cred_manager.get_credential(target_name)
        
        if existing_cred:
            print("找到现有凭证，准备更新...")
            # 显示当前令牌信息
            current_password = existing_cred.get("password", "")
            print(f"当前令牌: {current_password[:50]}..." if len(current_password) > 50 else f"当前令牌: {current_password}")
            
            # 更新令牌
            changer.update_access_token(target_name, new_token)
            
            # 验证更新
            updated_cred = changer.cred_manager.get_credential(target_name)
            if updated_cred:
                updated_password = updated_cred.get("password", "")
                print(f"更新后令牌: {updated_password[:50]}..." if len(updated_password) > 50 else f"更新后令牌: {updated_password}")
                
                # 检查新令牌是否存在于更新后的凭证中
                if new_token in updated_password:
                    print("✓ 令牌更新验证成功")
                else:
                    print("✗ 令牌更新验证失败")
            else:
                print("✗ 无法获取更新后的凭证")
        else:
            print(f"未找到凭证: {target_name}")
            print("尝试创建新凭证...")
            
            # 尝试创建新凭证
            changer.create_access_token(target_name, new_token)
            
            # 验证创建
            created_cred = changer.cred_manager.get_credential(target_name)
            if created_cred:
                created_password = created_cred.get("password", "")
                print(f"创建后令牌: {created_password[:50]}..." if len(created_password) > 50 else f"创建后令牌: {created_password}")
                
                # 检查新令牌是否存在于创建的凭证中
                if new_token in created_password:
                    print("✓ 令牌创建验证成功")
                else:
                    print("✗ 令牌创建验证失败")
            else:
                print("✗ 无法获取创建后的凭证")
    except Exception as e:
        print(f"更新/创建令牌时出错: {str(e)}")
    
    print("\n")


# 主函数
if __name__ == "__main__":
    print("凭证更改器测试脚本")
    print("在Python控制台中运行以下命令来测试功能:\n")
    
    print("1. 测试获取特定凭证:")
    print("   test_get_credential()")
    print()
    
    print("2. 测试列出所有凭证:")
    print("   test_list_credentials()")
    print()
    
    print("3. 测试更新令牌:")
    print("   test_update_token()")
    print()
    
    print("或者运行所有测试:")
    print("   test_get_credential()")
    print("   test_list_credentials()")
    print("   test_update_token()")
    print()
    
    # 自动运行测试
    print("自动运行所有测试...")
    test_get_credential()
    test_list_credentials()
    test_update_token()
    print("测试完成!")