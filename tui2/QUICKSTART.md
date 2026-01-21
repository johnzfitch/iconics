# Iconics TUI2 (SQLite) - Quickstart

## 1) Create or refresh the SQLite catalog

```bash
cd /home/zack/dev/iconics
python3 scripts/migrate_catalog_to_sqlite.py --overwrite
```

This writes `/home/zack/dev/iconics/iconics.sqlite3`.

## 2) Launch

```bash
cd /home/zack/dev/iconics
./bin/tui2
```

## 3) Keys (high-signal)

```text
Tab     Cycle focus (Tree / Grid / Details / Dedupe / Audit)
/       Search
Space   Toggle selected icon in basket
y       Copy basket as markdown to clipboard
q       Quit
```

## 4) CLIP filter syntax

```text
clip:<icon_id>     Filter grid to icons similar to <icon_id>
similar:<icon_id>  Alias of clip:
```

