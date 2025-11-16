#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试随机密码生成功能
"""

import sys
import os

# 添加父目录到路径以导入 verdent_auto_register
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from verdent_auto_register import VerdentAutoRegister
import re


def test_password_strength(password: str) -> dict:
    """
    测试密码强度
    
    Returns:
        包含测试结果的字典
    """
    results = {
        "password": password,
        "length": len(password),
        "has_uppercase": bool(re.search(r'[A-Z]', password)),
        "has_lowercase": bool(re.search(r'[a-z]', password)),
        "has_digit": bool(re.search(r'[0-9]', password)),
        "has_special": bool(re.search(r'[@#$%&*]', password)),
        "valid_length": 12 <= len(password) <= 16,
    }
    
    results["is_valid"] = all([
        results["has_uppercase"],
        results["has_lowercase"],
        results["has_digit"],
        results["has_special"],
        results["valid_length"]
    ])
    
    return results


def main():
    print("="*70)
    print("测试随机密码生成功能")
    print("="*70)
    
    # 测试 1: 生成 10 个随机密码并验证
    print("\n[测试 1] 生成 10 个随机密码并验证强度")
    print("-"*70)
    
    all_valid = True
    passwords = []
    
    for i in range(10):
        password = VerdentAutoRegister.generate_random_password()
        passwords.append(password)
        result = test_password_strength(password)
        
        status = "✓" if result["is_valid"] else "✗"
        print(f"{status} 密码 {i+1}: {password}")
        print(f"   长度: {result['length']} | "
              f"大写: {'✓' if result['has_uppercase'] else '✗'} | "
              f"小写: {'✓' if result['has_lowercase'] else '✗'} | "
              f"数字: {'✓' if result['has_digit'] else '✗'} | "
              f"特殊: {'✓' if result['has_special'] else '✗'}")
        
        if not result["is_valid"]:
            all_valid = False
            print(f"   [警告] 密码不符合要求!")
    
    # 测试 2: 验证密码唯一性
    print("\n[测试 2] 验证密码唯一性")
    print("-"*70)
    unique_passwords = set(passwords)
    print(f"生成的密码数量: {len(passwords)}")
    print(f"唯一密码数量: {len(unique_passwords)}")
    
    if len(unique_passwords) == len(passwords):
        print("✓ 所有密码都是唯一的")
    else:
        print("✗ 发现重复密码!")
        all_valid = False
    
    # 测试 3: 测试不同长度
    print("\n[测试 3] 测试不同长度的密码生成")
    print("-"*70)
    
    for length in [12, 14, 16]:
        password = VerdentAutoRegister.generate_random_password(length)
        result = test_password_strength(password)
        status = "✓" if result["is_valid"] and result["length"] == length else "✗"
        print(f"{status} 长度 {length}: {password} (实际长度: {result['length']})")
    
    # 测试 4: 测试边界情况
    print("\n[测试 4] 测试边界情况")
    print("-"*70)
    
    # 长度小于 12 应该自动调整为 12
    password_short = VerdentAutoRegister.generate_random_password(8)
    print(f"请求长度 8,实际长度: {len(password_short)} (应为 12)")
    
    # 长度大于 16 应该自动调整为 16
    password_long = VerdentAutoRegister.generate_random_password(20)
    print(f"请求长度 20,实际长度: {len(password_long)} (应为 16)")
    
    # 总结
    print("\n" + "="*70)
    if all_valid:
        print("✓ 所有测试通过!")
        return 0
    else:
        print("✗ 部分测试失败!")
        return 1


if __name__ == "__main__":
    sys.exit(main())

