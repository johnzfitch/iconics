#!/usr/bin/env bash
# Iconics Global Installation Script
# Makes the 'icon' command available system-wide

set -e

ICONICS_DIR="/home/zack/dev/iconics"
ICON_SCRIPT="$ICONICS_DIR/icon"

echo "╔════════════════════════════════════════════════╗"
echo "║   Iconics - Global Installation Setup         ║"
echo "╚════════════════════════════════════════════════╝"
echo ""

# Check if script exists
if [[ ! -f "$ICON_SCRIPT" ]]; then
    echo "❌ Error: icon script not found at $ICON_SCRIPT"
    exit 1
fi

# Make executable
chmod +x "$ICON_SCRIPT"

# Determine installation method
if [[ -w "/usr/local/bin" ]]; then
    # Method 1: Symlink to /usr/local/bin (preferred)
    echo "Installing icon command to /usr/local/bin..."
    ln -sf "$ICON_SCRIPT" /usr/local/bin/icon
    echo "✅ Installed: /usr/local/bin/icon -> $ICON_SCRIPT"
elif sudo -n true 2>/dev/null; then
    # Method 2: Use sudo if available
    echo "Installing icon command to /usr/local/bin (requires sudo)..."
    sudo ln -sf "$ICON_SCRIPT" /usr/local/bin/icon
    echo "✅ Installed: /usr/local/bin/icon -> $ICON_SCRIPT"
else
    # Method 3: Add to user's local bin
    mkdir -p "$HOME/.local/bin"
    ln -sf "$ICON_SCRIPT" "$HOME/.local/bin/icon"
    echo "✅ Installed: $HOME/.local/bin/icon -> $ICON_SCRIPT"

    # Check if ~/.local/bin is in PATH
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        echo ""
        echo "⚠️  Warning: $HOME/.local/bin is not in your PATH"
        echo ""
        echo "Add this line to your ~/.bashrc or ~/.zshrc:"
        echo ""
        echo '    export PATH="$HOME/.local/bin:$PATH"'
        echo ""
        echo "Then reload your shell: source ~/.bashrc"
    fi
fi

echo ""
echo "╔════════════════════════════════════════════════╗"
echo "║   Installation Complete!                       ║"
echo "╚════════════════════════════════════════════════╝"
echo ""
echo "Quick Start:"
echo "  icon search security       # Search for icons"
echo "  icon use lock shield       # Export and get markdown"
echo "  icon suggest authentication # Get icon suggestions"
echo "  icon md network            # Generate markdown snippet"
echo "  icon help                  # Show all commands"
echo ""
echo "Test it now: icon search info"
echo ""
