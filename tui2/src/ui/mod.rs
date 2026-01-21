pub mod header;
pub mod tree;
pub mod grid;
pub mod details;
pub mod dedupe;
pub mod audit;
pub mod help;

use crate::app::App;
use ratatui::{
    layout::{Constraint, Direction, Layout},
    Frame,
};

pub fn render(f: &mut Frame, app: &mut App) {
    let main_layout = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(3),  // Header
            Constraint::Min(10),    // Main content
            Constraint::Length(8),  // Bottom panels (dedupe + audit)
        ])
        .split(f.area());

    // Render header
    header::render(f, app, main_layout[0]);

    // Main content area (3 columns: tree, grid, details)
    let content_layout = Layout::default()
        .direction(Direction::Horizontal)
        .constraints([
            Constraint::Percentage(25),  // Tree
            Constraint::Percentage(50),  // Grid
            Constraint::Percentage(25),  // Details
        ])
        .split(main_layout[1]);

    // Render main panels
    tree::render(f, app, content_layout[0]);
    grid::render(f, app, content_layout[1]);
    details::render(f, app, content_layout[2]);

    // Bottom area (dedupe + audit)
    if app.show_dedupe || app.show_audit {
        let bottom_layout = Layout::default()
            .direction(Direction::Horizontal)
            .constraints([
                Constraint::Percentage(30),  // Dedupe
                Constraint::Percentage(70),  // Audit
            ])
            .split(main_layout[2]);

        if app.show_dedupe {
            dedupe::render(f, app, bottom_layout[0]);
        }

        if app.show_audit {
            audit::render(f, app, bottom_layout[1]);
        }
    }

    if app.show_help {
        help::render(f, app, f.area());
    }
}
