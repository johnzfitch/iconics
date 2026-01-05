#!/bin/bash
# Automated environment setup for Iconics vision labeling system
# Sets up Qwen2.5-VL-7B-Instruct or InternVL3-14B for icon semantic labeling

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_DIR/.venv-vision"

echo "====================================="
echo "Iconics Vision Labeling Setup"
echo "====================================="
echo ""
echo "Project directory: $PROJECT_DIR"
echo "Virtual environment: $VENV_DIR"
echo ""

# Check for Python 3.9+
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 not found. Please install Python 3.9 or later."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "Detected Python version: $PYTHON_VERSION"

# Create virtual environment
if [ -d "$VENV_DIR" ]; then
    echo "Virtual environment already exists at $VENV_DIR"
    read -p "Recreate it? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing existing environment..."
        rm -rf "$VENV_DIR"
    else
        echo "Using existing environment."
    fi
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo "Upgrading pip and wheel..."
pip install -U pip wheel

# Detect CUDA version (optional but helpful)
if command -v nvcc &> /dev/null; then
    CUDA_VERSION=$(nvcc --version | grep "release" | sed -n 's/.*release \([0-9]\+\.[0-9]\+\).*/\1/p')
    echo "Detected CUDA version: $CUDA_VERSION"
else
    echo "CUDA not detected (nvcc not found). Proceeding with CPU-only PyTorch."
fi

# Install PyTorch (adjust for your CUDA version)
echo ""
echo "Installing PyTorch..."
echo "NOTE: This script installs CUDA 12.1 PyTorch by default."
echo "If you need a different version, edit this script or install manually."
echo ""

# Install PyTorch with CUDA 12.1 (adjust cu121 to your CUDA version)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# Install Transformers from source (avoids KeyError: 'qwen2_5_vl')
echo ""
echo "Installing Transformers from source..."
pip install git+https://github.com/huggingface/transformers

# Install accelerate
echo "Installing accelerate..."
pip install accelerate

# Install Qwen VL utilities
echo "Installing qwen-vl-utils..."
pip install "qwen-vl-utils[decord]==0.0.8"

# Install image processing libraries
echo "Installing image processing libraries..."
pip install pillow numpy opencv-python

# Optional: Install quantization support
echo ""
read -p "Install bitsandbytes for 8-bit/4-bit quantization? (recommended for 4090) (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Installing bitsandbytes..."
    pip install bitsandbytes
else
    echo "Skipping bitsandbytes. You can install later with: pip install bitsandbytes"
fi

# Optional: Install flash-attn (improves inference speed)
echo ""
read -p "Install flash-attn for performance optimization? (requires compilation, takes ~5-10 min) (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Installing flash-attn (this may take a while)..."
    pip install flash-attn --no-build-isolation
else
    echo "Skipping flash-attn. You can install later with: pip install flash-attn --no-build-isolation"
fi

# Verify installation
echo ""
echo "====================================="
echo "Verifying installation..."
echo "====================================="
echo ""

python3 << 'EOF'
import sys
import torch
print(f"Python version: {sys.version}")
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA version: {torch.version.cuda}")
    print(f"GPU: {torch.cuda.get_device_name(0)}")

try:
    import transformers
    print(f"Transformers version: {transformers.__version__}")
except ImportError:
    print("ERROR: Transformers not found!")

try:
    import accelerate
    print(f"Accelerate version: {accelerate.__version__}")
except ImportError:
    print("WARNING: Accelerate not found!")

try:
    from qwen_vl_utils import process_vision_info
    print("qwen-vl-utils: OK")
except ImportError:
    print("WARNING: qwen-vl-utils not found!")

try:
    import bitsandbytes
    print(f"bitsandbytes version: {bitsandbytes.__version__}")
except ImportError:
    print("INFO: bitsandbytes not installed (optional)")

try:
    import flash_attn
    print(f"flash-attn version: {flash_attn.__version__}")
except ImportError:
    print("INFO: flash-attn not installed (optional)")
EOF

echo ""
echo "====================================="
echo "Setup Complete!"
echo "====================================="
echo ""
echo "To activate this environment in the future, run:"
echo "  source $VENV_DIR/bin/activate"
echo ""
echo "Next steps:"
echo "  1. Download Qwen2.5-VL-7B-Instruct model (first run will auto-download)"
echo "  2. Run: python3 scripts/convert-win2k-icons.py (after creating the script)"
echo "  3. Run: python3 icon-manager.py generate-csv --vision win2k-import.csv"
echo ""
echo "Model download will happen automatically on first use (~15GB)."
echo "Make sure you have sufficient disk space in ~/.cache/huggingface/"
echo ""
