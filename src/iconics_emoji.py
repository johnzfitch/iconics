"""
Iconics Emoji Scanning and Conversion Module

This module scans files for emoji usage and suggests icon replacements.
It helps migrate projects from emoji-based documentation to professional
icon-based documentation.

Key Features:
    - Scan files/directories for emoji usage
    - Map emojis to semantic icon queries
    - Generate replacement suggestions with context
    - Apply conversions (with dry-run support)

Example:
    >>> scanner = EmojiScanner()
    >>> report = scanner.scan("./docs")
    >>> print(report["emojis_found"])
    15
    >>> # Convert with preview
    >>> changes = scanner.convert(report, "./icons", dry_run=True)
"""

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class EmojiScanner:
    """
    Scan files for emoji usage and suggest icon replacements.

    This class provides methods to find emojis in source files and
    documentation, and suggests appropriate icon replacements based
    on semantic meaning.

    Attributes:
        retriever: Optional IconicsRetriever for vector-based suggestions
        EMOJI_MAP: Mapping of emojis to semantic search queries

    Example:
        >>> scanner = EmojiScanner()
        >>> report = scanner.scan("./README.md", extensions=["md"])
        >>> for occ in report["occurrences"]:
        ...     print(f"{occ['emoji']} -> {occ['suggested_icons']}")
    """

    # Emoji to semantic query mapping
    # Maps common emojis to icon search queries
    EMOJI_MAP: Dict[str, str] = {
        # Security/Lock
        "\U0001F512": "lock security",           #
        "\U0001F513": "unlock open-lock",        #
        "\U0001F510": "lock security private",   #
        "\U0001F511": "key authentication",      #

        # Status/Alerts
        "\u26A0\uFE0F": "warning alert",         #
        "\u26A0": "warning alert",               # (without variant selector)
        "\u2705": "success check complete",      #
        "\u274C": "error close remove",          #
        "\u2754": "question help",               #
        "\u2753": "question help",               #
        "\u2139\uFE0F": "info information",      #
        "\u2139": "info information",            # (without variant selector)

        # Arrows/Navigation
        "\U0001F680": "launch speed rocket",     #
        "\u2B06\uFE0F": "arrow up",              #
        "\u2B07\uFE0F": "arrow down",            #
        "\u27A1\uFE0F": "arrow right",           #
        "\u2B05\uFE0F": "arrow left",            #

        # Files/Folders
        "\U0001F4C1": "folder directory",        #
        "\U0001F4C2": "folder open",             #
        "\U0001F4C4": "document file",           #
        "\U0001F4DD": "document edit write",     #
        "\U0001F4CB": "clipboard",               #
        "\U0001F4DA": "books documentation",     #

        # Settings/Tools
        "\u2699\uFE0F": "settings config gear",  #
        "\u2699": "settings config gear",        # (without variant selector)
        "\U0001F527": "settings tool wrench",    #
        "\U0001F6E0\uFE0F": "tools development", #
        "\U0001F6E0": "tools development",       # (without variant selector)

        # Users/People
        "\U0001F464": "user profile person",     #
        "\U0001F465": "users group team",        #

        # Communication
        "\U0001F514": "notification alert bell", #
        "\U0001F4E7": "email mail",              #
        "\U0001F4AC": "chat message",            #
        "\U0001F4E2": "announcement megaphone",  #

        # Commerce
        "\U0001F4B3": "payment billing card",    #
        "\U0001F6D2": "cart shopping",           #

        # Search/Find
        "\U0001F50D": "search find magnify",     #
        "\U0001F50E": "search find magnify",     #

        # Actions
        "\u2795": "add create plus",             #
        "\U0001F5D1\uFE0F": "delete trash remove",  #
        "\U0001F5D1": "delete trash remove",     # (without variant selector)
        "\U0001F4E4": "upload export",           #
        "\U0001F4E5": "download import",         #
        "\U0001F517": "link chain url",          #
        "\U0001F504": "refresh sync",            #
        "\U0001F4BE": "save disk",               #

        # Charts/Data
        "\U0001F4CA": "chart analytics bar",     #
        "\U0001F4C8": "chart growth line",       #
        "\U0001F4C9": "chart decline line",      #
        "\U0001F5C3\uFE0F": "database storage",  #
        "\U0001F5C4\uFE0F": "archive storage",   #

        # Time
        "\u23F0": "clock alarm time",            #
        "\U0001F550": "clock time",              #
        "\U0001F4C5": "calendar date",           #
        "\u23F1\uFE0F": "time clock timer",      #
        "\u23F1": "time clock timer",            # (without variant selector)

        # Home/Building
        "\U0001F3E0": "home house",              #

        # Misc
        "\U0001F4A1": "idea tip lightbulb",      #
        "\u2B50": "star favorite",               #
        "\U0001F31F": "star sparkle",            #
        "\u2764\uFE0F": "heart like",            #
        "\U0001F525": "fire trending hot",       #
        "\u2728": "sparkle new",                 #
        "\U0001F6E1\uFE0F": "shield protection", #
        "\U0001F6E1": "shield protection",       # (without variant selector)

        # Status indicators
        "\U0001F534": "status red error",        #
        "\U0001F7E0": "status orange warning",   #
        "\U0001F7E1": "status yellow caution",   #
        "\U0001F7E2": "status green success",    #
        "\U0001F535": "status blue info",        #

        # Media
        "\U0001F4F7": "camera photo",            #
        "\U0001F4F8": "camera photo flash",      #
        "\U0001F3AC": "video media",             #
        "\U0001F3A5": "video camera",            #
        "\U0001F3B5": "audio music",             #
        "\U0001F3B6": "music notes",             #
        "\U0001F5BC\uFE0F": "image picture",     #
        "\U0001F5BC": "image picture",           # (without variant selector)

        # Cloud/Network
        "\U0001F310": "globe world internet",    #
        "\U0001F30D": "globe earth",             #
        "\U0001F30E": "globe americas",          #
        "\U0001F30F": "globe asia",              #
        "\u2601\uFE0F": "cloud server",          #
        "\u2601": "cloud server",                # (without variant selector)
        "\U0001F4E1": "network signal",          #
    }

    # Compiled regex pattern for emoji detection
    # This matches common emoji ranges
    EMOJI_PATTERN = re.compile(
        "["
        "\U0001F300-\U0001F9FF"  # Miscellaneous Symbols and Pictographs, Emoticons, etc.
        "\U00002702-\U000027B0"  # Dingbats
        "\U0001F600-\U0001F64F"  # Emoticons
        "\U0001F680-\U0001F6FF"  # Transport and Map Symbols
        "\U0001F1E0-\U0001F1FF"  # Flags
        "\u2600-\u26FF"          # Misc symbols
        "\u2700-\u27BF"          # Dingbats
        "\u23E9-\u23F3"          # Media control symbols
        "\u23F0-\u23FA"          # Clock and media symbols
        "\u2934-\u2935"          # Arrows
        "\u25AA-\u25FE"          # Geometric shapes
        "\u2B05-\u2B07"          # Arrows
        "\u2B1B-\u2B1C"          # Squares
        "\u2B50"                 # Star
        "\u2B55"                 # Circle
        "\u3030"                 # Wavy dash
        "\u303D"                 # Part alternation mark
        "\u3297"                 # Circled Ideograph Congratulation
        "\u3299"                 # Circled Ideograph Secret
        "\uFE0F"                 # Variation Selector-16
        "]+",
        re.UNICODE
    )

    def __init__(self, retriever=None):
        """
        Initialize emoji scanner.

        Args:
            retriever: Optional IconicsRetriever for vector-based icon suggestions.
                      If None, uses static EMOJI_MAP for suggestions.
        """
        self.retriever = retriever

    def scan(
        self,
        path: str,
        extensions: Optional[List[str]] = None,
        recursive: bool = True
    ) -> Dict:
        """
        Scan files for emoji usage.

        Args:
            path: File or directory path to scan
            extensions: File extensions to scan (default: ["md", "mdx", "tsx", "jsx", "html"])
            recursive: If True and path is directory, scan recursively

        Returns:
            Scan report dictionary:
            {
                "files_scanned": 42,
                "emojis_found": 15,
                "occurrences": [
                    {
                        "file": "README.md",
                        "line": 10,
                        "column": 5,
                        "emoji": "",
                        "context": "## Security",
                        "suggested_query": "lock security",
                        "suggested_icons": ["lock-32x32", "shield-32x32"]
                    }
                ]
            }
        """
        if extensions is None:
            extensions = ["md", "mdx", "tsx", "jsx", "html", "vue", "svelte"]

        scan_path = Path(path)
        occurrences = []
        files_scanned = 0

        if scan_path.is_file():
            # Single file scan
            if self._should_scan(scan_path, extensions):
                occurrences.extend(self._scan_file(scan_path))
                files_scanned = 1
        elif scan_path.is_dir():
            # Directory scan
            pattern = "**/*" if recursive else "*"
            for file_path in scan_path.glob(pattern):
                if file_path.is_file() and self._should_scan(file_path, extensions):
                    occurrences.extend(self._scan_file(file_path))
                    files_scanned += 1
        else:
            raise FileNotFoundError(f"Path not found: {path}")

        # Deduplicate by emoji, keeping counts
        emoji_counts: Dict[str, int] = {}
        for occ in occurrences:
            emoji = occ["emoji"]
            emoji_counts[emoji] = emoji_counts.get(emoji, 0) + 1

        logger.info(
            f"Scanned {files_scanned} files, found {len(occurrences)} emoji occurrences"
        )

        return {
            "files_scanned": files_scanned,
            "emojis_found": len(occurrences),
            "unique_emojis": len(emoji_counts),
            "emoji_counts": emoji_counts,
            "occurrences": occurrences
        }

    def convert(
        self,
        report: Dict,
        icon_path: str,
        dry_run: bool = True,
        icon_format: str = "![{name}]({path})"
    ) -> Dict:
        """
        Apply emoji-to-icon conversions.

        Args:
            report: Scan report from scan() method
            icon_path: Path to icons directory (relative to files being converted)
            dry_run: If True, return diffs without modifying files
            icon_format: Format string for icon markdown. Placeholders:
                        {name} = icon semantic name
                        {path} = full icon path

        Returns:
            Conversion result:
            {
                "files_modified": 3,
                "replacements_made": 15,
                "dry_run": True,
                "changes": [
                    {
                        "file": "README.md",
                        "line": 10,
                        "original": "## Security",
                        "replaced": "## ![lock](icons/lock-32x32.png) Security"
                    }
                ]
            }
        """
        changes = []
        files_to_modify: Dict[str, List[Dict]] = {}

        # Group occurrences by file
        for occ in report.get("occurrences", []):
            file_path = occ["file"]
            if file_path not in files_to_modify:
                files_to_modify[file_path] = []
            files_to_modify[file_path].append(occ)

        files_modified = 0
        replacements_made = 0

        for file_path, file_occurrences in files_to_modify.items():
            try:
                path = Path(file_path)
                content = path.read_text(encoding="utf-8")
                lines = content.split("\n")
                modified = False

                # Sort occurrences by line, then by column (reverse for in-place replacement)
                sorted_occs = sorted(
                    file_occurrences,
                    key=lambda x: (x["line"], x["column"]),
                    reverse=True
                )

                for occ in sorted_occs:
                    line_idx = occ["line"] - 1  # Convert to 0-indexed
                    if line_idx >= len(lines):
                        continue

                    emoji = occ["emoji"]
                    suggested_icons = occ.get("suggested_icons", [])

                    if not suggested_icons:
                        continue

                    # Use first suggested icon
                    icon_id = suggested_icons[0]
                    icon_name = icon_id.split("-")[0]  # e.g., "lock" from "lock-32x32"

                    # Generate replacement text
                    replacement = icon_format.format(
                        name=icon_name,
                        path=f"{icon_path}/{icon_id}.png"
                    )

                    # Record the change
                    original_line = lines[line_idx]
                    new_line = original_line.replace(emoji, replacement, 1)

                    if original_line != new_line:
                        changes.append({
                            "file": file_path,
                            "line": occ["line"],
                            "original": original_line,
                            "replaced": new_line,
                            "emoji": emoji,
                            "icon": icon_id
                        })

                        lines[line_idx] = new_line
                        modified = True
                        replacements_made += 1

                # Write changes if not dry run
                if modified and not dry_run:
                    path.write_text("\n".join(lines), encoding="utf-8")
                    files_modified += 1

            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                continue

        if dry_run:
            files_modified = len(files_to_modify)

        return {
            "files_modified": files_modified,
            "replacements_made": replacements_made,
            "dry_run": dry_run,
            "changes": changes
        }

    def get_icon_suggestions(
        self,
        emoji: str,
        k: int = 3
    ) -> List[str]:
        """
        Get icon suggestions for an emoji.

        Args:
            emoji: Emoji character(s)
            k: Number of suggestions to return

        Returns:
            List of icon IDs
        """
        # Get semantic query from emoji map
        query = self.EMOJI_MAP.get(emoji, "")

        if not query:
            # Try without variation selector
            emoji_base = emoji.replace("\uFE0F", "")
            query = self.EMOJI_MAP.get(emoji_base, "icon ui")

        # If we have a retriever, use vector search
        if self.retriever is not None:
            try:
                results = self.retriever.retrieve(query, k=k, mode="projected")
                return [r.icon_id for r in results]
            except Exception as e:
                logger.warning(f"Vector retrieval failed: {e}")

        # Fallback: return query terms as icon suggestions
        return [f"{term}-32x32" for term in query.split()[:k]]

    def _should_scan(self, file_path: Path, extensions: List[str]) -> bool:
        """Check if file should be scanned based on extension."""
        ext = file_path.suffix.lstrip(".")
        return ext.lower() in [e.lower() for e in extensions]

    def _scan_file(self, file_path: Path) -> List[Dict]:
        """Scan a single file for emojis."""
        occurrences = []

        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")

            for line_num, line in enumerate(lines, start=1):
                # Find all emojis in line
                for match in self.EMOJI_PATTERN.finditer(line):
                    emoji = match.group()

                    # Get context (surrounding text)
                    start = max(0, match.start() - 30)
                    end = min(len(line), match.end() + 30)
                    context = line[start:end].strip()

                    # Get suggestions
                    suggested_icons = self.get_icon_suggestions(emoji)
                    suggested_query = self.EMOJI_MAP.get(
                        emoji,
                        self.EMOJI_MAP.get(emoji.replace("\uFE0F", ""), "")
                    )

                    occurrences.append({
                        "file": str(file_path),
                        "line": line_num,
                        "column": match.start() + 1,
                        "emoji": emoji,
                        "context": context,
                        "suggested_query": suggested_query,
                        "suggested_icons": suggested_icons
                    })

        except Exception as e:
            logger.error(f"Error scanning {file_path}: {e}")

        return occurrences


def find_emojis(text: str) -> List[Tuple[str, int, int]]:
    """
    Find all emojis in text with positions.

    Args:
        text: Text to scan

    Returns:
        List of tuples: (emoji, start_pos, end_pos)
    """
    scanner = EmojiScanner()
    results = []

    for match in scanner.EMOJI_PATTERN.finditer(text):
        results.append((match.group(), match.start(), match.end()))

    return results
