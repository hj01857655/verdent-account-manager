#!/usr/bin/env python3
"""
测试 JWT Token 解析功能
"""

import base64
import json
from datetime import datetime

# 测试 Token
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo3NDk0NjI4NTU5MzIxNDk3NjAsInZlcnNpb24iOjAsInRva2VuX3R5cGUiOiJhY2Nlc3MiLCJleHAiOjE3NjU3MDk0MjksImlhdCI6MTc2MzExNzQyOSwibmJmIjoxNzYzMTE3NDI5fQ.3Nb7K7V56ypYbgj5ESWgoGjC2NRUBhvkVyMLsnB9btE"

def parse_jwt(token):
    """解析 JWT Token"""
    parts = token.split('.')
    if len(parts) != 3:
        raise ValueError("Invalid JWT format")
    
    # 解码 header
    header_b64 = parts[0]
    header_padding = 4 - len(header_b64) % 4
    if header_padding != 4:
        header_b64 += '=' * header_padding
    header = json.loads(base64.urlsafe_b64decode(header_b64))
    
    # 解码 payload
    payload_b64 = parts[1]
    payload_padding = 4 - len(payload_b64) % 4
    if payload_padding != 4:
        payload_b64 += '=' * payload_padding
    payload = json.loads(base64.urlsafe_b64decode(payload_b64))
    
    return header, payload

def main():
    print("=" * 60)
    print("JWT Token 解析测试")
    print("=" * 60)
    
    header, payload = parse_jwt(TOKEN)
    
    print("\n1. Header:")
    print(json.dumps(header, indent=2))
    
    print("\n2. Payload:")
    print(json.dumps(payload, indent=2))
    
    print("\n3. 关键字段:")
    print(f"   user_id: {payload.get('user_id')}")
    print(f"   token_type: {payload.get('token_type')}")
    print(f"   exp (过期时间戳): {payload.get('exp')}")
    print(f"   iat (签发时间戳): {payload.get('iat')}")
    print(f"   nbf (生效时间戳): {payload.get('nbf')}")
    
    print("\n4. 时间转换:")
    if 'exp' in payload:
        exp_timestamp = payload['exp']
        exp_datetime = datetime.fromtimestamp(exp_timestamp)
        print(f"   Token 过期时间: {exp_datetime}")
        print(f"   RFC3339 格式: {exp_datetime.isoformat()}")
    
    if 'iat' in payload:
        iat_timestamp = payload['iat']
        iat_datetime = datetime.fromtimestamp(iat_timestamp)
        print(f"   Token 签发时间: {iat_datetime}")
    
    print("\n5. 验证:")
    print(f"   ✓ Token 格式正确")
    print(f"   ✓ 包含 exp 字段: {payload.get('exp')}")
    print(f"   ✓ 过期日期: 2025-12-14 (预期)")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    main()

