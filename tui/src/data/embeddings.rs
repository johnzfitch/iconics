use anyhow::{Context, Result};
use serde::Deserialize;
use std::path::Path;

#[derive(Debug, Clone, Deserialize)]
#[allow(dead_code)]
pub struct EmbeddingMetadata {
    pub version: String,
    pub model: String,
    pub dimension: usize,
    pub total_icons: usize,
}

#[derive(Debug)]
#[allow(dead_code)]
pub struct EmbeddingData {
    pub metadata: EmbeddingMetadata,
    // Note: We're not loading the actual numpy arrays yet
    // This would require ndarray crate and numpy bindings
    // For now, just track metadata
}

impl EmbeddingData {
    pub fn load(embeddings_dir: &Path) -> Result<Self> {
        let metadata_path = embeddings_dir.join("metadata.json");
        let content = std::fs::read_to_string(&metadata_path)
            .context("Failed to read embeddings metadata")?;
        let metadata: EmbeddingMetadata = serde_json::from_str(&content)
            .context("Failed to parse embeddings metadata")?;

        Ok(Self { metadata })
    }
}
