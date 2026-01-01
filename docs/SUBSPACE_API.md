# Iconics CLIP Vector Subspace - API Reference

## Overview

The Iconics subspace analysis modules provide mathematical tools for analyzing the latent semantic structure of icon embeddings using Singular Value Decomposition (SVD).

## Modules

### iconics_subspace.py

Core SVD analysis and projection operations.

#### Functions

##### `compute_svd(embeddings: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]`

Compute full SVD decomposition of embedding matrix.

**Args:**
- `embeddings`: Icon embedding matrix (n_icons, embedding_dim)

**Returns:**
- `U`: Left singular vectors (n_icons, n_icons)
- `S`: Singular values in descending order (min(n_icons, embedding_dim),)
- `Vt`: Right singular vectors transposed (embedding_dim, embedding_dim)

**Example:**
```python
embeddings = np.load("embeddings/icon_embeddings.npy")
U, S, Vt = compute_svd(embeddings)
```

---

##### `select_effective_dim(singular_values: np.ndarray, variance_threshold: float = 0.95) -> Tuple[int, Dict]`

Select effective dimensionality using explained variance criterion.

**Args:**
- `singular_values`: Singular values from SVD
- `variance_threshold`: Minimum variance to retain (default: 0.95)

**Returns:**
- `k`: Effective dimensionality
- `analysis`: Dictionary with variance analysis metadata

**Example:**
```python
k, analysis = select_effective_dim(S, variance_threshold=0.95)
print(f"Selected k={k}, explains {analysis['explained_variance_ratio']:.2%}")
```

---

##### `build_projection_matrix(Vt: np.ndarray, k: int) -> np.ndarray`

Build orthogonal projection matrix P = V_k V_k^T.

**Args:**
- `Vt`: Right singular vectors transposed (d, d)
- `k`: Number of dimensions to retain

**Returns:**
- `P`: Projection matrix (d, d)

**Mathematical Properties:**
- P is symmetric: P^T = P
- P is idempotent: P² = P
- rank(P) = k

**Example:**
```python
P = build_projection_matrix(Vt, k=166)
```

---

##### `project_to_subspace(q: np.ndarray, P: np.ndarray) -> Tuple[np.ndarray, np.ndarray]`

Project query vector onto icon subspace.

**Args:**
- `q`: Query vector (d,)
- `P`: Projection matrix (d, d)

**Returns:**
- `q_projected`: Component in subspace (d,)
- `q_orthogonal`: Component orthogonal to subspace (d,)

**Properties:**
- q = q_projected + q_orthogonal
- q_projected ⊥ q_orthogonal
- ||q||² = ||q_projected||² + ||q_orthogonal||²

**Example:**
```python
q_proj, q_orth = project_to_subspace(query, P)
in_subspace_variance = np.linalg.norm(q_proj)**2 / np.linalg.norm(query)**2
```

---

##### `get_coordinates(q: np.ndarray, Vt: np.ndarray, k: int) -> np.ndarray`

Get coordinates of query in principal component basis.

**Args:**
- `q`: Query vector (d,)
- `Vt`: Right singular vectors transposed (d, d)
- `k`: Number of dimensions

**Returns:**
- `coordinates`: PC loadings (k,)

**Example:**
```python
coords = get_coordinates(query, Vt, k=166)
top_pcs = np.argsort(np.abs(coords))[-5:][::-1]
```

---

##### `save_subspace(output_dir: Path, S: np.ndarray, Vt: np.ndarray, k: int, analysis: SubspaceAnalysis)`

Save subspace analysis to disk.

**Args:**
- `output_dir`: Output directory
- `S`: Singular values
- `Vt`: Right singular vectors
- `k`: Effective dimensionality
- `analysis`: SubspaceAnalysis object

**Creates:**
- `singular_values.npy`: All singular values
- `basis_vectors.npy`: First k basis vectors (V_k)
- `effective_dim.json`: Dimensionality metadata
- `component_analysis.json`: Icon loadings per component

---

##### `load_subspace(subspace_dir: Path) -> Tuple[np.ndarray, np.ndarray, int, Dict]`

Load subspace analysis from disk.

**Args:**
- `subspace_dir`: Directory with subspace artifacts

**Returns:**
- `S`: Singular values
- `V_k`: Basis vectors (d, k)
- `k`: Effective dimensionality
- `metadata`: Analysis metadata dictionary

**Example:**
```python
S, V_k, k, metadata = load_subspace("embeddings/subspace")
P = V_k @ V_k.T
```

---

### iconics_correlation.py

Metadata correlation analysis and semantic axis identification.

#### Functions

##### `load_catalog_metadata(catalog_path: Path) -> Dict[str, Dict]`

Load icon catalog and extract semantic metadata.

**Args:**
- `catalog_path`: Path to icon-catalog.json

**Returns:**
- Dictionary mapping icon_id to metadata with fields:
  - emotional_valence: float (-1 to 1)
  - abstraction_level: int (1-5)
  - category: str
  - metaphor: str
  - tags: List[str]

---

##### `align_metadata_with_embeddings(metadata: Dict, icon_index: Dict) -> Dict[str, np.ndarray]`

Align metadata with embedding matrix row order.

**Args:**
- `metadata`: Icon metadata dictionary
- `icon_index`: Mapping from icon_id to row index

**Returns:**
- Dictionary of aligned feature arrays:
  - emotional_valence: (n_icons,) array
  - abstraction_level: (n_icons,) array
  - category_encoded: (n_icons, n_categories) one-hot array
  - metaphor_encoded: (n_icons, n_metaphors) one-hot array

---

##### `correlate_with_metadata(U: np.ndarray, k: int, aligned_metadata: Dict, p_threshold: float = 0.01) -> Dict`

Compute correlations between PCs and metadata features.

**Args:**
- `U`: Left singular vectors (n_icons, n_components)
- `k`: Number of components to analyze
- `aligned_metadata`: Aligned metadata arrays
- `p_threshold`: Significance threshold

**Returns:**
- Dictionary with correlation results:
  - continuous: {feature_name: {correlations, p_values, significant_components}}
  - categorical: {feature_type: {category: {correlations, p_values, ...}}}

**Example:**
```python
correlations = correlate_with_metadata(U, k=166, aligned_metadata)
valence_cors = correlations['continuous']['emotional_valence']
```

---

##### `identify_semantic_axes(correlations: Dict, p_threshold: float = 0.01, min_correlation: float = 0.3) -> Dict[str, int]`

Identify PCs that serve as semantic axes.

**Args:**
- `correlations`: Correlation results
- `p_threshold`: Significance threshold
- `min_correlation`: Minimum |r| to consider

**Returns:**
- Dictionary mapping semantic feature to PC index:
  - "valence_axis": 3
  - "abstraction_axis": 7
  - etc.

**Example:**
```python
semantic_axes = identify_semantic_axes(correlations, min_correlation=0.10)
abstraction_pc = semantic_axes.get('abstraction_level_axis')
```

---

##### `analyze_and_save_correlations(...) -> Tuple[Dict[str, int], Dict]`

End-to-end correlation analysis pipeline.

**Args:**
- `embeddings_path`: Path to icon_embeddings.npy
- `index_path`: Path to icon_index.json
- `catalog_path`: Path to icon-catalog.json
- `subspace_dir`: Directory with SVD results
- `output_dir`: Directory to save results
- `p_threshold`: Significance threshold (default: 0.01)
- `min_correlation`: Minimum correlation (default: 0.3)

**Returns:**
- `semantic_axes`: Identified semantic axes
- `correlations`: Full correlation results

**Creates:**
- `semantic_axes.json`: Semantic axis mapping
- `correlation_analysis.json`: Full correlation results

---

## Complete Usage Example

```python
from pathlib import Path
import numpy as np
import json
from iconics_subspace import (
    compute_svd, select_effective_dim, build_projection_matrix,
    project_to_subspace, save_subspace, load_subspace
)
from iconics_correlation import analyze_and_save_correlations

# Paths
base_dir = Path("/home/zack/dev/iconics")
embeddings_path = base_dir / "embeddings" / "icon_embeddings.npy"
index_path = base_dir / "embeddings" / "icon_index.json"
output_dir = base_dir / "embeddings" / "subspace"

# Load embeddings
embeddings = np.load(embeddings_path)
with open(index_path) as f:
    icon_index = json.load(f)

# Compute SVD
U, S, Vt = compute_svd(embeddings)
k, analysis = select_effective_dim(S, variance_threshold=0.95)
print(f"Effective dimension: k={k}")

# Build projection
P = build_projection_matrix(Vt, k)

# Project a query
query = embeddings[0]
q_proj, q_orth = project_to_subspace(query, P)

# Compute variance in subspace
variance_ratio = np.linalg.norm(q_proj)**2 / np.linalg.norm(query)**2
print(f"Query variance in subspace: {variance_ratio:.2%}")

# Find nearest neighbors in subspace
all_proj = embeddings @ P
distances = np.linalg.norm(all_proj - q_proj[np.newaxis, :], axis=1)
nearest = np.argsort(distances)[:10]

# Run correlation analysis
semantic_axes, correlations = analyze_and_save_correlations(
    embeddings_path,
    index_path,
    base_dir / "icon-catalog.json",
    output_dir,
    output_dir
)

print(f"Identified {len(semantic_axes)} semantic axes")
```

## Data Structures

### SubspaceAnalysis (dataclass)

```python
@dataclass
class SubspaceAnalysis:
    effective_dim: int
    total_variance: float
    explained_variance_ratio: float
    variance_threshold: float
    elbow_point: Optional[int]
    component_correlations: Dict[str, List[Tuple[str, float]]]
```

## File Formats

### effective_dim.json
```json
{
  "effective_dim": 166,
  "total_variance": 7875.0,
  "explained_variance_ratio": 0.9504,
  "variance_threshold": 0.95,
  "elbow_point": 2
}
```

### semantic_axes.json
```json
{
  "abstraction_level_axis": 2,
  "ui_axis": 1,
  "files_axis": 6,
  "tools_axis": 10
}
```

### component_analysis.json
```json
{
  "component_0_top": [
    ["icon_id_1", 0.5],
    ["icon_id_2", 0.48],
    ...
  ],
  "component_0_bottom": [
    ["icon_id_3", -0.52],
    ...
  ]
}
```

## Mathematical Reference

### SVD Decomposition
```
X = U Σ V^T

where:
- X ∈ ℝ^(n×d): embedding matrix
- U ∈ ℝ^(n×n): left singular vectors (icon space)
- Σ ∈ ℝ^(n×d): diagonal matrix of singular values
- V ∈ ℝ^(d×d): right singular vectors (embedding space basis)
```

### Projection Matrix
```
P = V_k V_k^T

where:
- V_k: first k columns of V
- P ∈ ℝ^(d×d): symmetric, idempotent projection operator
- rank(P) = k
```

### Orthogonal Decomposition
```
q = Pq + (I - P)q = q_proj + q_orth

Properties:
- q_proj ⊥ q_orth
- ||q||² = ||q_proj||² + ||q_orth||²
```

### Variance Explained
```
explained_variance_ratio = Σᵢ₌₁ᵏ σᵢ² / Σⱼ₌₁ⁿ σⱼ²
```

## Testing

Run unit tests:
```bash
pytest tests/unit/test_subspace_unit.py -v
```

All 29 tests verify mathematical properties:
- SVD reconstruction accuracy
- Orthonormality of basis vectors
- Projection symmetry and idempotency
- Orthogonal decomposition correctness
- Pythagorean theorem
- Save/load round-trip consistency
