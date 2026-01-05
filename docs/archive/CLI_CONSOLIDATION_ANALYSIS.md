# CLI Consolidation Analysis

## Current State

**iconics.py (new unified CLI):** 14 commands
**icon-manager.py (legacy):** 35 commands

## Commands Status

### ✅ Already in Both CLIs (No Migration Needed)
- `add` - Add icon to catalog
- `embed` - Generate CLIP embeddings
- `import` / `import-csv` - Bulk import from CSV
- `info` - Show icon details
- `list` - List icons by category
- `query` - Direct CLIP query
- `recent` - Show recently cataloged icons
- `search` - Semantic search
- `stats` - Library statistics
- `suggest` - Context-based suggestions
- `validate` - Catalog integrity check

### ✅ New Unified CLI Features (iconics.py only)
- `here` - Export to current directory
- `ingest` - Auto-label and catalog (VLM pipeline)
- `sync` - Sync raw/ with catalog/embeddings
- `use` - Export + generate markdown (replaces export/provision)
- `watch` - File system monitoring with auto-ingest

### 📋 icon-manager.py Commands NOT in iconics.py

#### HIGH PRIORITY (Consider Migrating)

| Command | Purpose | Status | Recommendation |
|---------|---------|--------|----------------|
| `generate-csv` | Vision-based CSV generation | **Has batch labeling** | ✅ Keep in icon-manager.py (specialized tool) |
| `provision` | Provision icons to project | Duplicates `use` | ❌ Deprecated by `iconics use` |
| `export` / `export-category` | Export icons | Duplicates `use` | ❌ Deprecated by `iconics use` |
| `gallery` | HTML gallery generation | Useful for visualization | 🤔 Consider migrating |
| `popular` | Most used icons | Analytics feature | 🤔 Consider migrating |
| `history` | Icon usage tracking | Analytics feature | 🤔 Consider migrating |

#### MEDIUM PRIORITY (Specialized Tools)

| Command | Purpose | Keep? |
|---------|---------|-------|
| `dedupe` | Remove duplicate icons | ✅ Keep (maintenance tool) |
| `standardize` | Filename/metadata cleanup | ✅ Keep (maintenance tool) |
| `import-win2k` | Win2k ICO import pipeline | ✅ Keep (specialized) |
| `enrich` / `enrich-llm` | Auto-enrich metadata | ✅ Keep (experimental) |

#### LOW PRIORITY (Advanced/Experimental)

| Command | Purpose | Keep? |
|---------|---------|-------|
| `analyze-subspace` | SVD analysis | ✅ Keep (research tool) |
| `batch-query` | Batch semantic search | ✅ Keep (specialized) |
| `convert-emoji` / `scan-emoji` / `scan-emojis` | Emoji tools | ✅ Keep (specialized) |
| `eval-retrieval` | Retrieval quality eval | ✅ Keep (research tool) |
| `generate-imports` | Framework import files | ✅ Keep (specialized) |
| `interpolate` / `traverse` / `residual` | Advanced CLIP ops | ✅ Keep (research tools) |
| `apply-template` / `create-template` | Template system | ✅ Keep (specialized) |

---

## Consolidation Strategy

### Option A: Migrate Selected Commands to iconics.py (Recommended)
**Migrate to iconics.py:**
- `gallery` - Visual gallery generation (useful for docs)
- `popular` - Analytics (useful for understanding usage)
- `history` - Project-specific analytics

**Keep in icon-manager.py as specialized toolkit:**
- All the research/advanced tools (analyze-subspace, eval-retrieval, etc.)
- Maintenance tools (dedupe, standardize)
- Specialized import pipelines (import-win2k)
- Template system
- Batch operations (batch-query, generate-csv)

**Rename icon-manager.py → `iconics-tools.py`** or `iconics-advanced.py`

This gives us:
- **iconics.py** - Primary CLI for daily use (search, ingest, use, watch)
- **iconics-tools.py** - Advanced/specialized operations

### Option B: Make icon-manager.py a Thin Wrapper
Replace icon-manager.py with:
```python
#!/usr/bin/env python3
import sys
import subprocess

# Map old commands to new
COMMAND_MAP = {
    'export': 'use',
    'provision': 'use',
    'generate-csv': 'generate-csv',  # Keep specialized
}

cmd = sys.argv[1] if len(sys.argv) > 1 else None
new_cmd = COMMAND_MAP.get(cmd, cmd)

# Delegate to iconics.py or keep specialized
if new_cmd in ['generate-csv', 'dedupe', ...]:  # Specialized commands
    # Run original icon-manager.py logic
    pass
else:
    # Delegate to iconics.py
    subprocess.run(['iconics'] + [new_cmd] + sys.argv[2:])
```

---

## Recommendation: **Option A**

**Actions:**
1. ✅ Keep iconics.py as primary CLI
2. ✅ Rename icon-manager.py → iconics-tools.py
3. Migrate 3 commands to iconics.py:
   - `gallery` → `iconics gallery` (HTML visualization)
   - `popular` → `iconics popular` (analytics)
   - `history` → `iconics history <project>` (project analytics)
4. Update documentation to point to iconics.py as primary entry point

**Result:**
- **iconics.py** - 17 commands (current 14 + gallery + popular + history)
- **iconics-tools.py** - 22 commands (specialized/advanced tools)
- Clear separation: daily use vs. advanced operations

---

## Files to Update

1. `/home/zack/dev/iconics/iconics.py` - Add 3 new subparsers
2. `/home/zack/dev/iconics/icon-manager.py` - Rename to iconics-tools.py
3. `~/.claude/skills/iconics.sh` - Update to use `iconics.py --quiet`
4. `/home/zack/dev/iconics/CLAUDE.md` - Update command reference
5. `/home/zack/dev/iconics/README.md` - Update CLI documentation

---

## Migration Priority

If migrating to iconics.py:

**Priority 1: gallery** (useful for docs/visualization)
```python
# In iconics.py
gallery_parser = subparsers.add_parser('gallery', help='Generate HTML gallery')
gallery_parser.add_argument('--output', default='gallery.html', help='Output file')
```

**Priority 2: popular** (analytics)
```python
popular_parser = subparsers.add_parser('popular', help='Show most used icons')
popular_parser.add_argument('--limit', type=int, default=20, help='Number to show')
```

**Priority 3: history** (project-specific analytics)
```python
history_parser = subparsers.add_parser('history', help='Show icon usage history')
history_parser.add_argument('project', help='Project directory')
```

---

**Status:** Analysis complete. Awaiting user decision on migration approach.
