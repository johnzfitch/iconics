"""
Unit tests for iconics_provision.py

Tests the IconicsProvisioner class for provisioning icons to projects,
manifest management, and framework import generation.
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

from iconics_provision import IconicsProvisioner, load_catalog


class TestIconicsProvisioner(unittest.TestCase):
    """Test IconicsProvisioner class."""

    @classmethod
    def setUpClass(cls):
        """Create temporary directories and mock data."""
        cls.temp_dir = tempfile.mkdtemp()
        cls.source_dir = Path(cls.temp_dir) / "source"
        cls.dest_dir = Path(cls.temp_dir) / "dest"

        cls.source_dir.mkdir()
        cls.dest_dir.mkdir()

        # Create mock icon files
        cls.mock_icons = ["lock-32x32", "shield-32x32", "key-32x32", "folder-32x32"]
        for icon_id in cls.mock_icons:
            (cls.source_dir / f"{icon_id}.png").write_bytes(b"fake png data")

        # Create mock catalog
        cls.mock_catalog = {
            "version": "1.0",
            "icons": [
                {
                    "id": "lock-32x32",
                    "semanticName": "lock-32x32",
                    "tags": ["lock", "security", "protection"],
                    "category": "security"
                },
                {
                    "id": "shield-32x32",
                    "semanticName": "shield-32x32",
                    "tags": ["shield", "security", "guard"],
                    "category": "security"
                },
                {
                    "id": "key-32x32",
                    "semanticName": "key-32x32",
                    "tags": ["key", "authentication", "access"],
                    "category": "security"
                },
                {
                    "id": "folder-32x32",
                    "semanticName": "folder-32x32",
                    "tags": ["folder", "files", "directory"],
                    "category": "files"
                }
            ]
        }

        # Write catalog file
        cls.catalog_file = Path(cls.temp_dir) / "catalog.json"
        with open(cls.catalog_file, 'w') as f:
            json.dump(cls.mock_catalog, f)

    @classmethod
    def tearDownClass(cls):
        """Clean up temporary directories."""
        shutil.rmtree(cls.temp_dir)

    def setUp(self):
        """Create fresh provisioner and destination for each test."""
        self.provisioner = IconicsProvisioner(
            str(self.source_dir),
            self.mock_catalog
        )
        # Clear destination directory
        if self.dest_dir.exists():
            shutil.rmtree(self.dest_dir)
        self.dest_dir.mkdir()

    def test_init(self):
        """Test provisioner initialization."""
        self.assertEqual(self.provisioner.source, self.source_dir)
        self.assertEqual(len(self.provisioner._icon_by_id), 4)
        self.assertIn("lock-32x32", self.provisioner._icon_by_id)

    def test_provision_single_icon(self):
        """Test provisioning a single icon."""
        result = self.provisioner.provision(
            ["lock-32x32"],
            str(self.dest_dir),
            update_manifest=False
        )

        self.assertEqual(len(result["copied"]), 1)
        self.assertIn("lock-32x32.png", result["copied"])
        self.assertEqual(len(result["skipped"]), 0)
        self.assertEqual(len(result["missing"]), 0)

        # Verify file exists
        self.assertTrue((self.dest_dir / "lock-32x32.png").exists())

    def test_provision_multiple_icons(self):
        """Test provisioning multiple icons."""
        result = self.provisioner.provision(
            ["lock-32x32", "shield-32x32", "key-32x32"],
            str(self.dest_dir),
            update_manifest=False
        )

        self.assertEqual(len(result["copied"]), 3)
        self.assertEqual(len(result["skipped"]), 0)
        self.assertEqual(len(result["missing"]), 0)

    def test_provision_skips_existing(self):
        """Test that existing icons are skipped."""
        # First provision
        self.provisioner.provision(["lock-32x32"], str(self.dest_dir), update_manifest=False)

        # Second provision should skip
        result = self.provisioner.provision(
            ["lock-32x32", "shield-32x32"],
            str(self.dest_dir),
            update_manifest=False
        )

        self.assertEqual(len(result["copied"]), 1)  # Only shield
        self.assertEqual(len(result["skipped"]), 1)  # lock was skipped
        self.assertIn("lock-32x32.png", result["skipped"])

    def test_provision_missing_icon(self):
        """Test handling of missing icons."""
        result = self.provisioner.provision(
            ["nonexistent-icon"],
            str(self.dest_dir),
            update_manifest=False
        )

        self.assertEqual(len(result["copied"]), 0)
        self.assertEqual(len(result["missing"]), 1)
        self.assertIn("nonexistent-icon.png", result["missing"])

    def test_provision_with_subdir(self):
        """Test provisioning to a subdirectory."""
        result = self.provisioner.provision(
            ["lock-32x32"],
            str(self.dest_dir),
            icon_subdir=".github/assets/icons",
            update_manifest=False
        )

        self.assertEqual(len(result["copied"]), 1)
        # Verify file in subdirectory
        self.assertTrue((self.dest_dir / ".github/assets/icons/lock-32x32.png").exists())

    def test_provision_with_manifest(self):
        """Test that manifest is created."""
        result = self.provisioner.provision(
            ["lock-32x32", "shield-32x32"],
            str(self.dest_dir),
            update_manifest=True
        )

        self.assertIsNotNone(result["manifest_path"])
        manifest_path = Path(result["manifest_path"])
        self.assertTrue(manifest_path.exists())

        # Check manifest content
        with open(manifest_path) as f:
            manifest = json.load(f)

        self.assertIn("version", manifest)
        self.assertIn("icons", manifest)
        self.assertEqual(len(manifest["icons"]), 2)
        self.assertIn("lock-32x32", manifest["icons"])
        self.assertIn("shield-32x32", manifest["icons"])

    def test_manifest_accumulates(self):
        """Test that manifest accumulates icons over multiple provisions."""
        # First provision
        self.provisioner.provision(["lock-32x32"], str(self.dest_dir))

        # Second provision
        self.provisioner.provision(["shield-32x32"], str(self.dest_dir))

        # Check manifest
        manifest_path = self.dest_dir / "iconics-manifest.json"
        with open(manifest_path) as f:
            manifest = json.load(f)

        self.assertEqual(len(manifest["icons"]), 2)
        self.assertIn("lock-32x32", manifest["icons"])
        self.assertIn("shield-32x32", manifest["icons"])

    def test_provision_from_manifest(self):
        """Test provisioning from an existing manifest."""
        # Create a manifest
        manifest = {
            "version": "1.0",
            "icons": ["lock-32x32", "shield-32x32"],
            "icon_subdir": ""
        }
        manifest_path = Path(self.temp_dir) / "source-manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f)

        # Provision from manifest
        result = self.provisioner.provision_from_manifest(
            str(manifest_path),
            str(self.dest_dir)
        )

        self.assertEqual(len(result["copied"]), 2)

    def test_provision_from_manifest_not_found(self):
        """Test error when manifest not found."""
        with self.assertRaises(FileNotFoundError):
            self.provisioner.provision_from_manifest(
                "/nonexistent/manifest.json",
                str(self.dest_dir)
            )

    def test_catalog_search(self):
        """Test catalog-based search fallback."""
        results = self.provisioner._catalog_search("security lock", k=2)

        self.assertEqual(len(results), 2)
        # lock-32x32 should be first (matches both terms)
        self.assertEqual(results[0], "lock-32x32")

    def test_catalog_search_no_results(self):
        """Test catalog search with no matches."""
        results = self.provisioner._catalog_search("nonexistent concept", k=2)

        self.assertEqual(len(results), 0)


class TestProvisionFromQuery(unittest.TestCase):
    """Test provision_from_query method."""

    @classmethod
    def setUpClass(cls):
        """Create temporary directories."""
        cls.temp_dir = tempfile.mkdtemp()
        cls.source_dir = Path(cls.temp_dir) / "source"
        cls.dest_dir = Path(cls.temp_dir) / "dest"

        cls.source_dir.mkdir()
        cls.dest_dir.mkdir()

        # Create mock icons
        for icon_id in ["lock-32x32", "shield-32x32", "folder-32x32"]:
            (cls.source_dir / f"{icon_id}.png").write_bytes(b"fake png")

        cls.mock_catalog = {
            "icons": [
                {"id": "lock-32x32", "semanticName": "lock", "tags": ["lock", "security"]},
                {"id": "shield-32x32", "semanticName": "shield", "tags": ["shield", "protection"]},
                {"id": "folder-32x32", "semanticName": "folder", "tags": ["folder", "files"]}
            ]
        }

    @classmethod
    def tearDownClass(cls):
        """Clean up."""
        shutil.rmtree(cls.temp_dir)

    def setUp(self):
        """Reset destination directory."""
        if self.dest_dir.exists():
            shutil.rmtree(self.dest_dir)
        self.dest_dir.mkdir()

        self.provisioner = IconicsProvisioner(
            str(self.source_dir),
            self.mock_catalog
        )

    def test_provision_from_query_catalog_fallback(self):
        """Test query-based provisioning with catalog fallback."""
        result = self.provisioner.provision_from_query(
            queries=["security", "files"],
            dest=str(self.dest_dir),
            k=1,
            retriever=None
        )

        # Should have query_results
        self.assertIn("query_results", result)
        self.assertIn("security", result["query_results"])
        self.assertIn("files", result["query_results"])

        # Should have provisioned icons
        self.assertGreater(len(result["copied"]), 0)

    def test_provision_from_query_with_retriever(self):
        """Test query-based provisioning with mock retriever."""
        # Create mock retriever
        mock_retriever = MagicMock()
        mock_result = MagicMock()
        mock_result.icon_id = "lock-32x32"
        mock_retriever.retrieve.return_value = [mock_result]

        result = self.provisioner.provision_from_query(
            queries=["security"],
            dest=str(self.dest_dir),
            k=1,
            retriever=mock_retriever
        )

        self.assertIn("lock-32x32", result["query_results"]["security"])


class TestGenerateImports(unittest.TestCase):
    """Test generate_imports method."""

    @classmethod
    def setUpClass(cls):
        """Create temporary directories."""
        cls.temp_dir = tempfile.mkdtemp()
        cls.source_dir = Path(cls.temp_dir) / "source"
        cls.source_dir.mkdir()

        cls.mock_catalog = {"icons": []}
        cls.provisioner = IconicsProvisioner(str(cls.source_dir), cls.mock_catalog)

        # Create a manifest
        cls.manifest = {
            "version": "1.0",
            "icons": ["lock-32x32", "shield-32x32"],
            "icon_subdir": "icons"
        }
        cls.manifest_path = Path(cls.temp_dir) / "manifest.json"
        with open(cls.manifest_path, 'w') as f:
            json.dump(cls.manifest, f)

    @classmethod
    def tearDownClass(cls):
        """Clean up."""
        shutil.rmtree(cls.temp_dir)

    def test_generate_react_imports(self):
        """Test React import generation."""
        output_path = Path(self.temp_dir) / "Icons.tsx"

        content = self.provisioner.generate_imports(
            str(self.manifest_path),
            "react",
            str(output_path)
        )

        self.assertTrue(output_path.exists())
        self.assertIn("import React from 'react'", content)
        self.assertIn("Lock32x32Icon", content)
        self.assertIn("Shield32x32Icon", content)
        self.assertIn("export const Icons", content)

    def test_generate_vue_imports(self):
        """Test Vue import generation."""
        output_path = Path(self.temp_dir) / "icons.js"

        content = self.provisioner.generate_imports(
            str(self.manifest_path),
            "vue",
            str(output_path)
        )

        self.assertTrue(output_path.exists())
        self.assertIn("export const icons", content)
        self.assertIn("lock32x32:", content)
        self.assertIn("export default icons", content)

    def test_generate_css_imports(self):
        """Test CSS import generation."""
        output_path = Path(self.temp_dir) / "icons.css"

        content = self.provisioner.generate_imports(
            str(self.manifest_path),
            "css",
            str(output_path)
        )

        self.assertTrue(output_path.exists())
        self.assertIn(".icon-lock", content)
        self.assertIn("background-image:", content)

    def test_generate_typescript_imports(self):
        """Test TypeScript import generation."""
        output_path = Path(self.temp_dir) / "icons.ts"

        content = self.provisioner.generate_imports(
            str(self.manifest_path),
            "typescript",
            str(output_path)
        )

        self.assertTrue(output_path.exists())
        self.assertIn("export const ICONS", content)
        self.assertIn("as const", content)
        self.assertIn("export type IconKey", content)
        self.assertIn("export function getIconPath", content)

    def test_generate_imports_manifest_not_found(self):
        """Test error when manifest not found."""
        with self.assertRaises(FileNotFoundError):
            self.provisioner.generate_imports(
                "/nonexistent/manifest.json",
                "react",
                "/tmp/output.tsx"
            )


class TestLoadCatalog(unittest.TestCase):
    """Test load_catalog function."""

    def test_load_catalog(self):
        """Test loading catalog from file."""
        temp_dir = tempfile.mkdtemp()
        try:
            catalog = {"version": "1.0", "icons": [{"id": "test"}]}
            catalog_path = Path(temp_dir) / "catalog.json"
            with open(catalog_path, 'w') as f:
                json.dump(catalog, f)

            loaded = load_catalog(str(catalog_path))

            self.assertEqual(loaded["version"], "1.0")
            self.assertEqual(len(loaded["icons"]), 1)
        finally:
            shutil.rmtree(temp_dir)

    def test_load_catalog_not_found(self):
        """Test error when catalog not found."""
        with self.assertRaises(FileNotFoundError):
            load_catalog("/nonexistent/catalog.json")


class TestHelperMethods(unittest.TestCase):
    """Test static helper methods."""

    def test_to_component_name(self):
        """Test component name generation."""
        self.assertEqual(
            IconicsProvisioner._to_component_name("lock-32x32"),
            "Lock32x32Icon"
        )
        self.assertEqual(
            IconicsProvisioner._to_component_name("shield"),
            "ShieldIcon"
        )
        self.assertEqual(
            IconicsProvisioner._to_component_name("folder-open-24x24"),
            "FolderOpen24x24Icon"
        )

    def test_to_key_name(self):
        """Test key name generation."""
        self.assertEqual(
            IconicsProvisioner._to_key_name("lock-32x32"),
            "lock32x32"
        )
        self.assertEqual(
            IconicsProvisioner._to_key_name("shield"),
            "shield"
        )
        self.assertEqual(
            IconicsProvisioner._to_key_name("folder-open-24x24"),
            "folderOpen24x24"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
