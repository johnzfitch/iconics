# Iconics Handoff Document - Agentic Executive Session

**Date:** 2026-01-04
**Status:** Bug fixing in progress - VLM integration and auto-pipeline
**Priority:** Fix retriever initialization, verify canonical/icon_id normalization

---

## 1. Current Bug to Fix First

### Bug A: Retriever Initialization Error (BLOCKING)

**Symptom:**
```
Could not initialize retriever/labeler: 5673
CLIP retrieval failed: Retriever not initialized
✗ Ingestion failed: Retriever not initialized
```

**File:** `iconics.py` - ingest command handler

**Likely cause:** Error handling printing wrong value (5673 looks like icon count, not error message)

**Action needed:** Debug retriever initialization in `iconics.py` ingest command

### Bug B: Canonical Name vs icon_id Mismatch

**Problem:** VLM returns `canonical` field but `iconics_executive.py` looks for `icon_id`, falling back to filename (path.stem).

**Evidence from testing:**
```
→ adversarial-lock-blurred (VLM Enriched, conf=0.950)
```
Should be semantic name like "lock" or "padlock", not the filename.

**File:** `src/iconics_executive.py`

**Fix Applied (lines ~368-371):**
```python
# Normalize: VLM returns 'canonical' but we need 'icon_id' for catalog
# Use canonical as the icon ID (semantic name)
if 'canonical' in label_data and 'icon_id' not in label_data:
    label_data['icon_id'] = label_data['canonical']
```

**Status:** Fix applied but NOT verified due to Bug A blocking testing

### Bug C: k-NN Matching Wrong Icons

**Symptom:** Blurred lock icon matched to "home" or "help-20-20x20" with high similarity

**Possible causes:**
- Embeddings index out of sync with catalog
- Icon ID mapping corruption in embeddings
- Stale test icons in catalog from previous runs (confirmed: "home" entry points to test file)

**Action needed:** Clean test artifacts from catalog before retesting

---

## 2. What's Working

### Components Tested and Functional:

- **CLIP embeddings** - ViT-B-32 model loads and embeds images ✅
- **FAISS index** - Vector search with IndexFlatIP for cosine similarity ✅
- **Incremental embeddings** - `add_incremental_embedding()` method in retriever ✅
- **VLM labeling** - Qwen2.5-VL-7B generates labels with confidence ✅
- **RAG-enhanced prompts** - k-NN context passed to VLM ✅
- **High-confidence bypass** - Icons with ≥0.92 similarity skip VLM ✅
- **IconLabel dataclass** - Structured results with to_dict() conversion ✅
- **HuggingFace offline mode** - Environment variables set to prevent runtime downloads ✅
- **Batch labeling** - Integrated into icon-manager.py (lines 1717-1781) ✅
- **Multi-modal output** - JSON, quiet, verbose modes in iconics.py ✅

### Bugs Fixed This Session:

1. **Method name mismatch** - `retrieve_for_image` doesn't exist → Complete rewrite of `_find_nearest_neighbor()`
2. **API misunderstanding** - `retrieve_by_icon()` expects ID not path → Use `embed_image()` + `retrieve_for_labeling()`
3. **Parameter name** - `k=10` → `k_neighbors=10`
4. **Type conversion** - Added `icon_label.to_dict()` for IconLabel dataclass
5. **Missing confidence** - Added to LIBRARIAN_SYSTEM_PROMPT output format
6. **HuggingFace downloads** - Added offline mode to iconics_vision.py
7. **Canonical/icon_id mapping** - Added normalization (NEEDS VERIFICATION)

---

## 3. What's NOT Working

See **Section 1: Current Bug to Fix First** above.

---

## 4. Remaining TODOs (Prioritized)

### HIGH Priority (Blocking):
1. ❌ **Fix retriever initialization** - Blocking all ingest testing
2. ❌ **Verify canonical/icon_id normalization** - Fix applied but untested
3. ❌ **Fix k-NN match accuracy** - Icons matching wrong neighbors
4. ❌ **Clean test artifacts** - Remove test icons from catalog

### MEDIUM Priority:
5. ⏳ **Manual watcher test** - Script at `/tmp/test-watcher-manual.sh`
6. ⏳ **CLI consolidation decision** - Analysis at `CLI_CONSOLIDATION_ANALYSIS.md`
7. ⏳ **Adversarial naming drift test** - Script at `/tmp/test-naming-drift.py`

### LOW Priority:
8. 📋 **Rename icon-manager.py → iconics-tools.py** - Recommended in analysis
9. 📋 **Document Reflective Audit** - System 2 reasoning for naming drift
10. 📋 **Optimize batch sizes** - Current: VLM=4, CLIP=64

---

## 5. Key File Locations and Purpose

### Core Pipeline:

| File | Lines | Purpose |
|------|-------|---------|
| `iconics.py` | 345 | Unified CLI entry point - **INVESTIGATE INGEST COMMAND** |
| `src/iconics_executive.py` | ~600 | OODA loop orchestrator - **Contains canonical/icon_id fix** |
| `src/iconics_retrieval.py` | ~970 | CLIP embeddings, FAISS search, incremental updates |
| `src/iconics_vision.py` | ~800 | VLM (Qwen2.5-VL) integration - **Contains offline mode fix** |
| `src/iconics_prompts.py` | ~150 | System prompts for VLM - **Contains confidence field fix** |
| `src/iconics_watcher.py` | ~200 | File watcher with 500ms debouncing |
| `icon-manager.py` | 2700+ | Legacy CLI - **Contains batch labeling integration** |

### Data Files:

| File | Size | Purpose |
|------|------|---------|
| `icon-catalog.json` | 5,673 | Master catalog of all icons - **May contain test artifacts** |
| `embeddings/icon_embeddings.npy` | (N, 512) | CLIP vectors |
| `embeddings/icon_index.json` | N entries | icon_id → index mapping |
| `embeddings/metadata.json` | Stats | Embedding metadata |

### Test/Analysis Files:

| File | Purpose |
|------|---------|
| `/tmp/test-naming-drift.py` | Adversarial test generator (blur, invert) |
| `/tmp/test-watcher-manual.sh` | Watcher test script (2 terminals) |
| `CLI_CONSOLIDATION_ANALYSIS.md` | 35 vs 14 command comparison |
| `TESTING_SUMMARY.md` | Test results and known limitations |
| `~/.claude/skills/iconics.sh` | Claude Code skill wrapper (thin wrapper to iconics.py) |

---

## 6. Architecture Overview

### Auto-Pipeline Flow:

```
Drop Icon → Watcher (500ms debounce) → Executive (OODA Loop)
                                            │
                                            ├─→ CLIP Embed → k-NN Search
                                            │                    │
                                            │        ┌───────────┘
                                            │        ▼
                                            │   Similarity ≥ 0.92? ──Yes──→ High-Confidence Bypass
                                            │        │
                                            │        No
                                            │        ▼
                                            ├─→ VLM Label (RAG: k=10 context)
                                            │        │
                                            │        ▼
                                            │   Reflective Audit (System 2 reasoning)
                                            │        │
                                            │        ▼
                                            ├─→ Catalog Update (icon_id from canonical)
                                            │        │
                                            └─→ Incremental Embedding (FAISS append)
                                                     │
                                                     ▼
                                            Icon Immediately Searchable ✅
```

### OODA Loop (Executive Pattern):

1. **Observe** - Watch raw/ directory for new icons
2. **Orient** - CLIP embedding + k-NN retrieval
3. **Decide** - High-confidence bypass OR VLM labeling
4. **Act** - Catalog update + incremental embedding

---

## 7. How to Test

### Test Ingest Pipeline:

```bash
cd /home/zack/dev/iconics

# Create test icon
cp raw/lock-16x16.png /tmp/test-icon.png

# Run with verbose output
.venv-vision/bin/python3 iconics.py --verbose ingest /tmp/test-icon.png

# Force VLM labeling (skip high-confidence bypass)
.venv-vision/bin/python3 iconics.py --verbose ingest /tmp/test-icon.png --force

# Expected output:
# - k-NN match shown
# - VLM label generated
# - Icon cataloged with semantic name (NOT filename)
# - Incremental embedding added
```

### Test Retrieval:

```bash
# Search by text
.venv-vision/bin/python3 iconics.py search "security lock"

# Query with k neighbors
.venv-vision/bin/python3 iconics.py query "authentication" --k 5
```

### Test Watcher (Manual):

```bash
# Terminal 1: Start watcher
.venv-vision/bin/python3 iconics.py watch

# Terminal 2: Drop icon
cp raw/some-icon.png raw/test-drop.png

# Watch Terminal 1 for processing output
# Should see: Ingest → Label → Catalog → Embed → "Available for search"
```

### Run Adversarial Naming Drift Test:

```bash
cd /tmp && python3 test-naming-drift.py

# Verify test icons created:
ls -lh /tmp/naming-drift-test/

# Ingest with force to trigger VLM:
cd /home/zack/dev/iconics
.venv-vision/bin/python3 iconics.py --verbose ingest /tmp/naming-drift-test/adversarial-lock-blurred.png --force

# Expected: Icon cataloged with semantic name like "lock", not "adversarial-lock-blurred"
```

### Verify Embeddings Sync:

```bash
# Check counts match
jq '.icons | length' icon-catalog.json
python3 -c "import numpy as np; print(np.load('embeddings/icon_embeddings.npy').shape[0])"

# Should be equal or embeddings can be 1-2 behind (incremental adds are async)
```

### Clean Test Artifacts:

```bash
# Find test icons in catalog
grep -i "test-\|adversarial" icon-catalog.json

# Remove them (manual JSON editing or re-import clean catalog)
```

---

## 8. Critical Code Sections

### iconics_executive.py - Canonical/Icon_ID Normalization

**Location:** Lines 362-373

```python
icon_label = self.labeler.label_icon(
    path,
    k_neighbors=10,  # Fixed: was k=10
    use_cache=True
)

# Convert IconLabel to dict for processing
label_data = icon_label.to_dict()

# Normalize: VLM returns 'canonical' but we need 'icon_id' for catalog
# Use canonical as the icon ID (semantic name)
if 'canonical' in label_data and 'icon_id' not in label_data:
    label_data['icon_id'] = label_data['canonical']
```

### iconics_executive.py - Incremental Embedding

**Location:** Lines 398-405

```python
# Incremental embedding update (makes icon immediately searchable)
if self.retriever:
    try:
        self.retriever.add_incremental_embedding(path)
        logger.debug(f"Added incremental embedding for {path.name}")
    except Exception as e:
        logger.error(f"Failed to add incremental embedding for {path.name}: {e}")
        # Non-fatal - catalog update succeeded, embedding can be added later
```

### iconics_vision.py - Offline Mode

**Location:** Lines 27-31

```python
# Configure HuggingFace for local-first operation
# Models must be pre-downloaded during setup, not at runtime
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HOME", os.path.expanduser("~/.cache/huggingface"))
```

### iconics_retrieval.py - Incremental Embedding Method

**Location:** Lines 899-970

```python
def add_incremental_embedding(self, icon_path: Path) -> None:
    """Add a single icon embedding without full rebuild."""
    # 1. Embed new icon
    # 2. Append to embeddings array (np.vstack)
    # 3. Update index mappings
    # 4. Add to FAISS index (fast incremental operation)
    # 5. Persist to disk (npy, json, faiss)
```

---

## 9. Quick Debugging Commands

```bash
# Check catalog for test artifacts
grep -i "adversarial\|test-" icon-catalog.json

# View recent catalog entries
jq '.icons[-5:]' icon-catalog.json

# Check embedding index mapping
head -20 embeddings/icon_index.json

# Test CLIP embedding directly
.venv-vision/bin/python3 -c "
from src.iconics_retrieval import IconicsRetriever
r = IconicsRetriever()
print(f'Loaded {len(r.icon_ids)} embeddings')
"

# Test VLM labeling directly
.venv-vision/bin/python3 -c "
from pathlib import Path
from src.iconics_vision import VisionLabeler
labeler = VisionLabeler()
label = labeler.label_icon(Path('/tmp/test-icon.png'), k_neighbors=10)
print(f'Label: {label.canonical} (conf={label.confidence})')
"
```

---

## 10. Environment Notes

- **Python venv:** `.venv-vision/bin/python3`
- **VRAM requirement:** 24GB for Qwen2.5-VL-7B
- **HuggingFace cache:** `~/.cache/huggingface` (models pre-downloaded)
- **Offline mode:** Set via environment variables in `iconics_vision.py`
- **CLIP model:** ViT-B-32 (512-dimensional embeddings)
- **Batch sizes:** VLM=4 icons/batch, CLIP=64 icons/batch

---

## 11. Known Limitations (from TESTING_SUMMARY.md)

1. **No deduplication** - Same icon can be ingested multiple times
2. **No error recovery** - If VLM fails, icon not cataloged
3. **No rollback** - Partial failures leave inconsistent state
4. **Watcher untested** - Manual testing script exists but not run
5. **Reflective Audit untested** - Adversarial test created but not run
6. **Batch size hardcoded** - Should be configurable based on VRAM
7. **Test artifacts in catalog** - Need cleanup before production use

---

## 12. Next Steps for Continuing Agent

### Immediate (Critical):

1. **Debug retriever initialization error** in `iconics.py` ingest command
   - Search for where `IconicsRetriever` is instantiated
   - Check error handling (why "5673" instead of error message?)
   - Verify `.venv-vision` Python environment is correct

2. **Clean test artifacts** from catalog
   - Remove entries with test/adversarial in paths
   - Verify embeddings sync after cleanup

3. **Verify canonical/icon_id fix**
   - Once retriever works, re-run test ingestion
   - Confirm icon cataloged with semantic name, not filename
   - Check VLM cache files in `vision_cache/` for validation

### Short-term (Important):

4. **Run manual watcher test** using `/tmp/test-watcher-manual.sh`
5. **Run adversarial naming drift test** and verify Reflective Audit catches it
6. **Make CLI consolidation decision** based on analysis in `CLI_CONSOLIDATION_ANALYSIS.md`

### Medium-term (Nice to have):

7. Rename `icon-manager.py` → `iconics-tools.py` for clarity
8. Document Reflective Audit system in detail
9. Add configuration for batch sizes and thresholds
10. Add deduplication and error recovery

---

## 13. Session Context

**Previous Session:** CLIP vector subspace system (2026-01-01)
**Current Session:** Agentic executive with VLM integration (2026-01-04)

**Work Done:**
- Autonomous bug fixing loop (5 bugs fixed)
- Batch labeling integration
- CLI consolidation analysis
- Test script creation
- HuggingFace offline mode
- Canonical/icon_id normalization

**Status:** Stuck on retriever initialization error, blocking final verification of fixes.

**User was AFK during:** Autonomous testing and bug fixing phase

---

**Last Update:** 2026-01-04
**Session Agent:** Claude Sonnet 4.5
