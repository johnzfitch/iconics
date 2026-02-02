# Iconics TUI Quick Start

## Installation

```bash
# Install required dependencies
pip install textual term-image

# Optional: clipboard support
pip install pyperclip
```

## Basic Usage

```bash
# Launch TUI
iconics tui

# Start with search
iconics tui --query "security lock"

# Filter by category
iconics tui --category security

# Combined
iconics tui --category ui --query "button"
```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `/` | Focus search box |
| `↑` `↓` `←` `→` | Navigate icon grid |
| `Enter` | Show usage command for selected icon |
| `c` | Copy file path to clipboard |
| `Esc` | Cancel search / Clear filter |
| `q` | Quit application |
| `?` | Show help overlay |

## Interface Layout

```
┌─────────────────────────────────────────────────────┐
│ Iconics - Icon Library Browser            12:34 PM │ Header
├─────────────────────────────────────────────────────┤
│ Search: lock_                                   [?] │ Search Box
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐     │
│  │ 🔒  │  │ 🔒  │  │ 🔓  │  │ 🔐  │  │ 🔑  │     │ Icon Grid
│  │lock │  │lock │  │unlck│  │key  │  │key  │     │
│  └─────┘  └─────┘  └─────┘  └─────┘  └─────┘     │
│  lock-16  lock-32  unlock   lockkey  key-16       │
│                                                     │
│  [Selected icon highlighted with border]           │
├─────────────────────────────────────────────────────┤
│ lock-32x32                      Category: security  │ Details Panel
│ Tags: lock, padlock, security, auth, protection     │
│ Description: Padlock icon for authentication...     │
│                                                     │
│ Press [Enter] to use, [c] to copy, [q] to quit     │
├─────────────────────────────────────────────────────┤
│ q Quit  / Search  c Copy  ↵ Use  ? Help            │ Footer
└─────────────────────────────────────────────────────┘
```

## Search Tips

### Semantic Search
The TUI uses CLIP embeddings for semantic search:

```
"security lock" → finds locks, shields, keys
"network connection" → finds wifi, globe, server icons
"happy face" → finds smile, emoji icons
```

### Category Filtering
Pre-filter to specific categories:

- `security` - Locks, shields, keys, certificates
- `files` - Folders, documents, archives
- `network` - Wifi, globe, cloud, connections
- `ui` - Buttons, arrows, controls, menus
- `tools` - Settings, search, toolbox
- `development` - Database, console, terminal
- `emoji` - Faces, expressions, characters

## Terminal Compatibility

### Best Experience
- **Kitty terminal** - Full graphics support
- **iTerm2** (macOS) - Inline images
- **xterm** with Sixel - Good quality

### Fallback Rendering
- Any terminal - Uses Unicode blocks or category emoji
- Still fully functional, just less visual

### Check Your Terminal
```bash
# Test if your terminal supports graphics
echo $TERM

# Kitty users
echo $TERM_PROGRAM  # Should show "kitty"
```

## Common Workflows

### 1. Browse by Category
```bash
iconics tui --category security
# Navigate with arrows
# Press Enter to see usage command
```

### 2. Search and Export
```bash
iconics tui --query "network wifi"
# Navigate to desired icon
# Press 'c' to copy path
# Or note the semantic name and use:
iconics use wifi-icon
```

### 3. Explore Similar Icons
```bash
iconics tui --query "lock"
# Results automatically sorted by relevance
# Top results are most similar to query
```

## Troubleshooting

### Dependencies Not Installed
```
Error: TUI dependencies not installed
Solution: pip install textual term-image
```

### Images Not Rendering
```
Problem: Icons show as emoji instead of actual images
Cause: term-image not installed or terminal lacks graphics support
Solution:
  1. pip install term-image
  2. Use Kitty, iTerm2, or Sixel-capable terminal
  3. Emoji fallback still works for browsing
```

### Clipboard Copy Fails
```
Problem: "Copy failed" message
Cause: pyperclip not installed
Solution:
  1. pip install pyperclip
  2. Or manually copy path from details panel
```

### Retriever Not Initialized
```
Error: CLIP retriever not initialized
Cause: Missing embeddings files
Solution:
  1. Check embeddings/ directory exists
  2. Run: iconics embed --force
```

## Performance Notes

- **First launch**: 1-2 seconds (loads catalog + embeddings)
- **Search**: 100-500ms (CLIP similarity computation)
- **Navigation**: Instant (local state)
- **Large library**: Limited to 50 results per search for speed

## Advanced Features

### Viewing Icon Details
Select any icon to see:
- Semantic name
- File path
- Category
- Tags (up to 10 shown)
- Description
- Similarity score (during search)

### Canceling Operations
- `Esc` while in search box → Unfocus search
- `Esc` while browsing → Clear search and show all icons

### Getting Help
Press `?` at any time to see:
- Keyboard shortcuts
- Library statistics
- Current view status

## Development Mode

For debugging and development:

```bash
# Run with Textual dev console
textual run --dev src/iconics_tui.py

# Or standalone
cd /home/zack/dev/iconics
python3 src/iconics_tui.py "lock"
```

## Integration with CLI

The TUI is fully integrated with iconics CLI:

```bash
# Use TUI to browse, then export via CLI
iconics tui --query "security"
# [Find icon: shield-protection-32x32]
iconics use shield-protection
```

## Tips & Tricks

1. **Fast Search**: Type `/` from anywhere to jump to search box
2. **Browse All**: Leave search empty to see all icons (limited to 100)
3. **Category Tags**: Tags include category, making search more powerful
4. **Arrow Navigation**: Hold arrow keys for rapid navigation
5. **Escape Hatch**: `q` works from any state to quit immediately

## Known Limitations

- Grid layout is fixed (5 icons per row)
- No multi-selection
- No direct export from TUI (shows command instead)
- Search limited to 50 results
- All icons limited to 100

These are intentional performance optimizations and may be enhanced in future versions.

---

**Version**: 1.0
**Last Updated**: 2026-01-04
