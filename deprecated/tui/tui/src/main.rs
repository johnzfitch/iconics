mod app;
mod data;
mod ui;

use anyhow::Result;
use crossterm::{
    event::{self, DisableMouseCapture, EnableMouseCapture, Event, KeyCode, KeyEventKind},
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use ratatui::{backend::CrosstermBackend, Terminal};
use std::{
    io,
    path::PathBuf,
};

use app::{App, FocusPanel, LogLevel};
use data::catalog::IconCatalog;
use data::embeddings::EmbeddingData;

#[tokio::main]
async fn main() -> Result<()> {
    // Setup terminal
    enable_raw_mode()?;
    let mut stdout = io::stdout();
    execute!(stdout, EnterAlternateScreen, EnableMouseCapture)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;

    // Determine paths
    let catalog_path = std::env::args()
        .nth(1)
        .map(PathBuf::from)
        .unwrap_or_else(|| {
            let home = std::env::var("HOME").unwrap_or_else(|_| ".".to_string());
            PathBuf::from(home).join("dev/iconics/icon-catalog.json")
        });

    let base_path = catalog_path
        .parent()
        .expect("Failed to get catalog parent directory")
        .to_path_buf();

    // Load catalog
    let catalog = IconCatalog::load(&catalog_path)?;

    // Try to load embeddings
    let embeddings_path = base_path.join("embeddings");
    let embeddings = if embeddings_path.exists() {
        EmbeddingData::load(&embeddings_path).ok()
    } else {
        None
    };

    // Initialize app
    let mut app = App::new(catalog, base_path, embeddings)?;

    // Load first image
    if let Err(e) = app.refresh_selection().await {
        app.log(LogLevel::System, format!("Error loading image: {}", e));
    }

    // Main loop
    let result = run_app(&mut terminal, &mut app).await;

    // Restore terminal
    disable_raw_mode()?;
    execute!(
        terminal.backend_mut(),
        LeaveAlternateScreen,
        DisableMouseCapture
    )?;
    terminal.show_cursor()?;

    result
}

async fn run_app(
    terminal: &mut Terminal<CrosstermBackend<io::Stdout>>,
    app: &mut App,
) -> Result<()> {
    loop {
        terminal.draw(|f| ui::render(f, app))?;

        if app.grid_needs_refresh {
            app.grid_needs_refresh = false;
            if let Err(e) = app.load_visible_grid_images().await {
                app.log(LogLevel::System, format!("Grid load error: {}", e));
            }
        }

        if event::poll(std::time::Duration::from_millis(100))? {
            if let Event::Key(key) = event::read()? {
                if key.kind != KeyEventKind::Press {
                    continue;
                }

                if app.search_mode {
                    match key.code {
                        KeyCode::Esc => {
                            app.search_mode = false;
                            app.log(LogLevel::Info, "Search cancelled");
                        }
                        KeyCode::Enter => {
                            app.search_mode = false;
                            app.filter_icons();
                            if let Err(e) = app.refresh_selection().await {
                                app.log(LogLevel::System, format!("Error loading image: {}", e));
                            }
                        }
                        KeyCode::Backspace => {
                            app.search_query.pop();
                        }
                        KeyCode::Char(c) => {
                            app.search_query.push(c);
                        }
                        _ => {}
                    }
                } else {
                    // Global keybindings
                    match key.code {
                        KeyCode::Char('q') => {
                            app.log(LogLevel::System, "Exiting Iconics TUI");
                            break;
                        }
                        KeyCode::Tab => {
                            app.cycle_focus();
                        }
                        KeyCode::Char('/') => {
                            app.search_mode = true;
                            app.search_query.clear();
                            app.log(LogLevel::Info, "Search mode activated");
                        }
                        KeyCode::Char('d') => {
                            app.show_dedupe = !app.show_dedupe;
                            app.log(
                                LogLevel::Info,
                                format!("Dedupe panel: {}", if app.show_dedupe { "shown" } else { "hidden" })
                            );
                        }
                        KeyCode::Char('a') => {
                            app.show_audit = !app.show_audit;
                            app.log(
                                LogLevel::Info,
                                format!("Audit log: {}", if app.show_audit { "shown" } else { "hidden" })
                            );
                        }
                        KeyCode::Char(' ') => {
                            app.toggle_basket();
                        }
                        KeyCode::Char('y') => {
                            if let Err(e) = app.export_basket_to_clipboard() {
                                app.log(LogLevel::System, format!("Export failed: {}", e));
                            }
                        }
                        _ => {
                            // Panel-specific keybindings
                            handle_panel_input(app, key.code).await?;
                        }
                    }
                }
            }
        }
    }

    Ok(())
}

async fn handle_panel_input(app: &mut App, key_code: KeyCode) -> Result<()> {
    match app.focus {
        FocusPanel::Grid => {
            match key_code {
                KeyCode::Down | KeyCode::Char('j') => {
                    app.grid_next();
                    if let Err(e) = app.refresh_selection().await {
                        app.log(LogLevel::System, format!("Error loading image: {}", e));
                    }
                }
                KeyCode::Up | KeyCode::Char('k') => {
                    app.grid_previous();
                    if let Err(e) = app.refresh_selection().await {
                        app.log(LogLevel::System, format!("Error loading image: {}", e));
                    }
                }
                KeyCode::Right | KeyCode::Char('l') => {
                    app.grid_move_right();
                    if let Err(e) = app.refresh_selection().await {
                        app.log(LogLevel::System, format!("Error loading image: {}", e));
                    }
                }
                KeyCode::Left | KeyCode::Char('h') => {
                    app.grid_move_left();
                    if let Err(e) = app.refresh_selection().await {
                        app.log(LogLevel::System, format!("Error loading image: {}", e));
                    }
                }
                KeyCode::Char('g') => {
                    if !app.filtered_icons.is_empty() {
                        app.grid_selected_idx = 0;
                        app.grid_scroll_offset = 0;
                        if let Err(e) = app.refresh_selection().await {
                            app.log(LogLevel::System, format!("Error loading image: {}", e));
                        }
                    }
                }
                KeyCode::Char('G') => {
                    if !app.filtered_icons.is_empty() {
                        app.grid_selected_idx = app.filtered_icons.len() - 1;
                        let visible_items = app.grid_cols * app.grid_rows;
                        if app.filtered_icons.len() > visible_items {
                            app.grid_scroll_offset = app.filtered_icons.len() - visible_items;
                        }
                        if let Err(e) = app.refresh_selection().await {
                            app.log(LogLevel::System, format!("Error loading image: {}", e));
                        }
                    }
                }
                _ => {}
            }
        }
        FocusPanel::Tree => {
            match key_code {
                KeyCode::Down | KeyCode::Char('j') => {
                    if app.tree_state.key_down() {
                        app.apply_tree_selection().await?;
                    }
                }
                KeyCode::Up | KeyCode::Char('k') => {
                    if app.tree_state.key_up() {
                        app.apply_tree_selection().await?;
                    }
                }
                KeyCode::Right | KeyCode::Char('l') => {
                    if app.tree_state.key_right() {
                        app.apply_tree_selection().await?;
                    }
                }
                KeyCode::Left | KeyCode::Char('h') => {
                    if app.tree_state.key_left() {
                        app.apply_tree_selection().await?;
                    }
                }
                KeyCode::Enter => {
                    if app.tree_state.toggle_selected() {
                        app.apply_tree_selection().await?;
                    }
                }
                KeyCode::Esc => {
                    if app.tree_state.select(Vec::new()) {
                        app.apply_tree_selection().await?;
                    }
                }
                _ => {}
            }
        }
        FocusPanel::Details => {
            // Details panel navigation (scroll through variants, etc.)
            match key_code {
                KeyCode::Down | KeyCode::Char('j') => {
                    // Scroll down
                }
                KeyCode::Up | KeyCode::Char('k') => {
                    // Scroll up
                }
                _ => {}
            }
        }
        FocusPanel::Dedupe => {
            // Dedupe management actions
            match key_code {
                KeyCode::Char('m') => {
                    app.log(LogLevel::Dedupe, "Merged to canonical (placeholder)");
                }
                KeyCode::Char('s') => {
                    app.log(LogLevel::Dedupe, "Kept as separate (placeholder)");
                }
                _ => {}
            }
        }
        FocusPanel::Audit => {
            // Audit log navigation (scroll)
            match key_code {
                KeyCode::Down | KeyCode::Char('j') => {
                    app.audit_scroll = app.audit_scroll.saturating_add(1);
                }
                KeyCode::Up | KeyCode::Char('k') => {
                    app.audit_scroll = app.audit_scroll.saturating_sub(1);
                }
                _ => {}
            }
        }
    }

    Ok(())
}
