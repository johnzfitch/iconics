#!/bin/bash
# Convert ICO files to PNG, extracting all sizes and labeling them

OUTPUT_DIR="raw/converted-from-ico"
mkdir -p "$OUTPUT_DIR"

total=$(ls -1 *.ico 2>/dev/null | wc -l)
count=0

echo "Converting $total ICO files to PNG with size labels..."

for ico in *.ico; do
    count=$((count + 1))
    basename="${ico%.ico}"

    # Clean up basename (remove spaces, special chars)
    clean_name=$(echo "$basename" | sed 's/[^a-zA-Z0-9_-]/_/g' | sed 's/__*/_/g')

    # Get number of images in ICO file
    num_images=$(magick identify "$ico" 2>/dev/null | wc -l)

    if [ "$num_images" -eq 0 ]; then
        echo "[$count/$total] SKIP: $ico (invalid)"
        continue
    fi

    # Extract each size
    if [ "$num_images" -eq 1 ]; then
        # Single image - get dimensions
        dimensions=$(magick identify -format "%wx%h" "$ico[0]" 2>/dev/null)
        if [ -n "$dimensions" ]; then
            magick "$ico[0]" -background none -flatten "$OUTPUT_DIR/${clean_name}_${dimensions}.png" 2>/dev/null
            echo "[$count/$total] $ico -> ${clean_name}_${dimensions}.png"
        fi
    else
        # Multiple images - extract each
        for i in $(seq 0 $((num_images - 1))); do
            dimensions=$(magick identify -format "%wx%h" "$ico[$i]" 2>/dev/null)
            if [ -n "$dimensions" ]; then
                magick "$ico[$i]" -background none -flatten "$OUTPUT_DIR/${clean_name}_${dimensions}.png" 2>/dev/null
            fi
        done
        echo "[$count/$total] $ico -> extracted $num_images sizes"
    fi
done

echo ""
echo "=== Conversion Complete ==="
echo "Total ICO files processed: $total"
echo "PNG files created: $(ls -1 $OUTPUT_DIR/*.png 2>/dev/null | wc -l)"
