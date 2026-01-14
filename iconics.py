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
sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))

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

    md_parser = subparsers.add_parser('md',
                                     help='Generate markdown snippets (no export)')
    md_parser.add_argument('icons', nargs='+',
                          help='Icon IDs or semantic names')

    cat_parser = subparsers.add_parser('cat',
                                      help='Export entire category')
    cat_parser.add_argument('category', help='Category to export')
    cat_parser.add_argument('--project', '-p', type=Path,
                           help='Project directory (auto-detected if not specified)')

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

        elif args.command == 'md':
            # Generate markdown snippets without exporting
            icons = executive.catalog._catalog.get('icons', [])
            icon_lookup = {icon['id']: icon for icon in icons}

            # Also build semantic name lookup
            for icon in icons:
                if icon.get('semanticName'):
                    icon_lookup[icon['semanticName']] = icon

            found_icons = []
            failed = []

            for query in args.icons:
                # Exact match first
                if query in icon_lookup:
                    found_icons.append(icon_lookup[query])
                else:
                    # Fuzzy match
                    matched = False
                    for icon in icons:
                        if query.lower() in icon['id'].lower() or \
                           query.lower() in icon.get('semanticName', '').lower():
                            found_icons.append(icon)
                            matched = True
                            break
                    if not matched:
                        failed.append(query)

            if not found_icons:
                output.error("No icons found")
                if failed:
                    output.info(f"Failed to find: {', '.join(failed)}")
                sys.exit(1)

            output.info("\nMarkdown snippets:\n")
            for icon in found_icons:
                name = icon.get('semanticName', icon['id'])
                cat = icon.get('category', 'ui')
                # Generate markdown using standard path
                md = f"![{name}](.github/assets/icons/{name}.png)"
                print(f"  {md}")

            if failed:
                output.warn(f"\nNot found: {', '.join(failed)}")

        elif args.command == 'cat':
            # Export entire category
            category = args.category.lower()
            icons = executive.catalog._catalog.get('icons', [])

            # Filter by category
            matching = [icon for icon in icons if icon.get('category', '').lower() == category]

            if not matching:
                output.error(f"No icons found in category '{category}'")
                cats = set(icon.get('category', 'unknown') for icon in icons)
                output.info(f"Available categories: {', '.join(sorted(cats))}")
                sys.exit(1)

            output.info(f"Exporting {len(matching)} icons from category '{category}'...")

            # Use the executive to export all icons
            icon_ids = [icon['id'] for icon in matching]
            result = executive.use_icons(
                query_ids=icon_ids[:50],  # Limit to 50 to avoid overwhelming
                target_dir=args.project,
                generate_markdown=True
            )

            if result['exported']:
                output.success(f"Exported {len(result['exported'])} icons")
                if len(matching) > 50:
                    output.warn(f"Limited to first 50 icons. Category has {len(matching)} total.")
            else:
                output.error("Export failed")
                sys.exit(1)

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

        elif args.command == 'suggest':
            # Context-based icon suggestions using semantic matching
            context = args.context.lower()

            # Context weight mappings for common use cases
            CONTEXT_WEIGHTS = {
                'authentication': ['lock', 'key', 'shield', 'certificate', 'login', 'user', 'password'],
                'auth': ['lock', 'key', 'shield', 'certificate', 'login', 'user', 'password'],
                'login': ['lock', 'key', 'shield', 'login', 'user', 'password', 'certificate'],
                'security': ['shield', 'lock', 'key', 'protection', 'certificate', 'secure', 'keychain'],
                'secure': ['shield', 'lock', 'key', 'protection', 'certificate'],
                'network': ['network', 'cloud', 'globe', 'wifi', 'server', 'connection', 'internet'],
                'api': ['network', 'cloud', 'server', 'database', 'endpoint', 'connection'],
                'server': ['server', 'network', 'cloud', 'database', 'computer'],
                'data': ['database', 'folder', 'storage', 'cloud', 'file', 'document', 'save'],
                'database': ['database', 'storage', 'server', 'data', 'table'],
                'storage': ['database', 'folder', 'storage', 'cloud', 'save', 'disk'],
                'error': ['warning', 'error', 'alert', 'danger', 'bug', 'problem', 'critical'],
                'warning': ['warning', 'alert', 'caution', 'danger', 'exclamation', 'attention'],
                'alert': ['warning', 'alert', 'bell', 'notification', 'exclamation'],
                'success': ['checkbox', 'checkmark', 'success', 'done', 'complete', 'approved', 'ok'],
                'complete': ['checkbox', 'checkmark', 'success', 'done', 'complete'],
                'done': ['checkbox', 'checkmark', 'success', 'done', 'complete'],
                'info': ['info', 'help', 'question', 'about', 'details', 'information'],
                'help': ['help', 'question', 'info', 'about', 'book'],
                'information': ['info', 'help', 'question', 'about', 'details'],
                'settings': ['settings', 'gear', 'options', 'toolbox', 'config', 'preferences', 'wrench'],
                'config': ['settings', 'gear', 'options', 'toolbox', 'config', 'preferences'],
                'options': ['settings', 'gear', 'options', 'toolbox', 'preferences'],
                'navigation': ['home', 'menu', 'arrow', 'close', 'back', 'forward', 'navigation'],
                'menu': ['menu', 'navigation', 'home', 'list', 'hamburger'],
                'ui': ['arrow', 'button', 'checkbox', 'menu', 'close', 'home', 'navigation'],
                'files': ['folder', 'document', 'file', 'pdf', 'documents', 'archive', 'text'],
                'documents': ['folder', 'document', 'file', 'pdf', 'documents', 'book', 'text'],
                'docs': ['folder', 'document', 'file', 'pdf', 'book', 'text'],
                'code': ['console', 'terminal', 'code', 'script', 'database', 'git', 'bug'],
                'development': ['console', 'terminal', 'code', 'script', 'database', 'git', 'bug'],
                'programming': ['console', 'terminal', 'code', 'script', 'database'],
                'search': ['search', 'find', 'magnifying', 'lookup', 'query', 'discover'],
                'find': ['search', 'find', 'magnifying', 'lookup'],
                'user': ['user', 'profile', 'account', 'person', 'login', 'logout', 'avatar'],
                'account': ['user', 'profile', 'account', 'person', 'login'],
                'profile': ['user', 'profile', 'account', 'person', 'avatar'],
                'email': ['email', 'mail', 'message', 'inbox', 'envelope', 'letter'],
                'mail': ['email', 'mail', 'message', 'inbox', 'envelope'],
                'message': ['email', 'mail', 'message', 'chat', 'comment', 'envelope'],
                'chat': ['chat', 'message', 'comment', 'conversation', 'bubble'],
                'notification': ['bell', 'notification', 'alert', 'message', 'badge'],
                'media': ['video', 'audio', 'image', 'photo', 'camera', 'play', 'music'],
                'image': ['image', 'picture', 'photo', 'camera', 'graphic'],
                'photo': ['image', 'picture', 'photo', 'camera'],
                'video': ['video', 'play', 'media', 'camera', 'film'],
                'audio': ['audio', 'sound', 'music', 'speaker', 'volume'],
                'time': ['clock', 'timer', 'calendar', 'schedule', 'time', 'alarm'],
                'calendar': ['calendar', 'clock', 'schedule', 'date', 'event'],
                'clock': ['clock', 'timer', 'time', 'alarm', 'watch'],
                'tools': ['toolbox', 'wrench', 'hammer', 'gear', 'settings', 'screwdriver'],
                'money': ['money', 'cash', 'payment', 'dollar', 'coin', 'credit', 'cart'],
                'payment': ['money', 'cash', 'payment', 'credit', 'cart', 'checkout'],
                'shopping': ['cart', 'basket', 'checkout', 'buy', 'bag'],
            }

            # Get suggestions for context
            suggestions = CONTEXT_WEIGHTS.get(context, None)

            if suggestions:
                # Use CLIP to find actual icons matching these terms
                if executive.retriever:
                    all_results = []
                    for term in suggestions[:args.limit]:
                        results = executive.retriever.retrieve(term, k=3)
                        for r in results:
                            if r.icon_id not in [x['icon_id'] for x in all_results]:
                                all_results.append({
                                    'icon_id': r.icon_id,
                                    'score': r.score,
                                    'term': term
                                })

                    # Sort by score and dedupe
                    seen = set()
                    final_results = []
                    for r in sorted(all_results, key=lambda x: x['score'], reverse=True):
                        # Normalize icon_id to semantic name
                        base_name = r['icon_id'].split('-')[0].replace('_', ' ')
                        if base_name not in seen:
                            seen.add(base_name)
                            final_results.append(r)
                        if len(final_results) >= args.limit:
                            break

                    if final_results:
                        output.info(f"\nIcon suggestions for '{context}':\n")
                        for i, r in enumerate(final_results, 1):
                            print(f"  {i}. {r['icon_id']}")
                    else:
                        output.warn(f"No icons found for context '{context}'")
                else:
                    # Fallback: just show the terms
                    output.info(f"\nSuggested icon terms for '{context}':")
                    for term in suggestions[:args.limit]:
                        print(f"  {term}")
            else:
                # Use CLIP search as fallback
                if executive.retriever:
                    results = executive.retriever.retrieve(context, k=args.limit)
                    if results:
                        output.info(f"\nIcon suggestions for '{context}':\n")
                        for i, r in enumerate(results, 1):
                            print(f"  {i}. {r.icon_id}")
                    else:
                        output.warn(f"No icons found for context '{context}'")
                else:
                    output.error("CLIP retriever not initialized")
                    sys.exit(1)

        elif args.command == 'info':
            # Show detailed icon information
            icon_name = args.name

            # Search catalog for the icon
            icons = executive.catalog._catalog.get('icons', [])

            # Try exact match first
            found = None
            for icon in icons:
                if icon['id'] == icon_name or icon.get('semanticName', '') == icon_name:
                    found = icon
                    break

            # Try fuzzy match if not found
            if not found:
                for icon in icons:
                    if icon_name.lower() in icon['id'].lower() or \
                       icon_name.lower() in icon.get('semanticName', '').lower():
                        found = icon
                        break

            if found:
                print(f"\nIcon: {found['id']}")
                print(f"  Semantic Name: {found.get('semanticName', 'N/A')}")
                print(f"  Category: {found.get('category', 'unknown')}")
                print(f"  Tags: {', '.join(found.get('tags', []))}")
                if found.get('description'):
                    print(f"  Description: {found['description']}")
                if found.get('sourceFile'):
                    print(f"  Source: {found['sourceFile']}")
                if found.get('style'):
                    print(f"  Style: {found['style']}")
                if found.get('usedIn'):
                    print(f"  Used In: {', '.join(found['usedIn'][:5])}")

                # Check embedding status
                if executive.retriever and found['id'] in executive.retriever.icon_index:
                    print(f"  Embedding: Yes (index {executive.retriever.icon_index[found['id']]})")
                else:
                    print(f"  Embedding: No")
            else:
                output.error(f"Icon '{icon_name}' not found")
                # Suggest similar icons
                if executive.retriever:
                    results = executive.retriever.retrieve(icon_name, k=5)
                    if results:
                        output.info("Did you mean:")
                        for r in results:
                            print(f"  {r.icon_id}")
                sys.exit(1)

        elif args.command == 'recent':
            # Show recently cataloged icons (by position in catalog - last N added)
            icons = executive.catalog._catalog.get('icons', [])
            n = args.n

            if not icons:
                output.warn("No icons in catalog")
                sys.exit(0)

            recent = icons[-n:][::-1]  # Get last N, reverse for newest first

            output.info(f"\nMost recent {len(recent)} icons:\n")
            for i, icon in enumerate(recent, 1):
                name = icon.get('semanticName', icon['id'])
                cat = icon.get('category', 'unknown')
                print(f"  {i}. {name:30} [{cat}]")

        elif args.command == 'list':
            # List icons in a category
            category = args.category.lower()
            icons = executive.catalog._catalog.get('icons', [])

            # Filter by category
            matching = [icon for icon in icons if icon.get('category', '').lower() == category]

            if not matching:
                output.error(f"No icons found in category '{category}'")
                # Show available categories
                cats = set(icon.get('category', 'unknown') for icon in icons)
                output.info(f"Available categories: {', '.join(sorted(cats))}")
                sys.exit(1)

            output.info(f"\nIcons in category '{category}' ({len(matching)} total):\n")

            # Group by first letter for readability
            from itertools import groupby

            # Show first 50 or all if less
            display = matching[:50]
            for icon in display:
                name = icon.get('semanticName', icon['id'])
                print(f"  {name}")

            if len(matching) > 50:
                output.info(f"\n  ... and {len(matching) - 50} more")

        elif args.command == 'validate':
            # Validate catalog integrity
            output.info("Validating catalog integrity...\n")

            icons = executive.catalog._catalog.get('icons', [])
            issues = []

            # Check for required fields
            required_fields = ['id', 'category']
            for icon in icons:
                for field in required_fields:
                    if field not in icon or not icon[field]:
                        issues.append(f"Missing {field}: {icon.get('id', 'UNKNOWN')}")

            # Check for duplicate IDs
            seen_ids = {}
            for icon in icons:
                icon_id = icon.get('id', '')
                if icon_id in seen_ids:
                    issues.append(f"Duplicate ID: {icon_id}")
                seen_ids[icon_id] = True

            # Check embedding coverage
            if executive.retriever:
                embedding_ids = set(executive.retriever.icon_ids)
                catalog_ids = set(icon['id'] for icon in icons)

                missing_embeddings = catalog_ids - embedding_ids
                orphan_embeddings = embedding_ids - catalog_ids

                if missing_embeddings:
                    issues.append(f"Icons missing embeddings: {len(missing_embeddings)}")
                    for icon_id in list(missing_embeddings)[:5]:
                        issues.append(f"  - {icon_id}")
                    if len(missing_embeddings) > 5:
                        issues.append(f"  ... and {len(missing_embeddings) - 5} more")

                if orphan_embeddings:
                    issues.append(f"Orphan embeddings (not in catalog): {len(orphan_embeddings)}")
                    for icon_id in list(orphan_embeddings)[:5]:
                        issues.append(f"  - {icon_id}")

            # Check for missing source files
            missing_files = 0
            for icon in icons[:100]:  # Check first 100 to avoid slowdown
                source = icon.get('sourceFile', '')
                if source:
                    # Try multiple locations
                    found = False
                    for base in [Path('.'), Path('raw'), Path('catalog')]:
                        if (base / source).exists() or Path(source).exists():
                            found = True
                            break
                    if not found:
                        missing_files += 1

            if missing_files > 0:
                issues.append(f"Missing source files (sampled): {missing_files}")

            # Summary
            if issues:
                output.warn(f"Found {len(issues)} issues:\n")
                for issue in issues:
                    print(f"  {issue}")
            else:
                output.success("Catalog validation passed!")
                print(f"\n  Total icons: {len(icons)}")
                print(f"  Categories: {len(set(icon.get('category', 'unknown') for icon in icons))}")
                if executive.retriever:
                    print(f"  Embeddings: {len(executive.retriever.icon_ids)}")

        elif args.command == 'sync':
            # Sync raw/ with catalog/embeddings
            output.info("Syncing raw/ with catalog and embeddings...\n")

            raw_path = Path('raw')
            if not raw_path.exists():
                output.error("raw/ directory not found")
                sys.exit(1)

            # Find all icon files in raw/
            raw_files = []
            for ext in ['.png', '.svg', '.webp']:
                raw_files.extend(raw_path.glob(f'*{ext}'))

            # Get catalog IDs
            catalog_ids = {icon['id'] for icon in executive.catalog._catalog.get('icons', [])}

            # Get embedding IDs
            embedding_ids = set(executive.retriever.icon_ids) if executive.retriever else set()

            # Find files not in catalog
            raw_stems = {f.stem for f in raw_files}
            not_cataloged = raw_stems - catalog_ids
            not_embedded = catalog_ids - embedding_ids

            output.info(f"Raw files: {len(raw_files)}")
            output.info(f"Cataloged: {len(catalog_ids)}")
            output.info(f"Embedded: {len(embedding_ids)}")
            print()

            if not_cataloged:
                output.warn(f"Files not in catalog: {len(not_cataloged)}")
                for name in list(not_cataloged)[:10]:
                    print(f"  {name}")
                if len(not_cataloged) > 10:
                    print(f"  ... and {len(not_cataloged) - 10} more")
                print()

            if not_embedded:
                output.warn(f"Catalog entries missing embeddings: {len(not_embedded)}")
                for name in list(not_embedded)[:10]:
                    print(f"  {name}")
                if len(not_embedded) > 10:
                    print(f"  ... and {len(not_embedded) - 10} more")
                print()

            if not args.dry_run:
                # Actually perform the sync
                if not_cataloged:
                    output.info("Ingesting uncataloged files...")
                    for name in not_cataloged:
                        file_path = raw_path / f"{name}.png"
                        if file_path.exists():
                            result = executive.execute_ingest(file_path)
                            if result.status != 'error':
                                output.debug(f"Ingested: {name}")
                    output.success(f"Ingested {len(not_cataloged)} files")
            else:
                output.info("[Dry run mode - no changes made]")

        elif args.command == 'query':
            # Direct CLIP embedding query
            query_text = ' '.join(args.text)

            if not executive.retriever:
                output.error("CLIP retriever not initialized. Check embeddings path.")
                sys.exit(1)

            # Perform retrieval
            results = executive.retriever.retrieve(query_text, k=args.limit)

            if not results:
                output.warn(f"No results for query: '{query_text}'")
                sys.exit(0)

            # Format output
            result_dicts = [
                {
                    'icon_id': r.icon_id,
                    'score': r.score,
                    'residual_score': getattr(r, 'residual_score', 0.0)
                }
                for r in results
            ]
            print(output.format_search_results(result_dicts, query_text, show_scores=True))

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
