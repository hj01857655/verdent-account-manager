#!/usr/bin/env python3
"""
测试 Verdent API 响应,查看 /user/center/info 返回的数据结构
"""

import requests
import json

# 测试 Token
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo3NDk0NjI4NTU5MzIxNDk3NjAsInZlcnNpb24iOjAsInRva2VuX3R5cGUiOiJhY2Nlc3MiLCJleHAiOjE3NjU3MDk0MjksImlhdCI6MTc2MzExNzQyOSwibmJmIjoxNzYzMTE3NDI5fQ.3Nb7K7V56ypYbgj5ESWgoGjC2NRUBhvkVyMLsnB9btE"

def test_user_info():
    """测试 /user/center/info 端点"""
    print("=" * 60)
    print("测试 API: /user/center/info")
    print("=" * 60)
    
    url = "https://agent.verdent.ai/user/center/info"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Cookie": f"token={TOKEN}",
        "Origin": "https://www.verdent.ai",
        "Referer": "https://www.verdent.ai/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"\n状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n完整响应 JSON:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # 分析数据结构
            if data.get('data'):
                user_data = data['data']
                print("\n" + "=" * 60)
                print("关键字段分析:")
                print("=" * 60)
                
                # 检查过期时间相关字段
                expire_fields = [
                    'expireTime', 'expire_time', 'expiresAt', 'expires_at',
                    'expiredAt', 'expired_at', 'validUntil', 'valid_until'
                ]
                
                print("\n1. 过期时间相关字段:")
                for field in expire_fields:
                    if field in user_data:
                        print(f"   ✓ {field}: {user_data[field]}")
                
                # 检查订阅信息
                if 'subscriptionInfo' in user_data:
                    print("\n2. 订阅信息 (subscriptionInfo):")
                    sub_info = user_data['subscriptionInfo']
                    print(json.dumps(sub_info, indent=4, ensure_ascii=False))
                
                # 检查 Token 信息
                if 'tokenInfo' in user_data:
                    print("\n3. Token 信息 (tokenInfo):")
                    token_info = user_data['tokenInfo']
                    print(json.dumps(token_info, indent=4, ensure_ascii=False))
                
                # 列出所有顶级字段
                print("\n4. 所有顶级字段:")
                for key in user_data.keys():
                    print(f"   - {key}")
        else:
            print(f"\n错误: HTTP {response.status_code}")
            print(response.text)
    
    except Exception as e:
        print(f"\n异常: {e}")

def test_jwt_decode():
    """解析 JWT Token 中的过期时间"""
    print("\n" + "=" * 60)
    print("解析 JWT Token")
    print("=" * 60)
    
    import base64
    
    try:
        # JWT 格式: header.payload.signature
        parts = TOKEN.split('.')
        if len(parts) != 3:
            print("Token 格式错误")
            return
        
        # 解码 payload (需要添加 padding)
        payload = parts[1]
        # 添加必要的 padding
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += '=' * padding
        
        decoded = base64.urlsafe_b64decode(payload)
        payload_data = json.loads(decoded)
        
        print("\nJWT Payload:")
        print(json.dumps(payload_data, indent=2, ensure_ascii=False))
        
        if 'exp' in payload_data:
            import datetime
            exp_timestamp = payload_data['exp']
            exp_date = datetime.datetime.fromtimestamp(exp_timestamp)
            print(f"\n过期时间戳 (exp): {exp_timestamp}")
            print(f"过期日期: {exp_date}")
            print(f"RFC3339 格式: {exp_date.isoformat()}")
    
    except Exception as e:
        print(f"\n解析失败: {e}")

if __name__ == "__main__":
    # 测试 API
    test_user_info()
    
    # 解析 JWT
    test_jwt_decode()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

