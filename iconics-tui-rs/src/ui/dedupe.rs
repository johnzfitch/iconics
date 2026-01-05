use crate::app::{App, FocusPanel};
use ratatui::{
    layout::Rect,
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, List, ListItem, Paragraph},
    Frame,
};

pub fn render(f: &mut Frame, app: &App, area: Rect) {
    let is_focused = app.focus == FocusPanel::Dedupe;

    let border_style = if is_focused {
        Style::default().fg(Color::Yellow)
    } else {
        Style::default().fg(Color::Gray)
    };

    let block = Block::default()
        .title(" Dedupe & Cluster Management ")
        .borders(Borders::ALL)
        .border_style(border_style);

    let inner = block.inner(area);
    f.render_widget(block, area);

    // Placeholder content for dedupe management
    // In a full implementation, this would show:
    // - Current cluster being reviewed
    // - Canonical icon (highest confidence)
    // - Duplicate candidates with match percentages
    // - Action buttons: [Merge to Canonical], [Keep Separate]

    if let Some(icon) = app.get_selected_icon() {
        let items = vec![
            ListItem::new(Line::from(vec![
                Span::styled("Cluster: ", Style::default().fg(Color::Gray)),
                Span::styled(
                    format!("[{}]", icon.semantic_name),
                    Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD)
                ),
            ])),
            ListItem::new(""),
            ListItem::new(Line::from(vec![
                Span::styled("  ★ ", Style::default().fg(Color::Yellow)),
                Span::styled("Canonical: ", Style::default().fg(Color::Green)),
                Span::raw(&icon.semantic_name),
            ])),
            ListItem::new(""),
            ListItem::new(Line::from(vec![
                Span::styled("  ≈ ", Style::default().fg(Color::DarkGray)),
                Span::raw("Similar: lock-32x32 "),
                Span::styled("(98%)", Style::default().fg(Color::Yellow)),
            ])),
            ListItem::new(Line::from(vec![
                Span::styled("  ≈ ", Style::default().fg(Color::DarkGray)),
                Span::raw("Similar: padlock "),
                Span::styled("(87%)", Style::default().fg(Color::Magenta)),
            ])),
        ];

        let list = List::new(items);
        f.render_widget(list, inner);
    } else {
        let msg = Paragraph::new("No clusters detected\n\nThis panel shows duplicate detection\nand variant clustering when available.")
            .style(Style::default().fg(Color::DarkGray));
        f.render_widget(msg, inner);
    }
}
