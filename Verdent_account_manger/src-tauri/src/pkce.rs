use rand::Rng;
use sha2::{Digest, Sha256};
use base64::{Engine as _, engine::general_purpose};

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct PkceParams {
    pub state: String,
    pub code_verifier: String,
    pub code_challenge: String,
}

impl PkceParams {
    pub fn generate() -> Self {
        let state = generate_random_hex(32);
        let code_verifier = state.clone();
        
        let mut hasher = Sha256::new();
        hasher.update(code_verifier.as_bytes());
        let hash = hasher.finalize();
        
        let code_challenge = general_purpose::STANDARD
            .encode(hash)
            .replace('+', "-")
            .replace('/', "_")
            .trim_end_matches('=')
            .to_string();
        
        Self {
            state,
            code_verifier,
            code_challenge,
        }
    }
}

fn generate_random_hex(len: usize) -> String {
    let mut rng = rand::thread_rng();
    let bytes: Vec<u8> = (0..len).map(|_| rng.gen()).collect();
    hex::encode(bytes)
}
