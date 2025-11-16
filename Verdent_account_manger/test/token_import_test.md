# Token 导入功能测试指南

## 测试准备

### 1. 获取测试 Token

你需要一个有效的 Verdent Token 来测试导入功能。可以通过以下方式获取:

**方法 1: 从现有账户获取**
- 登录 Verdent AI 网站
- 打开浏览器开发者工具 (F12)
- 进入 Application/Storage -> Cookies
- 找到 `token` 字段,复制其值

**方法 2: 从已注册账户获取**
- 在账户管理器中查看已有账户
- 复制账户的 Token 字段

### 2. 准备测试数据

创建一个测试文件 `test_tokens.txt`,每行一个 Token:
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5ODc2NTQzMjEwIiwibmFtZSI6IkphbmUgU21pdGgiLCJpYXQiOjE1MTYyMzkwMjJ9.kPH7rZvVvZ8vZ8vZ8vZ8vZ8vZ8vZ8vZ8vZ8vZ8vZ8vZ
```

## 测试用例

### 测试用例 1: 单个 Token 导入 (新账户)

**步骤**:
1. 启动应用程序
2. 点击 "📥 导入 Token" 按钮
3. 在文本框中粘贴一个有效的 Token
4. 点击 "开始导入"

**预期结果**:
- ✅ 显示 loading 状态
- ✅ 导入成功提示: "导入完成! 成功: 1 个 失败: 0 个"
- ✅ 账户列表中出现新账户
- ✅ 账户信息完整 (邮箱、订阅类型、额度等)

**验证点**:
- 邮箱地址正确
- 订阅类型显示正确 (Free/Starter/Pro/Max)
- 额度信息准确 (剩余/已用/总计)
- Token 已保存
- 密码字段为空 (正常现象)

---

### 测试用例 2: 单个 Token 导入 (更新现有账户)

**步骤**:
1. 使用已存在的账户的 Token
2. 点击 "📥 导入 Token" 按钮
3. 粘贴该账户的 Token
4. 点击 "开始导入"

**预期结果**:
- ✅ 导入成功
- ✅ 账户信息被更新
- ✅ 不会创建重复账户
- ✅ `last_updated` 时间更新

**验证点**:
- 账户数量不变
- 账户信息已更新为最新
- 后端日志显示 "账户已存在,更新信息..."

---

### 测试用例 3: 批量导入多个 Token

**步骤**:
1. 点击 "📥 导入 Token" 按钮
2. 粘贴 3-5 个 Token (每行一个)
3. 点击 "开始导入"

**预期结果**:
- ✅ 显示 loading 状态
- ✅ 逐个处理 Token (控制台可见进度)
- ✅ 显示统计结果
- ✅ 所有成功的账户都已添加

**验证点**:
- 导入速度合理 (每个 Token 间隔约 500ms)
- 成功数量正确
- 失败数量正确 (如有)
- 账户列表正确更新

---

### 测试用例 4: 无效 Token 处理

**步骤**:
1. 点击 "📥 导入 Token" 按钮
2. 粘贴一个无效的 Token (如: "invalid_token_123")
3. 点击 "开始导入"

**预期结果**:
- ✅ 导入失败
- ✅ 显示错误信息: "导入完成! 成功: 0 个 失败: 1 个"
- ✅ 失败详情中包含错误原因

**验证点**:
- 不会创建账户
- 错误信息清晰明确
- 应用不会崩溃

---

### 测试用例 5: 空 Token 处理

**步骤**:
1. 点击 "📥 导入 Token" 按钮
2. 不输入任何内容或只输入空行
3. 点击 "开始导入"

**预期结果**:
- ✅ 显示提示: "请输入至少一个 Token"
- ✅ 对话框不关闭
- ✅ 不执行导入操作

---

### 测试用例 6: 混合导入 (有效 + 无效)

**步骤**:
1. 点击 "📥 导入 Token" 按钮
2. 粘贴 3 个 Token:
   - 第 1 个: 有效 Token
   - 第 2 个: 无效 Token
   - 第 3 个: 有效 Token
3. 点击 "开始导入"

**预期结果**:
- ✅ 显示结果: "成功: 2 个 失败: 1 个"
- ✅ 失败详情显示第 2 个 Token 的错误
- ✅ 成功的账户已添加

---

### 测试用例 7: 网络错误处理

**步骤**:
1. 断开网络连接
2. 点击 "📥 导入 Token" 按钮
3. 粘贴有效 Token
4. 点击 "开始导入"

**预期结果**:
- ✅ 显示网络错误信息
- ✅ 导入失败
- ✅ 应用不会崩溃

---

## 后端日志验证

在测试过程中,检查后端控制台输出:

**成功导入的日志示例**:
```
[*] ========== 导入 Token 账户 ==========
[*] Token 长度: 123 字符
[*] 使用 Token 获取用户信息...
[✓] 成功获取用户信息
[*] 账户邮箱: test@example.com
[*] 额度信息:
    已消耗: 1.23
    总额度: 100.00
    剩余: 98.77
[*] 订阅信息:
    类型: Some("Pro")
    周期结束: Some(1234567890)
    自动续订: true
[*] 创建新账户...
[✓] 新账户已创建
[✓] Token 导入成功: test@example.com
======================================
```

**失败导入的日志示例**:
```
[*] ========== 导入 Token 账户 ==========
[*] Token 长度: 15 字符
[*] 使用 Token 获取用户信息...
[×] 获取用户信息失败: HTTP错误: 401 Unauthorized
```

## 性能测试

### 批量导入性能

测试导入 10 个 Token 的时间:
- 预期时间: 约 5-10 秒 (每个 Token 500ms 延迟 + API 请求时间)
- 内存占用: 应保持稳定,不会持续增长
- CPU 占用: 应保持在合理范围

## 数据验证

导入成功后,检查 `accounts.json` 文件:

```json
{
  "accounts": [
    {
      "id": "uuid-here",
      "email": "test@example.com",
      "password": "",
      "token": "eyJhbGci...",
      "quota_remaining": "98.77",
      "quota_used": "1.23",
      "quota_total": "100.00",
      "subscription_type": "Pro",
      "current_period_end": 1234567890,
      "auto_renew": true,
      "trial_days": 7,
      "expire_time": "2024-12-31T23:59:59+08:00",
      "status": "active",
      "last_updated": "2024-11-14T10:30:00+08:00"
    }
  ]
}
```

## 常见问题

### Q1: 导入后密码为空是否正常?
**A**: 是的,通过 Token 导入的账户没有密码。如需使用"测试登录"功能,请手动编辑账户添加密码。

### Q2: 如何获取 Token?
**A**: 从浏览器 Cookies 中获取,或从已登录的账户中复制。

### Q3: 导入失败怎么办?
**A**: 检查 Token 是否有效、网络连接是否正常、查看后端日志获取详细错误信息。

### Q4: 可以导入多少个 Token?
**A**: 理论上没有限制,但建议每次不超过 20 个,避免请求过快。

