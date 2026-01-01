"""
Unit tests for iconics_embeddings module.

These tests use mocks to avoid loading the real CLIP model and processing
actual images. They focus on validating the logic, error handling, and
data flow of the embedding module.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pytest
import torch

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from iconics_embeddings import (
    embed_icons,
    embed_image,
    embed_text,
    load_clip_model,
    load_embeddings,
    normalize_embeddings,
    save_embeddings,
)


class TestNormalizeEmbeddings:
    """Test embedding normalization."""

    def test_normalize_2d_array(self):
        """Test normalizing 2D array to unit sphere."""
        embeddings = np.random.randn(100, 512)
        normalized = normalize_embeddings(embeddings)

        # Check shape preserved
        assert normalized.shape == embeddings.shape

        # Check unit norm
        norms = np.linalg.norm(normalized, axis=1)
        assert np.allclose(norms, 1.0)

    def test_normalize_1d_array(self):
        """Test normalizing 1D vector."""
        embedding = np.random.randn(512)
        normalized = normalize_embeddings(embedding)

        # Check shape preserved
        assert normalized.shape == embedding.shape

        # Check unit norm
        norm = np.linalg.norm(normalized)
        assert np.isclose(norm, 1.0)

    def test_normalize_zero_vector(self):
        """Test normalizing zero vector (should return zero)."""
        embedding = np.zeros(512)
        normalized = normalize_embeddings(embedding)

        # Should return zero vector unchanged
        assert np.allclose(normalized, 0.0)

    def test_normalize_already_normalized(self):
        """Test normalizing already-normalized embeddings."""
        # Create random unit vectors
        embeddings = np.random.randn(100, 512)
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

        # Normalize again
        normalized = normalize_embeddings(embeddings)

        # Should be unchanged
        assert np.allclose(normalized, embeddings)

    def test_normalize_preserves_direction(self):
        """Test that normalization preserves vector direction."""
        embedding = np.array([3.0, 4.0])
        normalized = normalize_embeddings(embedding)

        # Should be [0.6, 0.8]
        expected = np.array([0.6, 0.8])
        assert np.allclose(normalized, expected)


class TestLoadClipModel:
    """Test CLIP model loading."""

    @patch("iconics_embeddings.open_clip.create_model_and_transforms")
    @patch("iconics_embeddings.open_clip.get_tokenizer")
    @patch("iconics_embeddings.torch.cuda.is_available")
    def test_load_model_auto_cuda(
        self, mock_cuda_available, mock_get_tokenizer, mock_create_model
    ):
        """Test loading model with auto-detection of CUDA."""
        mock_cuda_available.return_value = True

        # Mock model
        mock_model = Mock()
        mock_model.eval.return_value = mock_model
        mock_model.parameters.return_value = [Mock()]

        mock_preprocess = Mock()
        mock_tokenizer = Mock()

        mock_create_model.return_value = (mock_model, None, mock_preprocess)
        mock_get_tokenizer.return_value = mock_tokenizer

        # Load model
        model, preprocess, tokenizer = load_clip_model()

        # Verify CUDA was used
        mock_create_model.assert_called_once()
        call_kwargs = mock_create_model.call_args[1]
        assert call_kwargs["device"] == "cuda"

        # Verify model setup
        mock_model.eval.assert_called_once()

        assert model is mock_model
        assert preprocess is mock_preprocess
        assert tokenizer is mock_tokenizer

    @patch("iconics_embeddings.open_clip.create_model_and_transforms")
    @patch("iconics_embeddings.open_clip.get_tokenizer")
    @patch("iconics_embeddings.torch.cuda.is_available")
    def test_load_model_auto_cpu(
        self, mock_cuda_available, mock_get_tokenizer, mock_create_model
    ):
        """Test loading model with auto-detection of CPU."""
        mock_cuda_available.return_value = False

        # Mock model
        mock_model = Mock()
        mock_model.eval.return_value = mock_model
        mock_model.parameters.return_value = [Mock()]

        mock_preprocess = Mock()
        mock_tokenizer = Mock()

        mock_create_model.return_value = (mock_model, None, mock_preprocess)
        mock_get_tokenizer.return_value = mock_tokenizer

        # Load model
        model, preprocess, tokenizer = load_clip_model()

        # Verify CPU was used
        call_kwargs = mock_create_model.call_args[1]
        assert call_kwargs["device"] == "cpu"

    @patch("iconics_embeddings.open_clip.create_model_and_transforms")
    @patch("iconics_embeddings.open_clip.get_tokenizer")
    def test_load_model_explicit_device(self, mock_get_tokenizer, mock_create_model):
        """Test loading model with explicit device."""
        # Mock model
        mock_model = Mock()
        mock_model.eval.return_value = mock_model
        mock_model.parameters.return_value = [Mock()]

        mock_preprocess = Mock()
        mock_tokenizer = Mock()

        mock_create_model.return_value = (mock_model, None, mock_preprocess)
        mock_get_tokenizer.return_value = mock_tokenizer

        # Load with explicit device
        load_clip_model(device="cpu")

        # Verify device was used
        call_kwargs = mock_create_model.call_args[1]
        assert call_kwargs["device"] == "cpu"

    @patch("iconics_embeddings.open_clip.create_model_and_transforms")
    def test_load_model_failure(self, mock_create_model):
        """Test handling of model loading failure."""
        mock_create_model.side_effect = RuntimeError("Model not found")

        with pytest.raises(RuntimeError, match="Could not load CLIP model"):
            load_clip_model()


class TestEmbedText:
    """Test text embedding."""

    def test_embed_text_success(self):
        """Test successful text embedding."""
        # Mock model and tokenizer
        mock_model = Mock()
        mock_tokenizer = Mock()

        # Mock tokenizer output
        mock_tokens = Mock()
        mock_tokens.to.return_value = mock_tokens
        mock_tokenizer.return_value = mock_tokens

        # Mock model output (not normalized)
        mock_embedding = torch.tensor([[3.0, 4.0]])
        mock_model.encode_text.return_value = mock_embedding

        # Embed text
        result = embed_text("test query", mock_model, mock_tokenizer, device="cpu")

        # Verify calls
        mock_tokenizer.assert_called_once_with(["test query"])
        mock_tokens.to.assert_called_once_with("cpu")
        mock_model.encode_text.assert_called_once_with(mock_tokens)

        # Verify normalization
        expected = np.array([[0.6, 0.8]])
        assert np.allclose(result, expected)

    def test_embed_text_empty_string(self):
        """Test that empty string raises ValueError."""
        mock_model = Mock()
        mock_tokenizer = Mock()

        with pytest.raises(ValueError, match="Query cannot be empty"):
            embed_text("", mock_model, mock_tokenizer)

        with pytest.raises(ValueError, match="Query cannot be empty"):
            embed_text("   ", mock_model, mock_tokenizer)


class TestEmbedImage:
    """Test single image embedding."""

    @patch("iconics_embeddings.Image.open")
    def test_embed_image_success(self, mock_image_open):
        """Test successful image embedding."""
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            image_path = Path(f.name)

        try:
            # Mock PIL image
            mock_pil_image = Mock()
            mock_pil_image.convert.return_value = mock_pil_image
            mock_image_open.return_value = mock_pil_image

            # Mock model and preprocess
            mock_model = Mock()
            mock_preprocess = Mock()

            # Mock preprocessing output
            mock_tensor = Mock()
            mock_tensor.unsqueeze.return_value = mock_tensor
            mock_tensor.to.return_value = mock_tensor
            mock_preprocess.return_value = mock_tensor

            # Mock model output (not normalized)
            mock_embedding = torch.tensor([[3.0, 4.0]])
            mock_model.encode_image.return_value = mock_embedding

            # Embed image
            result = embed_image(image_path, mock_model, mock_preprocess, device="cpu")

            # Verify calls
            mock_image_open.assert_called_once_with(image_path)
            mock_pil_image.convert.assert_called_once_with("RGB")
            mock_preprocess.assert_called_once_with(mock_pil_image)
            mock_model.encode_image.assert_called_once_with(mock_tensor)

            # Verify normalization
            expected = np.array([[0.6, 0.8]])
            assert np.allclose(result, expected)

        finally:
            image_path.unlink()

    def test_embed_image_not_found(self):
        """Test that missing image raises FileNotFoundError."""
        mock_model = Mock()
        mock_preprocess = Mock()

        with pytest.raises(FileNotFoundError):
            embed_image(Path("/nonexistent/image.png"), mock_model, mock_preprocess)

    @patch("iconics_embeddings.Image.open")
    def test_embed_image_corrupt(self, mock_image_open):
        """Test that corrupt image raises IOError."""
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            image_path = Path(f.name)

        try:
            # Mock corrupt image
            mock_image_open.side_effect = IOError("Corrupt image")

            mock_model = Mock()
            mock_preprocess = Mock()

            with pytest.raises(IOError, match="Could not load or process image"):
                embed_image(image_path, mock_model, mock_preprocess)

        finally:
            image_path.unlink()


class TestEmbedIcons:
    """Test batch icon embedding."""

    @patch("iconics_embeddings.Image.open")
    def test_embed_icons_success(self, mock_image_open):
        """Test successful batch icon embedding."""
        # Create temporary files
        temp_files = []
        for i in range(5):
            f = tempfile.NamedTemporaryFile(
                suffix=".png", prefix=f"icon_{i}_", delete=False
            )
            temp_files.append(Path(f.name))
            f.close()

        try:
            # Mock PIL image
            mock_pil_image = Mock()
            mock_pil_image.convert.return_value = mock_pil_image
            mock_image_open.return_value = mock_pil_image

            # Mock model and preprocess
            mock_model = Mock()
            mock_preprocess = Mock()

            # Mock preprocessing output - must return actual tensors for torch.cat
            def mock_preprocess_fn(img):
                return torch.randn(3, 224, 224)

            mock_preprocess.side_effect = mock_preprocess_fn

            # Mock model output (batch of 2D embeddings)
            def mock_encode_image(batch):
                batch_size = batch.shape[0]
                return torch.randn(batch_size, 512)

            mock_model.encode_image.side_effect = mock_encode_image

            # Embed icons
            embeddings, index = embed_icons(
                temp_files, mock_model, mock_preprocess, batch_size=10, device="cpu"
            )

            # Verify output shape
            assert embeddings.shape == (5, 512)

            # Verify index
            assert len(index) == 5
            for path in temp_files:
                assert path.stem in index

            # Verify normalization
            norms = np.linalg.norm(embeddings, axis=1)
            assert np.allclose(norms, 1.0)

        finally:
            for f in temp_files:
                f.unlink()

    @patch("iconics_embeddings.Image.open")
    def test_embed_icons_skip_corrupt(self, mock_image_open):
        """Test that corrupt images are skipped with warning."""
        # Create temporary files
        temp_files = []
        for i in range(3):
            f = tempfile.NamedTemporaryFile(
                suffix=".png", prefix=f"icon_{i}_", delete=False
            )
            temp_files.append(Path(f.name))
            f.close()

        try:
            # Mock PIL image - fail on second image
            call_count = [0]

            def mock_open_side_effect(path):
                call_count[0] += 1
                if call_count[0] == 2:
                    raise IOError("Corrupt image")
                mock_img = Mock()
                mock_img.convert.return_value = mock_img
                return mock_img

            mock_image_open.side_effect = mock_open_side_effect

            # Mock model and preprocess
            mock_model = Mock()
            mock_preprocess = Mock()

            # Must return actual tensors
            def mock_preprocess_fn(img):
                return torch.randn(3, 224, 224)

            mock_preprocess.side_effect = mock_preprocess_fn

            # Mock model output
            def mock_encode_image(batch):
                batch_size = batch.shape[0]
                return torch.randn(batch_size, 512)

            mock_model.encode_image.side_effect = mock_encode_image

            # Embed icons
            embeddings, index = embed_icons(
                temp_files, mock_model, mock_preprocess, batch_size=10, device="cpu"
            )

            # Should have 2 embeddings (skipped middle one)
            assert embeddings.shape[0] == 2
            assert len(index) == 2

        finally:
            for f in temp_files:
                f.unlink()

    def test_embed_icons_empty_list(self):
        """Test that empty icon list raises ValueError."""
        mock_model = Mock()
        mock_preprocess = Mock()

        with pytest.raises(ValueError, match="No icon paths provided"):
            embed_icons([], mock_model, mock_preprocess)

    @patch("iconics_embeddings.Image.open")
    def test_embed_icons_all_corrupt(self, mock_image_open):
        """Test that all corrupt images raises RuntimeError."""
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            image_path = Path(f.name)

        try:
            # Mock corrupt image
            mock_image_open.side_effect = IOError("Corrupt image")

            mock_model = Mock()
            mock_preprocess = Mock()

            with pytest.raises(RuntimeError, match="No valid images could be processed"):
                embed_icons([image_path], mock_model, mock_preprocess)

        finally:
            image_path.unlink()


class TestSaveLoadEmbeddings:
    """Test saving and loading embeddings."""

    def test_save_embeddings(self):
        """Test saving embeddings to disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            # Create test data
            embeddings = np.random.randn(100, 512)
            index = {f"icon_{i}": i for i in range(100)}
            metadata = {"model": "ViT-B-32", "pretrained": "laion2b_s34b_b79k"}

            # Save
            save_embeddings(embeddings, index, output_dir, metadata)

            # Verify files exist
            assert (output_dir / "icon_embeddings.npy").exists()
            assert (output_dir / "icon_index.json").exists()
            assert (output_dir / "metadata.json").exists()

            # Verify contents
            saved_embeddings = np.load(output_dir / "icon_embeddings.npy")
            assert np.allclose(saved_embeddings, embeddings)

            with open(output_dir / "icon_index.json") as f:
                saved_index = json.load(f)
            assert saved_index == index

            with open(output_dir / "metadata.json") as f:
                saved_metadata = json.load(f)
            assert saved_metadata["model"] == "ViT-B-32"
            assert saved_metadata["count"] == 100
            assert saved_metadata["dimension"] == 512

    def test_load_embeddings(self):
        """Test loading embeddings from disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            # Create and save test data
            embeddings = np.random.randn(100, 512)
            index = {f"icon_{i}": i for i in range(100)}
            metadata = {"model": "ViT-B-32"}

            save_embeddings(embeddings, index, output_dir, metadata)

            # Load
            loaded_embeddings, loaded_index, loaded_metadata = load_embeddings(
                output_dir
            )

            # Verify
            assert np.allclose(loaded_embeddings, embeddings)
            assert loaded_index == index
            assert loaded_metadata["model"] == "ViT-B-32"

    def test_load_embeddings_missing_directory(self):
        """Test that missing directory raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="Embeddings directory not found"):
            load_embeddings(Path("/nonexistent/directory"))

    def test_load_embeddings_missing_file(self):
        """Test that missing file raises FileNotFoundError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            with pytest.raises(FileNotFoundError, match="Embeddings file not found"):
                load_embeddings(output_dir)

    def test_load_embeddings_inconsistent_data(self):
        """Test that inconsistent index/embeddings raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            # Create inconsistent data
            embeddings = np.random.randn(100, 512)
            index = {f"icon_{i}": i for i in range(50)}  # Wrong size
            metadata = {"model": "ViT-B-32"}

            save_embeddings(embeddings, index, output_dir, metadata)

            # Should raise on load
            with pytest.raises(ValueError, match="Index size.*does not match"):
                load_embeddings(output_dir)


class TestBatchProcessing:
    """Test batch processing logic."""

    @patch("iconics_embeddings.Image.open")
    def test_multiple_batches(self, mock_image_open):
        """Test processing icons across multiple batches."""
        # Create 15 temporary files (will be 3 batches of 5)
        temp_files = []
        for i in range(15):
            f = tempfile.NamedTemporaryFile(
                suffix=".png", prefix=f"icon_{i}_", delete=False
            )
            temp_files.append(Path(f.name))
            f.close()

        try:
            # Mock PIL image
            mock_pil_image = Mock()
            mock_pil_image.convert.return_value = mock_pil_image
            mock_image_open.return_value = mock_pil_image

            # Mock model and preprocess
            mock_model = Mock()
            mock_preprocess = Mock()

            # Must return actual tensors
            def mock_preprocess_fn(img):
                return torch.randn(3, 224, 224)

            mock_preprocess.side_effect = mock_preprocess_fn

            # Track batch sizes
            batch_sizes = []

            def mock_encode_image(batch):
                # Infer batch size from concatenated tensor
                batch_size = batch.shape[0]
                batch_sizes.append(batch_size)
                return torch.randn(batch_size, 512)

            mock_model.encode_image.side_effect = mock_encode_image

            # Embed icons with batch size of 5
            embeddings, index = embed_icons(
                temp_files, mock_model, mock_preprocess, batch_size=5, device="cpu"
            )

            # Should have 15 total embeddings
            assert embeddings.shape[0] == 15
            assert len(index) == 15

            # Should have made 3 batch calls
            assert len(batch_sizes) == 3

        finally:
            for f in temp_files:
                f.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
