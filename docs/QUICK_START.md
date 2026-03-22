# Iconics Quick Start Guide

**Fast, on-the-fly icon usage from anywhere**

---

## Getting Started

Use the repo-local CLI entrypoint directly:

```bash
cd /home/zack/dev/iconics
uv run python iconics.py --help
```

---

## The Fastest Workflows

### 1. Find and Use Icons

```bash
# Find icons
uv run python iconics.py search authentication

# Use them instantly (exports + generates markdown)
uv run python iconics.py use lock key
```

### 2. Get Suggestions

```bash
uv run python iconics.py suggest authentication
uv run python iconics.py suggest network
uv run python iconics.py suggest error
```

### 3. Just Get Markdown

```bash
uv run python iconics.py md shield database network
```

---

## Common Workflows

### Starting a New Project

```bash
uv run python iconics.py suggest security
uv run python iconics.py use lock shield key certificate
```

### Adding Icons to Existing Documentation

```bash
uv run python iconics.py search data
uv run python iconics.py use database folder documents
```

### Export All Icons from a Category

```bash
uv run python iconics.py cat security
uv run python iconics.py cat ui
```

---

## Quick Command Reference

| Command | What It Does | Example |
|---------|--------------|---------|
| `iconics search <query>` | Find icons by keyword | `uv run python iconics.py search security` |
| `iconics use <name>...` | Export + generate markdown | `uv run python iconics.py use lock shield` |
| `iconics suggest <context>` | Get icon suggestions | `uv run python iconics.py suggest api` |
| `iconics md <name>...` | Generate markdown only | `uv run python iconics.py md network` |
| `iconics cat <category>` | Export whole category | `uv run python iconics.py cat security` |
| `iconics info <name>` | Show icon details | `uv run python iconics.py info lock` |
| `iconics recent` | Show recently added | `uv run python iconics.py recent` |
| `iconics stats` | Show library stats | `uv run python iconics.py stats` |

---

## Context Suggestions

The `suggest` command understands these contexts:

- `authentication` / `auth` / `login` -> lock, key, shield, certificate, login
- `security` / `secure` -> shield, lock, key, protection, certificate
- `network` / `api` / `server` -> network, cloud, globe, wifi, connect
- `data` / `database` -> database, folder, save-file, cloud, documents
- `error` / `warning` -> warning, error, alert, caution, danger
- `success` / `done` -> checkbox, checkmark, success, done
- `info` / `help` -> info, help, question, about
- `settings` / `config` -> settings, options, control-panel, toolbox
- `navigation` / `menu` -> home, menu, arrows, close
- `files` / `docs` -> folder, document, pdf, file
- `code` / `development` -> console, script, database, terminal
- `search` / `find` -> search, find, magnifying-glass, lookup
- `user` / `account` -> login, logout, user, profile

---

## Smart Features

### 1. Project Auto-Detection

The `iconics use` command automatically detects your project root:
- First tries git root (`git rev-parse --show-toplevel`)
- Falls back to nearest README.md location
- Exports icons to `.github/assets/icons/`
- Generates correct relative paths in markdown

### 2. Path-Aware Markdown

Markdown snippets adjust paths based on your current directory:
```bash
cd /home/zack/dev/myproject          # -> .github/assets/icons/lock.png
cd /home/zack/dev/myproject/docs     # -> ../.github/assets/icons/lock.png
cd /home/zack/dev/myproject/src/api  # -> ../../.github/assets/icons/lock.png
```

### 3. Batch Operations

All commands support multiple icons:
```bash
uv run python iconics.py use warning error info success
uv run python iconics.py md lock key shield certificate
uv run python iconics.py info lock key shield
```

---

## Shortcuts

All commands have short aliases:

| Full | Short | Example |
|------|-------|---------|
| `search` | `s` | `icon s security` |
| `use` | `u` | `icon u lock` |
| `suggest` | `sug` | `icon sug auth` |
| `md` | `md` | `iconics md lock` |
| `here` | `h` | `icon h warning` |
| `cat` | `cat` | `iconics cat ui` |
| `info` | `i` | `iconics info lock` |
| `recent` | `r` | `icon r` |
| `stats` | `st` | `icon st` |
| `validate` | `v` | `icon v` |
| `list` | `l` | `icon l security` |

---

## Real-World Examples

### Example 1: Adding Security Section to README

```bash
uv run python iconics.py suggest security
uv run python iconics.py use lock shield
```

### Example 2: API Documentation

```bash
uv run python iconics.py suggest api
uv run python iconics.py use network database cloud
```

### Example 3: Quick Error Documentation

```bash
uv run python iconics.py use error warning info
```

---

## Tips & Tricks

### 1. Combine Search + Use

```bash
uv run python iconics.py search security
uv run python iconics.py use lock shield certificate
```

### 2. Preview Before Using

```bash
uv run python iconics.py info lock
uv run python iconics.py use lock
```

### 3. Explore by Category

```bash
uv run python iconics.py cat security
```

### 4. Track Recent Additions

```bash
uv run python iconics.py recent
uv run python iconics.py use arrow-up arrow-down arrow-left arrow-right
```

---

## For AI Assistants

This tool is designed for quick, emoji-free icon usage:

### Typical Workflow:
1. `iconics suggest <context>` to recommend appropriate icons.
2. `iconics use <names>` to export and generate ready-to-paste markdown.
3. Include the generated markdown in documentation.

### Example:

User: "Add security documentation to the README"

Assistant:
`uv run python iconics.py suggest security`
`uv run python iconics.py use lock shield`

Then include:

```markdown
## ![lock](.github/assets/icons/lock.png) Security Features
### ![shield](.github/assets/icons/shield.png) Encrypted Data
```

### Benefits Over Emojis:
- Professional appearance with semantic icons
- Consistent styling across all projects
- Meaningful visuals that match the content
- Reusable assets tracked in git
- No emoji rendering issues across platforms

---

## Troubleshooting

### Command not found

Use `uv run python iconics.py ...` from the repo root, or add the repo wrapper to your PATH.

### Icons not showing in GitHub

Verify the icon files exist:

```bash
ls -la .github/assets/icons/
```

### Need to update icon library

```bash
cd /home/zack/dev/iconics
git pull origin master
```

---

## Advanced Usage

### Export to Specific Directory

```bash
cd /path/to/project
uv run python /home/zack/dev/iconics/iconics.py use lock shield
```

### Generate CSV for Bulk Import

```bash
cd /home/zack/dev/iconics
uv run python iconics.py db migrate --overwrite
uv run python iconics.py import batch.csv
```

### Validate Icon Library

```bash
uv run python iconics.py validate
```

---

## Getting Help

```bash
uv run python iconics.py --help
uv run python iconics.py db --help
```

---

**Iconics** - Professional icons, instantly accessible everywhere
