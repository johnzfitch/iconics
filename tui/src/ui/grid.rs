use crate::app::{App, FocusPanel};
use ratatui::{
    layout::{Constraint, Direction, Layout, Rect},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, Paragraph},
    Frame,
};

pub fn render(f: &mut Frame, app: &mut App, area: Rect) {
    let is_focused = app.focus == FocusPanel::Grid;

    // Split into grid area and semantic axis
    let layout = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Min(10),     // Grid
            Constraint::Length(3),   // Semantic axis
        ])
        .split(area);

    // Render grid
    render_grid(f, app, layout[0], is_focused);

    // Render semantic axis slider
    render_semantic_axis(f, app, layout[1]);
}

fn render_grid(f: &mut Frame, app: &mut App, area: Rect, is_focused: bool) {
    let border_style = if is_focused {
        Style::default().fg(Color::Yellow)
    } else {
        Style::default().fg(Color::Gray)
    };

    let block = Block::default()
        .title(format!(
            " Icon Grid ({}/{}) ",
            app.grid_selected_idx + 1,
            app.filtered_icons.len()
        ))
        .borders(Borders::ALL)
        .border_style(border_style);

    let inner_area = block.inner(area);
    f.render_widget(block, area);

    if app.filtered_icons.is_empty() {
        let msg = Paragraph::new("No icons to display")
            .style(Style::default().fg(Color::DarkGray));
        f.render_widget(msg, inner_area);
        return;
    }

    // Calculate grid dimensions
    let cell_width = 12;  // Width per icon cell
    let cell_height = 6;  // Height per icon cell

    let cols = (inner_area.width / cell_width).max(1) as usize;
    let rows = (inner_area.height / cell_height).max(1) as usize;

    // Update app's grid dimensions
    app.grid_cols = cols;
    app.grid_rows = rows;

    let _visible_items = cols * rows;

    // Render grid cells
    for row in 0..rows {
        for col in 0..cols {
            let idx = app.grid_scroll_offset + row * cols + col;
            if idx >= app.filtered_icons.len() {
                break;
            }

            let x = inner_area.x + (col as u16 * cell_width);
            let y = inner_area.y + (row as u16 * cell_height);

            if x + cell_width > inner_area.x + inner_area.width
                || y + cell_height > inner_area.y + inner_area.height
            {
                continue;
            }

            let cell_area = Rect {
                x,
                y,
                width: cell_width,
                height: cell_height,
            };

            let is_selected = idx == app.grid_selected_idx;
            render_grid_cell(f, app, cell_area, idx, is_selected);
        }
    }
}

fn render_grid_cell(f: &mut Frame, app: &App, area: Rect, filtered_idx: usize, is_selected: bool) {
    let icon_idx = app.filtered_icons[filtered_idx];
    let icon = &app.catalog.icons[icon_idx];

    let border_style = if is_selected {
        Style::default()
            .fg(Color::Yellow)
            .add_modifier(Modifier::BOLD)
    } else {
        Style::default().fg(Color::DarkGray)
    };

    let in_basket = app.basket.contains(&icon.id);
    let title = if in_basket {
        format!(" {} ", icon.semantic_name.chars().take(8).collect::<String>())
    } else {
        format!(" {} ", icon.semantic_name.chars().take(8).collect::<String>())
    };

    let block = Block::default()
        .borders(Borders::ALL)
        .border_style(border_style)
        .title(title);

    let inner = block.inner(area);
    f.render_widget(block, area);

    // Try to render image if we have a cached protocol for this icon
    // Note: For full implementation, we'd need to load grid images asynchronously
    // For now, just show a placeholder
    let placeholder = if in_basket {
        Paragraph::new("[+]").style(Style::default().fg(Color::Green))
    } else {
        Paragraph::new("[]").style(Style::default().fg(Color::DarkGray))
    };

    f.render_widget(placeholder, inner);
}

fn render_semantic_axis(f: &mut Frame, app: &App, area: Rect) {
    // Semantic axis slider
    let axis_text = if app.embeddings.is_some() {
        Line::from(vec![
            Span::styled("[Open]", Style::default().fg(Color::Cyan)),
            Span::raw(" "),
            Span::styled("━━━━━━━━━●━━━━━━━━━", Style::default().fg(Color::DarkGray)),
            Span::raw(" "),
            Span::styled("[Closed]", Style::default().fg(Color::Magenta)),
        ])
    } else {
        Line::from(vec![
            Span::styled("Semantic Axis: ", Style::default().fg(Color::DarkGray)),
            Span::raw("CLIP embeddings not loaded"),
        ])
    };

    let axis = Paragraph::new(axis_text)
        .block(
            Block::default()
                .borders(Borders::ALL)
                .border_style(Style::default().fg(Color::DarkGray))
        );

    f.render_widget(axis, area);
}
