"""
Iconics Configuration - Centralized path and config management

Resolution order:
1. Environment variable (ICONICS_ROOT)
2. Git repository root (if in repo)
3. Parent of current file's directory
"""

import os
from pathlib import Path
from functools import lru_cache


@lru_cache(maxsize=1)
def get_iconics_root() -> Path:
    """Get the Iconics root directory using multiple detection methods."""
    # 1. Environment variable
    if env_root := os.environ.get('ICONICS_ROOT'):
        return Path(env_root).resolve()

    # 2. Git root detection
    try:
        import subprocess
        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent,
            check=False
        )
        if result.returncode == 0:
            return Path(result.stdout.strip())
    except Exception:
        pass

    # 3. Relative to this file (src/iconics_config.py -> parent is iconics/)
    return Path(__file__).parent.parent.resolve()


# Root directory
ICONICS_ROOT = get_iconics_root()

# Derived paths
RAW_DIR = ICONICS_ROOT / "raw"
CATALOG_FILE = ICONICS_ROOT / "icon-catalog.json"
CATALOG_DIR = ICONICS_ROOT / "catalog"
EMBEDDINGS_DIR = ICONICS_ROOT / "embeddings"
EMBEDDINGS_ARRAY_FILE = EMBEDDINGS_DIR / "icon_embeddings.npy"
EMBEDDINGS_INDEX_FILE = EMBEDDINGS_DIR / "icon_index.json"
EMBEDDINGS_METADATA_FILE = EMBEDDINGS_DIR / "metadata.json"
SUBSPACE_DIR = EMBEDDINGS_DIR / "subspace"
SUBSPACE_BASIS_FILE = SUBSPACE_DIR / "basis_vectors.npy"
SUBSPACE_DIM_FILE = SUBSPACE_DIR / "effective_dim.json"
SUBSPACE_SINGULAR_VALUES_FILE = SUBSPACE_DIR / "singular_values.npy"
EVAL_DIR = ICONICS_ROOT / "eval"
HISTORY_FILE = ICONICS_ROOT / ".icon-history.json"
ANALYTICS_FILE = ICONICS_ROOT / ".icon-analytics.json"
CONFIG_FILE = ICONICS_ROOT / "config.yaml"
TEMPLATES_FILE = ICONICS_ROOT / "icon-templates.json"


# Environment configuration
CLIP_MODEL = os.environ.get("ICONICS_CLIP_MODEL", "ViT-L-14")
PRETRAINED = os.environ.get("ICONICS_PRETRAINED", "laion2b_s32b_b82k")
DEVICE = os.environ.get("ICONICS_DEVICE", "cuda")
LOG_LEVEL = os.environ.get('ICONICS_LOG_LEVEL', 'INFO')
