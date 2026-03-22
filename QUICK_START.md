# Iconics Quick Start (SQLite + TUI2)

## 1) Build or refresh the SQLite catalog

The Rust TUI2 and the main `iconics.py` CLI now default to SQLite (`iconics.sqlite3`) as the runtime catalog backend.

```bash
cd /home/zack/dev/iconics
uv sync
uv run python iconics.py db migrate --overwrite
```

This creates `/home/zack/dev/iconics/iconics.sqlite3`.

## 2) Verify catalog + embeddings are consistent

```bash
cd /home/zack/dev/iconics
uv run python iconics.py db verify
```

## 3) Use the CLI

### Search (CLIP when available; metadata fallback otherwise)

```bash
cd /home/zack/dev/iconics
uv run python iconics.py search security --limit 10
uv run python iconics.py query "lock shield" --limit 10
```

If CLIP text-embedding deps are missing or the local model cannot initialize, the CLI falls back to metadata-only search (name/tags/category/description).

### Export icons + markdown

```bash
cd /home/zack/dev/iconics
uv run python iconics.py use shield-security-protection-16x16 folder-48x48
```

## 4) Launch TUI2

```bash
cd /home/zack/dev/iconics
uv run python iconics.py tui
```

Start filtered:

```bash
uv run python iconics.py tui --query security
uv run python iconics.py tui --category files
```

## Notes

- `iconics.sqlite3` is generated from `icon-catalog.json` and is intentionally ignored by git via `/home/zack/dev/iconics/.gitignore`.
- Embeddings are stored as files under `/home/zack/dev/iconics/embeddings/`.
- The live subspace artifacts are under `/home/zack/dev/iconics/embeddings/subspace/`.
- `db verify` checks catalog and embedding sync before you rely on search or the TUI.

If you run `python3 iconics.py ...` directly, some machines will pick up system Python without the ML dependencies. For quality and consistency, prefer `uv run python iconics.py ...`.
