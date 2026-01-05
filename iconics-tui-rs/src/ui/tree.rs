use crate::app::{App, FocusPanel};
use ratatui::{
    layout::Rect,
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, List, ListItem},
    Frame,
};
use std::collections::BTreeMap;

pub fn render(f: &mut Frame, app: &App, area: Rect) {
    let is_focused = app.focus == FocusPanel::Tree;

    // Build category tree
    let mut categories: BTreeMap<String, usize> = BTreeMap::new();
    for icon in &app.catalog.icons {
        *categories.entry(icon.category.clone()).or_insert(0) += 1;
    }

    let items: Vec<ListItem> = categories
        .iter()
        .map(|(category, count)| {
            let category_style = get_category_color(category);
            let content = Line::from(vec![
                Span::styled(
                    format!("  {} ", get_category_icon(category)),
                    category_style.add_modifier(Modifier::BOLD),
                ),
                Span::styled(category.clone(), category_style),
                Span::styled(
                    format!(" ({})", count),
                    Style::default().fg(Color::DarkGray),
                ),
            ]);
            ListItem::new(content)
        })
        .collect();

    let title = format!(" Semantic Library ({} categories) ", categories.len());
    let border_style = if is_focused {
        Style::default().fg(Color::Yellow)
    } else {
        Style::default().fg(Color::Gray)
    };

    let list = List::new(items)
        .block(
            Block::default()
                .title(title)
                .borders(Borders::ALL)
                .border_style(border_style),
        );

    f.render_widget(list, area);
}

fn get_category_color(category: &str) -> Style {
    match category {
        "security" => Style::default().fg(Color::Red),
        "network" => Style::default().fg(Color::Blue),
        "files" => Style::default().fg(Color::Yellow),
        "development" => Style::default().fg(Color::Green),
        "tools" => Style::default().fg(Color::Magenta),
        "ui" => Style::default().fg(Color::Cyan),
        "emoji" => Style::default().fg(Color::LightMagenta),
        _ => Style::default().fg(Color::White),
    }
}

fn get_category_icon(category: &str) -> &str {
    match category {
        "security" => "🛡",
        "network" => "🌐",
        "files" => "📁",
        "development" => "⚙",
        "tools" => "🔧",
        "ui" => "🎨",
        "emoji" => "😊",
        _ => "📦",
    }
}
