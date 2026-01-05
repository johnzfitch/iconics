#!/bin/bash
# Convert GIF files to PNG

OUTPUT_DIR="raw"
cd "$(dirname "$0")"

total=$(find raw/ -name "*.gif" 2>/dev/null | wc -l)
count=0

echo "Converting $total GIF files to PNG..."

find raw/ -name "*.gif" | while read -r gif; do
    count=$((count + 1))
    basename=$(basename "$gif" .gif)

    # Clean up basename
    clean_name=$(echo "$basename" | sed 's/[^a-zA-Z0-9_-]/_/g' | sed 's/__*/_/g')

    # Get dimensions
    dimensions=$(magick identify -format "%wx%h" "$gif" 2>/dev/null)

    if [ -n "$dimensions" ]; then
        # Convert to PNG
        magick "$gif" -background none -flatten "$OUTPUT_DIR/${clean_name}_${dimensions}.png" 2>/dev/null
        echo "[$count/$total] $basename -> ${clean_name}_${dimensions}.png"
    else
        echo "[$count/$total] SKIP: $basename (invalid)"
    fi
done

echo ""
echo "=== GIF Conversion Complete ==="
echo "Total GIF files processed: $total"
