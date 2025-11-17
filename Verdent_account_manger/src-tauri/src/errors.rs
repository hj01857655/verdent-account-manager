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
