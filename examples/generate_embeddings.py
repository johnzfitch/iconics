#!/usr/bin/env python3
"""
Example: Generate CLIP embeddings for all Iconics icons.

This script demonstrates the complete workflow:
1. Load CLIP model
2. Process all PNG icons in the raw/ directory
3. Generate normalized embeddings
4. Save embeddings with metadata
5. Perform sample similarity search

Usage:
    source ~/.local/share/python-global/bin/activate
    python3 examples/generate_embeddings.py
"""

import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import numpy as np
from iconics_embeddings import (
    embed_icons,
    embed_text,
    load_clip_model,
    save_embeddings,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """Generate embeddings for all icons."""
    workspace = Path(__file__).parent.parent
    raw_dir = workspace / "raw"
    embeddings_dir = workspace / "embeddings"

    # Load CLIP model
    logger.info("Loading CLIP model...")
    model, preprocess, tokenizer = load_clip_model(
        model_name="ViT-B-32",
        pretrained="laion2b_s34b_b79k",
        # device="cuda"  # Uncomment to use GPU
    )

    # Get all PNG icons
    icon_paths = sorted(raw_dir.glob("*.png"))
    logger.info(f"Found {len(icon_paths)} icon files")

    if not icon_paths:
        logger.error(f"No PNG files found in {raw_dir}")
        return 1

    # Generate embeddings
    logger.info("Generating embeddings...")
    embeddings, index = embed_icons(
        icon_paths,
        model,
        preprocess,
        batch_size=64,
        device="cuda",  # or "cpu"
    )

    logger.info(f"Generated {embeddings.shape[0]} embeddings (dimension {embeddings.shape[1]})")

    # Save embeddings
    metadata = {
        "model": "ViT-B-32",
        "pretrained": "laion2b_s34b_b79k",
        "total_icons": len(icon_paths),
        "successful": embeddings.shape[0],
        "failed": len(icon_paths) - embeddings.shape[0],
    }

    logger.info(f"Saving embeddings to {embeddings_dir}...")
    save_embeddings(embeddings, index, embeddings_dir, metadata)

    logger.info("✓ Embeddings generated and saved successfully!")

    # Example: Similarity search
    logger.info("\n--- Example Similarity Search ---")
    query = "security lock icon"
    logger.info(f"Query: '{query}'")

    query_embedding = embed_text(query, model, tokenizer)
    similarities = embeddings @ query_embedding.T
    top_k = np.argsort(similarities.flatten())[-10:][::-1]

    reverse_index = {v: k for k, v in index.items()}
    logger.info("Top 10 matches:")
    for rank, idx in enumerate(top_k, 1):
        icon_id = reverse_index[idx]
        score = similarities[idx, 0]
        logger.info(f"  {rank}. {icon_id}: {score:.4f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
