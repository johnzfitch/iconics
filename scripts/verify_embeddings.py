#!/usr/bin/env python3
"""
Verify Iconics Embeddings Integrity

Checks:
1. File existence and loadability
2. Catalog/embeddings synchronization
3. Embedding normalization
4. Index consistency
5. Duplicate detection
"""

import sys
import json
from pathlib import Path
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from iconics_retrieval import IconicsRetriever


def check_files_exist(embeddings_dir: Path) -> bool:
    """Check all required files exist."""
    print("📁 Checking file existence...")

    required_files = [
        embeddings_dir / "icon_embeddings.npy",
        embeddings_dir / "icon_index.json",
        embeddings_dir / "metadata.json"
    ]

    all_exist = True
    for file_path in required_files:
        if file_path.exists():
            size_mb = file_path.stat().st_size / (1024 * 1024)
            print(f"   ✓ {file_path.name} ({size_mb:.2f} MB)")
        else:
            print(f"   ✗ {file_path.name} MISSING")
            all_exist = False

    return all_exist


def check_loadable(embeddings_dir: Path) -> tuple:
    """Check if files are loadable without errors."""
    print("\n🔍 Checking file integrity...")

    try:
        # Load embeddings
        embeddings = np.load(embeddings_dir / "icon_embeddings.npy")
        print(f"   ✓ Embeddings loaded: {embeddings.shape} ({embeddings.dtype})")

        # Load index
        with open(embeddings_dir / "icon_index.json") as f:
            index = json.load(f)
        print(f"   ✓ Index loaded: {len(index)} entries")

        # Load metadata
        with open(embeddings_dir / "metadata.json") as f:
            metadata = json.load(f)
        print(f"   ✓ Metadata loaded: {metadata.get('count')} icons, dim={metadata.get('dimension')}")

        return embeddings, index, metadata

    except Exception as e:
        print(f"   ✗ Load error: {e}")
        return None, None, None


def check_normalization(embeddings: np.ndarray) -> bool:
    """Check if embeddings are L2-normalized."""
    print("\n📏 Checking normalization...")

    norms = np.linalg.norm(embeddings, axis=1)
    mean_norm = np.mean(norms)
    std_norm = np.std(norms)
    min_norm = np.min(norms)
    max_norm = np.max(norms)

    print(f"   L2 norms: mean={mean_norm:.6f}, std={std_norm:.6f}")
    print(f"   Range: [{min_norm:.6f}, {max_norm:.6f}]")

    # Check if close to 1.0 (normalized)
    is_normalized = np.allclose(norms, 1.0, atol=1e-5)

    if is_normalized:
        print(f"   ✓ Embeddings are properly normalized")
    else:
        non_normalized = np.sum(~np.isclose(norms, 1.0, atol=1e-5))
        print(f"   ⚠ {non_normalized} embeddings not normalized")

    return is_normalized


def check_index_consistency(embeddings: np.ndarray, index: dict, metadata: dict) -> bool:
    """Check index consistency with embeddings."""
    print("\n🔗 Checking index consistency...")

    issues = []

    # Check counts match
    if len(index) != embeddings.shape[0]:
        issues.append(f"Index size ({len(index)}) != embeddings rows ({embeddings.shape[0]})")

    if metadata.get('count') != len(index):
        issues.append(f"Metadata count ({metadata.get('count')}) != index size ({len(index)})")

    if metadata.get('dimension') != embeddings.shape[1]:
        issues.append(f"Metadata dimension ({metadata.get('dimension')}) != embeddings dim ({embeddings.shape[1]})")

    # Check index values are contiguous 0..n-1
    expected_indices = set(range(len(index)))
    actual_indices = set(index.values())

    if expected_indices != actual_indices:
        missing = expected_indices - actual_indices
        extra = actual_indices - expected_indices
        if missing:
            issues.append(f"Missing indices: {sorted(missing)[:5]}...")
        if extra:
            issues.append(f"Extra indices: {sorted(extra)[:5]}...")

    # Check for duplicate icon IDs
    icon_ids = list(index.keys())
    unique_ids = set(icon_ids)
    if len(icon_ids) != len(unique_ids):
        duplicates = [id for id in unique_ids if icon_ids.count(id) > 1]
        issues.append(f"Duplicate icon IDs: {duplicates[:5]}")

    if issues:
        for issue in issues:
            print(f"   ✗ {issue}")
        return False
    else:
        print(f"   ✓ Index is consistent")
        return True


def check_catalog_sync(catalog_path: Path) -> dict:
    """Check synchronization with catalog using IconicsRetriever."""
    print("\n🔄 Checking catalog synchronization...")

    try:
        retriever = IconicsRetriever(
            embeddings_path='embeddings',
            subspace_path='subspace'
        )

        sync = retriever.validate_catalog_sync(catalog_path)

        missing_from_catalog = sync['in_embeddings_not_catalog']
        missing_from_embeddings = sync['in_catalog_not_embeddings']

        print(f"   Icons in embeddings: {len(retriever.icon_ids)}")

        # Load catalog to get total
        with open(catalog_path) as f:
            catalog_data = json.load(f)
        print(f"   Icons in catalog: {len(catalog_data['icons'])}")

        if missing_from_catalog:
            print(f"   ⚠ {len(missing_from_catalog)} icons in embeddings but NOT in catalog")
            print(f"      Examples: {missing_from_catalog[:5]}")
        else:
            print(f"   ✓ All embeddings exist in catalog")

        if missing_from_embeddings:
            print(f"   ⚠ {len(missing_from_embeddings)} icons in catalog but NOT in embeddings")
            print(f"      Examples: {missing_from_embeddings[:5]}")
        else:
            print(f"   ✓ All catalog icons have embeddings")

        return sync

    except Exception as e:
        print(f"   ✗ Sync check failed: {e}")
        return None


def main():
    """Run all verification checks."""
    print("=" * 60)
    print("Iconics Embeddings Verification")
    print("=" * 60)

    workspace = Path(__file__).parent
    embeddings_dir = workspace / "embeddings"
    catalog_path = workspace / "icon-catalog.json"

    # Run checks
    files_ok = check_files_exist(embeddings_dir)
    if not files_ok:
        print("\n❌ FAILED: Missing required files")
        sys.exit(1)

    embeddings, index, metadata = check_loadable(embeddings_dir)
    if embeddings is None:
        print("\n❌ FAILED: Cannot load files")
        sys.exit(1)

    normalized_ok = check_normalization(embeddings)
    index_ok = check_index_consistency(embeddings, index, metadata)

    sync = check_catalog_sync(catalog_path)

    # Final verdict
    print("\n" + "=" * 60)

    if sync is None:
        print("❌ VERIFICATION FAILED: Could not check sync")
        sys.exit(1)

    has_issues = (
        not normalized_ok or
        not index_ok or
        len(sync['in_embeddings_not_catalog']) > 0 or
        len(sync['in_catalog_not_embeddings']) > 0
    )

    if has_issues:
        print("⚠️  VERIFICATION WARNING: Issues detected")
        print("\nRecommended fix:")
        print("  source .venv-vision/bin/activate")
        print("  python3 icon-manager.py embed --force")
    else:
        print("✅ VERIFICATION PASSED: Embeddings are valid")

    print("=" * 60)


if __name__ == "__main__":
    main()
