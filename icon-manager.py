#!/usr/bin/env python3
"""
Iconics Manager - Semantic icon library management system
Manages the Iconics icon library for use across GitHub projects

Repository: https://github.com/johnzfitch/iconics
"""

import json
import os
import shutil
import argparse
import csv
from pathlib import Path
from typing import List, Dict, Optional

ICON_DIR = Path("/home/zack/dev/iconics")
CATALOG_FILE = ICON_DIR / "icon-catalog.json"
RAW_DIR = ICON_DIR / "raw"
CATALOG_DIR = ICON_DIR / "catalog"

class IconManager:
    def __init__(self):
        self.catalog = self.load_catalog()

    def load_catalog(self) -> Dict:
        """Load icon catalog from JSON file"""
        if CATALOG_FILE.exists():
            with open(CATALOG_FILE, 'r') as f:
                return json.load(f)
        return {
            "version": "1.0",
            "icons": [],
            "categories": ["files", "network", "security", "tools", "ui", "emoji", "development"]
        }

    def save_catalog(self):
        """Save catalog to JSON file"""
        with open(CATALOG_FILE, 'w') as f:
            json.dump(self.catalog, f, indent=2)
        print(f"✓ Catalog saved to {CATALOG_FILE}")

    def find_icon_by_id(self, icon_id: str) -> Optional[Dict]:
        """Find icon in catalog by numeric ID"""
        for icon in self.catalog["icons"]:
            if icon["id"] == icon_id:
                return icon
        return None

    def find_icons_by_tag(self, tag: str) -> List[Dict]:
        """Find all icons matching a tag"""
        tag_lower = tag.lower()
        return [icon for icon in self.catalog["icons"]
                if tag_lower in [t.lower() for t in icon.get("tags", [])]]

    def find_icons_by_semantic(self, name: str) -> List[Dict]:
        """Find icons by semantic name"""
        name_lower = name.lower()
        return [icon for icon in self.catalog["icons"]
                if name_lower in icon.get("semanticName", "").lower()]

    def search(self, query: str) -> List[Dict]:
        """Search icons by tag or semantic name"""
        results = []
        results.extend(self.find_icons_by_tag(query))
        results.extend(self.find_icons_by_semantic(query))
        # Remove duplicates
        seen = set()
        unique_results = []
        for icon in results:
            if icon["id"] not in seen:
                seen.add(icon["id"])
                unique_results.append(icon)
        return unique_results

    def add_icon(self, icon_id: str, semantic_name: str, tags: List[str],
                 category: str, description: str = ""):
        """Add or update icon in catalog"""
        existing = self.find_icon_by_id(icon_id)

        icon_data = {
            "id": icon_id,
            "filename": f"raw/{icon_id}.png",
            "semanticName": semantic_name,
            "tags": tags,
            "category": category,
            "description": description,
            "usedIn": existing.get("usedIn", []) if existing else []
        }

        if existing:
            # Update existing
            idx = self.catalog["icons"].index(existing)
            self.catalog["icons"][idx] = icon_data
            print(f"✓ Updated icon {icon_id} ({semantic_name})")
        else:
            # Add new
            self.catalog["icons"].append(icon_data)
            print(f"✓ Added icon {icon_id} ({semantic_name})")

        # Create symlink in catalog directory
        self.create_symlink(icon_id, semantic_name, category)
        self.save_catalog()

    def create_symlink(self, icon_id: str, semantic_name: str, category: str):
        """Create symlink in catalog/category/ directory"""
        category_dir = CATALOG_DIR / category
        category_dir.mkdir(parents=True, exist_ok=True)

        source = RAW_DIR / f"{icon_id}.png"
        target = category_dir / f"{semantic_name}.png"

        if target.exists() or target.is_symlink():
            target.unlink()

        if source.exists():
            target.symlink_to(f"../../raw/{icon_id}.png")
            print(f"  → Created symlink: catalog/{category}/{semantic_name}.png")

    def list_category(self, category: str):
        """List all icons in a category"""
        icons = [icon for icon in self.catalog["icons"]
                 if icon.get("category") == category]

        if not icons:
            print(f"No icons found in category '{category}'")
            return

        print(f"\n{category.upper()} ({len(icons)} icons):")
        print("-" * 60)
        for icon in sorted(icons, key=lambda x: x["semanticName"]):
            tags_str = ", ".join(icon.get("tags", []))
            print(f"  {icon['semanticName']:20} (#{icon['id']})  Tags: {tags_str}")

    def export_to_project(self, project_path: str, icon_names: List[str]):
        """Export icons to a project's .github/assets/icons/ directory"""
        project = Path(project_path)
        icon_dir = project / ".github" / "assets" / "icons"
        icon_dir.mkdir(parents=True, exist_ok=True)

        exported = []
        for name in icon_names:
            # Find icon by semantic name
            icons = self.find_icons_by_semantic(name)
            if not icons:
                print(f"✗ Icon '{name}' not found in catalog")
                continue

            icon = icons[0]  # Take first match
            source = ICON_DIR / icon["filename"]
            target = icon_dir / f"{icon['semanticName']}.png"

            if source.exists():
                shutil.copy2(source, target)
                exported.append(icon['semanticName'])

                # Track usage
                project_name = project.name
                if project_name not in icon.get("usedIn", []):
                    icon.setdefault("usedIn", []).append(project_name)

                print(f"✓ Exported {icon['semanticName']}.png")

        if exported:
            self.save_catalog()
            print(f"\n✓ Exported {len(exported)} icons to {icon_dir}")

    def stats(self):
        """Show catalog statistics"""
        total = len(self.catalog["icons"])
        by_category = {}
        for icon in self.catalog["icons"]:
            cat = icon.get("category", "uncategorized")
            by_category[cat] = by_category.get(cat, 0) + 1

        print("\n=== Icon Library Statistics ===")
        print(f"Total cataloged icons: {total}")
        print(f"\nBy category:")
        for cat, count in sorted(by_category.items()):
            print(f"  {cat:15} {count:3} icons")

        # Most used icons
        used_icons = [(icon, len(icon.get("usedIn", [])))
                      for icon in self.catalog["icons"]
                      if icon.get("usedIn")]
        if used_icons:
            print(f"\nMost used icons:")
            for icon, count in sorted(used_icons, key=lambda x: x[1], reverse=True)[:5]:
                projects = ", ".join(icon["usedIn"])
                print(f"  {icon['semanticName']:15} used in {count} project(s): {projects}")

    def bulk_import(self, csv_file: str):
        """Import icons from CSV file

        CSV Format: id,semantic,tags,category,description
        Example: Lock,lock,"security,padlock,locked",security,Padlock icon for security

        Args:
            csv_file: Path to CSV file
        """
        csv_path = Path(csv_file)
        if not csv_path.exists():
            print(f"✗ Error: CSV file not found: {csv_file}")
            return

        success_count = 0
        error_count = 0

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            # Validate headers
            required_headers = {'id', 'semantic', 'tags', 'category'}
            if not required_headers.issubset(reader.fieldnames):
                print(f"✗ Error: CSV must have headers: id, semantic, tags, category, description")
                print(f"  Found: {', '.join(reader.fieldnames)}")
                return

            print(f"Importing icons from {csv_file}...")

            for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                try:
                    # Parse tags (handle comma-separated or space-separated)
                    tags_str = row['tags'].strip()
                    if ',' in tags_str:
                        tags = [t.strip() for t in tags_str.split(',') if t.strip()]
                    else:
                        tags = [t.strip() for t in tags_str.split() if t.strip()]

                    # Validate category
                    category = row['category'].strip()
                    if category not in self.catalog["categories"]:
                        print(f"  ✗ Row {row_num}: Invalid category '{category}', skipping")
                        error_count += 1
                        continue

                    # Add icon
                    icon_id = row['id'].strip()
                    semantic = row['semantic'].strip()
                    description = row.get('description', '').strip()

                    if not icon_id or not semantic:
                        print(f"  ✗ Row {row_num}: Missing id or semantic name, skipping")
                        error_count += 1
                        continue

                    # Check if already exists
                    existing = self.find_icon_by_id(icon_id)
                    if existing:
                        print(f"  ⚠ Row {row_num}: Icon '{icon_id}' already exists, skipping")
                        continue

                    self.add_icon(icon_id, semantic, tags, category, description)
                    success_count += 1

                except Exception as e:
                    print(f"  ✗ Row {row_num}: Error processing row: {e}")
                    error_count += 1

        # Final summary (catalog already saved by add_icon calls)
        print(f"\n=== Import Summary ===")
        print(f"✓ Successfully imported: {success_count} icons")
        if error_count > 0:
            print(f"✗ Errors/Skipped: {error_count}")
        print(f"Total cataloged icons: {len(self.catalog['icons'])}")

    def suggest_from_filename(self, filename: str) -> dict:
        """Generate semantic name and tags from filename

        Args:
            filename: Icon filename (without extension)

        Returns:
            dict with suggested semantic, tags, category
        """
        import re

        # Clean filename: lowercase, replace separators with spaces
        name = filename.replace('_', ' ').replace('-', ' ')
        name = re.sub(r'\s+', ' ', name).strip().lower()

        # Generate semantic name (lowercase with hyphens)
        semantic = name.replace(' ', '-')

        # Generate tags from words
        words = name.split()
        tags = list(set(words))  # Remove duplicates

        # Guess category based on common keywords
        category_keywords = {
            'files': ['file', 'document', 'folder', 'pdf', 'doc', 'text', 'page', 'book', 'paper'],
            'network': ['network', 'wifi', 'cloud', 'internet', 'connection', 'globe', 'web', 'server', 'router'],
            'security': ['lock', 'key', 'shield', 'security', 'secure', 'certificate', 'password', 'protection'],
            'tools': ['tool', 'wrench', 'gear', 'settings', 'config', 'hammer', 'screwdriver', 'toolbox'],
            'ui': ['button', 'icon', 'arrow', 'close', 'open', 'menu', 'navigation', 'pointer', 'cursor'],
            'development': ['code', 'bug', 'database', 'api', 'console', 'terminal', 'git', 'debug', 'test'],
            'emoji': ['smile', 'happy', 'sad', 'face', 'emotion', 'laugh', 'cry']
        }

        # Find matching category
        category = 'ui'  # Default
        max_matches = 0
        for cat, keywords in category_keywords.items():
            matches = sum(1 for word in words if any(kw in word for kw in keywords))
            if matches > max_matches:
                max_matches = matches
                category = cat

        return {
            'semantic': semantic,
            'tags': tags,
            'category': category
        }

    def generate_csv_from_filenames(self, output_file: str, limit: int = None):
        """Generate CSV file with suggestions from icon filenames

        Args:
            output_file: Path to output CSV file
            limit: Maximum number of icons to process (None = all)
        """
        print(f"Scanning {RAW_DIR} for uncataloged icons...")

        # Get all PNG files in raw directory
        all_icons = [f.stem for f in RAW_DIR.glob("*.png")]

        # Filter out already cataloged icons
        cataloged_ids = {icon['id'] for icon in self.catalog['icons']}
        uncataloged = [icon for icon in all_icons if icon not in cataloged_ids]

        if not uncataloged:
            print("✓ All icons are already cataloged!")
            return

        print(f"Found {len(uncataloged)} uncataloged icons")

        if limit:
            uncataloged = uncataloged[:limit]
            print(f"Limiting to {limit} icons for CSV generation")

        # Generate suggestions
        suggestions = []
        for icon_id in uncataloged:
            suggestion = self.suggest_from_filename(icon_id)
            suggestions.append({
                'id': icon_id,
                'semantic': suggestion['semantic'],
                'tags': ','.join(suggestion['tags'][:5]),  # Limit to 5 tags
                'category': suggestion['category'],
                'description': f"{suggestion['semantic'].replace('-', ' ').title()} icon"
            })

        # Write to CSV
        output_path = Path(output_file)
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['id', 'semantic', 'tags', 'category', 'description']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(suggestions)

        print(f"\n✓ Generated {len(suggestions)} icon suggestions")
        print(f"✓ Saved to: {output_path}")
        print(f"\nNext steps:")
        print(f"1. Review and edit {output_path} in a spreadsheet")
        print(f"2. Improve tags and descriptions as needed")
        print(f"3. Import with: python3 icon-manager.py import-csv {output_path}")

    def create_template(self, template_name: str, tags: List[str], category: str):
        """Create a reusable template for icon families

        Args:
            template_name: Name of the template (e.g., 'arrow', 'social-media')
            tags: Common tags to apply
            category: Category for this icon family
        """
        # Load or create templates file
        templates_file = ICON_DIR / "icon-templates.json"
        if templates_file.exists():
            with open(templates_file, 'r') as f:
                templates = json.load(f)
        else:
            templates = {}

        templates[template_name] = {
            'tags': tags,
            'category': category
        }

        with open(templates_file, 'w') as f:
            json.dump(templates, f, indent=2)

        print(f"✓ Created template '{template_name}'")
        print(f"  Category: {category}")
        print(f"  Tags: {', '.join(tags)}")

    def apply_template(self, template_name: str, icon_specs: List[dict]):
        """Apply a template to multiple icons

        Args:
            template_name: Name of the template to apply
            icon_specs: List of dicts with 'id', 'semantic', and optional extra 'tags'
        """
        templates_file = ICON_DIR / "icon-templates.json"
        if not templates_file.exists():
            print(f"✗ No templates found. Create one with 'create-template' first")
            return

        with open(templates_file, 'r') as f:
            templates = json.load(f)

        if template_name not in templates:
            print(f"✗ Template '{template_name}' not found")
            print(f"Available templates: {', '.join(templates.keys())}")
            return

        template = templates[template_name]
        success_count = 0

        print(f"Applying template '{template_name}' to {len(icon_specs)} icons...")

        for spec in icon_specs:
            icon_id = spec['id']
            semantic = spec['semantic']
            extra_tags = spec.get('extra_tags', [])
            description = spec.get('description', f"{semantic.replace('-', ' ').title()} icon")

            # Combine template tags with any extra tags
            all_tags = template['tags'] + extra_tags

            # Check if already exists
            if self.find_icon_by_id(icon_id):
                print(f"  ⚠ '{icon_id}' already exists, skipping")
                continue

            self.add_icon(icon_id, semantic, all_tags, template['category'], description)
            success_count += 1

        print(f"\n✓ Applied template to {success_count} icons")

def main():
    parser = argparse.ArgumentParser(description="Icon library management system")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Add command
    add_parser = subparsers.add_parser("add", help="Add icon to catalog")
    add_parser.add_argument("icon_id", help="Numeric icon ID (e.g., 100)")
    add_parser.add_argument("semantic_name", help="Semantic name (e.g., document)")
    add_parser.add_argument("--tags", nargs="+", required=True, help="Tags (e.g., file text document)")
    add_parser.add_argument("--category", required=True, choices=["files", "network", "security", "tools", "ui", "emoji", "development"])
    add_parser.add_argument("--description", default="", help="Description")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search icons")
    search_parser.add_argument("query", help="Search query (tag or semantic name)")

    # List command
    list_parser = subparsers.add_parser("list", help="List icons in category")
    list_parser.add_argument("category", choices=["files", "network", "security", "tools", "ui", "emoji", "development"])

    # Export command
    export_parser = subparsers.add_parser("export", help="Export icons to project")
    export_parser.add_argument("project_path", help="Path to project directory")
    export_parser.add_argument("icons", nargs="+", help="Icon semantic names to export")

    # Stats command
    subparsers.add_parser("stats", help="Show catalog statistics")

    # Import CSV command
    import_parser = subparsers.add_parser("import-csv", help="Bulk import icons from CSV file")
    import_parser.add_argument("csv_file", help="Path to CSV file (id,semantic,tags,category,description)")

    # Generate CSV command
    generate_parser = subparsers.add_parser("generate-csv", help="Auto-generate CSV from uncataloged icon filenames")
    generate_parser.add_argument("output_file", help="Path to output CSV file")
    generate_parser.add_argument("--limit", type=int, help="Maximum number of icons to process (default: all)")

    # Template commands
    template_create_parser = subparsers.add_parser("create-template", help="Create reusable template for icon families")
    template_create_parser.add_argument("name", help="Template name (e.g., arrow, social)")
    template_create_parser.add_argument("--tags", nargs="+", required=True, help="Common tags for this template")
    template_create_parser.add_argument("--category", required=True, choices=["files", "network", "security", "tools", "ui", "emoji", "development"])

    template_apply_parser = subparsers.add_parser("apply-template", help="Apply template to multiple icons via CSV")
    template_apply_parser.add_argument("template", help="Template name to apply")
    template_apply_parser.add_argument("csv_file", help="CSV file with id,semantic,extra_tags,description columns")

    args = parser.parse_args()
    manager = IconManager()

    if args.command == "add":
        manager.add_icon(args.icon_id, args.semantic_name, args.tags,
                        args.category, args.description)

    elif args.command == "search":
        results = manager.search(args.query)
        if results:
            print(f"\nFound {len(results)} icon(s) matching '{args.query}':")
            for icon in results:
                tags = ", ".join(icon.get("tags", []))
                print(f"  {icon['semanticName']:20} #{icon['id']:4}  [{icon['category']}]  Tags: {tags}")
        else:
            print(f"No icons found matching '{args.query}'")

    elif args.command == "list":
        manager.list_category(args.category)

    elif args.command == "export":
        manager.export_to_project(args.project_path, args.icons)

    elif args.command == "stats":
        manager.stats()

    elif args.command == "import-csv":
        manager.bulk_import(args.csv_file)

    elif args.command == "generate-csv":
        manager.generate_csv_from_filenames(args.output_file, args.limit)

    elif args.command == "create-template":
        manager.create_template(args.name, args.tags, args.category)

    elif args.command == "apply-template":
        # Load CSV and apply template
        icon_specs = []
        with open(args.csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                spec = {
                    'id': row['id'],
                    'semantic': row['semantic'],
                }
                if 'extra_tags' in row and row['extra_tags']:
                    spec['extra_tags'] = [t.strip() for t in row['extra_tags'].split(',')]
                else:
                    spec['extra_tags'] = []
                if 'description' in row:
                    spec['description'] = row['description']
                icon_specs.append(spec)
        manager.apply_template(args.template, icon_specs)

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
