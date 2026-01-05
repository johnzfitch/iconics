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
SUBSPACE_DIR = ICONICS_ROOT / "subspace"
EVAL_DIR = ICONICS_ROOT / "eval"
HISTORY_FILE = ICONICS_ROOT / ".icon-history.json"
ANALYTICS_FILE = ICONICS_ROOT / ".icon-analytics.json"
CONFIG_FILE = ICONICS_ROOT / "config.yaml"
TEMPLATES_FILE = ICONICS_ROOT / "icon-templates.json"


# Environment configuration
CLIP_MODEL = os.environ.get('ICONICS_CLIP_MODEL', 'ViT-B-32')
PRETRAINED = os.environ.get('ICONICS_PRETRAINED', 'laion2b_s34b_b79k')
DEVICE = os.environ.get('ICONICS_DEVICE', 'cuda')
LOG_LEVEL = os.environ.get('ICONICS_LOG_LEVEL', 'INFO')
