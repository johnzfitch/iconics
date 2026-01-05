# Iconics Parallel Agent Tasks

## Agent 1: Dedupe Detection System

### Context
Iconics icon library has 5,673+ icons with CLIP embeddings (512-dim, L2-normalized). Many icons are duplicates or near-duplicates. We need to find and manage them.

### Goal
Build `iconics dedupe` command that finds duplicate clusters using CLIP similarity.

### Requirements

#### CLI Interface
```bash
iconics dedupe                           # Find dupes, default threshold 0.95
iconics dedupe --threshold 0.90          # Lower threshold = more matches
iconics dedupe --dry-run                 # Preview only, no changes
iconics dedupe --interactive             # Prompt for each cluster
iconics dedupe --output dupes.json       # Export clusters to JSON
```

#### Output Format
```
Found 47 duplicate clusters (127 icons total)

Cluster 1 (3 icons, avg similarity: 0.97):
  → lock-16x16 (canonical candidate - most tags)
    lock-16x16-old
    lock-small

Cluster 2 (2 icons, avg similarity: 0.96):
  → folder-open-32x32 (canonical candidate - highest resolution)
    folder-open

Actions: [k]eep canonical, [m]erge metadata, [s]kip, [q]uit
```

#### Algorithm
```python
def find_duplicate_clusters(embeddings: np.ndarray, icon_ids: List[str], threshold: float = 0.95) -> List[DupeCluster]:
    """
    Find duplicate clusters using CLIP similarity.

    Approach:
    1. Compute pairwise similarities (or use FAISS for large N)
    2. Build graph where edge exists if sim > threshold
    3. Find connected components
    4. For each component, compute avg similarity and suggest canonical
    """
    # For 5673 icons, full pairwise is ~16M comparisons - manageable
    # But FAISS range_search is faster

    similarities = embeddings @ embeddings.T  # Cosine sim (normalized)

    # Build adjacency from similarities > threshold
    # Use scipy.sparse for efficiency
    from scipy.sparse import csr_matrix
    from scipy.sparse.csgraph import connected_components

    adj = (similarities > threshold).astype(int)
    np.fill_diagonal(adj, 0)  # No self-loops

    n_components, labels = connected_components(csr_matrix(adj))

    # Group by component, filter singletons
    clusters = []
    for comp_id in range(n_components):
        members = [icon_ids[i] for i, l in enumerate(labels) if l == comp_id]
        if len(members) > 1:
            # Compute cluster stats
            member_indices = [i for i, l in enumerate(labels) if l == comp_id]
            cluster_sims = similarities[np.ix_(member_indices, member_indices)]
            avg_sim = (cluster_sims.sum() - len(members)) / (len(members) * (len(members) - 1))

            clusters.append(DupeCluster(
                members=members,
                avg_similarity=avg_sim,
                suggested_canonical=pick_canonical(members)
            ))

    return sorted(clusters, key=lambda c: -len(c.members))

def pick_canonical(members: List[str]) -> str:
    """Pick best canonical from cluster."""
    # Heuristics:
    # 1. Highest resolution (parse WxH from name)
    # 2. Most metadata (tags, description)
    # 3. Shortest name (less likely to be variant)
    # 4. Most recently used
    ...
```

#### Data Structures
```python
@dataclass
class DupeCluster:
    members: List[str]           # All icon IDs in cluster
    avg_similarity: float        # Average pairwise CLIP similarity
    suggested_canonical: str     # Best candidate to keep

    def to_dict(self) -> dict:
        return asdict(self)
```

#### Merge Operation
```python
def merge_metadata(keep_id: str, remove_ids: List[str], catalog: IconCatalog):
    """Merge metadata from removed icons into keeper."""
    keep_entry = catalog.get_entry(keep_id)

    all_tags = set(keep_entry.get('tags', []))
    descriptions = [keep_entry.get('description', '')]

    for rid in remove_ids:
        entry = catalog.get_entry(rid)
        if entry:
            all_tags.update(entry.get('tags', []))
            if entry.get('description'):
                descriptions.append(entry['description'])

    # Update keeper with merged metadata
    keep_entry['tags'] = sorted(all_tags)
    keep_entry['description'] = descriptions[0]  # Keep longest or first
    keep_entry['merged_from'] = remove_ids  # Audit trail

    catalog.update_entry(keep_id, keep_entry)
```

### Files to Create/Modify
- **NEW:** `src/iconics_dedupe.py` — Core dedupe logic
- **MODIFY:** `iconics.py` — Add `dedupe` subcommand
- **MODIFY:** `src/iconics_executive.py` — Add IconCatalog.update_entry() if missing

### Testing
```bash
# Dry run to see clusters
iconics dedupe --threshold 0.95 --dry-run

# Export for analysis
iconics dedupe --threshold 0.95 --output /tmp/dupes.json
jq '.clusters | length' /tmp/dupes.json

# Interactive cleanup
iconics dedupe --threshold 0.97 --interactive
```

### Key Files Reference
- Embeddings: `embeddings/icon_embeddings.npy` shape (N, 512)
- Index: `embeddings/icon_index.json` {icon_id: index}
- Catalog: `icon-catalog.json`
- Retriever: `src/iconics_retrieval.py` (has embeddings loaded)

---

## Agent 2: Variant Grouping System

### Context
Iconics has icons at multiple resolutions: lock-16x16, lock-32x32, lock-64x64. These should be grouped as variants of a single concept. Builds on the dedupe system.

### Goal
Build `iconics variants` command that detects, displays, and bundles size variants.

### Requirements

#### CLI Interface
```bash
iconics variants lock                    # Show all variants of "lock"
iconics variants --detect                # Auto-detect all variant groups
iconics variants --detect --output groups.json
iconics variants --bundle lock           # Create lock.imrb multi-res bundle
iconics variants --bundle lock -o ./out/lock.imrb
```

#### Output Format
```
Variant Group: lock (4 sizes)
  Canonical: lock-32x32

  Size     Icon ID              Tags
  ─────────────────────────────────────
  16x16    lock-16x16           security, padlock
  24x24    lock-24x24           security, padlock, small
  32x32    lock-32x32 ★         security, padlock, auth
  64x64    lock-64x64           security, padlock, large

  CLIP Similarity Matrix:
          16x16  24x24  32x32  64x64
  16x16   1.000  0.982  0.971  0.945
  24x24   0.982  1.000  0.989  0.967
  32x32   0.971  0.989  1.000  0.984
  64x64   0.945  0.967  0.984  1.000
```

#### Detection Algorithm
```python
import re
from collections import defaultdict

SIZE_PATTERNS = [
    r'^(.+)-(\d+)x(\d+)$',           # name-WxH
    r'^(.+)_(\d+)x(\d+)$',           # name_WxH
    r'^(.+)-(\d+)x(\d+)-(.+)$',      # name-WxH-variant
    r'^(\d+)x(\d+)-(.+)$',           # WxH-name (reversed)
]

def extract_base_and_size(icon_id: str) -> Tuple[Optional[str], Optional[Tuple[int, int]]]:
    """Extract base name and size from icon ID."""
    for pattern in SIZE_PATTERNS:
        match = re.match(pattern, icon_id)
        if match:
            groups = match.groups()
            # Handle different pattern structures
            if pattern == SIZE_PATTERNS[3]:  # WxH-name
                return groups[2], (int(groups[0]), int(groups[1]))
            else:
                return groups[0], (int(groups[1]), int(groups[2]))
    return None, None

def detect_variant_groups(icon_ids: List[str], embeddings: np.ndarray,
                          similarity_threshold: float = 0.90) -> List[VariantGroup]:
    """
    Detect variant groups by:
    1. Name pattern matching (base-WxH)
    2. CLIP similarity verification (> threshold)
    """
    # Group by base name
    base_groups = defaultdict(list)
    for icon_id in icon_ids:
        base, size = extract_base_and_size(icon_id)
        if base and size:
            base_groups[base].append((icon_id, size))

    # Filter groups with multiple sizes
    variant_groups = []
    for base, variants in base_groups.items():
        if len(variants) < 2:
            continue

        # Verify with CLIP similarity
        variant_ids = [v[0] for v in variants]
        variant_indices = [icon_index[vid] for vid in variant_ids]
        variant_embeddings = embeddings[variant_indices]

        sim_matrix = variant_embeddings @ variant_embeddings.T
        avg_sim = (sim_matrix.sum() - len(variants)) / (len(variants) * (len(variants) - 1))

        if avg_sim >= similarity_threshold:
            variant_groups.append(VariantGroup(
                base_name=base,
                variants={vid: size for vid, size in variants},
                similarity_matrix=sim_matrix,
                canonical=pick_canonical_variant(variants)
            ))

    return sorted(variant_groups, key=lambda g: -len(g.variants))

def pick_canonical_variant(variants: List[Tuple[str, Tuple[int, int]]]) -> str:
    """Pick canonical variant (prefer 32x32, then largest, then most metadata)."""
    # Prefer common UI sizes: 32x32 > 24x24 > 48x48 > 16x16 > 64x64
    size_priority = {(32, 32): 0, (24, 24): 1, (48, 48): 2, (16, 16): 3, (64, 64): 4}
    return min(variants, key=lambda v: size_priority.get(v[1], 99))[0]
```

#### Multi-Resolution Bundle Format (.imrb)
```python
import zipfile
import json

def create_bundle(group: VariantGroup, icon_dir: Path, output_path: Path):
    """Create .imrb multi-resolution bundle (ZIP-based)."""
    manifest = {
        "format": "iconics-mrb-v1",
        "canonical": group.canonical,
        "base_name": group.base_name,
        "variants": {},
        "metadata": get_merged_metadata(group)
    }

    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for icon_id, (w, h) in group.variants.items():
            icon_path = find_icon_file(icon_id, icon_dir)
            if icon_path:
                size_key = f"{w}x{h}"
                manifest["variants"][size_key] = {
                    "original_id": icon_id,
                    "filename": f"{size_key}.png"
                }
                z.write(icon_path, f"{size_key}.png")

        z.writestr("manifest.json", json.dumps(manifest, indent=2))

    return output_path
```

#### Data Structures
```python
@dataclass
class VariantGroup:
    base_name: str                              # e.g., "lock"
    variants: Dict[str, Tuple[int, int]]        # {icon_id: (width, height)}
    similarity_matrix: np.ndarray               # Pairwise CLIP similarities
    canonical: str                              # Preferred variant ID

    @property
    def sizes(self) -> List[Tuple[int, int]]:
        return sorted(set(self.variants.values()))

    def get_variant(self, size: Tuple[int, int]) -> Optional[str]:
        for icon_id, s in self.variants.items():
            if s == size:
                return icon_id
        return None
```

### Files to Create/Modify
- **NEW:** `src/iconics_variants.py` — Variant detection and bundling
- **MODIFY:** `iconics.py` — Add `variants` subcommand

### Testing
```bash
# Detect all variant groups
iconics variants --detect

# Inspect specific group
iconics variants lock

# Create bundle
iconics variants --bundle lock -o /tmp/lock.imrb
```

### Integration with Dedupe
When running dedupe, exclude known variants from duplicate detection to avoid flagging intentional size variants as duplicates.

---

## Agent 3: Iconics TUI

### Context
Iconics is a CLI icon library manager. We're adding a TUI for visual browsing using Textual (Python) with terminal image rendering.

### Goal
Build `iconics tui` command that provides:
1. Visual icon grid with previews
2. Search with real-time filtering
3. Icon details panel
4. Keyboard navigation

### Stack
- **Textual** — Python TUI framework
- **term-image** — Terminal image rendering
- Protocol detection for Kitty/Sixel/iTerm2/halfblocks fallback

### Requirements

#### CLI Interface
```bash
iconics tui                    # Launch TUI
iconics tui --category ui      # Pre-filter to category
iconics tui --query "lock"     # Start with search
```

#### Layout
```
┌─────────────────────────────────────────────────────────────────┐
│ 🔍 Search: lock_                                          [?]   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────┐  ┌───────┐  ┌───────┐  ┌───────┐  ┌───────┐        │
│  │ 🔒    │  │ 🔒    │  │ 🔓    │  │ 🔐    │  │ 🔑    │        │
│  │       │  │       │  │       │  │       │  │       │        │
│  └───────┘  └───────┘  └───────┘  └───────┘  └───────┘        │
│  lock-16   lock-32   unlock-16  lock-key   key-16             │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│ lock-32x32                                    Category: security│
│ Tags: lock, padlock, security, auth, protection                 │
│ Description: A padlock icon for authentication and security...  │
│                                                                 │
│ [Enter] Use  [c] Copy path  [v] Variants  [d] Details  [q] Quit │
└─────────────────────────────────────────────────────────────────┘
```

#### Core App Structure
```python
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Static
from textual.containers import Container, Grid
from textual.binding import Binding
from textual import work

class IconicsApp(App):
    """Iconics TUI Application."""

    TITLE = "Iconics"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("/", "focus_search", "Search"),
        Binding("c", "copy_path", "Copy path"),
        Binding("enter", "use_icon", "Use"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Input(placeholder="Search icons...", id="search-box")
        yield Grid(id="icon-grid")
        yield Static(id="details-panel")
        yield Footer()

    @work(exclusive=True)
    async def do_search(self, query: str):
        """Search icons (runs in background worker)."""
        results = self.retriever.retrieve(query, k=50)
        self.update_grid(results)
```

#### Terminal Image Rendering
```python
from term_image.image import from_file

def render_icon(path: Path, width: int = 8) -> str:
    """Render icon using term-image with protocol auto-detection."""
    img = from_file(path)
    img.set_size(width=width)
    return str(img)
```

### Files to Create
- **NEW:** `src/iconics_tui.py` — Main TUI application
- **MODIFY:** `iconics.py` — Add `tui` subcommand

### Dependencies
```bash
pip install textual term-image
```

### Testing
```bash
# Basic launch
iconics tui

# With search
iconics tui --query "security lock"

# Debug mode
textual run --dev src/iconics_tui.py
```

### Keyboard Shortcuts
| Key | Action |
|-----|--------|
| `/` | Focus search |
| `↑↓←→` | Navigate grid |
| `Enter` | Use icon (export) |
| `c` | Copy path to clipboard |
| `q` | Quit |
