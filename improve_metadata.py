#!/usr/bin/env python3
"""
Quick script to improve icon metadata in bulk for batch2.csv
"""

import csv
import re

# Category mapping patterns
category_patterns = {
    'tools': ['camera', 'canon', 'powerbook', 'powermac', 'ipod', 'nano', 'scanner', 'printer', 'screwdriver', 'ruler', 'pen-tool', 'paint', 'editor', 'player', 'browser'],
    'network': ['network', 'rss', 'reddit', 'pinterest', 'safari', 'opera'],
    'emoji': ['owl', 'piggy', 'peace', 'smile', 'poo', 'pirate', 'pets'],
    'files': ['file', 'folder', 'document', 'book', 'picture', 'image', 'save'],
    'security': ['safe', 'no-entry'],
    'development': ['pixel', 'rgb'],
}

def improve_row(row):
    """Improve a single row of icon metadata"""
    icon_id, semantic, tags, category, description = row

    # Skip header
    if icon_id == 'id':
        return row

    # Clean up semantic name
    semantic_clean = semantic.lower().replace(' ', '-').replace('_', '-')
    semantic_clean = re.sub(r'[()]', '', semantic_clean)

    # Improve category based on semantic name
    for cat, patterns in category_patterns.items():
        if any(pattern in semantic_clean for pattern in patterns):
            category = cat
            break

    # Add more descriptive tags based on semantic name
    tag_list = [t.strip() for t in tags.split(',') if t.strip()]

    # Add generic relevant tags based on common patterns
    if 'player' in semantic_clean and 'media' not in tag_list:
        tag_list.extend(['media', 'control'])
    if 'save' in semantic_clean and 'file' not in tag_list:
        tag_list.append('file')
    if 'rotate' in semantic_clean and 'transform' not in tag_list:
        tag_list.append('transform')
    if 'power' in semantic_clean and 'mac' in semantic_clean:
        tag_list.extend(['apple', 'desktop', 'computer'])
    if 'book' in semantic_clean and 'laptop' not in semantic_clean:
        tag_list.extend(['apple', 'laptop'])

    # Remove duplicates while preserving order
    seen = set()
    tag_list = [x for x in tag_list if not (x in seen or seen.add(x))]

    tags_clean = ','.join(tag_list[:8])  # Limit to 8 tags

    # Improve description
    if description.endswith(' icon'):
        description = description[:-5]  # Remove generic " icon" suffix

    if not description or description == semantic:
        # Generate better description
        desc_parts = semantic.replace('-', ' ').replace('_', ' ').split()
        description = ' '.join(desc_parts).title() + ' icon'

    return [icon_id, semantic_clean, tags_clean, category, description]

def main():
    input_file = '/home/zack/dev/iconics/batch2.csv'
    output_file = '/home/zack/dev/iconics/batch2_improved.csv'

    rows = []
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) == 5:
                improved = improve_row(row)
                rows.append(improved)

    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    print(f"✓ Improved {len(rows)-1} icons")
    print(f"✓ Saved to: {output_file}")

if __name__ == '__main__':
    main()
