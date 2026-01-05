#!/usr/bin/env bash
# Iconics Project Structure Migration
# Reorganizes directory structure, removes hardcoded paths, adds environment config
#
# Usage:
#   ./scripts/migrate-structure.sh --dry-run   # Preview changes
#   ./scripts/migrate-structure.sh             # Execute migration

set -euo pipefail

DRY_RUN=false
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=true

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

log() { echo "[$(date +%H:%M:%S)] $*"; }
run() {
    if $DRY_RUN; then
        echo "[DRY-RUN] $*"
    else
        eval "$@"
    fi
}

if $DRY_RUN; then
    log "==== DRY RUN MODE - No changes will be made ===="
else
    log "==== EXECUTING MIGRATION ===="
fi

# ==============================================================================
# Phase 1: Create new directories
# ==============================================================================
log "[1/9] Creating new directories..."
run "mkdir -p bin"
run "mkdir -p docs/archive"
run "mkdir -p legacy"

# ==============================================================================
# Phase 2: Move/rename directories
# ==============================================================================
log "[2/9] Reorganizing directories..."

# Rename Rust TUI (remove old tui file first if it exists)
if [ -d "iconics-tui-rs" ]; then
    # Remove old tui launcher file/directory if it exists
    if [ -e "tui" ]; then
        run "rm -rf tui"
    fi
    run "mv iconics-tui-rs tui"
elif [ -d "tui" ]; then
    log "  ✓ tui directory already exists (migration already run)"
fi

# Remove old launchers
if [ -f "tui-rs" ]; then
    run "rm -f tui-rs"
fi

# Move refactor docs to archive
if [ -d "refactor" ]; then
    run "mv refactor docs/archive/"
fi

# ==============================================================================
# Phase 3: Move utility scripts to scripts/
# ==============================================================================
log "[3/9] Moving utility scripts to scripts/..."

# Python scripts
for script in deduplicate_icons.py upscale_icons.py verify_duplicates.py \
              verify_embeddings.py improve_csv.py improve_batch3.py \
              improve_metadata.py generate_all_embeddings.py \
              run_subspace_analysis.py; do
    if [ -f "$script" ]; then
        run "mv '$script' scripts/"
    fi
done

# Shell scripts
for script in convert-gif-to-png.sh convert-ico-to-png.sh; do
    if [ -f "$script" ]; then
        run "mv '$script' scripts/"
    fi
done

# ==============================================================================
# Phase 4: Move documentation files
# ==============================================================================
log "[4/9] Organizing documentation..."

# Move docs to docs/
for doc in QUICK_START.md SETUP.md ICON_MANAGEMENT_PLAN.md \
           ICON-SOURCES.md HANDOFF.md agents.md; do
    if [ -f "$doc" ]; then
        run "mv '$doc' docs/"
    fi
done

# Move to docs/archive/
for doc in CLI_CONSOLIDATION_ANALYSIS.md TESTING_SUMMARY.md \
           validation_report.md final_validation_report.md \
           VARIANT_GROUPING_IMPLEMENTATION.md TUI_IMPLEMENTATION.md \
           TUI_QUICKSTART.md TUI_STATUS.md TUI_TESTING_CHECKLIST.md; do
    if [ -f "$doc" ]; then
        run "mv '$doc' docs/archive/"
    fi
done

# Move Rust TUI docs to tui/ (after rename)
for doc in WHY_RUST_TUI.md RUST_TUI_IMPLEMENTATION.md; do
    if [ -f "$doc" ]; then
        run "mv '$doc' tui/"
    fi
done

# Move legacy vendor files to legacy/
for file in "32px Vol. 1.icontainer" "530-boxy-social-icons-2.jpg" \
            "680-boxy-social-icons-2.jpg" "Display.jpg" "Help.chm" \
            "Icon archive PSD.psd" "Image Licence.pdf" "Readme.rtf" \
            "boxy-social-icons-2.psd" "credits.txt" \
            "free icons (www.awicons.com).url" \
            "icons (www.awicons.com).url" "icons.txt" "index.url" \
            "small-homeware-icons.pdf" "icon-editor.exe" \
            "license.txt" "License.txt" "readme.txt"; do
    if [ -f "$file" ]; then
        run "mv '$file' legacy/"
    fi
done

# ==============================================================================
# Phase 5: Delete obsolete files and directories
# ==============================================================================
log "[5/9] Deleting obsolete files and directories..."

# Delete directories
for dir in pyghidra_mcp_projects "files(71)" index nanobanana-output \
           tmp tests/fixtures tests/integration archive; do
    if [ -d "$dir" ]; then
        run "rm -rf '$dir'"
    fi
done

# Delete Python TUI (replaced by Rust)
if [ -d "src/iconics_tui" ]; then
    run "rm -rf src/iconics_tui"
fi
if [ -f "src/iconics_tui.py" ]; then
    run "rm -f src/iconics_tui.py"
fi

# Delete batch CSV files
run "rm -f batch*.csv *_improved.csv enrichment_verification*.csv"
run "rm -f final-batch.csv new-icons*.csv new-icons-batch.csv remaining.csv"
run "rm -f win2k-import-*.csv icon-import-template.csv"

# Delete backup files
run "rm -f icon-manager.py.orig"
run "rm -f src/iconics_vision.py.bak src/iconics_vision.py.bak2"
run "rm -f icon-catalog.json.bak.*"

# Delete macOS resource forks
run "rm -f ._*"

# Delete archive files
run "rm -f gif-archive-*.zip ico-archive-*.zip src.zip"

# Delete logs and generated files
run "rm -f *.log gallery.html conversion-test.log setup_vision.log import-test.log"

# Delete duplicate launchers (only if files, not directories)
if [ -f "tui" ]; then
    run "rm -f tui"
fi
if [ -f "tui-rs" ]; then
    run "rm -f tui-rs"
fi

# Delete minimal unused files
run "rm -f main.py"

# ==============================================================================
# Phase 6: Create new configuration files
# ==============================================================================
log "[6/9] Creating new configuration files..."

# Create .env.example
if $DRY_RUN; then
    echo "[DRY-RUN] cat > .env.example << 'EOF'"
    echo "[DRY-RUN] (environment configuration template)"
else
    cat > .env.example << 'EOF'
# Iconics Environment Configuration
# Copy to .env and customize

# Base directory (auto-detected if not set)
# Default: Git root or parent of this file
# ICONICS_ROOT=/path/to/iconics

# CLIP Model Configuration
ICONICS_CLIP_MODEL=ViT-B-32
ICONICS_PRETRAINED=laion2b_s34b_b79k
ICONICS_DEVICE=cuda

# Python interpreter (for icon bash script)
ICONICS_PYTHON=python3

# Logging
ICONICS_LOG_LEVEL=INFO

# Vision/VLM (optional)
# ICONICS_VLM_ENDPOINT=http://localhost:8080
# ICONICS_VLM_MODEL=llava

# Future secrets (not currently used)
# ICONICS_API_KEY=
EOF
fi

# Create src/iconics_config.py
if $DRY_RUN; then
    echo "[DRY-RUN] cat > src/iconics_config.py << 'PYEOF'"
    echo "[DRY-RUN] (centralized path configuration module)"
else
    cat > src/iconics_config.py << 'PYEOF'
"""
Iconics Configuration - Centralized path and config management

Resolution order:
1. Environment variable (ICONICS_ROOT)
2. Git repository root (if in repo)
3. Parent of current file's directory
"""

import os
from pathlib import Path
from functools import lru_cache


@lru_cache(maxsize=1)
def get_iconics_root() -> Path:
    """Get the Iconics root directory using multiple detection methods."""
    # 1. Environment variable
    if env_root := os.environ.get('ICONICS_ROOT'):
        return Path(env_root).resolve()

    # 2. Git root detection
    try:
        import subprocess
        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent,
            check=False
        )
        if result.returncode == 0:
            return Path(result.stdout.strip())
    except Exception:
        pass

    # 3. Relative to this file (src/iconics_config.py -> parent is iconics/)
    return Path(__file__).parent.parent.resolve()


# Root directory
ICONICS_ROOT = get_iconics_root()

# Derived paths
RAW_DIR = ICONICS_ROOT / "raw"
CATALOG_FILE = ICONICS_ROOT / "icon-catalog.json"
CATALOG_DIR = ICONICS_ROOT / "catalog"
EMBEDDINGS_DIR = ICONICS_ROOT / "embeddings"
SUBSPACE_DIR = ICONICS_ROOT / "subspace"
EVAL_DIR = ICONICS_ROOT / "eval"
HISTORY_FILE = ICONICS_ROOT / ".icon-history.json"
ANALYTICS_FILE = ICONICS_ROOT / ".icon-analytics.json"
CONFIG_FILE = ICONICS_ROOT / "config.yaml"
TEMPLATES_FILE = ICONICS_ROOT / "icon-templates.json"


# Environment configuration
CLIP_MODEL = os.environ.get('ICONICS_CLIP_MODEL', 'ViT-B-32')
PRETRAINED = os.environ.get('ICONICS_PRETRAINED', 'laion2b_s34b_b79k')
DEVICE = os.environ.get('ICONICS_DEVICE', 'cuda')
LOG_LEVEL = os.environ.get('ICONICS_LOG_LEVEL', 'INFO')
PYEOF
fi

# Create bin/tui launcher
if $DRY_RUN; then
    echo "[DRY-RUN] cat > bin/tui << 'EOF'"
    echo "[DRY-RUN] (Rust TUI launcher script)"
else
    cat > bin/tui << 'EOF'
#!/usr/bin/env bash
# Iconics TUI Launcher
# Auto-builds if needed, then launches the Rust TUI

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TUI_DIR="$SCRIPT_DIR/tui"

cd "$TUI_DIR"

# Build if binary doesn't exist or source is newer
if [[ ! -f target/release/iconics-tui ]] || [[ src/main.rs -nt target/release/iconics-tui ]]; then
    echo "Building iconics-tui..."
    cargo build --release
fi

exec target/release/iconics-tui "$@"
EOF
    chmod +x bin/tui
fi

# ==============================================================================
# Phase 7: Update hardcoded paths with sed
# ==============================================================================
log "[7/9] Updating hardcoded paths in source files..."

# Update icon-manager.py shebang and imports
run "sed -i '1s|#!/home/zack/.local/share/python-global/bin/python|#!/usr/bin/env python3|' icon-manager.py"
run "sed -i '20,25d' icon-manager.py"  # Delete lines 20-25 (old path constants)
run "sed -i '19a\\from src.iconics_config import (\\n    ICONICS_ROOT as ICON_DIR,\\n    CATALOG_FILE,\\n    RAW_DIR,\\n    CATALOG_DIR,\\n    HISTORY_FILE,\\n    ANALYTICS_FILE\\n)' icon-manager.py"

# Update icon bash script
run "sed -i 's|ICONICS_DIR=\"/home/zack/dev/iconics\"|ICONICS_DIR=\"\${ICONICS_ROOT:-\$(cd \"\$(dirname \"\$0\")\" \&\& pwd)}\"|' icon"
run "sed -i 's|PYTHON=\"/home/zack/.local/share/python-global/bin/python\"|PYTHON=\"\${ICONICS_PYTHON:-python3}\"|' icon"

# Update config.yaml
run "sed -i 's|workspace: \"/home/zack/dev/iconics\"|# workspace: auto-detected via ICONICS_ROOT env var or git root|' config.yaml"

# Update scripts that moved to scripts/
if [ -f "scripts/deduplicate_icons.py" ]; then
    run "sed -i \"5,6d\" scripts/deduplicate_icons.py"
    run "sed -i \"4a\\import sys\\nsys.path.insert(0, str(Path(__file__).parent.parent / 'src'))\\nfrom iconics_config import RAW_DIR\\nUPSCALED_DIR = RAW_DIR / '64x64'\" scripts/deduplicate_icons.py"
fi

if [ -f "scripts/upscale_icons.py" ]; then
    run "sed -i \"4,5d\" scripts/upscale_icons.py"
    run "sed -i \"3a\\import sys\\nsys.path.insert(0, str(Path(__file__).parent.parent / 'src'))\\nfrom iconics_config import RAW_DIR\\nSOURCE_DIR = RAW_DIR\\nDEST_DIR = RAW_DIR / '64x64'\" scripts/upscale_icons.py"
fi

if [ -f "scripts/verify_duplicates.py" ]; then
    run "sed -i \"6d\" scripts/verify_duplicates.py"
    run "sed -i \"5a\\import sys\\nsys.path.insert(0, str(Path(__file__).parent.parent / 'src'))\\nfrom iconics_config import RAW_DIR\" scripts/verify_duplicates.py"
fi

if [ -f "scripts/generate_all_embeddings.py" ]; then
    run "sed -i \"5d; 15d\" scripts/generate_all_embeddings.py"
    run "sed -i \"14a\\from iconics_config import ICONICS_ROOT as workspace\" scripts/generate_all_embeddings.py"
fi

if [ -f "scripts/rename_with_descriptors.py" ]; then
    run "sed -i \"16d\" scripts/rename_with_descriptors.py"
    run "sed -i \"15a\\import sys\\nsys.path.insert(0, str(Path(__file__).parent.parent / 'src'))\\nfrom iconics_config import RAW_DIR\" scripts/rename_with_descriptors.py"
fi

# Update library modules (only __main__ blocks)
if [ -f "src/iconics_correlation.py" ]; then
    run "sed -i 's|base_dir = Path(\"/home/zack/dev/iconics\")|from iconics_config import ICONICS_ROOT\\n    base_dir = ICONICS_ROOT|' src/iconics_correlation.py"
fi

if [ -f "src/iconics_subspace.py" ]; then
    run "sed -i 's|base_dir = Path(\"/home/zack/dev/iconics\")|from iconics_config import ICONICS_ROOT\\n    base_dir = ICONICS_ROOT|' src/iconics_subspace.py"
fi

if [ -f "src/iconics_embeddings.py" ]; then
    run "sed -i 's|workspace = Path(\"/home/zack/dev/iconics\")|from iconics_config import ICONICS_ROOT\\n    workspace = ICONICS_ROOT|' src/iconics_embeddings.py"
fi

# Update shell scripts
if [ -f "examples/pre-commit-hook.sh" ]; then
    run "sed -i 's|/home/zack/dev/iconics/icon|\$ICONICS_ROOT/icon|g' examples/pre-commit-hook.sh"
fi

if [ -f "tui/test-catalog.sh" ]; then
    run "sed -i 's|CATALOG=\"/home/zack/dev/iconics/icon-catalog.json\"|ICONICS_ROOT=\"\${ICONICS_ROOT:-\$(cd \"\$(dirname \"\$0\")/..\" \&\& pwd)}\"\\nCATALOG=\"\$ICONICS_ROOT/icon-catalog.json\"|' tui/test-catalog.sh"
    run "sed -i 's|FULL_PATH=\"/home/zack/dev/iconics/\$filename\"|FULL_PATH=\"\$ICONICS_ROOT/\$filename\"|' tui/test-catalog.sh"
fi

# ==============================================================================
# Phase 8: Update .gitignore
# ==============================================================================
log "[8/9] Updating .gitignore..."

if $DRY_RUN; then
    echo "[DRY-RUN] cat >> .gitignore << 'EOF'"
    echo "[DRY-RUN] (adding environment and cache patterns)"
else
    cat >> .gitignore << 'EOF'

# Environment
.env
.env.local
.env.*.local

# Batch CSVs (legacy)
batch*.csv
*_improved.csv
enrichment_verification*.csv
remaining.csv
final-batch.csv
new-icons*.csv
*-import-*.csv

# Caches
vision_cache/
tui/target/

# History (local)
.icon-history.json
.icon-analytics.json

# Temporary files
*.log
*.tmp
*.orig
*.bak
*.bak2
gallery.html
EOF
fi

# ==============================================================================
# Phase 9: Add catalog versioning
# ==============================================================================
log "[9/9] Adding catalog versioning..."

if $DRY_RUN; then
    echo "[DRY-RUN] python3 -c 'add version wrapper to icon-catalog.json'"
else
    python3 << 'PYEOF'
import json
from datetime import datetime
from pathlib import Path

catalog_file = Path('icon-catalog.json')

with open(catalog_file) as f:
    data = json.load(f)

# Only migrate if not already versioned
if 'version' not in data:
    print("  Migrating catalog to v2.0 format...")
    versioned_data = {
        'version': '2.0',
        'created': datetime.now().isoformat(),
        'last_modified': datetime.now().isoformat(),
        'icon_count': len(data.get('icons', data)),
        'icons': data.get('icons', data)
    }

    with open(catalog_file, 'w') as f:
        json.dump(versioned_data, f, indent=2)

    print(f"  ✓ Catalog versioned: {versioned_data['icon_count']} icons")
else:
    print("  ✓ Catalog already versioned")
PYEOF
fi

# ==============================================================================
# Test that iconics still works (non-dry-run only)
# ==============================================================================

if ! $DRY_RUN; then
    log ""
    log "[TEST] Verifying iconics functionality..."

    # Test 1: icon stats
    log "  Testing: icon stats"
    if ./icon stats &>/dev/null; then
        log "  ✓ icon stats works"
    else
        log "  ✗ ERROR: icon stats failed"
        exit 1
    fi

    # Test 2: icon search
    log "  Testing: icon search test"
    if ./icon search test | grep -q "Found.*icon"; then
        log "  ✓ icon search works"
    else
        log "  ✗ ERROR: icon search failed"
        exit 1
    fi

    # Test 3: Check Python imports
    log "  Testing: Python module imports"
    if python3 -c "from src.iconics_config import ICONICS_ROOT; print(ICONICS_ROOT)" &>/dev/null; then
        log "  ✓ Python imports work"
    else
        log "  ✗ ERROR: Python imports failed"
        exit 1
    fi
fi

# ==============================================================================
# Complete
# ==============================================================================

if $DRY_RUN; then
    log ""
    log "==== DRY RUN COMPLETE ===="
    log ""
    log "Review the operations above, then run without --dry-run to execute"
    log ""
    log "To execute migration:"
    log "  ./scripts/migrate-structure.sh"
else
    log ""
    log "==== MIGRATION COMPLETE ===="
    log ""
    log "✓ All tests passed"
    log ""
    log "Next steps:"
    log "  1. Review changes: git status"
    log "  2. Test interactively: icon suggest security"
    log "  3. Commit: git add -A && git commit -m 'refactor: reorganize project structure'"
fi
