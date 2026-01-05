"""
Iconics FAISS Index Wrapper Module

This module provides a FAISS-based index for efficient nearest neighbor search
over icon embeddings. Supports both raw CLIP embeddings and projected subspace
embeddings.

Mathematical Foundation:
    Given normalized embeddings E in R^(n,d), we use FAISS IndexFlatIP
    (Inner Product) which computes cosine similarity for L2-normalized vectors:

    similarity(q, e_i) = q^T e_i = cos(theta) for ||q|| = ||e_i|| = 1

    The index returns the k nearest neighbors in O(n*d) time for flat index,
    with exact results (no approximation).
"""

import logging
from pathlib import Path
from typing import List, Tuple, Optional

import faiss
import numpy as np

logger = logging.getLogger(__name__)


class IconicsIndex:
    """
    FAISS index wrapper for efficient icon similarity search.

    This class wraps a FAISS flat index for exact nearest neighbor search
    using inner product (equivalent to cosine similarity for normalized vectors).

    Attributes:
        index: FAISS IndexFlatIP instance
        icon_ids: List of icon identifiers corresponding to index rows
        n_icons: Number of icons in index
        dimension: Embedding dimension

    Example:
        >>> embeddings = np.random.randn(1000, 512).astype(np.float32)
        >>> embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        >>> icon_ids = [f"icon_{i}" for i in range(1000)]
        >>> index = IconicsIndex(embeddings, icon_ids)
        >>>
        >>> query = np.random.randn(512).astype(np.float32)
        >>> query = query / np.linalg.norm(query)
        >>> indices, scores = index.search(query, k=10)
    """

    def __init__(
        self,
        embeddings: np.ndarray,
        icon_ids: List[str],
        use_projection: bool = False,
        use_gpu: bool = False
    ):
        """
        Initialize FAISS index with embeddings.

        Args:
            embeddings: Normalized embedding matrix of shape (n_icons, dimension).
                       Must be float32 and L2-normalized for correct similarity scores.
            icon_ids: List of icon identifiers, one per embedding row.
                     Order must match embedding row order.
            use_projection: If True, indicates embeddings are projected to subspace.
                           This is for metadata only; doesn't affect search.
            use_gpu: If True, use GPU-accelerated FAISS (requires faiss-gpu).
                    For <100K vectors, CPU is often fast enough.

        Raises:
            ValueError: If embeddings and icon_ids have mismatched lengths
            ValueError: If embeddings is not 2D
            ValueError: If embeddings is not float32
        """
        # Validate inputs
        if embeddings.ndim != 2:
            raise ValueError(f"Embeddings must be 2D, got shape {embeddings.shape}")

        if embeddings.shape[0] != len(icon_ids):
            raise ValueError(
                f"Embeddings rows ({embeddings.shape[0]}) != icon_ids length ({len(icon_ids)})"
            )

        # Ensure float32 for FAISS compatibility
        if embeddings.dtype != np.float32:
            logger.warning(f"Converting embeddings from {embeddings.dtype} to float32")
            embeddings = embeddings.astype(np.float32)

        # Store metadata
        self.icon_ids = list(icon_ids)
        self.n_icons = len(icon_ids)
        self.dimension = embeddings.shape[1]
        self.use_projection = use_projection
        self.use_gpu = use_gpu

        # Create FAISS index
        # IndexFlatIP: Flat index with Inner Product (cosine sim for normalized vecs)
        self.index = faiss.IndexFlatIP(self.dimension)

        # Optionally move to GPU
        if use_gpu:
            try:
                res = faiss.StandardGpuResources()
                self.index = faiss.index_cpu_to_gpu(res, 0, self.index)
                logger.info("FAISS index moved to GPU")
            except Exception as e:
                logger.warning(f"Failed to move FAISS to GPU: {e}. Using CPU.")
                self.use_gpu = False

        # Ensure contiguous array for FAISS
        embeddings_contiguous = np.ascontiguousarray(embeddings)

        # Add embeddings to index
        self.index.add(embeddings_contiguous)

        logger.info(
            f"Created FAISS index with {self.n_icons} icons, "
            f"dimension={self.dimension}, projected={use_projection}, gpu={self.use_gpu}"
        )

    def search(
        self,
        query: np.ndarray,
        k: int = 10
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Search for k nearest neighbors to query.

        Uses inner product similarity, which equals cosine similarity for
        L2-normalized vectors. Higher scores indicate more similar icons.

        Args:
            query: Query vector of shape (dimension,) or (1, dimension).
                  Should be L2-normalized for correct similarity interpretation.
            k: Number of nearest neighbors to return.
               If k > n_icons, returns all icons.

        Returns:
            Tuple of (indices, scores) where:
            - indices: Array of shape (k,) with icon indices (into icon_ids)
            - scores: Array of shape (k,) with similarity scores (descending)

        Raises:
            ValueError: If query dimension doesn't match index dimension
        """
        # Handle 1D query
        if query.ndim == 1:
            query = query.reshape(1, -1)

        # Validate dimension
        if query.shape[1] != self.dimension:
            raise ValueError(
                f"Query dimension ({query.shape[1]}) != index dimension ({self.dimension})"
            )

        # Ensure float32 and contiguous
        if query.dtype != np.float32:
            query = query.astype(np.float32)
        query = np.ascontiguousarray(query)

        # Clamp k to available icons
        k = min(k, self.n_icons)

        # FAISS search
        scores, indices = self.index.search(query, k)

        # Flatten from (1, k) to (k,)
        return indices.flatten(), scores.flatten()

    def search_batch(
        self,
        queries: np.ndarray,
        k: int = 10
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Search for k nearest neighbors for multiple queries.

        Args:
            queries: Query matrix of shape (n_queries, dimension).
            k: Number of nearest neighbors per query.

        Returns:
            Tuple of (indices, scores) where:
            - indices: Array of shape (n_queries, k) with icon indices
            - scores: Array of shape (n_queries, k) with similarity scores
        """
        if queries.ndim == 1:
            queries = queries.reshape(1, -1)

        if queries.shape[1] != self.dimension:
            raise ValueError(
                f"Query dimension ({queries.shape[1]}) != index dimension ({self.dimension})"
            )

        if queries.dtype != np.float32:
            queries = queries.astype(np.float32)
        queries = np.ascontiguousarray(queries)

        k = min(k, self.n_icons)

        scores, indices = self.index.search(queries, k)

        return indices, scores

    def get_icon_id(self, index: int) -> str:
        """
        Get icon ID for a given index.

        Args:
            index: Row index in the embedding matrix

        Returns:
            Icon ID string

        Raises:
            IndexError: If index is out of bounds
        """
        if index < 0 or index >= self.n_icons:
            raise IndexError(f"Index {index} out of bounds [0, {self.n_icons})")
        return self.icon_ids[index]

    def get_index(self, icon_id: str) -> int:
        """
        Get row index for a given icon ID.

        Args:
            icon_id: Icon identifier string

        Returns:
            Row index in embedding matrix

        Raises:
            KeyError: If icon_id not found
        """
        try:
            return self.icon_ids.index(icon_id)
        except ValueError:
            raise KeyError(f"Icon ID '{icon_id}' not found in index")

    def save(self, path: str) -> None:
        """
        Save FAISS index to disk.

        Saves only the FAISS index binary. Icon IDs must be saved separately
        and provided when loading.

        Args:
            path: File path for the index (typically .faiss extension)
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        faiss.write_index(self.index, str(path))
        logger.info(f"Saved FAISS index to {path}")

    @classmethod
    def load(
        cls,
        path: str,
        icon_ids: List[str]
    ) -> "IconicsIndex":
        """
        Load FAISS index from disk.

        Args:
            path: File path to the saved FAISS index
            icon_ids: List of icon IDs in the same order as when index was created

        Returns:
            IconicsIndex instance with loaded index

        Raises:
            FileNotFoundError: If index file doesn't exist
            ValueError: If icon_ids length doesn't match index size
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Index file not found: {path}")

        # Load FAISS index
        index = faiss.read_index(str(path))

        # Validate size
        if index.ntotal != len(icon_ids):
            raise ValueError(
                f"Index size ({index.ntotal}) != icon_ids length ({len(icon_ids)})"
            )

        # Create instance without normal initialization
        instance = cls.__new__(cls)
        instance.index = index
        instance.icon_ids = list(icon_ids)
        instance.n_icons = len(icon_ids)
        instance.dimension = index.d
        instance.use_projection = False  # Unknown from saved index

        logger.info(f"Loaded FAISS index from {path}: {instance.n_icons} icons")

        return instance

    def __len__(self) -> int:
        """Return number of icons in index."""
        return self.n_icons

    def __contains__(self, icon_id: str) -> bool:
        """Check if icon_id is in index."""
        return icon_id in self.icon_ids

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"IconicsIndex(n_icons={self.n_icons}, dimension={self.dimension}, "
            f"projected={self.use_projection})"
        )


def build_index_from_embeddings(
    embeddings_path: Path,
    index_path: Path,
    icon_ids: List[str],
    projected_embeddings: Optional[np.ndarray] = None
) -> IconicsIndex:
    """
    Build and save FAISS index from embeddings file.

    Convenience function for building an index from saved embeddings.

    Args:
        embeddings_path: Path to embeddings .npy file
        index_path: Path where to save the FAISS index
        icon_ids: List of icon IDs matching embedding rows
        projected_embeddings: Optional pre-projected embeddings.
                             If None, loads raw embeddings from file.

    Returns:
        Built IconicsIndex instance
    """
    if projected_embeddings is not None:
        embeddings = projected_embeddings
        use_projection = True
    else:
        embeddings = np.load(embeddings_path)
        use_projection = False

    # Create index
    index = IconicsIndex(embeddings, icon_ids, use_projection=use_projection)

    # Save to disk
    index.save(str(index_path))

    return index
