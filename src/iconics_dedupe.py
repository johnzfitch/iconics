"""
Iconics Duplicate Detection System

This module implements Agent 1: Dedupe Detection using CLIP embeddings
to identify duplicate and near-duplicate icons in the library.

Key Features:
    - Connected component clustering via scipy.sparse
    - Smart canonical selection (resolution, tags, name length)
    - Metadata merging for removed duplicates
    - Interactive and batch modes
    - Dry-run preview support

Algorithm:
    1. Compute pairwise CLIP similarities
    2. Build adjacency graph where edges exist if similarity > threshold
    3. Find connected components (duplicate clusters)
    4. For each cluster, pick canonical icon and merge metadata
"""

import json
import logging
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components

logger = logging.getLogger(__name__)


@dataclass
class DupeCluster:
    """
    Container for a duplicate cluster.

    Attributes:
        members: All icon IDs in this cluster
        avg_similarity: Average pairwise CLIP similarity within cluster
        suggested_canonical: Best candidate to keep (others would be removed/merged)
    """
    members: List[str]
    avg_similarity: float
    suggested_canonical: str

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return asdict(self)


def extract_resolution(icon_id: str) -> Optional[Tuple[int, int]]:
    """
    Extract resolution from icon ID if present.

    Supports formats:
        - icon-WxH (e.g., "lock-32x32")
        - icon_WxH (e.g., "lock_16x16")
        - icon-WxH-variant (e.g., "lock-64x64-old")

    Args:
        icon_id: Icon identifier

    Returns:
        Tuple of (width, height) if found, None otherwise
    """
    patterns = [
        r'(\d+)x(\d+)',  # Simple WxH pattern
    ]

    for pattern in patterns:
        match = re.search(pattern, icon_id)
        if match:
            width = int(match.group(1))
            height = int(match.group(2))
            return (width, height)

    return None


def pick_canonical(members: List[str], catalog_lookup: Dict[str, Dict]) -> str:
    """
    Pick the best canonical icon from a cluster.

    Heuristics (in order of priority):
    1. Highest resolution (prefer larger icons)
    2. Most metadata (tags count)
    3. Shortest name (less likely to be a variant like "icon-old")
    4. Alphabetically first (deterministic tie-breaker)

    Args:
        members: List of icon IDs in the cluster
        catalog_lookup: Dict mapping icon_id -> catalog entry

    Returns:
        Icon ID of the suggested canonical
    """
    def score_icon(icon_id: str) -> Tuple[int, int, int, str]:
        """
        Score an icon for canonical selection.

        Returns tuple for sorting (higher is better for first 2 elements):
            - Resolution area (higher is better)
            - Tag count (higher is better)
            - Name length (negated - shorter is better)
            - Icon ID (for deterministic ordering)
        """
        # Resolution: Higher is better
        resolution = extract_resolution(icon_id)
        if resolution:
            width, height = resolution
            res_score = width * height
        else:
            res_score = 0  # Icons without resolution are deprioritized

        # Metadata: More tags is better
        entry = catalog_lookup.get(icon_id, {})
        tags = entry.get('tags', [])
        tag_count = len(tags)

        # Name length: Shorter is better (negate for sorting)
        # Icons like "lock-old" or "lock-variant-2" are longer
        name_len = -len(icon_id)

        return (res_score, tag_count, name_len, icon_id)

    # Sort by score (descending for first 3, ascending for ID)
    best = max(members, key=lambda m: score_icon(m))
    return best


def find_duplicate_clusters(
    embeddings: np.ndarray,
    icon_ids: List[str],
    catalog_lookup: Dict[str, Dict],
    threshold: float = 0.95
) -> List[DupeCluster]:
    """
    Find duplicate clusters using CLIP similarity.

    Approach:
    1. Compute pairwise similarities (cosine similarity, embeddings are L2-normalized)
    2. Build adjacency graph where edge exists if similarity > threshold
    3. Find connected components using scipy
    4. For each component with multiple members, compute stats and suggest canonical

    Args:
        embeddings: Icon embedding matrix, shape (n_icons, dim), L2-normalized
        icon_ids: List of icon IDs matching embedding rows
        catalog_lookup: Dict mapping icon_id -> catalog entry (for metadata)
        threshold: Similarity threshold for considering icons as duplicates (default: 0.95)

    Returns:
        List of DupeCluster objects, sorted by cluster size (largest first)
    """
    n = len(icon_ids)

    if n == 0:
        return []

    # Memory check: similarity matrix is n x n float32 (4 bytes each)
    estimated_memory_mb = (n * n * 4) / (1024 * 1024)
    max_memory_mb = 1024  # 1GB limit
    if estimated_memory_mb > max_memory_mb:
        raise MemoryError(
            f"Similarity matrix for {n} icons would require ~{estimated_memory_mb:.0f}MB. "
            f"Maximum allowed is {max_memory_mb}MB. Consider filtering the icon set first."
        )
    elif estimated_memory_mb > 256:
        logger.warning(
            f"Large similarity matrix: {n} icons will use ~{estimated_memory_mb:.0f}MB"
        )

    logger.info(f"Computing pairwise similarities for {n} icons...")

    # Compute pairwise cosine similarities
    # Since embeddings are L2-normalized, cosine sim = dot product
    similarities = embeddings @ embeddings.T  # Shape: (n, n)

    logger.info(f"Building adjacency graph (threshold={threshold})...")

    # Build adjacency matrix: 1 if similarity > threshold, 0 otherwise
    adj = (similarities > threshold).astype(int)

    # Remove self-loops (diagonal)
    np.fill_diagonal(adj, 0)

    # Find connected components
    logger.info("Finding connected components...")
    n_components, labels = connected_components(csr_matrix(adj), directed=False)

    logger.info(f"Found {n_components} components, filtering for duplicates...")

    # Group by component, filter singletons
    clusters = []
    for comp_id in range(n_components):
        # Get members of this component
        member_mask = (labels == comp_id)
        member_indices = np.where(member_mask)[0]
        members = [icon_ids[i] for i in member_indices]

        # Skip singletons (not duplicates)
        if len(members) <= 1:
            continue

        # Compute cluster statistics
        # Extract submatrix of similarities within this cluster
        cluster_sims = similarities[np.ix_(member_indices, member_indices)]

        # Average pairwise similarity (excluding diagonal)
        n_members = len(members)
        total_sim = cluster_sims.sum() - n_members  # Subtract diagonal (all 1.0s)
        n_pairs = n_members * (n_members - 1)
        avg_sim = total_sim / n_pairs if n_pairs > 0 else 0.0

        # Pick canonical
        canonical = pick_canonical(members, catalog_lookup)

        clusters.append(DupeCluster(
            members=members,
            avg_similarity=float(avg_sim),
            suggested_canonical=canonical
        ))

    # Sort by cluster size (largest first)
    clusters.sort(key=lambda c: len(c.members), reverse=True)

    logger.info(f"Found {len(clusters)} duplicate clusters ({sum(len(c.members) for c in clusters)} icons total)")

    return clusters


def merge_metadata(
    keep_id: str,
    remove_ids: List[str],
    catalog: 'IconCatalog'  # Forward reference to avoid circular import
) -> Dict:
    """
    Merge metadata from removed icons into the canonical keeper.

    Process:
    1. Collect all unique tags from all icons
    2. Merge descriptions (keep keeper's, optionally extend)
    3. Add audit trail of merged icons
    4. Update catalog entry

    Args:
        keep_id: Icon ID to keep (canonical)
        remove_ids: Icon IDs to remove and merge into canonical
        catalog: IconCatalog instance

    Returns:
        Updated catalog entry for the keeper
    """
    # Get keeper entry
    keep_entry = catalog.get_entry(keep_id)
    if not keep_entry:
        logger.error(f"Canonical icon {keep_id} not found in catalog")
        return {}

    # Collect metadata from all removed icons
    all_tags = set(keep_entry.get('tags', []))
    descriptions = [keep_entry.get('description', '')]

    for rid in remove_ids:
        entry = catalog.get_entry(rid)
        if entry:
            # Merge tags
            all_tags.update(entry.get('tags', []))

            # Collect descriptions (we'll keep the longest one)
            desc = entry.get('description', '')
            if desc and desc not in descriptions:
                descriptions.append(desc)

    # Update keeper entry
    keep_entry['tags'] = sorted(all_tags)

    # Keep longest description
    if descriptions:
        keep_entry['description'] = max(descriptions, key=len)

    # Add audit trail
    if 'merged_from' not in keep_entry:
        keep_entry['merged_from'] = []
    keep_entry['merged_from'].extend(remove_ids)
    keep_entry['merged_from'] = sorted(set(keep_entry['merged_from']))  # Dedupe

    # Update catalog
    catalog.update_entry(keep_id, keep_entry)

    logger.info(f"Merged {len(remove_ids)} icons into {keep_id}")

    return keep_entry


def format_cluster_output(
    cluster: DupeCluster,
    cluster_num: int,
    catalog_lookup: Dict[str, Dict],
    verbose: bool = False
) -> str:
    """
    Format a cluster for human-readable output.

    Args:
        cluster: DupeCluster to format
        cluster_num: Cluster number (for display)
        catalog_lookup: Dict mapping icon_id -> catalog entry
        verbose: If True, include detailed metadata

    Returns:
        Formatted string representation
    """
    lines = []
    lines.append(f"\nCluster {cluster_num} ({len(cluster.members)} icons, avg similarity: {cluster.avg_similarity:.3f}):")

    # Sort members: canonical first, then alphabetically
    canonical = cluster.suggested_canonical
    others = [m for m in cluster.members if m != canonical]
    others.sort()

    # Canonical
    lines.append(f"  → {canonical} (canonical candidate)")
    if verbose:
        entry = catalog_lookup.get(canonical, {})
        tags = entry.get('tags', [])
        if tags:
            lines.append(f"      Tags: {', '.join(tags[:5])}")
        resolution = extract_resolution(canonical)
        if resolution:
            lines.append(f"      Resolution: {resolution[0]}x{resolution[1]}")

    # Others
    for icon_id in others:
        lines.append(f"    {icon_id}")
        if verbose:
            entry = catalog_lookup.get(icon_id, {})
            tags = entry.get('tags', [])
            if tags:
                lines.append(f"      Tags: {', '.join(tags[:5])}")
            resolution = extract_resolution(icon_id)
            if resolution:
                lines.append(f"      Resolution: {resolution[0]}x{resolution[1]}")

    return '\n'.join(lines)


def export_clusters_to_json(
    clusters: List[DupeCluster],
    output_path: Path,
    catalog_lookup: Dict[str, Dict]
) -> None:
    """
    Export duplicate clusters to JSON file.

    Args:
        clusters: List of DupeCluster objects
        output_path: Path to write JSON file
        catalog_lookup: Dict mapping icon_id -> catalog entry (for metadata)
    """
    export_data = {
        'version': '1.0',
        'total_clusters': len(clusters),
        'total_duplicates': sum(len(c.members) for c in clusters),
        'clusters': []
    }

    for i, cluster in enumerate(clusters, 1):
        cluster_data = cluster.to_dict()
        cluster_data['cluster_id'] = i

        # Add metadata for each member
        cluster_data['member_metadata'] = {}
        for icon_id in cluster.members:
            entry = catalog_lookup.get(icon_id, {})
            cluster_data['member_metadata'][icon_id] = {
                'tags': entry.get('tags', []),
                'category': entry.get('category', 'unknown'),
                'resolution': extract_resolution(icon_id)
            }

        export_data['clusters'].append(cluster_data)

    with open(output_path, 'w') as f:
        json.dump(export_data, f, indent=2)

    logger.info(f"Exported {len(clusters)} clusters to {output_path}")


def interactive_dedupe(
    clusters: List[DupeCluster],
    catalog: 'IconCatalog'  # Forward reference
) -> Dict[str, int]:
    """
    Interactive mode: Prompt user for each cluster.

    Args:
        clusters: List of DupeCluster objects
        catalog: IconCatalog instance

    Returns:
        Dict with stats: {'kept': int, 'merged': int, 'skipped': int}
    """
    stats = {'kept': 0, 'merged': 0, 'skipped': 0}

    print(f"\nFound {len(clusters)} duplicate clusters")
    print("Actions: [k]eep canonical + merge, [s]kip, [q]uit\n")

    for i, cluster in enumerate(clusters, 1):
        # Build catalog lookup for this cluster
        catalog_lookup = {
            icon_id: catalog.get_entry(icon_id) or {}
            for icon_id in cluster.members
        }

        # Display cluster
        print(format_cluster_output(cluster, i, catalog_lookup, verbose=True))

        # Prompt
        while True:
            try:
                action = input(f"\nAction for cluster {i}/{len(clusters)}? [k/s/q]: ").lower().strip()

                if action == 'q':
                    print("\nQuitting interactive mode...")
                    return stats

                elif action == 's':
                    print("Skipped.")
                    stats['skipped'] += 1
                    break

                elif action == 'k':
                    # Keep canonical, merge others
                    canonical = cluster.suggested_canonical
                    remove_ids = [m for m in cluster.members if m != canonical]

                    if not remove_ids:
                        print("No duplicates to merge (only one icon in cluster).")
                        stats['skipped'] += 1
                        break

                    # Merge metadata
                    merge_metadata(canonical, remove_ids, catalog)

                    print(f"✓ Kept {canonical}, merged {len(remove_ids)} duplicates")
                    stats['kept'] += 1
                    stats['merged'] += len(remove_ids)
                    break

                else:
                    print("Invalid action. Use k, s, or q.")

            except (KeyboardInterrupt, EOFError):
                print("\n\nInterrupted. Quitting...")
                return stats

    return stats
