# Iconics TUI v2 - Current Status

## ✅ What Works

1. **Search & Navigation**
   - Semantic CLIP search (use descriptive phrases for best results)
   - Real-time filtering with 200ms debounce
   - Vim-style j/k navigation
   - Fast scrolling through 5,682 icons

2. **Metadata Display**
   - Icon name, ID, category
   - Full tag lists
   - Descriptions
   - File paths

3. **Keybindings**
   - `/` - Focus search
   - `j/k` or arrows - Navigate
   - `c` - Copy path to clipboard
   - `Enter` - Use icon (integrates with export)
   - `q` - Quit

## ⚠️ Known Limitation: Image Preview

**The pixel-perfect Kitty graphics preview is not working yet.**

### Why?
Textual uses Rich for rendering, which sanitizes/escapes terminal escape sequences. The Kitty graphics protocol requires raw escape codes to be passed through to the terminal, but Rich treats them as text and escapes them.

### What we tried:
- ✅ Kitty protocol implementation works (tested standalone)
- ✅ Images render correctly outside Textual
- ❌ Textual's Rich rendering layer blocks the sequences

### Solutions to explore:
1. **Custom Textual widget** - Write directly to console, bypassing Rich
2. **Sixel protocol** - Alternative to Kitty (also has Rich issues)  
3. **ASCII art / halfblocks** - Lower quality but would work
4. **External viewer** - Open images in separate window (feh, kitty icat)
5. **Wait for Textual image support** - Framework may add this feature

## 💡 Search Tips

The CLIP embeddings work best with **descriptive phrases**, not single words:

❌ **Bad**: "help"  
→ Returns: balloons, random documents (poor semantic match)

✅ **Good**: "question mark help information"  
→ Returns: help icons, question marks, info icons

✅ **Good**: "security lock shield protection"  
→ Returns: locks, shields, security icons

✅ **Good**: "network connection wifi internet"  
→ Returns: wireless, network icons

## 🎯 Current Value

Even without image preview, the TUI provides:

1. **Fast semantic search** - Find icons by meaning, not just name
2. **Better than grep** - Natural language queries work
3. **Metadata at a glance** - Full icon info without opening files
4. **Keyboard-driven** - No mouse needed
5. **Works great for agents** - Can be integrated into CLI workflows

## 🚀 Next Steps

### Short-term (works now):
- Use TUI for **search and discovery**
- Copy paths, export icons
- Browse categories
- View metadata

### Medium-term (needs implementation):
- External image viewer integration (`kitty icat`, `feh`)
- ASCII art preview as fallback
- Grid view (Phase 4)

### Long-term (needs research):
- True inline image support in Textual
- Or: Build custom TUI without Textual constraints

## 🎨 Workaround for Now

To view icons while using TUI:

```bash
# Terminal 1: Run TUI
./tui --query "security lock shield"

# Terminal 2: Watch and display selected icon
# (Use 'c' in TUI to copy path, then view)
kitty icat raw/lock-24x24.png
```

Or use the existing CLI commands that already work great:
```bash
# Search and view in one go
iconics search "security lock" | head -5

# Export directly
iconics use lock shield key
```

---

**The TUI is functional and useful for search/discovery. Image preview is a nice-to-have that we'll solve in a future iteration.**
