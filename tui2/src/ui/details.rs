use crate::app::{App, FocusPanel};
use ratatui::{
    layout::{Constraint, Direction, Layout, Rect},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, List, ListItem, Paragraph, Wrap},
    Frame,
};
use ratatui_image::StatefulImage;

pub fn render(f: &mut Frame, app: &mut App, area: Rect) {
    let is_focused = app.focus == FocusPanel::Details;

    let border_style = if is_focused {
        Style::default().fg(Color::Yellow)
    } else {
        Style::default().fg(Color::Gray)
    };

    // Split into sections
    let layout = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(12),  // Large preview
            Constraint::Min(8),      // Metadata
            Constraint::Length(6),   // Variants
            Constraint::Length(4),   // Similarity matrix (placeholder)
            Constraint::Length(6),   // Basket
        ])
        .split(area);

    // Preview section
    render_preview(f, app, layout[0], border_style);

    // Metadata section
    render_metadata(f, app, layout[1], border_style);

    // Variants section
    render_variants(f, app, layout[2], border_style);

    // Similarity matrix section
    render_similarity(f, app, layout[3], border_style);

    // Basket section
    render_basket(f, app, layout[4], border_style);
}

fn render_preview(f: &mut Frame, app: &mut App, area: Rect, border_style: Style) {
    let block = Block::default()
        .title(" Preview ")
        .borders(Borders::ALL)
        .border_style(border_style);

    let inner = block.inner(area);
    f.render_widget(block, area);

    if let Some(ref mut image_state) = app.current_image_state {
        let image_widget = StatefulImage::default();
        f.render_stateful_widget(image_widget, inner, image_state);
    } else {
        let msg = Paragraph::new("No icon selected")
            .style(Style::default().fg(Color::DarkGray));
        f.render_widget(msg, inner);
    }
}

fn render_metadata(f: &mut Frame, app: &App, area: Rect, border_style: Style) {
    let block = Block::default()
        .title(" Metadata ")
        .borders(Borders::ALL)
        .border_style(border_style);

    let inner = block.inner(area);
    f.render_widget(block, area);

    if let Some(icon) = app.get_selected_icon() {
        let mut lines = vec![
            Line::from(vec![
                Span::styled("Name: ", Style::default().fg(Color::Gray)),
                Span::styled(
                    &icon.semantic_name,
                    Style::default().fg(Color::White).add_modifier(Modifier::BOLD)
                ),
            ]),
            Line::from(vec![
                Span::styled("Category: ", Style::default().fg(Color::Gray)),
                Span::styled(&icon.category, Style::default().fg(Color::Cyan)),
            ]),
            Line::from(vec![
                Span::styled("Tags: ", Style::default().fg(Color::Gray)),
                Span::raw(icon.tags.join(", ")),
            ]),
            Line::from(""),
            Line::from(vec![
                Span::styled("Description: ", Style::default().fg(Color::Gray)),
            ]),
            Line::from(icon.description.clone()),
        ];

        // Add CLIP vector info if available
        if app.embeddings.is_some() {
            lines.push(Line::from(""));
            if let Some(ref preview) = app.clip_vector_preview {
                lines.push(Line::from(vec![
                    Span::styled("CLIP Vector: ", Style::default().fg(Color::Yellow)),
                    Span::styled(preview, Style::default().fg(Color::DarkGray)),
                ]));
            } else {
                lines.push(Line::from(vec![
                    Span::styled("CLIP Vector: ", Style::default().fg(Color::Yellow)),
                    Span::styled("unavailable", Style::default().fg(Color::DarkGray)),
                ]));
            }

            if let Some(index) = app.clip_index {
                lines.push(Line::from(vec![
                    Span::styled("Embedding Index: ", Style::default().fg(Color::Gray)),
                    Span::styled(index.to_string(), Style::default().fg(Color::Yellow)),
                ]));
            }

            if let Some(norm) = app.clip_norm {
                lines.push(Line::from(vec![
                    Span::styled("Vector Norm: ", Style::default().fg(Color::Gray)),
                    Span::styled(format!("{norm:.3}"), Style::default().fg(Color::Green)),
                ]));
            }
        }

        let paragraph = Paragraph::new(lines).wrap(Wrap { trim: true });
        f.render_widget(paragraph, inner);
    } else {
        let msg = Paragraph::new("No icon selected")
            .style(Style::default().fg(Color::DarkGray));
        f.render_widget(msg, inner);
    }
}

fn render_variants(f: &mut Frame, app: &App, area: Rect, border_style: Style) {
    let block = Block::default()
        .title(" Variants ")
        .borders(Borders::ALL)
        .border_style(border_style);

    let inner = block.inner(area);
    f.render_widget(block, area);

    if let Some(_icon) = app.get_selected_icon() {
        // Show common size variants
        let variants = vec![
            Line::from(vec![
                Span::raw("  "),
                Span::styled("16x16", Style::default().fg(Color::Cyan)),
                Span::raw("  "),
                Span::styled("32x32", Style::default().fg(Color::Cyan)),
                Span::raw("  "),
                Span::styled("64x64", Style::default().fg(Color::Green).add_modifier(Modifier::BOLD)),
            ]),
            Line::from(vec![
                Span::raw("  "),
                Span::styled("128x128", Style::default().fg(Color::Cyan)),
                Span::raw("  "),
                Span::styled("256x256", Style::default().fg(Color::DarkGray)),
            ]),
        ];

        let paragraph = Paragraph::new(variants);
        f.render_widget(paragraph, inner);
    } else {
        let msg = Paragraph::new("No variants")
            .style(Style::default().fg(Color::DarkGray));
        f.render_widget(msg, inner);
    }
}

fn render_similarity(f: &mut Frame, app: &App, area: Rect, border_style: Style) {
    let block = Block::default()
        .title(" Similarity Matrix ")
        .borders(Borders::ALL)
        .border_style(border_style);

    let inner = block.inner(area);
    f.render_widget(block, area);

    if app.embeddings.is_some() {
        if app.clip_similar.is_empty() {
            let msg = Paragraph::new("No similarity data")
                .style(Style::default().fg(Color::DarkGray));
            f.render_widget(msg, inner);
            return;
        }

        let lines: Vec<Line> = app
            .clip_similar
            .iter()
            .take(3)
            .map(|(icon_id, score)| {
                let name = app
                    .get_icon_by_id(icon_id)
                    .map(|icon| icon.semantic_name.as_str())
                    .unwrap_or(icon_id.as_str());
                Line::from(vec![
                    Span::styled(format!("{score:.3}"), Style::default().fg(Color::Green)),
                    Span::raw(" "),
                    Span::raw(name),
                ])
            })
            .collect();

        let paragraph = Paragraph::new(lines);
        f.render_widget(paragraph, inner);
    } else {
        let msg = Paragraph::new("CLIP required")
            .style(Style::default().fg(Color::DarkGray));
        f.render_widget(msg, inner);
    }
}

fn render_basket(f: &mut Frame, app: &App, area: Rect, border_style: Style) {
    let title = format!(" Basket ({} staged, y=export) ", app.basket.len());

    let block = Block::default()
        .title(title)
        .borders(Borders::ALL)
        .border_style(border_style);

    let inner = block.inner(area);
    f.render_widget(block, area);

    if app.basket.is_empty() {
        let msg = Paragraph::new("No icons staged (press Space to add, y to copy)")
            .style(Style::default().fg(Color::DarkGray));
        f.render_widget(msg, inner);
    } else {
        let items: Vec<ListItem> = app
            .basket
            .iter()
            .take(3)  // Show only first 3
            .filter_map(|id| {
                app.catalog.icons.iter().find(|icon| &icon.id == id)
            })
            .map(|icon| {
                ListItem::new(Line::from(vec![
                    Span::styled("  + ", Style::default().fg(Color::Green)),
                    Span::raw(&icon.semantic_name),
                ]))
            })
            .collect();

        let list = List::new(items);
        f.render_widget(list, inner);
    }
}
