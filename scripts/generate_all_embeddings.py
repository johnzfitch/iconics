#!/usr/bin/env python3
"""Generate embeddings for all icons in the iconics library."""

import sys

import logging
from pathlib import Path

import torch

from iconics_config import CLIP_MODEL, DEVICE, EMBEDDINGS_ARRAY_FILE, EMBEDDINGS_DIR, PRETRAINED
from iconics_embeddings import load_clip_model, embed_icons, save_embeddings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    workspace = EMBEDDINGS_DIR.parent
    raw_dir = workspace / "raw"
    output_dir = EMBEDDINGS_DIR
    requested_device = DEVICE if DEVICE in {"cuda", "cpu"} else None
    actual_device = requested_device or ("cuda" if torch.cuda.is_available() else "cpu")
    if actual_device == "cuda" and not torch.cuda.is_available():
        actual_device = "cpu"

    # Get all PNG files
    icon_paths = sorted(raw_dir.glob("*.png"))
    logger.info(f"Found {len(icon_paths)} icons to process")

    # Load CLIP model
    logger.info("Loading CLIP model...")
    model, preprocess, tokenizer = load_clip_model(model_name=CLIP_MODEL, pretrained=PRETRAINED, device=actual_device)
    logger.info("Model loaded successfully")

    # Generate embeddings
    logger.info("Generating embeddings...")
    embeddings, index = embed_icons(icon_paths, model, preprocess, batch_size=64)
    logger.info(f"Generated {embeddings.shape[0]} embeddings of dimension {embeddings.shape[1]}")

    # Save embeddings
    logger.info("Saving embeddings...")
    metadata = {
        "model": CLIP_MODEL,
        "pretrained": PRETRAINED,
        "source_dir": str(raw_dir),
        "device": actual_device,
    }
    save_embeddings(embeddings, index, output_dir, metadata)
    logger.info(f"Embeddings saved to {output_dir}")

    # Verify
    import numpy as np
    saved_emb = np.load(output_dir / EMBEDDINGS_ARRAY_FILE.name, allow_pickle=False)
    logger.info(f"Verification: Loaded {saved_emb.shape[0]} embeddings")

    print(f"\n=== EMBEDDING GENERATION COMPLETE ===")
    print(f"Total icons processed: {embeddings.shape[0]}")
    print(f"Embedding dimension: {embeddings.shape[1]}")
    print(f"Output directory: {output_dir}")

if __name__ == "__main__":
    main()
