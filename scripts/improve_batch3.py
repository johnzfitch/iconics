#!/usr/bin/env python3
import csv

# Valid categories only
VALID_CATEGORIES = {'files', 'network', 'security', 'tools', 'ui', 'emoji', 'development'}

def improve_row(row):
    """Improve a single icon row"""
    semantic = row['semantic'].lower()
    
    # Improve categorization
    if any(x in semantic for x in ['doc', 'folder', 'page', 'file', 'book', 'pdf']):
        row['category'] = 'files'
    elif any(x in semantic for x in ['twitter', 'facebook', 'gmail', 'web', 'internet', 'mail', 'linkedin']):
        row['category'] = 'network'
    elif any(x in semantic for x in ['lock', 'key', 'secure', 'password', 'shield']):
        row['category'] = 'security'
    elif any(x in semantic for x in ['gear', 'hammer', 'wrench', 'settings', 'config', 'tool']):
        row['category'] = 'tools'
    elif any(x in semantic for x in ['code', 'develop', 'debug', 'compile', 'git', 'terminal']):
        row['category'] = 'development'
    elif any(x in semantic for x in ['smile', 'happy', 'sad', 'emoji', 'emotion', 'face']):
        row['category'] = 'emoji'
    else:
        row['category'] = 'ui'
    
    # Improve descriptions - remove "icon" suffix and make more descriptive
    if row['description'].endswith(' icon'):
        row['description'] = row['description'][:-5]
    
    return row

with open('batch3.csv', 'r', encoding='utf-8') as infile:
    reader = csv.DictReader(infile)
    rows = [improve_row(row) for row in reader]

with open('batch3_improved.csv', 'w', encoding='utf-8', newline='') as outfile:
    fieldnames = ['id', 'semantic', 'tags', 'category', 'description']
    writer = csv.DictWriter(outfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

from collections import Counter
cat_dist = Counter(row['category'] for row in rows)
print(f"Improved {len(rows)} icons -> batch3_improved.csv")
print("\nCategory distribution:")
for cat, count in sorted(cat_dist.items()):
    print(f"  {cat}: {count}")
