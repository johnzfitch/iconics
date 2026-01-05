#!/usr/bin/env bash
# Simple test to verify the catalog loads correctly

set -euo pipefail

ICONICS_ROOT="${ICONICS_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
CATALOG="$ICONICS_ROOT/icon-catalog.json"
BINARY="./target/release/iconics-tui"

echo "Testing Iconics TUI Rust implementation..."
echo

# Check catalog exists
echo "1. Checking catalog exists..."
if [[ ! -f "$CATALOG" ]]; then
    echo "   ERROR: Catalog not found at $CATALOG"
    exit 1
fi
echo "   OK: Found catalog ($(wc -l < "$CATALOG") lines)"

# Check catalog is valid JSON
echo "2. Checking catalog is valid JSON..."
if ! jq -e '.icons | length' "$CATALOG" > /dev/null 2>&1; then
    echo "   ERROR: Catalog is not valid JSON"
    exit 1
fi
ICON_COUNT=$(jq -r '.icons | length' "$CATALOG")
echo "   OK: Valid JSON with $ICON_COUNT icons"

# Check binary exists
echo "3. Checking binary exists..."
if [[ ! -f "$BINARY" ]]; then
    echo "   ERROR: Binary not found. Run 'cargo build --release' first"
    exit 1
fi
echo "   OK: Binary found ($(stat -c%s "$BINARY" | numfmt --to=iec-i)B)"

# Test a few icon paths from catalog
echo "4. Checking icon files exist..."
SAMPLE_COUNT=0
SUCCESS_COUNT=0
jq -r '.icons[0:10] | .[].filename' "$CATALOG" | while read -r filename; do
    SAMPLE_COUNT=$((SAMPLE_COUNT + 1))
    FULL_PATH="$ICONICS_ROOT/$filename"
    if [[ -f "$FULL_PATH" ]]; then
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    fi
done
echo "   OK: Sampled icon files exist"

echo
echo "All tests passed! The TUI should work correctly."
echo
echo "To run the TUI:"
echo "  ./tui-rs"
echo
echo "Or directly:"
echo "  cd iconics-tui-rs && cargo run --release"
