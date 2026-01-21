# Iconics

**A semantic icon library with intelligent tagging and discovery**

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Icons](https://img.shields.io/badge/icons-8203-brightgreen.svg)
![Cataloged](https://img.shields.io/badge/cataloged-8203-brightgreen.svg)
![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen.svg)

**![book](.github/assets/icons/book.png) [Quick Start](QUICK_START.md) | ![script](.github/assets/icons/script.png) [For AI Assistants](CLAUDE.md)**

---

## Overview

Iconics is a globally-accessible, semantically-tagged icon library designed for instant use across all projects. Use professional icons instead of emojis everywhere - GitHub, documentation, websites, and more.

### Key Features

- **Global CLI Access:** `iconics use lock shield` from anywhere, instantly
- **Smart Project Detection:** Auto-detects project root and exports to correct location
- **Ready-to-Paste Markdown:** Generates markdown snippets automatically
- **Context-Aware Suggestions:** `iconics suggest authentication` recommends appropriate icons
- **Semantic Search:** Find icons by meaning, not filename
- **8,203 Icons - Fully Cataloged:** All icons tagged, categorized, and ready to use
- **No More Emojis:** Professional, semantic icons for all your projects

---

## Quick Start

### No Installation Required!

Use the iconics command directly:

```bash
~/dev/iconics/iconics.py search security
~/dev/iconics/iconics.py use lock shield
```

**Recommended:** Add an alias for convenience:
```bash
alias iconics='~/dev/iconics/iconics.py'
```

See [SETUP.md](SETUP.md) for shell completion and other optional features.

### 1. Find Icons

```bash
iconics search security
# or get suggestions
iconics suggest authentication
```

### 2. Use Instantly (Exports + Generates Markdown)

```bash
iconics use lock shield
```

**Output:**
```
Exporting to: ~/your-project
✓ Exported lock.png
✓ Exported shield.png

Markdown snippets:
  ![lock](.github/assets/icons/lock.png)
  ![shield](.github/assets/icons/shield.png)
```

**Copy and paste the markdown directly into your README!**

### 3. That's It!

```markdown
## ![lock](.github/assets/icons/lock.png) Security Features

### ![shield](.github/assets/icons/shield.png) Encrypted Communication
Your content here...
```

**See [QUICK_START.md](QUICK_START.md) for the complete guide.**

---

## Alternative: Python Manager

You can also use the Python manager directly for advanced operations:

```bash
cd ~/dev/iconics
python3 icon-manager.py search security
python3 icon-manager.py export ~/dev/my-project lock shield
```

---

## Library Stats

- **Total Icons:** 8,203 PNG files
- **Cataloged:** 8,203 icons (100% coverage) ![tick](.github/assets/icons/tick.png) **COMPLETE!**
- **Categories:** 7 (files, network, security, tools, ui, emoji, development)
- **CLIP Embeddings:** 8,202 icons with 512-dimensional semantic vectors
- **Projects Using:** 17 projects tracked via usage analytics

### Category Breakdown
- **UI Elements:** 6,489 icons (arrows, buttons, controls, indicators, media, numbers, sizes)
- **Files:** 683 icons (documents, folders, blueprints, file types, bookmarks, archives)
- **Emoji:** 279 icons (expressions, symbols, yin-yang, faces, characters)
- **Network:** 223 icons (wifi, cloud, globe, connections, streaming, browsers)
- **Security:** 239 icons (locks, keys, shields, certificates, safes, protection)
- **Tools:** 205 icons (hardware, utilities, design tools, devices, instruments)
- **Development:** 85 icons (console, database, code, terminal, apps, scripts)

---

## Directory Structure

```
iconics/
├── raw/                           # Original icon files
├── catalog/                       # Organized by category (symlinks)
│   ├── files/                     # folder.png
│   ├── network/                   # network.png
│   ├── security/                  # lock.png, shield.png
│   ├── tools/                     # search.png, toolbox.png
│   ├── ui/                        # info.png, warning.png
│   ├── emoji/                     # (to be populated)
│   └── development/               # database.png
├── iconics.sqlite3                # SQLite catalog database (default runtime source of truth)
├── icon-catalog.json              # Legacy input for migration (still useful for audits)
├── icon-manager.py                # CLI management tool
└── README.md                      # This file
```

---

## Global CLI Commands

The `iconics` command provides instant access from anywhere. All commands work from any directory and auto-detect your project.

### Quick Commands

```bash
iconics search <query>              # Semantic search via CLIP embeddings
iconics use <name> [name2...]       # Export + generate markdown
iconics suggest <context>           # Get context-aware suggestions
iconics info <name>                 # Show icon information
iconics query <text>                # Direct CLIP embedding query
iconics recent [N]                  # Show recent additions
iconics tui                         # Launch interactive terminal UI (TUI2, SQLite-backed)
iconics db migrate                  # Build/refresh iconics.sqlite3 from icon-catalog.json
iconics db verify                   # Verify embeddings + catalog sync
```

**Example Workflow:**
```bash
iconics suggest security
# → lock, key, shield, certificate, login

iconics use lock shield
# → Exports icons and generates ready-to-paste markdown
```

**Full command reference:** `iconics --help` or see [QUICK_START.md](QUICK_START.md)

---

## Python Manager Commands

You can also use the Python manager directly for advanced operations:

### Search

Find icons by tag or semantic name:

```bash
python3 icon-manager.py search <query>
```

**Examples:**
```bash
python3 icon-manager.py search security    # Find all security icons
python3 icon-manager.py search lock        # Find lock-related icons
python3 icon-manager.py search network     # Find network icons
```

### List Category

Show all icons in a specific category:

```bash
python3 icon-manager.py list <category>
```

**Categories:** files, network, security, tools, ui, emoji, development

**Example:**
```bash
python3 icon-manager.py list security
```

### Export to Project

Copy icons to a project with semantic names:

```bash
python3 icon-manager.py export <project-path> <icon1> <icon2> ...
```

**Example:**
```bash
python3 icon-manager.py export ~/dev/my-app lock shield database network
```

Icons are exported to: `<project>/.github/assets/icons/`

### Add Icon to Catalog

Catalog a new icon with metadata:

```bash
python3 icon-manager.py add <icon-id> <semantic-name> \
  --tags <tag1> <tag2> ... \
  --category <category> \
  --description "Description"
```

**Example:**
```bash
python3 icon-manager.py add "Key" "key" \
  --tags security key access password \
  --category security \
  --description "Key icon for authentication"
```

### Bulk Import from CSV

Import multiple icons at once from a CSV file:

```bash
python3 icon-manager.py import-csv icons-to-import.csv
```

**CSV Format:**
```csv
id,semantic,tags,category,description
Phone,phone,"telephone,call,mobile,contact",ui,Phone icon for calls
Printer,printer,"print,document,office",tools,Printer icon
Calculator,calculator,"math,numbers,compute",tools,Calculator icon
```

**Benefits:**
- **3-4x faster** than individual commands
- Easy to prepare in spreadsheet software (Excel, Google Sheets)
- Batch review before import
- Automatic duplicate detection

**Template:** See `icon-import-template.csv` for a ready-to-use template

### Auto-Generate CSV from Filenames

Let the tool suggest names and tags based on icon filenames:

```bash
python3 icon-manager.py generate-csv suggested-icons.csv --limit 50
```

**What it does:**
- Scans uncataloged icons in `raw/` directory
- Parses filenames to suggest semantic names
- Auto-generates tags from filename words
- Guesses categories based on keywords
- Creates ready-to-edit CSV file

**Benefits:**
- **10x faster** than manual tagging from scratch
- Smart suggestions from descriptive filenames
- Batch review and edit in spreadsheet
- Skip icons with numeric/unclear names

**Workflow:**
```bash
# 1. Generate suggestions for 100 icons
python3 icon-manager.py generate-csv batch1.csv --limit 100

# 2. Edit batch1.csv in Excel/Google Sheets
#    - Review suggestions
#    - Improve tags
#    - Fix categories

# 3. Import the reviewed batch
python3 icon-manager.py import-csv batch1.csv
```

### Template System (Icon Families)

Create reusable templates for icon families to save time:

**Create a template:**
```bash
python3 icon-manager.py create-template arrow \
  --tags navigation direction pointer movement \
  --category ui
```

**Apply template to multiple icons:**
```csv
# arrow-icons.csv
id,semantic,extra_tags,description
Up,arrow-up,upward vertical,Upward arrow
Down,arrow-down,downward vertical,Downward arrow
Left,arrow-left,leftward horizontal,Left arrow
Right,arrow-right,rightward horizontal,Right arrow
```

```bash
python3 icon-manager.py apply-template arrow arrow-icons.csv
```

**Benefits:**
- Define common tags once for icon families
- Apply consistently across all variants
- Add variant-specific tags as needed
- Perfect for: arrows, social media icons, file types, status indicators

**Example templates:**
- **arrow:** navigation, direction, pointer
- **social:** social-media, sharing, platform
- **file-type:** file, document, format
- **status:** indicator, state, condition

### View Statistics

Show enhanced library statistics with category breakdowns:

```bash
python3 icon-manager.py stats
```

**Shows:**
- Total library coverage (cataloged vs uncataloged)
- Detailed breakdown by category with samples
- Most used icons across projects
- Project usage summary

### Validate Catalog

Check catalog integrity for issues:

```bash
python3 icon-manager.py validate
```

**Checks:**
- Missing source files in `raw/` directory
- Broken symlinks in `catalog/` directories
- Orphaned symlinks pointing to non-existent files
- Directory structure integrity

### Icon Information

Show detailed information about a specific icon:

```bash
python3 icon-manager.py info <semantic-name>
```

**Example:**
```bash
python3 icon-manager.py info lock
```

**Output includes:**
- Semantic name and icon ID
- Filename and file paths
- Category and description
- All tags
- Projects using this icon
- File existence status

### Recent Icons

View recently cataloged icons:

```bash
python3 icon-manager.py recent --limit <N>
```

**Examples:**
```bash
python3 icon-manager.py recent           # Show last 20 icons
python3 icon-manager.py recent --limit 50  # Show last 50 icons
```

### Export Category

Export all icons from a specific category at once:

```bash
python3 icon-manager.py export-category <project-path> <category>
```

**Example:**
```bash
python3 icon-manager.py export-category ~/dev/my-app security
```

**Benefits:**
- Export entire category in one command
- Perfect for themed projects (security docs, UI kits, etc.)
- Faster than individual exports for multiple icons

---

## Currently Cataloged Icons

| Preview | Name | Category | Tags |
|---------|------|----------|------|
| ![lock](catalog/security/lock.png) | lock | security | security, padlock, locked |
| ![shield](catalog/security/shield.png) | shield | security | security, shield, protection, guard |
| ![info](catalog/ui/info.png) | info | ui | information, help, question, about |
| ![warning](catalog/ui/warning.png) | warning | ui | warning, alert, caution, danger, exclamation |
| ![network](catalog/network/network.png) | network | network | network, connection, tower, wifi, ethernet |
| ![folder](catalog/files/folder.png) | folder | files | folder, directory, files, organize |
| ![database](catalog/development/database.png) | database | development | database, data, storage, server, api |
| ![search](catalog/tools/search.png) | search | tools | search, find, magnifying-glass, lookup |
| ![toolbox](catalog/tools/toolbox.png) | toolbox | tools | tools, toolbox, utilities, settings |

---

## Integration with Projects

### 1. Find Icons

```bash
cd /path/to/iconics
python3 icon-manager.py search <keyword>
```

### 2. Export Icons

```bash
python3 icon-manager.py export ~/dev/your-project icon1 icon2 icon3
```

### 3. Use in README

```markdown
# Your Project

## ![Shield](.github/assets/icons/shield.png) Security

Security features documented here...

## ![Network](.github/assets/icons/network.png) Architecture

Network architecture details...
```

---

## Categories

### files
Documents, folders, archives, file types

### network
Connections, wifi, ethernet, cloud, servers

### security
Locks, shields, keys, authentication, encryption

### tools
Wrenches, gears, settings, utilities, maintenance

### ui
Interface elements, buttons, indicators, controls

### emoji
Faces, emotions, reactions, expressions

### development
Code, databases, APIs, debugging, testing

---

## Tagging Best Practices

### Good Tags ![tick](.github/assets/icons/tick.png)
- **Descriptive:** lock, security, padlock
- **Action-based:** search, find, lookup
- **Context:** authentication, password, access
- **Synonyms:** folder, directory, files

### Avoid ![error](.github/assets/icons/error.png)
- Too generic: icon, image, graphic
- Too specific: "blue lock with gold keyhole"
- Duplicates: lock, locking, locked (choose one primary)

---

## Projects Using Iconics

### eero-reverse-engineering
Network security research project

**Icons Used:**
- info, network, shield, database, folder, toolbox, search, lock, warning

**Integration:** Professional README with subtle icon accents for section headers

[View Project →](https://github.com/johnzfitch/eero-reverse-engineering)

---

## Roadmap

### Phase 1 ![tick](.github/assets/icons/tick.png) (Complete)
- ![tick](.github/assets/icons/tick.png) Basic CLI tool
- ![tick](.github/assets/icons/tick.png) JSON catalog system
- ![tick](.github/assets/icons/tick.png) Search functionality
- ![tick](.github/assets/icons/tick.png) Export to projects
- ![tick](.github/assets/icons/tick.png) Initial 9 icons cataloged

### Phase 2 ![tick](.github/assets/icons/tick.png) (Complete)
- ![tick](.github/assets/icons/tick.png) Bulk CSV import (3-4x faster)
- ![tick](.github/assets/icons/tick.png) Auto-generate CSV from filenames (10x faster)
- ![tick](.github/assets/icons/tick.png) Template system for icon families
- ![tick](.github/assets/icons/tick.png) Expand catalog to 1,215 icons (100% complete)
- ![tick](.github/assets/icons/tick.png) Enhanced statistics with category breakdowns
- ![tick](.github/assets/icons/tick.png) Catalog validation and integrity checking
- ![tick](.github/assets/icons/tick.png) Detailed icon information command
- ![tick](.github/assets/icons/tick.png) Recent icons tracking
- ![tick](.github/assets/icons/tick.png) Batch export by category
- ![tick](.github/assets/icons/tick.png) **Global CLI access system**
- ![tick](.github/assets/icons/tick.png) **Smart project detection**
- ![tick](.github/assets/icons/tick.png) **Auto-generated markdown snippets**
- ![tick](.github/assets/icons/tick.png) **Context-aware icon suggestions**
- ![tick](.github/assets/icons/tick.png) **One-command export and use**

### Phase 3 (Future)
- [ ] Web interface for visual browsing
- [ ] Thumbnail generation
- [ ] Auto-detection of similar icons
- [ ] SVG support
- [ ] Multiple sizes (16x16, 24x24, 32x32, 48x48)
- [ ] Icon variations (color schemes, outlined vs filled)
- [ ] Git hooks integration
- [ ] Package manager (pip install iconics)

---

## Contributing

### Adding Icons to Catalog

1. Visual browse icons in `raw/` directory
2. Catalog with semantic metadata:

```bash
python3 icon-manager.py add "Filename" "semantic-name" \
  --tags relevant tags here \
  --category appropriate-category \
  --description "Clear description"
```

### Improving Existing Entries

- Add missing tags
- Update descriptions for clarity
- Fix incorrect categorizations
- Report issues or suggest improvements

---

## Technical Details

### Requirements
- Python 3.6+
- Standard library only (no external dependencies)

### Icon Format
- Format: PNG
- Size: Primarily 16x16 (some larger variants available)
- Vintage: 2009-2011 era icon packs

### Storage Efficiency
- Original files stored once in `raw/`
- Symlinks in `catalog/` for zero-duplicate storage
- Catalog metadata ~1KB per icon

---

## License

MIT License - see LICENSE file for details

Icons sourced from various free icon packs (2009-2011).
Suitable for personal and open-source projects.

---

## Quick Reference Card

| Command | Purpose |
|---------|---------|
| `search <query>` | Find icons by tag/name |
| `list <category>` | Show category contents |
| `export <path> <icons...>` | Copy icons to project |
| `export-category <path> <category>` | Export all icons from a category |
| `add <id> <name> --tags... --category...` | Catalog new icon |
| `import-csv <file>` | Bulk import from CSV (3-4x faster) |
| `generate-csv <output> --limit N` | Auto-generate CSV from filenames (10x faster) |
| `create-template <name> --tags... --category` | Create reusable template |
| `apply-template <name> <csv>` | Apply template to icon family |
| `stats` | Show enhanced library statistics |
| `validate` | Check catalog integrity |
| `info <semantic-name>` | Show detailed icon information |
| `recent --limit N` | Show recently cataloged icons |

---

## Links

- **Setup Guide:** [SETUP.md](SETUP.md) - Installation, aliases, shell completion
- **Quick Start Guide:** [QUICK_START.md](QUICK_START.md) - Fast workflows and examples
- **For AI Assistants:** [CLAUDE.md](CLAUDE.md) - Complete guide for Claude agents
- **Repository:** https://github.com/johnzfitch/iconics
- **Issues:** https://github.com/johnzfitch/iconics/issues
- **Example Usage:** [eero-reverse-engineering](https://github.com/johnzfitch/eero-reverse-engineering)

---

**Iconics** - *Finding the right icon should be easy*

---

**Version:** 1.0.0
**Last Updated:** 2025-10-28
**Maintainer:** Zack
