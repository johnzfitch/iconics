# Iconics TUI - Quickstart

## Launch
```bash
cd /home/zack/dev/iconics
./tui-rs
```

## Keys
```
j/k     Navigate up/down
g/G     Jump to first/last
/       Search mode
q       Quit
```

## Search
```
/security   Find security icons
/48x48      Find by size
/folder     Find folders
```

## Requirements
- Kitty, WezTerm, or Ghostty terminal (for best image quality)
- Sixel-capable terminal (good quality)
- Any terminal works (basic quality with halfblocks)

## Files
- Binary: `iconics-tui-rs/target/release/iconics-tui`
- Source: `iconics-tui-rs/src/main.rs`
- Launcher: `tui-rs`

## Build
```bash
cd iconics-tui-rs
cargo build --release
```

That's it!
