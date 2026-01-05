"""
Iconics Variant Grouping System

Detects, displays, and bundles icon size variants (lock-16x16, lock-32x32, etc.)
Uses name pattern matching + CLIP similarity verification.

Key Features:
- Regex-based size extraction from icon IDs
- CLIP similarity verification (threshold 0.90)
- Multi-resolution bundle format (.imrb ZIP-based)
- Canonical variant selection (prefer 32x32)
- Integration with dedupe system
"""

import json
import logging
import re
import zipfile
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import numpy as np

logger = logging.getLogger(__name__)


# Size extraction patterns (in priority order)
SIZE_PATTERNS = [
    r'^(.+)-(\d+)x(\d+)$',           # name-WxH (e.g., lock-32x32)
    r'^(.+)_(\d+)x(\d+)$',           # name_WxH (e.g., lock_32x32)
    r'^(.+)-(\d+)x(\d+)-(.+)$',      # name-WxH-variant (e.g., lock-16x16-old)
    r'^(\d+)x(\d+)-(.+)$',           # WxH-name (e.g., 32x32-lock)
]


def extract_base_and_size(icon_id: str) -> Tuple[Optional[str], Optional[Tuple[int, int]]]:
    """
    Extract base name and size from icon ID using regex patterns.

    Patterns recognized:
    - lock-32x32 → ("lock", (32, 32))
    - lock_32x32 → ("lock", (32, 32))
    - lock-16x16-old → ("lock", (16, 16))
    - 32x32-lock → ("lock", (32, 32))

    Args:
        icon_id: Icon identifier (stem from filename)

    Returns:
        Tuple of (base_name, (width, height)) or (None, None) if no pattern matches
    """
    for pattern in SIZE_PATTERNS:
        match = re.match(pattern, icon_id)
        if match:
            groups = match.groups()

            # Handle different pattern structures
            if pattern == SIZE_PATTERNS[3]:  # WxH-name (reversed)
                # Groups: (width, height, name)
                return groups[2], (int(groups[0]), int(groups[1]))
            elif pattern == SIZE_PATTERNS[2]:  # name-WxH-variant
                # Groups: (name, width, height, variant_suffix)
                # Ignore variant suffix, use base name only
                return groups[0], (int(groups[1]), int(groups[2]))
            else:  # name-WxH or name_WxH
                # Groups: (name, width, height)
                return groups[0], (int(groups[1]), int(groups[2]))

    return None, None


@dataclass
class VariantGroup:
    """
    Represents a group of icon variants at different resolutions.

    Attributes:
        base_name: Base icon name (e.g., "lock")
        variants: Dict mapping icon_id to (width, height)
        similarity_matrix: Pairwise CLIP similarities (n_variants x n_variants)
        canonical: Preferred variant ID (prefer 32x32)
    """
    base_name: str
    variants: Dict[str, Tuple[int, int]]  # {icon_id: (width, height)}
    similarity_matrix: np.ndarray
    canonical: str

    @property
    def sizes(self) -> List[Tuple[int, int]]:
        """Get sorted list of unique sizes."""
        return sorted(set(self.variants.values()))

    @property
    def avg_similarity(self) -> float:
        """Compute average pairwise similarity (excluding diagonal)."""
        n = len(self.variants)
        if n <= 1:
            return 1.0

        total_sim = self.similarity_matrix.sum() - n  # Subtract diagonal
        avg_sim = total_sim / (n * (n - 1))
        return float(avg_sim)

    def get_variant(self, size: Tuple[int, int]) -> Optional[str]:
        """
        Get icon ID for a specific size.

        Args:
            size: (width, height) tuple

        Returns:
            Icon ID or None if size not available
        """
        for icon_id, s in self.variants.items():
            if s == size:
                return icon_id
        return None

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'base_name': self.base_name,
            'canonical': self.canonical,
            'variants': {
                icon_id: {'width': w, 'height': h}
                for icon_id, (w, h) in self.variants.items()
            },
            'sizes': [{'width': w, 'height': h} for w, h in self.sizes],
            'avg_similarity': self.avg_similarity,
            'similarity_matrix': self.similarity_matrix.tolist()
        }


def pick_canonical_variant(variants: List[Tuple[str, Tuple[int, int]]]) -> str:
    """
    Pick canonical variant from a group.

    Priority (lower is better):
    1. 32x32 (most common UI size)
    2. 24x24 (second most common)
    3. 48x48 (common desktop size)
    4. 16x16 (small UI elements)
    5. 64x64 (large UI elements)
    6. Other sizes (sorted by total pixels, descending)

    Args:
        variants: List of (icon_id, (width, height)) tuples

    Returns:
        Icon ID of the canonical variant
    """
    # Define priority for common sizes
    size_priority = {
        (32, 32): 0,
        (24, 24): 1,
        (48, 48): 2,
        (16, 16): 3,
        (64, 64): 4,
    }

    def variant_priority(v: Tuple[str, Tuple[int, int]]) -> Tuple[int, int]:
        icon_id, (w, h) = v

        # First sort key: size priority (lower is better)
        # If size not in priority dict, use 99 + negative pixel count
        # (prefer larger sizes among non-standard sizes)
        if (w, h) in size_priority:
            prio = size_priority[(w, h)]
        else:
            # For non-standard sizes, sort by pixel count (larger is better)
            # Use 100 - pixel_count to maintain ascending sort order
            prio = 100 + (-(w * h) // 1000)  # Normalize to avoid huge numbers

        # Second sort key: lexicographic on icon_id (for determinism)
        return (prio, icon_id)

    return min(variants, key=variant_priority)[0]


def detect_variant_groups(
    icon_ids: List[str],
    embeddings: np.ndarray,
    icon_index: Dict[str, int],
    similarity_threshold: float = 0.90
) -> List[VariantGroup]:
    """
    Detect variant groups using name patterns + CLIP similarity.

    Process:
    1. Group icons by extracted base name
    2. Filter groups with multiple sizes
    3. Verify with CLIP similarity (avg similarity > threshold)
    4. Create VariantGroup for valid groups

    Args:
        icon_ids: List of icon identifiers
        embeddings: Icon embedding matrix (n_icons, d)
        icon_index: Dict mapping icon_id to embedding index
        similarity_threshold: Minimum average similarity for variant group (default: 0.90)

    Returns:
        List of VariantGroup objects, sorted by group size (descending)
    """
    # Step 1: Group by base name
    base_groups = defaultdict(list)

    for icon_id in icon_ids:
        base, size = extract_base_and_size(icon_id)
        if base and size:
            base_groups[base].append((icon_id, size))

    logger.info(f"Found {len(base_groups)} potential variant groups from {len(icon_ids)} icons")

    # Step 2: Filter groups with multiple sizes
    variant_groups = []

    for base, variants in base_groups.items():
        if len(variants) < 2:
            continue

        # Verify all variants exist in index
        variant_ids = [v[0] for v in variants]
        missing_ids = [vid for vid in variant_ids if vid not in icon_index]

        if missing_ids:
            logger.warning(f"Base '{base}': {len(missing_ids)} variants missing from embeddings: {missing_ids[:3]}...")
            # Filter to only available variants
            variants = [(vid, size) for vid, size in variants if vid in icon_index]
            if len(variants) < 2:
                continue
            variant_ids = [v[0] for v in variants]

        # Step 3: Verify with CLIP similarity
        variant_indices = [icon_index[vid] for vid in variant_ids]
        variant_embeddings = embeddings[variant_indices]

        # Compute pairwise similarity matrix
        sim_matrix = variant_embeddings @ variant_embeddings.T

        # Compute average similarity (excluding diagonal)
        n = len(variants)
        avg_sim = (sim_matrix.sum() - n) / (n * (n - 1))

        if avg_sim >= similarity_threshold:
            canonical = pick_canonical_variant(variants)

            variant_groups.append(VariantGroup(
                base_name=base,
                variants={vid: size for vid, size in variants},
                similarity_matrix=sim_matrix,
                canonical=canonical
            ))

            logger.debug(f"Variant group '{base}': {len(variants)} variants, avg_sim={avg_sim:.3f}")
        else:
            logger.debug(
                f"Rejected group '{base}': avg_sim={avg_sim:.3f} < {similarity_threshold}"
            )

    # Sort by number of variants (descending)
    variant_groups.sort(key=lambda g: -len(g.variants))

    logger.info(f"Detected {len(variant_groups)} valid variant groups")

    return variant_groups


def create_bundle(
    group: VariantGroup,
    icon_dir: Path,
    output_path: Path,
    catalog: Optional[Dict] = None
) -> Path:
    """
    Create .imrb multi-resolution bundle (ZIP-based).

    Bundle format:
    - manifest.json: Metadata and file mapping
    - <size>.png: Icon files (e.g., 16x16.png, 32x32.png)

    Args:
        group: VariantGroup to bundle
        icon_dir: Directory containing source icon files
        output_path: Output path for .imrb file
        catalog: Optional catalog dict for metadata extraction

    Returns:
        Path to created bundle file

    Raises:
        FileNotFoundError: If source icons cannot be found
    """
    # Build manifest
    manifest = {
        "format": "iconics-mrb-v1",
        "canonical": group.canonical,
        "base_name": group.base_name,
        "variants": {},
        "metadata": _get_merged_metadata(group, catalog) if catalog else {}
    }

    # Find icon files
    icon_files = {}
    for icon_id, (w, h) in group.variants.items():
        icon_path = _find_icon_file(icon_id, icon_dir)
        if icon_path:
            icon_files[(w, h)] = icon_path
        else:
            logger.warning(f"Icon file not found for {icon_id}")

    if not icon_files:
        raise FileNotFoundError(f"No icon files found for group '{group.base_name}'")

    # Create ZIP bundle
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for (w, h), icon_path in icon_files.items():
            size_key = f"{w}x{h}"
            filename = f"{size_key}.png"

            # Find the icon_id for this size
            icon_id = group.get_variant((w, h))

            manifest["variants"][size_key] = {
                "original_id": icon_id,
                "filename": filename
            }

            # Add to ZIP
            z.write(icon_path, filename)

        # Write manifest
        z.writestr("manifest.json", json.dumps(manifest, indent=2))

    logger.info(f"Created bundle: {output_path} ({len(icon_files)} variants)")

    return output_path


def read_bundle(bundle_path: Path, size: Optional[Tuple[int, int]] = None) -> Dict:
    """
    Read .imrb bundle and optionally extract icon at specific size.

    Args:
        bundle_path: Path to .imrb file
        size: Optional (width, height) to extract. If None, returns metadata only.

    Returns:
        Dict with:
        - manifest: Bundle manifest
        - icon_data: PNG bytes if size specified, otherwise None
        - available_sizes: List of available sizes

    Raises:
        FileNotFoundError: If bundle not found
        ValueError: If size requested but not available
    """
    if not bundle_path.exists():
        raise FileNotFoundError(f"Bundle not found: {bundle_path}")

    with zipfile.ZipFile(bundle_path, 'r') as z:
        # Read manifest
        manifest_data = z.read("manifest.json")
        manifest = json.loads(manifest_data)

        # Parse available sizes
        available_sizes = []
        for size_key in manifest["variants"].keys():
            try:
                w, h = map(int, size_key.split('x'))
                available_sizes.append((w, h))
            except ValueError:
                logger.warning(f"Invalid size key in manifest: {size_key}")
                continue

        # Extract icon data if size specified
        icon_data = None
        if size is not None:
            size_key = f"{size[0]}x{size[1]}"
            if size_key not in manifest["variants"]:
                raise ValueError(
                    f"Size {size} not available. Available: {available_sizes}"
                )

            filename = manifest["variants"][size_key]["filename"]
            icon_data = z.read(filename)

        return {
            "manifest": manifest,
            "icon_data": icon_data,
            "available_sizes": available_sizes
        }


def _find_icon_file(icon_id: str, icon_dir: Path) -> Optional[Path]:
    """
    Find icon file by ID in directory.

    Searches for:
    - {icon_id}.png
    - raw/{icon_id}.png
    - catalog/{icon_id}.png

    Args:
        icon_id: Icon identifier
        icon_dir: Base directory to search

    Returns:
        Path to icon file or None if not found
    """
    # Common locations to search
    search_paths = [
        icon_dir / f"{icon_id}.png",
        icon_dir / "raw" / f"{icon_id}.png",
        icon_dir / "catalog" / f"{icon_id}.png",
        icon_dir.parent / "raw" / f"{icon_id}.png",  # If icon_dir is 'catalog'
    ]

    for path in search_paths:
        if path.exists():
            return path

    return None


def _get_merged_metadata(group: VariantGroup, catalog: Dict) -> Dict:
    """
    Extract and merge metadata from catalog for variant group.

    Takes metadata from the canonical variant, merges tags from all variants.

    Args:
        group: VariantGroup
        catalog: Catalog dict

    Returns:
        Merged metadata dict
    """
    # Get catalog lookup
    catalog_lookup = {icon['id']: icon for icon in catalog.get('icons', [])}

    # Get canonical metadata
    canonical_entry = catalog_lookup.get(group.canonical, {})

    # Merge tags from all variants
    all_tags = set(canonical_entry.get('tags', []))

    for icon_id in group.variants.keys():
        entry = catalog_lookup.get(icon_id, {})
        all_tags.update(entry.get('tags', []))

    return {
        'semantic_name': canonical_entry.get('semanticName', group.base_name),
        'tags': sorted(all_tags),
        'category': canonical_entry.get('category', 'unknown'),
        'description': canonical_entry.get('description', ''),
    }


def get_variant_ids(group: VariantGroup) -> Set[str]:
    """
    Get set of all icon IDs in a variant group.

    Useful for excluding variants from duplicate detection.

    Args:
        group: VariantGroup

    Returns:
        Set of icon IDs
    """
    return set(group.variants.keys())


def filter_non_canonical_variants(
    icon_ids: List[str],
    variant_groups: List[VariantGroup]
) -> List[str]:
    """
    Filter out non-canonical variants from icon list.

    Used by dedupe system to avoid flagging intentional variants as duplicates.

    Args:
        icon_ids: List of icon IDs
        variant_groups: List of detected variant groups

    Returns:
        Filtered list containing only canonical variants (or non-variants)
    """
    # Build set of non-canonical variant IDs
    non_canonical = set()
    for group in variant_groups:
        for icon_id in group.variants.keys():
            if icon_id != group.canonical:
                non_canonical.add(icon_id)

    # Filter
    filtered = [icon_id for icon_id in icon_ids if icon_id not in non_canonical]

    logger.info(
        f"Filtered {len(icon_ids) - len(filtered)} non-canonical variants "
        f"from {len(icon_ids)} icons"
    )

    return filtered


def format_variant_group_display(
    group: VariantGroup,
    catalog: Optional[Dict] = None,
    show_matrix: bool = True
) -> str:
    """
    Format variant group for display.

    Args:
        group: VariantGroup to display
        catalog: Optional catalog for metadata
        show_matrix: Whether to include similarity matrix

    Returns:
        Formatted string for terminal display
    """
    lines = []

    # Header
    lines.append(f"Variant Group: {group.base_name} ({len(group.variants)} sizes)")
    lines.append(f"  Canonical: {group.canonical}")
    lines.append("")

    # Variants table
    lines.append("  Size     Icon ID              Tags")
    lines.append("  " + "─" * 60)

    # Get catalog lookup if available
    catalog_lookup = {}
    if catalog:
        catalog_lookup = {icon['id']: icon for icon in catalog.get('icons', [])}

    # Sort by size
    sorted_variants = sorted(group.variants.items(), key=lambda x: x[1])

    for icon_id, (w, h) in sorted_variants:
        size_str = f"{w}x{h}".ljust(8)

        # Add star for canonical
        id_str = icon_id
        if icon_id == group.canonical:
            id_str += " ★"
        id_str = id_str.ljust(20)

        # Get tags from catalog
        tags = []
        if icon_id in catalog_lookup:
            tags = catalog_lookup[icon_id].get('tags', [])
        tags_str = ', '.join(tags[:3])  # Show first 3 tags
        if len(tags) > 3:
            tags_str += f" (+{len(tags) - 3})"

        lines.append(f"  {size_str} {id_str} {tags_str}")

    # Similarity matrix
    if show_matrix and len(group.variants) > 1:
        lines.append("")
        lines.append("  CLIP Similarity Matrix:")

        # Get sorted icon IDs for consistent ordering
        sorted_ids = [icon_id for icon_id, _ in sorted_variants]

        # Build header
        header = "          " + "  ".join(f"{w}x{h}".rjust(5) for _, (w, h) in sorted_variants)
        lines.append(header)

        # Build rows
        for i, (icon_id, (w_i, h_i)) in enumerate(sorted_variants):
            row_label = f"  {w_i}x{h_i}".ljust(10)
            row_values = []

            for j in range(len(sorted_variants)):
                sim = group.similarity_matrix[i, j]
                row_values.append(f"{sim:.3f}")

            lines.append(row_label + "  ".join(v.rjust(5) for v in row_values))

        lines.append("")
        lines.append(f"  Average similarity: {group.avg_similarity:.3f}")

    return "\n".join(lines)
