use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Icon {
    pub id: String,
    #[serde(default)]
    pub filename: Option<String>,
    #[serde(default)]
    pub source_file: Option<String>,
    pub semantic_name: String,
    pub tags: Vec<String>,
    pub category: String,
    pub description: String,
    #[serde(default)]
    pub used_in: Vec<String>,
    #[serde(default)]
    pub metaphor: Option<String>,
    #[serde(default)]
    pub emotional_valence: Option<f32>,
    #[serde(default)]
    pub abstraction_level: Option<u8>,
}

impl Icon {
    /// Get the file path for this icon (filename or source_file)
    pub fn path(&self) -> Option<&str> {
        self.filename.as_deref().or(self.source_file.as_deref())
    }
}

#[derive(Debug, Deserialize)]
pub struct IconCatalog {
    #[allow(dead_code)]
    pub version: String,
    pub icons: Vec<Icon>,
}

impl IconCatalog {
    pub fn load(path: &Path) -> Result<Self> {
        let content = std::fs::read_to_string(path)
            .context("Failed to read catalog file")?;
        let catalog: IconCatalog = serde_json::from_str(&content)
            .context("Failed to parse catalog JSON")?;
        Ok(catalog)
    }
}
