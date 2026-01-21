#!/usr/bin/env bash
# Simple test to verify the SQLite catalog loads correctly

set -euo pipefail

TUI_DIR="$(cd "$(dirname "$0")" && pwd)"
ICONICS_ROOT="${ICONICS_ROOT:-$(cd "$TUI_DIR/.." && pwd)}"
DB="${ICONICS_DB:-$ICONICS_ROOT/iconics.sqlite3}"
BINARY="./target/release/iconics-tui2"

cd "$TUI_DIR"

echo "Testing Iconics TUI2 (SQLite) implementation..."
echo

# Check DB exists
echo "1. Checking SQLite DB exists..."
if [[ ! -f "$DB" ]]; then
    echo "   ERROR: DB not found at $DB"
    exit 1
fi
echo "   OK: Found DB ($(stat -c%s "$DB" | numfmt --to=iec-i)B)"

# Check binary exists
echo "2. Checking binary exists..."
if [[ ! -f "$BINARY" ]]; then
    echo "   ERROR: Binary not found. Run 'cargo build --release' first"
    exit 1
fi
echo "   OK: Binary found ($(stat -c%s "$BINARY" | numfmt --to=iec-i)B)"

# Validate SQLite schema + sample files without relying on sqlite3 CLI
echo "3. Validating schema, counts, and sample files..."
python3 - "$DB" "$ICONICS_ROOT" <<'PY'
import sqlite3
import sys
from pathlib import Path

db_path = Path(sys.argv[1])
root = Path(sys.argv[2])

conn = sqlite3.connect(str(db_path))
cur = conn.cursor()

tables = {row[0] for row in cur.execute("SELECT name FROM sqlite_master WHERE type='table'")}
required = {"icons", "icon_tags", "icon_used_in"}
missing = sorted(required - tables)
if missing:
    raise SystemExit(f"Missing required tables: {missing}")

icon_count = cur.execute("SELECT COUNT(*) FROM icons").fetchone()[0]
if icon_count <= 0:
    raise SystemExit("icons table is empty")

sample = cur.execute(
    "SELECT COALESCE(filename, source_file) FROM icons WHERE COALESCE(filename, source_file) IS NOT NULL LIMIT 10"
).fetchall()
if not sample:
    raise SystemExit("No sample icons with paths found")

missing_files = []
for (rel_path,) in sample:
    path = root / rel_path
    if not path.is_file():
        missing_files.append(str(path))

if missing_files:
    raise SystemExit("Missing icon files:\n" + "\n".join(missing_files))

print(f"   OK: icons={icon_count}, sampled_files={len(sample)}")
PY

echo
echo "All tests passed! The TUI should work correctly."
echo
echo "To run the TUI:"
echo "  cd /home/zack/dev/iconics && ./bin/tui2"
echo
echo "Or directly:"
echo "  cd /home/zack/dev/iconics/tui2 && cargo run --release"
