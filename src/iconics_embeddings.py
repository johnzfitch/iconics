"""
Iconics CLIP Embedding Generation Module

This module provides functions for generating CLIP embeddings from icon images
and text queries. It handles batch processing, normalization, and persistence
of embeddings for the Iconics vector search system.

Example:
    >>> from pathlib import Path
    >>> from iconics_embeddings import load_clip_model, embed_icons, save_embeddings
    >>>
    >>> # Load CLIP model
    >>> model, preprocess, tokenizer = load_clip_model()
    >>>
    >>> # Generate embeddings for all icons
    >>> icon_paths = list(Path("raw").glob("*.png"))
    >>> embeddings, index = embed_icons(icon_paths, model, preprocess)
    >>>
    >>> # Save to disk
    >>> save_embeddings(embeddings, index, Path("embeddings"))
"""

import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
from PIL import Image
from tqdm import tqdm

from iconics_config import (
    CLIP_MODEL,
    DEVICE,
    EMBEDDINGS_ARRAY_FILE,
    EMBEDDINGS_DIR,
    EMBEDDINGS_INDEX_FILE,
    EMBEDDINGS_METADATA_FILE,
    PRETRAINED,
)

try:
    import open_clip
except ImportError:  # pragma: no cover
    class _MissingOpenCLIP:
        def create_model_and_transforms(self, *args, **kwargs):
            raise ModuleNotFoundError("open_clip is not installed")

        def get_tokenizer(self, *args, **kwargs):
            raise ModuleNotFoundError("open_clip is not installed")

    open_clip = _MissingOpenCLIP()

logger = logging.getLogger(__name__)


class CLIPUnavailableError(ModuleNotFoundError, RuntimeError):
    """Raised when CLIP dependencies or weights are unavailable."""


def _raise_clip_unavailable(message: str, *, cause: Exception | None = None) -> None:
    error = CLIPUnavailableError(message)
    if cause is not None:
        raise error from cause
    raise error


def load_embedding_metadata(embeddings_dir: Path = EMBEDDINGS_DIR) -> Dict:
    """Load embedding metadata if present, otherwise return an empty dict."""
    metadata_path = Path(embeddings_dir) / EMBEDDINGS_METADATA_FILE.name
    if not metadata_path.exists():
        return {}

    import json

    try:
        with open(metadata_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {}
    if not isinstance(data, dict):
        return {}
    return data


def load_clip_model(
    model_name: str = CLIP_MODEL,
    pretrained: str = PRETRAINED,
    device: Optional[str] = None,
) -> Tuple[torch.nn.Module, callable, callable]:
    """
    Load OpenCLIP model with caching and auto-device detection.

    Args:
        model_name: CLIP model architecture (e.g., "ViT-B-32", "ViT-L-14")
        pretrained: Pretrained weights identifier (e.g., "laion2b_s34b_b79k")
        device: Target device ("cuda", "cpu", or None for auto-detection)

    Returns:
        Tuple of (model, preprocess_fn, tokenizer)

    Example:
        >>> model, preprocess, tokenizer = load_clip_model()
        >>> model.eval()  # Set to evaluation mode
    """
    # Auto-detect device if not specified
    if device is None:
        device = DEVICE if DEVICE in {"cuda", "cpu"} else ("cuda" if torch.cuda.is_available() else "cpu")
    if device == "cuda" and not torch.cuda.is_available():
        logger.warning("CUDA requested but unavailable; falling back to CPU")
        device = "cpu"

    logger.info(f"Loading CLIP model: {model_name} ({pretrained}) on {device}")
    start_time = time.time()

    try:
        # Load model with OpenCLIP
        model, _, preprocess = open_clip.create_model_and_transforms(
            model_name=model_name,
            pretrained=pretrained,
            device=device,
        )
        tokenizer = open_clip.get_tokenizer(model_name)

        # Set to evaluation mode and disable gradients
        model.eval()
        for param in model.parameters():
            param.requires_grad = False

        load_time = time.time() - start_time
        logger.info(f"Model loaded successfully in {load_time:.2f}s")

        return model, preprocess, tokenizer

    except Exception as e:
        logger.error(f"Failed to load CLIP model: {e}")
        _raise_clip_unavailable(
            f"Could not load CLIP model '{model_name}' with pretrained '{pretrained}': {e}",
            cause=e,
        )


def embed_icons(
    icon_paths: List[Path],
    model: torch.nn.Module,
    preprocess: callable,
    batch_size: int = 64,
    device: str = "cuda",
) -> Tuple[np.ndarray, Dict[str, int]]:
    """
    Generate CLIP embeddings for a batch of icon images.

    Processes images in batches through the CLIP vision encoder and normalizes
    embeddings to unit sphere. Skips corrupt or missing images with warnings.

    Args:
        icon_paths: List of paths to PNG icon files
        model: CLIP model instance
        preprocess: CLIP preprocessing function
        batch_size: Number of images to process per batch
        device: Target device for computation

    Returns:
        Tuple of (embeddings_array, icon_id_to_row_index_mapping)
        - embeddings_array: (N, D) normalized embeddings
        - mapping: dict mapping icon_id (stem) to row index

    Example:
        >>> from pathlib import Path
        >>> model, preprocess, _ = load_clip_model()
        >>> paths = list(Path("raw").glob("*.png"))
        >>> embeddings, index = embed_icons(paths, model, preprocess)
        >>> print(embeddings.shape)  # (N, 512) for ViT-B-32
    """
    if not icon_paths:
        raise ValueError("No icon paths provided")

    logger.info(f"Embedding {len(icon_paths)} icons in batches of {batch_size}")

    embeddings_list = []
    icon_index = {}
    skipped = 0
    current_row = 0

    # Process in batches
    for i in tqdm(range(0, len(icon_paths), batch_size), desc="Embedding icons"):
        batch_paths = icon_paths[i:i + batch_size]
        batch_images = []
        batch_ids = []

        # Load and preprocess images
        for path in batch_paths:
            try:
                image = Image.open(path).convert("RGB")
                processed = preprocess(image).unsqueeze(0)
                batch_images.append(processed)
                batch_ids.append(path.stem)
            except Exception as e:
                logger.warning(f"Skipping corrupt/missing image {path}: {e}")
                skipped += 1
                continue

        if not batch_images:
            continue

        # Stack batch and move to device
        batch_tensor = torch.cat(batch_images, dim=0).to(device)

        # Generate embeddings (inference_mode is ~5% faster than no_grad)
        with torch.inference_mode():
            batch_embeddings = model.encode_image(batch_tensor)
            batch_embeddings = batch_embeddings.cpu().numpy()

        # Normalize to unit sphere
        batch_embeddings = normalize_embeddings(batch_embeddings)

        # Update index mapping
        for icon_id in batch_ids:
            icon_index[icon_id] = current_row
            current_row += 1

        embeddings_list.append(batch_embeddings)

    if not embeddings_list:
        raise RuntimeError("No valid images could be processed")

    # Concatenate all batches
    embeddings = np.vstack(embeddings_list)

    logger.info(
        f"Generated {embeddings.shape[0]} embeddings "
        f"(dimension {embeddings.shape[1]}), skipped {skipped}"
    )

    return embeddings, icon_index


def embed_text(
    query: str,
    model: torch.nn.Module,
    tokenizer: callable,
    device: str = "cuda",
) -> np.ndarray:
    """
    Encode text query through CLIP text encoder.

    Args:
        query: Text query string
        model: CLIP model instance
        tokenizer: CLIP tokenizer function
        device: Target device for computation

    Returns:
        Normalized embedding vector (1, D)

    Raises:
        ValueError: If query is empty string

    Example:
        >>> model, _, tokenizer = load_clip_model()
        >>> embedding = embed_text("security lock icon", model, tokenizer)
        >>> print(embedding.shape)  # (1, 512) for ViT-B-32
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")

    # Tokenize text
    text_tokens = tokenizer([query]).to(device)

    # Generate embedding
    with torch.inference_mode():
        text_embedding = model.encode_text(text_tokens)
        text_embedding = text_embedding.cpu().numpy()

    # Normalize to unit sphere
    text_embedding = normalize_embeddings(text_embedding)

    return text_embedding


def embed_image(
    image_path: Path,
    model: torch.nn.Module,
    preprocess: callable,
    device: str = "cuda",
) -> np.ndarray:
    """
    Encode single image through CLIP vision encoder.

    Args:
        image_path: Path to image file
        model: CLIP model instance
        preprocess: CLIP preprocessing function
        device: Target device for computation

    Returns:
        Normalized embedding vector (1, D)

    Raises:
        FileNotFoundError: If image_path does not exist
        IOError: If image cannot be loaded

    Example:
        >>> model, preprocess, _ = load_clip_model()
        >>> embedding = embed_image(Path("raw/lock.png"), model, preprocess)
        >>> print(embedding.shape)  # (1, 512) for ViT-B-32
    """
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    try:
        # Load and preprocess image
        image = Image.open(image_path).convert("RGB")
        processed = preprocess(image).unsqueeze(0).to(device)

        # Generate embedding
        with torch.inference_mode():
            embedding = model.encode_image(processed)
            embedding = embedding.cpu().numpy()

        # Normalize to unit sphere
        embedding = normalize_embeddings(embedding)

        return embedding

    except Exception as e:
        logger.error(f"Failed to embed image {image_path}: {e}")
        raise IOError(f"Could not load or process image: {e}")


def normalize_embeddings(embeddings: np.ndarray) -> np.ndarray:
    """
    L2 normalize embedding vectors to unit sphere.

    Args:
        embeddings: Array of shape (N, D) or (D,)

    Returns:
        Normalized embeddings with same shape as input

    Example:
        >>> embeddings = np.random.randn(100, 512)
        >>> normalized = normalize_embeddings(embeddings)
        >>> norms = np.linalg.norm(normalized, axis=1)
        >>> assert np.allclose(norms, 1.0)
    """
    # Handle 1D arrays
    if embeddings.ndim == 1:
        norm = np.linalg.norm(embeddings)
        if norm == 0:
            logger.warning("Zero vector provided to normalize_embeddings")
            return embeddings
        return embeddings / norm

    # Handle 2D arrays
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)

    # Avoid division by zero
    norms = np.where(norms == 0, 1, norms)

    return embeddings / norms


def save_embeddings(
    embeddings: np.ndarray,
    index: Dict[str, int],
    output_dir: Path,
    metadata: Optional[Dict] = None,
) -> None:
    """
    Save embeddings, index, and metadata to disk.

    Creates three files:
    - icon_embeddings.npy: Numpy array of embeddings
    - icon_index.json: Icon ID to row index mapping
    - metadata.json: Model info, timestamp, and counts

    Args:
        embeddings: Numpy array of shape (N, D)
        index: Dict mapping icon_id to row index
        output_dir: Directory to save files
        metadata: Optional additional metadata to include

    Example:
        >>> embeddings = np.random.randn(100, 512)
        >>> index = {f"icon_{i}": i for i in range(100)}
        >>> save_embeddings(embeddings, index, Path("embeddings"))
    """
    import json

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save embeddings
    embeddings_path = output_dir / EMBEDDINGS_ARRAY_FILE.name
    np.save(embeddings_path, embeddings)
    logger.info(f"Saved embeddings to {embeddings_path}")

    # Save index
    index_path = output_dir / EMBEDDINGS_INDEX_FILE.name
    with open(index_path, "w") as f:
        json.dump(index, f, indent=2)
    logger.info(f"Saved index to {index_path}")

    # Build metadata
    meta = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "count": len(index),
        "dimension": embeddings.shape[1],
        "dtype": str(embeddings.dtype),
        "model": CLIP_MODEL,
        "pretrained": PRETRAINED,
        "device": device_from_metadata(metadata),
    }

    if metadata:
        meta.update(metadata)

    # Save metadata
    metadata_path = output_dir / EMBEDDINGS_METADATA_FILE.name
    with open(metadata_path, "w") as f:
        json.dump(meta, f, indent=2)
    logger.info(f"Saved metadata to {metadata_path}")


def load_embeddings(
    embeddings_dir: Path,
) -> Tuple[np.ndarray, Dict[str, int], Dict]:
    """
    Load embeddings, index, and metadata from disk.

    Args:
        embeddings_dir: Directory containing saved embeddings

    Returns:
        Tuple of (embeddings_array, index_dict, metadata_dict)

    Raises:
        FileNotFoundError: If any required file is missing
        ValueError: If loaded data is invalid

    Example:
        >>> embeddings, index, metadata = load_embeddings(Path("embeddings"))
        >>> print(f"Loaded {len(index)} embeddings")
    """
    import json

    # Check directory exists
    embeddings_dir = Path(embeddings_dir)
    if not embeddings_dir.exists():
        raise FileNotFoundError(f"Embeddings directory not found: {embeddings_dir}")

    # Load embeddings
    embeddings_path = embeddings_dir / EMBEDDINGS_ARRAY_FILE.name
    if not embeddings_path.exists():
        raise FileNotFoundError(f"Embeddings file not found: {embeddings_path}")
    embeddings = np.load(embeddings_path, allow_pickle=False)
    logger.info(f"Loaded embeddings from {embeddings_path}: {embeddings.shape}")

    # Load index
    index_path = embeddings_dir / EMBEDDINGS_INDEX_FILE.name
    if not index_path.exists():
        raise FileNotFoundError(f"Index file not found: {index_path}")
    with open(index_path, "r") as f:
        index = json.load(f)
    logger.info(f"Loaded index from {index_path}: {len(index)} entries")

    # Load metadata
    metadata_path = embeddings_dir / EMBEDDINGS_METADATA_FILE.name
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
    with open(metadata_path, "r") as f:
        metadata = json.load(f)
    logger.info(f"Loaded metadata from {metadata_path}")

    # Validate consistency
    if len(index) != embeddings.shape[0]:
        raise ValueError(
            f"Index size ({len(index)}) does not match embeddings shape ({embeddings.shape[0]})"
        )

    return embeddings, index, metadata


def device_from_metadata(metadata: Optional[Dict]) -> str:
    """Resolve a persisted device name if present."""
    if not isinstance(metadata, dict):
        return "cuda" if torch.cuda.is_available() else "cpu"
    device = metadata.get("device")
    if isinstance(device, str) and device.strip():
        return device
    return "cuda" if torch.cuda.is_available() else "cpu"


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Load model
    model, preprocess, tokenizer = load_clip_model()

    workspace = EMBEDDINGS_DIR.parent
    raw_dir = workspace / "raw"
    icon_paths = sorted(raw_dir.glob("*.png"))

    print(f"Found {len(icon_paths)} icon files")

    # Generate embeddings
    embeddings, index = embed_icons(icon_paths, model, preprocess)

    # Save to disk
    output_dir = EMBEDDINGS_DIR
    metadata = {
        "model": CLIP_MODEL,
        "pretrained": PRETRAINED,
        "device": "cuda" if torch.cuda.is_available() else "cpu",
    }
    save_embeddings(embeddings, index, output_dir, metadata)

    print(f"Embeddings saved to {output_dir}")

    # Test text embedding
    query = "security lock icon"
    query_embedding = embed_text(query, model, tokenizer)
    print(f"Query embedding shape: {query_embedding.shape}")

    # Test similarity search
    similarities = embeddings @ query_embedding.T
    top_k = np.argsort(similarities.flatten())[-10:][::-1]

    print(f"\nTop 10 matches for '{query}':")
    reverse_index = {v: k for k, v in index.items()}
    for idx in top_k:
        icon_id = reverse_index[idx]
        score = similarities[idx, 0]
        print(f"  {icon_id}: {score:.4f}")
