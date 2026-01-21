# Iconics TUI2 (SQLite-backed)

Iconics TUI2 is the Rust terminal UI for the Iconics library that reads its catalog from SQLite (`iconics.sqlite3`) instead of the large JSON catalog file. It keeps CLIP embeddings as files on disk (`embeddings/*.npy|json`) and uses them for similarity insights and `clip:` filtering.

## Quick start

1) Build or refresh the SQLite DB:

```bash
cd /home/zack/dev/iconics
python3 scripts/migrate_catalog_to_sqlite.py --overwrite
```

2) Run TUI2:

```bash
cd /home/zack/dev/iconics
./bin/tui2
```

## Config

TUI2 resolves the DB path in this order:

1. First CLI arg: `./bin/tui2 /path/to/iconics.sqlite3`
2. Env var: `ICONICS_DB=/path/to/iconics.sqlite3 ./bin/tui2`
3. Auto-detect: `./iconics.sqlite3` or `../iconics.sqlite3` (based on current working directory)
4. Fallback: `/home/zack/dev/iconics/iconics.sqlite3`

The embeddings directory is resolved as: `<db_parent>/embeddings`.

## Layout (high level)

- Tree (left): category/library browser, drives filtering
- Grid (center): thumbnail grid with keyboard navigation
- Details (right): preview, metadata, CLIP vector preview + similarity list
- Dedupe (bottom-left): similarity/duplicate workflow surface (iterating)
- Audit (bottom-right): timestamped log for actions

## Docs

- User guide: `/home/zack/dev/iconics/tui2/USAGE.md`
- Quickstart: `/home/zack/dev/iconics/tui2/QUICKSTART.md`

## Build

```bash
cd /home/zack/dev/iconics/tui2
cargo build --release
```

The binary is `target/release/iconics-tui2`.

