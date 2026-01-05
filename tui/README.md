# Iconics Executive TUI

A sophisticated terminal user interface for browsing and managing the Iconics icon library with CLIP embeddings support.

## Overview

Iconics TUI is a multi-panel terminal interface designed for efficient icon exploration, semantic search, variant management, and duplicate detection. Built with Rust and ratatui, it provides a responsive, keyboard-driven experience with image rendering support via the Kitty graphics protocol.

## Architecture

The application follows a modular architecture:

```
src/
├── main.rs              # Entry point and event loop
├── app.rs               # Application state and logic
├── data/
│   ├── catalog.rs       # Icon catalog loading
│   ├── embeddings.rs    # CLIP embeddings support
│   └── variants.rs      # Variant grouping (placeholder)
└── ui/
    ├── mod.rs           # Layout manager
    ├── header.rs        # Header bar
    ├── tree.rs          # Semantic library tree
    ├── grid.rs          # Icon grid view
    ├── details.rs       # Icon details panel
    ├── dedupe.rs        # Duplicate management
    └── audit.rs         # Reflective audit log
```

## Layout

The TUI features a 6-panel layout:

```
┌─────────────────────────────────────────────────────────────────────────┐
│ ICONICS EXECUTIVE TUI | Mode: Hybrid | Protocol: Kitty | Status: Active │
├──────────────┬──────────────────────────────────────┬───────────────────┤
│              │                                      │                   │
│  Semantic    │   Icon Subspace Explorer & Grid     │  Icon Details &   │
│  Library     │   (Grid of icon images)             │  Variant Manager  │
│  Browser     │                                      │                   │
│  (Tree)      │   [Semantic Axis: Open <-> Closed]  │  - Large preview  │
│              │                                      │  - CLIP vector    │
│              │                                      │  - Variants       │
│              │                                      │  - Similarity     │
│              │                                      │  - Basket         │
├──────────────┼──────────────────────────────────────┴───────────────────┤
│  Dedupe &    │  Reflective Audit Log                                    │
│  Cluster     │  (AI reasoning timestamps)                               │
│  Management  │                                                           │
└──────────────┴───────────────────────────────────────────────────────────┘
```

### Panel Details

1. **Header** (top bar):
   - Title: "ICONICS EXECUTIVE TUI"
   - Mode: Hybrid (Keyword/CLIP) or Keyword-only
   - Protocol: Kitty graphics protocol
   - Status: Current state and icon count

2. **Semantic Library Browser** (left sidebar, 25%):
   - Tree view of icon categories
   - Color-coded by category
   - Shows icon count per category
   - Categories: security, network, files, development, tools, ui, emoji

3. **Icon Grid** (center panel, 50%):
   - Grid layout of icons
   - Dynamic columns/rows based on terminal size
   - Keyboard navigation (arrow keys, hjkl)
   - Visual selection highlight
   - Bottom: Semantic axis slider (when CLIP embeddings loaded)

4. **Icon Details** (right panel, 25%):
   - Large icon preview (Kitty protocol)
   - Metadata: name, category, tags, description
   - CLIP vector preview (when available)
   - Variant sizes (16x16, 32x32, 64x64, 128x128, 256x256)
   - Similarity matrix (placeholder heatmap)
   - Basket: List of staged icons

5. **Dedupe & Cluster Management** (bottom left, 30%):
   - Current cluster view
   - Canonical icon identification
   - Duplicate candidates with match percentages
   - Action buttons (placeholder)

6. **Reflective Audit Log** (bottom right, 70%):
   - Timestamped log entries
   - Color-coded by level:
     - SYSTEM (cyan): System messages
     - INFO (green): User actions
     - CLIP (yellow): CLIP operations
     - DEDUPE (magenta): Duplicate detection
   - Auto-scrolls to bottom
   - Maintains up to 1000 entries

## Keybindings

### Global Keys

| Key | Action |
|-----|--------|
| `q` | Quit application |
| `Tab` | Cycle focus between panels |
| `/` | Enter search mode |
| `Space` | Toggle icon in/out of basket |
| `d` | Toggle dedupe panel visibility |
| `a` | Toggle audit log visibility |

### Search Mode

| Key | Action |
|-----|--------|
| `Esc` | Cancel search |
| `Enter` | Execute search and exit search mode |
| `Backspace` | Delete character |
| Any character | Add to search query |

### Grid Navigation (when focused)

| Key | Action |
|-----|--------|
| `↑` / `k` | Move up |
| `↓` / `j` | Move down |
| `←` / `h` | Move left |
| `→` / `l` | Move right |
| `g` | Jump to first icon |
| `G` | Jump to last icon |

### Tree Navigation (when focused)

| Key | Action |
|-----|--------|
| `↑` / `k` | Navigate up |
| `↓` / `j` | Navigate down |
| `Enter` | Expand/collapse category |

### Dedupe Panel (when focused)

| Key | Action |
|-----|--------|
| `m` | Merge to canonical (placeholder) |
| `s` | Keep as separate (placeholder) |

### Audit Log (when focused)

| Key | Action |
|-----|--------|
| `↑` / `k` | Scroll up |
| `↓` / `j` | Scroll down |

## Features

### Current Features

- **Multi-panel layout** with 6 distinct panels
- **Icon catalog loading** from JSON
- **CLIP embeddings detection** (metadata only for now)
- **Grid view** with dynamic sizing
- **Image preview** using Kitty graphics protocol
- **Search functionality** across icon names, tags, descriptions, categories
- **Basket system** for staging icons
- **Focus management** with Tab cycling
- **Audit logging** with color-coded entries
- **Category-based organization** with color coding

### Planned Enhancements

1. **Full CLIP integration**:
   - Load numpy embedding arrays
   - Semantic similarity search
   - Interactive semantic axis navigation
   - Vector-based icon clustering

2. **Tree widget integration**:
   - Expandable category tree
   - Subcategory support
   - Cluster groups within categories

3. **Variant detection**:
   - Automatic variant grouping (sizes)
   - Canonical icon selection
   - Variant management UI

4. **Duplicate detection**:
   - Perceptual hash comparison
   - CLIP similarity scoring
   - Interactive merge/keep decisions

5. **Grid image rendering**:
   - Load and cache grid cell images
   - Async image loading
   - Thumbnail generation

6. **Export functionality**:
   - Export basket to clipboard
   - Generate markdown snippets
   - Batch export operations

## Building

### Prerequisites

- Rust 1.70+ (2021 edition)
- A terminal with Kitty graphics protocol support (kitty, WezTerm, etc.)

### Build Commands

```bash
# Development build
cargo build

# Release build (optimized)
cargo build --release

# Run
cargo run

# Run with custom catalog path
cargo run -- /path/to/icon-catalog.json
```

## Usage

### Running the TUI

```bash
# Use default catalog path (~/.dev/iconics/icon-catalog.json)
./target/release/iconics-tui

# Use custom catalog path
./target/release/iconics-tui /path/to/icon-catalog.json
```

### Terminal Requirements

The TUI works best with terminals that support:
- Kitty graphics protocol (for image rendering)
- True color (24-bit color)
- UTF-8 encoding
- Minimum 120x30 terminal size recommended

Recommended terminals:
- Kitty
- WezTerm
- iTerm2 (limited graphics support)

### CLIP Embeddings

To enable CLIP features, ensure the embeddings directory exists:

```
/path/to/iconics/
├── icon-catalog.json
└── embeddings/
    ├── metadata.json
    ├── icon_embeddings.npy
    └── icon_index.json
```

The TUI will automatically detect and load the embeddings metadata.

## Dependencies

Key dependencies:
- `ratatui` 0.30 - TUI framework
- `ratatui-image` 10.0 - Image rendering
- `crossterm` 0.29 - Terminal control
- `tui-tree-widget` 0.22 - Tree view widget
- `tokio` 1.x - Async runtime
- `image` 0.25 - Image processing
- `serde_json` - JSON parsing
- `lru` 0.12 - Image caching
- `chrono` 0.4 - Timestamp handling

## Performance

- **Image caching**: LRU cache with 200 entry capacity
- **Async image loading**: Non-blocking image operations
- **Virtual scrolling**: Efficient rendering for 5000+ icons
- **Lazy rendering**: Only visible cells are rendered

## Development

### Code Structure

The codebase follows Rust best practices:
- **Modular design**: Separate concerns into modules
- **Type safety**: Strong typing with minimal `unwrap()`
- **Error handling**: Proper `Result` types with `anyhow`
- **Async/await**: Tokio for async operations
- **Clean architecture**: UI separated from business logic

### Adding New Panels

To add a new panel:

1. Create `src/ui/newpanel.rs`
2. Implement `pub fn render(f: &mut Frame, app: &App, area: Rect)`
3. Add to `src/ui/mod.rs`
4. Update layout in `ui::render()`
5. Add focus state to `FocusPanel` enum
6. Implement panel-specific keybindings

### Adding New Features

1. Update `App` struct in `app.rs` with new state
2. Implement business logic methods on `App`
3. Update relevant UI modules to use new state
4. Add keybindings in `main.rs`
5. Test with `cargo run`

## Troubleshooting

### Images not rendering

- Ensure terminal supports Kitty graphics protocol
- Check terminal size (minimum 120x30)
- Verify icon files exist at paths in catalog

### Search not working

- Ensure search query is entered in search mode (`/` key)
- Press `Enter` to execute search
- Check catalog contains searchable fields

### High memory usage

- Reduce LRU cache size in `App::new()` (default: 200)
- Disable image preview in grid view
- Reduce terminal size to show fewer grid cells

## License

Part of the Iconics project. See main project documentation for license details.

## Contributing

This is a personal project. For bug reports or feature suggestions, please coordinate with the main Iconics project.

## Version History

- **v0.1.0** (2025-01-05): Initial implementation
  - Multi-panel layout (6 panels)
  - Icon catalog loading
  - Grid view with navigation
  - Image preview (Kitty protocol)
  - Search functionality
  - Basket system
  - Audit logging
  - Focus management

## Future Roadmap

1. **Q1 2025**: Full CLIP integration with vector search
2. **Q1 2025**: Tree widget with expandable categories
3. **Q2 2025**: Variant detection and grouping
4. **Q2 2025**: Duplicate detection with perceptual hashing
5. **Q2 2025**: Export functionality
6. **Q3 2025**: Grid image rendering optimization
7. **Q3 2025**: Advanced filtering (size, format, metadata)
8. **Q4 2025**: Icon editing capabilities
9. **Q4 2025**: Batch operations
10. **Q4 2025**: Plugin system for extensions

## Contact

For questions or issues, see the main Iconics project documentation.
