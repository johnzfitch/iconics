# Iconics

**A semantic icon library with intelligent tagging and discovery**

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Icons](https://img.shields.io/badge/icons-3369-brightgreen.svg)
![Cataloged](https://img.shields.io/badge/cataloged-3372-brightgreen.svg)
![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen.svg)

![book](catalog/files/book.png) [Quick Start](QUICK_START.md) | ![script](catalog/development/script.png) [For AI Assistants](CLAUDE.md)

---

## ![info](catalog/ui/info.png) Overview

Iconics is a globally-accessible, semantically-tagged icon library designed for instant use across all projects. Use professional icons instead of emojis everywhere - GitHub, documentation, websites, and more.

### ![star](catalog/ui/star.png) Key Features

- ![globe](catalog/network/globe.png) **Global CLI Access:** `icon use lock shield` from anywhere, instantly
- ![target](catalog/ui/target.png) **Smart Project Detection:** Auto-detects project root and exports to correct location
- ![document](catalog/files/document.png) **Ready-to-Paste Markdown:** Generates markdown snippets automatically
- ![lightbulb](catalog/ui/lightbulb.png) **Context-Aware Suggestions:** `icon suggest authentication` recommends appropriate icons
- ![search](catalog/tools/search.png) **Semantic Search:** Find icons by meaning, not filename
- ![folder](catalog/files/folder.png) **3,369 Icons - Fully Cataloged:** All icons tagged, categorized, and ready to use (including all sizes from ICO/GIF conversions)
- ![badge-cancel](catalog/ui/badge-cancel.png) **No More Emojis:** Professional, semantic icons for all your projects

---

## ![rocket](catalog/ui/rocket.png) Quick Start

### ![tick](catalog/ui/tick.png) No Installation Required!

Use the icon command directly:

```bash
~/iconics/icon search security
~/iconics/icon use lock shield
```

**Recommended:** Add an alias for convenience:
```bash
alias icon='~/iconics/icon'
```

See [SETUP.md](SETUP.md) for shell completion and other optional features.

### ![search](catalog/tools/search.png) 1. Find Icons

```bash
icon search security
# or get suggestions
icon suggest authentication
```

### ![play](catalog/ui/play.png) 2. Use Instantly (Exports + Generates Markdown)

```bash
icon use lock shield
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

### ![accept](catalog/ui/accept.png) 3. That's It!

```markdown
## ![lock](.github/assets/icons/lock.png) Security Features

### ![shield](.github/assets/icons/shield.png) Encrypted Communication
Your content here...
```

**See [QUICK_START.md](QUICK_START.md) for the complete guide.**

---

## ![console](catalog/development/console.png) Classic Usage (Python Manager)

You can also use the Python manager directly:

```bash
cd ~/iconics
python3 icon-manager.py search security
python3 icon-manager.py export ~/dev/my-project lock shield
```

---

## ![statistics](catalog/ui/statistics.png) Library Stats

- ![folder](catalog/files/folder.png) **Total Icons:** 3,369 PNG files
- ![tick](catalog/ui/tick.png) **Cataloged:** 3,372 icons (100% coverage) - **COMPLETE!**
- ![tag](catalog/ui/tag.png) **Categories:** 7 (files, network, security, tools, ui, emoji, development)
- ![briefcase](catalog/files/briefcase.png) **Projects Using:** Multiple (tracked via usage analytics)
- ![save](catalog/ui/save.png) **Archives:** ICO (6.3MB) and GIF (575KB) originals preserved in archives

### ![hierarchy](catalog/ui/hierarchy.png) Category Breakdown

- ![control-panel](catalog/tools/control-panel.png) **UI Elements:** 2,969 icons (arrows, buttons, controls, indicators, media, numbers, sizes)
- ![document](catalog/files/document.png) **Files:** 179 icons (documents, folders, blueprints, file types, bookmarks, archives)
- ![shield](catalog/security/shield.png) **Security:** 76 icons (locks, keys, shields, certificates, safes, clocks, alarms)
- ![toolbox](catalog/tools/toolbox.png) **Tools:** 60 icons (hardware, utilities, design tools, devices, instruments)
- ![database](catalog/development/database.png) **Development:** 39 icons (console, database, code, terminal, git, apps)
- ![globe](catalog/network/globe.png) **Network:** 31 icons (wifi, cloud, globe, connections, streaming, browsers)
- ![smile](catalog/emoji/smile.png) **Emoji:** 18 icons (expressions, symbols, yin-yang, faces)

---

## ![folder](catalog/files/folder.png) Directory Structure

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
├── icon-catalog.json              # Master catalog database
├── icon-manager.py                # CLI management tool
└── README.md                      # This file
```

---

## ![console](catalog/development/console.png) Global CLI Commands

The `icon` command provides instant access from anywhere. All commands work from any directory and auto-detect your project.

### ![fast](catalog/ui/fast.png) Quick Commands

```bash
icon search <query>              # Search for icons
icon use <name> [name2...]       # Export + generate markdown
icon suggest <context>           # Get context-aware suggestions
icon md <name>                   # Generate markdown snippet
icon cat <category>              # Export whole category
icon i <name>                    # Show icon information
icon recent [N]                  # Show recent additions
```

**Example Workflow:**
```bash
icon suggest security
# → lock, key, shield, certificate, login

icon use lock shield
# → Exports icons and generates ready-to-paste markdown
```

**Full command reference:** `icon help` or see [QUICK_START.md](QUICK_START.md)

---

## ![script](catalog/development/script.png) Python Manager Commands

You can also use the Python manager directly for advanced operations:

### ![search](catalog/tools/search.png) Search

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

### ![list](catalog/ui/list.png) List Category

Show all icons in a specific category:

```bash
python3 icon-manager.py list <category>
```

**Categories:** files, network, security, tools, ui, emoji, development

**Example:**
```bash
python3 icon-manager.py list security
```

### ![export](catalog/tools/export.png) Export to Project

Copy icons to a project with semantic names:

```bash
python3 icon-manager.py export <project-path> <icon1> <icon2> ...
```

**Example:**
```bash
python3 icon-manager.py export ~/dev/my-app lock shield database network
```

Icons are exported to: `<project>/.github/assets/icons/`

### ![add](catalog/ui/add.png) Add Icon to Catalog

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

### ![import](catalog/tools/import.png) Bulk Import from CSV

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
- ![fast](catalog/ui/fast.png) **3-4x faster** than individual commands
- ![table](catalog/ui/table.png) Easy to prepare in spreadsheet software (Excel, Google Sheets)
- ![search](catalog/tools/search.png) Batch review before import
- ![shield](catalog/security/shield.png) Automatic duplicate detection

**Template:** See `icon-import-template.csv` for a ready-to-use template

### ![lightbulb](catalog/ui/lightbulb.png) Auto-Generate CSV from Filenames

Let the tool suggest names and tags based on icon filenames:

```bash
python3 icon-manager.py generate-csv suggested-icons.csv --limit 50
```

**What it does:**
- ![search](catalog/tools/search.png) Scans uncataloged icons in `raw/` directory
- ![tag](catalog/ui/tag.png) Parses filenames to suggest semantic names
- ![tag](catalog/ui/tag.png) Auto-generates tags from filename words
- ![folder](catalog/files/folder.png) Guesses categories based on keywords
- ![document](catalog/files/document.png) Creates ready-to-edit CSV file

**Benefits:**
- ![fast](catalog/ui/fast.png) **10x faster** than manual tagging from scratch
- ![lightbulb](catalog/ui/lightbulb.png) Smart suggestions from descriptive filenames
- ![table](catalog/ui/table.png) Batch review and edit in spreadsheet
- ![fast](catalog/ui/fast.png) Skip icons with numeric/unclear names

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

### ![blueprint](catalog/files/blueprint.png) Template System (Icon Families)

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
- ![tick](catalog/ui/tick.png) Define common tags once for icon families
- ![tick](catalog/ui/tick.png) Apply consistently across all variants
- ![add](catalog/ui/add.png) Add variant-specific tags as needed
- ![star](catalog/ui/star.png) Perfect for: arrows, social media icons, file types, status indicators

**Example templates:**
- **arrow:** navigation, direction, pointer
- **social:** social-media, sharing, platform
- **file-type:** file, document, format
- **status:** indicator, state, condition

### ![statistics](catalog/ui/statistics.png) View Statistics

Show enhanced library statistics with category breakdowns:

```bash
python3 icon-manager.py stats
```

**Shows:**
- ![folder](catalog/files/folder.png) Total library coverage (cataloged vs uncataloged)
- ![hierarchy](catalog/ui/hierarchy.png) Detailed breakdown by category with samples
- ![star](catalog/ui/star.png) Most used icons across projects
- ![briefcase](catalog/files/briefcase.png) Project usage summary

### ![shield](catalog/security/shield.png) Validate Catalog

Check catalog integrity for issues:

```bash
python3 icon-manager.py validate
```

**Checks:**
- ![warning](catalog/ui/warning.png) Missing source files in `raw/` directory
- ![warning](catalog/ui/warning.png) Broken symlinks in `catalog/` directories
- ![warning](catalog/ui/warning.png) Orphaned symlinks pointing to non-existent files
- ![tick](catalog/ui/tick.png) Directory structure integrity

### ![info](catalog/ui/info.png) Icon Information

Show detailed information about a specific icon:

```bash
python3 icon-manager.py info <semantic-name>
```

**Example:**
```bash
python3 icon-manager.py info lock
```

**Output includes:**
- ![tag](catalog/ui/tag.png) Semantic name and icon ID
- ![document](catalog/files/document.png) Filename and file paths
- ![folder](catalog/files/folder.png) Category and description
- ![tag](catalog/ui/tag.png) All tags
- ![briefcase](catalog/files/briefcase.png) Projects using this icon
- ![tick](catalog/ui/tick.png) File existence status

### ![clock](catalog/security/clock.png) Recent Icons

View recently cataloged icons:

```bash
python3 icon-manager.py recent --limit <N>
```

**Examples:**
```bash
python3 icon-manager.py recent           # Show last 20 icons
python3 icon-manager.py recent --limit 50  # Show last 50 icons
```

### ![export](catalog/tools/export.png) Export Category

Export all icons from a specific category at once:

```bash
python3 icon-manager.py export-category <project-path> <category>
```

**Example:**
```bash
python3 icon-manager.py export-category ~/dev/my-app security
```

**Benefits:**
- ![fast](catalog/ui/fast.png) Export entire category in one command
- ![star](catalog/ui/star.png) Perfect for themed projects (security docs, UI kits, etc.)
- ![fast](catalog/ui/fast.png) Faster than individual exports for multiple icons

---

## ![table](catalog/ui/table.png) Currently Cataloged Icons

| Preview | Name | Category | Tags |
|---------|------|----------|------|
| ![lock](catalog/security/lock.png) | lock | security | security, padlock, locked |
| ![shield](catalog/security/shield.png) | shield | security | security, shield, protection, guard |
| ![info](catalog/ui/info.png) | info | ui | information, help, question, about |
| ![warning](catalog/ui/warning.png) | warning | ui | warning, alert, caution, danger, exclamation |
| ![network](catalog/network/network-connection.png) | network | network | network, connection, tower, wifi, ethernet |
| ![folder](catalog/files/folder.png) | folder | files | folder, directory, files, organize |
| ![database](catalog/development/database.png) | database | development | database, data, storage, server, api |
| ![search](catalog/tools/search.png) | search | tools | search, find, magnifying-glass, lookup |
| ![toolbox](catalog/tools/toolbox.png) | toolbox | tools | tools, toolbox, utilities, settings |

---

## ![connect](catalog/network/connect.png) Integration with Projects

### ![search](catalog/tools/search.png) 1. Find Icons

```bash
cd /path/to/iconics
python3 icon-manager.py search <keyword>
```

### ![export](catalog/tools/export.png) 2. Export Icons

```bash
python3 icon-manager.py export ~/dev/your-project icon1 icon2 icon3
```

### ![document](catalog/files/document.png) 3. Use in README

```markdown
# Your Project

## ![Shield](.github/assets/icons/shield.png) Security

Security features documented here...

## ![Network](.github/assets/icons/network.png) Architecture

Network architecture details...
```

---

## ![tag](catalog/ui/tag.png) Categories

### ![folder](catalog/files/folder.png) files
Documents, folders, archives, file types

### ![globe](catalog/network/globe.png) network
Connections, wifi, ethernet, cloud, servers

### ![shield](catalog/security/shield.png) security
Locks, shields, keys, authentication, encryption

### ![toolbox](catalog/tools/toolbox.png) tools
Wrenches, gears, settings, utilities, maintenance

### ![control-panel](catalog/tools/control-panel.png) ui
Interface elements, buttons, indicators, controls

### ![smile](catalog/emoji/smile.png) emoji
Faces, emotions, reactions, expressions

### ![database](catalog/development/database.png) development
Code, databases, APIs, debugging, testing

---

## ![tag](catalog/ui/tag.png) Tagging Best Practices

### ![tick](catalog/ui/tick.png) Good Tags
- **Descriptive:** lock, security, padlock
- **Action-based:** search, find, lookup
- **Context:** authentication, password, access
- **Synonyms:** folder, directory, files

### ![warning](catalog/ui/warning.png) Avoid
- Too generic: icon, image, graphic
- Too specific: "blue lock with gold keyhole"
- Duplicates: lock, locking, locked (choose one primary)

---

## ![briefcase](catalog/files/briefcase.png) Projects Using Iconics

### eero-reverse-engineering
Network security research project

**Icons Used:**
- info, network, shield, database, folder, toolbox, search, lock, warning

**Integration:** Professional README with subtle icon accents for section headers

![attach](catalog/ui/attach.png) [View Project](https://github.com/johnzfitch/eero-reverse-engineering)

---

## ![map](catalog/ui/map.png) Roadmap

### ![tick](catalog/ui/tick.png) Phase 1 (Complete)
- ![tick](catalog/ui/tick.png) Basic CLI tool
- ![tick](catalog/ui/tick.png) JSON catalog system
- ![tick](catalog/ui/tick.png) Search functionality
- ![tick](catalog/ui/tick.png) Export to projects
- ![tick](catalog/ui/tick.png) Initial 9 icons cataloged

### ![tick](catalog/ui/tick.png) Phase 2 (Complete)
- ![tick](catalog/ui/tick.png) Bulk CSV import (3-4x faster)
- ![tick](catalog/ui/tick.png) Auto-generate CSV from filenames (10x faster)
- ![tick](catalog/ui/tick.png) Template system for icon families
- ![tick](catalog/ui/tick.png) Expand catalog to 1,215 icons (100% complete)
- ![tick](catalog/ui/tick.png) Enhanced statistics with category breakdowns
- ![tick](catalog/ui/tick.png) Catalog validation and integrity checking
- ![tick](catalog/ui/tick.png) Detailed icon information command
- ![tick](catalog/ui/tick.png) Recent icons tracking
- ![tick](catalog/ui/tick.png) Batch export by category
- ![tick](catalog/ui/tick.png) **Global CLI access system**
- ![tick](catalog/ui/tick.png) **Smart project detection**
- ![tick](catalog/ui/tick.png) **Auto-generated markdown snippets**
- ![tick](catalog/ui/tick.png) **Context-aware icon suggestions**
- ![tick](catalog/ui/tick.png) **One-command export and use**

### ![target](catalog/ui/target.png) Phase 3 (Future)
- ![play](catalog/ui/play.png) Web interface for visual browsing
- ![play](catalog/ui/play.png) Thumbnail generation
- ![play](catalog/ui/play.png) Auto-detection of similar icons
- ![play](catalog/ui/play.png) SVG support
- ![play](catalog/ui/play.png) Multiple sizes (16x16, 24x24, 32x32, 48x48)
- ![play](catalog/ui/play.png) Icon variations (color schemes, outlined vs filled)
- ![play](catalog/ui/play.png) Git hooks integration
- ![play](catalog/ui/play.png) Package manager (pip install iconics)

---

## ![handshake](catalog/ui/handshake.png) Contributing

### ![add](catalog/ui/add.png) Adding Icons to Catalog

1. Visual browse icons in `raw/` directory
2. Catalog with semantic metadata:

```bash
python3 icon-manager.py add "Filename" "semantic-name" \
  --tags relevant tags here \
  --category appropriate-category \
  --description "Clear description"
```

### ![edit](catalog/ui/edit.png) Improving Existing Entries

- Add missing tags
- Update descriptions for clarity
- Fix incorrect categorizations
- Report issues or suggest improvements

---

## ![settings](catalog/tools/settings.png) Technical Details

### ![list](catalog/ui/list.png) Requirements
- Python 3.6+
- Standard library only (no external dependencies)

### ![info](catalog/ui/info.png) Icon Format
- Format: PNG
- Size: Primarily 16x16 (some larger variants available)
- Vintage: 2009-2011 era icon packs

### ![save](catalog/ui/save.png) Storage Efficiency
- Original files stored once in `raw/`
- Symlinks in `catalog/` for zero-duplicate storage
- Catalog metadata ~1KB per icon

---

## ![certificate](catalog/security/certificate.png) License

MIT License - see LICENSE file for details

Icons sourced from various free icon packs (2009-2011).
Suitable for personal and open-source projects.

---

## ![index](catalog/ui/index.png) Quick Reference Card

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

## ![attach](catalog/ui/attach.png) Links

- ![book](catalog/files/book.png) **Setup Guide:** [SETUP.md](SETUP.md) - Installation, aliases, shell completion
- ![rocket](catalog/ui/rocket.png) **Quick Start Guide:** [QUICK_START.md](QUICK_START.md) - Fast workflows and examples
- ![script](catalog/development/script.png) **For AI Assistants:** [CLAUDE.md](CLAUDE.md) - Complete guide for Claude agents
- ![globe](catalog/network/globe.png) **Repository:** https://github.com/johnzfitch/iconics
- ![warning](catalog/ui/warning.png) **Issues:** https://github.com/johnzfitch/iconics/issues
- ![briefcase](catalog/files/briefcase.png) **Example Usage:** [eero-reverse-engineering](https://github.com/johnzfitch/eero-reverse-engineering)

---

**Iconics** - *Finding the right icon should be easy*

---

**Version:** 1.0.0
**Last Updated:** 2025-10-28
**Maintainer:** Zack
