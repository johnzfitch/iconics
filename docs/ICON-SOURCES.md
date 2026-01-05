# Free Icon Packs from 2004-2008

High-quality vintage icon collections perfect for GitHub READMEs and technical documentation. These icon sets have the polished, professional look of the Web 2.0 era without the flatness of modern minimalist icons.

---

## Top Recommended Packs

### 1. FamFamFam Silk Icons (2005)
**The gold standard for web icons from that era.**

- **Count**: 1,000+ icons
- **Size**: 16x16 PNG
- **License**: CC Attribution 2.5 (free for commercial use with credit)
- **Style**: Smooth, glossy, professional web icons
- **Best for**: UI elements, actions, file types, status indicators

**Download**:
- Official: http://www.famfamfam.com/lab/icons/silk/
- GitHub Mirror: https://github.com/legacy-icons/famfamfam-silk
- Icon Archive: https://www.iconarchive.com/show/silk-icons-by-famfamfam.html
- Internet Archive: https://archive.org/details/famfamfam_silk_icons_v013_202308

**Why it's great**: Incredibly comprehensive coverage of common concepts (locks, folders, arrows, status icons). The 16x16 size is perfect for inline documentation use. Clean, crisp rendering at small sizes.

---

### 2. Fugue Icons by Yusuke Kamiyamane (2007-2008)
**Massive collection with excellent coverage.**

- **Count**: 3,570+ icons
- **Size**: 16x16 PNG
- **License**: CC Attribution 3.0 (commercial use with backlink)
- **Style**: Highly detailed, consistent visual language
- **Best for**: Comprehensive application UI, detailed status icons

**Download**:
- Official: https://p.yusukekamiyamane.com/
- Icons101: https://www.icons101.com/iconset/setid_1185/Fugue_by_Yusuke_Kamiyamane
- Icon Archive: https://www.iconarchive.com/show/fugue-icons-by-yusuke-kamiyamane.html
- GitHub: https://github.com/unikent/fugue-icons

**Why it's great**: Largest collection available. If you need an icon for something obscure, Fugue probably has it. Consistent style across all 3,500+ icons.

---

### 3. Tango Icon Theme (2006-2007)
**The GNOME/KDE standard with excellent scalability.**

- **Count**: 230+ base icons (multiple sizes)
- **Sizes**: 16x16, 22x22, 24x24, 32x32, 48x48 PNG + SVG source
- **License**: Public Domain
- **Style**: Colorful, friendly, consistent palette
- **Best for**: Desktop-style icons, application icons, large displays

**Download**:
- Tek Eye Archive: https://www.tekeye.uk/free_resources/tango_desktop_project/index
- GitHub: https://github.com/Distrotech/tango-icon-theme
- Iconfinder: https://www.iconfinder.com/iconsets/tango-icon-library
- Icon Archive: https://www.iconarchive.com/tag/tango

**Why it's great**: Multiple sizes in the same pack, so you can use 16x16 for inline and 32x32 for headers. SVG sources available for custom sizing. True open source (public domain).

---

### 4. Nuvola Icon Set (2003-2004)
**Early KDE icon set with distinctive 3D style.**

- **Count**: ~600 icons
- **Sizes**: 16x16, 22x22, 32x32, 48x48, 64x64, 128x128 PNG + SVG
- **License**: LGPL 2.1
- **Style**: 3D glossy, colorful, distinctive
- **Best for**: Application icons, larger displays

**Download**:
- Wikimedia Commons: https://commons.wikimedia.org/wiki/Category:Nuvola_icons
- KDE Store: https://store.kde.org/p/1122823
- Icons8 (PNG/SVG): https://icons8.com/icons/set/nuvola

**Why it's great**: Beautiful 3D aesthetic that stands out. Multiple sizes available. Good for larger icon displays in documentation.

---

### 5. Crystal XP Icons (2004-2006)
**Windows XP-era icons with crystal clarity.**

- **Count**: 43+ themed sets
- **Sizes**: Various (16x16 to 256x256)
- **License**: Varies by set (most free for personal use)
- **Style**: Glossy, Windows XP aesthetic
- **Best for**: Windows-themed documentation, nostalgic feel

**Download**:
- Icon Archive: https://www.iconarchive.com/tag/crystal-xp
- WinCustomize: https://www.wincustomize.com/explore/iconpackager/

**Why it's great**: That distinctive early 2000s Windows look. Good for Windows-focused documentation.

---

## Additional Collections

### Internet Archive - Retro Windows Icons
**2000+ authentic Windows 95/98/XP/2000 icons**

- Source: https://archive.org/details/retro-windows-icons
- Good for: Authentic retro computing documentation

### HackerNoon Pixel Icon Library
**Classic pixelated icons**

- GitHub: https://github.com/hackernoon/pixel-icon-library
- Style: 8-bit pixel art
- Good for: Retro/gaming documentation

### Streamline Pixel Icons
**662 icons inspired by Susan Kare's original Mac icons**

- Source: https://www.streamlinehq.com/icons/pixel
- Style: 32px grid pixel art
- Good for: Classic computing aesthetic

---

## License Summary

| Pack | License | Commercial Use | Attribution Required |
|------|---------|----------------|---------------------|
| FamFamFam Silk | CC BY 2.5 | Yes | Yes |
| Fugue | CC BY 3.0 | Yes | Yes (backlink) |
| Tango | Public Domain | Yes | No |
| Nuvola | LGPL 2.1 | Yes | Yes |
| Crystal XP | Varies | Check each set | Varies |

---

## Recommended Download Priority

For building out the Iconics library:

1. **FamFamFam Silk** - Essential baseline (1000 icons)
2. **Fugue** - Fill gaps with specialized icons (3570 icons)
3. **Tango** - Multi-size variants (230 base icons)
4. **Nuvola** - Additional 3D style options (600 icons)

This would give approximately **5,400+ unique icons** across all sizes.

---

## Size Recommendations for GitHub READMEs

| Use Case | Recommended Size | Best Pack |
|----------|------------------|-----------|
| Inline with text | 16x16 or 24x24 | Silk, Fugue |
| Section headers | 24x24 or 32x32 | Tango, Silk |
| Feature highlights | 32x32 or 48x48 | Tango, Nuvola |
| Hero sections | 64x64+ | Nuvola, Tango |

---

## Conversion Notes

When importing icons:
- ICO files can be converted to PNG using ImageMagick: `magick input.ico output.png`
- GIF files: `magick input.gif output.png`
- SVG to PNG at specific size: `magick -density 300 input.svg -resize 24x24 output.png`

For upscaling small icons (16x16 to 24x24), consider AI upscaling tools like gemini-cli or cod3x for better results than basic interpolation.

---

*Last updated: 2025-12-02*
