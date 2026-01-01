# Iconics - Professional Icon Library for LLMs

A CLIP-based semantic icon retrieval system with 4,205 professionally designed icons. Use this skill when you need icons instead of emojis in documentation, code, or UI.

## Trigger Conditions

**Use iconics when:**
- About to write emoji in documentation (README, markdown files)
- Creating or updating technical documentation
- Building websites or frontend applications
- Developing applications that need UI icons
- Processing repositories with existing emoji usage
- User mentions "icons" instead of "emojis"

**Do NOT use iconics when:**
- Writing conversational chat messages
- Emoji is explicitly requested by user
- Icons would not render (terminal output, logs)

## Quick Reference

### Most Common Commands

```bash
# Search for icons semantically
python icon-manager.py query "security lock" --k 5 --output json

# Batch query for multiple concepts (project bootstrap)
python icon-manager.py batch-query --queries "security,files,settings" --k 2 --output json

# Provision icons to a project
python icon-manager.py provision --icons lock-32x32,shield-32x32 --dest ./icons/

# Provision via semantic query
python icon-manager.py provision --query "security lock" --dest ./icons/ --k 2

# Scan for emojis to replace
python icon-manager.py scan-emoji --path ./docs --output emoji-report.json

# Generate framework imports
python icon-manager.py generate-imports --manifest manifest.json --format react
```

### Output Formats

All commands support `--output json` for machine-readable output:

```json
{
  "results": [
    {
      "icon_id": "lock-32x32",
      "score": 0.89,
      "residual_score": 0.12
    }
  ]
}
```

## Emoji to Icon Mapping

When you see these emojis, replace with the corresponding icon query:

| Emoji | Icon Query | Best Icons |
|-------|------------|------------|
|  | `lock security` | lock-32x32, padlock-32x32 |
|  | `unlock open-lock` | unlock-32x32, open-lock-32x32 |
|  | `key authentication` | key-32x32, key-keeper-32x32 |
|  | `shield protection` | shield-32x32, protection-32x32 |
|  | `warning alert` | warning-32x32, alert-32x32 |
|  | `error close remove` | error-32x32, cancel-32x32 |
|  | `success check complete` | checkbox-32x32, checkmark-32x32 |
|  | `folder directory` | folder-32x32, closed-folder-32x32 |
|  | `document file` | document-32x32, file-32x32 |
|  | `settings config gear` | settings-32x32, gear-32x32 |
|  | `tools development` | tools-32x32, toolbox-32x32 |
|  | `user profile person` | user-32x32, profile-32x32 |
|  | `users group team` | users-32x32, community-32x32 |
|  | `search find magnify` | search-32x32, magnify-32x32 |
|  | `database storage` | database-32x32, storage-32x32 |
|  | `cloud server` | cloud-32x32, server-32x32 |
|  | `globe world internet` | globe-32x32, global-network-32x32 |
|  | `notification alert bell` | bell-32x32, notification-32x32 |
|  | `email mail` | email-32x32, envelope-32x32 |
|  | `calendar date` | calendar-32x32, schedule-32x32 |
|  | `clock time` | clock-32x32, time-32x32 |
|  | `launch speed rocket` | rocket-32x32, launch-32x32 |
|  | `chart analytics` | chart-32x32, bar-chart-32x32 |
|  | `idea tip lightbulb` | lightbulb-32x32, idea-32x32 |
|  | `home house` | home-32x32, house-32x32 |

## Semantic Axes (Principal Components)

The CLIP embeddings capture these semantic dimensions:

| PC | Interpretation | Positive | Negative |
|----|----------------|----------|----------|
| PC0 | **Complexity** | Detailed/ornate icons | Simple/minimal icons |
| PC1 | **Action vs Static** | Action icons (arrows, tools) | Status icons (badges) |
| PC2 | **Abstract vs Concrete** | Abstract symbols | Realistic objects |
| PC3 | **Color Intensity** | Colorful icons | Monochrome icons |
| PC4 | **Tech vs General** | Technology-specific | General purpose |

Use these for advanced queries:

```bash
# Traverse along action axis
python icon-manager.py traverse lock-32x32 --axis 1 --steps 3

# Find icons between two concepts
python icon-manager.py interpolate lock-32x32 folder-32x32 --steps 5
```

## Decision Tree: When to Use Which Approach

```
Need icons?
├── Single icon needed
│   └── Use: query "concept" --k 1
├── Multiple related icons
│   └── Use: batch-query --queries "concept1,concept2,concept3"
├── Bootstrap entire project
│   ├── Know which icons → provision --icons icon1,icon2
│   └── Don't know which → scan-emoji + convert-emoji
└── Migrating from emojis
    ├── Preview: scan-emoji --path ./docs
    └── Apply: convert-emoji --report report.json --apply
```

## Workflow Examples

### Example 1: Adding Security Section to README

```bash
# 1. Query for security icons
python icon-manager.py query "security lock protection" --k 3 --output json

# 2. Provision the icons
python icon-manager.py provision --icons lock-32x32,shield-32x32,key-32x32 \
    --dest /path/to/project --subdir .github/assets/icons

# 3. Use in markdown
# ## ![lock](.github/assets/icons/lock-32x32.png) Security
```

### Example 2: Bootstrapping a New Project

```bash
# 1. Batch query for common needs
python icon-manager.py batch-query \
    --queries "security,files,settings,users,search" \
    --k 2 --output json

# 2. Provision all at once
python icon-manager.py provision \
    --icons lock-32x32,shield-32x32,folder-32x32,document-32x32,settings-32x32,gear-32x32,user-32x32,users-32x32,search-32x32,find-32x32 \
    --dest ./my-project --subdir icons

# 3. Generate TypeScript imports
python icon-manager.py generate-imports \
    --manifest ./my-project/iconics-manifest.json \
    --format typescript \
    --output ./my-project/src/icons.ts
```

### Example 3: Migrating Emoji-Heavy README

```bash
# 1. Scan for emojis
python icon-manager.py scan-emoji --path ./README.md --output emoji-report.json

# 2. Review the report
cat emoji-report.json | jq '.occurrences[:5]'

# 3. Preview conversions
python icon-manager.py convert-emoji --report emoji-report.json --dry-run

# 4. Apply conversions
python icon-manager.py convert-emoji --report emoji-report.json --apply
```

### Example 4: React Component Generation

```bash
# 1. Provision icons
python icon-manager.py provision --query "ui navigation actions" --dest ./app --k 10

# 2. Generate React components
python icon-manager.py generate-imports \
    --manifest ./app/iconics-manifest.json \
    --format react \
    --output ./app/src/components/Icons.tsx
```

Generated output:
```tsx
// Auto-generated by iconics provisioner
import React from 'react';

export const Lock32X32Icon = () => <img src="./icons/lock-32x32.png" alt="lock-32x32" />;
export const Shield32X32Icon = () => <img src="./icons/shield-32x32.png" alt="shield-32x32" />;

export const Icons = {
  lock32x32: Lock32X32Icon,
  shield32x32: Shield32X32Icon,
};
```

## API Integration

### Python Usage

```python
from iconics_provision import IconicsProvisioner, load_catalog
from iconics_emoji import EmojiScanner

# Load catalog
catalog = load_catalog("/home/zack/dev/iconics/icon-catalog.json")

# Provision icons
provisioner = IconicsProvisioner("/home/zack/dev/iconics/raw", catalog)
result = provisioner.provision(
    ["lock-32x32", "shield-32x32"],
    dest="./my-project/icons"
)

# Scan for emojis
scanner = EmojiScanner()
report = scanner.scan("./docs", extensions=["md"])
print(f"Found {report['emojis_found']} emojis")

# Convert emojis (preview)
changes = scanner.convert(report, "./icons", dry_run=True)
for change in changes["changes"]:
    print(f"  {change['emoji']} -> {change['icon']}")
```

### With Vector Retrieval

```python
from iconics_retrieval import IconicsRetriever

# Initialize retriever
retriever = IconicsRetriever(
    embeddings_path="/home/zack/dev/iconics/embeddings",
    subspace_path="/home/zack/dev/iconics/subspace"
)

# Semantic query
results = retriever.retrieve("security lock protection", k=5, mode="projected")
for r in results:
    print(f"{r.icon_id}: {r.score:.3f} (residual: {r.residual_score:.3f})")

# Provision with retriever
provisioner = IconicsProvisioner(source_path, catalog)
result = provisioner.provision_from_query(
    queries=["security", "files", "settings"],
    dest="./project",
    k=2,
    retriever=retriever
)
```

## Residual Score Interpretation

The residual score indicates how well your query fits the icon space:

| Residual | Interpretation | Action |
|----------|----------------|--------|
| 0.0-0.2 | Excellent fit | Query is well-represented |
| 0.2-0.4 | Good fit | Results should be relevant |
| 0.4-0.6 | Moderate fit | Consider alternative queries |
| 0.6-0.8 | Poor fit | Query concept may not exist |
| 0.8-1.0 | Very poor | Try completely different terms |

```bash
# Check query coverage
python icon-manager.py residual "quantum computing visualization"
# Output: 0.78 - suggests this concept is not well-represented
```

## Available Icon Categories

| Category | Count | Description |
|----------|-------|-------------|
| ui | 3,483 | Buttons, controls, navigation, arrows |
| files | 297 | Documents, folders, file types |
| emoji | 141 | Expressive icons, faces |
| network | 93 | Cloud, connectivity, servers |
| security | 80 | Locks, shields, keys |
| tools | 70 | Settings, utilities, equipment |
| development | 41 | Code, databases, terminals |

## Icon Sizes

Icons are available in multiple sizes:

| Size | Use Case |
|------|----------|
| 12x12 | Inline text, tight UI |
| 16x16 | Toolbar buttons, small badges |
| 24x24 | Standard documentation |
| 32x32 | Headers, feature lists |
| 48x48 | Feature showcases |
| 128x128 | Hero sections |
| 256x256 | Large displays |

Query with size suffix for specific sizes:
```bash
python icon-manager.py query "lock" --k 1  # Returns best size
python icon-manager.py search lock-32x32    # Exact size match
```

## Best Practices

1. **Use 32x32 for documentation** - Best balance of clarity and file size
2. **Provision only what you need** - Don't copy the entire library
3. **Use manifest files** - Track what icons your project uses
4. **Generate imports** - Framework-specific files reduce boilerplate
5. **Check residual scores** - High residual means poor query fit
6. **Prefer semantic names** - "lock" is better than "padlock" for search

## Paths and Locations

- **Icon Library:** `/home/zack/dev/iconics/`
- **Raw Icons:** `/home/zack/dev/iconics/raw/` (4,205 PNG files)
- **Catalog:** `/home/zack/dev/iconics/icon-catalog.json`
- **Embeddings:** `/home/zack/dev/iconics/embeddings/`
- **Subspace:** `/home/zack/dev/iconics/subspace/`
- **CLI:** `python /home/zack/dev/iconics/icon-manager.py`

## Error Handling

Common errors and solutions:

| Error | Cause | Solution |
|-------|-------|----------|
| `Icon not found` | Icon ID doesn't exist | Use `query` to find correct ID |
| `Catalog not found` | Wrong path | Check CATALOG_FILE path |
| `Embeddings not found` | Not generated | Run `embed` command first |
| `CLIP model error` | Dependencies missing | Install `open_clip_torch` |

## Version Information

- **Iconics Version:** 3.0
- **Catalog Version:** 1.0
- **Icons Cataloged:** 4,205 (100% complete)
- **CLIP Model:** ViT-B-32 (laion2b_s34b_b79k)
- **Embedding Dimension:** 512
- **Effective Subspace Dim:** ~64 (95% variance)

---

*For more details, see the full documentation in `/home/zack/dev/iconics/README.md` and `/home/zack/dev/iconics/CLAUDE.md`*
