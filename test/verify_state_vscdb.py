"""
验证 VS Code state.vscdb 数据库中的 token 存储
"""
import sqlite3
import os
import json

# VS Code globalStorage 路径
appdata = os.environ.get('APPDATA')
state_db_path = os.path.join(appdata, r'Code\User\globalStorage\state.vscdb')

print(f"数据库路径: {state_db_path}")
print(f"文件存在: {os.path.exists(state_db_path)}")
print(f"文件大小: {os.path.getsize(state_db_path)} bytes\n")

# 连接数据库
conn = sqlite3.connect(state_db_path)
cursor = conn.cursor()

# 1. 查看表结构
print("=" * 80)
print("数据库表结构")
print("=" * 80)
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
for table in tables:
    print(f"\n表名: {table[0]}")
    cursor.execute(f"PRAGMA table_info({table[0]})")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]} ({col[2]})")

# 2. 查找所有与 verdent 相关的键
print("\n" + "=" * 80)
print("Verdent 相关的所有存储项")
print("=" * 80)
cursor.execute("SELECT key, value FROM ItemTable WHERE key LIKE '%verdent%'")
verdent_items = cursor.fetchall()

for key, value in verdent_items:
    print(f"\nKey: {key}")
    print(f"Value类型: {type(value)}")
    print(f"Value长度: {len(value) if value else 0} bytes")
    
    # 尝试解析为文本
    if value:
        # 判断是字节还是字符串
        if isinstance(value, bytes):
            # 检查是否是加密数据（通常以 v10 开头）
            if value[:3] == b'v10':
                print(f"加密格式: v10")
                print(f"十六进制前64字节: {value[:64].hex()}")
            else:
                try:
                    text = value.decode('utf-8')
                    print(f"文本内容: {text[:200]}")
                    try:
                        parsed = json.loads(text)
                        print(f"JSON解析成功，类型: {type(parsed)}")
                    except:
                        pass
                except:
                    print(f"十六进制前64字节: {value[:64].hex()}")
        else:
            # 已经是字符串
            print(f"文本内容: {value[:200]}")
            try:
                parsed = json.loads(value)
                print(f"JSON解析成功，类型: {type(parsed)}")
            except:
                pass

# 3. 查找 SecretStorage 相关项
print("\n" + "=" * 80)
print("所有 SecretStorage 项 (secret:// 开头)")
print("=" * 80)
cursor.execute("SELECT key, value FROM ItemTable WHERE key LIKE 'secret://%'")
secret_items = cursor.fetchall()

for key, value in secret_items:
    print(f"\nSecret Key: {key}")
    if value:
        if isinstance(value, bytes):
            print(f"长度: {len(value)} bytes")
            print(f"加密版本: {value[:3].decode('ascii', errors='ignore')}")
            print(f"十六进制前32字节: {value[:32].hex()}")
        else:
            print(f"字符串值: {value[:100]}")

# 4. 专门查找 ycAuthToken
print("\n" + "=" * 80)
print("ycAuthToken 查询")
print("=" * 80)
cursor.execute("SELECT key, value FROM ItemTable WHERE key LIKE '%ycAuthToken%'")
token_items = cursor.fetchall()

for key, value in token_items:
    print(f"\nToken Key: {key}")
    if value:
        if isinstance(value, bytes):
            print(f"总长度: {len(value)} bytes")
            print(f"前缀: {value[:10].hex()}")
            print(f"加密标识: {value[:3]}")
            print(f"完整十六进制:\n{value.hex()}")
        else:
            print(f"字符串值: {value}")

# 5. 统计信息
print("\n" + "=" * 80)
print("数据库统计")
print("=" * 80)
cursor.execute("SELECT COUNT(*) FROM ItemTable")
total_count = cursor.fetchone()[0]
print(f"总记录数: {total_count}")

cursor.execute("SELECT COUNT(*) FROM ItemTable WHERE key LIKE 'secret://%'")
secret_count = cursor.fetchone()[0]
print(f"SecretStorage 记录数: {secret_count}")

cursor.execute("SELECT COUNT(*) FROM ItemTable WHERE key LIKE '%verdent%'")
verdent_count = cursor.fetchone()[0]
print(f"Verdent 相关记录数: {verdent_count}")

conn.close()
print("\n完成！")
