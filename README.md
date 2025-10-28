# Iconics

**A semantic icon library with intelligent tagging and discovery**

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Icons](https://img.shields.io/badge/icons-1700%2B-brightgreen.svg)
![Cataloged](https://img.shields.io/badge/cataloged-121-orange.svg)

---

## Overview

Iconics is a centralized, semantically-tagged icon library designed for easy discovery and reuse across multiple projects. Instead of hunting through folders of numbered files, search by meaning and context.

### Key Features

- **Semantic Naming:** Icons tagged with meaningful names (lock, shield, network)
- **Rich Metadata:** Tags, categories, descriptions for powerful search
- **CLI Management:** Search, export, and organize from the command line
- **Project Tracking:** Automatic tracking of which projects use which icons
- **Symlink Organization:** Efficient storage with categorized views
- **Cross-Project Reuse:** Export icons to any project with semantic names

---

## Quick Start

### Search for Icons

```bash
cd /home/zack/dev/iconics
python3 icon-manager.py search security
```

**Output:**
```
Found 2 icon(s) matching 'security':
  lock                  #Lock  [security]  Tags: security, padlock, locked
  shield                #Shield_16x16  [security]  Tags: security, shield, protection, guard
```

### Export to Your Project

```bash
python3 icon-manager.py export ~/dev/my-project lock shield network
```

Icons are copied to `my-project/.github/assets/icons/` with semantic names, ready to use:

```markdown
## ![Shield](.github/assets/icons/shield.png) Security Features

Your content here...
```

---

## Library Stats

- **Total Icons:** 1,700+ PNG files
- **Cataloged:** 121 icons (7% coverage)
- **Categories:** 7 (files, network, security, tools, ui, emoji, development)
- **Projects Using:** 1 (eero-reverse-engineering)

### Category Breakdown
- **UI Elements:** 62 icons (arrows, buttons, media controls, labels)
- **Files:** 17 icons (documents, folders, media types)
- **Security:** 11 icons (locks, keys, certificates, visibility)
- **Development:** 10 icons (console, scripts, errors, login)
- **Tools:** 10 icons (settings, print, power, battery)
- **Network:** 8 icons (wifi, cloud, globe, connections)
- **Emoji:** 3 icons (happy, sad, smile)

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
├── icon-catalog.json              # Master catalog database
├── icon-manager.py                # CLI management tool
└── README.md                      # This file
```

---

## CLI Commands

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

### View Statistics

Show library statistics:

```bash
python3 icon-manager.py stats
```

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

### Good Tags ✅
- **Descriptive:** lock, security, padlock
- **Action-based:** search, find, lookup
- **Context:** authentication, password, access
- **Synonyms:** folder, directory, files

### Avoid ❌
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

### Phase 1 ✅ (Complete)
- ✅ Basic CLI tool
- ✅ JSON catalog system
- ✅ Search functionality
- ✅ Export to projects
- ✅ Initial 9 icons cataloged

### Phase 2 ✅ (Complete)
- ✅ Bulk tagging tool for rapid cataloging
- ✅ Expand catalog to 121 icons
- [ ] Web interface for visual browsing
- [ ] Thumbnail generation
- [ ] Auto-detection of similar icons

### Phase 3 (Future)
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
| `add <id> <name> --tags... --category...` | Catalog new icon |
| `stats` | Show library statistics |

---

## Links

- **Repository:** https://github.com/johnzfitch/iconics
- **Issues:** https://github.com/johnzfitch/iconics/issues
- **Example Usage:** [eero-reverse-engineering](https://github.com/johnzfitch/eero-reverse-engineering)

---

**Iconics** - *Finding the right icon should be easy*

---

**Version:** 1.0.0
**Last Updated:** 2025-10-28
**Maintainer:** Zack
