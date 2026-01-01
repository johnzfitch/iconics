"""
Unit tests for iconics_retrieval.py

Tests the IconicsRetriever class including query embedding, projection,
retrieval modes, and mathematical properties.

Uses mock data to avoid loading actual CLIP model during unit tests.
"""

import unittest
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

import numpy as np

# Add src to path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from iconics_retrieval import IconicsRetriever, RetrievalResult


class MockRetrieverTestCase(unittest.TestCase):
    """Base class with mock data setup for retriever tests."""

    @classmethod
    def setUpClass(cls):
        """Create mock embeddings and subspace data."""
        cls.temp_dir = tempfile.mkdtemp()
        cls.embeddings_dir = Path(cls.temp_dir) / "embeddings"
        cls.subspace_dir = Path(cls.temp_dir) / "subspace"

        cls.embeddings_dir.mkdir()
        cls.subspace_dir.mkdir()

        np.random.seed(42)

        # Create mock embeddings
        cls.n_icons = 100
        cls.d = 64  # Embedding dimension
        cls.k = 16  # Subspace dimension

        # Create normalized embeddings
        embeddings = np.random.randn(cls.n_icons, cls.d).astype(np.float32)
        cls.embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

        # Save embeddings
        np.save(cls.embeddings_dir / "icon_embeddings.npy", cls.embeddings)

        # Create icon index
        cls.icon_index = {f"icon_{i}": i for i in range(cls.n_icons)}
        with open(cls.embeddings_dir / "icon_index.json", "w") as f:
            json.dump(cls.icon_index, f)

        # Create subspace data
        # Create orthonormal basis via SVD
        random_matrix = np.random.randn(cls.d, cls.d).astype(np.float32)
        _, _, Vt = np.linalg.svd(random_matrix, full_matrices=True)
        cls.V_k = Vt[:cls.k, :].T  # Shape (d, k)

        np.save(cls.subspace_dir / "basis_vectors.npy", cls.V_k)

        # Save singular values
        cls.singular_values = np.array([10.0 / (i + 1) for i in range(cls.d)], dtype=np.float32)
        np.save(cls.subspace_dir / "singular_values.npy", cls.singular_values)

        # Save effective dim
        with open(cls.subspace_dir / "effective_dim.json", "w") as f:
            json.dump({"effective_dim": cls.k}, f)

    @classmethod
    def tearDownClass(cls):
        """Clean up temporary directory."""
        shutil.rmtree(cls.temp_dir)

    def setUp(self):
        """Create retriever instance with mocked CLIP."""
        # Patch CLIP model loading
        self.patcher = patch.object(IconicsRetriever, '_ensure_model_loaded')
        self.mock_ensure_model = self.patcher.start()

        self.retriever = IconicsRetriever(
            embeddings_path=str(self.embeddings_dir),
            subspace_path=str(self.subspace_dir)
        )

    def tearDown(self):
        """Stop patching."""
        self.patcher.stop()


class TestRetrievalResult(unittest.TestCase):
    """Test RetrievalResult dataclass."""

    def test_basic_creation(self):
        """Test creating a RetrievalResult."""
        result = RetrievalResult(
            icon_id="test_icon",
            score=0.95,
            residual_score=0.1
        )

        self.assertEqual(result.icon_id, "test_icon")
        self.assertEqual(result.score, 0.95)
        self.assertEqual(result.residual_score, 0.1)
        self.assertIsNone(result.coordinates)

    def test_with_coordinates(self):
        """Test creating result with coordinates."""
        coords = np.array([1.0, 2.0, 3.0])
        result = RetrievalResult(
            icon_id="test_icon",
            score=0.9,
            residual_score=0.2,
            coordinates=coords
        )

        np.testing.assert_array_equal(result.coordinates, coords)

    def test_residual_required(self):
        """Test that residual_score is always required."""
        # This should raise an error because residual_score is None
        with self.assertRaises(ValueError):
            RetrievalResult(
                icon_id="test",
                score=0.9,
                residual_score=None
            )

    def test_to_dict(self):
        """Test to_dict serialization."""
        result = RetrievalResult(
            icon_id="test_icon",
            score=0.95,
            residual_score=0.1
        )

        d = result.to_dict()

        self.assertIn("icon_id", d)
        self.assertIn("score", d)
        self.assertIn("residual_score", d)
        self.assertEqual(d["icon_id"], "test_icon")


class TestRetrieverInit(MockRetrieverTestCase):
    """Test IconicsRetriever initialization."""

    def test_loads_embeddings(self):
        """Test that embeddings are loaded correctly."""
        self.assertEqual(self.retriever.embeddings.shape, (self.n_icons, self.d))
        np.testing.assert_allclose(self.retriever.embeddings, self.embeddings)

    def test_loads_icon_ids(self):
        """Test that icon IDs are loaded correctly."""
        self.assertEqual(len(self.retriever.icon_ids), self.n_icons)
        self.assertEqual(self.retriever.icon_ids[0], "icon_0")

    def test_loads_subspace(self):
        """Test that subspace data is loaded correctly."""
        self.assertEqual(self.retriever.k, self.k)
        self.assertEqual(self.retriever.V_k.shape, (self.d, self.k))

    def test_builds_projection_matrix(self):
        """Test that projection matrix is built correctly."""
        P = self.retriever.projection_matrix

        self.assertEqual(P.shape, (self.d, self.d))

        # P should be symmetric
        np.testing.assert_allclose(P, P.T, atol=1e-6)

        # P should be idempotent: P @ P = P
        P_squared = P @ P
        np.testing.assert_allclose(P_squared, P, atol=1e-6)

    def test_contains(self):
        """Test __contains__ method."""
        self.assertIn("icon_0", self.retriever)
        self.assertIn("icon_50", self.retriever)
        self.assertNotIn("nonexistent", self.retriever)

    def test_len(self):
        """Test __len__ method."""
        self.assertEqual(len(self.retriever), self.n_icons)


class TestEmbedQuery(MockRetrieverTestCase):
    """Test embed_query method."""

    def test_embed_query_with_array(self):
        """Test embed_query with pre-computed embedding."""
        query = np.random.randn(self.d).astype(np.float32)

        result = self.retriever.embed_query(query)

        np.testing.assert_array_equal(result, query)
        self.assertEqual(result.dtype, np.float32)

    def test_embed_query_with_2d_array(self):
        """Test embed_query flattens 2D input."""
        query = np.random.randn(1, self.d).astype(np.float32)

        result = self.retriever.embed_query(query)

        self.assertEqual(result.shape, (self.d,))


class TestProjectToIconics(MockRetrieverTestCase):
    """Test project_to_iconics method."""

    def test_projection_decomposition(self):
        """Test that q = q_proj + q_orth."""
        q = np.random.randn(self.d).astype(np.float32)

        q_proj, q_orth = self.retriever.project_to_iconics(q)

        # Reconstruction
        reconstructed = q_proj + q_orth
        np.testing.assert_allclose(reconstructed, q, atol=1e-5)

    def test_orthogonality(self):
        """Test that q_proj is orthogonal to q_orth."""
        q = np.random.randn(self.d).astype(np.float32)

        q_proj, q_orth = self.retriever.project_to_iconics(q)

        dot_product = np.dot(q_proj, q_orth)
        self.assertAlmostEqual(dot_product, 0.0, places=5)

    def test_pythagorean_theorem(self):
        """Test ||q||^2 = ||q_proj||^2 + ||q_orth||^2."""
        q = np.random.randn(self.d).astype(np.float32)

        q_proj, q_orth = self.retriever.project_to_iconics(q)

        norm_q_sq = np.sum(q ** 2)
        norm_proj_sq = np.sum(q_proj ** 2)
        norm_orth_sq = np.sum(q_orth ** 2)

        np.testing.assert_allclose(norm_q_sq, norm_proj_sq + norm_orth_sq, rtol=1e-5)

    def test_projection_idempotence(self):
        """Test project(project(q)) = project(q)."""
        q = np.random.randn(self.d).astype(np.float32)

        q_proj, _ = self.retriever.project_to_iconics(q)
        q_proj_again, q_orth_again = self.retriever.project_to_iconics(q_proj)

        np.testing.assert_allclose(q_proj_again, q_proj, atol=1e-6)
        self.assertLess(np.linalg.norm(q_orth_again), 1e-5)

    def test_projection_dimension_mismatch(self):
        """Test that wrong dimension raises ValueError."""
        wrong_q = np.random.randn(self.d + 10).astype(np.float32)

        with self.assertRaises(ValueError):
            self.retriever.project_to_iconics(wrong_q)


class TestGetCoordinates(MockRetrieverTestCase):
    """Test get_coordinates method."""

    def test_coordinates_shape(self):
        """Test coordinates have correct shape."""
        q = np.random.randn(self.d).astype(np.float32)

        coords = self.retriever.get_coordinates(q)

        self.assertEqual(coords.shape, (self.k,))

    def test_coordinates_are_projections(self):
        """Test coordinates[i] = <q, v_i>."""
        q = np.random.randn(self.d).astype(np.float32)

        coords = self.retriever.get_coordinates(q)

        # Manually compute
        for i in range(self.k):
            v_i = self.retriever.V_k[:, i]
            expected = np.dot(q, v_i)
            self.assertAlmostEqual(coords[i], expected, places=5)

    def test_reconstruction_from_coordinates(self):
        """Test that V_k @ coords = q_projected."""
        q = np.random.randn(self.d).astype(np.float32)

        coords = self.retriever.get_coordinates(q)
        reconstructed = self.retriever.V_k @ coords

        # This should equal the projection
        q_proj, _ = self.retriever.project_to_iconics(q)

        np.testing.assert_allclose(reconstructed, q_proj, atol=1e-5)


class TestRetrieve(MockRetrieverTestCase):
    """Test retrieve method."""

    def test_retrieve_returns_results(self):
        """Test retrieve returns list of RetrievalResult."""
        query = np.random.randn(self.d).astype(np.float32)
        query = query / np.linalg.norm(query)

        results = self.retriever.retrieve(query, k=10, mode="raw")

        self.assertEqual(len(results), 10)
        self.assertIsInstance(results[0], RetrievalResult)

    def test_retrieve_residual_always_present(self):
        """Test that residual_score is always included."""
        query = np.random.randn(self.d).astype(np.float32)
        query = query / np.linalg.norm(query)

        for mode in ["raw", "projected", "weighted"]:
            results = self.retriever.retrieve(query, k=5, mode=mode)

            for result in results:
                self.assertIsNotNone(result.residual_score)
                self.assertGreaterEqual(result.residual_score, 0.0)
                self.assertLessEqual(result.residual_score, 1.0)

    def test_retrieve_scores_descending(self):
        """Test that results are sorted by score descending."""
        query = np.random.randn(self.d).astype(np.float32)
        query = query / np.linalg.norm(query)

        results = self.retriever.retrieve(query, k=10, mode="raw")
        scores = [r.score for r in results]

        # Check descending order
        self.assertTrue(all(scores[i] >= scores[i+1] for i in range(len(scores)-1)))

    def test_retrieve_raw_mode(self):
        """Test raw retrieval mode."""
        query = np.random.randn(self.d).astype(np.float32)
        query = query / np.linalg.norm(query)

        results = self.retriever.retrieve(query, k=5, mode="raw")

        self.assertEqual(len(results), 5)

    def test_retrieve_projected_mode(self):
        """Test projected retrieval mode."""
        query = np.random.randn(self.d).astype(np.float32)
        query = query / np.linalg.norm(query)

        results = self.retriever.retrieve(query, k=5, mode="projected")

        self.assertEqual(len(results), 5)

    def test_retrieve_weighted_mode(self):
        """Test weighted retrieval mode."""
        query = np.random.randn(self.d).astype(np.float32)
        query = query / np.linalg.norm(query)

        results = self.retriever.retrieve(query, k=5, mode="weighted")

        self.assertEqual(len(results), 5)

    def test_retrieve_with_custom_weights(self):
        """Test weighted mode with custom weights."""
        query = np.random.randn(self.d).astype(np.float32)
        query = query / np.linalg.norm(query)

        weights = np.ones(self.k, dtype=np.float32) * 2.0

        results = self.retriever.retrieve(query, k=5, mode="weighted", weights=weights)

        self.assertEqual(len(results), 5)

    def test_retrieve_invalid_mode(self):
        """Test that invalid mode raises ValueError."""
        query = np.random.randn(self.d).astype(np.float32)

        with self.assertRaises(ValueError):
            self.retriever.retrieve(query, k=5, mode="invalid_mode")

    def test_retrieve_with_filter_fn(self):
        """Test filter function."""
        query = np.random.randn(self.d).astype(np.float32)
        query = query / np.linalg.norm(query)

        # Filter to only even-numbered icons
        def filter_fn(icon_id):
            num = int(icon_id.split("_")[1])
            return num % 2 == 0

        results = self.retriever.retrieve(query, k=10, mode="raw", filter_fn=filter_fn)

        # All results should be even-numbered
        for result in results:
            num = int(result.icon_id.split("_")[1])
            self.assertEqual(num % 2, 0)

    def test_retrieve_with_coordinates(self):
        """Test include_coordinates option."""
        query = np.random.randn(self.d).astype(np.float32)
        query = query / np.linalg.norm(query)

        results = self.retriever.retrieve(
            query, k=5, mode="raw", include_coordinates=True
        )

        for result in results:
            self.assertIsNotNone(result.coordinates)
            self.assertEqual(result.coordinates.shape, (self.k,))


class TestRetrieveByIcon(MockRetrieverTestCase):
    """Test retrieve_by_icon method."""

    def test_retrieve_by_icon_basic(self):
        """Test basic icon-to-icon retrieval."""
        results = self.retriever.retrieve_by_icon("icon_0", k=5)

        self.assertEqual(len(results), 5)
        # Should not include the query icon itself
        icon_ids = [r.icon_id for r in results]
        self.assertNotIn("icon_0", icon_ids)

    def test_retrieve_by_icon_exclude_self(self):
        """Test that exclude_self=True removes query icon."""
        results = self.retriever.retrieve_by_icon("icon_0", k=5, exclude_self=True)

        icon_ids = [r.icon_id for r in results]
        self.assertNotIn("icon_0", icon_ids)

    def test_retrieve_by_icon_include_self(self):
        """Test that exclude_self=False includes query icon."""
        results = self.retriever.retrieve_by_icon("icon_0", k=5, exclude_self=False)

        # First result should be the icon itself (most similar)
        self.assertEqual(results[0].icon_id, "icon_0")
        np.testing.assert_allclose(results[0].score, 1.0, atol=1e-5)

    def test_retrieve_by_icon_not_found(self):
        """Test that unknown icon raises KeyError."""
        with self.assertRaises(KeyError):
            self.retriever.retrieve_by_icon("nonexistent_icon", k=5)


class TestTraverseAxis(MockRetrieverTestCase):
    """Test traverse_axis method."""

    def test_traverse_positive(self):
        """Test traversal in positive direction."""
        icons = self.retriever.traverse_axis("icon_0", axis=0, steps=3, direction="positive")

        self.assertEqual(len(icons), 3)

    def test_traverse_negative(self):
        """Test traversal in negative direction."""
        icons = self.retriever.traverse_axis("icon_0", axis=0, steps=3, direction="negative")

        self.assertEqual(len(icons), 3)

    def test_traverse_both(self):
        """Test traversal in both directions."""
        icons = self.retriever.traverse_axis("icon_0", axis=0, steps=3, direction="both")

        # Should include: 3 negative + center + 3 positive = 7
        self.assertEqual(len(icons), 7)

        # Center should be the query icon
        self.assertEqual(icons[3], "icon_0")

    def test_traverse_invalid_axis(self):
        """Test that invalid axis raises ValueError."""
        with self.assertRaises(ValueError):
            self.retriever.traverse_axis("icon_0", axis=self.k + 10, steps=3)

    def test_traverse_icon_not_found(self):
        """Test that unknown icon raises KeyError."""
        with self.assertRaises(KeyError):
            self.retriever.traverse_axis("nonexistent", axis=0, steps=3)


class TestInterpolate(MockRetrieverTestCase):
    """Test interpolate method."""

    def test_interpolate_basic(self):
        """Test basic interpolation."""
        icons = self.retriever.interpolate("icon_0", "icon_50", steps=5)

        self.assertEqual(len(icons), 5)

    def test_interpolate_endpoints(self):
        """Test interpolation starts and ends at given icons."""
        icons = self.retriever.interpolate("icon_0", "icon_50", steps=5)

        # First should be icon_0 (or closest)
        self.assertEqual(icons[0], "icon_0")
        # Last should be icon_50 (or closest)
        self.assertEqual(icons[-1], "icon_50")

    def test_interpolate_icon_not_found(self):
        """Test that unknown icon raises KeyError."""
        with self.assertRaises(KeyError):
            self.retriever.interpolate("icon_0", "nonexistent", steps=5)

        with self.assertRaises(KeyError):
            self.retriever.interpolate("nonexistent", "icon_0", steps=5)


class TestOrthogonalResidualScore(MockRetrieverTestCase):
    """Test orthogonal_residual_score method."""

    def test_residual_score_range(self):
        """Test residual score is in [0, 1]."""
        # Create queries that are fully in subspace
        in_subspace = self.retriever.V_k[:, 0].copy()

        score = self.retriever._compute_residual_score(in_subspace)

        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_low_residual_for_icon_embedding(self):
        """Test that icon embeddings have low residual."""
        # Icon embeddings should mostly lie in the subspace
        icon_embedding = self.embeddings[0]

        score = self.retriever._compute_residual_score(icon_embedding)

        # Not necessarily very low, but should be < 1
        self.assertLess(score, 1.0)

    def test_orthogonal_query_high_residual(self):
        """Test that query orthogonal to subspace has high residual."""
        # Create a vector orthogonal to all basis vectors
        # Start with random vector, remove components in subspace
        q = np.random.randn(self.d).astype(np.float32)
        q_proj, _ = self.retriever.project_to_iconics(q)
        q_orth = q - q_proj

        if np.linalg.norm(q_orth) > 1e-6:
            q_orth = q_orth / np.linalg.norm(q_orth)

            score = self.retriever._compute_residual_score(q_orth)

            # Should be very close to 1.0 (fully outside subspace)
            self.assertGreater(score, 0.9)


class TestMathematicalProperties(MockRetrieverTestCase):
    """Integration tests for mathematical properties."""

    def test_pythagorean_multiple_queries(self):
        """Test Pythagorean theorem holds for many queries."""
        for _ in range(20):
            q = np.random.randn(self.d).astype(np.float32)

            q_proj, q_orth = self.retriever.project_to_iconics(q)

            norm_q_sq = np.sum(q ** 2)
            norm_proj_sq = np.sum(q_proj ** 2)
            norm_orth_sq = np.sum(q_orth ** 2)

            np.testing.assert_allclose(
                norm_q_sq,
                norm_proj_sq + norm_orth_sq,
                rtol=1e-4,
                err_msg="Pythagorean theorem violated"
            )

    def test_projection_idempotence_multiple(self):
        """Test projection idempotence for many queries."""
        for _ in range(20):
            q = np.random.randn(self.d).astype(np.float32)

            q_proj, _ = self.retriever.project_to_iconics(q)
            q_proj_again, _ = self.retriever.project_to_iconics(q_proj)

            np.testing.assert_allclose(
                q_proj_again,
                q_proj,
                atol=1e-5,
                err_msg="Projection not idempotent"
            )

    def test_orthogonality_multiple(self):
        """Test orthogonality for many queries."""
        for _ in range(20):
            q = np.random.randn(self.d).astype(np.float32)

            q_proj, q_orth = self.retriever.project_to_iconics(q)

            dot = np.dot(q_proj, q_orth)

            self.assertLess(
                abs(dot),
                1e-4,
                f"Components not orthogonal: dot={dot}"
            )

    def test_normalized_embeddings(self):
        """Test that all embeddings are normalized."""
        norms = np.linalg.norm(self.retriever.embeddings, axis=1)

        np.testing.assert_allclose(
            norms,
            np.ones(self.n_icons),
            atol=1e-5,
            err_msg="Embeddings not L2-normalized"
        )


class TestHelperMethods(MockRetrieverTestCase):
    """Test helper methods."""

    def test_get_icon_embedding(self):
        """Test get_icon_embedding returns correct embedding."""
        embedding = self.retriever.get_icon_embedding("icon_0")

        np.testing.assert_array_equal(embedding, self.embeddings[0])

    def test_get_icon_embedding_not_found(self):
        """Test get_icon_embedding raises KeyError for unknown icon."""
        with self.assertRaises(KeyError):
            self.retriever.get_icon_embedding("nonexistent")

    def test_get_icon_coordinates(self):
        """Test get_icon_coordinates returns correct shape."""
        coords = self.retriever.get_icon_coordinates("icon_0")

        self.assertEqual(coords.shape, (self.k,))

    def test_similarity(self):
        """Test similarity method."""
        sim = self.retriever.similarity("icon_0", "icon_0")

        # Self-similarity should be 1.0
        np.testing.assert_allclose(sim, 1.0, atol=1e-5)

    def test_similarity_symmetric(self):
        """Test that similarity is symmetric."""
        sim_ab = self.retriever.similarity("icon_0", "icon_1")
        sim_ba = self.retriever.similarity("icon_1", "icon_0")

        np.testing.assert_allclose(sim_ab, sim_ba)


if __name__ == "__main__":
    unittest.main(verbosity=2)
