use crate::app::App;
use ratatui::{
    layout::Rect,
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, Paragraph},
    Frame,
};

pub fn render(f: &mut Frame, app: &App, area: Rect) {
    let mode = if app.embeddings.is_some() {
        "Hybrid (Keyword/CLIP)"
    } else {
        "Keyword"
    };

    let protocol = "Kitty";
    let status = if app.search_mode {
        format!("Search Mode ('{}')", app.search_query)
    } else {
        format!("Active ({} icons)", app.filtered_icons.len())
    };

    let header_text = Line::from(vec![
        Span::styled(
            " ICONICS EXECUTIVE TUI ",
            Style::default()
                .fg(Color::Cyan)
                .add_modifier(Modifier::BOLD),
        ),
        Span::raw(" | "),
        Span::styled("Mode: ", Style::default().fg(Color::Gray)),
        Span::styled(mode, Style::default().fg(Color::Yellow)),
        Span::raw(" | "),
        Span::styled("Protocol: ", Style::default().fg(Color::Gray)),
        Span::styled(protocol, Style::default().fg(Color::Green)),
        Span::raw(" | "),
        Span::styled("Status: ", Style::default().fg(Color::Gray)),
        Span::styled(status, Style::default().fg(Color::Magenta)),
    ]);

    let header = Paragraph::new(header_text)
        .block(
            Block::default()
                .borders(Borders::ALL)
                .border_style(Style::default().fg(Color::Cyan))
        );

    f.render_widget(header, area);
}
