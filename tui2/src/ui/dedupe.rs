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

    if let Some(icon) = app.get_selected_icon() {
        let mut items = vec![
            ListItem::new(Line::from(vec![
                Span::styled("Cluster: ", Style::default().fg(Color::Gray)),
                Span::styled(
                    format!("[{}]", icon.semantic_name),
                    Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD),
                ),
            ])),
            ListItem::new(""),
            ListItem::new(Line::from(vec![
                Span::styled("  * ", Style::default().fg(Color::Yellow)),
                Span::styled("Canonical: ", Style::default().fg(Color::Green)),
                Span::raw(&icon.semantic_name),
            ])),
            ListItem::new(""),
        ];

        if app.embeddings.is_some() {
            if app.clip_similar.is_empty() {
                items.push(ListItem::new(Line::from(vec![
                    Span::styled("  ~ ", Style::default().fg(Color::DarkGray)),
                    Span::raw("No CLIP matches available"),
                ])));
            } else {
                for (icon_id, score) in app.clip_similar.iter().take(3) {
                    let name = app
                        .get_icon_by_id(icon_id)
                        .map(|icon| icon.semantic_name.as_str())
                        .unwrap_or(icon_id.as_str());
                    items.push(ListItem::new(Line::from(vec![
                        Span::styled("  ~ ", Style::default().fg(Color::DarkGray)),
                        Span::raw(format!("Similar: {} ", name)),
                        Span::styled(
                            format!("({:.1}%)", score * 100.0),
                            Style::default().fg(Color::Yellow),
                        ),
                    ])));
                }
            }
        } else {
            items.push(ListItem::new(Line::from(vec![
                Span::styled("  ~ ", Style::default().fg(Color::DarkGray)),
                Span::raw("CLIP embeddings not loaded"),
            ])));
        }

        let list = List::new(items);
        f.render_widget(list, inner);
    } else {
        let msg = Paragraph::new("No clusters detected\n\nThis panel shows duplicate detection\nand variant clustering when available.")
            .style(Style::default().fg(Color::DarkGray));
        f.render_widget(msg, inner);
    }
}
