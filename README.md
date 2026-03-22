# <img src=".github/assets/icons/star-24x24.png" width="24" height="24" alt="star"> Iconics

**A semantic icon library with intelligent tagging and discovery**

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Icons](https://img.shields.io/badge/icons-8202-brightgreen.svg)
![Cataloged](https://img.shields.io/badge/cataloged-8202-brightgreen.svg)
![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen.svg)

[Quick Start](QUICK_START.md) | [For AI Assistants](CLAUDE.md)

---

## <img src=".github/assets/icons/help-book-3d-24x24.png" width="24" height="24" alt="overview"> Overview

Iconics is a locally managed, semantically tagged icon library designed for instant use across projects. Use professional icons instead of emojis in documentation, GitHub READMEs, product docs, and UI guides.

Core goals:
- SQLite as the runtime catalog authority
- Semantic search with metadata fallback when CLIP is unavailable
- One-command export with ready-to-paste markdown
- Local-first usage tracking with no network telemetry

---

## <img src=".github/assets/icons/lightning-24x24.png" width="24" height="24" alt="quick-start"> Quick Start

Use the CLI directly from the repo:

```bash
cd /home/zack/dev/iconics
uv run python iconics.py search security
uv run python iconics.py use lock-24x24 shield-security-protection-24x24
```

Recommended convenience alias:

```bash
alias iconics='uv run python /home/zack/dev/iconics/iconics.py'
```

Example workflow:

```bash
iconics suggest authentication
iconics use lock-24x24 shield-security-protection-24x24
```

Markdown output example:

```markdown
## ![lock](.github/assets/icons/lock-24x24.png) Security Features
### ![shield](.github/assets/icons/shield-security-protection-24x24.png) Encryption
```

---

## <img src=".github/assets/icons/list-24x24.png" width="24" height="24" alt="commands"> Command Reference

- `iconics search <query>`: semantic search with metadata fallback
- `iconics query <text>`: direct CLIP query with metadata fallback
- `iconics suggest <context>`: context-aware suggestions
- `iconics info <name>`: icon metadata
- `iconics use <name...>`: export icons + markdown snippets
- `iconics md <name...>`: markdown only (no export)
- `iconics cat <category> [--limit N|--all]`: export an entire category
- `iconics categories`: list allowed categories
- `iconics recent --limit N`: show most recent catalog additions
- `iconics history [project]`: show usage history from local logs
- `iconics popular --limit N`: show most-used icons from local analytics
- `iconics stats`: library stats summary
- `iconics validate`: integrity checks
- `iconics db migrate|verify`: SQLite catalog operations
- `iconics provision icons|query|manifest|imports`: copy icons or generate framework imports
- `iconics emoji scan|convert`: scan and replace emoji usage
- `iconics sync`: reconcile raw files, catalog entries, and embeddings
- `iconics relabel`: re-run vision labeling for taxonomy cleanup
- `iconics tui`: launch the Rust TUI2

---

## <img src=".github/assets/icons/downloads-folder-24x24.png" width="24" height="24" alt="provision"> Project Provisioning

Copy only the icons you need into a project and keep a manifest:

```bash
iconics provision icons lock-24x24 shield-security-protection-24x24 --dest ./
```

Provision via semantic query:

```bash
iconics provision query "security lock" --dest ./ --k 2
```

Generate framework imports from a manifest:

```bash
iconics provision imports ./iconics-manifest.json --format react --output ./src/icons.tsx
```

---

## <img src=".github/assets/icons/warning-24x24.png" width="24" height="24" alt="emoji"> Emoji Cleanup

Scan a repository for emoji usage and convert to icon markdown:

```bash
iconics emoji scan --path ./docs --output emoji-report.json
iconics emoji convert --report emoji-report.json --apply
```

---

## <img src=".github/assets/icons/gear-24x24.png" width="24" height="24" alt="catalog"> Catalog Management

Manual add:

```bash
iconics add lock-24x24 --semantic lock --tags security,auth --category security --desc "Lock icon"
```

Bulk import from CSV:

```bash
iconics import ./icons-to-import.csv
```

Expected CSV headers:

```csv
id,semantic,tags,category,description
Lock,lock,"security,auth,access",security,Lock icon
```

Usage tracking logs are local only and are ignored via `.gitignore`:
- `icon-usage-history.json`
- `icon-usage-analytics.json`

---

## <img src=".github/assets/icons/wrench-24x24.png" width="24" height="24" alt="deps"> Optional Dependencies

Some commands require extra dependencies:
- `watch`: file watcher support (`iconics watch`)
- `dedupe`: duplicate detection (`iconics dedupe`)

Install with uv:

```bash
cd /home/zack/dev/iconics
uv sync --extra watch --extra dedupe
```

---

## <img src=".github/assets/icons/hierarchy-24x24.png" width="24" height="24" alt="structure"> Directory Structure

```
iconics/
|-- raw/                 # Original icon files
|-- catalog/             # Categorized symlinks
|-- embeddings/          # CLIP embeddings and subspace artifacts
|-- iconics.sqlite3      # SQLite catalog (runtime default)
|-- icon-catalog.json    # Export/bootstrap catalog snapshot
|-- iconics.py           # Unified CLI
`-- deprecated/          # Archived tools and references
```

---

## <img src=".github/assets/icons/accept-24x24.png" width="24" height="24" alt="license"> License

MIT
