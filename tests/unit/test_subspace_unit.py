"""
Unit tests for iconics_subspace.py

Tests mathematical properties and correctness of SVD-based subspace analysis.
"""

import unittest
import numpy as np
from pathlib import Path
import tempfile
import shutil
import sys

# Add src to path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from iconics_subspace import (
    compute_svd,
    select_effective_dim,
    build_projection_matrix,
    project_to_subspace,
    get_coordinates,
    analyze_components,
    save_subspace,
    load_subspace,
    SubspaceAnalysis
)


class TestComputeSVD(unittest.TestCase):
    """Test SVD computation and properties."""

    def setUp(self):
        """Create test embedding matrix."""
        np.random.seed(42)
        self.n_icons = 100
        self.embedding_dim = 64
        self.embeddings = np.random.randn(self.n_icons, self.embedding_dim).astype(np.float32)

    def test_svd_shapes(self):
        """Test that SVD returns correct shapes."""
        U, S, Vt = compute_svd(self.embeddings)

        self.assertEqual(U.shape, (self.n_icons, self.n_icons))
        self.assertEqual(S.shape, (min(self.n_icons, self.embedding_dim),))
        self.assertEqual(Vt.shape, (self.embedding_dim, self.embedding_dim))

    def test_svd_reconstruction(self):
        """Test X ≈ U @ diag(S) @ Vt reconstruction."""
        U, S, Vt = compute_svd(self.embeddings)

        # Reconstruct using reduced form: U[:, :k] @ diag(S[:k]) @ Vt[:k, :]
        k = len(S)
        reconstructed = U[:, :k] @ np.diag(S) @ Vt[:k, :]

        # Should reconstruct original matrix exactly
        np.testing.assert_allclose(
            reconstructed,
            self.embeddings,
            rtol=1e-4,
            atol=1e-6,
            err_msg="SVD reconstruction failed"
        )

    def test_singular_values_descending(self):
        """Test that singular values are in descending order."""
        _, S, _ = compute_svd(self.embeddings)

        # Check descending order
        self.assertTrue(np.all(S[:-1] >= S[1:]), "Singular values not descending")
        self.assertTrue(np.all(S >= 0), "Negative singular values found")

    def test_orthonormality_U(self):
        """Test that U has orthonormal columns: U^T U = I."""
        U, _, _ = compute_svd(self.embeddings)

        # U^T @ U should be identity
        product = U.T @ U
        identity = np.eye(U.shape[1])

        np.testing.assert_allclose(
            product,
            identity,
            rtol=1e-5,
            atol=1e-7,
            err_msg="U does not have orthonormal columns"
        )

    def test_orthonormality_V(self):
        """Test that V has orthonormal columns: Vt^T Vt = I."""
        _, _, Vt = compute_svd(self.embeddings)

        # Vt.T @ Vt should be identity (since Vt = V^T)
        product = Vt.T @ Vt
        identity = np.eye(Vt.shape[0])

        np.testing.assert_allclose(
            product,
            identity,
            rtol=1e-5,
            atol=1e-7,
            err_msg="V does not have orthonormal columns"
        )

    def test_invalid_input(self):
        """Test that invalid input raises ValueError."""
        with self.assertRaises(ValueError):
            compute_svd(np.random.randn(10))  # 1D array

        with self.assertRaises(ValueError):
            compute_svd(np.random.randn(10, 10, 10))  # 3D array


class TestSelectEffectiveDim(unittest.TestCase):
    """Test effective dimensionality selection."""

    def setUp(self):
        """Create test singular values."""
        # Create singular values with known variance distribution
        # First 10 values are large, rest decay rapidly
        self.S = np.array([10.0, 9.0, 8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0] +
                          [0.5, 0.25, 0.1, 0.05, 0.01] * 10)

    def test_variance_threshold_selection(self):
        """Test that effective dim meets variance threshold."""
        k, analysis = select_effective_dim(self.S, variance_threshold=0.95)

        # Check that selected k explains >= 95% variance
        variance = self.S ** 2
        total_var = np.sum(variance)
        explained = np.sum(variance[:k]) / total_var

        self.assertGreaterEqual(
            explained,
            0.95,
            "Selected dimension does not meet variance threshold"
        )

    def test_analysis_metadata(self):
        """Test that analysis dictionary contains required fields."""
        k, analysis = select_effective_dim(self.S, variance_threshold=0.90)

        required_fields = [
            'total_variance',
            'explained_variance_ratio',
            'variance_threshold',
            'elbow_point',
            'variance_per_component'
        ]

        for field in required_fields:
            self.assertIn(field, analysis, f"Missing field: {field}")

        # Check types
        self.assertIsInstance(analysis['total_variance'], float)
        self.assertIsInstance(analysis['explained_variance_ratio'], float)
        self.assertIsInstance(analysis['variance_per_component'], list)

    def test_different_thresholds(self):
        """Test that higher threshold requires more dimensions."""
        k_90, _ = select_effective_dim(self.S, variance_threshold=0.90)
        k_95, _ = select_effective_dim(self.S, variance_threshold=0.95)
        k_99, _ = select_effective_dim(self.S, variance_threshold=0.99)

        # Higher threshold should require more dimensions
        self.assertLessEqual(k_90, k_95)
        self.assertLessEqual(k_95, k_99)


class TestBuildProjectionMatrix(unittest.TestCase):
    """Test projection matrix construction."""

    def setUp(self):
        """Create test basis vectors."""
        np.random.seed(42)
        self.d = 64
        self.k = 16

        # Create random orthonormal Vt
        random_matrix = np.random.randn(self.d, self.d)
        _, _, Vt = np.linalg.svd(random_matrix, full_matrices=True)
        self.Vt = Vt

    def test_projection_matrix_shape(self):
        """Test that projection matrix has correct shape."""
        P = build_projection_matrix(self.Vt, self.k)
        self.assertEqual(P.shape, (self.d, self.d))

    def test_projection_symmetry(self):
        """Test that P is symmetric: P^T = P."""
        P = build_projection_matrix(self.Vt, self.k)

        np.testing.assert_allclose(
            P,
            P.T,
            rtol=1e-5,
            atol=1e-7,
            err_msg="Projection matrix not symmetric"
        )

    def test_projection_idempotent(self):
        """Test that P is idempotent: P @ P = P."""
        P = build_projection_matrix(self.Vt, self.k)
        P_squared = P @ P

        np.testing.assert_allclose(
            P_squared,
            P,
            rtol=1e-5,
            atol=1e-7,
            err_msg="Projection matrix not idempotent"
        )

    def test_projection_rank(self):
        """Test that rank(P) = k."""
        P = build_projection_matrix(self.Vt, self.k)

        # Compute rank using SVD
        s = np.linalg.svd(P, compute_uv=False)
        rank = np.sum(s > 1e-10)

        self.assertEqual(rank, self.k, f"Projection rank {rank} != k {self.k}")

    def test_invalid_k(self):
        """Test that k > d raises ValueError."""
        with self.assertRaises(ValueError):
            build_projection_matrix(self.Vt, self.d + 1)


class TestProjectToSubspace(unittest.TestCase):
    """Test subspace projection."""

    def setUp(self):
        """Create test projection matrix and query vector."""
        np.random.seed(42)
        self.d = 64
        self.k = 16

        # Create orthonormal basis
        random_matrix = np.random.randn(self.d, self.d)
        _, _, Vt = np.linalg.svd(random_matrix, full_matrices=True)
        self.P = build_projection_matrix(Vt, self.k)

        # Create random query vector
        self.q = np.random.randn(self.d).astype(np.float32)

    def test_orthogonal_decomposition(self):
        """Test q = q_proj + q_orth where q_proj ⊥ q_orth."""
        q_proj, q_orth = project_to_subspace(self.q, self.P)

        # Test reconstruction
        reconstructed = q_proj + q_orth
        np.testing.assert_allclose(
            reconstructed,
            self.q,
            rtol=1e-5,
            atol=1e-7,
            err_msg="Projection decomposition failed"
        )

        # Test orthogonality
        dot_product = np.dot(q_proj, q_orth)
        self.assertAlmostEqual(
            dot_product,
            0.0,
            places=6,
            msg=f"Components not orthogonal: dot={dot_product}"
        )

    def test_pythagorean_theorem(self):
        """Test ||q||² = ||q_proj||² + ||q_orth||²."""
        q_proj, q_orth = project_to_subspace(self.q, self.P)

        norm_q_sq = np.sum(self.q ** 2)
        norm_proj_sq = np.sum(q_proj ** 2)
        norm_orth_sq = np.sum(q_orth ** 2)

        # Use relative tolerance for float32 precision
        np.testing.assert_allclose(
            norm_q_sq,
            norm_proj_sq + norm_orth_sq,
            rtol=1e-5,
            atol=1e-6,
            err_msg="Pythagorean theorem violated"
        )

    def test_projection_idempotence(self):
        """Test that projecting twice gives same result: P(Pq) = Pq."""
        q_proj, _ = project_to_subspace(self.q, self.P)
        q_proj_again, q_orth_again = project_to_subspace(q_proj, self.P)

        # Second projection should give same result
        np.testing.assert_allclose(
            q_proj_again,
            q_proj,
            rtol=1e-5,
            atol=1e-7,
            err_msg="Projection not idempotent"
        )

        # Orthogonal component should be zero
        self.assertLess(
            np.linalg.norm(q_orth_again),
            1e-6,
            "Projection of projected vector has non-zero orthogonal component"
        )

    def test_dimension_mismatch(self):
        """Test that dimension mismatch raises ValueError."""
        wrong_q = np.random.randn(self.d + 1)
        with self.assertRaises(ValueError):
            project_to_subspace(wrong_q, self.P)


class TestGetCoordinates(unittest.TestCase):
    """Test coordinate extraction in subspace basis."""

    def setUp(self):
        """Create test data."""
        np.random.seed(42)
        self.d = 64
        self.k = 16

        # Create orthonormal Vt
        random_matrix = np.random.randn(self.d, self.d)
        _, _, self.Vt = np.linalg.svd(random_matrix, full_matrices=True)

        # Create query vector
        self.q = np.random.randn(self.d).astype(np.float32)

    def test_coordinates_shape(self):
        """Test that coordinates have shape (k,)."""
        coords = get_coordinates(self.q, self.Vt, self.k)
        self.assertEqual(coords.shape, (self.k,))

    def test_reconstruction_from_coordinates(self):
        """Test that q ≈ V_k @ coords (projection)."""
        coords = get_coordinates(self.q, self.Vt, self.k)

        # Reconstruct: V_k @ coords
        V_k = self.Vt[:self.k, :].T  # Shape (d, k)
        reconstructed = V_k @ coords

        # This should equal the projection of q
        P = build_projection_matrix(self.Vt, self.k)
        q_proj = P @ self.q

        np.testing.assert_allclose(
            reconstructed,
            q_proj,
            rtol=1e-5,
            atol=1e-7,
            err_msg="Coordinate reconstruction failed"
        )

    def test_coordinates_are_projections(self):
        """Test that coordinates[i] = <q, v_i>."""
        coords = get_coordinates(self.q, self.Vt, self.k)

        # Manually compute dot products
        for i in range(self.k):
            v_i = self.Vt[i, :]  # i-th basis vector
            expected_coord = np.dot(self.q, v_i)

            self.assertAlmostEqual(
                coords[i],
                expected_coord,
                places=6,
                msg=f"Coordinate {i} incorrect"
            )


class TestAnalyzeComponents(unittest.TestCase):
    """Test component analysis."""

    def setUp(self):
        """Create test data."""
        np.random.seed(42)
        self.n_icons = 100
        self.d = 64
        self.k = 10

        # Create embeddings
        self.embeddings = np.random.randn(self.n_icons, self.d).astype(np.float32)

        # Compute SVD
        U, S, Vt = compute_svd(self.embeddings)
        self.U = U

        # Create icon index
        self.icon_index = {f"icon_{i}": i for i in range(self.n_icons)}

    def test_analysis_structure(self):
        """Test that analysis returns correct structure."""
        analysis = analyze_components(self.embeddings, self.U, self.k, self.icon_index)

        # Should have top and bottom for each component
        expected_keys = []
        for i in range(self.k):
            expected_keys.append(f"component_{i}_top")
            expected_keys.append(f"component_{i}_bottom")

        for key in expected_keys:
            self.assertIn(key, analysis, f"Missing key: {key}")

    def test_top_n_icons(self):
        """Test that correct number of icons returned."""
        top_n = 5
        analysis = analyze_components(
            self.embeddings, self.U, self.k, self.icon_index, top_n=top_n
        )

        for i in range(self.k):
            top_icons = analysis[f"component_{i}_top"]
            bottom_icons = analysis[f"component_{i}_bottom"]

            self.assertEqual(len(top_icons), top_n)
            self.assertEqual(len(bottom_icons), top_n)

    def test_loading_values(self):
        """Test that top icons have higher loadings than bottom."""
        analysis = analyze_components(self.embeddings, self.U, self.k, self.icon_index)

        for i in range(self.k):
            top_icons = analysis[f"component_{i}_top"]
            bottom_icons = analysis[f"component_{i}_bottom"]

            # Top loadings should be greater than bottom
            min_top_loading = min(loading for _, loading in top_icons)
            max_bottom_loading = max(loading for _, loading in bottom_icons)

            self.assertGreater(
                min_top_loading,
                max_bottom_loading,
                f"Component {i}: top loadings not > bottom loadings"
            )


class TestSaveLoadSubspace(unittest.TestCase):
    """Test saving and loading subspace results."""

    def setUp(self):
        """Create test data and temporary directory."""
        np.random.seed(42)
        self.d = 64
        self.k = 16

        # Create test SVD results
        random_matrix = np.random.randn(self.d, self.d)
        _, self.S, self.Vt = np.linalg.svd(random_matrix, full_matrices=True)

        # Create test analysis
        self.analysis = SubspaceAnalysis(
            effective_dim=self.k,
            total_variance=float(np.sum(self.S ** 2)),
            explained_variance_ratio=0.95,
            variance_threshold=0.95,
            elbow_point=12,
            component_correlations={"component_0_top": [("icon_1", 0.5)]}
        )

        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_save_creates_files(self):
        """Test that save creates all required files."""
        output_dir = Path(self.temp_dir)
        save_subspace(output_dir, self.S, self.Vt, self.k, self.analysis)

        # Check files exist
        self.assertTrue((output_dir / "singular_values.npy").exists())
        self.assertTrue((output_dir / "basis_vectors.npy").exists())
        self.assertTrue((output_dir / "effective_dim.json").exists())
        self.assertTrue((output_dir / "component_analysis.json").exists())

    def test_save_load_round_trip(self):
        """Test that save/load preserves data."""
        output_dir = Path(self.temp_dir)
        save_subspace(output_dir, self.S, self.Vt, self.k, self.analysis)

        # Load back
        S_loaded, V_k_loaded, k_loaded, metadata_loaded = load_subspace(output_dir)

        # Check singular values
        np.testing.assert_allclose(S_loaded, self.S, rtol=1e-6)

        # Check k
        self.assertEqual(k_loaded, self.k)

        # Check metadata
        self.assertEqual(metadata_loaded['effective_dim'], self.k)
        self.assertAlmostEqual(
            metadata_loaded['explained_variance_ratio'],
            self.analysis.explained_variance_ratio,
            places=6
        )

    def test_basis_vectors_shape(self):
        """Test that saved basis vectors have correct shape."""
        output_dir = Path(self.temp_dir)
        save_subspace(output_dir, self.S, self.Vt, self.k, self.analysis)

        V_k = np.load(output_dir / "basis_vectors.npy")
        self.assertEqual(V_k.shape, (self.d, self.k))


class TestMathematicalProperties(unittest.TestCase):
    """Integration tests for mathematical properties."""

    def setUp(self):
        """Create realistic test data."""
        np.random.seed(42)
        self.n_icons = 200
        self.d = 128

        # Create embeddings with structure
        # First 50 dimensions have large variance, rest have small variance
        latent_dim = 50
        latent_embeddings = np.random.randn(self.n_icons, latent_dim) * 2.0
        noise = np.random.randn(self.n_icons, self.d - latent_dim) * 0.1

        self.embeddings = np.hstack([latent_embeddings, noise]).astype(np.float32)

    def test_full_pipeline(self):
        """Test complete SVD pipeline."""
        # Compute SVD
        U, S, Vt = compute_svd(self.embeddings)

        # Select dimension
        k, analysis = select_effective_dim(S, variance_threshold=0.95)

        # Build projection
        P = build_projection_matrix(Vt, k)

        # Test random query
        q = np.random.randn(self.d).astype(np.float32)
        q_proj, q_orth = project_to_subspace(q, P)

        # Get coordinates
        coords = get_coordinates(q, Vt, k)

        # Verify all properties hold
        self.assertEqual(coords.shape, (k,))
        self.assertLess(np.linalg.norm(q - q_proj - q_orth), 1e-5)

    def test_variance_concentration(self):
        """Test that variance is concentrated in first k dimensions."""
        U, S, Vt = compute_svd(self.embeddings)
        k, analysis = select_effective_dim(S, variance_threshold=0.95)

        # First k singular values should explain ~95% variance
        variance = S ** 2
        total_var = np.sum(variance)
        explained = np.sum(variance[:k]) / total_var

        self.assertGreaterEqual(explained, 0.95)

        # k should be much less than d (dimensionality reduction)
        self.assertLess(k, self.d * 0.7)


if __name__ == "__main__":
    unittest.main(verbosity=2)
