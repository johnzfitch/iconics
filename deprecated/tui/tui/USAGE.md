# Iconics TUI - Quick Start Guide

## Installation

No installation needed! Just run from the project directory:

```bash
cd /home/zack/dev/iconics
./tui-rs
```

Or use the full path:

```bash
/home/zack/dev/iconics/tui-rs
```

If you want to run the compiled release binary directly:

```bash
/home/zack/dev/iconics/tui/target/release/iconics-tui
```

## First Launch (Layout Overview)

When you launch the TUI, you'll see:

```
┌─────────────────────────────────────────────────────────────────────────┐
│ ICONICS EXECUTIVE TUI | Mode: Hybrid/Keyword | Protocol: Kitty | Status  │
├──────────────┬──────────────────────────────────────┬───────────────────┤
│ Semantic     │ Icon Grid + Thumbnails               │ Details            │
│ Library      │ (navigate/select)                     │ (preview + CLIP)   │
│ (Tree)       │                                      │                   │
├──────────────┼──────────────────────────────────────┴───────────────────┤
│ Dedupe       │ Audit Log                                               │
└──────────────┴──────────────────────────────────────────────────────────┘
```

## Basic Navigation

### Global Keys

| Key | Action |
|-----|--------|
| `Tab` | Cycle focus between panels |
| `/` | Enter search mode |
| `Space` | Toggle selected icon in/out of basket |
| `y` | Copy basket export to clipboard (markdown) |
| `d` | Toggle dedupe panel |
| `a` | Toggle audit log panel |
| `q` | Quit the application |

### Tree Navigation (Semantic Library)

| Key | Action |
|-----|--------|
| `j` / `↓` | Move selection down |
| `k` / `↑` | Move selection up |
| `l` / `→` | Expand (or move to child) |
| `h` / `←` | Collapse (or move to parent) |
| `Enter` | Toggle expand/collapse |
| `Esc` | Clear selection and category filter |

Selecting a category filters the Grid to that category. Selecting a leaf (icon) also jumps the Grid selection.

### Grid Navigation (Icon Grid)

| Key | Action |
|-----|--------|
| `j` / `↓` | Move down |
| `k` / `↑` | Move up |
| `l` / `→` | Move right |
| `h` / `←` | Move left |
| `g` | Jump to first icon |
| `G` | Jump to last icon |

## Search

1. Press `/` to enter search mode
2. Type your search query
3. Press `Enter` to apply the filter
4. Press `Esc` to cancel search
5. Use `Backspace` to delete characters while typing

### Search Examples

- `/security` - Filter by keyword match
- `/48x48` - Filter by size tag/filename
- `/folder` - Filter by keyword match
- `/clip:shield-security-protection-16x16` - CLIP similarity filter by icon ID
- `/similar:folder-48x48` - Same as `clip:` (alias)

## Category Colors

Icons are color-coded by category in the UI:

- Red: security
- Blue: network
- Yellow: files
- Green: development
- Magenta: tools
- Cyan: ui
- White: other categories

## Basket Export (Clipboard / Markdown)

- Press `Space` to add/remove the selected icon to the Basket.
- Press `y` to copy a markdown snippet to the clipboard, one line per icon:
  - `![semantic name](icons/<file>.png)` when `icons/<file>.png` exists
  - Falls back to the catalog path (typically `raw/<file>.png`)

## Performance Tips

1. Images are cached - revisiting icons is fast
2. The cache holds 200 decoded images by default
3. Grid thumbnails are lazily loaded for visible cells
4. Image loading is async - the UI stays responsive while images load

## Terminal Requirements

### Best Experience

Use a terminal with Kitty graphics protocol support:
- Kitty
- WezTerm
- Ghostty

These will show full-resolution images with transparency.

### Good Experience

Terminals with Sixel support:
- Foot
- mlterm
- xterm (with `-ti vt340`)

### Basic Experience

Any terminal will work with Unicode half-blocks (lower quality).

The TUI automatically detects the best available protocol.

## Troubleshooting

### "No icons found"

Make sure the catalog exists:
```bash
ls -lh /home/zack/dev/iconics/icon-catalog.json
```

### "Failed to load image"

Check that the raw icons directory exists:
```bash
ls /home/zack/dev/iconics/raw/ | head
```

### Images look pixelated

Your terminal may be using the halfblock fallback. Check if your terminal supports Kitty or Sixel protocols.

### Slow performance

Try reducing the cache size by editing `/home/zack/dev/iconics/tui/src/app.rs`:
```rust
ImageCache::new(100)  // Example: reduce from 200
```

Then rebuild:
```bash
cd /home/zack/dev/iconics/tui && cargo build --release
```

## Advanced Usage

### Custom Catalog Path

```bash
./tui-rs /path/to/custom-catalog.json
```

### Debug Mode

Run with debug output:
```bash
RUST_LOG=debug ./tui-rs 2> debug.log
```

### Build from Source

```bash
cd /home/zack/dev/iconics/tui
cargo build --release
```

The binary will be at `target/release/iconics-tui`.

## Examples

### Find security icons

1. Press `/`
2. Type `security`
3. Press `Enter`
4. Browse with `j`/`k`

### Browse by category

1. Press `Tab` until the Tree is focused
2. Use `j`/`k` to select a category
3. Press `Enter` to expand/collapse, or `l` to expand and select an icon leaf

### Find icons by size

1. Press `/`
2. Type the size (e.g., `48x48`, `16x16`, `64x64`)
3. Press `Enter`

## Tips & Tricks

1. Use `g` and `G` to quickly jump to the start or end of the list
2. Search applies on `Enter` (you can cancel with `Esc`)
3. Press `Esc` in search mode to go back without filtering
4. The status bar shows how many icons match your search
5. Images are automatically resized to fit the preview pane

## Getting Help

For issues or feature requests, see the main Iconics README at:
```
/home/zack/dev/iconics/README.md
```
