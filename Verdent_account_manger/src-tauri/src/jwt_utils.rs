use serde::{Deserialize, Serialize};
use base64::{Engine as _, engine::general_purpose};

#[derive(Debug, Serialize, Deserialize)]
pub struct JwtPayload {
    pub user_id: Option<i64>,
    pub version: Option<i32>,
    pub token_type: Option<String>,
    pub exp: Option<i64>,  // 过期时间 (Unix 时间戳,秒)
    pub iat: Option<i64>,  // 签发时间
    pub nbf: Option<i64>,  // 生效时间
}

/// 从 JWT Token 中解析 payload
///
/// JWT 格式: header.payload.signature
/// 我们只需要解析 payload 部分
pub fn parse_jwt_payload(token: &str) -> Result<JwtPayload, Box<dyn std::error::Error>> {
    // 分割 JWT Token
    let parts: Vec<&str> = token.split('.').collect();

    if parts.len() != 3 {
        return Err("Invalid JWT format: expected 3 parts".into());
    }

    // 获取 payload 部分 (第二部分)
    let payload_base64 = parts[1];

    // JWT 使用 Base64 URL-safe 编码,不含 padding
    // 直接使用 URL_SAFE_NO_PAD 解码器,不需要添加 padding
    let payload_bytes = general_purpose::URL_SAFE_NO_PAD
        .decode(payload_base64.as_bytes())
        .map_err(|e| format!("Failed to decode base64: {}", e))?;

    // 解析 JSON
    let payload: JwtPayload = serde_json::from_slice(&payload_bytes)
        .map_err(|e| format!("Failed to parse JSON: {}", e))?;

    Ok(payload)
}

/// 添加 Base64 padding (保留以备将来使用)
#[allow(dead_code)]
fn add_base64_padding(input: &str) -> String {
    let padding_len = (4 - input.len() % 4) % 4;
    format!("{}{}", input, "=".repeat(padding_len))
}

/// 从 JWT Token 中提取过期时间并转换为 RFC3339 格式
pub fn extract_token_expire_time(token: &str) -> Option<String> {
    match parse_jwt_payload(token) {
        Ok(payload) => {
            if let Some(exp) = payload.exp {
                // 将 Unix 时间戳转换为 RFC3339 格式
                if let Some(dt) = chrono::DateTime::from_timestamp(exp, 0) {
                    return Some(dt.to_rfc3339());
                }
            }
            None
        }
        Err(e) => {
            eprintln!("[!] JWT 解析失败: {}", e);
            None
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_jwt_payload() {
        let token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo3NDk0NjI4NTU5MzIxNDk3NjAsInZlcnNpb24iOjAsInRva2VuX3R5cGUiOiJhY2Nlc3MiLCJleHAiOjE3NjU3MDk0MjksImlhdCI6MTc2MzExNzQyOSwibmJmIjoxNzYzMTE3NDI5fQ.3Nb7K7V56ypYbgj5ESWgoGjC2NRUBhvkVyMLsnB9btE";
        
        let payload = parse_jwt_payload(token).unwrap();
        
        assert_eq!(payload.user_id, Some(749462855932149760));
        assert_eq!(payload.exp, Some(1765709429));
        assert_eq!(payload.token_type, Some("access".to_string()));
    }

    #[test]
    fn test_extract_token_expire_time() {
        let token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo3NDk0NjI4NTU5MzIxNDk3NjAsInZlcnNpb24iOjAsInRva2VuX3R5cGUiOiJhY2Nlc3MiLCJleHAiOjE3NjU3MDk0MjksImlhdCI6MTc2MzExNzQyOSwibmJmIjoxNzYzMTE3NDI5fQ.3Nb7K7V56ypYbgj5ESWgoGjC2NRUBhvkVyMLsnB9btE";
        
        let expire_time = extract_token_expire_time(token).unwrap();
        
        // 应该是 2025-12-14 的某个时间
        assert!(expire_time.contains("2025-12-14"));
    }

    #[test]
    fn test_add_base64_padding() {
        assert_eq!(add_base64_padding("abc"), "abc=");
        assert_eq!(add_base64_padding("abcd"), "abcd");
        assert_eq!(add_base64_padding("ab"), "ab==");
    }
}

