"""
Iconics Project Provisioning Module

This module provides functionality for provisioning icons from the master
library to project directories. Instead of copying the entire 8000+ icon
library, projects can request only the icons they need.

Key Features:
    - Copy icons by ID or semantic query
    - Manifest tracking for project icons
    - Framework-specific import generation (React, Vue, CSS, TypeScript)
    - Manifest-based replication

Design Principle:
    8000 icons can't live in every project. Copy only what you need,
    track what you've provisioned, and generate framework-ready imports.

Example:
    >>> provisioner = IconicsProvisioner(source_path, catalog)
    >>> result = provisioner.provision(
    ...     ["lock-32x32", "shield-32x32"],
    ...     dest="/path/to/project/icons"
    ... )
    >>> print(result["copied"])
    ['lock-32x32.png', 'shield-32x32.png']
"""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Literal, Optional, Union

logger = logging.getLogger(__name__)


class IconicsProvisioner:
    """
    Provision icons from the master library to project directories.

    This class manages the copying of icons from the central iconics library
    to individual project directories. It maintains a manifest file to track
    which icons have been provisioned and when.

    Attributes:
        source: Path to the raw icons directory
        catalog: Icon catalog dictionary with icon metadata

    Example:
        >>> from iconics_provision import IconicsProvisioner, load_catalog
        >>> catalog = load_catalog("/home/zack/dev/iconics/icon-catalog.json")
        >>> provisioner = IconicsProvisioner("/home/zack/dev/iconics/raw", catalog)
        >>> result = provisioner.provision(
        ...     ["lock-32x32", "shield-32x32"],
        ...     dest="./icons/"
        ... )
    """

    # Manifest schema version
    MANIFEST_VERSION = "1.0"

    def __init__(self, source_path: str, catalog: Dict):
        """
        Initialize provisioner with source path and catalog.

        Args:
            source_path: Path to the raw icons directory (e.g., /home/zack/dev/iconics/raw)
            catalog: Icon catalog dictionary loaded from icon-catalog.json
        """
        self.source = Path(source_path)
        self.catalog = catalog

        # Build icon lookup by ID for fast access
        self._icon_by_id: Dict[str, Dict] = {}
        for icon in catalog.get("icons", []):
            self._icon_by_id[icon["id"]] = icon

        logger.info(f"Provisioner initialized with {len(self._icon_by_id)} icons")

    def provision(
        self,
        icon_ids: List[str],
        dest: str,
        update_manifest: bool = True,
        icon_subdir: str = "",
        create_dirs: bool = True
    ) -> Dict:
        """
        Copy icons to destination directory.

        Args:
            icon_ids: List of icon IDs to provision (e.g., ["lock-32x32", "shield-32x32"])
            dest: Destination directory for icons
            update_manifest: If True, update/create manifest.json in dest
            icon_subdir: Subdirectory within dest for icons (e.g., ".github/assets/icons")
            create_dirs: If True, create destination directories if they don't exist

        Returns:
            Dictionary with provisioning results:
            {
                "copied": ["lock-32x32.png", ...],
                "skipped": ["already-exists.png", ...],
                "missing": ["not-found.png", ...],
                "manifest_path": "dest/manifest.json" or None
            }
        """
        dest_path = Path(dest)
        if icon_subdir:
            icon_dest = dest_path / icon_subdir
        else:
            icon_dest = dest_path

        if create_dirs:
            icon_dest.mkdir(parents=True, exist_ok=True)

        copied = []
        skipped = []
        missing = []

        for icon_id in icon_ids:
            # Normalize icon_id (remove .png if present)
            icon_id = icon_id.replace(".png", "")

            source_file = self.source / f"{icon_id}.png"

            if not source_file.exists():
                logger.warning(f"Icon not found: {icon_id}")
                missing.append(f"{icon_id}.png")
                continue

            dest_file = icon_dest / f"{icon_id}.png"

            # Skip if already exists (unless updating manifest)
            if dest_file.exists():
                skipped.append(f"{icon_id}.png")
                continue

            # Copy the icon
            try:
                shutil.copy2(source_file, dest_file)
                copied.append(f"{icon_id}.png")
                logger.debug(f"Copied {icon_id}.png to {dest_file}")
            except Exception as e:
                logger.error(f"Failed to copy {icon_id}: {e}")
                missing.append(f"{icon_id}.png")

        result = {
            "copied": copied,
            "skipped": skipped,
            "missing": missing,
            "manifest_path": None
        }

        # Update manifest
        if update_manifest:
            manifest_path = dest_path / "iconics-manifest.json"
            self._update_manifest(manifest_path, icon_ids, icon_subdir)
            result["manifest_path"] = str(manifest_path)

        logger.info(
            f"Provisioned {len(copied)} icons, skipped {len(skipped)}, "
            f"missing {len(missing)}"
        )

        return result

    def provision_from_query(
        self,
        queries: List[str],
        dest: str,
        k: int = 2,
        retriever=None,
        mode: str = "projected",
        icon_subdir: str = "",
        update_manifest: bool = True,
    ) -> Dict:
        """
        Query for icons semantically, then provision top matches.

        This is a convenience method for LLM workflows that combines
        semantic search with provisioning.

        Args:
            queries: List of text queries (e.g., ["security lock", "database storage"])
            dest: Destination directory for icons
            k: Number of top matches per query to provision
            retriever: IconicsRetriever instance. If None, falls back to catalog search.
            mode: Retrieval mode for vector search ("raw", "projected", "weighted")

        Returns:
            Dictionary with provisioning results plus query mappings:
            {
                "copied": [...],
                "skipped": [...],
                "missing": [...],
                "manifest_path": "...",
                "query_results": {
                    "security lock": ["lock-32x32", "shield-32x32"],
                    ...
                }
            }
        """
        all_icon_ids = []
        query_results = {}

        for query in queries:
            matched_ids = []

            if retriever is not None:
                # Use vector retrieval
                try:
                    results = retriever.retrieve(query, k=k, mode=mode)
                    matched_ids = [r.icon_id for r in results]
                except Exception as e:
                    logger.warning(f"Vector retrieval failed for '{query}': {e}")
                    # Fall back to catalog search
                    matched_ids = self._catalog_search(query, k)
            else:
                # Use catalog search
                matched_ids = self._catalog_search(query, k)

            query_results[query] = matched_ids
            all_icon_ids.extend(matched_ids)

        # Remove duplicates while preserving order
        seen = set()
        unique_ids = []
        for icon_id in all_icon_ids:
            if icon_id not in seen:
                seen.add(icon_id)
                unique_ids.append(icon_id)

        # Provision the icons
        result = self.provision(
            unique_ids,
            dest,
            update_manifest=update_manifest,
            icon_subdir=icon_subdir,
        )
        result["query_results"] = query_results

        return result

    def provision_from_manifest(
        self,
        manifest_path: str,
        dest: str
    ) -> Dict:
        """
        Replicate icons from an existing manifest to a new destination.

        Useful for cloning a project's icon setup or synchronizing across
        multiple project locations.

        Args:
            manifest_path: Path to source manifest.json
            dest: New destination directory

        Returns:
            Provisioning results dictionary
        """
        manifest_file = Path(manifest_path)
        if not manifest_file.exists():
            raise FileNotFoundError(f"Manifest not found: {manifest_path}")

        with open(manifest_file) as f:
            manifest = json.load(f)

        icon_ids = manifest.get("icons", [])
        icon_subdir = manifest.get("icon_subdir", "")

        return self.provision(
            icon_ids,
            dest,
            icon_subdir=icon_subdir
        )

    def generate_imports(
        self,
        manifest_path: str,
        format: Literal["react", "vue", "css", "typescript"],
        output_path: str
    ) -> str:
        """
        Generate framework-specific import file from manifest.

        Creates ready-to-use import files for various frontend frameworks.

        Args:
            manifest_path: Path to iconics-manifest.json
            format: Target format ("react", "vue", "css", "typescript")
            output_path: Path to write the generated file

        Returns:
            Generated file content

        Example outputs:
            React: export const LockIcon = () => <img src="./icons/lock-32x32.png" />
            Vue: export const icons = { lock: '/icons/lock-32x32.png' }
            CSS: .icon-lock { background-image: url('./icons/lock-32x32.png') }
            TypeScript: export const ICONS = { lock: './icons/lock-32x32.png' } as const
        """
        manifest_file = Path(manifest_path)
        if not manifest_file.exists():
            raise FileNotFoundError(f"Manifest not found: {manifest_path}")

        with open(manifest_file) as f:
            manifest = json.load(f)

        icon_ids = manifest.get("icons", [])
        icon_subdir = manifest.get("icon_subdir", "")

        # Determine icon path prefix
        if icon_subdir:
            path_prefix = f"./{icon_subdir}"
        else:
            path_prefix = "./icons"

        # Generate based on format
        if format == "react":
            content = self._generate_react_imports(icon_ids, path_prefix)
        elif format == "vue":
            content = self._generate_vue_imports(icon_ids, path_prefix)
        elif format == "css":
            content = self._generate_css_imports(icon_ids, path_prefix)
        elif format == "typescript":
            content = self._generate_typescript_imports(icon_ids, path_prefix)
        else:
            raise ValueError(f"Unknown format: {format}")

        # Write output
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(content)

        logger.info(f"Generated {format} imports: {output_path}")

        return content

    def _catalog_search(self, query: str, k: int) -> List[str]:
        """
        Simple catalog-based search fallback.

        Uses tag and semantic name matching when vector retriever is unavailable.
        """
        query_lower = query.lower()
        query_terms = query_lower.split()

        scored = []
        for icon_id, icon in self._icon_by_id.items():
            score = 0
            semantic_name = icon.get("semanticName", "").lower()
            tags = [t.lower() for t in icon.get("tags", [])]

            # Check each query term
            for term in query_terms:
                if term in semantic_name:
                    score += 2
                if any(term in tag for tag in tags):
                    score += 1
                if any(term == tag for tag in tags):
                    score += 1

            if score > 0:
                scored.append((icon_id, score))

        # Sort by score descending
        scored.sort(key=lambda x: -x[1])

        return [icon_id for icon_id, _ in scored[:k]]

    def _update_manifest(
        self,
        manifest_path: Path,
        icon_ids: List[str],
        icon_subdir: str
    ) -> None:
        """Update or create manifest file."""
        # Load existing manifest if present
        if manifest_path.exists():
            with open(manifest_path) as f:
                manifest = json.load(f)
        else:
            manifest = {
                "version": self.MANIFEST_VERSION,
                "icons": [],
                "icon_subdir": icon_subdir,
                "created_at": datetime.now().isoformat()
            }

        # Add new icons (avoid duplicates)
        existing_icons = set(manifest.get("icons", []))
        for icon_id in icon_ids:
            icon_id = icon_id.replace(".png", "")
            existing_icons.add(icon_id)

        manifest["icons"] = sorted(list(existing_icons))
        manifest["updated_at"] = datetime.now().isoformat()

        # Save manifest
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        logger.debug(f"Updated manifest: {manifest_path}")

    def _generate_react_imports(
        self,
        icon_ids: List[str],
        path_prefix: str
    ) -> str:
        """Generate React component imports."""
        lines = [
            "// Auto-generated by iconics provisioner",
            "// Do not edit manually",
            "",
            "import React from 'react';",
            "",
        ]

        for icon_id in icon_ids:
            # Convert icon-id to ComponentName (e.g., lock-32x32 -> Lock32x32Icon)
            component_name = self._to_component_name(icon_id)
            lines.append(
                f"export const {component_name} = () => "
                f"<img src=\"{path_prefix}/{icon_id}.png\" alt=\"{icon_id}\" />;"
            )

        lines.append("")
        lines.append("// Icon map for dynamic access")
        lines.append("export const Icons = {")
        for icon_id in icon_ids:
            key = self._to_key_name(icon_id)
            component_name = self._to_component_name(icon_id)
            lines.append(f"  {key}: {component_name},")
        lines.append("};")
        lines.append("")

        return "\n".join(lines)

    def _generate_vue_imports(
        self,
        icon_ids: List[str],
        path_prefix: str
    ) -> str:
        """Generate Vue.js exports."""
        lines = [
            "// Auto-generated by iconics provisioner",
            "// Do not edit manually",
            "",
            "export const icons = {",
        ]

        for icon_id in icon_ids:
            key = self._to_key_name(icon_id)
            lines.append(f"  {key}: '{path_prefix}/{icon_id}.png',")

        lines.append("};")
        lines.append("")
        lines.append("export default icons;")
        lines.append("")

        return "\n".join(lines)

    def _generate_css_imports(
        self,
        icon_ids: List[str],
        path_prefix: str
    ) -> str:
        """Generate CSS classes."""
        lines = [
            "/* Auto-generated by iconics provisioner */",
            "/* Do not edit manually */",
            "",
        ]

        for icon_id in icon_ids:
            class_name = icon_id.replace("x", "-").lower()
            lines.append(f".icon-{class_name} {{")
            lines.append(f"  background-image: url('{path_prefix}/{icon_id}.png');")
            lines.append("  background-size: contain;")
            lines.append("  background-repeat: no-repeat;")
            lines.append("  display: inline-block;")
            lines.append("}")
            lines.append("")

        return "\n".join(lines)

    def _generate_typescript_imports(
        self,
        icon_ids: List[str],
        path_prefix: str
    ) -> str:
        """Generate TypeScript constants."""
        lines = [
            "// Auto-generated by iconics provisioner",
            "// Do not edit manually",
            "",
            "export const ICONS = {",
        ]

        for icon_id in icon_ids:
            key = self._to_key_name(icon_id)
            lines.append(f"  {key}: '{path_prefix}/{icon_id}.png',")

        lines.append("} as const;")
        lines.append("")
        lines.append("export type IconKey = keyof typeof ICONS;")
        lines.append("")
        lines.append("export function getIconPath(key: IconKey): string {")
        lines.append("  return ICONS[key];")
        lines.append("}")
        lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _to_component_name(icon_id: str) -> str:
        """Convert icon ID to React component name (PascalCase + Icon suffix)."""
        # lock-32x32 -> Lock32x32Icon
        parts = icon_id.replace("-", " ").replace("x", "X").split()
        pascal = "".join(p.capitalize() for p in parts)
        return f"{pascal}Icon"

    @staticmethod
    def _to_key_name(icon_id: str) -> str:
        """Convert icon ID to camelCase key."""
        # lock-32x32 -> lock32x32
        parts = icon_id.replace("-", "_").split("_")
        if len(parts) == 1:
            return parts[0]
        return parts[0] + "".join(p.capitalize() for p in parts[1:])


def load_catalog(path: str) -> Dict:
    """
    Load icon catalog from JSON file.

    Args:
        path: Path to icon-catalog.json

    Returns:
        Catalog dictionary
    """
    catalog_path = Path(path)
    if not catalog_path.exists():
        raise FileNotFoundError(f"Catalog not found: {path}")

    with open(catalog_path) as f:
        return json.load(f)
