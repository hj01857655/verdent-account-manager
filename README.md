# 凭证更改器

这是一个用于管理Windows凭证管理器中凭证的Python工具。它可以列出、创建、更新和删除Windows系统中的凭证，特别适用于管理访问令牌等敏感信息。

## 功能特点

- 列出系统中的所有凭证
- 获取特定凭证的详细信息
- 创建新凭证
- 更新现有凭证
- 删除凭证
- 专门用于管理访问令牌的功能

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 基本命令

1. **列出所有凭证**
   ```bash
   python credential_changer.py list
   ```
   
   以JSON格式输出：
   ```bash
   python credential_changer.py list --format json
   ```

2. **获取特定凭证信息**
   ```bash
   python credential_changer.py get "LegacyGeneric:target=ai.verdent.deck/access-token"
   ```

3. **创建新凭证**
   ```bash
   python credential_changer.py create "myapp.com/token" "username" "password123"
   ```

4. **更新凭证**
   ```bash
   python credential_changer.py update "myapp.com/token" "username" "newpassword123"
   ```

5. **删除凭证**
   ```bash
   python credential_changer.py delete "myapp.com/token"
   ```

### 访问令牌管理

1. **创建访问令牌**
   ```bash
   python credential_changer.py create-token "ai.verdent.deck/access-token" "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
   ```
   
   指定过期时间（毫秒时间戳）：
   ```bash
   python credential_changer.py create-token "ai.verdent.deck/access-token" "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." --expire 1765556378000
   ```

2. **更新访问令牌**
   ```bash
   python credential_changer.py update-token "ai.verdent.deck/access-token" "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
   ```
   
   指定新的过期时间：
   ```bash
   python credential_changer.py update-token "ai.verdent.deck/access-token" "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." --expire 1765556378000
   ```

## 示例

### 更新您提供的凭证

根据您提供的信息，要更新 `ai.verdent.deck/access-token` 凭证：

```bash
python credential_changer.py update-token "LegacyGeneric:target=ai.verdent.deck/access-token" "新的访问令牌" --expire 1765556378000
```

### 查看凭证详细信息

```bash
python credential_changer.py get "LegacyGeneric:target=ai.verdent.deck/access-token"
```

## 注意事项

1. 此工具需要管理员权限才能访问和修改Windows凭证管理器中的凭证
2. 操作凭证时请谨慎，错误的操作可能导致应用程序无法正常工作
3. 访问令牌通常有过期时间，请确保在令牌过期前更新

## 安全性

- 此工具直接与Windows凭证管理器交互，不会在磁盘上保存任何敏感信息
- 所有操作都在内存中进行，确保凭证信息的安全性
- 建议在使用完毕后关闭命令行窗口，防止敏感信息泄露