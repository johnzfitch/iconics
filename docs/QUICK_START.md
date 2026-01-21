# Iconics Quick Start Guide

**Fast, on-the-fly icon usage from anywhere**

---

## Installation

```bash
cd /home/zack/dev/iconics
./install.sh
```

**Note:** Add `~/.local/bin` to your PATH if prompted.

---

## The Fastest Workflows

### 1. Find and Use Icons (2 commands)

```bash
# Find icons
iconics search authentication

# Use them instantly (exports + generates markdown)
iconics use lock key
```

**Output:**
```
Exporting to: /home/zack/dev/your-project
✓ Exported lock.png
✓ Exported key.png

Markdown snippets:
  ![lock](.github/assets/icons/lock.png)
  ![key](.github/assets/icons/key.png)
```

**Copy-paste the markdown** directly into your README!

---

### 2. Get Suggestions (1 command)

Don't know which icons to use? Get context-aware suggestions:

```bash
iconics suggest authentication
# Suggests: lock, key, shield, certificate, login

iconics suggest network
# Suggests: network, cloud, globe, wifi, connect, server

iconics suggest error
# Suggests: warning, error, alert, caution, danger
```

---

### 3. Just Get Markdown (no export)

Already have icons exported? Just get the markdown:

```bash
iconics md shield database network
```

**Output:**
```markdown
![shield](.github/assets/icons/shield.png)
![database](.github/assets/icons/database.png)
![network](.github/assets/icons/network.png)
```

---

## Common Workflows

### Starting a New Project

```bash
# Get icon suggestions
iconics suggest security

# Export relevant icons
iconics use lock shield key certificate

# Paste the generated markdown into README.md
```

### Adding Icons to Existing Documentation

```bash
# Search for what you need
iconics search data

# Export and get markdown instantly
iconics use database folder documents
```

### Export All Icons from a Category

```bash
# Export entire security category
iconics cat security

# Or UI category
iconics cat ui
```

---

## Quick Command Reference

| Command | What It Does | Example |
|---------|--------------|---------|
| `iconics search <query>` | Find icons by keyword | `iconics search security` |
| `iconics use <name>...` | Export + generate markdown | `iconics use lock shield` |
| `iconics suggest <context>` | Get icon suggestions | `iconics suggest api` |
| `iconics md <name>...` | Generate markdown only | `iconics md network` |
| `iconics cat <category>` | Export whole category | `iconics cat security` |
| `iconics info <name>` | Show icon details | `iconics info lock` |
| `iconics recent` | Show recently added | `iconics recent` |
| `icon stats` | Show library stats | `icon stats` |

---

## Context Suggestions

The `suggest` command understands these contexts:

- `authentication` / `auth` / `login` → lock, key, shield, certificate, login
- `security` / `secure` → shield, lock, key, protection, certificate
- `network` / `api` / `server` → network, cloud, globe, wifi, connect
- `data` / `database` → database, folder, save-file, cloud, documents
- `error` / `warning` → warning, error, alert, caution, danger
- `success` / `done` → checkbox, checkmark, success, done
- `info` / `help` → info, help, question, about
- `settings` / `config` → settings, options, control-panel, toolbox
- `navigation` / `menu` → home, menu, arrows, close
- `files` / `docs` → folder, document, pdf, file
- `code` / `development` → console, script, database, terminal
- `search` / `find` → search, find, magnifying-glass, lookup
- `user` / `account` → login, logout, user, profile

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
cd /home/zack/dev/myproject          # → .github/assets/icons/lock.png
cd /home/zack/dev/myproject/docs     # → ../.github/assets/icons/lock.png
cd /home/zack/dev/myproject/src/api  # → ../../.github/assets/icons/lock.png
```

### 3. Batch Operations

All commands support multiple icons:
```bash
iconics use warning error info success
iconics md lock key shield certificate
iconics info lock key shield
```

---

## Shortcuts

All commands have short aliases:

| Full | Short | Example |
|------|-------|---------|
| `search` | `s` | `icon s security` |
| `use` | `u` | `icon u lock` |
| `suggest` | `sug` | `icon sug auth` |
| `markdown` | `md` | `iconics md lock` |
| `here` | `h` | `icon h warning` |
| `category` | `cat` | `iconics cat ui` |
| `info` | `i` | `iconics info lock` |
| `recent` | `r` | `icon r` |
| `stats` | `st` | `icon st` |
| `validate` | `v` | `icon v` |
| `list` | `l` | `icon l security` |

---

## Real-World Examples

### Example 1: Adding Security Section to README

```bash
# What icons should I use for security?
iconics suggest security
# → lock, shield, key, protection, certificate

# Export them and get markdown
iconics use lock shield
```

**Paste into README.md:**
```markdown
## ![lock](.github/assets/icons/lock.png) Security Features

### ![shield](.github/assets/icons/shield.png) Encrypted Communication
All data transmitted using TLS 1.3...
```

### Example 2: API Documentation

```bash
# Get appropriate icons
iconics suggest api
# → network, cloud, globe, server, database

# Export what I need
iconics use network database cloud
```

**Paste into docs/api.md:**
```markdown
## ![network](.github/assets/icons/network.png) API Endpoints

### ![database](.github/assets/icons/database.png) Data Access
RESTful API providing access to...

### ![cloud](.github/assets/icons/cloud.png) Cloud Integration
Seamless cloud storage support...
```

### Example 3: Quick Error Documentation

```bash
# Need error and warning icons
iconics use error warning info

# Copy the generated markdown and paste into docs
```

---

## Tips & Tricks

### 1. Combine Search + Use

```bash
# Find security icons
iconics search security

# Pick the ones you want
iconics use lock shield certificate
```

### 2. Preview Before Using

```bash
# See details about an icon
iconics info lock

# Check file status, tags, description
# Then export if it's what you need
iconics use lock
```

### 3. Explore by Category

```bash
# See what's available in a category
icon list security

# Export the whole category if needed
iconics cat security
```

### 4. Track Recent Additions

```bash
# See what's new in the library
iconics recent

# Export the latest icons
iconics use arrow-up arrow-down arrow-left arrow-right
```

---

## For AI Assistants (Claude)

This tool is designed for quick, emoji-free icon usage:

### Typical Workflow:
1. **Suggest**: `iconics suggest <context>` to recommend appropriate icons
2. **Export + Markdown**: `iconics use <names>` to export and generate ready-to-paste markdown
3. **Use in response**: Include the generated markdown in documentation

### Example:
```
User: "Add security documentation to the README"

Assistant Response:
"I'll add a security section to your README with appropriate icons."

[Runs: iconics suggest security]
[Runs: iconics use lock shield]

Then includes in README.md:
## ![lock](.github/assets/icons/lock.png) Security Features

### ![shield](.github/assets/icons/shield.png) Encrypted Data
...
```

### Benefits Over Emojis:
- **Professional appearance** with semantic icons
- **Consistent styling** across all projects
- **Meaningful visuals** that match the content
- **Reusable assets** tracked in git
- **No emoji rendering issues** across platforms

---

## Troubleshooting

### Command not found: icon

Make sure `~/.local/bin` is in your PATH:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Add this line to `~/.bashrc` or `~/.zshrc` to make it permanent.

### Icons not showing in GitHub

Verify the icon files exist:
```bash
ls -la .github/assets/icons/
```

Check markdown paths match file locations.

### Need to update icon library

```bash
cd /home/zack/dev/iconics
git pull origin master
```

---

## Advanced Usage

### Export to Specific Directory

```bash
# Export to current directory instead of project root
icon here warning error info

# Export to arbitrary path
cd /path/to/project
iconics use lock shield
```

### Generate CSV for Bulk Import

```bash
# Auto-generate CSV from uncataloged icons
cd /home/zack/dev/iconics
python3 icon-manager.py generate-csv batch.csv --limit 100

# Edit batch.csv in spreadsheet software

# Import the batch
python3 icon-manager.py import-csv batch.csv
```

### Validate Icon Library

```bash
# Check for missing files or broken symlinks
icon validate
```

---

## Getting Help

```bash
# Show all commands
iconics --help

# Full manager options
python3 /home/zack/dev/iconics/icon-manager.py --help
```

---

**Iconics** - Professional icons, instantly accessible everywhere 🚀