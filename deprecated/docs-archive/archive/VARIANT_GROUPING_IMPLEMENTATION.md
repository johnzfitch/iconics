# Variant Grouping System Implementation

## Overview

Implemented Agent 2: Variant Grouping System as specified in `agents.md`. The system detects, displays, and bundles icon size variants using name pattern matching + CLIP similarity verification.

## Files Created

### `/home/zack/dev/iconics/src/iconics_variants.py`

Core variant detection and bundling logic with the following components:

#### 1. Size Extraction (`extract_base_and_size()`)

Robust regex pattern matching supporting:
- `name-WxH` (e.g., `lock-32x32`)
- `name_WxH` (e.g., `lock_32x32`)
- `name-WxH-variant` (e.g., `lock-16x16-old`)
- `WxH-name` (e.g., `32x32-lock`)

Returns `(base_name, (width, height))` tuple.

#### 2. Variant Detection (`detect_variant_groups()`)

Algorithm:
1. Group icons by extracted base name
2. Filter groups with multiple sizes (≥2 variants)
3. Verify with CLIP similarity (avg pairwise similarity ≥ threshold)
4. Create `VariantGroup` for valid groups

Key features:
- Handles missing embeddings gracefully
- Configurable similarity threshold (default: 0.90)
- Returns groups sorted by size (descending)

#### 3. VariantGroup Dataclass

Attributes:
- `base_name`: Base icon name (e.g., "lock")
- `variants`: Dict mapping icon_id to (width, height)
- `similarity_matrix`: Pairwise CLIP similarities (n×n numpy array)
- `canonical`: Preferred variant ID

Properties:
- `sizes`: Sorted list of unique sizes
- `avg_similarity`: Average pairwise similarity

Methods:
- `get_variant(size)`: Get icon ID for specific size
- `to_dict()`: JSON-serializable representation

#### 4. Canonical Selection (`pick_canonical_variant()`)

Priority order:
1. 32x32 (most common UI size)
2. 24x24 (second most common)
3. 48x48 (common desktop size)
4. 16x16 (small UI elements)
5. 64x64 (large UI elements)
6. Other sizes sorted by pixel count (larger is better)

#### 5. Bundle Format (`create_bundle()`, `read_bundle()`)

ZIP-based `.imrb` (Iconics Multi-Resolution Bundle) format:

```
bundle.imrb (ZIP archive)
├── manifest.json          # Metadata
├── 16x16.png             # Icon variants
├── 24x24.png
├── 32x32.png
└── 64x64.png
```

Manifest structure:
```json
{
  "format": "iconics-mrb-v1",
  "canonical": "lock-32x32",
  "base_name": "lock",
  "variants": {
    "16x16": {"original_id": "lock-16x16", "filename": "16x16.png"},
    "32x32": {"original_id": "lock-32x32", "filename": "32x32.png"}
  },
  "metadata": {
    "semantic_name": "lock",
    "tags": ["security", "padlock", "auth"],
    "category": "security",
    "description": "..."
  }
}
```

#### 6. Display Formatting (`format_variant_group_display()`)

Terminal-friendly output with:
- Variant table (size, icon ID, tags)
- Star (★) marking canonical variant
- Optional CLIP similarity matrix
- Average similarity score

#### 7. Dedupe Integration

Utility functions:
- `get_variant_ids()`: Extract all icon IDs from variant group
- `filter_non_canonical_variants()`: Exclude non-canonical variants from icon lists

Used by dedupe system to avoid flagging intentional size variants as duplicates.

## Files Modified

### `/home/zack/dev/iconics/iconics.py`

Added `variants` subcommand with three operational modes:

#### Mode 1: Show Specific Variant Group

```bash
iconics variants lock
iconics variants aim-24x24  # Also works with specific variant ID
```

Displays detailed information about the variant group including:
- All available sizes
- Canonical variant (marked with ★)
- Tags from catalog
- CLIP similarity matrix (with `--verbose`)

#### Mode 2: Auto-Detect All Groups

```bash
iconics variants --detect                     # Display first 10 groups
iconics variants --detect --output groups.json # Export all to JSON
iconics variants --detect --threshold 0.95     # Stricter similarity
```

Scans entire library for variant groups and:
- Reports count and total variants
- Shows detailed view of first 10 groups
- Optionally exports all groups to JSON

Output format:
```
Found 47 variant groups (156 icons total)

Variant Group: lock (4 sizes)
  Canonical: lock-32x32

  Size     Icon ID              Tags
  ────────────────────────────────────
  16x16    lock-16x16           security, padlock
  24x24    lock-24x24           security, padlock, small
  32x32    lock-32x32 ★         security, padlock, auth
  64x64    lock-64x64           security, padlock, large

  Average similarity: 0.97
```

#### Mode 3: Create Bundle

```bash
iconics variants --bundle lock                 # Creates lock.imrb
iconics variants --bundle lock -o /tmp/lock.imrb
```

Packages all variants into a single `.imrb` file with:
- All size variants
- Merged metadata from catalog
- Manifest for programmatic access

## CLI Arguments

```
positional arguments:
  name                  Show variants for specific icon base name

options:
  --detect              Auto-detect all variant groups
  --bundle BASE_NAME    Create .imrb bundle for variant group
  --output, -o OUTPUT   Output path for bundle or JSON export
  --threshold THRESHOLD CLIP similarity threshold (default: 0.90)
```

## Integration Points

### With Retriever

Uses existing `IconicsRetriever` components:
- `embeddings`: Icon embedding matrix
- `icon_ids`: List of icon identifiers
- `icon_index`: Dict mapping icon_id to index

### With Catalog

Accesses `icon-catalog.json` for:
- Tag extraction
- Category information
- Semantic names
- Descriptions

### With Dedupe System

Provides filtering functions to exclude non-canonical variants from duplicate detection:

```python
from iconics_variants import detect_variant_groups, filter_non_canonical_variants

# Detect variants
groups = detect_variant_groups(icon_ids, embeddings, icon_index)

# Filter to only canonical variants
canonical_only = filter_non_canonical_variants(icon_ids, groups)

# Now run dedupe on canonical_only to avoid flagging intentional variants
```

## Testing Verification

### Regex Extraction

Tested with various patterns:
```
aim-16x16     → base='aim'      size=(16, 16)  ✓
aim_32x32     → base='aim'      size=(32, 32)  ✓
lock-16x16-old → base='lock'    size=(16, 16)  ✓
32x32-lock    → base='lock'     size=(32, 32)  ✓
just-an-icon  → base=None       size=None      ✓
```

### Canonical Selection

```python
# Standard sizes
variants = [
    ('aim-16x16', (16, 16)),
    ('aim-24x24', (24, 24)),
    ('aim-32x32', (32, 32)),
    ('aim-48x48', (48, 48)),
]
canonical = pick_canonical_variant(variants)
# Result: 'aim-32x32' ✓ (preferred size)

# Non-standard sizes (prefer largest)
variants = [
    ('icon-96x96', (96, 96)),
    ('icon-128x128', (128, 128)),
    ('icon-256x256', (256, 256)),
]
canonical = pick_canonical_variant(variants)
# Result: 'icon-256x256' ✓ (largest)
```

### CLI Integration

```bash
$ python3 iconics.py --help | grep variants
variants            Detect and manage icon size variants

$ python3 iconics.py variants --help
usage: iconics variants [-h] [--detect] [--bundle BASE_NAME] ...
```

## Known Test Icons

From `raw/` directory:

### aim (5 sizes)
- aim-16x16.png
- aim-24x24.png
- aim-32x32.png
- aim-48x48.png
- aim-256x256.png

### addthis (3 sizes)
- addthis-32x32.png
- addthis-48x48.png
- addthis-64x64.png

### accounting (2 sizes)
- accounting-16x16.png
- accounting-64x64.png

These can be used for testing the detection algorithm.

## Implementation Status

✓ Core variant detection with CLIP verification
✓ Regex pattern extraction (4 patterns)
✓ Canonical variant selection with priority
✓ VariantGroup dataclass with similarity matrix
✓ ZIP-based .imrb bundle creation
✓ Bundle reading with size extraction
✓ Terminal display formatting
✓ CLI integration with 3 modes
✓ Dedupe system integration functions
✓ Comprehensive error handling
✓ Catalog metadata merging
✓ Icon file resolution

## Future Enhancements

Potential improvements (not in current spec):

1. **Automatic variant generation**: Create missing sizes from existing variants
2. **Bundle extraction**: Extract specific sizes from .imrb files
3. **Smart bundling**: Auto-detect and bundle all variant groups in one command
4. **Variant recommendation**: Suggest which sizes are missing for completeness
5. **Size validation**: Check if actual file dimensions match claimed size in filename

## Notes

- Similarity threshold of 0.90 balances precision/recall for variants
- Lower threshold may include false positives (visually different icons with similar names)
- Higher threshold may miss legitimate variants (minor differences in rendering)
- The 32x32 preference aligns with common UI/web design standards
- Bundle format is extensible (version field for future changes)
- All functions handle missing icons gracefully (warn once, continue processing)
