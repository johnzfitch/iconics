#!/usr/bin/env python3
"""
Iconics - Unified Agentic Icon Library Executive

One CLI, one command structure, one vision.
Drop icons → auto-catalog → auto-embed.
Agent-friendly, human-friendly, local-first.
"""

import argparse
import json
import sys
import time
from pathlib import Path

# Add src/ to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from iconics_output import Output, OutputContext
from iconics_executive import IconicsExecutive


def validate_threshold(value: str) -> float:
    """Validate threshold argument is between 0.0 and 1.0."""
    try:
        f = float(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid threshold: {value}")
    if not 0.0 <= f <= 1.0:
        raise argparse.ArgumentTypeError(
            f"Threshold must be between 0.0 and 1.0, got {f}"
        )
    return f


def main():
    """Main entry point for iconics CLI."""

    # 1. Initialize Argparse with Subcommand Groups
    parser = argparse.ArgumentParser(
        prog="iconics",
        description="Iconics - Unified Agentic Icon Library Executive",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  iconics search "security lock"           # Semantic search
  iconics ingest raw/new-icon.png          # Auto-label and catalog
  iconics use lock shield key              # Export with markdown
  iconics tui --query "security"           # Launch interactive TUI
  iconics watch                            # Monitor raw/ directory

Output modes:
  --quiet     Agent mode (minimal output)
  --json      Machine mode (JSON output)
  --verbose   Human mode (detailed output)
"""
    )

    # Global Options
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Agent mode: Minimal output (just IDs)')
    parser.add_argument('--json', '-j', action='store_true',
                       help='Machine mode: JSON output')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Human mode: Debug/detailed output')
    parser.add_argument('--no-color', action='store_true',
                       help='Disable ANSI colors')

    subparsers = parser.add_subparsers(dest='command', required=True,
                                       help='Available commands')

    # --- DISCOVERY GROUP ---
    search_parser = subparsers.add_parser('search',
                                         help='Semantic search via CLIP embeddings')
    search_parser.add_argument('query', nargs='+',
                              help='Search query (natural language)')
    search_parser.add_argument('--limit', '-l', type=int, default=10,
                              help='Number of results (default: 10)')

    suggest_parser = subparsers.add_parser('suggest',
                                          help='Context-based icon suggestions')
    suggest_parser.add_argument('context', help='Context keyword or description')
    suggest_parser.add_argument('--limit', '-l', type=int, default=5,
                               help='Number of suggestions (default: 5)')

    info_parser = subparsers.add_parser('info',
                                       help='Show detailed icon information')
    info_parser.add_argument('name', help='Icon semantic name or ID')

    # --- EXPORT GROUP ---
    use_parser = subparsers.add_parser('use',
                                       help='Export icons + generate markdown')
    use_parser.add_argument('icons', nargs='+',
                           help='Icon IDs or semantic names to export')
    use_parser.add_argument('--project', '-p', type=Path,
                           help='Project directory (auto-detected if not specified)')

    here_parser = subparsers.add_parser('here',
                                       help='Export to current directory')
    here_parser.add_argument('icons', nargs='+',
                            help='Icon IDs or semantic names to export')

    # --- AUTO-PIPELINE GROUP ---
    ingest_parser = subparsers.add_parser('ingest',
                                         help='Auto-label and catalog new icon(s)')
    ingest_parser.add_argument('path', nargs='?', default='raw/',
                              help='Path to icon file or directory (default: raw/)')
    ingest_parser.add_argument('--force', action='store_true',
                              help='Reprocess already cataloged icons')
    ingest_parser.add_argument('--dry-run', action='store_true',
                              help='Preview changes without applying')

    watch_parser = subparsers.add_parser('watch',
                                        help='Start resident file watcher')
    watch_parser.add_argument('--debounce', type=int, default=500,
                             help='Debounce delay in ms (default: 500)')
    watch_parser.add_argument('--path', type=Path, default=Path('raw'),
                             help='Directory to watch (default: raw/)')

    sync_parser = subparsers.add_parser('sync',
                                       help='Sync raw/ with catalog/embeddings')
    sync_parser.add_argument('--dry-run', action='store_true',
                            help='Preview changes without applying')

    # --- CATALOG GROUP ---
    add_parser = subparsers.add_parser('add',
                                      help='Manually add icon to catalog')
    add_parser.add_argument('id', help='Icon ID')
    add_parser.add_argument('--semantic', required=True,
                           help='Semantic name')
    add_parser.add_argument('--tags', required=True,
                           help='Comma-separated tags')
    add_parser.add_argument('--category', required=True,
                           help='Category (ui, files, security, etc.)')
    add_parser.add_argument('--desc', help='Description')

    import_parser = subparsers.add_parser('import',
                                         help='Bulk import from CSV')
    import_parser.add_argument('csv_file', type=Path,
                              help='Path to CSV file')

    stats_parser = subparsers.add_parser('stats',
                                        help='Show library statistics')

    recent_parser = subparsers.add_parser('recent',
                                         help='Show recently cataloged icons')
    recent_parser.add_argument('n', type=int, nargs='?', default=10,
                              help='Number of icons to show (default: 10)')

    list_parser = subparsers.add_parser('list',
                                       help='List icons in category')
    list_parser.add_argument('category',
                            help='Category name')

    validate_parser = subparsers.add_parser('validate',
                                           help='Validate catalog integrity')

    # --- EMBEDDINGS GROUP ---
    embed_parser = subparsers.add_parser('embed',
                                        help='Regenerate CLIP embeddings')
    embed_parser.add_argument('--force', action='store_true',
                             help='Force full rebuild (default: incremental)')

    query_parser = subparsers.add_parser('query',
                                        help='Direct CLIP embedding query')
    query_parser.add_argument('text', nargs='+',
                             help='Text to embed and query')
    query_parser.add_argument('--limit', '-l', type=int, default=10,
                             help='Number of results (default: 10)')

    # --- TUI GROUP ---
    tui_parser = subparsers.add_parser('tui',
                                       help='Launch interactive terminal UI')
    tui_parser.add_argument('--category', '-c',
                           help='Pre-filter to category')
    tui_parser.add_argument('--query', '-q',
                           help='Start with search query')

        # --- VARIANTS GROUP ---
    variants_parser = subparsers.add_parser('variants',
                                           help='Detect and manage icon size variants')
    variants_parser.add_argument('name', nargs='?',
                                help='Show variants for specific icon base name')
    variants_parser.add_argument('--detect', action='store_true',
                                help='Auto-detect all variant groups')
    variants_parser.add_argument('--bundle', metavar='BASE_NAME',
                                help='Create .imrb bundle for variant group')
    variants_parser.add_argument('--output', '-o', type=Path,
                                help='Output path for bundle or JSON export')
    variants_parser.add_argument('--threshold', type=validate_threshold, default=0.90,
                                help='CLIP similarity threshold (default: 0.90)')

# --- DEDUPE GROUP ---
    dedupe_parser = subparsers.add_parser('dedupe',
                                         help='Find and manage duplicate icons')
    dedupe_parser.add_argument('--threshold', '-t', type=validate_threshold, default=0.95,
                              help='Similarity threshold for duplicates (default: 0.95)')
    dedupe_parser.add_argument('--dry-run', action='store_true',
                              help='Preview clusters without making changes')
    dedupe_parser.add_argument('--interactive', '-i', action='store_true',
                              help='Interactive mode: prompt for each cluster')
    dedupe_parser.add_argument('--output', '-o', type=Path,
                              help='Export clusters to JSON file')

    # 2. Parse and Initialize Output Context
    args = parser.parse_args()

    # Determine Output Mode
    if args.json:
        mode = 'json'
    elif args.quiet:
        mode = 'quiet'
    elif args.verbose:
        mode = 'table'
    else:
        mode = 'compact'

    # Global Output Setup
    output = Output(mode=mode, quiet=args.quiet, color=not args.no_color)
    OutputContext.set_global(output)

    # 3. Initialize the Resident Executive
    executive = IconicsExecutive(output=output)

    try:
        # Hand off to Executive for command routing
        if args.command == 'search':
            query = ' '.join(args.query)
            if not executive.retriever:
                output.error("CLIP retriever not initialized. Check embeddings path.")
                sys.exit(1)

            # Use retriever for text query
            results = executive.retriever.retrieve(query, k=args.limit)
            if not results:
                output.warn(f"No results found for '{query}'")
                sys.exit(0)

            # Format and display results
            result_dicts = [
                {
                    'icon_id': r.icon_id,
                    'score': r.score,
                    'residual_score': getattr(r, 'residual_score', 0.0)
                }
                for r in results
            ]
            print(output.format_search_results(result_dicts, query, show_scores=args.verbose))

        elif args.command == 'ingest':
            path = Path(args.path)

            if not path.exists():
                output.error(f"Path not found: {path}")
                sys.exit(1)

            # Handle single file vs directory
            if path.is_file():
                if output.mode != 'quiet':
                    output.info(f"Ingesting: {path.name}")

                result = executive.execute_ingest(path, force=args.force)

                if result.status == 'error':
                    output.error(f"Ingestion failed: {result.metadata.get('error', 'Unknown error')}")
                    sys.exit(1)

                # Display result
                output.format_ingest_result_detailed(result.to_dict())

                if result.audit_corrections:
                    output.debug(f"Applied {len(result.audit_corrections)} audit corrections")

            elif path.is_dir():
                # Batch ingestion
                icon_files = []
                for ext in ['.png', '.svg', '.webp']:
                    icon_files.extend(path.glob(f'*{ext}'))

                if not icon_files:
                    output.warn(f"No icon files found in {path}")
                    sys.exit(0)

                output.info(f"Found {len(icon_files)} icon(s) to ingest")

                success_count = 0
                bypass_count = 0
                vlm_count = 0
                error_count = 0

                for icon_path in icon_files:
                    result = executive.execute_ingest(icon_path, force=args.force)

                    if result.status == 'error':
                        error_count += 1
                        output.error(f"{icon_path.name}: {result.metadata.get('error', 'Unknown')}")
                    elif result.status == 'bypass':
                        bypass_count += 1
                        success_count += 1
                    elif result.status == 'vlm':
                        vlm_count += 1
                        success_count += 1

                # Summary
                if output.mode != 'quiet':
                    output.success(f"Ingestion complete: {success_count}/{len(icon_files)} succeeded")
                    output.info(f"  Bypass: {bypass_count}, VLM: {vlm_count}, Errors: {error_count}")

        elif args.command == 'use':
            result = executive.use_icons(
                query_ids=args.icons,
                target_dir=args.project,
                generate_markdown=True
            )

            if not result['exported']:
                output.error("No icons were exported")
                sys.exit(1)

            # Display results using the formatter
            print(output.format_export_result(
                exported=[item['semantic_name'] for item in result['exported']],
                failed=result['failed'],
                project_path=result['target_dir'],
                markdown_snippets=result['markdown']
            ))

        elif args.command == 'here':
            # 'here' is just 'use' with current directory
            result = executive.use_icons(
                query_ids=args.icons,
                target_dir=Path.cwd() / 'icons',
                generate_markdown=True
            )

            if not result['exported']:
                output.error("No icons were exported")
                sys.exit(1)

            print(output.format_export_result(
                exported=[item['semantic_name'] for item in result['exported']],
                failed=result['failed'],
                project_path=result['target_dir'],
                markdown_snippets=result['markdown']
            ))

        elif args.command == 'stats':
            stats = executive.get_stats()
            output.format_stats(stats)

        elif args.command == 'tui':
            # Import TUI module
            try:
                from iconics_tui import run_tui
            except ImportError as e:
                output.error(f"TUI dependencies not installed: {e}")
                output.info("Install with: pip install textual term-image")
                sys.exit(1)

            # Ensure retriever is initialized
            if not executive.retriever:
                output.error("CLIP retriever not initialized. Check embeddings path.")
                sys.exit(1)

            # Launch TUI
            try:
                run_tui(
                    retriever=executive.retriever,
                    catalog_path=Path('icon-catalog.json'),
                    query=args.query,
                    category=args.category
                )
            except KeyboardInterrupt:
                output.info("\nTUI closed by user")
                sys.exit(0)
            except Exception as e:
                output.error(f"TUI failed: {e}")
                if args.verbose:
                    import traceback
                    traceback.print_exc()
                sys.exit(1)

        elif args.command == 'watch':
            from iconics_watcher import IconicsWatcher

            # Create and start watcher
            watcher = IconicsWatcher(
                executive=executive,
                watch_path=args.path,
                debounce_ms=args.debounce
            )

            try:
                watcher.start()

                # Keep running until interrupted
                output.info("Press Ctrl+C to stop watching...")

                while True:
                    time.sleep(1)

            except KeyboardInterrupt:
                output.info("\nStopping watcher...")
                watcher.stop()
                output.success("Watcher stopped cleanly")
                sys.exit(0)

        elif args.command == 'variants':
            from iconics_variants import (
                detect_variant_groups,
                create_bundle,
                format_variant_group_display,
                extract_base_and_size
            )

            if not executive.retriever:
                output.error("CLIP retriever not initialized. Check embeddings path.")
                sys.exit(1)

            # Load catalog
            with open('icon-catalog.json') as f:
                catalog = json.load(f)

            # Mode 1: Show variants for specific icon
            if args.name and not args.detect and not args.bundle:
                # Find the variant group containing this icon
                all_groups = detect_variant_groups(
                    icon_ids=executive.retriever.icon_ids,
                    embeddings=executive.retriever.embeddings,
                    icon_index=executive.retriever.icon_index,
                    similarity_threshold=args.threshold
                )

                # Check if name is a base name or an icon ID
                base, size = extract_base_and_size(args.name)
                search_base = base if base else args.name

                # Find matching group
                matching_group = None
                for group in all_groups:
                    if group.base_name == search_base or args.name in group.variants:
                        matching_group = group
                        break

                if matching_group:
                    print(format_variant_group_display(matching_group, catalog, show_matrix=args.verbose))
                else:
                    output.error(f"No variant group found for '{args.name}'")
                    sys.exit(1)

            # Mode 2: Auto-detect all variant groups
            elif args.detect:
                output.info(f"Detecting variant groups (threshold={args.threshold})...")

                groups = detect_variant_groups(
                    icon_ids=executive.retriever.icon_ids,
                    embeddings=executive.retriever.embeddings,
                    icon_index=executive.retriever.icon_index,
                    similarity_threshold=args.threshold
                )

                if not groups:
                    output.success("No variant groups found!")
                    sys.exit(0)

                # Summary
                total_variants = sum(len(g.variants) for g in groups)
                output.info(f"Found {len(groups)} variant groups ({total_variants} icons total)")

                # Export to JSON if requested
                if args.output:
                    output_data = {
                        'threshold': args.threshold,
                        'groups': [g.to_dict() for g in groups]
                    }
                    with open(args.output, 'w') as f:
                        json.dump(output_data, f, indent=2)
                    output.success(f"Exported {len(groups)} groups to {args.output}")
                else:
                    # Display groups
                    for group in groups[:10]:  # Show first 10
                        print(format_variant_group_display(group, catalog, show_matrix=False))
                        print()

                    if len(groups) > 10:
                        output.info(f"... and {len(groups) - 10} more groups (use --output to export all)")

            # Mode 3: Create bundle for specific variant group
            elif args.bundle:
                output.info(f"Creating bundle for '{args.bundle}'...")

                # Detect groups
                groups = detect_variant_groups(
                    icon_ids=executive.retriever.icon_ids,
                    embeddings=executive.retriever.embeddings,
                    icon_index=executive.retriever.icon_index,
                    similarity_threshold=args.threshold
                )

                # Find matching group
                matching_group = None
                for group in groups:
                    if group.base_name == args.bundle:
                        matching_group = group
                        break

                if not matching_group:
                    output.error(f"No variant group found for '{args.bundle}'")
                    sys.exit(1)

                # Determine output path
                if args.output:
                    bundle_path = args.output
                else:
                    bundle_path = Path(f"{args.bundle}.imrb")

                # Create bundle
                try:
                    result_path = create_bundle(
                        group=matching_group,
                        icon_dir=Path.cwd(),
                        output_path=bundle_path,
                        catalog=catalog
                    )
                    output.success(f"Created bundle: {result_path} ({len(matching_group.variants)} variants)")
                except FileNotFoundError as e:
                    output.error(f"Bundle creation failed: {e}")
                    sys.exit(1)

            else:
                output.error("Please specify --detect, --bundle, or provide an icon name")
                sys.exit(1)


        elif args.command == 'dedupe':
            from iconics_dedupe import (
                find_duplicate_clusters,
                format_cluster_output,
                export_clusters_to_json,
                interactive_dedupe
            )

            if not executive.retriever:
                output.error("CLIP retriever not initialized. Check embeddings path.")
                sys.exit(1)

            # Load catalog for metadata lookups
            catalog_lookup = {
                icon['id']: icon
                for icon in executive.catalog._catalog.get('icons', [])
            }

            output.info(f"Finding duplicates (threshold={args.threshold})...")

            # Find duplicate clusters
            clusters = find_duplicate_clusters(
                embeddings=executive.retriever.embeddings,
                icon_ids=executive.retriever.icon_ids,
                catalog_lookup=catalog_lookup,
                threshold=args.threshold
            )

            if not clusters:
                output.success("No duplicate clusters found!")
                sys.exit(0)

            # Summary
            total_icons = sum(len(c.members) for c in clusters)
            output.info(f"Found {len(clusters)} duplicate clusters ({total_icons} icons total)")

            # Export to JSON if requested
            if args.output:
                export_clusters_to_json(clusters, args.output, catalog_lookup)
                output.success(f"Exported clusters to {args.output}")

            # Display clusters
            if not args.interactive:
                for i, cluster in enumerate(clusters, 1):
                    print(format_cluster_output(cluster, i, catalog_lookup, verbose=args.verbose))

            # Interactive mode
            if args.interactive and not args.dry_run:
                stats = interactive_dedupe(clusters, executive.catalog)
                output.success(
                    f"\nDedupe complete: {stats['kept']} canonicals kept, "
                    f"{stats['merged']} duplicates merged, {stats['skipped']} skipped"
                )
            elif args.dry_run:
                output.info("\n[Dry run mode - no changes made]")

        else:
            output.error(f"Command '{args.command}' not yet implemented")
            sys.exit(1)

    except KeyboardInterrupt:
        output.info("\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        output.error(f"Executive failure: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
