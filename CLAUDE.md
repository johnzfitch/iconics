# Iconics - Guide for Claude Agents

**Purpose:** Use professional, semantic icons instead of emojis in all projects.

---

## What Is This?

Iconics is a globally-accessible icon library with 1,200+ PNG icons designed to replace emojis in documentation, GitHub READMEs, and technical writing. The system provides:

- **Global `icon` command** - Works from anywhere
- **Smart project detection** - Auto-finds project root
- **Instant markdown generation** - Ready to paste
- **Context-aware suggestions** - Recommends appropriate icons

**Location:** `/home/zack/dev/iconics`

**Status:** 128 icons cataloged (10.5%), 1,087 more available

---

## Why Use Iconics?

### Replace This (Emojis):
```markdown
## 🔒 Security Features
### 🛡️ Encryption
### 🔑 Authentication
```

### With This (Professional Icons):
```markdown
## ![lock](.github/assets/icons/lock.png) Security Features
### ![shield](.github/assets/icons/shield.png) Encryption
### ![key](.github/assets/icons/key.png) Authentication
```

**Benefits:**
- Professional appearance
- Semantic meaning (lock = security, not just a visual)
- Consistent across platforms
- Git-tracked assets
- No emoji rendering issues

---

## The Standard Workflow

### 1. User Asks for Documentation/Features

**User:** "Add security documentation to the README"

### 2. Get Icon Suggestions

```bash
icon suggest security
```

**Output:**
```
Icon suggestions for 'security':
  lock, shield, key, protection, certificate
```

### 3. Export Icons + Generate Markdown

```bash
icon use lock shield
```

**Output:**
```
Exporting to: /home/zack/dev/project
✓ Exported lock.png
✓ Exported shield.png

Markdown snippets:
  ![lock](.github/assets/icons/lock.png)
  ![shield](.github/assets/icons/shield.png)
```

### 4. Use the Generated Markdown

Copy the markdown snippets directly into your response:

```markdown
## ![lock](.github/assets/icons/lock.png) Security Features

This project implements several security measures:

### ![shield](.github/assets/icons/shield.png) TLS Encryption
All network traffic is encrypted using TLS 1.3...
```

---

## Built-In Context Suggestions

Use `icon suggest <context>` for these common scenarios:

| Context | Suggested Icons |
|---------|-----------------|
| `authentication` / `auth` / `login` | lock, key, shield, certificate, login |
| `security` / `secure` | shield, lock, key, protection, certificate |
| `network` / `api` / `server` | network, cloud, globe, wifi, connect |
| `data` / `database` / `storage` | database, folder, save-file, cloud, documents |
| `error` / `warning` / `alert` | warning, error, alert, caution, danger |
| `success` / `complete` / `done` | checkbox, checkmark, success, done |
| `info` / `information` / `help` | info, help, question, about |
| `settings` / `config` / `options` | settings, options, control-panel, toolbox |
| `navigation` / `menu` / `ui` | home, menu, arrows, close |
| `files` / `documents` / `docs` | folder, document, pdf, file |
| `code` / `development` / `programming` | console, script, database, terminal |
| `search` / `find` / `lookup` | search, find, magnifying-glass, lookup |
| `user` / `account` / `profile` | login, logout, user, account, profile |

---

## Quick Command Reference

### Most Used Commands

```bash
# Get suggestions for a context
icon suggest authentication

# Export icons and get markdown (most common)
icon use lock shield key

# Just generate markdown (icons already exported)
icon md database network

# Search for icons by keyword
icon search security

# Show icon details
icon i lock

# Export entire category
icon cat security
```

### Shortcuts

All commands have short aliases:
- `icon s <query>` → search
- `icon u <names>` → use (export + markdown)
- `icon sug <context>` → suggest
- `icon md <names>` → markdown only
- `icon i <name>` → info
- `icon r` → recent
- `icon cat <category>` → export category

---

## When to Use Iconics

### ✅ Use Icons For:

1. **Section Headers in READMEs**
   ```markdown
   ## ![network](.github/assets/icons/network.png) API Architecture
   ```

2. **Feature Documentation**
   ```markdown
   ### ![shield](.github/assets/icons/shield.png) Security
   ### ![database](.github/assets/icons/database.png) Data Storage
   ```

3. **Technical Guides**
   ```markdown
   ## ![warning](.github/assets/icons/warning.png) Important Security Notice
   ```

4. **Project Organization**
   ```markdown
   - ![folder](.github/assets/icons/folder.png) **Documentation**: See docs/
   - ![code](.github/assets/icons/console.png) **Development**: See CONTRIBUTING.md
   ```

### ❌ Don't Overuse:

- **Not every line** - Use for headers and key points, not inline text
- **Not in code** - Only in markdown/documentation
- **Not when unnecessary** - If the text is already clear, skip the icon
- **Not for decorative purposes** - Each icon should add semantic meaning

---

## Example Workflows

### Example 1: Adding API Documentation

**User Request:** "Document the API endpoints"

**Your Actions:**
```bash
icon suggest api
# → network, cloud, globe, server, database

icon use network database
```

**Your Response:**
```markdown
## ![network](.github/assets/icons/network.png) API Documentation

### ![database](.github/assets/icons/database.png) Data Endpoints

GET /api/v1/data
...
```

### Example 2: Security Features

**User Request:** "Add security section to README"

**Your Actions:**
```bash
icon suggest security
# → lock, shield, key, protection, certificate

icon use lock shield key
```

**Your Response:**
```markdown
## ![lock](.github/assets/icons/lock.png) Security

### ![shield](.github/assets/icons/shield.png) Encrypted Communication
All traffic uses TLS 1.3...

### ![key](.github/assets/icons/key.png) Authentication
JWT-based authentication with...
```

### Example 3: Project Setup Instructions

**User Request:** "Create installation documentation"

**Your Actions:**
```bash
icon suggest settings
# → settings, options, control-panel, toolbox

icon use toolbox settings
```

**Your Response:**
```markdown
## ![toolbox](.github/assets/icons/toolbox.png) Installation

### ![settings](.github/assets/icons/settings.png) Configuration

1. Clone the repository
2. Install dependencies
...
```

---

## Best Practices

### 1. Be Proactive

When creating or modifying documentation, automatically use icons without waiting for the user to ask.

**Good:**
```
User: "Add a security section"
Assistant: [Runs: icon suggest security]
Assistant: [Runs: icon use lock shield]
Assistant: "I've added a security section with professional icons."
```

### 2. Choose Semantic Icons

Pick icons that match the **meaning** of the content, not just the visual:
- **Security** → lock, shield, key (not padlock emoji)
- **Network** → network, cloud, globe (not wifi emoji)
- **Error** → warning, error (not ⚠️)

### 3. Consistent Usage

Within a project, use consistent icon styles:
- Use icons for all major sections, or none
- Don't mix emojis and icons
- Keep icon density consistent (e.g., one per h2 header)

### 4. Generate Markdown Immediately

Always run `icon use` to get ready-to-paste markdown. Don't manually type paths:

**Bad:**
```markdown
![lock](path/to/icon.png)  # Manual, error-prone
```

**Good:**
```bash
icon use lock
# Copy the generated: ![lock](.github/assets/icons/lock.png)
```

### 5. Verify Icon Availability

If a suggested icon isn't cataloged, search or suggest alternatives:

```bash
icon search authentication
# Shows all authentication-related icons
```

---

## Troubleshooting

### Icon Not Found

```bash
# Search for alternatives
icon search <keyword>

# Check what's available
icon recent
icon stats
```

### Need Icon Information

```bash
# Get details about an icon
icon i <name>

# Shows: tags, description, file status, projects using it
```

### Wrong Project Detected

The `icon use` command auto-detects project root via:
1. Git root (`git rev-parse --show-toplevel`)
2. Nearest README.md
3. Current directory

If wrong, manually specify:
```bash
cd /path/to/correct/project
icon use lock shield
```

---

## Categories Available

Browse by category:

- **security** (11 icons) - lock, shield, key, certificate, keychain, protection, unlock, open-lock, eye, hide, show
- **ui** (66 icons) - info, warning, arrows, buttons, controls, home, menu, close, delete, checkbox
- **files** (17 icons) - folder, document, pdf, photo, video, archive, new-document, open-file, save-file
- **network** (8 icons) - network, cloud, globe, wifi, network-radar, global-network, connect, disconnect
- **development** (11 icons) - database, console, application, script, plugin, error, login, logout, update
- **tools** (12 icons) - search, toolbox, settings, options, control-panel, print, export, import, battery, power
- **emoji** (3 icons) - happy, sad, smile

Export entire categories:
```bash
icon cat security
# Exports all 11 security icons
```

---

## Advanced Features

### Batch Operations

Export multiple icons at once:
```bash
icon use lock shield key certificate database network
```

### Markdown Only (No Export)

If icons already exist in project:
```bash
icon md lock shield
# Just generates markdown, no export
```

### Show Recent Additions

See what's newly cataloged:
```bash
icon recent 10
# Shows last 10 added icons
```

### Explore Icons

```bash
# Search by keyword
icon search <keyword>

# List category contents
icon list security

# Show library statistics
icon stats
```

---

## Integration Examples

### In README.md Updates

**Before:**
```markdown
## Features
- Security
- API Access
- Data Storage
```

**After:**
```markdown
## Features
- ![lock](.github/assets/icons/lock.png) **Security**: End-to-end encryption
- ![network](.github/assets/icons/network.png) **API Access**: RESTful API
- ![database](.github/assets/icons/database.png) **Data Storage**: PostgreSQL database
```

### In Documentation Files

```markdown
# Project Documentation

## ![info](.github/assets/icons/info.png) Overview
...

## ![toolbox](.github/assets/icons/toolbox.png) Installation
...

## ![settings](.github/assets/icons/settings.png) Configuration
...
```

---

## Performance Notes

- All commands run in **< 1 second**
- No network requests required
- Works offline
- Zero dependencies (Python 3 standard library only)

---

## Remember

1. **Always prefer icons over emojis** in professional documentation
2. **Use `icon suggest` first** to get appropriate recommendations
3. **Run `icon use`** to export and generate markdown in one command
4. **Copy-paste the generated markdown** - don't type paths manually
5. **Be proactive** - add icons when creating/updating docs without being asked

---

## Quick Start Summary

```bash
# 1. Get suggestions
icon suggest <context>

# 2. Export and get markdown
icon use <icon1> <icon2> <icon3>

# 3. Paste the generated markdown into documentation

# That's it!
```

---

## Files and Locations

- **Icon Library:** `/home/zack/dev/iconics/`
- **Command:** `icon` (globally accessible)
- **Raw Icons:** `/home/zack/dev/iconics/raw/` (1,215 PNG files)
- **Catalog:** `/home/zack/dev/iconics/icon-catalog.json` (128 cataloged)
- **Installation:** `/home/zack/dev/iconics/install.sh`

---

## For Future Development

If the user asks to catalog more icons:

```bash
# Auto-generate suggestions from uncataloged icons
cd /home/zack/dev/iconics
python3 icon-manager.py generate-csv batch.csv --limit 100

# Review and edit the CSV, then import
python3 icon-manager.py import-csv batch.csv
```

See the main README.md for full cataloging workflows.

---

**Remember:** Iconics exists to replace emojis with professional, semantic icons. Use it proactively in all documentation work.

---

**Last Updated:** 2025-10-28
**Version:** 2.0 (Global CLI Access)
**Cataloged Icons:** 128/1,215 (10.5%)
