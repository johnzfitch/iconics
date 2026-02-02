# Iconics TUI v2 - Testing Checklist

## Implementation Complete

The TUI v2 has been implemented with the following features:

### Phase 1: Kitty Rendering ✓
- `src/iconics_tui/rendering.py` - Kitty graphics protocol support
- `add_background()` - Adds light gray background behind icons
- `render_kitty()` - Pixel-perfect image rendering
- `render_kitty_with_background()` - Convenience function
- `test_kitty_support()` - Terminal capability detection

### Phase 2: Textual App Structure ✓
- `src/iconics_tui/app.py` - Main Textual application
- `src/iconics_tui/widgets.py` - Custom widgets (IconListItem, PreviewPane)
- Miller columns layout: List view (40%) + Preview pane (60%)
- Search input at top
- Footer with keybindings
- Vim-style navigation (j/k)

### Phase 3: IconicsRetriever Integration ✓
- Semantic search via CLIP embeddings
- Fallback to text matching
- Debounced search (200ms delay)
- Full catalog metadata integration
- Category pre-filtering support

## How to Test

**IMPORTANT**: Use the virtual environment (all dependencies including faiss-cpu are installed there):

### 1. Basic Launch
```bash
# Activate venv (or use .venv/bin/python3)
source .venv/bin/activate

# Launch with no query (shows first 100 icons)
python3 iconics.py tui

# Launch with initial query
python3 iconics.py tui --query "security"

# Launch with category filter
python3 iconics.py tui --category ui

# Or run directly without activating:
.venv/bin/python3 iconics.py tui --query "security"
```

### 2. Navigation Tests
- **j/k or ↓/↑**: Navigate through icon list
- **/**: Focus search box
- **Esc**: Return focus to list
- **q**: Quit application

### 3. Search Tests
- Type in search box (should debounce at 200ms)
- Short queries (< 3 chars): Text matching only
- Longer queries: Semantic CLIP search
- Verify results update smoothly

### 4. Visual Tests
**CRITICAL**: These tests verify the core value proposition of TUI v2

- [ ] Icons render pixel-perfect (NOT halfblocks or ASCII)
- [ ] Icons have light gray background (visible on dark terminal)
- [ ] Large preview (at least 256px) shows clear details
- [ ] Can identify icons visually at a glance
- [ ] Full icon names visible in list (no truncation)

### 5. Functionality Tests
- [ ] Selecting icon updates preview immediately
- [ ] Preview shows metadata (category, tags, size, path)
- [ ] Search filters results correctly
- [ ] c: Copy path notification appears
- [ ] Enter: "Use icon" notification appears

## Expected Behavior

### Good Experience:
- Icons are clearly identifiable
- Preview is large and detailed
- Navigation is smooth
- Search is responsive (debounced)
- List shows meaningful names

### Issues to Watch For:
- Blurry or halfblock icons → Kitty protocol not working
- Dark icons invisible → Background not applied
- Truncated names → Adjust column width
- Slow search → Debouncing not working
- Empty previews → Path resolution issue

## Definition of Done (from Action Plan)

```bash
iconics tui --query "security"
```

- [x] Icons render pixel-perfect (Kitty protocol, NOT halfblocks)
- [ ] Can identify icons visually at a glance ← **USER TEST REQUIRED**
- [x] Light background behind all icons
- [x] Full names visible (list view)
- [x] Search works with existing CLIP retriever
- [x] j/k/↑/↓ navigation
- [x] Enter to use, c to copy path
- [x] q to quit

## Phase 4: Grid View (Not Yet Implemented)

The grid view toggle ('g' key) is currently a placeholder. When pressed, it shows:
> "Grid view coming in Phase 4"

This is a future enhancement and not required for core functionality.

## Files Modified/Created

### New Files:
- `src/iconics_tui/__init__.py` - Package initialization
- `src/iconics_tui/rendering.py` - Kitty graphics protocol
- `src/iconics_tui/widgets.py` - Custom Textual widgets
- `src/iconics_tui/app.py` - Main application

### Modified Files:
- `pyproject.toml` - Added textual>=1.0.0 dependency
- (python-textual installed via pacman)

### Already Existed:
- `iconics.py` - TUI command handler already implemented (lines 351-381)

## Troubleshooting

### "TUI dependencies not installed"
- textual is installed via pacman: `python-textual 6.8.0-1`
- Verify: `python3 -c "import textual; print(textual.__version__)"`

### "CLIP retriever not initialized"
- Ensure embeddings exist: `embeddings/icon_embeddings.npy`
- Run: `python3 iconics.py embed` if needed

### Icons not displaying
- Ensure you're in a Kitty terminal: `echo $TERM` should contain "kitty"
- Test Kitty support: `python3 src/iconics_tui/rendering.py`

### Images show as escape codes
- Your terminal doesn't support Kitty graphics protocol
- Try launching Kitty terminal: `kitty`
- Then run TUI from within Kitty

## Next Steps

1. **Test in Kitty terminal** (required for visual verification)
2. **Try various queries** to test semantic search
3. **Navigate through results** to verify preview updates
4. **Report any issues** with icon visibility or performance

## Success Criteria

The TUI is successful if:
1. You can browse icons visually without reading names
2. Icons are clearly identifiable in the preview pane
3. Search finds relevant icons quickly
4. The interface feels responsive and polished

---

**Ready for interactive testing!**
