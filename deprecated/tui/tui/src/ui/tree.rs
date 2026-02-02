use crate::app::{App, FocusPanel};
use ratatui::{
    layout::Rect,
    style::{Color, Modifier, Style},
    widgets::{Block, Borders},
    Frame,
};
use tui_tree_widget::Tree;

pub fn render(f: &mut Frame, app: &mut App, area: Rect) {
    let is_focused = app.focus == FocusPanel::Tree;
    let border_style = if is_focused {
        Style::default().fg(Color::Yellow)
    } else {
        Style::default().fg(Color::Gray)
    };

    let title = if let Some(ref category) = app.active_category {
        format!(" Semantic Library (filter: {}) ", category)
    } else {
        format!(" Semantic Library ({} categories) ", app.tree_items.len())
    };

    let Ok(tree) = Tree::new(&app.tree_items) else {
        return;
    };

    let tree = tree
        .block(
            Block::default()
                .title(title)
                .borders(Borders::ALL)
                .border_style(border_style),
        )
        .highlight_style(
            Style::default()
                .fg(Color::Black)
                .bg(Color::Yellow)
                .add_modifier(Modifier::BOLD),
        )
        .highlight_symbol("> ")
        .node_closed_symbol("+ ")
        .node_open_symbol("- ")
        .node_no_children_symbol("  ");

    f.render_stateful_widget(tree, area, &mut app.tree_state);
}
