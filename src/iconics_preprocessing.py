"""
Pixel-Perfect Icon Preprocessing for Vision Models
Handles tiny glyphs (16x16 to 48x48) by upscaling and creating multi-matte composites
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from pathlib import Path
from typing import Tuple, Optional
from functools import lru_cache
import hashlib

# VLM optimal input size (empirically determined for Qwen2.5-VL and InternVL)
TARGET_SIZE = 336


def _get_file_hash(icon_path: Path) -> str:
    """Get hash of file for caching."""
    with open(icon_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()


def load_icon(icon_path: Path) -> Image.Image:
    """
    Load icon image and ensure RGBA format.

    Args:
        icon_path: Path to icon file (PNG)

    Returns:
        PIL Image in RGBA mode
    """
    img = Image.open(icon_path)

    # Convert to RGBA if needed
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    return img

def upscale_nearest_neighbor(img: Image.Image, target_size: int = TARGET_SIZE) -> Image.Image:
    """
    Upscale image using nearest-neighbor interpolation (pixel-perfect).

    Args:
        img: Source image
        target_size: Target dimension (will scale to fit within this square)

    Returns:
        Upscaled image
    """
    # Calculate scale factor to fit within target_size
    width, height = img.size
    max_dim = max(width, height)

    if max_dim >= target_size:
        # Already large enough, return as-is
        return img

    # Calculate integer scale factor (prefer whole-number scaling for pixel art)
    scale_factor = target_size // max_dim

    # Use NEAREST resampling (preserves pixel edges)
    new_size = (width * scale_factor, height * scale_factor)
    return img.resize(new_size, Image.Resampling.NEAREST)

def create_matte(img: Image.Image, background_color: Tuple[int, int, int, int]) -> Image.Image:
    """
    Composite image onto solid color background.

    Args:
        img: Source RGBA image
        background_color: RGBA tuple (e.g., (128, 128, 128, 255) for gray)

    Returns:
        Composited image
    """
    # Create background
    bg = Image.new('RGBA', img.size, background_color)

    # Composite using alpha channel
    composited = Image.alpha_composite(bg, img)

    return composited

def get_tight_crop(img: Image.Image, padding: int = 4) -> Image.Image:
    """
    Crop to bounding box of non-transparent pixels.

    Args:
        img: Source RGBA image
        padding: Extra padding around bounding box

    Returns:
        Cropped image
    """
    # Use PIL's native getbbox() - faster than numpy
    # getbbox() returns (left, upper, right, lower) of non-zero regions
    bbox = img.split()[-1].getbbox()  # Get bbox of alpha channel
    
    if bbox is None:
        # Fully transparent, return original
        return img
    
    left, upper, right, lower = bbox
    width, height = img.size
    
    # Add padding
    left = max(0, left - padding)
    upper = max(0, upper - padding)
    right = min(width, right + padding)
    lower = min(height, lower + padding)

    # Crop
    cropped = img.crop((left, upper, right, lower))

    # Upscale cropped version to target size for better visibility
    return upscale_nearest_neighbor(cropped, TARGET_SIZE)

def create_edges_view(img: Image.Image) -> Image.Image:
    """
    Create edge-highlighted version of image.

    Args:
        img: Source RGBA image

    Returns:
        Image with edges highlighted
    """
    # Convert to grayscale for edge detection
    gray = img.convert('L')

    # Apply edge detection
    edges = gray.filter(ImageFilter.FIND_EDGES)

    # Enhance edges
    edges = edges.point(lambda x: x * 2)  # Brighten

    # Convert back to RGBA
    edges_rgba = edges.convert('RGBA')

    # Overlay edges on original
    result = Image.alpha_composite(img, edges_rgba)

    return result

def create_alpha_visualization(img: Image.Image) -> Image.Image:
    """
    Visualize alpha channel as grayscale image.

    Args:
        img: Source RGBA image

    Returns:
        Alpha channel as RGBA image (white = opaque, black = transparent)
    """
    # Extract alpha channel
    alpha = img.split()[-1]

    # Create RGBA image from alpha (white where opaque)
    alpha_vis = Image.merge('RGBA', [alpha, alpha, alpha, Image.new('L', img.size, 255)])

    return alpha_vis

def create_composite_panel(
    img: Image.Image,
    include_edges: bool = True,
    include_alpha: bool = True
) -> Image.Image:
    """
    Create 4-panel composite for vision model input.

    Layout (2x2 grid):
    ┌─────────┬─────────┐
    │  Gray   │  White  │
    │  Matte  │  Matte  │
    ├─────────┼─────────┤
    │  Tight  │  Edges  │
    │  Crop   │  /Alpha │
    └─────────┴─────────┘

    Args:
        img: Source icon image (RGBA)
        include_edges: Include edges view (bottom-right)
        include_alpha: Include alpha visualization (instead of edges if False)

    Returns:
        Composite panel image
    """
    # Upscale original
    upscaled = upscale_nearest_neighbor(img)

    # Create panels
    panel1 = create_matte(upscaled, (128, 128, 128, 255))  # Gray matte
    panel2 = create_matte(upscaled, (255, 255, 255, 255))  # White matte
    panel3 = get_tight_crop(img)                            # Tight crop

    # Bottom-right panel: edges or alpha
    if include_edges:
        panel4 = create_edges_view(upscaled)
    else:
        panel4 = create_alpha_visualization(upscaled)

    # Ensure all panels are same size (use upscaled size as reference)
    target_w, target_h = upscaled.size

    # Resize panel3 if needed (tight crop might be different size)
    if panel3.size != (target_w, target_h):
        panel3 = panel3.resize((target_w, target_h), Image.Resampling.NEAREST)

    # Create composite (2x2 grid)
    composite_w = target_w * 2
    composite_h = target_h * 2
    composite = Image.new('RGBA', (composite_w, composite_h), (255, 255, 255, 255))

    # Place panels
    composite.paste(panel1, (0, 0))
    composite.paste(panel2, (target_w, 0))
    composite.paste(panel3, (0, target_h))
    composite.paste(panel4, (target_w, target_h))

    # Add grid lines to distinguish panels
    draw = ImageDraw.Draw(composite)
    line_color = (200, 200, 200, 255)
    line_width = 2

    # Vertical line
    draw.line([(target_w, 0), (target_w, composite_h)], fill=line_color, width=line_width)

    # Horizontal line
    draw.line([(0, target_h), (composite_w, target_h)], fill=line_color, width=line_width)

    return composite

def preprocess_icon(
    icon_path: Path,
    output_path: Optional[Path] = None,
    include_edges: bool = True,
    include_alpha: bool = False
) -> Image.Image:
    """
    Main preprocessing function: load icon and create composite panel.

    Args:
        icon_path: Path to source icon
        output_path: Optional path to save composite (if None, returns in-memory)
        include_edges: Include edge-highlighted view
        include_alpha: Include alpha visualization (mutually exclusive with edges)

    Returns:
        Composite panel image
    """
    # Load icon
    img = load_icon(icon_path)

    # Create composite
    composite = create_composite_panel(img, include_edges, include_alpha)

    # Save if requested
    if output_path:
        composite.save(output_path)

    return composite

# Convenience function for batch processing
def preprocess_icons_batch(
    icon_paths: list[Path],
    output_dir: Path,
    verbose: bool = True,
    parallel: bool = True,
    max_workers: int = 4
) -> list[Path]:
    """
    Preprocess multiple icons in batch.

    Args:
        icon_paths: List of icon paths to process
        output_dir: Directory to save composites
        verbose: Print progress
        parallel: Use parallel processing (default True)
        max_workers: Number of parallel workers (default 4)

    Returns:
        List of output paths
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_paths = []
    
    def process_one(icon_path: Path) -> Optional[Path]:
        output_path = output_dir / f"{icon_path.stem}_composite.png"
        try:
            preprocess_icon(icon_path, output_path)
            return output_path
        except Exception as e:
            if verbose:
                print(f"  Error processing {icon_path.name}: {e}")
            return None

    if parallel and len(icon_paths) > 1:
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(process_one, p): p for p in icon_paths}
            
            for idx, future in enumerate(as_completed(futures), 1):
                icon_path = futures[future]
                if verbose:
                    print(f"[{idx}/{len(icon_paths)}] {icon_path.name}")
                
                result = future.result()
                if result:
                    output_paths.append(result)
    else:
        for idx, icon_path in enumerate(icon_paths, 1):
            if verbose:
                print(f"[{idx}/{len(icon_paths)}] {icon_path.name}")
            
            result = process_one(icon_path)
            if result:
                output_paths.append(result)

    return output_paths


def preprocess_icon_to_pil(icon_path: Path) -> Image.Image:
    """
    Preprocess icon and return PIL Image directly (no file I/O).
    
    Optimized for in-memory pipelines where you don't need to save to disk.
    
    Args:
        icon_path: Path to source icon
        
    Returns:
        Composite panel image as PIL Image
    """
    img = load_icon(icon_path)
    return create_composite_panel(img)

if __name__ == '__main__':
    """
    Example usage:
      python3 src/iconics_preprocessing.py raw/shell32-5-win2k-48x48.png /tmp/test_composite.png
    """
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 iconics_preprocessing.py <icon_path> [output_path]")
        print("\nExample:")
        print("  python3 src/iconics_preprocessing.py raw/lock-48x48.png /tmp/lock_composite.png")
        sys.exit(1)

    icon_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    if not icon_path.exists():
        print(f"Error: Icon not found: {icon_path}")
        sys.exit(1)

    print(f"Preprocessing: {icon_path}")
    composite = preprocess_icon(icon_path, output_path)

    if output_path:
        print(f"Saved composite to: {output_path}")
        print(f"Composite size: {composite.size}")
    else:
        print(f"Composite created (in-memory): {composite.size}")
