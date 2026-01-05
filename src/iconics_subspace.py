"""
Iconics CLIP Vector Subspace Analysis - SVD and Projection Module

This module implements the mathematical foundation for identifying and analyzing
the latent semantic subspace of icon embeddings using Singular Value Decomposition.

Mathematical Foundation:
    Given embedding matrix X ∈ ℝ^(n×d) where n=7875 icons, d=512 dimensions:

    SVD Decomposition: X = U Σ Vᵀ
    - U ∈ ℝ^(n×n): Left singular vectors (icon space)
    - Σ ∈ ℝ^(n×d): Diagonal matrix of singular values σ₁ ≥ σ₂ ≥ ... ≥ 0
    - V ∈ ℝ^(d×d): Right singular vectors (embedding space basis)

    The columns of V form an orthonormal basis for ℝ^d, ordered by importance.
    The icon subspace is spanned by the first k columns of V.

    Projection: P = V_k V_k^T where V_k ∈ ℝ^(d×k)
    - P is an orthogonal projection operator onto the k-dimensional subspace
    - For any query q ∈ ℝ^d: q = Pq + (I-P)q where Pq ⊥ (I-P)q
"""

from pathlib import Path
from typing import Tuple, Dict, List, Optional
import numpy as np
import json
from dataclasses import dataclass, asdict


@dataclass
class SubspaceAnalysis:
    """Container for subspace analysis results."""
    effective_dim: int
    total_variance: float
    explained_variance_ratio: float
    variance_threshold: float
    elbow_point: Optional[int]
    component_correlations: Dict[str, List[Tuple[str, float]]]  # PC -> [(icon_id, loading), ...]


def compute_svd(embeddings: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute Singular Value Decomposition of embedding matrix.

    Mathematical Details:
        X = U Σ Vᵀ
        - U: left singular vectors (n × n)
        - Σ: singular values in descending order
        - Vᵀ: right singular vectors transposed (d × d)

        Properties:
        - U^T U = I (orthonormal columns)
        - V^T V = I (orthonormal columns)
        - σ₁ ≥ σ₂ ≥ ... ≥ σ_min ≥ 0

    Args:
        embeddings: Icon embedding matrix of shape (n_icons, embedding_dim)
                   Typically (7875, 512) for CLIP embeddings

    Returns:
        Tuple of (U, S, Vt) where:
        - U: Left singular vectors (n_icons, n_icons)
        - S: Singular values in descending order (min(n_icons, embedding_dim),)
        - Vt: Right singular vectors transposed (embedding_dim, embedding_dim)

    Raises:
        ValueError: If embeddings is not a 2D array
        np.linalg.LinAlgError: If SVD computation fails
    """
    if embeddings.ndim != 2:
        raise ValueError(f"Expected 2D array, got shape {embeddings.shape}")

    # Compute full SVD
    # full_matrices=True ensures U is (n×n) and Vt is (d×d)
    U, S, Vt = np.linalg.svd(embeddings, full_matrices=True)

    # Verify mathematical properties
    assert U.shape[0] == embeddings.shape[0]  # n icons
    assert Vt.shape[0] == embeddings.shape[1]  # d dimensions
    assert S.shape[0] == min(embeddings.shape)
    assert np.all(S[:-1] >= S[1:]), "Singular values not in descending order"

    return U, S, Vt


def select_effective_dim(
    singular_values: np.ndarray,
    variance_threshold: float = 0.95
) -> Tuple[int, Dict[str, float]]:
    """
    Select effective dimensionality using explained variance criterion.

    The effective dimension k is chosen such that:
        Σᵢ₌₁ᵏ σᵢ² / Σⱼ₌₁ⁿ σⱼ² ≥ variance_threshold

    Also implements elbow detection as secondary criterion using
    the rate of change in explained variance.

    Args:
        singular_values: Array of singular values in descending order
        variance_threshold: Minimum proportion of variance to retain (default: 0.95)

    Returns:
        Tuple of (effective_dim, analysis_dict) where analysis_dict contains:
        - total_variance: Sum of squared singular values
        - explained_variance_ratio: Ratio at selected dimension
        - elbow_point: Dimension where rate of variance gain decreases
        - variance_per_component: Variance explained by each component
    """
    # Compute variance (squared singular values)
    variance = singular_values ** 2
    total_variance = np.sum(variance)

    # Compute cumulative explained variance ratio
    cumulative_variance = np.cumsum(variance)
    explained_variance_ratio = cumulative_variance / total_variance

    # Find dimension that meets variance threshold
    k_variance = np.searchsorted(explained_variance_ratio, variance_threshold) + 1

    # Elbow detection: find point of maximum curvature
    # Use second derivative of explained variance
    if len(explained_variance_ratio) >= 3:
        first_derivative = np.diff(explained_variance_ratio)
        second_derivative = np.diff(first_derivative)
        # Elbow is where second derivative is most negative (steepest decline in gain)
        elbow_point = int(np.argmin(second_derivative) + 2)  # +2 for double diff offset
    else:
        elbow_point = None

    analysis = {
        'total_variance': float(total_variance),
        'explained_variance_ratio': float(explained_variance_ratio[k_variance - 1]),
        'variance_threshold': variance_threshold,
        'elbow_point': elbow_point,
        'variance_per_component': variance[:k_variance].tolist()
    }

    return k_variance, analysis


def build_projection_matrix(Vt: np.ndarray, k: int) -> np.ndarray:
    """
    Build orthogonal projection matrix onto k-dimensional subspace.

    Mathematical Details:
        P = V_k V_k^T

        where V_k is the first k columns of V (equivalently, first k rows of Vᵀ transposed)

        Properties:
        - P is symmetric: P^T = P
        - P is idempotent: P² = P (projection property)
        - P is orthogonal projection: rank(P) = k
        - For any v: Pv is the component of v in the subspace

    Args:
        Vt: Right singular vectors transposed, shape (d, d)
        k: Number of dimensions to retain

    Returns:
        Projection matrix P of shape (d, d)

    Raises:
        ValueError: If k > rank(Vt)
    """
    if k > Vt.shape[0]:
        raise ValueError(f"k={k} exceeds embedding dimension {Vt.shape[0]}")

    # Extract first k rows of Vt, then transpose to get V_k
    # V_k has shape (d, k) - each column is a basis vector
    V_k = Vt[:k, :].T  # Transpose to get columns

    # P = V_k @ V_k.T
    P = V_k @ V_k.T

    # Verify projection properties
    assert P.shape[0] == P.shape[1] == Vt.shape[0]
    assert np.allclose(P, P.T), "Projection matrix not symmetric"

    return P


def project_to_subspace(
    q: np.ndarray,
    P: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Project query vector onto icon subspace and compute orthogonal component.

    Mathematical Details:
        q = q_proj + q_orth

        where:
        - q_proj = Pq (projection onto subspace)
        - q_orth = (I - P)q (orthogonal complement)
        - q_proj ⊥ q_orth (orthogonality: ⟨q_proj, q_orth⟩ = 0)
        - ||q||² = ||q_proj||² + ||q_orth||² (Pythagorean theorem)

    Args:
        q: Query vector of shape (d,)
        P: Projection matrix of shape (d, d)

    Returns:
        Tuple of (q_projected, q_orthogonal) both of shape (d,)

    Raises:
        ValueError: If dimensions don't match
    """
    if q.shape[0] != P.shape[0]:
        raise ValueError(f"Query dim {q.shape[0]} doesn't match projection {P.shape[0]}")

    q_projected = P @ q
    q_orthogonal = q - q_projected

    # Verify orthogonal decomposition
    original_norm_sq = np.sum(q ** 2)
    proj_norm_sq = np.sum(q_projected ** 2)
    orth_norm_sq = np.sum(q_orthogonal ** 2)

    # Pythagorean theorem should hold (with numerical tolerance)
    assert np.isclose(original_norm_sq, proj_norm_sq + orth_norm_sq, rtol=1e-5, atol=1e-6), \
        f"Pythagorean theorem violated: {original_norm_sq} != {proj_norm_sq} + {orth_norm_sq}"

    # Orthogonality check (relaxed tolerance for float32 precision)
    dot_product = np.dot(q_projected, q_orthogonal)
    assert np.abs(dot_product) < 1e-5, f"Components not orthogonal: dot={dot_product}"

    return q_projected, q_orthogonal


def get_coordinates(
    q: np.ndarray,
    Vt: np.ndarray,
    k: int
) -> np.ndarray:
    """
    Get coordinates of query vector in the icon subspace basis.

    Mathematical Details:
        coordinates = V_k^T q

        These are the loadings/coefficients of q when expressed in the
        principal component basis. The i-th coordinate represents how much
        q aligns with the i-th principal component.

        Reconstruction (approximate):
        q ≈ V_k @ coordinates = Σᵢ₌₁ᵏ coordinates[i] * V_k[:, i]

    Args:
        q: Query vector of shape (d,)
        Vt: Right singular vectors transposed, shape (d, d)
        k: Number of dimensions

    Returns:
        Coordinates in subspace basis, shape (k,)
    """
    if q.shape[0] != Vt.shape[1]:
        raise ValueError(f"Query dim {q.shape[0]} doesn't match Vt {Vt.shape[1]}")

    # V_k.T @ q = (Vt[:k, :]) @ q
    coordinates = Vt[:k, :] @ q

    return coordinates


def analyze_components(
    embeddings: np.ndarray,
    U: np.ndarray,
    k: int,
    icon_index: Dict[str, int],
    top_n: int = 10
) -> Dict[str, List[Tuple[str, float]]]:
    """
    Analyze principal components by finding icons with highest/lowest loadings.

    For each of the first k principal components, identifies the icons that
    load most strongly in the positive and negative directions. This reveals
    the semantic meaning of each component.

    Mathematical Details:
        U contains the icon loadings on each component.
        U[i, j] is the loading of icon i on principal component j.

        For component j:
        - Top icons: argmax_i U[i, j]
        - Bottom icons: argmin_i U[i, j]

    Args:
        embeddings: Icon embedding matrix (n_icons, d)
        U: Left singular vectors (n_icons, n_icons)
        k: Number of components to analyze
        icon_index: Mapping from icon_id to row index
        top_n: Number of top/bottom icons to return per component

    Returns:
        Dictionary mapping component index to list of (icon_id, loading) tuples
        Format: {
            "component_0_top": [(icon_id, loading), ...],
            "component_0_bottom": [(icon_id, loading), ...],
            ...
        }
    """
    # Create reverse index: row -> icon_id
    index_to_icon = {idx: icon_id for icon_id, idx in icon_index.items()}

    component_analysis = {}

    for i in range(k):
        # Get loadings for this component
        loadings = U[:, i]

        # Find top N positive loadings
        top_indices = np.argsort(loadings)[-top_n:][::-1]  # Descending order
        top_icons = [
            (index_to_icon[idx], float(loadings[idx]))
            for idx in top_indices
        ]

        # Find top N negative loadings (most negative)
        bottom_indices = np.argsort(loadings)[:top_n]
        bottom_icons = [
            (index_to_icon[idx], float(loadings[idx]))
            for idx in bottom_indices
        ]

        component_analysis[f"component_{i}_top"] = top_icons
        component_analysis[f"component_{i}_bottom"] = bottom_icons

    return component_analysis


def save_subspace(
    output_dir: Path,
    S: np.ndarray,
    Vt: np.ndarray,
    k: int,
    analysis: SubspaceAnalysis
) -> None:
    """
    Save subspace analysis results to disk.

    Creates a structured directory with all subspace artifacts:
    - singular_values.npy: All singular values
    - basis_vectors.npy: First k basis vectors (V_k)
    - effective_dim.json: Dimensionality selection metadata
    - component_analysis.json: Icon loadings per component

    Args:
        output_dir: Directory to save results
        S: Singular values
        Vt: Right singular vectors transposed
        k: Effective dimensionality
        analysis: SubspaceAnalysis object with metadata
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save singular values
    np.save(output_dir / "singular_values.npy", S)

    # Save basis vectors (V_k = first k rows of Vt, transposed)
    V_k = Vt[:k, :].T  # Shape: (d, k)
    np.save(output_dir / "basis_vectors.npy", V_k)

    # Save effective dimension metadata
    dim_metadata = {
        'effective_dim': int(analysis.effective_dim),
        'total_variance': float(analysis.total_variance),
        'explained_variance_ratio': float(analysis.explained_variance_ratio),
        'variance_threshold': float(analysis.variance_threshold),
        'elbow_point': int(analysis.elbow_point) if analysis.elbow_point is not None else None
    }
    with open(output_dir / "effective_dim.json", 'w') as f:
        json.dump(dim_metadata, f, indent=2)

    # Save component analysis
    with open(output_dir / "component_analysis.json", 'w') as f:
        json.dump(analysis.component_correlations, f, indent=2)

    print(f"Subspace saved to {output_dir}")
    print(f"  - Effective dimension: {k}")
    print(f"  - Explained variance: {analysis.explained_variance_ratio:.4f}")
    print(f"  - Total singular values: {len(S)}")


def load_subspace(
    subspace_dir: Path
) -> Tuple[np.ndarray, np.ndarray, int, Dict]:
    """
    Load subspace analysis results from disk.

    Args:
        subspace_dir: Directory containing subspace artifacts

    Returns:
        Tuple of (S, V_k, k, metadata) where:
        - S: Singular values
        - V_k: Basis vectors (d, k)
        - k: Effective dimensionality
        - metadata: Dictionary with analysis results

    Raises:
        FileNotFoundError: If required files are missing
    """
    subspace_dir = Path(subspace_dir)

    # Load singular values
    S = np.load(subspace_dir / "singular_values.npy")

    # Load basis vectors
    V_k = np.load(subspace_dir / "basis_vectors.npy")

    # Load metadata
    with open(subspace_dir / "effective_dim.json") as f:
        dim_metadata = json.load(f)

    with open(subspace_dir / "component_analysis.json") as f:
        component_analysis = json.load(f)

    k = dim_metadata['effective_dim']

    metadata = {
        **dim_metadata,
        'component_analysis': component_analysis
    }

    return S, V_k, k, metadata


def compute_and_save_subspace(
    embeddings_path: Path,
    index_path: Path,
    output_dir: Path,
    variance_threshold: float = 0.95
) -> SubspaceAnalysis:
    """
    End-to-end subspace computation and analysis pipeline.

    Args:
        embeddings_path: Path to icon_embeddings.npy
        index_path: Path to icon_index.json
        output_dir: Directory to save results
        variance_threshold: Minimum variance to retain (default: 0.95)

    Returns:
        SubspaceAnalysis object with complete analysis
    """
    # Load data
    print(f"Loading embeddings from {embeddings_path}")
    embeddings = np.load(embeddings_path)

    with open(index_path) as f:
        icon_index = json.load(f)

    print(f"Loaded {embeddings.shape[0]} icons with {embeddings.shape[1]}-d embeddings")

    # Compute SVD
    print("Computing SVD...")
    U, S, Vt = compute_svd(embeddings)
    print(f"SVD complete: U{U.shape}, S{S.shape}, Vt{Vt.shape}")

    # Select effective dimension
    print("Selecting effective dimensionality...")
    k, variance_analysis = select_effective_dim(S, variance_threshold)
    print(f"Selected k={k} (explains {variance_analysis['explained_variance_ratio']:.4f} variance)")

    # Analyze components
    print("Analyzing principal components...")
    component_correlations = analyze_components(embeddings, U, k, icon_index)
    print(f"Analyzed {k} components")

    # Create analysis object
    analysis = SubspaceAnalysis(
        effective_dim=k,
        total_variance=variance_analysis['total_variance'],
        explained_variance_ratio=variance_analysis['explained_variance_ratio'],
        variance_threshold=variance_threshold,
        elbow_point=variance_analysis['elbow_point'],
        component_correlations=component_correlations
    )

    # Save results
    save_subspace(output_dir, S, Vt, k, analysis)

    return analysis


if __name__ == "__main__":
    # Example usage
    from iconics_config import ICONICS_ROOT
    base_dir = ICONICS_ROOT
    embeddings_path = base_dir / "embeddings" / "icon_embeddings.npy"
    index_path = base_dir / "embeddings" / "icon_index.json"
    output_dir = base_dir / "embeddings" / "subspace"

    analysis = compute_and_save_subspace(
        embeddings_path,
        index_path,
        output_dir,
        variance_threshold=0.95
    )

    print("\nSubspace Analysis Complete!")
    print(f"Effective dimension: {analysis.effective_dim}")
    print(f"Explained variance: {analysis.explained_variance_ratio:.4f}")
    print(f"Elbow point: {analysis.elbow_point}")
