# Iconics

Use this skill when you need semantic icons instead of emojis in documentation, code, or UI.

## When to Use

- You are writing or updating documentation that should use icons.
- You need to search, export, or provision icons from the local library.
- You are cleaning up taxonomy or icon usage in a repo.

## Runtime Model

- SQLite is the runtime catalog authority.
- Embeddings live under `/home/zack/dev/iconics/embeddings/`.
- The live subspace artifacts live under `/home/zack/dev/iconics/embeddings/subspace/`.
- `search` and `query` fall back to metadata-only matching when CLIP is unavailable.

## Common Commands

```bash
cd /home/zack/dev/iconics
uv run python iconics.py search security
uv run python iconics.py query "security lock" --limit 5
uv run python iconics.py suggest authentication
uv run python iconics.py use lock-24x24 shield-security-protection-24x24
uv run python iconics.py md lock-24x24 shield-security-protection-24x24
uv run python iconics.py cat security
uv run python iconics.py provision query "security lock" --dest ./icons --k 2
uv run python iconics.py emoji scan --path ./docs --output emoji-report.json
uv run python iconics.py emoji convert --report emoji-report.json --apply
uv run python iconics.py validate
uv run python iconics.py db migrate --overwrite
uv run python iconics.py db verify
uv run python iconics.py tui
```

## Practical Guidance

- Prefer semantic names like `lock`, `shield`, `folder`, and `network` over raw filenames.
- Use `use` when you want icons plus ready-to-paste markdown.
- Use `md` when the icons are already exported and you only need markdown.
- Use `provision query` when you need icons copied into another project.
- Use `relabel` for taxonomy cleanup and `sync` for catalog or embedding drift repair.

## Output Expectations

`query` and `search` should return ranked results. When the CLIP path is unavailable, the CLI should still return metadata-ranked matches from names, tags, categories, and descriptions.

## Notes

- Keep active instructions focused on `iconics.py`; archival material under `deprecated/` is reference only.
- Prefer `uv run python iconics.py ...` so the repo uses its declared Python environment.
