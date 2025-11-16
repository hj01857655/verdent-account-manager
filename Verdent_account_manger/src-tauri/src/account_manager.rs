use serde::{Deserialize, Deserializer, Serialize};
use serde_json::Value;
use std::fs;
use std::path::PathBuf;
use chrono::Utc;
use thiserror::Error;

#[derive(Debug, Error)]
pub enum AccountError {
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    #[error("JSON error: {0}")]
    Json(#[from] serde_json::Error),

    #[error("Account not found: {0}")]
    NotFound(String),
}

// 自定义反序列化函数,支持将整数或字符串转换为 Option<String>
fn deserialize_quota<'de, D>(deserializer: D) -> Result<Option<String>, D::Error>
where
    D: Deserializer<'de>,
{
    let value: Option<Value> = Option::deserialize(deserializer)?;
    match value {
        None => Ok(None),
        Some(Value::String(s)) => Ok(Some(s)),
        Some(Value::Number(n)) => Ok(Some(n.to_string())),
        Some(_) => Ok(None),
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Account {
    pub id: String,
    pub email: String,
    pub password: String,
    pub register_time: String,
    pub expire_time: Option<String>,      // 订阅到期时间 (从 currentPeriodEnd 转换)
    pub status: String,
    pub token: Option<String>,
    #[serde(deserialize_with = "deserialize_quota")]
    pub quota_remaining: Option<String>,  // 改为 String 以支持小数
    #[serde(default, deserialize_with = "deserialize_quota")]
    pub quota_used: Option<String>,       // 新增: 已消耗额度 (旧数据可能没有此字段)
    #[serde(deserialize_with = "deserialize_quota")]
    pub quota_total: Option<String>,      // 改为 String 以支持小数
    #[serde(default)]
    pub subscription_type: Option<String>,
    #[serde(default)]
    pub trial_days: Option<i32>,          // 新增: 试用天数 (旧数据可能没有此字段)
    #[serde(default)]
    pub current_period_end: Option<i64>,  // 新增: 订阅周期结束时间 (Unix时间戳,秒)
    #[serde(default)]
    pub auto_renew: Option<bool>,         // 新增: 是否自动续订
    #[serde(default)]
    pub token_expire_time: Option<String>, // 新增: Token 过期时间 (从 JWT exp 字段解析)
    pub last_updated: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AccountList {
    pub accounts: Vec<Account>,
    pub last_sync: String,
}

pub struct AccountManager {
    storage_path: PathBuf,
}

impl AccountManager {
    pub fn new() -> Result<Self, AccountError> {
        let storage_dir = dirs::home_dir()
            .ok_or_else(|| std::io::Error::new(std::io::ErrorKind::NotFound, "Home directory not found"))?
            .join(".verdent_accounts");
        
        fs::create_dir_all(&storage_dir)?;
        
        let storage_path = storage_dir.join("accounts.json");
        
        if !storage_path.exists() {
            let initial_data = AccountList {
                accounts: Vec::new(),
                last_sync: Utc::now().to_rfc3339(),
            };
            fs::write(&storage_path, serde_json::to_string_pretty(&initial_data)?)?;
        }
        
        Ok(Self { storage_path })
    }
    
    pub fn get_storage_path(&self) -> String {
        self.storage_path.to_string_lossy().to_string()
    }
    
    fn load(&self) -> Result<AccountList, AccountError> {
        let content = fs::read_to_string(&self.storage_path)?;
        Ok(serde_json::from_str(&content)?)
    }
    
    fn save(&self, data: &AccountList) -> Result<(), AccountError> {
        let content = serde_json::to_string_pretty(data)?;
        fs::write(&self.storage_path, content)?;
        Ok(())
    }
    
    pub fn add_account(&self, mut account: Account) -> Result<Account, AccountError> {
        let mut data = self.load()?;
        
        if account.id.is_empty() {
            account.id = uuid::Uuid::new_v4().to_string();
        }
        
        account.last_updated = Some(Utc::now().to_rfc3339());
        
        data.accounts.push(account.clone());
        data.last_sync = Utc::now().to_rfc3339();
        
        self.save(&data)?;
        Ok(account)
    }
    
    pub fn get_all_accounts(&self) -> Result<Vec<Account>, AccountError> {
        let data = self.load()?;
        Ok(data.accounts)
    }
    
    pub fn get_account(&self, id: &str) -> Result<Account, AccountError> {
        let data = self.load()?;
        data.accounts
            .into_iter()
            .find(|acc| acc.id == id)
            .ok_or_else(|| AccountError::NotFound(id.to_string()))
    }
    
    pub fn update_account(&self, id: &str, updated: Account) -> Result<Account, AccountError> {
        let mut data = self.load()?;
        
        let account = data.accounts
            .iter_mut()
            .find(|acc| acc.id == id)
            .ok_or_else(|| AccountError::NotFound(id.to_string()))?;
        
        *account = updated;
        account.last_updated = Some(Utc::now().to_rfc3339());
        let result = account.clone();
        data.last_sync = Utc::now().to_rfc3339();
        
        self.save(&data)?;
        Ok(result)
    }
    
    pub fn delete_account(&self, id: &str) -> Result<(), AccountError> {
        let mut data = self.load()?;
        
        let original_len = data.accounts.len();
        data.accounts.retain(|acc| acc.id != id);
        
        if data.accounts.len() == original_len {
            return Err(AccountError::NotFound(id.to_string()));
        }
        
        data.last_sync = Utc::now().to_rfc3339();
        self.save(&data)?;
        Ok(())
    }
    
    pub fn update_account_token(&self, id: &str, token: String) -> Result<Account, AccountError> {
        let mut data = self.load()?;
        
        let account = data.accounts
            .iter_mut()
            .find(|acc| acc.id == id)
            .ok_or_else(|| AccountError::NotFound(id.to_string()))?;
        
        account.token = Some(token);
        account.last_updated = Some(Utc::now().to_rfc3339());
        let result = account.clone();
        data.last_sync = Utc::now().to_rfc3339();
        
        self.save(&data)?;
        Ok(result)
    }
    
    pub fn update_account_quota(&self, id: &str, remaining: i32, total: i32) -> Result<Account, AccountError> {
        let mut data = self.load()?;

        let account = data.accounts
            .iter_mut()
            .find(|acc| acc.id == id)
            .ok_or_else(|| AccountError::NotFound(id.to_string()))?;

        account.quota_remaining = Some(remaining.to_string());
        account.quota_total = Some(total.to_string());
        account.last_updated = Some(Utc::now().to_rfc3339());
        let result = account.clone();
        data.last_sync = Utc::now().to_rfc3339();

        self.save(&data)?;
        Ok(result)
    }
}
