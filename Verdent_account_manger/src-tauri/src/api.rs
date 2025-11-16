use reqwest::{Client, header};
use serde::{Deserialize, Serialize};
use crate::pkce::PkceParams;
use std::time::Duration;

#[derive(Debug, Serialize, Deserialize)]
pub struct ApiResponse<T> {
    #[serde(rename = "errCode")]
    pub err_code: i32,
    #[serde(rename = "errMsg")]
    pub err_msg: Option<String>,
    pub data: Option<T>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct AuthCodeData {
    pub code: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct TokenData {
    pub token: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct TokenInfo {
    #[serde(rename = "tokenConsumed")]
    pub token_consumed: Option<f64>,
    #[serde(rename = "tokenFree")]
    pub token_free: Option<f64>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SubscriptionInfo {
    #[serde(rename = "planName")]
    pub plan_name: Option<String>,
    #[serde(rename = "levelName")]
    pub level_name: Option<String>,
    #[serde(rename = "currentPeriodEnd")]
    pub current_period_end: Option<i64>,
    #[serde(rename = "autoRenew")]
    pub auto_renew: Option<bool>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct UserInfo {
    pub email: Option<String>,
    #[serde(rename = "tokenInfo")]
    pub token_info: Option<TokenInfo>,
    #[serde(rename = "subscriptionInfo")]
    pub subscription_info: Option<SubscriptionInfo>,
    #[serde(rename = "subscriptionType")]
    pub subscription_type: Option<String>,
    #[serde(rename = "trialDays")]
    pub trial_days: Option<i32>,
    #[serde(rename = "expireTime")]
    pub expire_time: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct LoginData {
    pub token: String,
    #[serde(rename = "expireTime")]
    pub expire_time: Option<i64>,
    #[serde(rename = "accessToken")]
    pub access_token: Option<String>,
    #[serde(rename = "refreshToken")]
    pub refresh_token: Option<String>,
    #[serde(rename = "accessTokenExpiresAt")]
    pub access_token_expires_at: Option<i64>,
    #[serde(rename = "refreshTokenExpiresAt")]
    pub refresh_token_expires_at: Option<i64>,
    #[serde(rename = "needBindInviteCode")]
    pub need_bind_invite_code: Option<bool>,
}

pub struct VerdentApi {
    client: Client,
    login_url: String,
    pkce_auth_url: String,
    pkce_callback_url: String,
    user_info_url: String,
}

impl VerdentApi {
    pub fn new() -> Self {
        // 创建带超时配置的 HTTP 客户端
        let client = Client::builder()
            .connect_timeout(Duration::from_secs(10))  // 连接超时 10 秒
            .timeout(Duration::from_secs(30))          // 总超时 30 秒
            .build()
            .unwrap_or_else(|_| Client::new());

        Self {
            client,
            login_url: "https://login.verdent.ai/passport/login".to_string(),
            pkce_auth_url: "https://login.verdent.ai/passport/pkce/auth".to_string(),
            pkce_callback_url: "https://login.verdent.ai/passport/pkce/callback".to_string(),
            user_info_url: "https://agent.verdent.ai/user/center/info".to_string(),
        }
    }

    pub async fn request_auth_code(
        &self,
        token: &str,
        pkce: &PkceParams,
    ) -> Result<String, Box<dyn std::error::Error>> {
        let payload = serde_json::json!({
            "codeChallenge": pkce.code_challenge
        });

        let response = self
            .client
            .post(&self.pkce_auth_url)
            .header(header::ACCEPT, "application/json, text/plain, */*")
            .header(header::CONTENT_TYPE, "application/json")
            .header(header::COOKIE, format!("token={}", token))
            .header(header::ORIGIN, "https://www.verdent.ai")
            .header(header::REFERER, "https://www.verdent.ai/")
            .header(header::USER_AGENT, "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            .json(&payload)
            .send()
            .await?;

        if !response.status().is_success() {
            return Err(format!("HTTP错误: {}", response.status()).into());
        }

        let result: ApiResponse<AuthCodeData> = response.json().await?;

        if result.err_code != 0 {
            return Err(format!("API错误: {}", result.err_msg.unwrap_or_default()).into());
        }

        Ok(result.data.ok_or("缺少授权码")?.code)
    }

    pub async fn exchange_token(
        &self,
        auth_code: &str,
        code_verifier: &str,
    ) -> Result<String, Box<dyn std::error::Error>> {
        let payload = serde_json::json!({
            "code": auth_code,
            "codeVerifier": code_verifier
        });

        let response = self
            .client
            .post(&self.pkce_callback_url)
            .header(header::ACCEPT, "application/json, text/plain, */*")
            .header(header::CONTENT_TYPE, "application/json")
            .header(header::ORIGIN, "https://www.verdent.ai")
            .header(header::REFERER, "https://www.verdent.ai/")
            .header(header::USER_AGENT, "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            .json(&payload)
            .send()
            .await?;

        if !response.status().is_success() {
            return Err(format!("HTTP错误: {}", response.status()).into());
        }

        let result: ApiResponse<TokenData> = response.json().await?;

        if result.err_code != 0 {
            return Err(format!("API错误: {}", result.err_msg.unwrap_or_default()).into());
        }

        Ok(result.data.ok_or("缺少访问令牌")?.token)
    }

    pub async fn fetch_user_info(
        &self,
        token: &str,
    ) -> Result<UserInfo, Box<dyn std::error::Error>> {
        use std::time::Instant;
        let start = Instant::now();

        println!("[*] 发送请求: GET {}", self.user_info_url);

        let response = self
            .client
            .get(&self.user_info_url)
            .header(header::ACCEPT, "application/json, text/plain, */*")
            .header(header::COOKIE, format!("token={}", token))
            .header(header::ORIGIN, "https://www.verdent.ai")
            .header(header::REFERER, "https://www.verdent.ai/")
            .header(header::USER_AGENT, "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            .send()
            .await?;

        let elapsed = start.elapsed();
        println!("[*] 请求耗时: {:.2}秒", elapsed.as_secs_f64());

        if !response.status().is_success() {
            let status = response.status();
            return Err(format!("HTTP错误: {}", status).into());
        }

        let result: ApiResponse<UserInfo> = response.json().await?;

        if result.err_code != 0 {
            return Err(format!("API错误: {}", result.err_msg.unwrap_or_default()).into());
        }

        Ok(result.data.ok_or("缺少用户信息")?)
    }

    /// 带重试机制的获取用户信息
    ///
    /// 参数:
    /// - token: 用户 Token
    /// - max_retries: 最大重试次数 (默认 3)
    ///
    /// 返回:
    /// - Ok(UserInfo): 成功获取的用户信息
    /// - Err(String): 详细的错误信息
    pub async fn fetch_user_info_with_retry(
        &self,
        token: &str,
        max_retries: u32,
    ) -> Result<UserInfo, String> {
        let mut last_error = String::new();

        for attempt in 1..=max_retries {
            println!("[*] 尝试获取用户信息 (第 {}/{} 次)...", attempt, max_retries);

            // 将 match 结果提取为 Result<UserInfo, (String, bool)>
            // 这样可以避免 Box<dyn StdError> 跨越 .await 边界
            let result = match self.fetch_user_info(token).await {
                Ok(user_info) => Ok(user_info),
                Err(e) => {
                    // 立即将错误转换为 String 并分类
                    let error_msg = e.to_string();
                    let classified_error = self.classify_error(&error_msg);
                    let should_retry = self.should_retry(&error_msg);
                    // e 在这里被丢弃
                    Err((classified_error, should_retry))
                }
            };

            match result {
                Ok(user_info) => {
                    if attempt > 1 {
                        println!("[✓] 重试成功!");
                    }
                    return Ok(user_info);
                }
                Err((classified_error, should_retry)) => {
                    last_error = classified_error;

                    println!("[!] 第 {} 次尝试失败: {}", attempt, last_error);

                    // 检查是否应该重试
                    if !should_retry {
                        println!("[!] 错误类型不可重试,停止尝试");
                        return Err(last_error);
                    }

                    // 如果不是最后一次尝试,等待后重试
                    if attempt < max_retries {
                        let wait_secs = attempt; // 指数退避: 1秒, 2秒, 3秒
                        println!("[*] 等待 {} 秒后重试...", wait_secs);
                        tokio::time::sleep(Duration::from_secs(wait_secs as u64)).await;
                    }
                }
            }
        }

        println!("[×] 所有重试均失败");
        Err(last_error)
    }

    /// 判断错误是否应该重试
    fn should_retry(&self, error_msg: &str) -> bool {
        // 网络错误、超时错误应该重试
        if error_msg.contains("网络连接")
            || error_msg.contains("超时")
            || error_msg.contains("connection")
            || error_msg.contains("timeout")
            || error_msg.contains("timed out")
            || error_msg.contains("error sending request") {
            return true;
        }

        // HTTP 5xx 服务器错误应该重试
        if error_msg.contains("HTTP错误: 5") {
            return true;
        }

        // HTTP 4xx 客户端错误不应该重试 (如 401 认证失败)
        if error_msg.contains("HTTP错误: 4") {
            return false;
        }

        // API 错误不应该重试
        if error_msg.contains("API错误") {
            return false;
        }

        // 默认不重试
        false
    }

    /// 分类错误并返回用户友好的错误消息
    fn classify_error(&self, error_msg: &str) -> String {
        // 网络连接错误
        if error_msg.contains("error sending request")
            || error_msg.contains("connection")
            || error_msg.contains("dns") {
            return "网络连接失败,请检查网络连接".to_string();
        }

        // 超时错误
        if error_msg.contains("timeout") || error_msg.contains("timed out") {
            return "请求超时,请稍后重试".to_string();
        }

        // HTTP 401 认证失败
        if error_msg.contains("HTTP错误: 401") {
            return "Token 已过期或无效,请重新登录".to_string();
        }

        // HTTP 403 权限不足
        if error_msg.contains("HTTP错误: 403") {
            return "权限不足,无法访问".to_string();
        }

        // HTTP 404 未找到
        if error_msg.contains("HTTP错误: 404") {
            return "API 端点不存在".to_string();
        }

        // HTTP 5xx 服务器错误
        if error_msg.contains("HTTP错误: 5") {
            return "服务器错误,请稍后重试".to_string();
        }

        // API 错误
        if error_msg.contains("API错误") {
            return error_msg.to_string();
        }

        // 其他错误
        error_msg.to_string()
    }

    pub async fn login(
        &self,
        email: &str,
        password: &str,
    ) -> Result<LoginData, Box<dyn std::error::Error>> {
        let payload = serde_json::json!({
            "email": email,
            "password": password
        });

        let response = self
            .client
            .post(&self.login_url)
            .header(header::ACCEPT, "application/json, text/plain, */*")
            .header(header::CONTENT_TYPE, "application/json")
            .header(header::ORIGIN, "https://www.verdent.ai")
            .header(header::REFERER, "https://www.verdent.ai/")
            .header(header::USER_AGENT, "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            .json(&payload)
            .send()
            .await?;

        if !response.status().is_success() {
            return Err(format!("HTTP错误: {}", response.status()).into());
        }

        let result: ApiResponse<LoginData> = response.json().await?;

        if result.err_code != 0 {
            return Err(format!("登录失败: {}", result.err_msg.unwrap_or_default()).into());
        }

        Ok(result.data.ok_or("缺少登录数据")?)
    }
}
