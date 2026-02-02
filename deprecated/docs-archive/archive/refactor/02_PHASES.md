# IMPLEMENTATION PHASES

## Phase 1: Embedding Generation

Create `iconics_embeddings.py`:

```python
# Requirements:
# - Load icons from raw/ directory (PNG files)
# - Use CLIP ViT-B/32 (or ViT-L/14 for higher quality)
# - Generate embeddings for all icons
# - Store as numpy array + index mapping (icon_id -> row index)
# - Handle batching for memory efficiency
# - Normalize embeddings to unit sphere

# Output files:
# - embeddings/icon_embeddings.npy (n x 512 float32)
# - embeddings/icon_index.json (icon_id -> row mapping)
# - embeddings/metadata.json (model used, timestamp, icon count)
```

---

## Phase 2: Subspace Analysis

Create `iconics_subspace.py`:

```python
# Requirements:
# - Load icon embeddings
# - Compute SVD decomposition
# - Determine effective dimensionality (where singular values plateau)
# - Store basis vectors V_k for top-k components
# - Compute projection matrix P = V_k @ V_k.T

# Analysis outputs:
# - subspace/singular_values.npy (for scree plot)
# - subspace/basis_vectors.npy (d x k matrix, the V_k)
# - subspace/projection_matrix.npy (d x d matrix, optional for speed)
# - subspace/effective_dim.json (k value and selection criteria)

# Interpretability analysis:
# - For each principal component, find icons with highest/lowest loadings
# - Generate report: what semantic dimension does PC_i capture?
# - Correlate PCs with existing metadata (valence, abstraction, action_type)
# - Output: subspace/component_analysis.json
```

---

## Phase 3: Retrieval Engine

Create `iconics_retrieval.py`:

```python
class IconicsRetriever:
    """
    CLIP-based retrieval with subspace projection.
    
    Query modes:
    1. Text query: "icon for data protection"
    2. Image query: upload an image, find similar icons
    3. Icon query: given icon_id, find related icons
    4. Semantic axis query: "more abstract version of X"
    
    Retrieval modes:
    1. Raw CLIP similarity (baseline)
    2. Subspace-projected similarity (removes non-icon dimensions)
    3. Component-weighted similarity (weight by semantic axes)
    """
    
    def __init__(self, embeddings_path, subspace_path, model_name="ViT-B/32"):
        # Load embeddings, subspace basis, CLIP model
        pass
    
    def embed_text(self, query: str) -> np.ndarray:
        # CLIP text encoder
        pass
    
    def embed_image(self, image_path: str) -> np.ndarray:
        # CLIP vision encoder
        pass
    
    def project_to_iconics(self, q: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """
        Returns (q_projected, q_orthogonal)
        q_projected lives in iconics subspace
        q_orthogonal is the residual (measures "un-icon-ness")
        """
        pass
    
    def get_coordinates(self, q: np.ndarray) -> np.ndarray:
        """
        Returns coordinates in the icon semantic basis.
        These are interpretable: coordinate[i] = loading on PC_i
        """
        pass
    
    def retrieve(
        self, 
        query: str | np.ndarray,
        k: int = 10,
        mode: Literal["raw", "projected", "weighted"] = "projected",
        weights: np.ndarray | None = None,  # for component-weighted mode
        filter_fn: Callable | None = None,  # e.g., filter by category
    ) -> list[RetrievalResult]:
        """
        Returns top-k icons with scores and metadata.
        IMPORTANT: Always include residual_score in output for LLM consumption.
        """
        pass
    
    def traverse_axis(
        self,
        icon_id: str,
        axis: int,  # which PC to traverse
        steps: int = 5,
        direction: Literal["positive", "negative", "both"] = "both"
    ) -> list[str]:
        """
        Starting from icon, move along semantic axis.
        E.g., if axis=valence_pc, traverse from negative to positive icons.
        """
        pass
    
    def interpolate(self, icon_a: str, icon_b: str, steps: int = 5) -> list[str]:
        """
        Find icons along the geodesic between two icons in subspace.
        """
        pass
    
    def orthogonal_residual_score(self, query: str) -> float:
        """
        How "un-icon-like" is this query?
        High score = query asks for something icons can't represent.
        """
        pass
```

---

## Phase 4: Index Integration

Create `iconics_index.py`:

```python
# Requirements:
# - Build FAISS index for fast approximate nearest neighbor
# - Support both raw embeddings and projected embeddings
# - Enable filtered search (by category, style, size)
# - Incremental updates when new icons are added

# Index types to support:
# - Flat L2/IP (exact, for small datasets)
# - IVF (approximate, for scale)
# - HNSW (graph-based, good recall)

class IconicsIndex:
    def __init__(self, embeddings: np.ndarray, use_projection: bool = True):
        pass
    
    def search(self, query: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]:
        # Returns (indices, distances)
        pass
    
    def add(self, icon_id: str, embedding: np.ndarray):
        # Incremental add
        pass
    
    def save(self, path: str):
        pass
    
    def load(cls, path: str) -> "IconicsIndex":
        pass
```

---

## Phase 5: Correlation Analysis

Create `iconics_correlation.py`:

```python
# Requirements:
# - Load existing metadata from icon-catalog.json
# - Load subspace components
# - Compute correlation between:
#   - PC_i and emotional_valence
#   - PC_i and abstraction_level  
#   - PC_i and action_type (one-hot encoded)
#   - PC_i and category (one-hot encoded)
# - Identify which PCs correspond to which semantic features
# - Output interpretable mapping: {"valence_axis": 3, "abstraction_axis": 7, ...}

def analyze_component_semantics(
    embeddings: np.ndarray,
    basis: np.ndarray,
    metadata: dict,
) -> dict:
    """
    Returns mapping from semantic concepts to principal components.
    Also returns correlation strengths and p-values.
    """
    pass
```

---

## Phase 6: CLI Integration

Extend existing `icon-manager.py` with new commands:

```bash
# Generate embeddings
python icon-manager.py embed --model ViT-B/32 --batch-size 64

# Analyze subspace
python icon-manager.py analyze-subspace --components 50

# Query icons
python icon-manager.py query "danger confirmation action" --k 10 --mode projected

# Traverse semantic axis
python icon-manager.py traverse lock-icon --axis 3 --steps 5

# Evaluate retrieval quality
python icon-manager.py eval-retrieval --test-set ground_truth.json

# Compare with baseline
python icon-manager.py compare-methods --queries test_queries.txt
```

---

## Phase 7: Evaluation

Create `iconics_eval.py`:

```python
# Requirements:
# - Create ground truth test set (manual or from usage data)
# - Metrics: Precision@k, Recall@k, MRR, NDCG
# - Compare: raw CLIP vs projected vs current SemanticMatcher
# - Ablation: vary number of subspace components (k)
# - Qualitative: sample retrievals for human review

# Test query types:
# 1. Literal: "folder icon" (should find folders)
# 2. Conceptual: "data organization" (should find folders, databases, etc.)
# 3. Emotional: "friendly approval" (should find positive action icons)
# 4. Compositional: "warning about deletion" (combines concepts)
# 5. Negation: "lock but not security" (tests fine-grained distinction)
```

---

## Phase 8: LLM Integration (NEW)

Create `iconics_provision.py` and `iconics_emoji.py`:

```python
# iconics_provision.py
# Requirements:
# - Copy icons from master library to project directories
# - Generate and maintain manifest.json tracking provisioned icons
# - Support query-based provisioning (find + copy in one step)
# - Generate framework-specific import files (React, Vue, CSS)

class IconicsProvisioner:
    def __init__(self, source_path: str, catalog: dict):
        self.source = Path(source_path)
        self.catalog = catalog
    
    def provision(
        self,
        icon_ids: list[str],
        dest: str,
        update_manifest: bool = True
    ) -> dict:
        """
        Copy icons to destination, return manifest entry.
        """
        pass
    
    def provision_from_query(
        self,
        queries: list[str],
        dest: str,
        k: int = 2,
        retriever: IconicsRetriever = None
    ) -> dict:
        """
        Query for icons, then provision matches.
        """
        pass
    
    def provision_from_manifest(
        self,
        manifest_path: str,
        dest: str
    ) -> dict:
        """
        Read manifest, provision all listed icons.
        """
        pass
    
    def generate_imports(
        self,
        manifest_path: str,
        format: Literal["react", "vue", "css", "typescript"],
        output_path: str
    ):
        """
        Generate framework-specific import file.
        """
        pass


# iconics_emoji.py
# Requirements:
# - Scan files for emoji usage
# - Map emojis to semantic queries
# - Generate replacement suggestions
# - Apply conversions with dry-run support

class EmojiScanner:
    # Common emoji to query mapping
    EMOJI_MAP = {
        "🔒": "lock security",
        "🔐": "lock security private",
        "⚠️": "warning alert",
        "✅": "success check complete",
        "❌": "error close remove",
        "🚀": "launch speed rocket",
        "📁": "folder directory",
        "📂": "folder open",
        "📄": "document file",
        "📝": "document edit write",
        "⚙️": "settings config gear",
        "🔧": "settings tool wrench",
        "👤": "user profile person",
        "👥": "users group team",
        "🔔": "notification alert bell",
        "💳": "payment billing card",
        "🔍": "search find magnify",
        "➕": "add create plus",
        "🗑️": "delete trash remove",
        "📤": "upload export",
        "📥": "download import",
        "🔗": "link chain url",
        "📊": "chart analytics bar",
        "📈": "chart growth line",
        "⏱️": "time clock timer",
        "🕐": "time clock",
        "🏠": "home house",
        "💡": "idea tip lightbulb",
    }
    
    def scan(
        self,
        path: str,
        extensions: list[str] = ["md", "mdx", "tsx", "jsx", "html"],
        recursive: bool = True
    ) -> dict:
        """
        Scan files for emoji, return report with suggestions.
        """
        pass
    
    def convert(
        self,
        report: dict,
        icon_path: str,
        dry_run: bool = True
    ) -> dict:
        """
        Apply emoji-to-icon conversions.
        Returns diff of changes (or would-be changes if dry_run).
        """
        pass
```

### CLI Commands for Phase 8

```bash
# Batch query multiple concepts
python icon-manager.py batch-query --input concepts.txt --output results.json --k 2

# Provision icons to project
python icon-manager.py provision --icons lock-secure-24,user-circle-24 --dest ./assets/icons/
python icon-manager.py provision --manifest manifest.json --dest ./assets/icons/
python icon-manager.py provision --query "navigation menu home" --dest ./icons/ --k 2

# Scan for emoji usage
python icon-manager.py scan-emoji --path ./docs --extensions md,mdx --output emoji-report.json

# Convert emojis to icons
python icon-manager.py convert-emoji --report emoji-report.json --dry-run
python icon-manager.py convert-emoji --report emoji-report.json --icon-path assets/icons --apply

# Generate framework imports
python icon-manager.py generate-imports --manifest manifest.json --format react --output Icons.tsx
python icon-manager.py generate-imports --manifest manifest.json --format vue --output icons.ts
python icon-manager.py generate-imports --manifest manifest.json --format css --output icons.css
```

### Skill File Generation

Generate `skill/SKILL.md` for LLM consumption:

```python
def generate_skill_file(
    workspace: str,
    semantic_mapping: dict,
    emoji_map: dict
) -> str:
    """
    Generate the SKILL.md file that teaches LLMs how to use iconics.
    Includes:
    - Trigger conditions
    - Quick command reference
    - Emoji mapping table
    - Semantic axes
    - Decision tree
    """
    pass
```

---

## Phase Summary

| Phase | Focus | Key Deliverables |
|-------|-------|------------------|
| 1 | Embedding Generation | icon_embeddings.npy, icon_index.json |
| 2 | Subspace Analysis | basis_vectors.npy, semantic_mapping.json |
| 3 | Retrieval Engine | IconicsRetriever class |
| 4 | Index Integration | FAISS indices |
| 5 | Correlation Analysis | component_analysis.json |
| 6 | CLI Integration | Updated icon-manager.py |
| 7 | Evaluation | ground_truth.json, comparison results |
| 8 | LLM Integration | provision/emoji commands, SKILL.md |
