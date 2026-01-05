#!/usr/bin/env python3
"""
Windows 2000 ICO → PNG Batch Converter
Converts Windows 2000 SP4 ICO files to PNG with semantic naming

Based on: /home/zack/dev/iconics/convert-ico-to-png.sh
"""

import argparse
import subprocess
import re
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

# Source file → semantic domain mapping
SOURCE_SEMANTIC_MAP = {
    'shell32.dll': 'files',
    'moricons.dll': 'ui',
    'netshell.dll': 'network',
    'cryptui.dll': 'security',
    'compstui.dll': 'ui',
    'progman.exe': 'files',
    'pifmgr.dll': 'files',
    'explorer.exe': 'files',
    'cmd.exe': 'development',
    'cscript.exe': 'development',
    'wscript.exe': 'development',
    'notepad.exe': 'tools',
    'mspaint.exe': 'tools',
    'calc.exe': 'tools',
    'inetcpl.cpl': 'network',
    'msoeres.dll': 'network',
    'conf.exe': 'network',
    'rasphone.exe': 'network',
    'rasdlg.dll': 'network',
    'certmgr.dll': 'security',
    'wsecedit.dll': 'security',
    'setupapi.dll': 'tools',
    'cleanmgr.exe': 'tools',
    'mmc.exe': 'tools',
    'eventvwr.exe': 'tools',
    'devmgr.dll': 'tools',
    'taskmgr.exe': 'tools',
    'freecell.exe': 'emoji',
    'solitaire.exe': 'emoji',
}

def parse_filename(filename: str) -> Tuple[str, str, str]:
    """
    Parse Windows ICO filename format: {SOURCE}_{GROUPID}_{RESOURCEID}.ico

    Returns:
        (source_file, group_id, resource_id)

    Examples:
        "shell32.dll_14_5.ico" → ("shell32.dll", "14", "5")
        "explorer.exe_14_104.ico" → ("explorer.exe", "14", "104")
    """
    # Remove .ico extension
    base = filename.replace('.ico', '')

    # Pattern: {source}_{group}_{resource}
    match = re.match(r'^(.+?)_(\d+)_(.+)$', base)
    if match:
        source, group, resource = match.groups()
        return (source, group, resource)

    # Fallback: treat entire name as source
    return (base, '0', '0')

def get_ico_info(ico_path: Path) -> List[Dict[str, any]]:
    """
    Get information about all images in an ICO file using ImageMagick.

    Returns:
        List of dicts with keys: index, width, height, depth, size_kb
    """
    try:
        # Run: magick identify -format "%w %h %z %b\n" file.ico
        result = subprocess.run(
            ['magick', 'identify', '-format', '%w %h %z %b\n', str(ico_path)],
            capture_output=True,
            text=True,
            check=True
        )

        images = []
        for idx, line in enumerate(result.stdout.strip().split('\n')):
            if not line:
                continue

            parts = line.split()
            if len(parts) >= 4:
                width, height, depth, size = parts[0], parts[1], parts[2], parts[3]
                images.append({
                    'index': idx,
                    'width': int(width),
                    'height': int(height),
                    'depth': int(depth),
                    'size_str': size,
                    'dimensions': f"{width}x{height}"
                })

        return images

    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to identify {ico_path.name}: {e}")
        return []

def filter_preferred_variants(images: List[Dict]) -> List[Dict]:
    """
    Filter ICO images to keep only preferred variants.

    Rules:
    - Keep all requested sizes (16x16, 32x32, 48x48)
    - Prefer 8-bit over 4-bit for same size
    - Skip sizes not in requested list
    """
    # Group by dimensions
    by_dimensions = defaultdict(list)
    for img in images:
        by_dimensions[img['dimensions']].append(img)

    # For each dimension, prefer higher bit depth
    preferred = []
    for dimension, variants in by_dimensions.items():
        # Sort by depth descending (8-bit before 4-bit)
        variants_sorted = sorted(variants, key=lambda x: x['depth'], reverse=True)
        preferred.append(variants_sorted[0])  # Take highest depth

    return preferred

def convert_ico_to_png(ico_path: Path, output_dir: Path, keep_sizes: List[str]) -> List[Path]:
    """
    Convert ICO file to PNG files for each size variant.

    Args:
        ico_path: Path to source ICO file
        output_dir: Directory to write PNG files
        keep_sizes: List of sizes to keep (e.g., ['16x16', '32x32', '48x48'])

    Returns:
        List of created PNG file paths
    """
    # Parse filename
    source_file, group_id, resource_id = parse_filename(ico_path.name)

    # Get ICO info
    images = get_ico_info(ico_path)
    if not images:
        return []

    # Filter to preferred variants
    preferred = filter_preferred_variants(images)

    # Filter to requested sizes
    if keep_sizes:
        preferred = [img for img in preferred if img['dimensions'] in keep_sizes]

    created_files = []

    for img in preferred:
        # Generate semantic filename
        # Format: {source}-{resource}-win2k-{size}.png
        # Example: shell32-5-win2k-48x48.png

        # Clean source name (remove .dll, .exe, .cpl extensions)
        source_clean = re.sub(r'\.(dll|exe|cpl)$', '', source_file)

        # Generate filename
        output_filename = f"{source_clean}-{resource_id}-win2k-{img['dimensions']}.png"
        output_path = output_dir / output_filename

        # Convert using ImageMagick
        try:
            subprocess.run(
                [
                    'magick',
                    f"{str(ico_path)}[{img['index']}]",
                    '-background', 'none',
                    '-flatten',
                    str(output_path)
                ],
                capture_output=True,
                check=True
            )
            created_files.append(output_path)

        except subprocess.CalledProcessError as e:
            print(f"Warning: Failed to convert {ico_path.name}[{img['index']}]: {e}")

    return created_files

def scan_ico_files(source_dir: Path) -> List[Path]:
    """Recursively scan for all .ico files in source directory."""
    return sorted(source_dir.rglob('*.ico'))

def main():
    parser = argparse.ArgumentParser(
        description='Convert Windows 2000 ICO files to PNG with semantic naming',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert all ICO files, keeping 48x48 and 16x16
  python3 convert-win2k-icons.py \\
    --source /path/to/win2k/icons/ \\
    --output raw/win2k/ \\
    --keep-sizes 16x16,48x48

  # Convert all sizes
  python3 convert-win2k-icons.py \\
    --source /path/to/win2k/icons/ \\
    --output raw/win2k/ \\
    --keep-sizes 16x16,32x32,48x48

  # Dry run (show what would be converted)
  python3 convert-win2k-icons.py \\
    --source /path/to/win2k/icons/ \\
    --output raw/win2k/ \\
    --dry-run
        """
    )

    parser.add_argument(
        '--source',
        type=Path,
        required=True,
        help='Source directory containing Windows 2000 ICO files'
    )

    parser.add_argument(
        '--output',
        type=Path,
        required=True,
        help='Output directory for PNG files (will be created if needed)'
    )

    parser.add_argument(
        '--keep-sizes',
        type=str,
        default='16x16,32x32,48x48',
        help='Comma-separated list of sizes to keep (default: 16x16,32x32,48x48)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be converted without actually converting'
    )

    parser.add_argument(
        '--log',
        type=Path,
        help='Write conversion log to JSON file'
    )

    args = parser.parse_args()

    # Validate source directory
    if not args.source.exists():
        print(f"Error: Source directory does not exist: {args.source}")
        return 1

    # Parse keep_sizes
    keep_sizes = [s.strip() for s in args.keep_sizes.split(',')]
    print(f"Keeping sizes: {', '.join(keep_sizes)}")

    # Create output directory
    if not args.dry_run:
        args.output.mkdir(parents=True, exist_ok=True)

    # Scan for ICO files
    print(f"\nScanning {args.source} for ICO files...")
    ico_files = scan_ico_files(args.source)
    print(f"Found {len(ico_files)} ICO files")

    if args.dry_run:
        print("\n=== DRY RUN MODE (no files will be created) ===\n")

    # Conversion statistics
    total_icos = len(ico_files)
    total_pngs = 0
    failed_icos = []
    conversion_log = []

    # Convert each ICO
    for idx, ico_path in enumerate(ico_files, 1):
        print(f"[{idx}/{total_icos}] {ico_path.name}")

        if args.dry_run:
            # Just show what would be converted
            images = get_ico_info(ico_path)
            preferred = filter_preferred_variants(images)
            filtered = [img for img in preferred if img['dimensions'] in keep_sizes]

            source_file, group_id, resource_id = parse_filename(ico_path.name)
            source_clean = re.sub(r'\.(dll|exe|cpl)$', '', source_file)

            for img in filtered:
                output_filename = f"{source_clean}-{resource_id}-win2k-{img['dimensions']}.png"
                print(f"  → {output_filename} ({img['depth']}-bit)")

        else:
            # Actually convert
            created_files = convert_ico_to_png(ico_path, args.output, keep_sizes)

            if created_files:
                total_pngs += len(created_files)
                print(f"  ✓ Created {len(created_files)} PNG(s)")

                # Log conversion
                source_file, group_id, resource_id = parse_filename(ico_path.name)
                conversion_log.append({
                    'ico_file': str(ico_path.relative_to(args.source)),
                    'source_file': source_file,
                    'group_id': group_id,
                    'resource_id': resource_id,
                    'created_pngs': [str(p.name) for p in created_files]
                })
            else:
                print(f"  ✗ Failed (no images extracted)")
                failed_icos.append(str(ico_path.name))

    # Print summary
    print("\n" + "=" * 60)
    print("Conversion Summary")
    print("=" * 60)
    print(f"Total ICO files processed: {total_icos}")
    if not args.dry_run:
        print(f"Total PNG files created: {total_pngs}")
        print(f"Failed conversions: {len(failed_icos)}")

        if failed_icos:
            print("\nFailed files:")
            for failed in failed_icos[:10]:  # Show first 10
                print(f"  - {failed}")
            if len(failed_icos) > 10:
                print(f"  ... and {len(failed_icos) - 10} more")

    # Write log file
    if args.log and not args.dry_run:
        log_data = {
            'source_dir': str(args.source),
            'output_dir': str(args.output),
            'keep_sizes': keep_sizes,
            'total_icos': total_icos,
            'total_pngs': total_pngs,
            'failed_icos': failed_icos,
            'conversions': conversion_log
        }

        with open(args.log, 'w') as f:
            json.dump(log_data, f, indent=2)

        print(f"\nConversion log written to: {args.log}")

    print("\nDone!")
    return 0

if __name__ == '__main__':
    exit(main())
