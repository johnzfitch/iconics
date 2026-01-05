import os
import re
import numpy as np
from PIL import Image

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from iconics_config import RAW_DIR

def get_id_from_filename(filename):
    stem = os.path.splitext(filename)[0]
    match = re.match(r'^(.*)_\d+x\d+$', stem)
    if match:
        return match.group(1)
    return stem

def mse(imageA, imageB):
    # the 'Mean Squared Error' between the two images is the
    # sum of the squared difference between the two images;
    # NOTE: the two images must have the same dimension
    err = np.sum((imageA.astype("float") - imageB.astype("float")) ** 2)
    err /= float(imageA.shape[0] * imageA.shape[1])
    return err

def main():
    files = os.listdir(RAW_DIR)
    groups = {}
    for f in files:
        if not f.endswith('.png'): continue
        fid = get_id_from_filename(f)
        if fid not in groups: groups[fid] = []
        groups[fid].append(f)

    # Filter for groups with > 1 item
    multi_groups = {k: v for k, v in groups.items() if len(v) > 1}
    print(f"Found {len(multi_groups)} groups with multiple variations.")
    
    # Check a sample
    sample_size = 50
    discrepancies = []
    
    print(f"Checking visual similarity for {sample_size} random groups...")
    
    keys = list(multi_groups.keys())
    # deterministic sample for reproducibility
    keys.sort() 
    sample_keys = keys[:sample_size]

    for k in sample_keys:
        files = multi_groups[k]
        # Load all images in group
        images = []
        try:
            for f in files:
                path = os.path.join(RAW_DIR, f)
                img = Image.open(path).convert('RGBA')
                images.append((f, img))
        except Exception as e:
            print(f"Error loading group {k}: {e}")
            continue

        # Compare every pair in the group
        # We resize the larger one down to the smaller one to compare content structure? 
        # Or smaller to larger? 
        # Usually verifying if a small icon is a downscaled version of a large one:
        # Resizing the LARGE one DOWN to the small one is usually a better check for consistency
        # than upsizing the small (which is blurry).
        
        base_file, base_img = images[0]
        
        for i in range(1, len(images)):
            comp_file, comp_img = images[i]
            
            # Determine which is larger
            if base_img.size[0] * base_img.size[1] > comp_img.size[0] * comp_img.size[1]:
                big, small = base_img, comp_img
                big_name, small_name = base_file, comp_file
            else:
                big, small = comp_img, base_img
                big_name, small_name = comp_file, base_file
                
            # Resize big to small size for comparison
            big_downscaled = big.resize(small.size, Image.Resampling.LANCZOS)
            
            # Convert to numpy arrays
            arr1 = np.array(big_downscaled)
            arr2 = np.array(small)
            
            # MSE
            err = mse(arr1, arr2)
            
            # Threshold? 
            # If icons are totally different, MSE will be huge (e.g. > 2000).
            # If they are same icon but just pixel-art differences at low res, MSE might be moderate (100-500).
            # If identical, near 0.
            
            print(f"Comparing {big_name} vs {small_name}: MSE = {err:.2f}")
            
            if err > 1000: # Arbitrary high threshold for "totally different image"
                discrepancies.append((big_name, small_name, err))

    print("-" * 30)
    if discrepancies:
        print(f"WARNING: Found {len(discrepancies)} pairs that look significantly different!")
        for d in discrepancies:
            print(f"  {d[0]} vs {d[1]} (MSE: {d[2]:.2f})")
    else:
        print("Verification Passed: All sampled pairs appear to be visual variants of the same icon.")

if __name__ == "__main__":
    main()
