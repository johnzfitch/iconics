#!/usr/bin/env python3
"""
Demonstration of Iconics CLIP Vector Subspace Analysis

This script demonstrates:
1. Loading pre-computed SVD subspace
2. Projecting new queries onto the icon subspace
3. Analyzing query similarity using subspace coordinates
4. Identifying semantic axes from metadata correlations
"""

from pathlib import Path
import sys
import numpy as np
import json

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from iconics_subspace import (
    load_subspace,
    build_projection_matrix,
    project_to_subspace,
    get_coordinates
)
from iconics_correlation import load_catalog_metadata


def main():
    """Run subspace analysis demonstration."""
    base_dir = Path(__file__).parent.parent
    subspace_dir = base_dir / "embeddings" / "subspace"
    embeddings_path = base_dir / "embeddings" / "icon_embeddings.npy"
    index_path = base_dir / "embeddings" / "icon_index.json"
    catalog_path = base_dir / "icon-catalog.json"

    print("=" * 80)
    print("ICONICS CLIP VECTOR SUBSPACE DEMONSTRATION")
    print("=" * 80)
    print()

    # 1. Load subspace
    print("1. Loading pre-computed subspace...")
    S, V_k, k, metadata = load_subspace(subspace_dir)

    print(f"   Effective dimension: k = {k}")
    print(f"   Explained variance: {metadata['explained_variance_ratio']:.4f}")
    print(f"   Elbow point: PC{metadata['elbow_point']}")
    print()

    # 2. Load embeddings and index
    print("2. Loading embeddings and index...")
    embeddings = np.load(embeddings_path)
    with open(index_path) as f:
        icon_index = json.load(f)

    print(f"   Total icons: {embeddings.shape[0]}")
    print(f"   Embedding dimension: {embeddings.shape[1]}")
    print()

    # 3. Build projection matrix
    print("3. Building projection matrix...")
    # Reconstruct Vt from V_k
    Vt = V_k.T  # V_k is (d, k), so Vt_k is (k, d)

    # For full projection, we need full Vt. Let's use V_k directly
    P = V_k @ V_k.T  # This is the projection matrix
    print(f"   Projection matrix shape: {P.shape}")
    print()

    # 4. Select a random icon embedding as query
    print("4. Analyzing sample query...")
    sample_idx = 100
    reverse_index = {idx: icon_id for icon_id, idx in icon_index.items()}
    sample_icon_id = reverse_index[sample_idx]
    q = embeddings[sample_idx]

    print(f"   Query icon: {sample_icon_id}")
    print(f"   Original norm: {np.linalg.norm(q):.4f}")

    # Project onto subspace
    q_proj, q_orth = project_to_subspace(q, P)

    print(f"   Projected norm: {np.linalg.norm(q_proj):.4f}")
    print(f"   Orthogonal norm: {np.linalg.norm(q_orth):.4f}")
    print(f"   Variance in subspace: {np.linalg.norm(q_proj)**2 / np.linalg.norm(q)**2:.4f}")
    print()

    # 5. Get coordinates in PC basis
    print("5. Computing principal component coordinates...")
    # Need full Vt for coordinates. Reconstruct or compute
    U_full, S_full, Vt_full = np.linalg.svd(embeddings, full_matrices=True)

    coords = get_coordinates(q, Vt_full, k)
    print(f"   Coordinate shape: {coords.shape}")
    print(f"   Top 5 PC loadings:")
    top_5_indices = np.argsort(np.abs(coords))[-5:][::-1]
    for i, idx in enumerate(top_5_indices):
        print(f"     PC{idx}: {coords[idx]:+.6f}")
    print()

    # 6. Load semantic axes
    print("6. Loading semantic axes...")
    semantic_axes_path = subspace_dir / "semantic_axes.json"
    if semantic_axes_path.exists():
        with open(semantic_axes_path) as f:
            semantic_axes = json.load(f)

        print(f"   Found {len(semantic_axes)} semantic axes:")
        for axis_name, pc_idx in sorted(semantic_axes.items(), key=lambda x: x[1])[:5]:
            if pc_idx < k:
                loading = coords[pc_idx]
                print(f"     {axis_name:20s} (PC{pc_idx:2d}): {loading:+.6f}")
    print()

    # 7. Compare with nearest neighbors in subspace
    print("7. Finding nearest neighbors in subspace...")

    # Project all embeddings
    all_proj = embeddings @ P

    # Compute distances in subspace
    distances = np.linalg.norm(all_proj - q_proj[np.newaxis, :], axis=1)

    # Find top 10 nearest neighbors
    nearest_indices = np.argsort(distances)[:10]

    print(f"   Top 10 nearest neighbors in icon subspace:")
    for rank, idx in enumerate(nearest_indices, 1):
        icon_id = reverse_index[idx]
        dist = distances[idx]
        print(f"     {rank:2d}. {icon_id:50s} (distance: {dist:.6f})")
    print()

    # 8. Variance analysis
    print("8. Variance distribution analysis...")
    variance = S_full ** 2
    total_var = np.sum(variance)
    cumulative_var = np.cumsum(variance) / total_var

    print(f"   Total variance: {total_var:.2f}")
    print(f"   Variance explained by dimension:")
    for dim in [10, 50, 100, 166, 200, 300]:
        if dim <= len(cumulative_var):
            print(f"     k={dim:3d}: {cumulative_var[dim-1]:.4f}")
    print()

    # 9. Load and display metadata correlations
    print("9. Metadata correlation summary...")
    correlation_path = subspace_dir / "correlation_analysis.json"
    if correlation_path.exists():
        with open(correlation_path) as f:
            correlations = json.load(f)

        # Show continuous features
        print("   Continuous features (top 3 PCs):")
        for feature in ['emotional_valence', 'abstraction_level']:
            if feature in correlations['continuous']:
                data = correlations['continuous'][feature]
                sig_comps = data['significant_components'][:3]
                for comp_idx in sig_comps:
                    r = data['correlations'][comp_idx]
                    p = data['p_values'][comp_idx]
                    print(f"     {feature:20s} × PC{comp_idx:2d}: r={r:+.4f}, p={p:.2e}")

        print()

        # Show categorical features (top 5)
        print("   Categorical features (top 5 by correlation):")
        all_cat_cors = []
        for cat_type in ['category', 'metaphor']:
            if cat_type in correlations['categorical']:
                for cat_name, data in correlations['categorical'][cat_type].items():
                    if data['significant_components']:
                        comp_idx = data['significant_components'][0]
                        r = data['correlations'][comp_idx]
                        p = data['p_values'][comp_idx]
                        all_cat_cors.append((abs(r), cat_type, cat_name, comp_idx, r, p))

        all_cat_cors.sort(reverse=True)
        for _, cat_type, cat_name, comp_idx, r, p in all_cat_cors[:5]:
            print(f"     {cat_name:20s} × PC{comp_idx:2d}: r={r:+.4f}, p={p:.2e}")

    print()
    print("=" * 80)
    print("DEMONSTRATION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
