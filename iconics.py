#!/usr/bin/env python3
"""
Iconics - Unified Agentic Icon Library Executive

One CLI, one command structure, one vision.
Drop icons → auto-catalog → auto-embed.
Agent-friendly, human-friendly, local-first.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
import shutil

def _detect_subcommand(argv: list[str]) -> str | None:
    """
    Return the first non-flag CLI token, which should be the subcommand.

    We intentionally avoid importing any project modules here so we can re-exec
    into an `uv` environment if the user is running system python.
    """
    for arg in argv[1:]:
        if not arg.startswith("-"):
            return arg
    return None

def _maybe_reexec_with_uv() -> None:
    """
    If the current interpreter is missing required ML deps, re-exec under `uv run`.

    This is the permanent fix for the "vision tool doesn't run" class of issues:
    users often invoke `python3 iconics.py ...` from a shell where system python
    is active, bypassing the project's dependency set defined in pyproject.toml.

    Safety:
      - Only re-execs when required imports are missing.
      - Uses an env guard to avoid infinite recursion.
      - Chdirs to the repo root (where pyproject.toml lives) for reliable resolution.
    """
    if os.environ.get("ICONICS_SKIP_UV_REEXEC") == "1":
        return

    subcommand = _detect_subcommand(sys.argv)
    if subcommand is None:
        return

    # Commands that do not require ML deps should never trigger re-exec.
    no_ml_commands = {
        "categories",
        "help",
        "completion",
    }
    if subcommand in no_ml_commands:
        return

    # These subcommands require the vision stack to be installed in the active python.
    # If not present, we re-exec under `uv run` to ensure pyproject dependencies apply.
    needs_vision = {
        "relabel",
        "ingest",
        "watch",
        "sync",
        "embed",
        "query",
        "dedupe",
        "variants",
    }
    if subcommand not in needs_vision:
        return

    missing: list[str] = []
    for module in ("transformers", "qwen_vl_utils", "open_clip"):
        try:
            __import__(module)
        except ModuleNotFoundError:
            missing.append(module)

    if not missing:
        return

    uv = shutil.which("uv")

    if uv is None:
        sys.stderr.write(
            "ERROR: Missing required dependencies for vision operations: "
            + ", ".join(missing)
            + "\n"
            "Fix: install deps via `uv sync` and run via `uv run python iconics.py ...`\n"
        )
        raise SystemExit(1)

    base_dir = Path(__file__).resolve().parent
    os.chdir(str(base_dir))

    env = os.environ.copy()
    env["ICONICS_SKIP_UV_REEXEC"] = "1"

    sys.stderr.write(
        "INFO: Missing vision deps ("
        + ", ".join(missing)
        + "); re-running under `uv run` from "
        + str(base_dir)
        + "\n"
    )

    args = [uv, "run", "python", str(base_dir / "iconics.py"), *sys.argv[1:]]
    os.execvpe(uv, args, env)


_maybe_reexec_with_uv()

# Add src/ to path for imports (after potential uv re-exec)
sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))

from iconics_output import Output, OutputContext
from iconics_executive import IconicsExecutive


def metadata_search(catalog: dict, query: str, limit: int = 10) -> list[dict]:
    """
    Lightweight fallback search when CLIP text-embedding deps are unavailable.

    Scores are heuristic and only intended for ranking within the fallback path.
    """
    icons = catalog.get("icons", [])
    query_lower = query.strip().lower()
    terms = {t for t in re.split(r"[\s\-_]+", query_lower) if t}
    if not terms:
        return []

    best_by_id: dict[str, float] = {}
    for icon in icons:
        icon_id = icon.get("id")
        if not icon_id:
            continue

        semantic = str(icon.get("semanticName") or icon_id).lower()
        category = str(icon.get("category") or "").lower()
        description = str(icon.get("description") or "").lower()
        tags = [str(t).lower() for t in (icon.get("tags") or []) if isinstance(t, str)]

        score = 0.0

        name_hits = sum(1 for t in terms if t in semantic)
        if name_hits:
            score += 0.6 * (name_hits / len(terms))

        tag_set = set(tags)
        tag_hits = len(terms & tag_set)
        if tag_hits:
            score += 0.3 * (tag_hits / len(terms))

        if any(t in category for t in terms):
            score += 0.05
        desc_hits = sum(1 for t in terms if t in description)
        if desc_hits:
            score += 0.05 * min(desc_hits / len(terms), 1.0)

        if score > 0:
            best_by_id[icon_id] = max(best_by_id.get(icon_id, 0.0), score)

    results = [{"icon_id": icon_id, "score": score, "residual_score": 0.0} for icon_id, score in best_by_id.items()]
    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:limit]


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
  iconics tui --query "security"           # Launch interactive TUI2 (SQLite)
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
    search_parser.add_argument('--hybrid', '-H', action='store_true',
                              help='Use hybrid search (CLIP + metadata matching)')
    search_parser.add_argument('--no-dedupe', action='store_true',
                              help='Disable deduplication of icon variants')

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

    categories_parser = subparsers.add_parser(
        'categories',
        help='List the allowed vision taxonomy categories',
    )
    categories_parser.add_argument(
        '--one-line',
        action='store_true',
        help='Print categories as a single comma-separated line',
    )

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

    relabel_parser = subparsers.add_parser('relabel',
                                         help='Re-run vision labeling to fix taxonomy drift (e.g. too many ui icons)')
    relabel_parser.add_argument('--where-category', default='ui',
                               help="Only relabel icons in this category (default: ui)")
    relabel_parser.add_argument('--limit', type=int, default=0,
                               help='Max icons to process (0 = all)')
    relabel_parser.add_argument('--dry-run', action='store_true',
                               help='Compute labels but do not write catalog updates')
    relabel_parser.add_argument('--no-bypass', action='store_true',
                               help='Disable retrieval bypass and force VLM for every icon processed')
    relabel_parser.add_argument('--update-tags', action='store_true',
                               help='Replace tags from vision output')
    relabel_parser.add_argument('--update-description', action='store_true',
                               help='Replace description from vision output')
    relabel_parser.add_argument(
        '--full',
        action='store_true',
        help='Update category, tags, description, and enrichment confidence (equivalent to --update-tags --update-description)',
    )
    relabel_parser.add_argument('--model', choices=['qwen2.5-vl-7b', 'internvl3-14b'], default='qwen2.5-vl-7b',
                               help='Which vision model to use')
    relabel_parser.add_argument('--device', default='cuda',
                               help='Device for vision model (default: cuda)')
    relabel_parser.add_argument('--quantization', choices=['8bit', '4bit'], default=None,
                               help='Optional quantization for vision model')
    relabel_parser.add_argument('--k-neighbors', type=int, default=10,
                               help='kNN candidates for retrieval context (default: 10)')
    relabel_parser.add_argument('--cache', action='store_true',
                               help='Use label cache (vision_cache/)')

    synonyms_parser = subparsers.add_parser('synonyms',
                                          help='Manage and (optionally) model-expand synonym maps')
    synonyms_sub = synonyms_parser.add_subparsers(dest='synonyms_command', required=True)

    synonyms_build = synonyms_sub.add_parser('build',
                                            help='Build synonyms map (seeded from legacy mapping)')
    synonyms_build.add_argument('--in', dest='input', type=Path, default=None,
                               help='Input synonyms JSON (overrides seed map)')
    synonyms_build.add_argument('--merge-seed', action='store_true',
                               help='Merge legacy seed map into input (union per concept)')
    synonyms_build.add_argument('--out', type=Path, default=Path('config/synonyms.json'),
                               help='Output JSON path (default: config/synonyms.json)')
    synonyms_build.add_argument('--concept', action='append', default=[],
                               help='Only build these concepts (repeatable)')
    synonyms_build.add_argument('--limit', type=int, default=0,
                               help='Max concepts to process (0 = all)')
    synonyms_build.add_argument('--max-synonyms', type=int, default=0,
                               help='Max synonyms per concept (0 = unlimited)')
    synonyms_build.add_argument('--report', type=Path, default=None,
                               help='Write a JSON diff report (before/after)')
    synonyms_build.add_argument('--use-model', action='store_true',
                               help='Use local vision model to expand/clean synonyms')
    synonyms_build.add_argument('--model', choices=['qwen2.5-vl-7b', 'internvl3-14b'], default='qwen2.5-vl-7b',
                               help='Which model to use (only with --use-model)')
    synonyms_build.add_argument('--device', default='cuda',
                               help='Device for model (default: cuda)')
    synonyms_build.add_argument('--quantization', choices=['8bit', '4bit'], default=None,
                               help='Optional quantization (only with --use-model)')
    synonyms_build.add_argument('--dry-run', action='store_true',
                               help='Print JSON to stdout instead of writing')

    synonyms_validate = synonyms_sub.add_parser('validate', help='Validate a synonyms JSON file')
    synonyms_validate.add_argument('--in', dest='input', type=Path, required=True,
                                  help='Synonyms JSON path to validate')

    synonyms_diff = synonyms_sub.add_parser('diff', help='Diff two synonyms JSON files')
    synonyms_diff.add_argument('--a', type=Path, required=True, help='Before JSON')
    synonyms_diff.add_argument('--b', type=Path, required=True, help='After JSON')
    synonyms_diff.add_argument('--json', action='store_true', help='Output diff as JSON')

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

    # --- SQLITE/DB GROUP ---
    db_parser = subparsers.add_parser('db', help='SQLite catalog operations')
    db_sub = db_parser.add_subparsers(dest='db_command', required=True)

    db_migrate = db_sub.add_parser('migrate', help='Create/refresh iconics.sqlite3 from icon-catalog.json')
    db_migrate.add_argument('--db', type=Path, default=None, help='Output SQLite DB path')
    db_migrate.add_argument('--overwrite', action='store_true', help='Overwrite existing DB')

    db_verify = db_sub.add_parser('verify', help='Verify embeddings + catalog sync')
    db_verify.add_argument('--catalog', type=Path, default=None, help='Catalog path (SQLite or JSON)')

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
    tui_parser.add_argument('--db', type=Path, default=None,
                           help='SQLite DB path (defaults to iconics.sqlite3)')

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
    base_dir = Path(__file__).resolve().parent

    if args.command == 'categories':
        from iconics_taxonomy import ALLOWED_CATEGORIES

        if args.one_line:
            print(", ".join(ALLOWED_CATEGORIES))
        else:
            print("Allowed categories:")
            for cat in ALLOWED_CATEGORIES:
                print(f"- {cat}")
        sys.exit(0)

    # SQLite is now the default catalog backend. JSON remains as migration input.
    default_catalog = base_dir / "iconics.sqlite3"

    # Allow env override (used by TUI2 as well)
    env_db = os.environ.get("ICONICS_DB")
    if env_db:
        default_catalog = Path(env_db).expanduser()

    # Ensure SQLite exists (non-destructive create; no overwrite).
    if default_catalog.suffix.lower() in {".sqlite3", ".sqlite", ".db"} and not default_catalog.exists():
        script = base_dir / "scripts" / "migrate_catalog_to_sqlite.py"
        json_catalog = base_dir / "icon-catalog.json"
        if not script.exists():
            output.error(f"Migration script not found: {script}")
            sys.exit(1)
        if not json_catalog.exists():
            output.error(f"JSON catalog not found: {json_catalog}")
            sys.exit(1)

        output.info(f"SQLite DB missing, creating: {default_catalog}")
        create = subprocess.run(
            [sys.executable, str(script), "--db", str(default_catalog)],
            cwd=str(base_dir),
        )
        if create.returncode != 0:
            output.error("Failed to create SQLite DB")
            sys.exit(create.returncode)

    executive = IconicsExecutive(
        embeddings_path=base_dir / 'embeddings',
        subspace_path=base_dir / 'subspace',
        catalog_path=default_catalog,
        output=output,
    )

    try:
        if args.command == 'db':
            if args.db_command == 'migrate':
                script = base_dir / "scripts" / "migrate_catalog_to_sqlite.py"
                db_path = args.db or (base_dir / "iconics.sqlite3")

                if db_path.exists() and not args.overwrite:
                    output.info(f"SQLite DB already exists: {db_path} (use --overwrite to rebuild)")
                    sys.exit(0)

                cmd = [
                    sys.executable,
                    str(script),
                    "--db",
                    str(db_path),
                ]
                if args.overwrite:
                    cmd.append("--overwrite")

                output.info(f"Running: {' '.join(cmd)}")
                proc = subprocess.run(cmd, cwd=str(base_dir))
                if proc.returncode != 0:
                    output.error("DB migration failed")
                    sys.exit(proc.returncode)

                output.success(f"SQLite DB ready: {db_path}")
                sys.exit(0)

            if args.db_command == 'verify':
                # Reuse existing verifier (JSON-first, but catalog path will be checked by SQLite tooling separately)
                verify = base_dir / "scripts" / "verify_embeddings.py"
                env = os.environ.copy()
                if args.catalog:
                    env["ICONICS_DB"] = str(args.catalog)
                proc = subprocess.run([sys.executable, str(verify)], cwd=str(base_dir), env=env)
                if proc.returncode != 0:
                    sys.exit(proc.returncode)
                output.success("Verification passed")
                sys.exit(0)

        if args.command == 'synonyms':
            if args.synonyms_command == 'build':
                from iconics_synonyms import (
                    diff_synonyms_maps,
                    expand_synonyms_with_vision_model,
                    load_concept_synonyms_seed,
                    load_synonyms_json,
                    merge_synonyms_maps,
                    prune_synonyms_map,
                    validate_synonyms_map,
                )

                if args.input:
                    input_path: Path = args.input
                    if not input_path.is_absolute():
                        input_path = base_dir / input_path
                    input_map = load_synonyms_json(input_path)
                    if args.merge_seed:
                        seed_map = load_concept_synonyms_seed(base_dir)
                        seed = merge_synonyms_maps(input_map, seed_map)
                    else:
                        seed = input_map
                else:
                    seed = load_concept_synonyms_seed(base_dir)
                    data = seed

                before = dict(seed)

                if args.concept:
                    wanted = {str(c).strip().lower() for c in args.concept if str(c).strip()}
                    seed = {k: v for k, v in seed.items() if k.lower() in wanted}
                    if not seed:
                        output.error(f"No matching concepts found for: {sorted(wanted)}")
                        sys.exit(1)

                if args.use_model:
                    try:
                        from iconics_vision import VisionLabeler
                    except Exception as e:
                        output.error(f"Vision model not available: {e}")
                        sys.exit(1)

                    output.info("Expanding synonyms with local model (offline)")
                    labeler = VisionLabeler(
                        model_name=args.model,
                        device=args.device,
                        quantization=args.quantization,
                        embeddings_path=str(base_dir / "embeddings"),
                        subspace_path=str(base_dir / "subspace"),
                        catalog_path=str(executive.catalog.catalog_path),
                    )
                    data, stats = expand_synonyms_with_vision_model(seed, labeler=labeler, limit=int(args.limit))
                    output.success(f"Synonyms model run complete: concepts={stats.concepts}, updated={stats.updated}, errors={stats.errors}")
                else:
                    if args.limit and args.limit > 0:
                        keys = list(seed.keys())[: args.limit]
                        data = {k: seed[k] for k in keys}
                    else:
                        data = seed

                data = prune_synonyms_map(data, int(args.max_synonyms))

                issues = validate_synonyms_map(data)
                if issues:
                    output.warn(f"Synonyms validation: {len(issues)} issue(s)")
                    if args.verbose:
                        for issue in issues[:100]:
                            print(f"  - {issue}")
                    else:
                        output.info("Run with --verbose to see details")

                if args.dry_run:
                    import json as _json

                    print(_json.dumps(data, indent=2, sort_keys=True))
                    sys.exit(0)

                out_path: Path = args.out
                if not out_path.is_absolute():
                    out_path = base_dir / out_path
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
                output.success(f"Wrote synonyms: {out_path}")

                if args.report:
                    report_path: Path = args.report
                    if not report_path.is_absolute():
                        report_path = base_dir / report_path
                    report_path.parent.mkdir(parents=True, exist_ok=True)
                    diff = diff_synonyms_maps(before, data)
                    report_path.write_text(json.dumps(diff, indent=2, sort_keys=True), encoding="utf-8")
                    output.success(f"Wrote synonyms diff report: {report_path}")
                sys.exit(0)

            if args.synonyms_command == 'validate':
                from iconics_synonyms import load_synonyms_json, validate_synonyms_map

                p: Path = args.input
                if not p.is_absolute():
                    p = base_dir / p
                data = load_synonyms_json(p)
                issues = validate_synonyms_map(data)
                if issues:
                    output.error(f"Synonyms invalid: {len(issues)} issue(s) in {p}")
                    for issue in issues[:200]:
                        print(f"  - {issue}")
                    sys.exit(2)
                output.success(f"Synonyms OK: {p}")
                sys.exit(0)

            if args.synonyms_command == 'diff':
                from iconics_synonyms import diff_synonyms_maps, load_synonyms_json

                a = args.a if args.a.is_absolute() else (base_dir / args.a)
                b = args.b if args.b.is_absolute() else (base_dir / args.b)
                before = load_synonyms_json(a)
                after = load_synonyms_json(b)
                diff = diff_synonyms_maps(before, after)
                if args.json or mode == "json":
                    print(json.dumps(diff, indent=2, sort_keys=True))
                else:
                    changed = len(diff)
                    output.info(f"Changed concepts: {changed}")
                    for concept, d in list(diff.items())[:50]:
                        added = d.get("added", [])
                        removed = d.get("removed", [])
                        line = f"{concept}: +{len(added)} -{len(removed)}"
                        print(f"  {line}")
                sys.exit(0)

        # Hand off to Executive for command routing
        if args.command == 'search':
            query = ' '.join(args.query)
            results = []

            if executive.retriever:
                try:
                    # Use hybrid search by default for better results
                    if args.hybrid or not args.no_dedupe:
                        results = executive.retriever.retrieve_hybrid(
                            query,
                            k=args.limit,
                            dedupe=not args.no_dedupe,
                            catalog_path=executive.catalog.catalog_path,
                        )
                    else:
                        results = executive.retriever.retrieve(query, k=args.limit)
                except ModuleNotFoundError as e:
                    output.warn(f"CLIP dependency missing: {e}")
                    output.info("Falling back to metadata-only search")

            if not results:
                results = metadata_search(executive.catalog._catalog, query, limit=args.limit)

            if not results:
                output.warn(f"No results found for '{query}'")
                sys.exit(0)

            # Format and display results
            result_dicts = []
            for r in results:
                if isinstance(r, dict):
                    result_dicts.append(
                        {
                            "icon_id": r.get("icon_id", ""),
                            "score": r.get("score", 0.0),
                            "residual_score": r.get("residual_score", 0.0),
                        }
                    )
                else:
                    result_dicts.append(
                        {
                            "icon_id": r.icon_id,
                            "score": r.score,
                            "residual_score": getattr(r, "residual_score", 0.0),
                        }
                    )
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
            try:
                # Prefer Rust TUI2 (SQLite-backed)
                tui2 = base_dir / "bin" / "tui2"
                if not tui2.exists():
                    output.error(f"TUI2 launcher not found: {tui2}")
                    sys.exit(1)

                db_path = args.db or (base_dir / "iconics.sqlite3")
                if not db_path.exists():
                    script = base_dir / "scripts" / "migrate_catalog_to_sqlite.py"
                    if not script.exists():
                        output.error(f"Migration script not found: {script}")
                        sys.exit(1)

                    output.info(f"SQLite DB not found, creating: {db_path}")
                    create = subprocess.run(
                        [sys.executable, str(script), "--db", str(db_path)],
                        cwd=str(base_dir),
                    )
                    if create.returncode != 0:
                        output.error("Failed to create SQLite DB for TUI2")
                        sys.exit(create.returncode)

                env = os.environ.copy()
                env["ICONICS_DB"] = str(db_path)
                if args.query:
                    env["ICONICS_TUI_QUERY"] = args.query
                if args.category:
                    env["ICONICS_TUI_CATEGORY"] = args.category

                proc = subprocess.run([str(tui2)], cwd=str(base_dir), env=env)
                if proc.returncode != 0:
                    output.error(f"TUI2 exited with code {proc.returncode}")
                    sys.exit(proc.returncode)
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

            catalog = executive.catalog._catalog

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
                all_results = []

                if executive.retriever:
                    try:
                        # Use CLIP to find actual icons matching these terms
                        for term in suggestions[:args.limit]:
                            results = executive.retriever.retrieve(term, k=3)
                            for r in results:
                                if r.icon_id not in [x['icon_id'] for x in all_results]:
                                    all_results.append({'icon_id': r.icon_id, 'score': r.score, 'term': term})
                    except ModuleNotFoundError as e:
                        output.warn(f"CLIP dependency missing: {e}")

                if not all_results:
                    # Fallback: metadata-only matching for each term.
                    for term in suggestions[:args.limit]:
                        for r in metadata_search(executive.catalog._catalog, term, limit=3):
                            if r["icon_id"] not in [x["icon_id"] for x in all_results]:
                                all_results.append({"icon_id": r["icon_id"], "score": r["score"], "term": term})

                # Sort by score and dedupe
                seen = set()
                final_results = []
                for r in sorted(all_results, key=lambda x: x['score'], reverse=True):
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
                # Use CLIP search as fallback
                if executive.retriever:
                    try:
                        results = executive.retriever.retrieve(context, k=args.limit)
                        if results:
                            output.info(f"\nIcon suggestions for '{context}':\n")
                            for i, r in enumerate(results, 1):
                                print(f"  {i}. {r.icon_id}")
                        else:
                            output.warn(f"No icons found for context '{context}'")
                    except ModuleNotFoundError as e:
                        output.warn(f"CLIP dependency missing: {e}")
                        results = metadata_search(executive.catalog._catalog, context, limit=args.limit)
                        if results:
                            output.info(f"\nIcon suggestions for '{context}':\n")
                            for i, r in enumerate(results, 1):
                                print(f"  {i}. {r['icon_id']}")
                        else:
                            output.warn(f"No icons found for context '{context}'")
                else:
                    results = metadata_search(executive.catalog._catalog, context, limit=args.limit)
                    if results:
                        output.info(f"\nIcon suggestions for '{context}':\n")
                        for i, r in enumerate(results, 1):
                            print(f"  {i}. {r['icon_id']}")
                    else:
                        output.warn(f"No icons found for context '{context}'")

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
                    for base in [base_dir, base_dir / "raw", base_dir / "catalog"]:
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

            raw_path = base_dir / "raw"
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

        elif args.command == 'relabel':
            # Re-run vision labeling to fix taxonomy drift (SQLite-first)
            from iconics_relabel import (
                RelabelStats,
                apply_label_to_icon,
                iter_icons_for_relabel,
                resolve_icon_path,
            )

            repo_root = base_dir
            where_category = str(args.where_category).strip()
            if not where_category:
                output.error("--where-category cannot be empty")
                sys.exit(1)

            icons = list(iter_icons_for_relabel(executive.catalog._catalog, where_category=where_category))
            if args.limit and args.limit > 0:
                icons = icons[: args.limit]

            output.info(f"Relabeling {len(icons)} icon(s) where category='{where_category}'")
            if args.no_bypass:
                output.info("Mode: VLM forced (retrieval bypass disabled)")

            try:
                from iconics_vision import VisionLabeler
            except Exception as e:
                output.error(f"Vision labeler not available: {e}")
                sys.exit(1)

            # Force bypass off by setting threshold > 1.0 (similarities are <= 1.0)
            bypass_threshold = 2.0 if args.no_bypass else None

            labeler = VisionLabeler(
                model_name=args.model,
                device=args.device,
                quantization=args.quantization,
                embeddings_path=str(repo_root / "embeddings"),
                subspace_path=str(repo_root / "subspace"),
                catalog_path=str(executive.catalog.catalog_path),
                retrieval_bypass_threshold=bypass_threshold if bypass_threshold is not None else 0.92,
            )

            update_fields = ["category", "enrichment_confidence"]
            if args.full or args.update_tags:
                update_fields.append("tags")
            if args.full or args.update_description:
                update_fields.append("description")

            output.info(f"Updating fields: {', '.join(update_fields)}")

            stats = RelabelStats()
            changed_categories = 0

            for idx, icon in enumerate(icons, 1):
                icon_id = icon.get("id", "<missing-id>")
                src = resolve_icon_path(repo_root, icon)
                if src is None:
                    stats.skipped_no_path += 1
                    continue
                if not src.exists():
                    stats.skipped_missing_file += 1
                    continue

                try:
                    stats.processed += 1
                    label = labeler.label_icon(
                        src,
                        use_cache=bool(args.cache),
                        k_neighbors=int(args.k_neighbors),
                    ).to_dict()

                    updated = apply_label_to_icon(icon, label, update_fields=update_fields)
                    if updated.get("category") != icon.get("category"):
                        changed_categories += 1

                    if args.dry_run:
                        old_cat = icon.get("category")
                        new_cat = updated.get("category")
                        if old_cat != new_cat:
                            old_tags = icon.get("tags") or []
                            new_tags = updated.get("tags") or []
                            output.info(
                                f"[Dry run] {icon_id}: category {old_cat!r} -> {new_cat!r} "
                                f"(tags {len(old_tags)} -> {len(new_tags)})"
                            )

                    if not args.dry_run:
                        executive.catalog.update_entry(icon_id, updated)
                        stats.updated += 1

                    if idx % 25 == 0:
                        output.info(f"Progress: {idx}/{len(icons)} processed (updated={stats.updated}, errors={stats.errors})")

                except KeyboardInterrupt:
                    output.warn("Interrupted by user")
                    break
                except Exception as e:
                    stats.errors += 1
                    output.warn(f"{icon_id}: relabel failed: {e}")

            output.success(
                f"Relabel complete: processed={stats.processed}, updated={stats.updated}, "
                f"missing_file={stats.skipped_missing_file}, no_path={stats.skipped_no_path}, "
                f"errors={stats.errors}, category_changes={changed_categories}"
            )

        elif args.command == 'query':
            # Direct CLIP embedding query
            query_text = ' '.join(args.text)

            results = []
            if executive.retriever:
                try:
                    results = executive.retriever.retrieve(query_text, k=args.limit)
                except ModuleNotFoundError as e:
                    output.warn(f"CLIP dependency missing: {e}")

            if not results:
                results = metadata_search(executive.catalog._catalog, query_text, limit=args.limit)

            if not results:
                output.warn(f"No results for query: '{query_text}'")
                sys.exit(0)

            # Format output
            result_dicts = []
            for r in results:
                if isinstance(r, dict):
                    result_dicts.append(
                        {
                            "icon_id": r.get("icon_id", ""),
                            "score": r.get("score", 0.0),
                            "residual_score": r.get("residual_score", 0.0),
                        }
                    )
                else:
                    result_dicts.append(
                        {
                            "icon_id": r.icon_id,
                            "score": r.score,
                            "residual_score": getattr(r, "residual_score", 0.0),
                        }
                    )
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
