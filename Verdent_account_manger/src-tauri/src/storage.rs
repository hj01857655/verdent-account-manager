use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs;
use std::path::PathBuf;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StorageValue {
    pub value: serde_json::Value,
}

pub struct StorageManager {
    storage_dir: PathBuf,
}

impl StorageManager {
    pub fn new() -> Result<Self, std::io::Error> {
        let storage_dir = dirs::home_dir()
            .ok_or_else(|| std::io::Error::new(std::io::ErrorKind::NotFound, "Home directory not found"))?
            .join(".verdent_account_manager");
        
        fs::create_dir_all(&storage_dir)?;
        
        Ok(Self { storage_dir })
    }

    pub fn save(&self, key: &str, value: serde_json::Value) -> Result<(), std::io::Error> {
        let file_path = self.storage_dir.join(format!("{}.json", key));
        let data = StorageValue { value };
        let json = serde_json::to_string_pretty(&data)?;
        fs::write(file_path, json)?;
        Ok(())
    }

    #[allow(dead_code)]
    pub fn load(&self, key: &str) -> Result<Option<serde_json::Value>, std::io::Error> {
        let file_path = self.storage_dir.join(format!("{}.json", key));
        
        if !file_path.exists() {
            return Ok(None);
        }
        
        let content = fs::read_to_string(file_path)?;
        let data: StorageValue = serde_json::from_str(&content)?;
        Ok(Some(data.value))
    }

    pub fn delete(&self, key: &str) -> Result<bool, std::io::Error> {
        let file_path = self.storage_dir.join(format!("{}.json", key));
        
        if file_path.exists() {
            fs::remove_file(file_path)?;
            Ok(true)
        } else {
            Ok(false)
        }
    }

    pub fn list_all(&self) -> Result<Vec<String>, std::io::Error> {
        let mut keys = Vec::new();
        
        for entry in fs::read_dir(&self.storage_dir)? {
            let entry = entry?;
            let path = entry.path();
            
            if path.is_file() {
                if let Some(file_name) = path.file_stem() {
                    if let Some(key) = file_name.to_str() {
                        keys.push(key.to_string());
                    }
                }
            }
        }
        
        Ok(keys)
    }

    #[allow(dead_code)]
    pub fn reset_device_identity(&self) -> Result<HashMap<String, bool>, std::io::Error> {
        let identity_keys = vec![
            "secrets_ycAuthToken",
            "secrets_verdentApiKey",
            "secrets_authNonce",
            "secrets_authNonceTimestamp",
            "globalState_userInfo",
            "globalState_taskHistory",
        ];

        let mut results = HashMap::new();

        for key in identity_keys {
            let deleted = self.delete(key)?;
            results.insert(key.to_string(), deleted);
        }

        self.save("globalState_apiProvider", serde_json::json!({"value": "openrouter"}))?;

        Ok(results)
    }

    #[allow(dead_code)]
    pub fn reset_all_storage(&self) -> Result<HashMap<String, bool>, std::io::Error> {
        let all_keys = vec![
            "secrets_ycAuthToken",
            "secrets_verdentApiKey",
            "secrets_authNonce",
            "secrets_authNonceTimestamp",
            "globalState_userInfo",
            "globalState_apiProvider",
            "globalState_taskHistory",
            "workspaceState_isPlanMode",
            "workspaceState_thinkLevel",
            "workspaceState_selectModel",
        ];

        let mut results = HashMap::new();

        for key in all_keys {
            let deleted = self.delete(key)?;
            results.insert(key.to_string(), deleted);
        }

        Ok(results)
    }

    #[allow(dead_code)]
    pub fn get_storage_path(&self) -> String {
        self.storage_dir.to_string_lossy().to_string()
    }

    pub fn clear(&self) -> Result<(), std::io::Error> {
        for entry in fs::read_dir(&self.storage_dir)? {
            let entry = entry?;
            let path = entry.path();
            if path.is_file() {
                fs::remove_file(path)?;
            }
        }
        Ok(())
    }

    pub fn get_path(&self) -> &std::path::Path {
        &self.storage_dir
    }

    pub fn list_keys(&self) -> Result<Vec<String>, std::io::Error> {
        self.list_all()
    }
}
