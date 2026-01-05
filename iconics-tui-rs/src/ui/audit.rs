use crate::app::{App, FocusPanel, LogLevel};
use ratatui::{
    layout::Rect,
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, List, ListItem, Paragraph},
    Frame,
};

pub fn render(f: &mut Frame, app: &App, area: Rect) {
    let is_focused = app.focus == FocusPanel::Audit;

    let border_style = if is_focused {
        Style::default().fg(Color::Yellow)
    } else {
        Style::default().fg(Color::Gray)
    };

    let title = format!(" Reflective Audit Log ({} entries) ", app.audit_log.len());

    let block = Block::default()
        .title(title)
        .borders(Borders::ALL)
        .border_style(border_style);

    let inner = block.inner(area);
    f.render_widget(block, area);

    if app.audit_log.is_empty() {
        let msg = Paragraph::new("No log entries yet")
            .style(Style::default().fg(Color::DarkGray));
        f.render_widget(msg, inner);
        return;
    }

    // Show last N entries that fit in the area
    let max_entries = (inner.height as usize).saturating_sub(1);
    let start_idx = if app.audit_log.len() > max_entries {
        app.audit_log.len() - max_entries
    } else {
        0
    };

    let items: Vec<ListItem> = app.audit_log[start_idx..]
        .iter()
        .map(|entry| {
            let timestamp = entry.timestamp.format("%H:%M:%S").to_string();

            let (level_str, level_color) = match entry.level {
                LogLevel::System => ("SYSTEM", Color::Cyan),
                LogLevel::Info => ("INFO", Color::Green),
                LogLevel::Clip => ("CLIP", Color::Yellow),
                LogLevel::Dedupe => ("DEDUPE", Color::Magenta),
            };

            ListItem::new(Line::from(vec![
                Span::styled(
                    format!("[{}] ", timestamp),
                    Style::default().fg(Color::DarkGray)
                ),
                Span::styled(
                    format!("{}: ", level_str),
                    Style::default()
                        .fg(level_color)
                        .add_modifier(Modifier::BOLD)
                ),
                Span::raw(&entry.message),
            ]))
        })
        .collect();

    let list = List::new(items);
    f.render_widget(list, inner);
}
