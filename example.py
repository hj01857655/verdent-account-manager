#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
凭证更改器示例脚本
演示如何使用CredentialChanger类来管理Windows凭证
"""

import sys
import os
import datetime
import json

# 添加当前目录到路径，以便导入credential_changer模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from credential_changer import CredentialChanger


def main():
    """主函数 - 演示凭证更改器的使用"""
    print("=== Windows凭证更改器示例 ===\n")
    
    # 创建凭证更改器实例
    changer = CredentialChanger()
    
    # 示例1: 列出所有凭证
    print("1. 列出系统中的所有凭证:")
    print("-" * 50)
    changer.list_all_credentials()
    print("\n")
    
    # 示例2: 获取特定凭证信息
    target_name = "LegacyGeneric:target=ai.verdent.deck/access-token"
    print(f"2. 获取凭证 '{target_name}' 的详细信息:")
    print("-" * 50)
    changer.get_credential_info(target_name)
    print("\n")
    
    # 示例3: 创建新的访问令牌
    print("3. 创建新的访问令牌凭证:")
    print("-" * 50)
    new_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo3NDk0NjAyMjQwNDMxODgyMjQsInZlcnNpb24iOjAsInRva2VuX3R5cGUiOiJhY2Nlc3MiLCJleHAiOjE3NjU1NTYzNzgsImlhdCI6MTc2Mjk2NDM3OCwibmJmIjoxNzYyOTY0Mzc4fQ.P4PmrRxnYDGznmzfK1Yxi1xCSivbJDcQ2dbIDAaakE4"
    expire_time = int(datetime.datetime.now().timestamp() * 1000) + 86400000  # 24小时后过期
    
    # 创建一个测试令牌
    test_target = "test.example.com/access-token"
    changer.create_access_token(test_target, new_token, expire_time)
    
    # 验证创建的令牌
    print(f"验证创建的令牌 '{test_target}':")
    changer.get_credential_info(test_target)
    print("\n")
    
    # 示例4: 更新访问令牌
    print("4. 更新访问令牌:")
    print("-" * 50)
    updated_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo5OTk5OTk5OTk5OTk5OTk5OTk5LCJ2ZXJzaW9uIjoxLCJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzY1NTU2Mzc4LCJpYXQiOjE3NjI5NjQzNzgsIm5iZiI6MTc2Mjk2NDM3OH0.updated_signature"
    new_expire_time = int(datetime.datetime.now().timestamp() * 1000) + 172800000  # 48小时后过期
    
    changer.update_access_token(test_target, updated_token, new_expire_time)
    
    # 验证更新的令牌
    print(f"验证更新的令牌 '{test_target}':")
    changer.get_credential_info(test_target)
    print("\n")
    
    # 示例5: 删除测试凭证
    print("5. 删除测试凭证:")
    print("-" * 50)
    changer.delete_credential(test_target)
    print("\n")
    
    # 示例6: 更新原始凭证（如果存在）
    print("6. 更新原始凭证（如果存在）:")
    print("-" * 50)
    original_target = "LegacyGeneric:target=ai.verdent.deck/access-token"
    
    # 检查原始凭证是否存在
    original_cred = changer.cred_manager.get_credential(original_target)
    if original_cred:
        print(f"找到原始凭证 '{original_target}'，准备更新...")
        
        # 解析原始令牌数据
        try:
            password_str = original_cred.get("password", "")
            if password_str.startswith("{") and password_str.endswith("}"):
                token_data = json.loads(password_str)
                print(f"原始令牌过期时间: {datetime.datetime.fromtimestamp(token_data.get('expireAt', 0) / 1000)}")
            
            # 更新令牌
            changer.update_access_token(original_target, new_token, new_expire_time)
        except Exception as e:
            print(f"更新原始凭证时出错: {str(e)}")
    else:
        print(f"未找到原始凭证 '{original_target}'")
    
    print("\n=== 示例完成 ===")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"运行示例时出错: {str(e)}")
        input("按任意键退出...")