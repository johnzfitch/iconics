"""
Unit tests for iconics_index.py

Tests FAISS index wrapper functionality including building, searching,
and save/load operations.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import sys
import numpy as np

# Add src to path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from iconics_index import IconicsIndex, build_index_from_embeddings


class TestIconicsIndexInit(unittest.TestCase):
    """Test IconicsIndex initialization."""

    def setUp(self):
        """Create test embeddings."""
        np.random.seed(42)
        self.n_icons = 100
        self.dimension = 64

        # Create normalized random embeddings
        embeddings = np.random.randn(self.n_icons, self.dimension).astype(np.float32)
        self.embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

        self.icon_ids = [f"icon_{i}" for i in range(self.n_icons)]

    def test_basic_init(self):
        """Test basic index initialization."""
        index = IconicsIndex(self.embeddings, self.icon_ids)

        self.assertEqual(len(index), self.n_icons)
        self.assertEqual(index.dimension, self.dimension)
        self.assertEqual(index.n_icons, self.n_icons)

    def test_init_stores_icon_ids(self):
        """Test that icon_ids are stored correctly."""
        index = IconicsIndex(self.embeddings, self.icon_ids)

        self.assertEqual(index.icon_ids, self.icon_ids)
        for i, icon_id in enumerate(self.icon_ids):
            self.assertEqual(index.get_icon_id(i), icon_id)
            self.assertEqual(index.get_index(icon_id), i)

    def test_init_with_projection_flag(self):
        """Test use_projection metadata flag."""
        index_raw = IconicsIndex(self.embeddings, self.icon_ids, use_projection=False)
        index_proj = IconicsIndex(self.embeddings, self.icon_ids, use_projection=True)

        self.assertFalse(index_raw.use_projection)
        self.assertTrue(index_proj.use_projection)

    def test_init_mismatched_lengths(self):
        """Test that mismatched embeddings/icon_ids raises ValueError."""
        wrong_ids = self.icon_ids[:-1]  # One less ID

        with self.assertRaises(ValueError):
            IconicsIndex(self.embeddings, wrong_ids)

    def test_init_wrong_dims(self):
        """Test that non-2D embeddings raises ValueError."""
        wrong_embeddings = np.random.randn(100).astype(np.float32)

        with self.assertRaises(ValueError):
            IconicsIndex(wrong_embeddings, ["icon_0"])

    def test_init_converts_dtype(self):
        """Test that float64 embeddings are converted to float32."""
        embeddings_f64 = self.embeddings.astype(np.float64)

        index = IconicsIndex(embeddings_f64, self.icon_ids)

        # Should work without error
        self.assertEqual(index.n_icons, self.n_icons)

    def test_contains(self):
        """Test __contains__ method."""
        index = IconicsIndex(self.embeddings, self.icon_ids)

        self.assertIn("icon_0", index)
        self.assertIn("icon_50", index)
        self.assertNotIn("nonexistent", index)


class TestIconicsIndexSearch(unittest.TestCase):
    """Test search functionality."""

    def setUp(self):
        """Create test index with known structure."""
        np.random.seed(42)
        self.n_icons = 100
        self.dimension = 64

        # Create embeddings where similar icons are close
        embeddings = np.random.randn(self.n_icons, self.dimension).astype(np.float32)
        self.embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

        self.icon_ids = [f"icon_{i}" for i in range(self.n_icons)]
        self.index = IconicsIndex(self.embeddings, self.icon_ids)

    def test_search_returns_correct_shapes(self):
        """Test search returns correct shapes."""
        query = np.random.randn(self.dimension).astype(np.float32)
        query = query / np.linalg.norm(query)

        k = 10
        indices, scores = self.index.search(query, k=k)

        self.assertEqual(indices.shape, (k,))
        self.assertEqual(scores.shape, (k,))

    def test_search_scores_descending(self):
        """Test search returns scores in descending order."""
        query = np.random.randn(self.dimension).astype(np.float32)
        query = query / np.linalg.norm(query)

        _, scores = self.index.search(query, k=20)

        # Scores should be descending
        self.assertTrue(np.all(scores[:-1] >= scores[1:]))

    def test_search_finds_exact_match(self):
        """Test that searching with an icon's own embedding finds itself first."""
        # Use first icon's embedding as query
        query = self.embeddings[0].copy()

        indices, scores = self.index.search(query, k=1)

        self.assertEqual(indices[0], 0)
        np.testing.assert_allclose(scores[0], 1.0, atol=1e-5)

    def test_search_with_2d_query(self):
        """Test search handles 2D query (1, d)."""
        query = np.random.randn(1, self.dimension).astype(np.float32)
        query = query / np.linalg.norm(query)

        indices, scores = self.index.search(query, k=5)

        self.assertEqual(indices.shape, (5,))

    def test_search_wrong_dimension(self):
        """Test search raises error on wrong dimension."""
        wrong_query = np.random.randn(self.dimension + 1).astype(np.float32)

        with self.assertRaises(ValueError):
            self.index.search(wrong_query, k=5)

    def test_search_k_larger_than_n(self):
        """Test search with k > n_icons returns all icons."""
        query = np.random.randn(self.dimension).astype(np.float32)
        query = query / np.linalg.norm(query)

        indices, scores = self.index.search(query, k=200)

        # Should return all icons (clamped to n_icons)
        self.assertEqual(len(indices), self.n_icons)

    def test_search_batch(self):
        """Test batch search."""
        n_queries = 5
        queries = np.random.randn(n_queries, self.dimension).astype(np.float32)
        queries = queries / np.linalg.norm(queries, axis=1, keepdims=True)

        k = 10
        indices, scores = self.index.search_batch(queries, k=k)

        self.assertEqual(indices.shape, (n_queries, k))
        self.assertEqual(scores.shape, (n_queries, k))

    def test_search_normalized_scores(self):
        """Test that scores are in valid range for normalized vectors."""
        query = np.random.randn(self.dimension).astype(np.float32)
        query = query / np.linalg.norm(query)

        _, scores = self.index.search(query, k=20)

        # Cosine similarity for normalized vectors should be in [-1, 1]
        self.assertTrue(np.all(scores >= -1.0))
        self.assertTrue(np.all(scores <= 1.0))


class TestIconicsIndexHelpers(unittest.TestCase):
    """Test helper methods."""

    def setUp(self):
        """Create test index."""
        np.random.seed(42)
        self.n_icons = 50
        self.dimension = 32

        embeddings = np.random.randn(self.n_icons, self.dimension).astype(np.float32)
        self.embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

        self.icon_ids = [f"icon_{i}" for i in range(self.n_icons)]
        self.index = IconicsIndex(self.embeddings, self.icon_ids)

    def test_get_icon_id(self):
        """Test get_icon_id returns correct ID."""
        for i in range(self.n_icons):
            self.assertEqual(self.index.get_icon_id(i), f"icon_{i}")

    def test_get_icon_id_out_of_bounds(self):
        """Test get_icon_id raises IndexError for invalid index."""
        with self.assertRaises(IndexError):
            self.index.get_icon_id(-1)

        with self.assertRaises(IndexError):
            self.index.get_icon_id(self.n_icons)

    def test_get_index(self):
        """Test get_index returns correct index."""
        for i in range(self.n_icons):
            self.assertEqual(self.index.get_index(f"icon_{i}"), i)

    def test_get_index_not_found(self):
        """Test get_index raises KeyError for missing icon."""
        with self.assertRaises(KeyError):
            self.index.get_index("nonexistent_icon")

    def test_len(self):
        """Test __len__ returns correct count."""
        self.assertEqual(len(self.index), self.n_icons)

    def test_repr(self):
        """Test __repr__ contains useful info."""
        repr_str = repr(self.index)

        self.assertIn("IconicsIndex", repr_str)
        self.assertIn(str(self.n_icons), repr_str)
        self.assertIn(str(self.dimension), repr_str)


class TestIconicsIndexSaveLoad(unittest.TestCase):
    """Test save and load operations."""

    def setUp(self):
        """Create test index and temporary directory."""
        np.random.seed(42)
        self.n_icons = 100
        self.dimension = 64

        embeddings = np.random.randn(self.n_icons, self.dimension).astype(np.float32)
        self.embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

        self.icon_ids = [f"icon_{i}" for i in range(self.n_icons)]
        self.index = IconicsIndex(self.embeddings, self.icon_ids)

        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_save_creates_file(self):
        """Test that save creates index file."""
        index_path = Path(self.temp_dir) / "test.faiss"

        self.index.save(str(index_path))

        self.assertTrue(index_path.exists())

    def test_save_load_roundtrip(self):
        """Test that save/load preserves search results."""
        index_path = Path(self.temp_dir) / "test.faiss"

        # Save
        self.index.save(str(index_path))

        # Create query
        query = np.random.randn(self.dimension).astype(np.float32)
        query = query / np.linalg.norm(query)

        # Get results before save
        indices_before, scores_before = self.index.search(query, k=10)

        # Load
        loaded_index = IconicsIndex.load(str(index_path), self.icon_ids)

        # Get results after load
        indices_after, scores_after = loaded_index.search(query, k=10)

        # Should be identical
        np.testing.assert_array_equal(indices_before, indices_after)
        np.testing.assert_allclose(scores_before, scores_after)

    def test_load_mismatched_size(self):
        """Test load raises error on mismatched icon_ids size."""
        index_path = Path(self.temp_dir) / "test.faiss"
        self.index.save(str(index_path))

        wrong_ids = self.icon_ids[:-1]  # One less

        with self.assertRaises(ValueError):
            IconicsIndex.load(str(index_path), wrong_ids)

    def test_load_missing_file(self):
        """Test load raises error for missing file."""
        with self.assertRaises(FileNotFoundError):
            IconicsIndex.load("/nonexistent/path.faiss", self.icon_ids)

    def test_load_preserves_dimension(self):
        """Test that loaded index has correct dimension."""
        index_path = Path(self.temp_dir) / "test.faiss"
        self.index.save(str(index_path))

        loaded = IconicsIndex.load(str(index_path), self.icon_ids)

        self.assertEqual(loaded.dimension, self.dimension)

    def test_save_creates_parent_dirs(self):
        """Test that save creates parent directories if needed."""
        nested_path = Path(self.temp_dir) / "a" / "b" / "c" / "test.faiss"

        self.index.save(str(nested_path))

        self.assertTrue(nested_path.exists())


class TestBuildIndexFromEmbeddings(unittest.TestCase):
    """Test convenience function for building index."""

    def setUp(self):
        """Create temporary directory and test embeddings."""
        self.temp_dir = tempfile.mkdtemp()

        np.random.seed(42)
        self.n_icons = 50
        self.dimension = 32

        embeddings = np.random.randn(self.n_icons, self.dimension).astype(np.float32)
        self.embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

        self.icon_ids = [f"icon_{i}" for i in range(self.n_icons)]

        # Save embeddings to file
        self.embeddings_path = Path(self.temp_dir) / "embeddings.npy"
        np.save(self.embeddings_path, self.embeddings)

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_build_from_file(self):
        """Test building index from embeddings file."""
        index_path = Path(self.temp_dir) / "index.faiss"

        index = build_index_from_embeddings(
            self.embeddings_path,
            index_path,
            self.icon_ids
        )

        self.assertEqual(len(index), self.n_icons)
        self.assertTrue(index_path.exists())

    def test_build_with_projected_embeddings(self):
        """Test building index with pre-projected embeddings."""
        index_path = Path(self.temp_dir) / "index.faiss"

        # Create mock projected embeddings
        projected = np.random.randn(self.n_icons, 16).astype(np.float32)
        projected = projected / np.linalg.norm(projected, axis=1, keepdims=True)

        index = build_index_from_embeddings(
            self.embeddings_path,
            index_path,
            self.icon_ids,
            projected_embeddings=projected
        )

        self.assertTrue(index.use_projection)
        self.assertEqual(index.dimension, 16)


class TestIndexMathematicalProperties(unittest.TestCase):
    """Test mathematical properties of the index."""

    def setUp(self):
        """Create test index with known properties."""
        np.random.seed(42)
        self.n_icons = 200
        self.dimension = 128

        # Create normalized embeddings
        embeddings = np.random.randn(self.n_icons, self.dimension).astype(np.float32)
        self.embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

        self.icon_ids = [f"icon_{i}" for i in range(self.n_icons)]
        self.index = IconicsIndex(self.embeddings, self.icon_ids)

    def test_self_similarity_is_one(self):
        """Test that cosine similarity with self is 1."""
        for i in range(min(10, self.n_icons)):
            query = self.embeddings[i]
            indices, scores = self.index.search(query, k=1)

            self.assertEqual(indices[0], i)
            np.testing.assert_allclose(scores[0], 1.0, atol=1e-5)

    def test_triangle_inequality_preserved(self):
        """Test that similar embeddings have similar search results."""
        # Create two similar queries
        base_query = np.random.randn(self.dimension).astype(np.float32)
        base_query = base_query / np.linalg.norm(base_query)

        # Slightly perturbed query
        noise = np.random.randn(self.dimension).astype(np.float32) * 0.1
        perturbed = base_query + noise
        perturbed = perturbed / np.linalg.norm(perturbed)

        # Get search results
        indices1, _ = self.index.search(base_query, k=10)
        indices2, _ = self.index.search(perturbed, k=10)

        # Similar queries should have significant overlap in top results
        overlap = len(set(indices1) & set(indices2))
        self.assertGreaterEqual(overlap, 3, "Similar queries should have some result overlap")

    def test_orthogonal_queries_give_different_results(self):
        """Test that orthogonal queries give different top results."""
        # Create orthogonal queries using Gram-Schmidt
        q1 = np.random.randn(self.dimension).astype(np.float32)
        q1 = q1 / np.linalg.norm(q1)

        q2 = np.random.randn(self.dimension).astype(np.float32)
        q2 = q2 - np.dot(q1, q2) * q1  # Make orthogonal
        q2 = q2 / np.linalg.norm(q2)

        # Verify orthogonal
        self.assertAlmostEqual(np.dot(q1, q2), 0.0, places=5)

        # Get top results
        indices1, _ = self.index.search(q1, k=5)
        indices2, _ = self.index.search(q2, k=5)

        # Top result should generally be different
        # (this may occasionally fail due to random chance)
        top1 = set(indices1[:3])
        top2 = set(indices2[:3])

        # At least somewhat different
        self.assertFalse(top1 == top2, "Orthogonal queries should not have identical top results")


if __name__ == "__main__":
    unittest.main(verbosity=2)
