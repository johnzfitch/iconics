"""
Iconics CLIP Vector Subspace - Metadata Correlation Analysis

This module analyzes correlations between principal components and semantic metadata
to identify interpretable semantic axes within the icon embedding space.

Goal: Map mathematical dimensions (PCs) to human-interpretable semantic features
like emotional valence, abstraction level, category, and metaphor.
"""

from pathlib import Path
from typing import Dict, List, Tuple, Optional
import numpy as np
import json
from scipy import stats
from collections import defaultdict, Counter


def load_catalog_metadata(catalog_path: Path) -> Dict[str, Dict]:
    """
    Load icon catalog and extract semantic metadata.

    Args:
        catalog_path: Path to icon-catalog.json

    Returns:
        Dictionary mapping icon_id to metadata dict with fields:
        - emotional_valence: float (-1 to 1, negative to positive affect)
        - abstraction_level: int (1-5, concrete to abstract)
        - category: str (security, files, ui, etc.)
        - metaphor: str (protection, storage, navigation, etc.)
        - tags: List[str]
    """
    with open(catalog_path) as f:
        catalog_data = json.load(f)

    # Handle both formats: {"icons": [...]} or direct list
    if isinstance(catalog_data, dict) and "icons" in catalog_data:
        icons = catalog_data["icons"]
    elif isinstance(catalog_data, list):
        icons = catalog_data
    else:
        raise ValueError(f"Unexpected catalog format: {type(catalog_data)}")

    metadata = {}
    for icon in icons:
        icon_id = icon["id"]
        metadata[icon_id] = {
            "emotional_valence": icon.get("emotional_valence", 0.0),
            "abstraction_level": icon.get("abstraction_level", 3),
            "category": icon.get("category", "unknown"),
            "metaphor": icon.get("metaphor", "unknown"),
            "tags": icon.get("tags", [])
        }

    return metadata


def one_hot_encode_categorical(
    values: List[str]
) -> Tuple[np.ndarray, List[str]]:
    """
    One-hot encode categorical variables.

    Args:
        values: List of categorical values

    Returns:
        Tuple of (encoded_matrix, categories) where:
        - encoded_matrix: (n_samples, n_categories) binary matrix
        - categories: List of unique category names
    """
    unique_categories = sorted(set(values))
    category_to_idx = {cat: i for i, cat in enumerate(unique_categories)}

    n_samples = len(values)
    n_categories = len(unique_categories)

    encoded = np.zeros((n_samples, n_categories), dtype=np.float32)
    for i, val in enumerate(values):
        encoded[i, category_to_idx[val]] = 1.0

    return encoded, unique_categories


def align_metadata_with_embeddings(
    metadata: Dict[str, Dict],
    icon_index: Dict[str, int]
) -> Dict[str, np.ndarray]:
    """
    Align metadata with embedding matrix row order.

    Args:
        metadata: Icon metadata dictionary
        icon_index: Mapping from icon_id to embedding row index

    Returns:
        Dictionary of aligned feature arrays:
        - emotional_valence: (n_icons,) float array
        - abstraction_level: (n_icons,) float array
        - category_encoded: (n_icons, n_categories) one-hot array
        - metaphor_encoded: (n_icons, n_metaphors) one-hot array
        - category_names: List of category names
        - metaphor_names: List of metaphor names
    """
    n_icons = len(icon_index)

    # Initialize arrays
    emotional_valence = np.zeros(n_icons, dtype=np.float32)
    abstraction_level = np.zeros(n_icons, dtype=np.float32)
    categories = []
    metaphors = []

    # Create reverse index
    index_to_icon = {idx: icon_id for icon_id, idx in icon_index.items()}

    # Collect values in row order
    for idx in range(n_icons):
        icon_id = index_to_icon[idx]

        if icon_id in metadata:
            meta = metadata[icon_id]
            emotional_valence[idx] = meta["emotional_valence"]
            abstraction_level[idx] = meta["abstraction_level"]
            categories.append(meta["category"])
            metaphors.append(meta["metaphor"])
        else:
            # Default values for missing metadata
            emotional_valence[idx] = 0.0
            abstraction_level[idx] = 3.0
            categories.append("unknown")
            metaphors.append("unknown")

    # One-hot encode categorical variables
    category_encoded, category_names = one_hot_encode_categorical(categories)
    metaphor_encoded, metaphor_names = one_hot_encode_categorical(metaphors)

    return {
        "emotional_valence": emotional_valence,
        "abstraction_level": abstraction_level,
        "category_encoded": category_encoded,
        "category_names": category_names,
        "metaphor_encoded": metaphor_encoded,
        "metaphor_names": metaphor_names,
        "categories": categories,  # Keep original for reference
        "metaphors": metaphors
    }


def correlate_with_metadata(
    U: np.ndarray,
    k: int,
    aligned_metadata: Dict[str, np.ndarray],
    p_threshold: float = 0.01
) -> Dict[str, Dict]:
    """
    Compute correlations between principal components and metadata features.

    For continuous features (valence, abstraction), computes Pearson correlation.
    For categorical features (category, metaphor), computes point-biserial correlation
    for each category.

    Args:
        U: Left singular vectors (n_icons, n_components), icon loadings on PCs
        k: Number of components to analyze
        aligned_metadata: Aligned metadata arrays from align_metadata_with_embeddings
        p_threshold: Significance threshold for correlations (default: 0.01)

    Returns:
        Dictionary with correlation results:
        {
            "continuous": {
                "emotional_valence": {
                    "correlations": [r_0, r_1, ..., r_k],
                    "p_values": [p_0, p_1, ..., p_k],
                    "significant_components": [i where p < threshold]
                },
                "abstraction_level": {...}
            },
            "categorical": {
                "category": {
                    "category_name_1": {
                        "correlations": [...],
                        "p_values": [...],
                        "significant_components": [...]
                    },
                    ...
                },
                "metaphor": {...}
            }
        }
    """
    correlations = {
        "continuous": {},
        "categorical": {}
    }

    # Continuous features: emotional valence and abstraction level
    for feature_name in ["emotional_valence", "abstraction_level"]:
        feature_values = aligned_metadata[feature_name]

        cors = []
        p_vals = []

        for i in range(k):
            component_loadings = U[:, i]
            r, p = stats.pearsonr(component_loadings, feature_values)
            cors.append(float(r))
            p_vals.append(float(p))

        significant = [i for i, p in enumerate(p_vals) if p < p_threshold]

        correlations["continuous"][feature_name] = {
            "correlations": cors,
            "p_values": p_vals,
            "significant_components": significant
        }

    # Categorical features: category and metaphor
    for feature_name in ["category", "metaphor"]:
        encoded_name = f"{feature_name}_encoded"
        names_key = f"{feature_name}_names"

        encoded_matrix = aligned_metadata[encoded_name]
        category_names = aligned_metadata[names_key]

        correlations["categorical"][feature_name] = {}

        for cat_idx, cat_name in enumerate(category_names):
            category_membership = encoded_matrix[:, cat_idx]

            cors = []
            p_vals = []

            for i in range(k):
                component_loadings = U[:, i]
                # Point-biserial correlation (special case of Pearson for binary variable)
                r, p = stats.pearsonr(component_loadings, category_membership)
                cors.append(float(r))
                p_vals.append(float(p))

            significant = [i for i, p in enumerate(p_vals) if p < p_threshold]

            correlations["categorical"][feature_name][cat_name] = {
                "correlations": cors,
                "p_values": p_vals,
                "significant_components": significant
            }

    return correlations


def identify_semantic_axes(
    correlations: Dict[str, Dict],
    p_threshold: float = 0.01,
    min_correlation: float = 0.3
) -> Dict[str, int]:
    """
    Identify principal components that serve as semantic axes.

    A PC is considered a semantic axis if it has:
    1. Significant correlation (p < p_threshold)
    2. Strong correlation magnitude (|r| > min_correlation)

    Args:
        correlations: Correlation results from correlate_with_metadata
        p_threshold: Significance threshold
        min_correlation: Minimum absolute correlation to consider

    Returns:
        Dictionary mapping semantic feature to primary PC index:
        {
            "valence_axis": 3,
            "abstraction_axis": 7,
            "security_axis": 12,
            ...
        }
    """
    semantic_axes = {}

    # Continuous features
    for feature_name, data in correlations["continuous"].items():
        cors = np.array(data["correlations"])
        p_vals = np.array(data["p_values"])

        # Find PC with strongest significant correlation
        significant_mask = p_vals < p_threshold
        strong_mask = np.abs(cors) > min_correlation
        valid_mask = significant_mask & strong_mask

        if np.any(valid_mask):
            valid_cors = np.abs(cors[valid_mask])
            valid_indices = np.where(valid_mask)[0]
            strongest_idx = valid_indices[np.argmax(valid_cors)]

            axis_name = f"{feature_name}_axis"
            semantic_axes[axis_name] = int(strongest_idx)

    # Categorical features - find dominant PC for each category
    for feature_type, categories in correlations["categorical"].items():
        for category_name, data in categories.items():
            cors = np.array(data["correlations"])
            p_vals = np.array(data["p_values"])

            significant_mask = p_vals < p_threshold
            strong_mask = np.abs(cors) > min_correlation
            valid_mask = significant_mask & strong_mask

            if np.any(valid_mask):
                valid_cors = np.abs(cors[valid_mask])
                valid_indices = np.where(valid_mask)[0]
                strongest_idx = valid_indices[np.argmax(valid_cors)]

                # Create axis name from category
                axis_name = f"{category_name}_axis"
                semantic_axes[axis_name] = int(strongest_idx)

    return semantic_axes


def generate_correlation_summary(
    correlations: Dict[str, Dict],
    semantic_axes: Dict[str, int],
    k: int
) -> str:
    """
    Generate human-readable summary of correlation analysis.

    Args:
        correlations: Correlation results
        semantic_axes: Identified semantic axes
        k: Number of components analyzed

    Returns:
        Formatted text summary
    """
    lines = []
    lines.append("=" * 80)
    lines.append("SEMANTIC AXIS ANALYSIS")
    lines.append("=" * 80)
    lines.append("")

    lines.append(f"Analyzed {k} principal components")
    lines.append(f"Identified {len(semantic_axes)} semantic axes")
    lines.append("")

    # Continuous features
    lines.append("Continuous Features:")
    lines.append("-" * 80)
    for feature_name, data in correlations["continuous"].items():
        significant = data["significant_components"]
        if significant:
            lines.append(f"\n{feature_name}:")
            for comp_idx in significant[:5]:  # Top 5
                r = data["correlations"][comp_idx]
                p = data["p_values"][comp_idx]
                lines.append(f"  PC{comp_idx}: r={r:+.4f}, p={p:.4e}")

    lines.append("")
    lines.append("Categorical Features:")
    lines.append("-" * 80)

    # Categorical features - show most significant
    for feature_type, categories in correlations["categorical"].items():
        lines.append(f"\n{feature_type}:")
        for category_name, data in sorted(
            categories.items(),
            key=lambda x: -max(np.abs(x[1]["correlations"]))
        )[:10]:  # Top 10 categories
            significant = data["significant_components"]
            if significant:
                comp_idx = significant[0]
                r = data["correlations"][comp_idx]
                p = data["p_values"][comp_idx]
                lines.append(f"  {category_name}: PC{comp_idx} r={r:+.4f}, p={p:.4e}")

    lines.append("")
    lines.append("=" * 80)
    lines.append("IDENTIFIED SEMANTIC AXES")
    lines.append("=" * 80)
    for axis_name, pc_idx in sorted(semantic_axes.items(), key=lambda x: x[1]):
        lines.append(f"{axis_name}: PC{pc_idx}")

    lines.append("")
    return "\n".join(lines)


def save_semantic_mapping(
    output_dir: Path,
    semantic_axes: Dict[str, int],
    correlations: Dict[str, Dict]
) -> None:
    """
    Save semantic mapping results to disk.

    Args:
        output_dir: Directory to save results
        semantic_axes: Identified semantic axes
        correlations: Full correlation results
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save semantic axes mapping
    with open(output_dir / "semantic_axes.json", 'w') as f:
        json.dump(semantic_axes, f, indent=2)

    # Save full correlation results
    with open(output_dir / "correlation_analysis.json", 'w') as f:
        json.dump(correlations, f, indent=2)

    print(f"Semantic mapping saved to {output_dir}")
    print(f"  - Identified {len(semantic_axes)} semantic axes")


def analyze_and_save_correlations(
    embeddings_path: Path,
    index_path: Path,
    catalog_path: Path,
    subspace_dir: Path,
    output_dir: Path,
    p_threshold: float = 0.01,
    min_correlation: float = 0.3
) -> Tuple[Dict[str, int], Dict[str, Dict]]:
    """
    End-to-end correlation analysis pipeline.

    Args:
        embeddings_path: Path to icon_embeddings.npy
        index_path: Path to icon_index.json
        catalog_path: Path to icon-catalog.json
        subspace_dir: Directory with SVD results
        output_dir: Directory to save correlation results
        p_threshold: Significance threshold
        min_correlation: Minimum correlation magnitude

    Returns:
        Tuple of (semantic_axes, correlations)
    """
    # Load data
    print(f"Loading embeddings and metadata...")
    embeddings = np.load(embeddings_path)

    with open(index_path) as f:
        icon_index = json.load(f)

    metadata = load_catalog_metadata(catalog_path)
    print(f"Loaded metadata for {len(metadata)} icons")

    # Load SVD results
    print(f"Loading SVD results from {subspace_dir}...")
    from iconics_subspace import load_subspace

    S, V_k, k, subspace_metadata = load_subspace(subspace_dir)
    print(f"Loaded subspace with k={k} dimensions")

    # Need to recompute U or load it
    # For now, recompute from embeddings
    print("Recomputing U (icon loadings)...")
    U_full, _, _ = np.linalg.svd(embeddings, full_matrices=False)
    U = U_full[:, :k]

    # Align metadata
    print("Aligning metadata with embeddings...")
    aligned_metadata = align_metadata_with_embeddings(metadata, icon_index)

    # Compute correlations
    print("Computing correlations...")
    correlations = correlate_with_metadata(U, k, aligned_metadata, p_threshold)

    # Identify semantic axes
    print("Identifying semantic axes...")
    semantic_axes = identify_semantic_axes(correlations, p_threshold, min_correlation)

    # Generate summary
    summary = generate_correlation_summary(correlations, semantic_axes, k)
    print(summary)

    # Save results
    save_semantic_mapping(output_dir, semantic_axes, correlations)

    return semantic_axes, correlations


if __name__ == "__main__":
    # Example usage
    from iconics_config import ICONICS_ROOT
    base_dir = ICONICS_ROOT
    embeddings_path = base_dir / "embeddings" / "icon_embeddings.npy"
    index_path = base_dir / "embeddings" / "icon_index.json"
    catalog_path = base_dir / "icon-catalog.json"
    subspace_dir = base_dir / "embeddings" / "subspace"
    output_dir = subspace_dir  # Save correlation results alongside subspace

    # Use lower threshold for icon embeddings (correlations are typically weaker)
    semantic_axes, correlations = analyze_and_save_correlations(
        embeddings_path,
        index_path,
        catalog_path,
        subspace_dir,
        output_dir,
        p_threshold=0.001,  # More stringent p-value
        min_correlation=0.10  # Lower correlation threshold for real data
    )

    print("\nCorrelation Analysis Complete!")
    print(f"Identified {len(semantic_axes)} semantic axes")
