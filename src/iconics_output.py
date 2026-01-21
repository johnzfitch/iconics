"""
Iconics Output Formatting Module

Provides clean, context-aware output formatting for CLI and API usage.
Supports multiple output modes: compact, table, json, quiet.
"""

import json
import sys
from typing import Any, Dict, List, Optional


# Global singleton for output context
_global_output = None


class OutputContext:
    """Global output context singleton."""

    @classmethod
    def set_global(cls, output):
        """Set global output formatter."""
        global _global_output
        _global_output = output

    @classmethod
    def get_global(cls):
        """Get global output formatter."""
        return _global_output


class OutputFormatter:
    """Format iconics output for different contexts (human, machine, Claude)."""

    def __init__(self, mode: str = "compact", quiet: bool = False, color: bool = True):
        """
        Initialize formatter.

        Args:
            mode: Output mode - "compact", "table", "json", "quiet"
            quiet: If True, suppress all non-essential output
            color: If True, use ANSI colors in output
        """
        self.mode = mode
        self.quiet = quiet
        self.use_color = color and sys.stdout.isatty()

        # ANSI color codes
        if self.use_color:
            self.colors = {
                'RED': '\033[0;31m',
                'GREEN': '\033[0;32m',
                'YELLOW': '\033[1;33m',
                'BLUE': '\033[0;34m',
                'CYAN': '\033[0;36m',
                'MAGENTA': '\033[0;35m',
                'END': '\033[0m',
            }
        else:
            self.colors = {k: '' for k in ['RED', 'GREEN', 'YELLOW', 'BLUE', 'CYAN', 'MAGENTA', 'END']}

    def format_search_results(
        self,
        results: List[Dict],
        query: str,
        show_scores: bool = False
    ) -> str:
        """
        Format search results.

        Args:
            results: List of result dicts with icon_id, score, residual_score
            query: Original search query
            show_scores: Whether to show similarity scores

        Returns:
            Formatted string
        """
        if self.mode == "json":
            return json.dumps({
                "query": query,
                "count": len(results),
                "results": results
            }, indent=2)

        if self.mode == "quiet":
            # Just icon IDs, one per line
            return "\n".join(r["icon_id"] for r in results)

        if self.mode == "table":
            return self._format_table_results(results, query, show_scores)

        # Compact mode (default)
        return self._format_compact_results(results, query, show_scores)

    def _format_compact_results(
        self,
        results: List[Dict],
        query: str,
        show_scores: bool
    ) -> str:
        """Compact one-line format."""
        lines = []

        if not self.quiet:
            lines.append(f"Results for '{query}' ({len(results)} found):")

        for i, r in enumerate(results, 1):
            icon_id = r["icon_id"]

            if show_scores:
                lines.append(f"  {i}. {icon_id} ({r['score']:.3f})")
            else:
                lines.append(f"  {i}. {icon_id}")

        return "\n".join(lines)

    def _format_table_results(
        self,
        results: List[Dict],
        query: str,
        show_scores: bool
    ) -> str:
        """Table format with aligned columns."""
        lines = []

        if not self.quiet:
            lines.append(f"Search: '{query}' ({len(results)} results)")
            lines.append("")

        # Header
        if show_scores:
            lines.append("  #  Icon ID                        Score")
            lines.append("  " + "─" * 50)
        else:
            lines.append("  #  Icon ID")
            lines.append("  " + "─" * 35)

        # Results
        for i, r in enumerate(results, 1):
            icon_id = r["icon_id"]

            if show_scores:
                lines.append(f"  {i:2d}  {icon_id:30s}  {r['score']:.3f}")
            else:
                lines.append(f"  {i:2d}  {icon_id}")

        return "\n".join(lines)

    def format_suggestions(
        self,
        suggestions: List[Dict],
        context: str,
        limit: int
    ) -> str:
        """
        Format context-based suggestions.

        Args:
            suggestions: List of (icon_dict, score) tuples
            context: Context keyword
            limit: Number shown

        Returns:
            Formatted string
        """
        if self.mode == "json":
            return json.dumps({
                "context": context,
                "suggestions": [
                    {
                        "id": s[0]["id"],
                        "semantic_name": s[0]["semanticName"],
                        "score": float(s[1]) if len(s) > 1 else 1.0
                    }
                    for s in suggestions
                ]
            }, indent=2)

        if self.mode == "quiet":
            return "\n".join(s[0]["semanticName"] for s in suggestions)

        # Compact/table mode
        lines = []
        if not self.quiet:
            lines.append(f"Suggestions for '{context}':")

        for i, (icon, score) in enumerate(suggestions[:limit], 1):
            name = icon["semanticName"]
            tags = ", ".join(icon.get("tags", [])[:3])  # First 3 tags

            if self.mode == "table":
                lines.append(f"  {i}. {name:20s}  [{tags}]")
            else:
                lines.append(f"  {i}. {name}")

        return "\n".join(lines)

    def format_export_result(
        self,
        exported: List[str],
        failed: List[str],
        project_path: str,
        markdown_snippets: Optional[List[str]] = None
    ) -> str:
        """
        Format export results.

        Args:
            exported: List of successfully exported icon IDs
            failed: List of failed icon IDs
            project_path: Destination path
            markdown_snippets: Optional markdown snippets for each icon

        Returns:
            Formatted string
        """
        if self.mode == "json":
            return json.dumps({
                "exported": exported,
                "failed": failed,
                "project": project_path,
                "markdown": markdown_snippets
            }, indent=2)

        if self.mode == "quiet":
            if markdown_snippets:
                return "\n".join(markdown_snippets)
            return "\n".join(exported)

        # Compact/table mode
        lines = []

        if not self.quiet:
            lines.append(f"Exported to: {project_path}")
            lines.append("")

        if exported:
            lines.append(f"OK: Exported {len(exported)} icon(s):")
            for icon_id in exported:
                lines.append(f"  - {self._clean_icon_id(icon_id)}")

        if failed:
            lines.append("")
            lines.append(f"ERR: Failed {len(failed)} icon(s):")
            for icon_id in failed:
                lines.append(f"  - {icon_id}")

        if markdown_snippets and not self.quiet:
            lines.append("")
            lines.append("Markdown:")
            for snippet in markdown_snippets:
                lines.append(f"  {snippet}")

        return "\n".join(lines)

    def format_validation(self, validation_result: Dict) -> str:
        """
        Format validation results.

        Args:
            validation_result: Dict with validation status

        Returns:
            Formatted string
        """
        if self.mode == "json":
            return json.dumps(validation_result, indent=2)

        if self.mode == "quiet":
            return "pass" if validation_result.get("passed", False) else "fail"

        # Compact/table mode
        lines = []
        lines.append("Validation Results:")
        lines.append("")

        for check, status in validation_result.items():
            if isinstance(status, bool):
                symbol = "OK" if status else "ERR"
                lines.append(f"  {symbol} {check}")
            elif isinstance(status, dict):
                lines.append(f"  {check}:")
                for key, val in status.items():
                    lines.append(f"    {key}: {val}")

        return "\n".join(lines)

    def format_icon_info(self, icon: Dict) -> str:
        """
        Format detailed icon information.

        Args:
            icon: Icon metadata dict

        Returns:
            Formatted string
        """
        if self.mode == "json":
            return json.dumps(icon, indent=2)

        if self.mode == "quiet":
            return icon["id"]

        # Compact/table mode
        lines = []
        lines.append(f"Icon: {icon['semanticName']}")
        lines.append(f"  ID: {icon['id']}")
        lines.append(f"  Category: {icon.get('category', 'unknown')}")
        lines.append(f"  Tags: {', '.join(icon.get('tags', []))}")

        if icon.get("description"):
            lines.append(f"  Description: {icon['description']}")

        if icon.get("usedIn"):
            lines.append(f"  Used in: {', '.join(icon['usedIn'])}")

        return "\n".join(lines)

    def _clean_icon_id(self, icon_id: str) -> str:
        """
        Clean icon ID for display (remove size suffixes).

        Args:
            icon_id: Raw icon ID

        Returns:
            Cleaned ID for display
        """
        # Remove common size suffixes for cleaner display
        for suffix in ["-64x64", "-32x32", "-24x24", "-12x12", "_64x64", "_32x32", "_24x24", "_12x12"]:
            if icon_id.endswith(suffix):
                return icon_id[:-len(suffix)]

        return icon_id

    def print(self, *args, **kwargs):
        """Print unless in quiet mode."""
        if not self.quiet:
            print(*args, **kwargs)

    def error(self, message: str):
        """Print error to stderr."""
        print(f"Error: {message}", file=sys.stderr)


# Convenience functions for quick formatting
def format_compact(data: Any, **kwargs) -> str:
    """Format data in compact mode."""
    formatter = OutputFormatter(mode="compact", **kwargs)
    if isinstance(data, list) and all(isinstance(x, dict) for x in data):
        return formatter.format_search_results(data, "", **kwargs)
    return str(data)


def format_json(data: Any) -> str:
    """Format data as JSON."""
    return json.dumps(data, indent=2)


def format_quiet(data: List[Dict]) -> str:
    """Format data in quiet mode (IDs only)."""
    if isinstance(data, list) and all(isinstance(x, dict) for x in data):
        return "\n".join(x.get("icon_id", x.get("id", "")) for x in data)
    return ""


# Convenience Output class with logging methods
class Output(OutputFormatter):
    """Extended output formatter with logging methods for agent-friendly CLI."""

    def info(self, message: str):
        """Print info message (respects quiet mode)."""
        if not self.quiet:
            if self.mode == 'json':
                print(json.dumps({"level": "info", "message": message}))
            else:
                print(f"{self.colors['BLUE']}INFO{self.colors['END']} {message}")

    def success(self, message: str):
        """Print success message (respects quiet mode)."""
        if not self.quiet:
            if self.mode == 'json':
                print(json.dumps({"level": "success", "message": message}))
            else:
                print(f"{self.colors['GREEN']}OK{self.colors['END']} {message}")

    def error(self, message: str):
        """Print error message to stderr (always shown)."""
        if self.mode == 'json':
            print(json.dumps({"level": "error", "message": message}), file=sys.stderr)
        else:
            print(f"{self.colors['RED']}ERR{self.colors['END']} {message}", file=sys.stderr)

    def warn(self, message: str):
        """Print warning message (respects quiet mode)."""
        if not self.quiet:
            if self.mode == 'json':
                print(json.dumps({"level": "warning", "message": message}))
            else:
                print(f"{self.colors['YELLOW']}WARN{self.colors['END']} {message}")

    def debug(self, message: str):
        """Print debug message (only in verbose mode)."""
        if self.mode == 'table':  # verbose mode
            print(f"{self.colors['CYAN']}DEBUG:{self.colors['END']} {message}")

    def format_audit_correction(self, original_label: str, corrected_label: str, reason: str):
        """Report a naming drift correction (for Reflective Audit)."""
        if self.quiet:
            return  # Agents don't need to see the audit details

        if self.mode == 'json':
            print(json.dumps({
                "audit": "correction",
                "from": original_label,
                "to": corrected_label,
                "reason": reason
            }))
            return

        # Human-friendly visual trace
        print(f"   {self.colors['YELLOW']}Audit:{self.colors['END']} Detected naming drift '{self.colors['YELLOW']}{original_label}{self.colors['END']}'")
        print(f"  {self.colors['GREEN']}OK{self.colors['END']} Action: Re-aligned to catalog standard '{self.colors['GREEN']}{corrected_label}{self.colors['END']}'")
        print(f"   Reason: {reason}")

    def format_ingest_result_detailed(self, result):
        """Format detailed ingest result (after Reflective Audit)."""
        if self.quiet:
            # Agent mode: just the icon ID
            print(result.get('icon_id', ''))
            return

        if self.mode == 'json':
            print(json.dumps(result, indent=2 if not self.quiet else None))
            return

        # Human mode: show bypass vs VLM
        path_name = result.get('path', {}).get('name', 'unknown') if isinstance(result.get('path'), dict) else str(result.get('path', 'unknown'))
        icon_id = result.get('icon_id', 'unknown')
        status = result.get('status', 'unknown')
        confidence = result.get('confidence', 0.0)

        if status == 'bypass':
            print(f"BYPASS {self.colors['CYAN']}{path_name}{self.colors['END']} -> {icon_id} (sim={confidence:.3f})")
        elif status == 'vlm':
            print(f"VLM {self.colors['GREEN']}{path_name}{self.colors['END']} -> {icon_id} (conf={confidence:.3f})")
        else:
            print(f"{path_name} -> {icon_id} (status={status})")

    def format_stats(self, stats: Dict):
        """Format library statistics."""
        if self.mode == 'json':
            print(json.dumps(stats, indent=2 if not self.quiet else None))
            return

        if self.quiet:
            # Just total count for agents
            print(stats.get('total', stats.get('total_icons', 0)))
            return

        # Human mode
        print(f"\n{self.colors['BLUE']}Iconics Library Statistics{self.colors['END']}")
        print(f"{'='*40}")
        for key, value in stats.items():
            key_display = key.replace('_', ' ').title()
            print(f"  {key_display}: {value}")

    def format_recent(self, icons: List[Dict], limit: int):
        """Format recently cataloged icons."""
        if self.mode == 'json':
            print(json.dumps({"recent": icons[:limit]}, indent=2 if not self.quiet else None))
            return

        if self.quiet:
            # Just IDs for agents
            for icon in icons[:limit]:
                print(icon.get('id', icon.get('semanticName', '')))
            return

        # Human mode
        print(f"\n{self.colors['BLUE']}Recently Cataloged Icons (last {limit}){self.colors['END']}")
        print(f"{'='*40}")
        for i, icon in enumerate(icons[:limit], 1):
            name = icon.get('semanticName', icon.get('id', 'unknown'))
            category = icon.get('category', 'unknown')
            print(f"  {i}. {self.colors['GREEN']}{name}{self.colors['END']} ({category})")
