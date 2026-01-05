import os
import re
from PIL import Image

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from iconics_config import RAW_DIR
UPSCALED_DIR = RAW_DIR / '64x64'

def get_original_size(filename):
    path = os.path.join(RAW_DIR, filename)
    try:
        with Image.open(path) as img:
            return img.size[0] * img.size[1]
    except Exception:
        return 0

def get_id_from_filename(filename):
    # Remove extension
    stem = os.path.splitext(filename)[0]
    # Regex to capture ID before dimension suffix (e.g., name_32x32 -> name)
    # We assume dimensions are at the end like _12x12, _24x24
    match = re.match(r'^(.*)_\d+x\d+$', stem)
    if match:
        return match.group(1)
    return stem

def main():
    files = [f for f in os.listdir(UPSCALED_DIR) if f.endswith('.png')]
    print(f"Scanning {len(files)} upscaled files...")

    # Group by ID
    groups = {}
    for filename in files:
        file_id = get_id_from_filename(filename)
        if file_id not in groups:
            groups[file_id] = []
        
        original_area = get_original_size(filename)
        groups[file_id].append({
            'filename': filename,
            'area': original_area
        })

    deleted_count = 0
    kept_count = 0

    for file_id, candidates in groups.items():
        # Sort by:
        # 1. Area (descending) - primary goal
        # 2. Filename length (ascending) - tiebreaker: prefer "name.png" over "name_32x32.png"
        # 3. Filename (ascending) - deterministic tiebreaker
        candidates.sort(key=lambda x: (-x['area'], len(x['filename']), x['filename']))
        
        winner = candidates[0]
        losers = candidates[1:]

        # Keep the winner (do nothing, just verify it exists)
        kept_count += 1

        # Delete losers
        for loser in losers:
            path = os.path.join(UPSCALED_DIR, loser['filename'])
            try:
                os.remove(path)
                deleted_count += 1
                # print(f"Deleted {loser['filename']} (Source Area: {loser['area']}) in favor of {winner['filename']} (Source Area: {winner['area']})")
            except OSError as e:
                print(f"Error deleting {path}: {e}")

    print(f"\nCleanup complete.")
    print(f"Unique icons retained: {kept_count}")
    print(f"Redundant upscaled files removed: {deleted_count}")

if __name__ == '__main__':
    main()
