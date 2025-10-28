# Icon Library Management System

## Current Situation
- **Location:** `/home/zack/dev/icons/`
- **Total Icons:** 1,231 PNG files (+ GIF versions)
- **Problem:** Icons are numerically named (100.png, 101.png, etc.) with no semantic meaning
- **Goal:** Create searchable, tagged icon library usable across all GitHub projects

---

## Proposed Solution: Icon Catalog System

### 1. Icon Catalog Database (JSON)

Create `icon-catalog.json` with structure:
```json
{
  "icons": [
    {
      "id": "100",
      "filename": "100.png",
      "semanticName": "document",
      "tags": ["file", "document", "text", "page"],
      "category": "files",
      "size": "16x16",
      "description": "Text document icon",
      "usedIn": ["eero-reverse-engineering"]
    },
    {
      "id": "10",
      "filename": "10.png",
      "semanticName": "emoji-smile",
      "tags": ["emoji", "face", "happy", "smile"],
      "category": "emoji",
      "size": "16x16",
      "description": "Smiling emoji face"
    }
  ],
  "categories": {
    "files": ["document", "folder", "archive"],
    "network": ["connection", "wifi", "ethernet"],
    "security": ["lock", "shield", "key"],
    "tools": ["wrench", "gear", "settings"],
    "navigation": ["arrow", "pointer", "direction"],
    "communication": ["email", "chat", "phone"],
    "media": ["image", "video", "audio"],
    "emoji": ["faces", "emotions"],
    "development": ["code", "bug", "test"]
  }
}
```

### 2. Management Tools

#### Option A: Custom Python Tool
```python
# icon-manager.py
import json
import os
from PIL import Image
import hashlib

class IconManager:
    def scan_icons(self, directory):
        # Scan all PNGs, generate thumbnails
        pass

    def tag_icon(self, icon_id, tags, semantic_name):
        # Add metadata to catalog
        pass

    def search(self, query):
        # Search by tags, semantic name, category
        pass

    def export_for_project(self, icon_ids, project_name):
        # Copy selected icons to project with semantic names
        pass
```

#### Option B: Use Existing Tools

**ImageMagick + identify:**
```bash
identify -format "%f %wx%h\n" *.png
# Get dimensions for all icons
```

**exiftool:**
```bash
exiftool -Comment="security,lock,padlock" 100.png
# Add EXIF metadata tags
```

**Organize with:**
- [DigiKam](https://www.digikam.org/) - Photo management with tagging
- [XnView MP](https://www.xnview.com/) - Multi-platform image viewer with catalog
- Custom web interface (lightweight Flask/FastAPI app)

### 3. Directory Structure Proposal

```
/home/zack/dev/icons/
├── raw/                           # Original numbered files
│   ├── 100.png
│   ├── 101.png
│   └── ...
├── catalog/                       # Organized by category
│   ├── files/
│   │   ├── document.png -> ../raw/100.png
│   │   ├── folder.png -> ../raw/150.png
│   │   └── ...
│   ├── network/
│   │   ├── connection.png -> ../raw/200.png
│   │   └── ...
│   ├── security/
│   │   ├── lock.png -> ../raw/686.png
│   │   ├── shield.png -> ../raw/893.png
│   │   └── ...
│   └── ...
├── icon-catalog.json              # Master catalog database
├── icon-manager.py                # Management CLI tool
├── thumbnails/                    # Generated thumbnails for browsing
└── README.md                      # Usage documentation
```

### 4. Workflow

#### Initial Cataloging (One-time)
1. Visual browse and tag icons (web interface or DigiKam)
2. Generate `icon-catalog.json` with metadata
3. Create symlinks in `catalog/` directory

#### Using Icons in Projects
```bash
# Search for icons
./icon-manager.py search "security lock"
# Output: lock.png (raw/686.png), shield.png (raw/893.png)

# Export to project
./icon-manager.py export eero-reverse-engineering lock shield network
# Copies to project/.github/assets/icons/ with semantic names
```

#### Maintaining Catalog
```bash
# Add new icon
./icon-manager.py add new-icon.png --tags "cloud,upload" --category "network"

# Update existing
./icon-manager.py tag 100.png --tags "document,file,text"

# Generate report
./icon-manager.py stats
# Shows usage across projects, most used icons, etc.
```

---

## Recommended Approach

### Phase 1: Manual Catalog Bootstrap (1-2 hours)
1. Create initial `icon-catalog.json` with ~50 most common icons
2. Tag by visual inspection with semantic names
3. Create symlink structure for categories

### Phase 2: Build Simple CLI Tool (2-3 hours)
```bash
# icon-manager.py features:
- search: Find icons by tag/name
- export: Copy icons to project
- tag: Add metadata to icon
- list: Show all icons in category
- stats: Usage statistics
```

### Phase 3: Web Interface (Optional, 4-5 hours)
- Visual grid browser
- Drag-and-drop tagging
- Project-specific icon sets
- Usage tracking

---

## Quick Start: Minimal Viable Solution

### Step 1: Create Basic Catalog
```bash
cd /home/zack/dev/icons

# Create initial structure
mkdir -p catalog/{files,network,security,tools,ui}
mkdir raw thumbnails
mv *.png *.gif raw/

# Start catalog file
cat > icon-catalog.json << 'EOF'
{
  "version": "1.0",
  "icons": [],
  "categories": ["files", "network", "security", "tools", "ui", "emoji"]
}
EOF
```

### Step 2: Tag Current Eero Icons
Update catalog with icons you've already used:
```json
{
  "icons": [
    {"id": "686", "filename": "raw/686.png", "semantic": "lock", "tags": ["security","lock","padlock"], "category": "security"},
    {"id": "893", "filename": "raw/893.png", "semantic": "shield", "tags": ["security","shield","protection"], "category": "security"},
    {"id": "940", "filename": "raw/940.png", "semantic": "info", "tags": ["info","information","help"], "category": "ui"},
    {"id": "438", "filename": "raw/438.png", "semantic": "network", "tags": ["network","connection","tower"], "category": "network"}
  ]
}
```

### Step 3: Create Symlinks
```bash
cd /home/zack/dev/icons
ln -s raw/686.png catalog/security/lock.png
ln -s raw/893.png catalog/security/shield.png
ln -s raw/940.png catalog/ui/info.png
ln -s raw/438.png catalog/network/connection.png
```

### Step 4: Update Eero Project
```bash
cd ~/dev/eero
rm -rf .github/assets/icons
mkdir -p .github/assets/icons
cp /home/zack/dev/icons/catalog/security/{lock,shield}.png .github/assets/icons/
cp /home/zack/dev/icons/catalog/ui/info.png .github/assets/icons/
cp /home/zack/dev/icons/catalog/network/connection.png .github/assets/icons/
```

---

## Tools Recommendations

### For Initial Cataloging
1. **XnView MP** (GUI) - Fast thumbnail browsing, batch renaming
2. **feh** (CLI) - Lightweight image viewer for Linux
3. **DigiKam** (GUI) - Full featured with tagging support

### For Management
1. **Custom Python Script** - Lightweight, fits workflow
2. **Git LFS** - If icons get large/numerous
3. **Markdown Index** - Simple alternative to JSON

### For Search
1. **fzf + preview** - Terminal fuzzy finder with image preview
2. **rofi/dmenu** - Quick launcher integration
3. **Simple web interface** - Flask + grid layout

---

## Next Steps

1. ✅ Identify which approach to take (custom tool vs existing software)
2. ⏳ Create initial catalog structure
3. ⏳ Tag 50-100 most useful icons
4. ⏳ Build basic `icon-manager.py` CLI
5. ⏳ Update eero project to use shared library
6. ⏳ Document usage for future projects

**Estimated Time:** 3-4 hours for full MVP solution
