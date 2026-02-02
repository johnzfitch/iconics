use crate::data::catalog::{Icon, IconCatalog};
use crate::data::embeddings::EmbeddingData;
use anyhow::{Context, Result};
use arboard::Clipboard;
use chrono::{DateTime, Local};
use image::DynamicImage;
use lru::LruCache;
use ratatui_image::{picker::Picker, protocol::StatefulProtocol};
use std::{
    collections::{BTreeMap, HashMap},
    num::NonZeroUsize,
    path::{Path, PathBuf},
    sync::Arc,
};
use tokio::sync::Mutex;
use tui_tree_widget::{TreeItem, TreeState};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum FocusPanel {
    Tree,
    Grid,
    Details,
    Dedupe,
    Audit,
}

#[derive(Debug, Clone)]
pub struct LogEntry {
    pub timestamp: DateTime<Local>,
    pub level: LogLevel,
    pub message: String,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum LogLevel {
    Info,
    Clip,
    Dedupe,
    System,
}

pub struct ImageCache {
    cache: LruCache<String, Arc<DynamicImage>>,
}

impl ImageCache {
    pub fn new(capacity: usize) -> Self {
        Self {
            cache: LruCache::new(NonZeroUsize::new(capacity).unwrap()),
        }
    }

    pub fn get(&mut self, id: &str) -> Option<Arc<DynamicImage>> {
        self.cache.get(id).cloned()
    }

    pub fn insert(&mut self, id: String, image: Arc<DynamicImage>) {
        self.cache.put(id, image);
    }
}

pub struct GridImageCache {
    cache: LruCache<String, StatefulProtocol>,
}

impl GridImageCache {
    pub fn new(capacity: usize) -> Self {
        Self {
            cache: LruCache::new(NonZeroUsize::new(capacity).unwrap()),
        }
    }

    pub fn get_mut(&mut self, id: &str) -> Option<&mut StatefulProtocol> {
        self.cache.get_mut(id)
    }

    pub fn contains(&self, id: &str) -> bool {
        self.cache.contains(id)
    }

    pub fn insert(&mut self, id: String, protocol: StatefulProtocol) {
        self.cache.put(id, protocol);
    }
}

pub struct App {
    // Data
    pub catalog: IconCatalog,
    pub embeddings: Option<EmbeddingData>,
    pub base_path: PathBuf,
    pub icon_index_by_id: HashMap<String, usize>,

    // Tree view state
    pub tree_state: TreeState<String>,
    pub tree_items: Vec<TreeItem<'static, String>>,
    #[allow(dead_code)]
    pub category_counts: HashMap<String, usize>,
    pub active_category: Option<String>,

    // Grid view state
    pub filtered_icons: Vec<usize>,
    pub grid_scroll_offset: usize,
    pub grid_selected_idx: usize,
    pub grid_cols: usize,
    pub grid_rows: usize,
    pub grid_needs_refresh: bool,

    // Details panel state
    pub selected_icon: Option<Icon>,
    pub basket: Vec<String>, // List of staged icon IDs

    // Search
    pub search_mode: bool,
    pub search_query: String,

    // Image rendering
    pub image_cache: Arc<Mutex<ImageCache>>,
    pub picker: Picker,
    pub current_image_state: Option<StatefulProtocol>,
    pub grid_image_states: GridImageCache,

    // CLIP insights
    pub clip_vector_preview: Option<String>,
    pub clip_index: Option<usize>,
    pub clip_norm: Option<f32>,
    pub clip_similar: Vec<(String, f32)>,

    // UI state
    pub focus: FocusPanel,
    pub show_dedupe: bool,
    pub show_audit: bool,
    #[allow(dead_code)]
    pub status_message: String,

    // Audit log
    pub audit_log: Vec<LogEntry>,
    pub audit_scroll: usize,
}

impl App {
    pub fn new(catalog: IconCatalog, base_path: PathBuf, embeddings: Option<EmbeddingData>) -> Result<Self> {
        let filtered_icons: Vec<usize> = (0..catalog.icons.len()).collect();

        let icon_index_by_id = catalog
            .icons
            .iter()
            .enumerate()
            .map(|(idx, icon)| (icon.id.clone(), idx))
            .collect();

        // Build category counts
        let mut category_counts = HashMap::new();
        for icon in &catalog.icons {
            *category_counts.entry(icon.category.clone()).or_insert(0) += 1;
        }

        let tree_items = Self::build_tree_items(&catalog)?;

        let picker = Picker::from_query_stdio().unwrap_or_else(|_| Picker::halfblocks());

        let mut app = Self {
            catalog,
            embeddings,
            base_path,
            icon_index_by_id,
            tree_state: TreeState::default(),
            tree_items,
            category_counts,
            active_category: None,
            filtered_icons,
            grid_scroll_offset: 0,
            grid_selected_idx: 0,
            grid_cols: 8,
            grid_rows: 4,
            grid_needs_refresh: true,
            selected_icon: None,
            basket: Vec::new(),
            search_mode: false,
            search_query: String::new(),
            image_cache: Arc::new(Mutex::new(ImageCache::new(200))),
            picker,
            current_image_state: None,
            grid_image_states: GridImageCache::new(256),
            clip_vector_preview: None,
            clip_index: None,
            clip_norm: None,
            clip_similar: Vec::new(),
            focus: FocusPanel::Grid,
            show_dedupe: true,
            show_audit: true,
            status_message: String::new(),
            audit_log: Vec::new(),
            audit_scroll: 0,
        };

        // Initialize with startup message
        app.log(LogLevel::System, "Iconics Executive TUI initialized");
        app.log(LogLevel::Info, format!("Loaded {} icons from catalog", app.catalog.icons.len()));

        if let Some(ref embeddings) = app.embeddings {
            let model = embeddings
                .metadata
                .model
                .as_deref()
                .unwrap_or("unknown");
            app.log(
                LogLevel::Clip,
                format!(
                    "CLIP embeddings loaded: {} vectors, dim {}, model {}",
                    embeddings.metadata.count,
                    embeddings.metadata.dimension,
                    model
                ),
            );
        }

        Ok(app)
    }

    fn build_tree_items(catalog: &IconCatalog) -> Result<Vec<TreeItem<'static, String>>> {
        let mut grouped: BTreeMap<String, Vec<&Icon>> = BTreeMap::new();
        for icon in &catalog.icons {
            grouped.entry(icon.category.clone()).or_default().push(icon);
        }

        let mut items = Vec::with_capacity(grouped.len());
        for (category, mut icons) in grouped {
            icons.sort_by(|a, b| a.semantic_name.cmp(&b.semantic_name));
            let children: Vec<TreeItem<'static, String>> = icons
                .into_iter()
                .map(|icon| TreeItem::new_leaf(icon.id.clone(), icon.semantic_name.clone()))
                .collect();
            let label = format!("{} ({})", category, children.len());
            let item = TreeItem::new(category.clone(), label, children)
                .context("Failed to build tree items")?;
            items.push(item);
        }

        Ok(items)
    }

    pub fn log(&mut self, level: LogLevel, message: impl Into<String>) {
        self.audit_log.push(LogEntry {
            timestamp: Local::now(),
            level,
            message: message.into(),
        });

        // Keep log bounded
        if self.audit_log.len() > 1000 {
            self.audit_log.drain(0..100);
        }
    }

    pub fn filter_icons(&mut self) {
        let query = self.search_query.trim().to_lowercase();
        let category_filter = self.active_category.as_deref().map(|cat| cat.to_lowercase());

        if let Some(ref embeddings) = self.embeddings {
            let clip_query = query
                .strip_prefix("clip:")
                .or_else(|| query.strip_prefix("similar:"));
            if let Some(raw_query) = clip_query {
                let icon_id = raw_query.trim();
                if !icon_id.is_empty() {
                    if let Some(results) = embeddings.top_similar(icon_id, 200) {
                        self.filtered_icons = results
                            .into_iter()
                            .filter_map(|(id, _)| self.icon_index_by_id.get(&id).copied())
                            .filter(|idx| {
                                if let Some(ref category) = category_filter {
                                    self.catalog.icons[*idx].category.to_lowercase() == *category
                                } else {
                                    true
                                }
                            })
                            .collect();
                        self.log(
                            LogLevel::Clip,
                            format!(
                                "CLIP search: {} results for '{}'",
                                self.filtered_icons.len(),
                                icon_id
                            ),
                        );
                        self.grid_selected_idx = 0;
                        self.grid_scroll_offset = 0;
                        return;
                    }
                    self.log(LogLevel::Clip, format!("No CLIP embedding for '{}'", icon_id));
                }
            }
        }

        self.filtered_icons = self
            .catalog
            .icons
            .iter()
            .enumerate()
            .filter(|(_, icon)| {
                let mut matches = true;
                if let Some(ref category) = category_filter {
                    matches &= icon.category.to_lowercase() == *category;
                }
                if !query.is_empty() {
                    let query_match = icon.semantic_name.to_lowercase().contains(&query)
                        || icon.description.to_lowercase().contains(&query)
                        || icon.tags.iter().any(|tag| tag.to_lowercase().contains(&query))
                        || icon.category.to_lowercase().contains(&query);
                    matches &= query_match;
                }
                matches
            })
            .map(|(i, _)| i)
            .collect();

        if !query.is_empty() || category_filter.is_some() {
            let category_label = category_filter.unwrap_or_else(|| "all".to_string());
            let query_label = if query.is_empty() { "none" } else { query.as_str() };
            self.log(
                LogLevel::Info,
                format!(
                    "Filtered to {} icons (category: {}, query: {})",
                    self.filtered_icons.len(),
                    category_label,
                    query_label
                ),
            );
        }

        self.grid_selected_idx = 0;
        self.grid_scroll_offset = 0;
    }

    pub fn get_icon_by_id(&self, icon_id: &str) -> Option<&Icon> {
        let idx = self.icon_index_by_id.get(icon_id)?;
        self.catalog.icons.get(*idx)
    }

    pub fn get_selected_icon(&self) -> Option<&Icon> {
        if self.grid_selected_idx < self.filtered_icons.len() {
            let icon_idx = self.filtered_icons[self.grid_selected_idx];
            self.catalog.icons.get(icon_idx)
        } else {
            None
        }
    }

    pub fn grid_next(&mut self) {
        if self.filtered_icons.is_empty() {
            return;
        }

        if self.grid_selected_idx < self.filtered_icons.len() - 1 {
            self.grid_selected_idx += 1;

            // Auto-scroll if needed
            let visible_items = self.grid_cols * self.grid_rows;
            if self.grid_selected_idx >= self.grid_scroll_offset + visible_items {
                self.grid_scroll_offset += self.grid_cols;
            }
        }
    }

    pub fn grid_previous(&mut self) {
        if self.grid_selected_idx > 0 {
            self.grid_selected_idx -= 1;

            // Auto-scroll if needed
            if self.grid_selected_idx < self.grid_scroll_offset {
                self.grid_scroll_offset = self.grid_scroll_offset.saturating_sub(self.grid_cols);
            }
        }
    }

    pub fn grid_move_right(&mut self) {
        if self.filtered_icons.is_empty() {
            return;
        }

        let new_idx = self.grid_selected_idx + 1;
        if new_idx < self.filtered_icons.len() {
            self.grid_selected_idx = new_idx;

            let visible_items = self.grid_cols * self.grid_rows;
            if self.grid_selected_idx >= self.grid_scroll_offset + visible_items {
                self.grid_scroll_offset += self.grid_cols;
            }
        }
    }

    pub fn grid_move_left(&mut self) {
        if self.grid_selected_idx > 0 {
            self.grid_selected_idx -= 1;

            if self.grid_selected_idx < self.grid_scroll_offset {
                self.grid_scroll_offset = self.grid_scroll_offset.saturating_sub(self.grid_cols);
            }
        }
    }

    fn scroll_to_selected(&mut self) {
        if self.filtered_icons.is_empty() || self.grid_cols == 0 || self.grid_rows == 0 {
            return;
        }

        let selected_row = self.grid_selected_idx / self.grid_cols;
        let top_row = self.grid_scroll_offset / self.grid_cols;
        let bottom_row = top_row + self.grid_rows.saturating_sub(1);

        if selected_row < top_row {
            self.grid_scroll_offset = selected_row * self.grid_cols;
        } else if selected_row > bottom_row {
            let new_top = selected_row.saturating_sub(self.grid_rows.saturating_sub(1));
            self.grid_scroll_offset = new_top * self.grid_cols;
        }
    }

    pub async fn apply_tree_selection(&mut self) -> Result<()> {
        let selection = self.tree_state.selected().to_vec();

        if selection.is_empty() {
            if self.active_category.take().is_some() {
                self.filter_icons();
                self.log(LogLevel::Info, "Category filter cleared");
                self.refresh_selection().await?;
            }
            return Ok(());
        }

        let category = selection[0].clone();
        let category_changed = self.active_category.as_deref() != Some(category.as_str());
        if category_changed {
            self.active_category = Some(category.clone());
            self.filter_icons();
            self.log(LogLevel::Info, format!("Category filter set to '{}'", category));
        }

        if selection.len() > 1 {
            let icon_id = &selection[1];
            if let Some(icon_idx) = self.icon_index_by_id.get(icon_id).copied() {
                if let Some(pos) = self.filtered_icons.iter().position(|idx| *idx == icon_idx) {
                    self.grid_selected_idx = pos;
                    self.scroll_to_selected();
                }
            }
        }

        if category_changed || selection.len() > 1 {
            self.refresh_selection().await?;
        }

        Ok(())
    }

    pub async fn refresh_selection(&mut self) -> Result<()> {
        self.load_current_image().await?;
        self.load_visible_grid_images().await?;
        Ok(())
    }

    pub fn cycle_focus(&mut self) {
        self.focus = match self.focus {
            FocusPanel::Tree => FocusPanel::Grid,
            FocusPanel::Grid => FocusPanel::Details,
            FocusPanel::Details => if self.show_dedupe { FocusPanel::Dedupe } else { FocusPanel::Audit },
            FocusPanel::Dedupe => if self.show_audit { FocusPanel::Audit } else { FocusPanel::Tree },
            FocusPanel::Audit => FocusPanel::Tree,
        };
    }

    pub fn toggle_basket(&mut self) {
        if let Some(icon) = self.get_selected_icon() {
            let id = icon.id.clone();
            let name = icon.semantic_name.clone();
            if let Some(pos) = self.basket.iter().position(|x| x == &id) {
                self.basket.remove(pos);
                self.log(LogLevel::Info, format!("Removed '{}' from basket", name));
            } else {
                self.basket.push(id);
                self.log(LogLevel::Info, format!("Added '{}' to basket", name));
            }
        }
    }

    fn export_path_for_icon(&self, icon: &Icon) -> Option<String> {
        let path = icon.path()?;
        let raw_path = Path::new(path);
        let file_name = raw_path.file_name()?;
        let icons_path = self.base_path.join("icons").join(file_name);
        if icons_path.exists() {
            return Some(format!("icons/{}", file_name.to_string_lossy()));
        }
        Some(path.to_string())
    }

    pub fn export_basket_markdown(&self) -> String {
        let mut lines = Vec::new();
        for icon_id in &self.basket {
            let Some(icon) = self.get_icon_by_id(icon_id) else {
                continue;
            };
            let Some(path) = self.export_path_for_icon(icon) else {
                continue;
            };
            lines.push(format!("![{}]({})", icon.semantic_name, path));
        }
        lines.join("\n")
    }

    pub fn export_basket_to_clipboard(&mut self) -> Result<()> {
        if self.basket.is_empty() {
            self.log(LogLevel::Info, "Basket is empty; nothing to export");
            return Ok(());
        }

        let markdown = self.export_basket_markdown();
        if markdown.is_empty() {
            self.log(LogLevel::Info, "Basket export generated no output");
            return Ok(());
        }

        let mut clipboard = Clipboard::new().context("Failed to access clipboard")?;
        clipboard
            .set_text(markdown)
            .context("Failed to set clipboard contents")?;
        self.log(
            LogLevel::Info,
            format!("Exported {} icons to clipboard as markdown", self.basket.len()),
        );
        Ok(())
    }

    fn clear_clip_insights(&mut self) {
        self.clip_vector_preview = None;
        self.clip_index = None;
        self.clip_norm = None;
        self.clip_similar.clear();
    }

    fn update_clip_insights(&mut self) {
        self.clear_clip_insights();

        let Some(ref embeddings) = self.embeddings else {
            return;
        };
        let Some(ref icon) = self.selected_icon else {
            return;
        };

        self.clip_index = embeddings.index_for(&icon.id);
        self.clip_vector_preview = embeddings.embedding_preview(&icon.id, 6);
        self.clip_norm = embeddings.norm_for(&icon.id);
        if let Some(similar) = embeddings.top_similar(&icon.id, 5) {
            self.clip_similar = similar;
        }
    }

    pub async fn load_visible_grid_images(&mut self) -> Result<()> {
        if self.filtered_icons.is_empty() || self.grid_cols == 0 || self.grid_rows == 0 {
            return Ok(());
        }

        let visible = self.grid_cols * self.grid_rows;
        let end = (self.grid_scroll_offset + visible).min(self.filtered_icons.len());

        for idx in self.grid_scroll_offset..end {
            let icon_idx = self.filtered_icons[idx];
            let icon = &self.catalog.icons[icon_idx];
            let icon_id = icon.id.clone();

            if self.grid_image_states.contains(&icon_id) {
                continue;
            }

            let path = match icon.path() {
                Some(p) => p,
                None => continue,
            };
            let image_path = self.base_path.join(path);

            let cached = {
                let mut cache = self.image_cache.lock().await;
                cache.get(&icon_id)
            };

            let dyn_img = if let Some(img) = cached {
                img
            } else {
                let image_path_clone = image_path.clone();
                let img = tokio::task::spawn_blocking(move || image::open(&image_path_clone)).await??;
                let img = Arc::new(img);
                let mut cache = self.image_cache.lock().await;
                cache.insert(icon_id.clone(), img.clone());
                img
            };

            let protocol = self.picker.new_resize_protocol((*dyn_img).clone());
            self.grid_image_states.insert(icon_id, protocol);
        }

        Ok(())
    }

    pub async fn load_current_image(&mut self) -> Result<()> {
        let icon = match self.get_selected_icon() {
            Some(icon) => icon.clone(),
            None => {
                self.current_image_state = None;
                self.selected_icon = None;
                self.clear_clip_insights();
                return Ok(());
            }
        };

        self.selected_icon = Some(icon.clone());
        self.update_clip_insights();

        let path = match icon.path() {
            Some(p) => p,
            None => {
                self.current_image_state = None;
                return Ok(());
            }
        };
        let image_path = self.base_path.join(path);
        let icon_id = icon.id.clone();

        // Check cache first
        let cached = {
            let mut cache = self.image_cache.lock().await;
            cache.get(&icon_id)
        };

        let dyn_img = if let Some(img) = cached {
            img
        } else {
            let image_path_clone = image_path.clone();
            let img = tokio::task::spawn_blocking(move || {
                image::open(&image_path_clone)
            })
            .await??;

            let img = Arc::new(img);
            let mut cache = self.image_cache.lock().await;
            cache.insert(icon_id.clone(), img.clone());
            img
        };

        let protocol = self.picker.new_resize_protocol((*dyn_img).clone());
        self.current_image_state = Some(protocol);

        Ok(())
    }
}
