use crate::app::App;
use ratatui::{
    layout::{Alignment, Constraint, Direction, Layout, Rect},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, Clear, Paragraph, Wrap},
    Frame,
};

pub fn render(f: &mut Frame, _app: &App, area: Rect) {
    let popup_area = centered_rect(72, 80, area);

    f.render_widget(Clear, popup_area);

    let title = Line::from(vec![
        Span::styled(" Help ", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD)),
        Span::raw(" "),
        Span::styled("(Esc or ? to close)", Style::default().fg(Color::Gray)),
    ]);

    let block = Block::default()
        .title(title)
        .borders(Borders::ALL)
        .border_style(Style::default().fg(Color::Yellow));

    let inner = block.inner(popup_area);
    f.render_widget(block, popup_area);

    let sections = vec![
        Line::from(vec![Span::styled(
            "Global",
            Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD),
        )]),
        Line::from("  q        Quit"),
        Line::from("  Tab      Cycle focus (Tree / Grid / Details / Dedupe / Audit)"),
        Line::from("  /        Search"),
        Line::from("  Space    Toggle selected icon in basket"),
        Line::from("  y        Copy basket as markdown to clipboard"),
        Line::from("  d        Toggle dedupe panel"),
        Line::from("  a        Toggle audit log panel"),
        Line::from("  ?        Toggle this help"),
        Line::from(""),
        Line::from(vec![Span::styled(
            "Search Mode",
            Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD),
        )]),
        Line::from("  Enter    Apply search"),
        Line::from("  Esc      Cancel search"),
        Line::from("  Backspace Delete character"),
        Line::from("  Typing   Append to query"),
        Line::from(""),
        Line::from(vec![Span::styled(
            "Tree (focused)",
            Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD),
        )]),
        Line::from("  j/k or Up/Down     Move selection"),
        Line::from("  h/l or Left/Right  Collapse/expand"),
        Line::from("  Enter             Toggle expand/collapse"),
        Line::from("  Esc               Clear selection + category filter"),
        Line::from(""),
        Line::from(vec![Span::styled(
            "Grid (focused)",
            Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD),
        )]),
        Line::from("  h/j/k/l or Arrows  Move selection"),
        Line::from("  g                 Jump to first icon"),
        Line::from("  G                 Jump to last icon"),
        Line::from(""),
        Line::from(vec![Span::styled(
            "Dedupe (focused)",
            Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD),
        )]),
        Line::from("  m                 Merge to canonical (placeholder)"),
        Line::from("  s                 Keep as separate (placeholder)"),
        Line::from(""),
        Line::from(vec![Span::styled(
            "Audit (focused)",
            Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD),
        )]),
        Line::from("  j/k or Up/Down     Scroll"),
    ];

    let paragraph = Paragraph::new(sections)
        .style(Style::default().fg(Color::White))
        .alignment(Alignment::Left)
        .wrap(Wrap { trim: true });

    // Add a small left/right padding by nesting in a layout.
    let padded = Layout::default()
        .direction(Direction::Horizontal)
        .constraints([Constraint::Length(2), Constraint::Min(1), Constraint::Length(2)])
        .split(inner);

    f.render_widget(paragraph, padded[1]);
}

fn centered_rect(percent_x: u16, percent_y: u16, r: Rect) -> Rect {
    let popup_layout = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Percentage((100 - percent_y) / 2),
            Constraint::Percentage(percent_y),
            Constraint::Percentage((100 - percent_y) / 2),
        ])
        .split(r);

    Layout::default()
        .direction(Direction::Horizontal)
        .constraints([
            Constraint::Percentage((100 - percent_x) / 2),
            Constraint::Percentage(percent_x),
            Constraint::Percentage((100 - percent_x) / 2),
        ])
        .split(popup_layout[1])[1]
}

