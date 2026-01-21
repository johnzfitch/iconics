#!/usr/bin/env python3
"""Generate embeddings for all icons in the iconics library."""

import sys

import logging
from pathlib import Path
from iconics_embeddings import load_clip_model, embed_icons, save_embeddings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from iconics_config import ICONICS_ROOT as workspace

def main():
    raw_dir = workspace / "raw"
    output_dir = workspace / "embeddings"

    # Get all PNG files
    icon_paths = sorted(raw_dir.glob("*.png"))
    logger.info(f"Found {len(icon_paths)} icons to process")

    # Load CLIP model
    logger.info("Loading CLIP model...")
    model, preprocess, tokenizer = load_clip_model(device="cuda")
    logger.info("Model loaded successfully")

    # Generate embeddings
    logger.info("Generating embeddings...")
    embeddings, index = embed_icons(icon_paths, model, preprocess, batch_size=64)
    logger.info(f"Generated {embeddings.shape[0]} embeddings of dimension {embeddings.shape[1]}")

    # Save embeddings
    logger.info("Saving embeddings...")
    metadata = {
        "model": "ViT-B-32",
        "pretrained": "laion2b_s34b_b79k",
        "source_dir": str(raw_dir),
    }
    save_embeddings(embeddings, index, output_dir, metadata)
    logger.info(f"Embeddings saved to {output_dir}")

    # Verify
    import numpy as np
    saved_emb = np.load(output_dir / "icon_embeddings.npy")
    logger.info(f"Verification: Loaded {saved_emb.shape[0]} embeddings")

    print(f"\n=== EMBEDDING GENERATION COMPLETE ===")
    print(f"Total icons processed: {embeddings.shape[0]}")
    print(f"Embedding dimension: {embeddings.shape[1]}")
    print(f"Output directory: {output_dir}")

if __name__ == "__main__":
    main()
