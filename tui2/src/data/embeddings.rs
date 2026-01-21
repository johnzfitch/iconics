use anyhow::{bail, ensure, Context, Result};
use ndarray::{Array2, ArrayView1};
use ndarray_npy::read_npy;
use serde::Deserialize;
use std::{cmp::Ordering, collections::HashMap, path::Path};

#[derive(Debug, Clone, Deserialize)]
#[allow(dead_code)]
#[serde(rename_all = "camelCase")]
pub struct EmbeddingMetadata {
    #[serde(default)]
    pub version: Option<String>,
    #[serde(default)]
    pub model: Option<String>,
    #[serde(default)]
    pub dimension: usize,
    #[serde(default, alias = "totalIcons", alias = "total_icons")]
    pub count: usize,
    #[serde(default)]
    pub dtype: Option<String>,
    #[serde(default)]
    pub pretrained: Option<String>,
    #[serde(default)]
    pub device: Option<String>,
    #[serde(default)]
    pub timestamp: Option<String>,
}

#[derive(Debug)]
pub struct EmbeddingData {
    pub metadata: EmbeddingMetadata,
    pub embeddings: Array2<f32>,
    pub icon_index: HashMap<String, usize>,
    pub index_to_icon: Vec<String>,
    pub norms: Vec<f32>,
}

impl EmbeddingData {
    pub fn load(embeddings_dir: &Path) -> Result<Self> {
        let metadata_path = embeddings_dir.join("metadata.json");
        let content = std::fs::read_to_string(&metadata_path)
            .context("Failed to read embeddings metadata")?;
        let mut metadata: EmbeddingMetadata = serde_json::from_str(&content)
            .context("Failed to parse embeddings metadata")?;

        let embeddings_path = embeddings_dir.join("icon_embeddings.npy");
        let embeddings: Array2<f32> = read_npy(&embeddings_path)
            .context("Failed to read embeddings numpy array")?;

        let index_path = embeddings_dir.join("icon_index.json");
        let index_content = std::fs::read_to_string(&index_path)
            .context("Failed to read embeddings index")?;
        let icon_index: HashMap<String, usize> = serde_json::from_str(&index_content)
            .context("Failed to parse embeddings index")?;

        let rows = embeddings.nrows();
        let cols = embeddings.ncols();

        if metadata.count == 0 {
            metadata.count = rows;
        }
        if metadata.dimension == 0 {
            metadata.dimension = cols;
        }

        ensure!(
            metadata.count == rows,
            "Embedding metadata count ({}) does not match array rows ({})",
            metadata.count,
            rows
        );
        ensure!(
            metadata.dimension == cols,
            "Embedding metadata dimension ({}) does not match array cols ({})",
            metadata.dimension,
            cols
        );
        ensure!(
            icon_index.len() == rows,
            "Embedding index size ({}) does not match array rows ({})",
            icon_index.len(),
            rows
        );

        let mut index_to_icon = vec![String::new(); rows];
        for (icon_id, idx) in &icon_index {
            if *idx >= rows {
                bail!(
                    "Embedding index out of bounds: {} (rows={})",
                    idx,
                    rows
                );
            }
            index_to_icon[*idx] = icon_id.clone();
        }

        if index_to_icon.iter().any(|id| id.is_empty()) {
            bail!("Embedding index is missing one or more icon IDs");
        }

        let norms = embeddings
            .outer_iter()
            .map(|row| row.dot(&row).sqrt())
            .collect();

        Ok(Self {
            metadata,
            embeddings,
            icon_index,
            index_to_icon,
            norms,
        })
    }

    pub fn index_for(&self, icon_id: &str) -> Option<usize> {
        self.icon_index.get(icon_id).copied()
    }

    pub fn embedding_for(&self, icon_id: &str) -> Option<ArrayView1<'_, f32>> {
        let idx = self.index_for(icon_id)?;
        Some(self.embeddings.row(idx))
    }

    pub fn embedding_preview(&self, icon_id: &str, dims: usize) -> Option<String> {
        let embedding = self.embedding_for(icon_id)?;
        let preview_dims = dims.min(embedding.len());
        let values: Vec<String> = embedding
            .iter()
            .take(preview_dims)
            .map(|value| format!("{value:.3}"))
            .collect();
        let suffix = if embedding.len() > preview_dims { ", ..." } else { "" };
        Some(format!("[{}{}]", values.join(", "), suffix))
    }

    pub fn norm_for(&self, icon_id: &str) -> Option<f32> {
        let idx = self.index_for(icon_id)?;
        self.norms.get(idx).copied()
    }

    pub fn top_similar(&self, icon_id: &str, k: usize) -> Option<Vec<(String, f32)>> {
        let idx = self.index_for(icon_id)?;
        let query = self.embeddings.row(idx);
        let query_norm = self.norms.get(idx).copied().unwrap_or(0.0);
        if query_norm == 0.0 {
            return Some(Vec::new());
        }

        let mut scores = Vec::with_capacity(self.embeddings.nrows().saturating_sub(1));
        for (row_idx, row) in self.embeddings.outer_iter().enumerate() {
            if row_idx == idx {
                continue;
            }
            let denom = query_norm * self.norms[row_idx];
            if denom == 0.0 {
                continue;
            }
            let mut dot = 0.0;
            for (a, b) in row.iter().zip(query.iter()) {
                dot += a * b;
            }
            let score = dot / denom;
            scores.push((row_idx, score));
        }

        scores.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(Ordering::Equal));
        scores.truncate(k);

        Some(
            scores
                .into_iter()
                .map(|(row_idx, score)| (self.index_to_icon[row_idx].clone(), score))
                .collect(),
        )
    }
}
