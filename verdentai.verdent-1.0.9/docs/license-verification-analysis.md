# Verdent 许可证和试用版本验证逻辑分析

## 概述
本文档分析了 Verdent 扩展中与试用版本、许可证验证和订阅管理相关的所有代码逻辑。

---

## 1. 核心 API 函数

### 1.1 HTTP 请求包装器 - `Byr`
**位置**: `extension/dist/extension.js:585217-585258`

```javascript
var Byr = (t, e) => {
  let i = k1(t, {
    timeout: 3e4,
    headers: { "Content-Type": "application/json", ...e?.headers },
    ...e,
  });
  return {
    get: async (n, a) => {
      try {
        let s = await i.get(n, a),
          { errCode: r, errMsg: u, data: d } = s.data;
        if (r !== 0) throw { message: u, status: r };
        return d;
      } catch (s) {
        if (_s.isAxiosError(s)) {
          let r = s,
            u = r.response?.status || 0;
          throw { message: r.response?.data?.errMsg || r.message, status: u };
        }
        throw { message: s?.message ?? s };
      }
    },
    post: async (n, a, s) => {
      try {
        let r = await i.post(n, a, s),
          { errCode: u, errMsg: d, data: f } = r.data;
        if (u !== 0) throw { message: d, status: u };
        return f;
      } catch (r) {
        if (_s.isAxiosError(r)) {
          let u = r,
            d = u.response?.status || 0;
          throw { message: u.response?.data?.errMsg || u.message, status: d };
        }
        // ⚠️ 关键错误消息位置
        throw {
          message:
            "Free trial unavailable. If you have any questions, please contact us at hi@verdent.ai.",
        };
      }
    },
  };
};
```

**关键点**:
- 这是一个 HTTP 请求包装器，处理 `get` 和 `post` 请求
- 在 `post` 方法的 catch 块中，当发生非 Axios 错误时，抛出"Free trial unavailable"消息
- 超时时间: 30秒 (3e4 毫秒)
- 标准响应格式: `{ errCode, errMsg, data }`

---

### 1.2 订阅创建 API - `Syr`
**位置**: `extension/dist/extension.js:585259-585261`

```javascript
var Syr = function (t = "https://api.verdent.ai", e, i) {
  return Byr(t, i).post("verdent/subscription/create", e);
}
```

**功能**: 
- 创建订阅
- 默认服务器: `https://api.verdent.ai`
- 端点: `verdent/subscription/create`
- 使用 Cookie token 认证

**调用位置**: `extension/dist/extension.js:630134`
```javascript
let k = await Syr(
  w,
  { plan_id: b.trialPlanId, device_id: S, source: "verdent" },
  { headers: { Cookie: `token=${I}` } }
);
```

---

### 1.3 用户信息获取 API - `Dyr`
**位置**: `extension/dist/extension.js:585262-585264`

```javascript
var Dyr = function (t = "https://agent.verdent.ai", e, i) {
  return Byr(t, i).get("user/center/info");
}
```

**功能**:
- 获取用户中心信息
- 默认服务器: `https://agent.verdent.ai`
- 端点: `user/center/info`

**调用位置**:
1. `extension/dist/extension.js:625519` - 在错误码 30001 时调用
2. `extension/dist/extension.js:629127` - 在 `fetchUserInfo()` 方法中

---

## 2. 认证系统

### 2.1 Token 管理
**存储键**: `ycAuthToken`

**相关代码位置**:
- `624474`: 读取 token
- `624481`: 初始化 API 实例
- `624681`: 登出时清除 token
- `629099`: 登出流程
- `629123`: 获取用户信息时使用

**Token 使用方式**:
```javascript
let d = await Zn(this.context, "ycAuthToken");
if (d) {
  s.Cookie = `token=${d}`;
}
```

---

### 2.2 用户信息获取 - `fetchUserInfo`
**位置**: `extension/dist/extension.js:629114-629133`

```javascript
async fetchUserInfo() {
  try {
    let e = this.configManager.get("mainServer.host") ?? "agent.verdent.ai",
      i = this.configManager.get("mainServer.port") ?? 443,
      n = i === 443 ? "https" : "http",
      a = `${n}://${e}:${i}/`;
    (i === 443 || i === 80) && (a = `${n}://${e}/`);
    let s = {};
    if (this.context) {
      let d = await Zn(this.context, "ycAuthToken");
      d && (s.Cookie = `token=${d}`);
    }
    return (
      await k1(a, { timeout: 1e4, headers: s }).get("/user/center/info")
    )?.data?.data;
  } catch (e) {
    console.error("Failed to fetch user info:", e?.message || e?.toString()),
      vt.error("Failed to fetch user info:", e?.message || e?.toString());
  }
}
```

**关键配置**:
- 可配置主服务器: `mainServer.host` (默认: `agent.verdent.ai`)
- 可配置端口: `mainServer.port` (默认: 443)
- 超时: 10秒 (1e4 毫秒)

---

### 2.3 登出逻辑 - `logout`
**位置**: `extension/dist/extension.js:624680-624690`

```javascript
async logout() {
  await Gi(this.context, "ycAuthToken", void 0),
    await Mr(this.context, "userInfo", void 0),
    await Gi(this.context, "authNonce", void 0),
    await Gi(this.context, "authNonceTimestamp", void 0),
    oa.commands.executeCommand("setContext", "verdent.showVerdentMenu", !1),
    await this.postStateToWebview(),
    await this.postMessageToWebview({ type: "logoutSuccess" }),
    (yb.instance = null),
    (W_.instance = null);
}
```

**清除内容**:
1. `ycAuthToken` - 认证令牌
2. `userInfo` - 用户信息
3. `authNonce` - 认证随机数
4. `authNonceTimestamp` - 认证时间戳
5. 隐藏 Verdent 菜单
6. 清空实例

---

### 2.4 登录回调处理
**位置**: `extension/dist/extension.js:630530-630614`

**完整流程**:
1. 验证认证状态和 nonce
2. 调用 `https://login.verdent.ai` 的 `passport/pkce/callback` 端点
3. 获取并保存 token
4. 调用 `fetchUserInfo()` 获取用户信息
5. 更新 UI 和上下文

**关键端点**:
```javascript
await k1("https://login.verdent.ai", { timeout: 1e5 }).post(
  "passport/pkce/callback",
  { code: e, codeVerifier: s }
)
```

---

## 3. 错误处理和订阅通知

### 3.1 错误码 30001 处理
**位置**: `extension/dist/extension.js:625515-625526`

```javascript
if (A.errNo === 30001) {
  let o = await Zn(this.context, "ycAuthToken"),
    h = this.config.get("mainServer.agentHost");
  try {
    let b = await Dyr(
      h,
      {},
      { headers: { Cookie: `token=${o}` } }
    );
    await this.say("subscribe_notice", JSON.stringify(b));
  } catch {}
}
```

**功能**: 
- 错误码 30001 触发订阅通知
- 获取用户中心信息
- 向用户发送订阅通知

---

### 3.2 获取免费试用页面
**位置**: `extension/dist/extension.js:630128-630143`

```javascript
case "getFreeTrialPage": {
  let b = await Lr(this.context, "userInfo"),
    I = await Zn(this.context, "ycAuthToken");
  try {
    let w = this.configManager.get("mainServer.apiHost"),
      S = this.configManager.get("deviceId") || "unknown-device",
      k = await Syr(
        w,
        { plan_id: b.trialPlanId, device_id: S, source: "verdent" },
        { headers: { Cookie: `token=${I}` } }
      );
    Gr.env.openExternal(Gr.Uri.parse(k.checkout_url));
  } catch (w) {
    Gr.window.showErrorMessage(w.message), console.log(w);
  }
  break;
}
```

**流程**:
1. 从上下文读取用户信息和认证令牌
2. 调用 `Syr` 创建订阅，传入:
   - `plan_id`: 从用户信息中的 `trialPlanId`
   - `device_id`: 设备 ID
   - `source`: "verdent"
3. 打开返回的 `checkout_url`

---

## 4. 存储的数据结构

### 4.1 全局状态存储
| 键名 | 描述 | 操作函数 |
|------|------|----------|
| `ycAuthToken` | 认证令牌 | `Zn()` 读取, `Gi()` 写入 |
| `userInfo` | 用户信息 (包含 `trialPlanId`, `userKey`, `email` 等) | `Lr()` 读取, `Mr()` 写入 |
| `authNonce` | PKCE 认证随机数 | `Zn()` 读取, `Gi()` 写入 |
| `authNonceTimestamp` | 认证时间戳 | `Zn()` 读取, `Gi()` 写入 |
| `models` | 模型配置 | `Lr()` 读取, `Mr()` 写入 |
| `customSolution` | 自定义方案 | `Lr()` 读取, `Mr()` 写入 |
| `apiProvider` | API 提供商 (如 "verdent") | `Mr()` 写入 |

---

## 5. 配置项

### 5.1 服务器配置
| 配置键 | 默认值 | 用途 |
|--------|--------|------|
| `mainServer.host` | `agent.verdent.ai` | Agent 服务器地址 |
| `mainServer.port` | `443` | 服务器端口 |
| `mainServer.agentHost` | - | Agent 主机 (用于订阅通知) |
| `mainServer.apiHost` | - | API 主机 (用于订阅创建) |
| `auth.login_url` | `https://verdent.ai/auth` | 登录页面 URL |
| `deviceId` | `"unknown-device"` | 设备标识符 |

---

## 6. API 端点总结

### 6.1 认证相关
| 端点 | 方法 | 服务器 | 用途 |
|------|------|--------|------|
| `/passport/pkce/callback` | POST | `https://login.verdent.ai` | PKCE 认证回调 |
| `/user/center/info` | GET | `https://agent.verdent.ai` | 获取用户信息 |

### 6.2 订阅相关
| 端点 | 方法 | 服务器 | 用途 |
|------|------|--------|------|
| `/verdent/subscription/create` | POST | `https://api.verdent.ai` | 创建订阅 |
| `/input_box/info` | GET | Agent 服务器 | 获取模型列表 |

---

## 7. 消息类型

### 7.1 WebView 消息
| 消息类型 | 方向 | 数据 | 用途 |
|----------|------|------|------|
| `logoutSuccess` | → WebView | - | 通知登出成功 |
| `authCallback` | → WebView | `{ customToken }` | 认证回调 |
| `userInfo` | → WebView | `{ text: JSON.stringify(userInfo) }` | 用户信息更新 |
| `subscribe_notice` | → WebView | JSON 字符串 | 订阅通知 |
| `getFreeTrialPage` | ← WebView | - | 请求打开试用页面 |
| `login_err` | 日志 | 错误信息 | 登录错误报告 |

---

## 8. 错误场景

### 8.1 "Free trial unavailable" 触发条件
**位置**: `extension/dist/extension.js:585251-585254`

**触发时机**:
- 在 `Byr` 的 `post` 方法中
- 当捕获到非 Axios 错误时
- 作为通用的订阅/试用相关错误的后备消息

**可能的原因**:
1. 网络连接失败 (非 HTTP 错误)
2. 订阅创建请求异常
3. 其他未被 Axios 识别的异常

---

### 8.2 错误码 30001
**触发场景**: 服务器返回错误码 30001
**处理方式**:
1. 调用 `Dyr` 获取用户中心信息
2. 发送 `subscribe_notice` 消息给 WebView
3. 显示服务器错误提示

---

## 9. 认证流程图

```
用户点击登录
    ↓
打开 https://verdent.ai/auth (可配置)
    ↓
用户完成认证
    ↓
回调 /passport/pkce/callback
    ↓
获取 token
    ↓
保存到 ycAuthToken
    ↓
调用 fetchUserInfo()
    ↓
保存用户信息
    ↓
更新 UI (显示 Verdent 菜单)
```

---

## 10. 订阅流程图

```
用户触发 "getFreeTrialPage"
    ↓
读取 userInfo.trialPlanId
    ↓
调用 Syr (subscription/create)
    ↓
传入: plan_id, device_id, source
    ↓
获取 checkout_url
    ↓
打开外部浏览器
```

---

## 11. 关键发现

### 11.1 安全性
- Token 通过 Cookie 传递: `Cookie: token=${token}`
- 使用 PKCE (Proof Key for Code Exchange) 认证流程
- Nonce 和时间戳用于防止重放攻击

### 11.2 错误处理
- "Free trial unavailable" 是一个通用的后备错误消息
- 实际的订阅和试用验证逻辑在服务器端
- 客户端主要负责 token 管理和 UI 展示

### 11.3 扩展性
- 服务器地址可配置
- 支持多个 API 提供商
- 模型配置动态加载

---

## 12. 相关文件位置

### 12.1 已编译文件
- **主文件**: `extension/dist/extension.js`
- **包配置**: `extension/package.json`

### 12.2 源代码 (未找到)
- TypeScript 源文件可能已被移除或未包含在当前目录中
- 只找到了编译后的 JavaScript 文件

---

## 13. 建议和注意事项

### 13.1 调试建议
1. 在 `Byr` 函数的错误处理中添加更详细的日志
2. 记录所有订阅相关的 API 调用和响应
3. 监控 `errNo === 30001` 的触发频率

### 13.2 潜在问题
1. "Free trial unavailable" 消息过于通用，难以定位具体问题
2. 错误处理中吞掉了部分异常 (`catch {}`)
3. 超时配置较长 (30秒)，可能影响用户体验

### 13.3 改进方向
1. 细化错误消息，提供更具体的失败原因
2. 添加重试机制
3. 实现更友好的订阅状态展示

---

**文档版本**: 1.0  
**生成时间**: 2025-11-16  
**分析范围**: extension/dist/extension.js (编译后代码)
