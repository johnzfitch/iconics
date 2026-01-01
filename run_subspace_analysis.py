#!/usr/bin/env python
"""
Run full subspace analysis on icon embeddings.

Performs SVD decomposition, selects effective dimensionality,
correlates with metadata, and saves all outputs.
"""

import sys
import json
from pathlib import Path
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from iconics_subspace import (
    compute_svd,
    select_effective_dim,
    analyze_components,
    save_subspace,
    SubspaceAnalysis
)
from iconics_correlation import (
    load_catalog_metadata,
    align_metadata_with_embeddings,
    correlate_with_metadata,
    identify_semantic_axes,
    save_semantic_mapping
)


def main():
    base_path = Path(__file__).parent
    embeddings_dir = base_path / "embeddings"
    subspace_dir = base_path / "subspace"

    print("=" * 60)
    print("ICONICS SUBSPACE ANALYSIS")
    print("=" * 60)

    # Load embeddings
    print("\n[1/6] Loading embeddings...")
    embeddings = np.load(embeddings_dir / "icon_embeddings.npy")
    with open(embeddings_dir / "icon_index.json") as f:
        icon_index = json.load(f)

    print(f"  Loaded {embeddings.shape[0]} embeddings of dimension {embeddings.shape[1]}")

    # Compute SVD
    print("\n[2/6] Computing SVD decomposition...")
    U, S, Vt = compute_svd(embeddings)
    print(f"  U shape: {U.shape}")
    print(f"  S shape: {S.shape}")
    print(f"  Vt shape: {Vt.shape}")
    print(f"  Top 10 singular values: {S[:10].round(2)}")

    # Select effective dimensionality
    print("\n[3/6] Selecting effective dimensionality...")
    k, analysis_metadata = select_effective_dim(S, variance_threshold=0.95)
    print(f"  Effective dimension k = {k}")
    print(f"  Explained variance: {analysis_metadata['explained_variance_ratio']:.4f}")
    print(f"  Compression: {embeddings.shape[1]} -> {k} ({k/embeddings.shape[1]*100:.1f}%)")

    # Analyze components
    print("\n[4/6] Analyzing component loadings...")
    component_analysis = analyze_components(
        embeddings=embeddings,
        U=U,
        k=k,
        icon_index=icon_index,
        top_n=10
    )
    print(f"  Analyzed {len(component_analysis)} components")

    # Build SubspaceAnalysis object
    analysis = SubspaceAnalysis(
        effective_dim=k,
        total_variance=float(np.sum(S ** 2)),
        explained_variance_ratio=analysis_metadata['explained_variance_ratio'],
        variance_threshold=0.95,
        elbow_point=analysis_metadata.get('elbow_point'),
        component_correlations=component_analysis
    )

    # Save subspace artifacts
    print("\n[5/6] Saving subspace artifacts...")
    save_subspace(subspace_dir, S, Vt, k, analysis)
    print(f"  Saved to {subspace_dir}/")

    # Correlation analysis with metadata
    print("\n[6/6] Running metadata correlation analysis...")
    catalog_path = base_path / "icon-catalog.json"

    try:
        metadata = load_catalog_metadata(catalog_path)
        aligned_metadata = align_metadata_with_embeddings(metadata, icon_index)

        # Correlate U (icon loadings) with metadata
        correlations = correlate_with_metadata(U, k, aligned_metadata)
        semantic_axes = identify_semantic_axes(correlations)

        save_semantic_mapping(subspace_dir, correlations, semantic_axes)

        print(f"  Found {len(semantic_axes)} semantic axes:")
        for feature, pc_data in list(semantic_axes.items())[:5]:
            pc_idx = pc_data['component']
            corr = pc_data['correlation']
            p = pc_data['p_value']
            print(f"    PC{pc_idx}: {feature} (r={corr:.3f}, p={p:.2e})")

    except Exception as e:
        import traceback
        print(f"  Warning: Correlation analysis failed: {e}")
        traceback.print_exc()
        print("  Subspace analysis complete without metadata correlations")

    # Summary
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)
    print(f"\nOutputs in {subspace_dir}/:")
    for f in subspace_dir.glob("*"):
        size = f.stat().st_size / 1024
        print(f"  {f.name}: {size:.1f} KB")

    print(f"\nKey metrics:")
    print(f"  - Icons: {embeddings.shape[0]}")
    print(f"  - Original dim: {embeddings.shape[1]}")
    print(f"  - Effective dim: {k}")
    print(f"  - Compression ratio: {embeddings.shape[1]/k:.1f}x")
    print(f"  - Explained variance: {analysis_metadata['explained_variance_ratio']*100:.1f}%")


if __name__ == "__main__":
    main()
