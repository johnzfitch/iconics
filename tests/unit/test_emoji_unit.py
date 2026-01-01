"""
Unit tests for iconics_emoji.py

Tests the EmojiScanner class for detecting emojis in files and
suggesting icon replacements.
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
import sys

# Add src to path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from iconics_emoji import EmojiScanner, find_emojis

# Emoji constants for consistent testing
EMOJI_LOCK = "\U0001F512"      #
EMOJI_SHIELD = "\U0001F6E1"    #
EMOJI_KEY = "\U0001F511"       #
EMOJI_WARNING = "\u26A0\uFE0F" #
EMOJI_CHECK = "\u2705"         #
EMOJI_FOLDER = "\U0001F4C1"    #
EMOJI_GEAR = "\u2699\uFE0F"    #
EMOJI_STAR = "\u2B50"          #
EMOJI_ROCKET = "\U0001F680"    #


class TestEmojiScanner(unittest.TestCase):
    """Test EmojiScanner class."""

    def setUp(self):
        """Create scanner and temp directory."""
        self.scanner = EmojiScanner()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temp directory."""
        shutil.rmtree(self.temp_dir)

    def test_init_without_retriever(self):
        """Test scanner initialization without retriever."""
        scanner = EmojiScanner()
        self.assertIsNone(scanner.retriever)

    def test_init_with_retriever(self):
        """Test scanner initialization with mock retriever."""
        mock_retriever = MagicMock()
        scanner = EmojiScanner(retriever=mock_retriever)
        self.assertEqual(scanner.retriever, mock_retriever)

    def test_emoji_map_exists(self):
        """Test that EMOJI_MAP is populated."""
        self.assertGreater(len(EmojiScanner.EMOJI_MAP), 20)
        self.assertIn("\U0001F512", EmojiScanner.EMOJI_MAP)  # lock
        self.assertIn("\u26A0\uFE0F", EmojiScanner.EMOJI_MAP)  # warning

    def test_scan_single_file(self):
        """Test scanning a single file."""
        # Create test file with emojis
        test_file = Path(self.temp_dir) / "test.md"
        test_file.write_text(f"# Security {EMOJI_LOCK}\n\nThis is protected {EMOJI_SHIELD} content.")

        report = self.scanner.scan(str(test_file))

        self.assertEqual(report["files_scanned"], 1)
        self.assertGreater(report["emojis_found"], 0)
        self.assertIn("occurrences", report)

    def test_scan_directory_recursive(self):
        """Test recursive directory scanning."""
        # Create directory structure
        subdir = Path(self.temp_dir) / "docs"
        subdir.mkdir()

        (Path(self.temp_dir) / "README.md").write_text(f"# Project {EMOJI_ROCKET}")
        (subdir / "guide.md").write_text(f"## Guide {EMOJI_STAR}")

        report = self.scanner.scan(str(self.temp_dir), extensions=["md"], recursive=True)

        self.assertEqual(report["files_scanned"], 2)
        self.assertEqual(report["emojis_found"], 2)

    def test_scan_directory_non_recursive(self):
        """Test non-recursive directory scanning."""
        subdir = Path(self.temp_dir) / "docs"
        subdir.mkdir()

        (Path(self.temp_dir) / "README.md").write_text(f"# Project {EMOJI_ROCKET}")
        (subdir / "guide.md").write_text(f"## Guide {EMOJI_STAR}")

        report = self.scanner.scan(str(self.temp_dir), extensions=["md"], recursive=False)

        self.assertEqual(report["files_scanned"], 1)  # Only root file

    def test_scan_filters_extensions(self):
        """Test that only specified extensions are scanned."""
        (Path(self.temp_dir) / "test.md").write_text(f"Markdown {EMOJI_LOCK}")
        (Path(self.temp_dir) / "test.txt").write_text(f"Text {EMOJI_KEY}")

        report = self.scanner.scan(str(self.temp_dir), extensions=["md"])

        self.assertEqual(report["files_scanned"], 1)

    def test_scan_occurrence_structure(self):
        """Test structure of occurrence records."""
        test_file = Path(self.temp_dir) / "test.md"
        test_file.write_text(f"## Security {EMOJI_LOCK}")

        report = self.scanner.scan(str(test_file))

        self.assertEqual(len(report["occurrences"]), 1)
        occ = report["occurrences"][0]

        self.assertIn("file", occ)
        self.assertIn("line", occ)
        self.assertIn("column", occ)
        self.assertIn("emoji", occ)
        self.assertIn("context", occ)
        self.assertIn("suggested_query", occ)
        self.assertIn("suggested_icons", occ)

    def test_scan_file_not_found(self):
        """Test error when path not found."""
        with self.assertRaises(FileNotFoundError):
            self.scanner.scan("/nonexistent/path")

    def test_scan_empty_file(self):
        """Test scanning file with no emojis."""
        test_file = Path(self.temp_dir) / "plain.md"
        test_file.write_text("This is plain text without emojis.")

        report = self.scanner.scan(str(test_file))

        self.assertEqual(report["emojis_found"], 0)
        self.assertEqual(report["unique_emojis"], 0)

    def test_scan_counts_unique_emojis(self):
        """Test counting unique emojis."""
        test_file = Path(self.temp_dir) / "test.md"
        test_file.write_text(f"Lock {EMOJI_LOCK} and more lock {EMOJI_LOCK} and warning {EMOJI_WARNING}")

        report = self.scanner.scan(str(test_file))

        self.assertEqual(report["emojis_found"], 3)
        self.assertEqual(report["unique_emojis"], 2)
        self.assertIn(EMOJI_LOCK, report["emoji_counts"])
        self.assertEqual(report["emoji_counts"][EMOJI_LOCK], 2)


class TestEmojiConvert(unittest.TestCase):
    """Test emoji conversion functionality."""

    def setUp(self):
        """Create scanner and temp directory."""
        self.scanner = EmojiScanner()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temp directory."""
        shutil.rmtree(self.temp_dir)

    def test_convert_dry_run(self):
        """Test conversion in dry-run mode."""
        test_file = Path(self.temp_dir) / "test.md"
        original_content = f"## Security {EMOJI_LOCK}"
        test_file.write_text(original_content)

        report = self.scanner.scan(str(test_file))
        result = self.scanner.convert(report, "./icons", dry_run=True)

        # File should be unchanged
        self.assertEqual(test_file.read_text(), original_content)

        # But changes should be recorded
        self.assertTrue(result["dry_run"])
        self.assertGreater(result["replacements_made"], 0)
        self.assertEqual(len(result["changes"]), 1)

    def test_convert_apply(self):
        """Test applying conversions."""
        test_file = Path(self.temp_dir) / "test.md"
        test_file.write_text(f"## Security {EMOJI_LOCK}")

        report = self.scanner.scan(str(test_file))
        result = self.scanner.convert(report, "./icons", dry_run=False)

        # File should be changed
        new_content = test_file.read_text()
        self.assertNotIn(EMOJI_LOCK, new_content)
        self.assertIn("![", new_content)

        self.assertFalse(result["dry_run"])
        self.assertGreater(result["replacements_made"], 0)

    def test_convert_change_structure(self):
        """Test structure of change records."""
        test_file = Path(self.temp_dir) / "test.md"
        test_file.write_text(f"## Security {EMOJI_LOCK}")

        report = self.scanner.scan(str(test_file))
        result = self.scanner.convert(report, "./icons", dry_run=True)

        change = result["changes"][0]

        self.assertIn("file", change)
        self.assertIn("line", change)
        self.assertIn("original", change)
        self.assertIn("replaced", change)
        self.assertIn("emoji", change)
        self.assertIn("icon", change)

    def test_convert_custom_format(self):
        """Test custom icon format."""
        test_file = Path(self.temp_dir) / "test.md"
        test_file.write_text(EMOJI_LOCK)

        report = self.scanner.scan(str(test_file))
        result = self.scanner.convert(
            report,
            "/static/icons",
            dry_run=True,
            icon_format="<Icon name=\"{name}\" />"
        )

        if result["changes"]:
            change = result["changes"][0]
            self.assertIn("<Icon name=", change["replaced"])


class TestEmojiSuggestions(unittest.TestCase):
    """Test icon suggestion functionality."""

    def test_get_icon_suggestions_known_emoji(self):
        """Test suggestions for known emoji."""
        scanner = EmojiScanner()

        suggestions = scanner.get_icon_suggestions("\U0001F512")  # lock

        self.assertIsInstance(suggestions, list)
        self.assertGreater(len(suggestions), 0)

    def test_get_icon_suggestions_unknown_emoji(self):
        """Test suggestions for unknown emoji (fallback)."""
        scanner = EmojiScanner()

        suggestions = scanner.get_icon_suggestions("\U0001F600")  # smiling face

        self.assertIsInstance(suggestions, list)
        # Should return fallback suggestions

    def test_get_icon_suggestions_with_retriever(self):
        """Test suggestions using mock retriever."""
        mock_result = MagicMock()
        mock_result.icon_id = "lock-32x32"

        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = [mock_result]

        scanner = EmojiScanner(retriever=mock_retriever)
        suggestions = scanner.get_icon_suggestions("\U0001F512")

        mock_retriever.retrieve.assert_called_once()
        self.assertIn("lock-32x32", suggestions)


class TestFindEmojis(unittest.TestCase):
    """Test find_emojis helper function."""

    def test_find_emojis_basic(self):
        """Test finding emojis in text."""
        text = f"Hello {EMOJI_LOCK} World {EMOJI_STAR}"

        results = find_emojis(text)

        self.assertEqual(len(results), 2)
        # Each result should be (emoji, start, end)
        self.assertEqual(len(results[0]), 3)

    def test_find_emojis_empty(self):
        """Test with no emojis."""
        text = "Plain text without emojis"

        results = find_emojis(text)

        self.assertEqual(len(results), 0)

    def test_find_emojis_multiple_same(self):
        """Test finding multiple same emojis."""
        text = f"{EMOJI_LOCK} {EMOJI_LOCK}"

        results = find_emojis(text)

        self.assertEqual(len(results), 2)

    def test_find_emojis_positions(self):
        """Test that positions are correct."""
        text = f"{EMOJI_STAR} is at start"

        results = find_emojis(text)

        self.assertEqual(len(results), 1)
        emoji, start, end = results[0]
        self.assertEqual(start, 0)


class TestEmojiPattern(unittest.TestCase):
    """Test the emoji regex pattern."""

    def test_pattern_matches_common_emojis(self):
        """Test that pattern matches common emojis."""
        common_emojis = [EMOJI_LOCK, EMOJI_SHIELD, EMOJI_KEY, EMOJI_WARNING,
                         EMOJI_CHECK, EMOJI_FOLDER, EMOJI_GEAR, EMOJI_STAR]

        for emoji in common_emojis:
            matches = list(EmojiScanner.EMOJI_PATTERN.finditer(emoji))
            self.assertGreater(
                len(matches), 0,
                f"Pattern should match {repr(emoji)}"
            )

    def test_pattern_no_false_positives(self):
        """Test that pattern doesn't match regular text."""
        text = "Hello World 123 abc !@#"

        matches = list(EmojiScanner.EMOJI_PATTERN.finditer(text))

        self.assertEqual(len(matches), 0)


class TestShouldScan(unittest.TestCase):
    """Test file extension filtering."""

    def test_should_scan_md(self):
        """Test markdown files are scanned."""
        scanner = EmojiScanner()
        self.assertTrue(scanner._should_scan(Path("test.md"), ["md"]))
        self.assertTrue(scanner._should_scan(Path("test.MD"), ["md"]))

    def test_should_scan_multiple_extensions(self):
        """Test multiple extensions."""
        scanner = EmojiScanner()
        extensions = ["md", "mdx", "tsx"]

        self.assertTrue(scanner._should_scan(Path("test.md"), extensions))
        self.assertTrue(scanner._should_scan(Path("test.mdx"), extensions))
        self.assertTrue(scanner._should_scan(Path("test.tsx"), extensions))
        self.assertFalse(scanner._should_scan(Path("test.py"), extensions))

    def test_should_scan_case_insensitive(self):
        """Test case-insensitive matching."""
        scanner = EmojiScanner()

        self.assertTrue(scanner._should_scan(Path("TEST.MD"), ["md"]))
        self.assertTrue(scanner._should_scan(Path("test.Md"), ["md"]))


class TestIntegration(unittest.TestCase):
    """Integration tests for full workflows."""

    def setUp(self):
        """Create temp directory with test files."""
        self.temp_dir = tempfile.mkdtemp()
        self.scanner = EmojiScanner()

        # Create test project structure
        (Path(self.temp_dir) / "README.md").write_text(f"""
# My Project

## Features
- {EMOJI_LOCK} Security: Built-in protection
- {EMOJI_FOLDER} Files: Easy file management
- {EMOJI_GEAR} Settings: Configurable

## {EMOJI_ROCKET} Installation
Run the following command...
""")

        docs_dir = Path(self.temp_dir) / "docs"
        docs_dir.mkdir()
        (docs_dir / "guide.md").write_text(f"""
# User Guide

## {EMOJI_WARNING} Warning
Be careful with these settings.
""")

    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.temp_dir)

    def test_full_scan_workflow(self):
        """Test complete scan workflow."""
        report = self.scanner.scan(
            str(self.temp_dir),
            extensions=["md"],
            recursive=True
        )

        self.assertEqual(report["files_scanned"], 2)
        self.assertGreaterEqual(report["emojis_found"], 5)  # 4 in README + 1 in guide
        self.assertGreaterEqual(report["unique_emojis"], 4)  # lock, folder, gear, rocket, warning

    def test_scan_and_convert_workflow(self):
        """Test scan followed by convert."""
        # Scan
        report = self.scanner.scan(str(self.temp_dir), extensions=["md"])

        # Convert dry-run
        dry_result = self.scanner.convert(report, "./icons", dry_run=True)

        self.assertGreater(dry_result["replacements_made"], 0)

        # Convert apply
        apply_result = self.scanner.convert(report, "./icons", dry_run=False)

        self.assertGreater(apply_result["replacements_made"], 0)

        # Verify files changed
        readme = (Path(self.temp_dir) / "README.md").read_text()
        self.assertNotIn(EMOJI_LOCK, readme)  # Should not have lock emoji anymore


if __name__ == "__main__":
    unittest.main(verbosity=2)
