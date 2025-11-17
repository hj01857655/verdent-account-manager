use serde::{Deserialize, Serialize};
use chrono::Utc;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Account {
    #[serde(default)]
    pub id: String,
    pub email: String,
    pub password: String,
    pub token: Option<String>,
    pub register_time: Option<String>,
    pub status: Option<String>,
    pub quota_remaining: Option<String>,
    pub quota_used: Option<String>,
    pub quota_total: Option<String>,
    pub subscription_type: Option<String>,
    pub trial_days: Option<i32>,
    pub expire_time: Option<String>,
    pub current_period_end: Option<i64>,
    pub auto_renew: Option<bool>,
    pub token_expire_time: Option<String>,
    pub last_updated: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AccountList {
    pub accounts: Vec<Account>,
    pub last_sync: String,
}

impl Default for AccountList {
    fn default() -> Self {
        Self {
            accounts: Vec::new(),
            last_sync: Utc::now().to_rfc3339(),
        }
    }
}
