"""
Iconics CLIP-based Retrieval Engine

This module implements the core retrieval functionality for the Iconics vector
search system. It combines CLIP embeddings with subspace projection for semantic
icon retrieval.

Key Features:
    - Text query: Natural language descriptions mapped to icon space
    - Image query: Find icons similar to a reference image
    - Icon query: Find related icons given an existing icon
    - Subspace projection: Query vectors projected to icon-specific subspace
    - Residual scoring: Measure how well a query fits the icon space

Mathematical Foundation:
    Given query q in R^d and icon subspace V_k (spanned by first k PCs):

    Projection: q_proj = V_k @ V_k^T @ q
    Residual: q_orth = q - q_proj

    Residual score = ||q_orth|| / ||q||
    - Low residual: Query well-represented by icon space
    - High residual: Query concept outside icon space

Retrieval Modes:
    1. "raw": Direct cosine similarity in CLIP space
    2. "projected": Project query to icon subspace first
    3. "weighted": Apply PC weights for semantic emphasis
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Literal, Optional, Tuple, Union

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """
    Container for a single retrieval result.

    Attributes:
        icon_id: Unique identifier for the icon
        score: Similarity score (higher is more similar)
        residual_score: Fraction of query orthogonal to icon space.
                       Always included. Range [0, 1].
                       - 0: Query fully in icon space
                       - 1: Query fully orthogonal to icon space
        coordinates: Optional PC coordinates of this icon in subspace.
                    Shape (k,) if provided.
    """
    icon_id: str
    score: float
    residual_score: float  # CRITICAL: Always required
    coordinates: Optional[np.ndarray] = field(default=None, repr=False)

    def __post_init__(self):
        """Validate residual_score is always present."""
        if self.residual_score is None:
            raise ValueError("residual_score must always be provided")

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        result = {
            "icon_id": self.icon_id,
            "score": float(self.score),
            "residual_score": float(self.residual_score)
        }
        if self.coordinates is not None:
            result["coordinates"] = self.coordinates.tolist()
        return result


class IconicsRetriever:
    """
    CLIP-based icon retrieval with subspace projection.

    This class provides the main retrieval interface for the Iconics system.
    It supports multiple query modes (text, image, icon) and retrieval modes
    (raw, projected, weighted).

    The retriever loads pre-computed embeddings and subspace data, and optionally
    a FAISS index for fast search. CLIP model is loaded lazily on first use.

    Attributes:
        embeddings: Icon embedding matrix (n_icons, d)
        icon_ids: List of icon identifiers
        V_k: Subspace basis vectors (d, k)
        k: Effective subspace dimension
        projection_matrix: P = V_k @ V_k^T for projection
        singular_values: Singular values from SVD

    Example:
        >>> retriever = IconicsRetriever(
        ...     embeddings_path="embeddings",
        ...     subspace_path="subspace"
        ... )
        >>>
        >>> # Text query
        >>> results = retriever.retrieve("security lock icon", k=10)
        >>> for r in results:
        ...     print(f"{r.icon_id}: {r.score:.4f} (residual: {r.residual_score:.4f})")
        >>>
        >>> # Find related icons
        >>> related = retriever.retrieve_by_icon("lock", k=5)
    """

    def __init__(
        self,
        embeddings_path: str,
        subspace_path: str,
        index_path: Optional[str] = None,
        model_name: str = "ViT-B-32"
    ):
        """
        Initialize retriever with embeddings and subspace data.

        Args:
            embeddings_path: Directory containing icon_embeddings.npy and icon_index.json
            subspace_path: Directory containing basis_vectors.npy, effective_dim.json,
                          and singular_values.npy
            index_path: Optional path to pre-built FAISS index (.faiss file).
                       If None, builds index on initialization.
            model_name: CLIP model architecture for query embedding.
                       Default "ViT-B-32" matches pre-computed embeddings.
        """
        embeddings_path = Path(embeddings_path)
        subspace_path = Path(subspace_path)

        # Load embeddings
        embeddings_file = embeddings_path / "icon_embeddings.npy"
        index_file = embeddings_path / "icon_index.json"

        if not embeddings_file.exists():
            raise FileNotFoundError(f"Embeddings not found: {embeddings_file}")
        if not index_file.exists():
            raise FileNotFoundError(f"Index not found: {index_file}")

        self.embeddings = np.load(embeddings_file).astype(np.float32)
        with open(index_file) as f:
            icon_index = json.load(f)

        # Create ordered icon_ids list (sorted by row index)
        self.icon_index = icon_index
        self._index_to_icon = {v: k for k, v in icon_index.items()}
        self.icon_ids = [self._index_to_icon[i] for i in range(len(icon_index))]

        logger.info(f"Loaded {len(self.icon_ids)} icon embeddings, shape {self.embeddings.shape}")

        # Load subspace
        basis_file = subspace_path / "basis_vectors.npy"
        dim_file = subspace_path / "effective_dim.json"
        sv_file = subspace_path / "singular_values.npy"

        if not basis_file.exists():
            raise FileNotFoundError(f"Basis vectors not found: {basis_file}")
        if not dim_file.exists():
            raise FileNotFoundError(f"Effective dim not found: {dim_file}")

        self.V_k = np.load(basis_file).astype(np.float32)  # Shape (d, k)
        with open(dim_file) as f:
            dim_metadata = json.load(f)
        self.k = dim_metadata["effective_dim"]

        # Load singular values if available
        if sv_file.exists():
            self.singular_values = np.load(sv_file).astype(np.float32)
        else:
            self.singular_values = None

        # Build projection matrix: P = V_k @ V_k^T
        self.projection_matrix = self.V_k @ self.V_k.T

        logger.info(f"Loaded subspace: k={self.k}, basis shape {self.V_k.shape}")

        # Build or load FAISS index
        self._build_faiss_index(index_path)

        # Lazy-load CLIP model
        self.model_name = model_name
        self._model = None
        self._preprocess = None
        self._tokenizer = None
        self._device = None

    def _build_faiss_index(self, index_path: Optional[str] = None) -> None:
        """Build or load FAISS index for fast search."""
        from iconics_index import IconicsIndex

        if index_path is not None:
            index_path = Path(index_path)
            if index_path.exists():
                self.faiss_index = IconicsIndex.load(str(index_path), self.icon_ids)
                logger.info(f"Loaded FAISS index from {index_path}")
                return

        # Build index from embeddings
        self.faiss_index = IconicsIndex(
            self.embeddings,
            self.icon_ids,
            use_projection=False
        )
        logger.info("Built FAISS index from embeddings")

    def _ensure_model_loaded(self) -> None:
        """Lazy-load CLIP model on first use."""
        if self._model is not None:
            return

        from iconics_embeddings import load_clip_model

        logger.info(f"Loading CLIP model: {self.model_name}")
        self._model, self._preprocess, self._tokenizer = load_clip_model(
            model_name=self.model_name
        )

        import torch
        self._device = "cuda" if torch.cuda.is_available() else "cpu"

    def embed_query(self, query: Union[str, np.ndarray]) -> np.ndarray:
        """
        Embed text query or return array if already embedded.

        Args:
            query: Either a text string to embed, or a pre-computed
                  embedding array of shape (d,) or (1, d)

        Returns:
            Normalized embedding vector of shape (d,)
        """
        if isinstance(query, np.ndarray):
            # Already embedded, just normalize shape
            if query.ndim == 2:
                query = query.flatten()
            return query.astype(np.float32)

        # Text query - need to embed
        self._ensure_model_loaded()

        from iconics_embeddings import embed_text

        embedding = embed_text(query, self._model, self._tokenizer, self._device)
        return embedding.flatten().astype(np.float32)

    def embed_image(self, image_path: Union[str, Path]) -> np.ndarray:
        """
        Embed image through CLIP vision encoder.

        Args:
            image_path: Path to image file

        Returns:
            Normalized embedding vector of shape (d,)
        """
        self._ensure_model_loaded()

        from iconics_embeddings import embed_image

        image_path = Path(image_path)
        embedding = embed_image(image_path, self._model, self._preprocess, self._device)
        return embedding.flatten().astype(np.float32)

    def project_to_iconics(self, q: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Project query to icon subspace and compute orthogonal residual.

        Mathematical Details:
            q = q_projected + q_orthogonal

            where:
            - q_projected = P @ q = V_k @ V_k^T @ q (projection onto icon subspace)
            - q_orthogonal = q - q_projected (residual outside icon space)
            - q_projected perpendicular to q_orthogonal

            Pythagorean theorem holds:
            ||q||^2 = ||q_projected||^2 + ||q_orthogonal||^2

        Args:
            q: Query vector of shape (d,)

        Returns:
            Tuple of (q_projected, q_orthogonal) where:
            - q_projected: Component in icon subspace, shape (d,)
            - q_orthogonal: Residual outside icon subspace, shape (d,)

        Raises:
            ValueError: If query dimension doesn't match embedding dimension
        """
        q = q.flatten().astype(np.float32)

        if q.shape[0] != self.projection_matrix.shape[0]:
            raise ValueError(
                f"Query dim ({q.shape[0]}) != embedding dim ({self.projection_matrix.shape[0]})"
            )

        # Projection: P @ q
        q_projected = self.projection_matrix @ q

        # Orthogonal residual
        q_orthogonal = q - q_projected

        return q_projected, q_orthogonal

    def get_coordinates(self, q: np.ndarray) -> np.ndarray:
        """
        Get coordinates of query in semantic subspace basis.

        The coordinates represent loadings on each principal component.
        Coordinate[i] is the dot product of q with the i-th basis vector.

        Mathematical Details:
            coordinates = V_k^T @ q

            Reconstruction: q_projected = V_k @ coordinates

        Args:
            q: Query vector of shape (d,)

        Returns:
            Coordinates in subspace basis, shape (k,)
        """
        q = q.flatten().astype(np.float32)

        # coordinates = V_k.T @ q
        coordinates = self.V_k.T @ q

        return coordinates

    def _compute_residual_score(self, q: np.ndarray) -> float:
        """
        Compute residual score for a query.

        Residual score = ||q_orthogonal|| / ||q||

        Measures how much of the query is outside the icon space.
        - 0: Query fully in icon space
        - 1: Query fully orthogonal to icon space

        Args:
            q: Query vector of shape (d,)

        Returns:
            Residual score in [0, 1]
        """
        _, q_orthogonal = self.project_to_iconics(q)

        q_norm = np.linalg.norm(q)
        q_orth_norm = np.linalg.norm(q_orthogonal)

        if q_norm < 1e-10:
            return 0.0

        return float(q_orth_norm / q_norm)

    def retrieve(
        self,
        query: Union[str, np.ndarray],
        k: int = 10,
        mode: Literal["raw", "projected", "weighted"] = "projected",
        weights: Optional[np.ndarray] = None,
        filter_fn: Optional[Callable[[str], bool]] = None,
        include_coordinates: bool = False
    ) -> List[RetrievalResult]:
        """
        Retrieve top-k icons for a query.

        Supports three retrieval modes:
        - "raw": Direct cosine similarity in CLIP space
        - "projected": Project query to icon subspace first
        - "weighted": Apply PC weights for semantic emphasis

        CRITICAL: Every result includes residual_score, measuring how well
        the query fits the icon space.

        Args:
            query: Text query string or pre-computed embedding
            k: Number of results to return
            mode: Retrieval mode ("raw", "projected", or "weighted")
            weights: PC weights for "weighted" mode, shape (k_subspace,).
                    Higher weight = more emphasis on that semantic axis.
            filter_fn: Optional filter function. Called with icon_id,
                      returns True to include, False to exclude.
            include_coordinates: If True, include PC coordinates in results.

        Returns:
            List of RetrievalResult objects, sorted by score descending.
            CRITICAL: Each result has residual_score populated.

        Raises:
            ValueError: If mode is invalid or weights shape is wrong
        """
        if mode not in ("raw", "projected", "weighted"):
            raise ValueError(f"Invalid mode: {mode}. Must be raw, projected, or weighted.")

        # Embed query if needed
        q = self.embed_query(query)

        # Compute residual score (always needed)
        residual_score = self._compute_residual_score(q)

        # Apply mode-specific transformation
        if mode == "raw":
            # Use query as-is
            query_for_search = q
        elif mode == "projected":
            # Project query to subspace
            q_projected, _ = self.project_to_iconics(q)
            # Re-normalize for cosine similarity
            q_norm = np.linalg.norm(q_projected)
            if q_norm > 1e-10:
                query_for_search = q_projected / q_norm
            else:
                query_for_search = q_projected
        elif mode == "weighted":
            # Get coordinates, apply weights, reconstruct
            coords = self.get_coordinates(q)

            if weights is None:
                # Default: use singular value weighting
                if self.singular_values is not None:
                    weights = self.singular_values[:self.k]
                else:
                    weights = np.ones(self.k, dtype=np.float32)

            if len(weights) != self.k:
                raise ValueError(f"Weights length ({len(weights)}) != k ({self.k})")

            # Apply weights and reconstruct
            weighted_coords = coords * weights
            q_weighted = self.V_k @ weighted_coords

            # Normalize
            q_norm = np.linalg.norm(q_weighted)
            if q_norm > 1e-10:
                query_for_search = q_weighted / q_norm
            else:
                query_for_search = q_weighted
        else:
            raise ValueError(f"Unknown mode: {mode}")

        # Ensure query is correct shape for FAISS
        query_for_search = query_for_search.astype(np.float32)

        # If filtering, we need to get more results then filter
        if filter_fn is not None:
            # Get all results then filter
            indices, scores = self.faiss_index.search(query_for_search, self.faiss_index.n_icons)

            results = []
            for idx, score in zip(indices, scores):
                icon_id = self.icon_ids[idx]
                if filter_fn(icon_id):
                    coords = None
                    if include_coordinates:
                        icon_embedding = self.embeddings[idx]
                        coords = self.get_coordinates(icon_embedding)

                    results.append(RetrievalResult(
                        icon_id=icon_id,
                        score=float(score),
                        residual_score=residual_score,
                        coordinates=coords
                    ))

                    if len(results) >= k:
                        break
        else:
            # Direct search
            indices, scores = self.faiss_index.search(query_for_search, k)

            results = []
            for idx, score in zip(indices, scores):
                icon_id = self.icon_ids[idx]

                coords = None
                if include_coordinates:
                    icon_embedding = self.embeddings[idx]
                    coords = self.get_coordinates(icon_embedding)

                results.append(RetrievalResult(
                    icon_id=icon_id,
                    score=float(score),
                    residual_score=residual_score,
                    coordinates=coords
                ))

        return results

    def retrieve_by_icon(
        self,
        icon_id: str,
        k: int = 10,
        exclude_self: bool = True
    ) -> List[RetrievalResult]:
        """
        Find icons similar to a given icon.

        Uses the icon's embedding as query to find semantically related icons.

        Args:
            icon_id: ID of the reference icon
            k: Number of similar icons to return
            exclude_self: If True, exclude the query icon from results

        Returns:
            List of RetrievalResult objects for similar icons

        Raises:
            KeyError: If icon_id not found
        """
        if icon_id not in self.icon_index:
            raise KeyError(f"Icon '{icon_id}' not found")

        # Get icon embedding
        idx = self.icon_index[icon_id]
        icon_embedding = self.embeddings[idx]

        # Search with k+1 if excluding self
        search_k = k + 1 if exclude_self else k

        # Use raw mode for icon-to-icon similarity
        results = self.retrieve(
            icon_embedding,
            k=search_k,
            mode="raw"
        )

        # Filter out self if needed
        if exclude_self:
            results = [r for r in results if r.icon_id != icon_id][:k]

        return results

    def traverse_axis(
        self,
        icon_id: str,
        axis: int,
        steps: int = 5,
        direction: Literal["positive", "negative", "both"] = "both"
    ) -> List[str]:
        """
        Move along semantic axis from an icon's position.

        This explores the semantic meaning of a principal component by
        finding icons at different positions along that axis.

        Args:
            icon_id: Starting icon ID
            axis: Principal component index (0 to k-1)
            steps: Number of steps in each direction
            direction: "positive", "negative", or "both"

        Returns:
            List of icon IDs along the traversal path.
            If "both", returns negative -> center -> positive order.

        Raises:
            KeyError: If icon_id not found
            ValueError: If axis is out of bounds
        """
        if icon_id not in self.icon_index:
            raise KeyError(f"Icon '{icon_id}' not found")

        if axis < 0 or axis >= self.k:
            raise ValueError(f"Axis {axis} out of bounds [0, {self.k})")

        # Get icon embedding and coordinates
        idx = self.icon_index[icon_id]
        icon_embedding = self.embeddings[idx]
        coords = self.get_coordinates(icon_embedding)

        # Get the axis vector
        axis_vector = self.V_k[:, axis]

        # Determine step size based on variance along this axis
        # Use the coordinate range across all icons
        all_coords = self.embeddings @ self.V_k
        axis_std = np.std(all_coords[:, axis])
        step_size = axis_std * 0.5

        result_icons = []

        # Generate positions along axis
        if direction == "positive":
            positions = range(1, steps + 1)
        elif direction == "negative":
            positions = range(-steps, 0)
        else:  # both
            positions = list(range(-steps, 0)) + [0] + list(range(1, steps + 1))

        for pos in positions:
            if pos == 0:
                result_icons.append(icon_id)
                continue

            # Create modified embedding by moving along axis
            new_coords = coords.copy()
            new_coords[axis] = coords[axis] + pos * step_size

            # Reconstruct embedding from coordinates
            new_embedding = self.V_k @ new_coords

            # Normalize
            norm = np.linalg.norm(new_embedding)
            if norm > 1e-10:
                new_embedding = new_embedding / norm

            # Find nearest icon
            results = self.retrieve(new_embedding, k=1, mode="raw")
            if results:
                result_icons.append(results[0].icon_id)

        return result_icons

    def interpolate(
        self,
        icon_a: str,
        icon_b: str,
        steps: int = 5
    ) -> List[str]:
        """
        Find icons along interpolation path between two icons.

        Performs linear interpolation in the embedding space and finds
        the nearest icon at each interpolation point.

        Args:
            icon_a: Starting icon ID
            icon_b: Ending icon ID
            steps: Number of interpolation steps (including endpoints)

        Returns:
            List of icon IDs along the path from A to B

        Raises:
            KeyError: If either icon_id not found
        """
        if icon_a not in self.icon_index:
            raise KeyError(f"Icon '{icon_a}' not found")
        if icon_b not in self.icon_index:
            raise KeyError(f"Icon '{icon_b}' not found")

        # Get embeddings
        idx_a = self.icon_index[icon_a]
        idx_b = self.icon_index[icon_b]
        emb_a = self.embeddings[idx_a]
        emb_b = self.embeddings[idx_b]

        result_icons = []

        # Interpolate
        for i in range(steps):
            t = i / (steps - 1) if steps > 1 else 0.0

            # Linear interpolation
            interp_emb = (1 - t) * emb_a + t * emb_b

            # Normalize for cosine similarity
            norm = np.linalg.norm(interp_emb)
            if norm > 1e-10:
                interp_emb = interp_emb / norm

            # Find nearest icon
            results = self.retrieve(interp_emb, k=1, mode="raw")
            if results:
                result_icons.append(results[0].icon_id)

        return result_icons

    def orthogonal_residual_score(self, query: str) -> float:
        """
        Compute how "un-icon-like" a query is.

        This measures the fraction of the query that lies outside the icon
        subspace. High score means the query concept is not well-represented
        by the icon library.

        Args:
            query: Text query string

        Returns:
            Residual score in [0, 1]:
            - 0.0: Query fully representable by icons
            - 1.0: Query completely outside icon space
        """
        q = self.embed_query(query)
        return self._compute_residual_score(q)

    def get_icon_embedding(self, icon_id: str) -> np.ndarray:
        """
        Get the embedding for a specific icon.

        Args:
            icon_id: Icon identifier

        Returns:
            Embedding vector of shape (d,)

        Raises:
            KeyError: If icon_id not found
        """
        if icon_id not in self.icon_index:
            raise KeyError(f"Icon '{icon_id}' not found")

        idx = self.icon_index[icon_id]
        return self.embeddings[idx].copy()

    def get_icon_coordinates(self, icon_id: str) -> np.ndarray:
        """
        Get the subspace coordinates for a specific icon.

        Args:
            icon_id: Icon identifier

        Returns:
            Coordinate vector of shape (k,)

        Raises:
            KeyError: If icon_id not found
        """
        embedding = self.get_icon_embedding(icon_id)
        return self.get_coordinates(embedding)

    def similarity(self, icon_a: str, icon_b: str) -> float:
        """
        Compute cosine similarity between two icons.

        Args:
            icon_a: First icon ID
            icon_b: Second icon ID

        Returns:
            Cosine similarity in [-1, 1]

        Raises:
            KeyError: If either icon not found
        """
        emb_a = self.get_icon_embedding(icon_a)
        emb_b = self.get_icon_embedding(icon_b)

        return float(np.dot(emb_a, emb_b))

    def __len__(self) -> int:
        """Return number of icons."""
        return len(self.icon_ids)

    def __contains__(self, icon_id: str) -> bool:
        """Check if icon_id exists."""
        return icon_id in self.icon_index

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"IconicsRetriever(n_icons={len(self.icon_ids)}, "
            f"dim={self.embeddings.shape[1]}, k={self.k})"
        )
