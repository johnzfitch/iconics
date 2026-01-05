"""
Iconics Export Module

Handles icon export operations with intelligent project detection,
usage tracking, and markdown generation.
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from iconics_output import OutputContext


class IconExporter:
    """
    Handles icon export operations for the Iconics system.

    Features:
    - Intelligent project directory detection
    - Automatic .github/assets/icons/ discovery
    - Usage tracking for analytics
    - Markdown snippet generation
    """

    def __init__(self, catalog, icon_dir: Path = Path('catalog')):
        """
        Initialize the exporter.

        Args:
            catalog: IconCatalog instance for metadata lookups
            icon_dir: Base directory containing icon files
        """
        self.catalog = catalog
        self.icon_dir = icon_dir
        self.output = OutputContext.get_global()

    def find_project_icon_dir(self, start_path: Optional[Path] = None) -> Path:
        """
        Find the appropriate icon directory for export.

        Searches for .github/assets/icons/ by walking up from start_path.
        Falls back to current directory if no project structure found.

        Args:
            start_path: Starting directory (default: cwd)

        Returns:
            Path to icon export directory
        """
        current = (start_path or Path.cwd()).resolve()

        # Walk up directory tree looking for project markers
        for parent in [current] + list(current.parents):
            # Check for existing .github/assets/icons/
            target = parent / ".github" / "assets" / "icons"
            if target.exists() and target.is_dir():
                return target

            # Check for git root (create structure there if found)
            if (parent / ".git").exists():
                return target  # Return even if doesn't exist - will be created

        # Fallback: use current directory
        return current / "icons"

    def resolve_icon_path(self, icon_id: str) -> Optional[tuple[Dict, Path]]:
        """
        Resolve icon ID to catalog entry and file path.

        Args:
            icon_id: Icon identifier

        Returns:
            Tuple of (catalog_entry, source_path) or None if not found
        """
        entry = self.catalog.get_entry(icon_id)
        if not entry:
            return None

        # Get source file path (try both 'sourceFile' and 'filename')
        source_file = entry.get('sourceFile') or entry.get('filename')
        if not source_file:
            return None

        source_path = Path(source_file)
        if not source_path.is_absolute():
            # Try relative to project root
            source_path = Path.cwd() / source_path

        if not source_path.exists():
            return None

        return entry, source_path

    def export_icons(
        self,
        icon_ids: List[str],
        target_dir: Optional[Path] = None,
        generate_markdown: bool = True
    ) -> Dict:
        """
        Export icons to target directory.

        Args:
            icon_ids: List of icon IDs to export
            target_dir: Target directory (auto-detected if None)
            generate_markdown: Whether to generate markdown snippets

        Returns:
            Dict with exported, failed, and markdown lists
        """
        dest = target_dir or self.find_project_icon_dir()
        dest.mkdir(parents=True, exist_ok=True)

        exported = []
        failed = []
        markdown_snippets = []

        for icon_id in icon_ids:
            result = self.resolve_icon_path(icon_id)

            if not result:
                failed.append(icon_id)
                if self.output and self.output.mode != 'quiet':
                    self.output.error(f"Icon '{icon_id}' not found in catalog")
                continue

            entry, src_path = result
            semantic_name = entry.get('semanticName', icon_id)

            # Target filename uses semantic name
            target_path = dest / f"{semantic_name}.png"

            try:
                shutil.copy2(src_path, target_path)

                # Calculate relative path from cwd for markdown
                try:
                    rel_path = os.path.relpath(target_path, Path.cwd())
                except ValueError:
                    # On Windows, relpath fails across drives
                    rel_path = str(target_path)

                exported.append({
                    'id': icon_id,
                    'semantic_name': semantic_name,
                    'path': str(target_path),
                    'rel_path': rel_path
                })

                # Generate markdown snippet
                if generate_markdown:
                    markdown_snippets.append(f"![{semantic_name}]({rel_path})")

                if self.output and self.output.mode == 'table':  # verbose mode
                    self.output.success(f"Exported {semantic_name}.png")

            except Exception as e:
                failed.append(icon_id)
                if self.output and self.output.mode != 'quiet':
                    self.output.error(f"Failed to export {icon_id}: {str(e)}")

        return {
            'exported': exported,
            'failed': failed,
            'target_dir': str(dest),
            'markdown': markdown_snippets if generate_markdown else None
        }

    def track_usage(self, project_path: Path, icon_ids: List[str]):
        """
        Track icon usage for analytics and history.

        Args:
            project_path: Project directory path
            icon_ids: List of icon IDs used
        """
        project_name = project_path.name
        timestamp = datetime.now().isoformat()

        # History file (per-project usage)
        history_file = Path.cwd() / 'icon-usage-history.json'
        history = {}

        if history_file.exists():
            with open(history_file) as f:
                history = json.load(f)

        history[project_name] = {
            'path': str(project_path),
            'icons': icon_ids,
            'timestamp': timestamp
        }

        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)

        # Analytics file (global usage stats)
        analytics_file = Path.cwd() / 'icon-usage-analytics.json'
        analytics = {}

        if analytics_file.exists():
            with open(analytics_file) as f:
                analytics = json.load(f)

        for icon_id in icon_ids:
            if icon_id not in analytics:
                analytics[icon_id] = {'count': 0, 'projects': []}

            analytics[icon_id]['count'] += 1
            if project_name not in analytics[icon_id]['projects']:
                analytics[icon_id]['projects'].append(project_name)

        with open(analytics_file, 'w') as f:
            json.dump(analytics, f, indent=2)
