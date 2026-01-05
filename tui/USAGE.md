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

## First Launch

When you launch the TUI, you'll see:

```
┌────────────────────────────┬──────────────────────────────────────┐
│ Icons (4205/4205)          │ Preview                               │
│ >> [security] shield-se... │                                       │
│    [files] folder-48x48    │      [Icon displayed here]            │
│    [development] databa... │                                       │
│    [ui] arrow-up-48x48     │                                       │
│    [ui] arrow-down-48x48   │                                       │
│    ...                     │                                       │
├────────────────────────────┼──────────────────────────────────────┤
│                            │ Metadata                              │
│                            │ ID: shield-security-protection-16x16  │
│                            │ Category: security                    │
│                            │ Tags: shield, 16x16, defense, ...     │
│                            │ Description: Shield security ...      │
│                            │ Path: raw/shield-security-...         │
└────────────────────────────┴──────────────────────────────────────┘
```

## Basic Navigation

| Key | Action |
|-----|--------|
| `j` | Move down one item |
| `k` | Move up one item |
| `↓` | Move down one item (alternative) |
| `↑` | Move up one item (alternative) |
| `g` | Jump to the first icon |
| `G` | Jump to the last icon |
| `q` | Quit the application |

## Search

1. Press `/` to enter search mode
2. Type your search query (searches name, tags, category, description)
3. Press `Enter` to apply the filter
4. Press `Esc` to cancel search
5. Use `Backspace` to delete characters while typing

### Search Examples

- `/security` - Find all security-related icons
- `/shield` - Find icons tagged with "shield"
- `/48x48` - Find all 48x48 icons
- `/folder` - Find folder icons
- `/arrow` - Find arrow icons

## Category Colors

Icons are color-coded by category in the list:

- Red: security
- Blue: network
- Yellow: files
- Green: development
- Magenta: tools
- Cyan: ui
- White: other categories

## Performance Tips

1. Images are cached - navigating back to a previously viewed icon is instant
2. The cache holds 100 images in memory (~200MB)
3. Image loading is async - the UI stays responsive while images load
4. Search is fast even with 4000+ icons

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

Try reducing the cache size by editing `src/main.rs`:
```rust
ImageCache::new(50)  // Instead of 100
```

Then rebuild:
```bash
cd iconics-tui-rs && cargo build --release
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
cd iconics-tui-rs
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

1. Press `/`
2. Type the category name (e.g., `files`, `network`, `ui`)
3. Press `Enter`

### Find icons by size

1. Press `/`
2. Type the size (e.g., `48x48`, `16x16`, `64x64`)
3. Press `Enter`

## Tips & Tricks

1. Use `g` and `G` to quickly jump to the start or end of the list
2. Search is incremental - you'll see the count update as you type
3. Press `Esc` in search mode to go back without filtering
4. The status bar shows how many icons match your search
5. Images are automatically resized to fit the preview pane

## Getting Help

For issues or feature requests, see the main Iconics README at:
```
/home/zack/dev/iconics/README.md
```
