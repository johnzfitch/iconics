# ICONICS - SEMANTIC ICON LIBRARY

## Overview
~8,000 semantically-indexed icons via CLIP embeddings. Use for UI, documentation, applications.

**Workspace:** `/home/zack/dev/iconics/`
**Icons:** `/home/zack/dev/iconics/raw/*.png`

---

## Trigger Conditions

### 1. Emoji in Artifacts
When about to write emoji in any deliverable (not chat), query iconics instead:
- ❌ `## 🔐 Security` in README
- ✅ `## ![Security](assets/icons/shield-secure-24.png) Security`

### 2. Documentation Creation
README, guides, specs, API docs - scan for concepts needing visual anchors.

### 3. Website/Frontend Development
Navigation, actions, status indicators, feature sections.

### 4. Application Development  
GUI toolbars, dialogs, system tray, mobile layouts.

### 5. Existing Repo with Emojis
User shares GitHub repo or docs with emoji usage - offer conversion.

---

## Hosting Strategy

**Problem:** 8k icons can't live in every project repo.

**Solution:** Project-local provisioning. Copy only needed icons.

```
iconics/                    (source library - your machine)
└── raw/                    (8,000 icons)

your-project/               (destination project)
└── assets/
    └── icons/              (only icons this project uses)
        ├── lock-secure-24.png
        ├── user-circle-24.png
        └── manifest.json   (tracks what's provisioned)
```

### Provisioning Commands

```bash
# Provision specific icons to project
python icon-manager.py provision \
  --icons lock-secure-24,user-circle-24,trash-delete-24 \
  --dest /path/to/project/assets/icons/

# Provision from manifest file
python icon-manager.py provision \
  --manifest icon-manifest.json \
  --dest ./assets/icons/

# Provision all icons matching query
python icon-manager.py provision \
  --query "navigation menu home settings user" \
  --dest ./src/assets/icons/ \
  --k 3  # top 3 per concept
```

### Manifest Format

```json
{
  "project": "my-webapp",
  "provisioned": "2025-01-15",
  "icons": {
    "lock-secure-24": {
      "source_query": "security lock",
      "usage": ["login-page", "settings"],
      "hash": "a3f2b1c..."
    },
    "user-circle-24": {
      "source_query": "user profile",
      "usage": ["header", "account"],
      "hash": "b4e2a1d..."
    }
  },
  "total_size_kb": 48
}
```

---

## Workflow: Project Bootstrapping

When starting a new web/app project:

### Step 1: Extract Concepts from Feature List

User describes project or provides feature list. Identify icon-worthy concepts:

```
Features: user auth, file uploads, team sharing, notifications, billing
    ↓
Concepts: user, lock, upload, folder, team/group, bell, credit-card, settings
```

### Step 2: Generate Icon Manifest

```bash
# Create concept list
cat > /tmp/concepts.txt << 'EOF'
user authentication login
file upload document
team group sharing collaborate  
notification alert bell
billing payment credit card
settings configuration gear
EOF

# Batch query to find best matches
python icon-manager.py batch-query \
  --input /tmp/concepts.txt \
  --output icon-manifest.json \
  --k 2  # top 2 per concept line
```

### Step 3: Provision to Project

```bash
python icon-manager.py provision \
  --manifest icon-manifest.json \
  --dest ./src/assets/icons/
```

### Step 4: Generate Import Map (optional)

```bash
python icon-manager.py generate-imports \
  --manifest ./src/assets/icons/manifest.json \
  --format react \
  --output ./src/components/Icons.tsx
```

Produces:
```tsx
// Auto-generated icon imports
import LockSecure from '../assets/icons/lock-secure-24.png';
import UserCircle from '../assets/icons/user-circle-24.png';
// ...

export const Icons = {
  security: LockSecure,
  user: UserCircle,
  // ...
} as const;
```

---

## Workflow: Emoji Conversion

### Scanning Existing Docs

```bash
# Scan directory for emoji usage
python icon-manager.py scan-emoji \
  --path /path/to/repo \
  --extensions md,mdx,tsx,jsx,html \
  --output emoji-report.json
```

Output:
```json
{
  "files_scanned": 47,
  "emoji_found": 23,
  "occurrences": [
    {
      "file": "README.md",
      "line": 12,
      "emoji": "🔒",
      "context": "## 🔒 Security Features",
      "suggested_icon": "lock-secure-24",
      "confidence": 0.91
    },
    {
      "file": "docs/api.md", 
      "line": 45,
      "emoji": "⚠️",
      "context": "⚠️ **Warning:** Rate limits apply",
      "suggested_icon": "warning-alert-24",
      "confidence": 0.88
    }
  ]
}
```

### Interactive Conversion

```bash
# Preview changes
python icon-manager.py convert-emoji \
  --report emoji-report.json \
  --dry-run

# Apply conversion
python icon-manager.py convert-emoji \
  --report emoji-report.json \
  --icon-path assets/icons \
  --apply
```

### Manual Conversion Patterns

When converting by hand in artifacts:

| Original | Replacement |
|----------|-------------|
| `## 🔐 Security` | `## ![Security](assets/icons/lock-secure-24.png) Security` |
| `- 🚀 Fast` | `- ![Fast](assets/icons/rocket-speed-24.png) Fast` |
| `> ⚠️ Warning` | `> ![Warning](assets/icons/warning-alert-24.png) Warning` |
| `✅ Complete` | `![Complete](assets/icons/check-circle-24.png) Complete` |

### Emoji to Concept Mapping

Common emoji translations:

| Emoji | Query | Top Match |
|-------|-------|-----------|
| 🔒 🔐 | lock security | lock-secure-24 |
| ⚠️ | warning alert | warning-alert-24 |
| ✅ ✓ | success check complete | check-circle-24 |
| ❌ | error close remove | x-circle-24 |
| 🚀 | launch speed rocket | rocket-launch-24 |
| 📁 📂 | folder directory | folder-24 |
| 📄 📝 | document file | document-24 |
| ⚙️ 🔧 | settings config gear | gear-settings-24 |
| 👤 👥 | user profile person | user-circle-24 |
| 🔔 | notification alert bell | bell-notification-24 |
| 💳 | payment billing card | credit-card-24 |
| 🔍 | search find | search-magnify-24 |
| ➕ | add create plus | plus-add-24 |
| 🗑️ | delete trash remove | trash-delete-24 |
| 📤 📥 | upload download | upload-24, download-24 |
| 🔗 | link chain url | link-chain-24 |
| 📊 📈 | chart analytics | chart-bar-24 |
| ⏱️ 🕐 | time clock | clock-time-24 |
| 🏠 | home house | home-house-24 |
| 💡 | idea tip lightbulb | lightbulb-idea-24 |

---

## Quick Commands Reference

```bash
# === SEARCH ===
python icon-manager.py query "concept" --k 5 --output json

# === COVERAGE CHECK ===
python icon-manager.py residual "complex concept"
# Score > 0.4 = poor coverage

# === TRAVERSAL ===
python icon-manager.py traverse icon-id --axis valence --direction positive --steps 3

# === BATCH ===
python icon-manager.py batch-query --input concepts.txt --output results.json

# === PROVISIONING ===
python icon-manager.py provision --icons id1,id2,id3 --dest ./assets/icons/
python icon-manager.py provision --manifest manifest.json --dest ./assets/icons/
python icon-manager.py provision --query "search navigation user" --dest ./icons/ --k 2

# === EMOJI CONVERSION ===
python icon-manager.py scan-emoji --path ./docs --output emoji-report.json
python icon-manager.py convert-emoji --report emoji-report.json --dry-run
python icon-manager.py convert-emoji --report emoji-report.json --apply

# === CODE GENERATION ===
python icon-manager.py generate-imports --manifest manifest.json --format react --output Icons.tsx
python icon-manager.py generate-imports --manifest manifest.json --format vue --output icons.ts
python icon-manager.py generate-imports --manifest manifest.json --format css --output icons.css
```

---

## Semantic Axes

| Axis | Negative | Positive |
|------|----------|----------|
| valence | danger, error | success, safe |
| abstraction | literal, concrete | metaphorical, conceptual |
| energy | static, complete | active, in-progress |
| complexity | simple, minimal | detailed, rich |

---

## Decision Tree

```
Creating/editing content?
│
├─► Chat/conversation → Emoji OK, skip iconics
│
└─► Artifact/deliverable
    │
    ├─► New project with UI?
    │   └─► Bootstrap: extract concepts → batch query → provision
    │
    ├─► Existing repo with emojis?
    │   └─► Scan → review report → convert → provision
    │
    ├─► Adding single icon reference?
    │   └─► Query → provision single icon → reference in artifact
    │
    └─► Code-only, no UI → Skip iconics
```

---

## Output Integration

Query returns:
```json
{
  "results": [{"icon_id": "lock-secure-24", "path": "raw/lock-secure-24.png", "score": 0.85}],
  "residual_score": 0.12
}
```

Use `path` directly in artifacts. Copy to project assets if needed:
```bash
cp /home/zack/dev/iconics/raw/lock-secure-24.png ./src/assets/icons/
```

---

## When NOT to Use

- Casual conversation (emoji is fine)
- Code comments (text suffices)
- Terminal-only CLI output (no rendering context)
- When user explicitly requests emoji
- Rapid prototyping where placeholder is acceptable

---

## Common Concept Categories

Pre-mapped for quick reference:

| Concept | Primary Icon | Variants |
|---------|--------------|----------|
| Navigation/Home | home-house-24 | home-outline-24, home-filled-24 |
| Settings/Config | gear-settings-24 | cog-24, sliders-24 |
| User/Profile | user-circle-24 | user-outline-24, users-group-24 |
| Search | search-magnify-24 | search-outline-24 |
| Security/Lock | lock-secure-24 | shield-24, key-24 |
| Delete/Remove | trash-delete-24 | x-close-24, minus-remove-24 |
| Add/Create | plus-add-24 | plus-circle-24 |
| Edit/Modify | pencil-edit-24 | pen-24 |
| Save | save-disk-24 | check-save-24 |
| Warning | warning-alert-24 | exclamation-24 |
| Error | error-circle-24 | x-circle-24 |
| Success | check-circle-24 | checkmark-24 |
| Info | info-circle-24 | question-help-24 |

---

## Location

Iconics workspace: `/home/zack/dev/iconics/`
Icons directory: `/home/zack/dev/iconics/raw/`
This skill file: `/mnt/skills/user/iconics/SKILL.md`
