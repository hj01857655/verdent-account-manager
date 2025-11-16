use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::fs;
use std::path::PathBuf;
use rand::Rng;
use uuid::Uuid;
use sha2::{Digest, Sha256};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VSCodeStorage {
    #[serde(flatten)]
    pub data: serde_json::Map<String, Value>,
}

pub struct VSCodeStorageManager {
    storage_path: PathBuf,
    extensions_path: PathBuf,
}

impl VSCodeStorageManager {
    pub fn new() -> Result<Self, std::io::Error> {
        let (storage_path, extensions_path) = if cfg!(target_os = "windows") {
            let appdata = std::env::var("APPDATA")
                .map_err(|_| std::io::Error::new(std::io::ErrorKind::NotFound, "APPDATA not found"))?;
            let userprofile = std::env::var("USERPROFILE")
                .map_err(|_| std::io::Error::new(std::io::ErrorKind::NotFound, "USERPROFILE not found"))?;
            
            let storage = PathBuf::from(appdata)
                .join("Code")
                .join("User")
                .join("globalStorage")
                .join("storage.json");
            
            let extensions = PathBuf::from(userprofile)
                .join(".vscode")
                .join("extensions");
            
            (storage, extensions)
        } else if cfg!(target_os = "macos") {
            let home = dirs::home_dir()
                .ok_or_else(|| std::io::Error::new(std::io::ErrorKind::NotFound, "Home directory not found"))?;
            
            let storage = home
                .join("Library")
                .join("Application Support")
                .join("Code")
                .join("User")
                .join("globalStorage")
                .join("storage.json");
            
            let extensions = home
                .join(".vscode")
                .join("extensions");
            
            (storage, extensions)
        } else {
            let home = dirs::home_dir()
                .ok_or_else(|| std::io::Error::new(std::io::ErrorKind::NotFound, "Home directory not found"))?;
            
            let storage = home
                .join(".config")
                .join("Code")
                .join("User")
                .join("globalStorage")
                .join("storage.json");
            
            let extensions = home
                .join(".vscode")
                .join("extensions");
            
            (storage, extensions)
        };

        Ok(Self { storage_path, extensions_path })
    }

    pub fn get_verdent_extension_version(&self) -> Result<String, std::io::Error> {
        if !self.extensions_path.exists() {
            return Err(std::io::Error::new(
                std::io::ErrorKind::NotFound,
                format!("Extensions directory not found: {:?}", self.extensions_path)
            ));
        }

        for entry in fs::read_dir(&self.extensions_path)? {
            let entry = entry?;
            let dir_name = entry.file_name();
            let dir_name_str = dir_name.to_string_lossy();
            
            if dir_name_str.starts_with("verdentai.verdent-") {
                if let Some(version) = dir_name_str.strip_prefix("verdentai.verdent-") {
                    return Ok(version.to_string());
                }
            }
        }

        Err(std::io::Error::new(
            std::io::ErrorKind::NotFound,
            "Verdent extension not found"
        ))
    }

    pub fn read_storage(&self) -> Result<VSCodeStorage, std::io::Error> {
        if !self.storage_path.exists() {
            return Err(std::io::Error::new(
                std::io::ErrorKind::NotFound,
                format!("VS Code storage file not found: {:?}", self.storage_path)
            ));
        }

        let content = fs::read_to_string(&self.storage_path)?;
        let data: serde_json::Map<String, Value> = serde_json::from_str(&content)?;
        Ok(VSCodeStorage { data })
    }

    pub fn write_storage(&self, storage: &VSCodeStorage) -> Result<(), std::io::Error> {
        let json = serde_json::to_string_pretty(&storage.data)?;
        
        if let Some(parent) = self.storage_path.parent() {
            fs::create_dir_all(parent)?;
        }
        
        fs::write(&self.storage_path, json)?;
        Ok(())
    }

    pub fn generate_sqm_id() -> String {
        let uuid = Uuid::new_v4();
        format!("{{{}}}", uuid.to_string().to_uppercase())
    }

    pub fn generate_device_id() -> String {
        Uuid::new_v4().to_string()
    }

    pub fn generate_machine_id() -> String {
        let mut rng = rand::thread_rng();
        let random_bytes: [u8; 32] = rng.gen();
        
        let mut hasher = Sha256::new();
        hasher.update(random_bytes);
        let hash = hasher.finalize();
        
        hex::encode(hash)
    }

    pub fn reset_telemetry_ids(&self) -> Result<(String, String, String), std::io::Error> {
        let mut storage = self.read_storage()?;

        let sqm_id = Self::generate_sqm_id();
        let device_id = Self::generate_device_id();
        let machine_id = Self::generate_machine_id();

        storage.data.insert("telemetry.sqmId".to_string(), Value::String(sqm_id.clone()));
        storage.data.insert("telemetry.devDeviceId".to_string(), Value::String(device_id.clone()));
        storage.data.insert("telemetry.machineId".to_string(), Value::String(machine_id.clone()));

        self.write_storage(&storage)?;

        Ok((sqm_id, device_id, machine_id))
    }

    pub fn get_current_ids(&self) -> Result<(Option<String>, Option<String>, Option<String>), std::io::Error> {
        let storage = self.read_storage()?;

        let sqm_id = storage.data.get("telemetry.sqmId")
            .and_then(|v| v.as_str())
            .map(|s| s.to_string());
        
        let device_id = storage.data.get("telemetry.devDeviceId")
            .and_then(|v| v.as_str())
            .map(|s| s.to_string());
        
        let machine_id = storage.data.get("telemetry.machineId")
            .and_then(|v| v.as_str())
            .map(|s| s.to_string());

        Ok((sqm_id, device_id, machine_id))
    }

    pub fn get_storage_path(&self) -> String {
        self.storage_path.to_string_lossy().to_string()
    }

    pub fn clear(&self) -> Result<(), std::io::Error> {
        let mut storage = self.read_storage()?;
        storage.data.remove("telemetry.sqmId");
        storage.data.remove("telemetry.devDeviceId");
        storage.data.remove("telemetry.machineId");
        self.write_storage(&storage)?;
        Ok(())
    }

    pub fn get_all_ids(&self) -> Result<Vec<String>, std::io::Error> {
        let (sqm_id, device_id, machine_id) = self.get_current_ids()?;
        let mut ids = Vec::new();
        
        if let Some(id) = sqm_id {
            ids.push(format!("sqmId: {}", id));
        }
        if let Some(id) = device_id {
            ids.push(format!("devDeviceId: {}", id));
        }
        if let Some(id) = machine_id {
            ids.push(format!("machineId: {}", id));
        }
        
        Ok(ids)
    }
}
