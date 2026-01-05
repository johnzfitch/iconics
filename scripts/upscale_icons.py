import os
from PIL import Image

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from iconics_config import RAW_DIR
SOURCE_DIR = RAW_DIR
DEST_DIR = RAW_DIR / '64x64'
TARGET_SIZE = (64, 64)

def main():
    # 1. Create output directory
    if not os.path.exists(DEST_DIR):
        os.makedirs(DEST_DIR)
        print(f"Created output directory: {DEST_DIR}")

    processed_count = 0
    skipped_count = 0
    errors = []

    # 2. Process all files
    files = os.listdir(SOURCE_DIR)
    
    print(f"Found {len(files)} files in source directory.")

    for filename in files:
        if not filename.lower().endswith('.png'):
            continue
            
        # 4. Skip files that are already 64x64 (based on name)
        if '64x64' in filename:
            skipped_count += 1
            continue

        source_path = os.path.join(SOURCE_DIR, filename)
        dest_path = os.path.join(DEST_DIR, filename)

        try:
            with Image.open(source_path) as img:
                # Check actual size just in case (optional, but good for validation)
                # if img.size == TARGET_SIZE:
                #     skipped_count += 1
                #     continue
                
                # 3. Upscale
                # Use nearest neighbor to preserve pixel sharpness
                resized_img = img.resize(TARGET_SIZE, resample=Image.Resampling.NEAREST)
                
                # Save
                resized_img.save(dest_path)
                processed_count += 1
                
                if processed_count % 100 == 0:
                    print(f"Processed {processed_count} images...", end='\r')

        except Exception as e:
            errors.append(f"Error processing {filename}: {str(e)}")

    print(f"\nProcessing complete.")
    print(f"Successfully processed: {processed_count}")
    print(f"Skipped (name match): {skipped_count}")
    
    if errors:
        print(f"Errors encountered: {len(errors)}")
        for err in errors[:5]:
            print(err)

if __name__ == '__main__':
    main()
