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
icon search authentication

# Use them instantly (exports + generates markdown)
icon use lock key
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
icon suggest authentication
# Suggests: lock, key, shield, certificate, login

icon suggest network
# Suggests: network, cloud, globe, wifi, connect, server

icon suggest error
# Suggests: warning, error, alert, caution, danger
```

---

### 3. Just Get Markdown (no export)

Already have icons exported? Just get the markdown:

```bash
icon md shield database network
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
icon suggest security

# Export relevant icons
icon use lock shield key certificate

# Paste the generated markdown into README.md
```

### Adding Icons to Existing Documentation

```bash
# Search for what you need
icon search data

# Export and get markdown instantly
icon use database folder documents
```

### Export All Icons from a Category

```bash
# Export entire security category
icon cat security

# Or UI category
icon cat ui
```

---

## Quick Command Reference

| Command | What It Does | Example |
|---------|--------------|---------|
| `icon search <query>` | Find icons by keyword | `icon search security` |
| `icon use <name>...` | Export + generate markdown | `icon use lock shield` |
| `icon suggest <context>` | Get icon suggestions | `icon suggest api` |
| `icon md <name>...` | Generate markdown only | `icon md network` |
| `icon cat <category>` | Export whole category | `icon cat security` |
| `icon i <name>` | Show icon details | `icon i lock` |
| `icon recent` | Show recently added | `icon recent` |
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

The `icon use` command automatically detects your project root:
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
icon use warning error info success
icon md lock key shield certificate
icon i lock key shield
```

---

## Shortcuts

All commands have short aliases:

| Full | Short | Example |
|------|-------|---------|
| `search` | `s` | `icon s security` |
| `use` | `u` | `icon u lock` |
| `suggest` | `sug` | `icon sug auth` |
| `markdown` | `md` | `icon md lock` |
| `here` | `h` | `icon h warning` |
| `category` | `cat` | `icon cat ui` |
| `info` | `i` | `icon i lock` |
| `recent` | `r` | `icon r` |
| `stats` | `st` | `icon st` |
| `validate` | `v` | `icon v` |
| `list` | `l` | `icon l security` |

---

## Real-World Examples

### Example 1: Adding Security Section to README

```bash
# What icons should I use for security?
icon suggest security
# → lock, shield, key, protection, certificate

# Export them and get markdown
icon use lock shield
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
icon suggest api
# → network, cloud, globe, server, database

# Export what I need
icon use network database cloud
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
icon use error warning info

# Copy the generated markdown and paste into docs
```

---

## Tips & Tricks

### 1. Combine Search + Use

```bash
# Find security icons
icon search security

# Pick the ones you want
icon use lock shield certificate
```

### 2. Preview Before Using

```bash
# See details about an icon
icon i lock

# Check file status, tags, description
# Then export if it's what you need
icon use lock
```

### 3. Explore by Category

```bash
# See what's available in a category
icon list security

# Export the whole category if needed
icon cat security
```

### 4. Track Recent Additions

```bash
# See what's new in the library
icon recent

# Export the latest icons
icon use arrow-up arrow-down arrow-left arrow-right
```

---

## For AI Assistants (Claude)

This tool is designed for quick, emoji-free icon usage:

### Typical Workflow:
1. **Suggest**: `icon suggest <context>` to recommend appropriate icons
2. **Export + Markdown**: `icon use <names>` to export and generate ready-to-paste markdown
3. **Use in response**: Include the generated markdown in documentation

### Example:
```
User: "Add security documentation to the README"

Assistant Response:
"I'll add a security section to your README with appropriate icons."

[Runs: icon suggest security]
[Runs: icon use lock shield]

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
icon use lock shield
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
icon help

# Full manager options
python3 /home/zack/dev/iconics/icon-manager.py --help
```

---

**Iconics** - Professional icons, instantly accessible everywhere 🚀