use crate::data::catalog::{Icon, IconCatalog};
use crate::data::embeddings::EmbeddingData;
use anyhow::Result;
use chrono::{DateTime, Local};
use image::DynamicImage;
use lru::LruCache;
use ratatui_image::{picker::Picker, protocol::StatefulProtocol};
use std::{
    collections::HashMap,
    num::NonZeroUsize,
    path::PathBuf,
    sync::Arc,
};
use tokio::sync::Mutex;
use tui_tree_widget::TreeState;

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

pub struct App {
    // Data
    pub catalog: IconCatalog,
    pub embeddings: Option<EmbeddingData>,
    pub base_path: PathBuf,

    // Tree view state
    #[allow(dead_code)]
    pub tree_state: TreeState<String>,
    #[allow(dead_code)]
    pub category_counts: HashMap<String, usize>,

    // Grid view state
    pub filtered_icons: Vec<usize>,
    pub grid_scroll_offset: usize,
    pub grid_selected_idx: usize,
    pub grid_cols: usize,
    pub grid_rows: usize,

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
    #[allow(dead_code)]
    pub grid_image_states: HashMap<String, StatefulProtocol>,

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

        // Build category counts
        let mut category_counts = HashMap::new();
        for icon in &catalog.icons {
            *category_counts.entry(icon.category.clone()).or_insert(0) += 1;
        }

        let picker = Picker::from_query_stdio().unwrap_or_else(|_| Picker::halfblocks());

        let mut app = Self {
            catalog,
            embeddings,
            base_path,
            tree_state: TreeState::default(),
            category_counts,
            filtered_icons,
            grid_scroll_offset: 0,
            grid_selected_idx: 0,
            grid_cols: 8,
            grid_rows: 4,
            selected_icon: None,
            basket: Vec::new(),
            search_mode: false,
            search_query: String::new(),
            image_cache: Arc::new(Mutex::new(ImageCache::new(200))),
            picker,
            current_image_state: None,
            grid_image_states: HashMap::new(),
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

        if app.embeddings.is_some() {
            app.log(LogLevel::Clip, "CLIP embeddings loaded successfully");
        }

        Ok(app)
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
        if self.search_query.is_empty() {
            self.filtered_icons = (0..self.catalog.icons.len()).collect();
        } else {
            let query = self.search_query.to_lowercase();
            self.filtered_icons = self
                .catalog
                .icons
                .iter()
                .enumerate()
                .filter(|(_, icon)| {
                    icon.semantic_name.to_lowercase().contains(&query)
                        || icon.description.to_lowercase().contains(&query)
                        || icon.tags.iter().any(|tag| tag.to_lowercase().contains(&query))
                        || icon.category.to_lowercase().contains(&query)
                })
                .map(|(i, _)| i)
                .collect();

            self.log(LogLevel::Info, format!("Filtered to {} icons matching '{}'", self.filtered_icons.len(), query));
        }

        self.grid_selected_idx = 0;
        self.grid_scroll_offset = 0;
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

    pub async fn load_current_image(&mut self) -> Result<()> {
        let icon = match self.get_selected_icon() {
            Some(icon) => icon.clone(),
            None => return Ok(()),
        };

        let path = match icon.path() {
            Some(p) => p,
            None => return Ok(()),
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
        self.selected_icon = Some(icon);

        Ok(())
    }
}
