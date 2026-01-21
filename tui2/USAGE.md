# Iconics TUI2 - Usage

Iconics TUI2 is the SQLite-backed Rust TUI for browsing the Iconics library with image previews, CLIP embeddings, a tree browser, a grid view, and a basket export workflow.

## Launch

Recommended (auto-builds if needed):

```bash
cd /home/zack/dev/iconics
./bin/tui2
```

Direct binary:

```bash
cd /home/zack/dev/iconics/tui2
cargo build --release
./target/release/iconics-tui2
```

## Data locations

TUI2 needs a SQLite DB (generated from the JSON catalog):

- Default: `/home/zack/dev/iconics/iconics.sqlite3`
- Override (highest priority): first CLI arg
- Override (second priority): `ICONICS_DB=/path/to/iconics.sqlite3`

Embeddings are loaded from the DB directory:

```text
/path/to/
├── iconics.sqlite3
└── embeddings/
    ├── metadata.json
    ├── icon_embeddings.npy
    └── icon_index.json
```

## Keybindings

### Global

| Key | Action |
|-----|--------|
| `q` | Quit |
| `Tab` | Cycle focus between panels |
| `/` | Enter search mode |
| `Space` | Toggle selected icon in/out of basket |
| `y` | Copy basket export to clipboard (markdown) |
| `d` | Toggle dedupe panel |
| `a` | Toggle audit log panel |
| `?` | Toggle in-app help |

### Search mode

| Key | Action |
|-----|--------|
| `Esc` | Cancel search |
| `Enter` | Apply search and exit |
| `Backspace` | Delete character |
| Any character | Append to query |

#### Search examples

- `/security` - Keyword match across name/tags/description/category
- `/48x48` - Useful for size-tagged icons / filenames
- `/clip:shield-security-protection-16x16` - Filter by CLIP similarity to an icon ID
- `/similar:folder-48x48` - Alias of `clip:`

### Tree (when focused)

| Key | Action |
|-----|--------|
| `↑` / `k` | Move up |
| `↓` / `j` | Move down |
| `→` / `l` | Expand (or move to child) |
| `←` / `h` | Collapse (or move to parent) |
| `Enter` | Toggle expand/collapse |
| `Esc` | Clear selection + category filter |

### Grid (when focused)

| Key | Action |
|-----|--------|
| `↑` / `k` | Move up |
| `↓` / `j` | Move down |
| `←` / `h` | Move left |
| `→` / `l` | Move right |
| `g` | Jump to first icon |
| `G` | Jump to last icon |

## Basket export (clipboard / markdown)

- Use `Space` to add/remove the selected icon.
- Press `y` to copy a markdown snippet, one line per icon:
  - `![semantic name](icons/<file>.png)` when `icons/<file>.png` exists
  - Falls back to the catalog path (typically `raw/<file>.png`)

## Troubleshooting

### "SQLite DB does not contain expected 'icons' table"

Run the migration script:

```bash
cd /home/zack/dev/iconics
python3 scripts/migrate_catalog_to_sqlite.py --overwrite
```

### "No icons found"

Verify the DB exists:

```bash
ls -lh /home/zack/dev/iconics/iconics.sqlite3
```

### Clipboard export does not show up in clipboard manager

TUI2 copies basket markdown using multiple backends (arboard + platform helpers). On Wayland, install `wl-copy` (package `wl-clipboard`). On X11, install `xclip` or `xsel`.

### Images look pixelated

Your terminal may be using the halfblock fallback. For best quality, use Kitty graphics protocol terminals like Kitty, WezTerm, or Ghostty.

### Reduce memory usage

Reduce cache size in `/home/zack/dev/iconics/tui2/src/app.rs` and rebuild:

```bash
cd /home/zack/dev/iconics/tui2
cargo build --release
```
