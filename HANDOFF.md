# Iconics Project Handoff Document

**Date:** 2026-01-01
**Status:** CLIP Vector Subspace System Complete + Friction Fixes Applied
**Uncommitted Changes:** Yes (see git status)

---

## Project Overview

Iconics is a semantic icon library with 7,878 PNG icons designed to replace emojis in documentation. The system provides:

- **Global `icon` command** - Works from anywhere
- **CLIP-based semantic search** - Find icons by natural language
- **Hybrid retrieval** - Blends keyword matching with vector similarity
- **Project provisioning** - Export icons to any project with markdown snippets

**Location:** `/home/zack/dev/iconics`

---

## Recent Work Completed

### CLIP Vector Subspace System (8 Phases)

Built a complete CLIP-based semantic retrieval system:

| Component | File | Description |
|-----------|------|-------------|
| Embeddings | `src/iconics_embeddings.py` | CLIP ViT-B/32 embeddings for all 7,878 icons |
| Subspace | `src/iconics_subspace.py` | SVD analysis, k=166 effective dimensions |
| Retrieval | `src/iconics_retrieval.py` | IconicsRetriever class with projection |
| Index | `src/iconics_index.py` | FAISS IndexFlatIP for fast search |
| Evaluation | `src/iconics_eval.py` | MRR, NDCG, Precision/Recall metrics |
| Provisioning | `src/iconics_provision.py` | Copy icons to project directories |
| Emoji Scanner | `src/iconics_emoji.py` | Find and replace emojis in files |

**Test Coverage:** 262 tests passing

### Friction Fixes (Latest Session)

1. **Python Environment** - Fixed shebang to use pyg Python directly
2. **Hybrid Query Mode** - Blends keyword + CLIP for better results
3. **Vector Fallback** - `icon use` falls back to semantic search
4. **Normalized Output** - Query results use consistent lowercase-dash IDs

---

## Key Files

```
iconics/
├── icon                      # Bash wrapper (global command)
├── icon-manager.py           # Main CLI tool (2700+ lines)
├── icon-catalog.json         # 5,671 cataloged icons
├── CLAUDE.md                 # Agent instructions
├── src/                      # CLIP modules
│   ├── iconics_embeddings.py
│   ├── iconics_subspace.py
│   ├── iconics_retrieval.py
│   ├── iconics_index.py
│   ├── iconics_eval.py
│   ├── iconics_provision.py
│   └── iconics_emoji.py
├── embeddings/               # Generated data
│   ├── icon_embeddings.npy   # (7878, 512) float32
│   ├── icon_index.json       # ID → row mapping
│   └── subspace/
│       ├── basis_vectors.npy # (512, 166) matrix
│       └── effective_dim.json
├── tests/                    # 262 tests
│   ├── conftest.py
│   └── unit/
├── raw/                      # Source PNG files (8k+)
└── catalog/                  # Organized by category
```

---

## How to Use

### Quick Commands (via `icon` wrapper)

```bash
# Search by keyword
icon search security

# Export icons + get markdown
icon use lock shield key

# Get suggestions for a context
icon suggest authentication

# Export entire category
icon cat security
```

### CLIP Vector Commands (via `icon-manager.py`)

```bash
# Semantic query (hybrid mode by default)
./icon-manager.py query "error close cancel" --k 10

# Pure CLIP mode (no keyword blending)
./icon-manager.py query "security" --no-hybrid

# Traverse semantic axis
./icon-manager.py traverse lock-24x24 --axis 0 --steps 5

# Compute residual score (how "icon-like" is query)
./icon-manager.py residual "abstract concept"

# Batch query for project setup
./icon-manager.py batch-query --queries "security,files,settings" --k 2

# Provision icons to project
./icon-manager.py provision --query "authentication" --dest ./icons/ --k 3

# Scan for emoji usage
./icon-manager.py scan-emoji --path ./docs

# Convert emojis to icons
./icon-manager.py convert-emoji --report emoji-report.json --apply
```

---

## Architecture Notes

### Hybrid Retrieval (query command)

The `query` command uses hybrid mode by default:

1. **Split query** into individual terms
2. **Keyword search** for each term using existing `search()` method
3. **CLIP retrieval** in projected subspace
4. **Score blending:**
   - +20% boost for keyword matches
   - +10% boost if query term appears in icon ID
5. **Re-rank** and return top-k

This fixes cases like "error close cancel" returning "mute" (visual similarity) by boosting icons that match keywords.

### Vector Fallback (export command)

When `icon use <name>` doesn't find an exact match:

1. Try `find_icons_by_semantic()` (exact/prefix/suffix matching)
2. If not found, call `_vector_fallback(name)`:
   - First try keyword search
   - Then try CLIP retrieval
3. Auto-export the best semantic match

### ID Normalization

Embeddings use raw filenames (mixed case, underscores), catalog uses standardized names (lowercase, dashes). The `normalize_to_catalog()` function converts:
- `Close_32x32` → `close-32x32`
- `mute_24x24` → `mute-24x24`

---

## Dependencies

The CLIP system requires the pyg Python environment:

```bash
# Activate pyg environment (via bashrc alias)
pyg

# Or use directly
~/.local/share/python-global/bin/python

# Required packages
torch>=2.0
open-clip-torch
faiss-cpu
numpy
scipy
```

The `icon-manager.py` shebang points directly to pyg Python, so `./icon-manager.py` works without activation.

---

## Current State

### Uncommitted Changes

```bash
git status  # Shows modified files
git diff    # See changes
```

Key uncommitted changes:
- `icon-manager.py` - Hybrid query mode, vector fallback, normalization
- `icon` wrapper - Updated to use $PYTHON variable

### What Works

- All 262 tests pass
- Hybrid query returns semantically relevant results
- Vector fallback for `icon use` works
- Output IDs are normalized
- Aegis project was successfully converted from emojis to icons

### Known Issues

1. **Duplicate results** - Some icons appear twice in results (e.g., `mute_24x24` and `Mute_24x24` both normalize to `mute-24x24`). Would be fixed by regenerating embeddings from catalog IDs.

2. **64x64 variants** - Many icons have 64x64 variants that dominate results. Could add size filtering.

3. **Embeddings/catalog mismatch** - Embeddings use raw filenames, catalog uses semantic names. The normalization function handles this at query time but it's not ideal.

---

## Potential Next Steps

### Short-term

1. **Commit current changes** - The friction fixes are uncommitted
2. **Add size filtering** - Option to prefer specific icon sizes (24x24, 32x32)
3. **Deduplicate results** - Remove duplicate normalized IDs from query output

### Medium-term

1. **Regenerate embeddings** - Use catalog semantic names instead of raw filenames
2. **Add `icon query` to wrapper** - Expose CLIP query in the `icon` command
3. **Improve provisioning** - Better manifest management, resize on export

### Long-term

1. **Hyperbolic embeddings** - Better hierarchy representation
2. **Fine-tune CLIP** - Train on icon-specific data
3. **Web UI** - Browse and search icons visually

---

## Testing

```bash
# Run all tests
cd /home/zack/dev/iconics
pytest tests/ -v

# Run specific test file
pytest tests/unit/test_retrieval_unit.py -v

# Quick functionality check
./icon-manager.py query "security" --k 5
icon use lock shield
icon search error
```

---

## Reference Documents

- `CLAUDE.md` - Agent instructions for using iconics
- `refactor/README.md` - Original CLIP architecture spec
- `refactor/02_PHASES.md` - Implementation phases
- `skill/SKILL.md` - LLM skill file for context-aware usage

---

## Contact

This is Zack's personal project. All code is in `/home/zack/dev/iconics`.

**Last Agent Session:** 2026-01-01 (Opus 4.5)
