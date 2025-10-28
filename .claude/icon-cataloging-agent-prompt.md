# Icon Cataloging Agent Task

## Mission
Systematically catalog all uncataloged icons in `/home/zack/dev/iconics/raw/` by adding semantic names, tags, and categories to the icon-catalog.json database.

## Context
- **Repository:** https://github.com/johnzfitch/iconics
- **Current Status:** 9 icons cataloged out of 1,700+
- **Tool:** `/home/zack/dev/iconics/icon-manager.py`
- **Goal:** Catalog 100+ high-value icons in this session

## Cataloging Strategy

### Phase 1: High-Priority Icons (Target: 50 icons)
Focus on commonly used icons across GitHub projects:

**Categories to prioritize:**
1. **UI Elements** (buttons, controls, indicators)
   - Examples: checkbox, radio, slider, toggle, dropdown
2. **Development** (code, git, debugging)
   - Examples: code, git, branch, commit, bug, test, api
3. **Files** (documents, formats, operations)
   - Examples: file, document, pdf, zip, csv, json, xml
4. **Security** (already started, expand)
   - Examples: key, fingerprint, certificate, vault, encryption
5. **Navigation** (arrows, directions)
   - Examples: arrow-up, arrow-down, arrow-left, arrow-right, home, back
6. **Communication** (messaging, social)
   - Examples: email, message, chat, notification, bell
7. **Tools** (already started, expand)
   - Examples: settings, gear, wrench, hammer, screwdriver

### Phase 2: Medium-Priority Icons (Target: 30 icons)
8. **Network** (already started, expand)
   - Examples: wifi, ethernet, cloud, server, router
9. **Media** (audio, video, images)
   - Examples: play, pause, stop, volume, camera, image, video
10. **Business** (commerce, finance)
    - Examples: cart, payment, money, credit-card, invoice
11. **Time** (calendars, clocks)
    - Examples: calendar, clock, timer, schedule, deadline
12. **People** (users, profiles)
    - Examples: user, profile, avatar, team, group

### Phase 3: Lower-Priority Icons (Target: 20 icons)
13. **Emoji** (expressions, emotions)
14. **Miscellaneous** (anything useful that doesn't fit above)

## Icon Discovery Process

### Step 1: Identify Uncataloged Icons
```bash
cd /home/zack/dev/iconics

# Check current catalog
python3 icon-manager.py stats

# List some uncataloged files in raw/
ls raw/ | head -50
```

### Step 2: Visual Inspection Strategy

For icons with descriptive filenames (e.g., "Lock.png", "Shield.png"):
- Use the filename as a starting point for semantic naming
- Verify by reading the icon visually if needed

For icons with numeric filenames (e.g., "100.png", "101.png"):
- Read the icon file using the Read tool to see what it depicts
- Assign semantic name based on visual appearance

### Step 3: Add to Catalog

Use the icon-manager.py tool:

```bash
python3 icon-manager.py add "<filename-without-extension>" "<semantic-name>" \
  --tags <tag1> <tag2> <tag3> <tag4> \
  --category <category> \
  --description "Brief description"
```

**Example:**
```bash
python3 icon-manager.py add "Key" "key" \
  --tags security key access password authentication \
  --category security \
  --description "Key icon for authentication and access control"
```

## Naming Conventions

### Semantic Names
- **Lowercase with hyphens:** arrow-up, user-profile, credit-card
- **Descriptive but concise:** 1-3 words maximum
- **Avoid ambiguity:** "file-text" not just "file"

### Tags (4-6 tags recommended)
1. **Primary purpose:** what the icon represents
2. **Synonyms:** alternative names
3. **Use cases:** when you'd use it
4. **Related concepts:** associated terms

**Good example:**
```
semantic: credit-card
tags: payment credit-card purchase transaction finance
```

**Bad example:**
```
semantic: card
tags: icon thing payment
```

### Categories (use existing 7 categories)
- files
- network
- security
- tools
- ui
- emoji
- development

### Descriptions
- One sentence, clear and specific
- Describe what it represents, not what it looks like
- **Good:** "Email icon for messaging and communication"
- **Bad:** "Blue envelope icon"

## Workflow

### 1. Batch Discovery (10-20 icons at a time)
```bash
# List icons with descriptive names first (easier to catalog)
ls raw/ | grep -iE "lock|key|user|file|folder|email|network|settings" | head -20

# Then look at a sample of numbered icons
ls raw/ | grep -E "^[0-9]+\.png$" | head -20
```

### 2. Catalog Each Icon
For each icon:
```bash
# If descriptive filename, catalog directly
python3 icon-manager.py add "Filename" "semantic-name" \
  --tags tag1 tag2 tag3 \
  --category category

# If numeric filename, read it first to see what it depicts
```

### 3. Verify Catalog Entry
```bash
# Search to verify it was added
python3 icon-manager.py search semantic-name

# Check stats
python3 icon-manager.py stats
```

### 4. Commit Progress Regularly
Every 25-50 icons cataloged:
```bash
git add icon-catalog.json catalog/
git commit -m "feat: Catalog [N] icons - [category focus]

Added [N] icons to catalog:
- [category1]: [count] icons
- [category2]: [count] icons

Total cataloged: [new total]"

git push origin master
```

## Special Cases

### Icons with Multiple Variants
If you find icons like "User.png", "User-2.png", "User-male.png":
- Catalog the primary one first: "user"
- Add variants as: "user-male", "user-female", "user-avatar"
- Tag them all similarly for searchability

### Branded/Social Icons
Found icons like "Twitter.ico", "Facebook.png":
- Category: ui (or create social if many exist)
- Tags: include brand name + "social" + "media"
- Semantic: lowercase brand name (twitter, facebook)

### Size Variants
Found "Icon 16x16.png", "Icon 24x24.png":
- Catalog the clearest/most usable size
- Note in description if multiple sizes exist
- For now, focus on 16x16 as primary

## Success Criteria

### Minimum Goals
- ✅ 100 icons cataloged (from current 9)
- ✅ All 7 categories have at least 5 icons each
- ✅ Security category expanded to 10+ icons
- ✅ Development category has 15+ icons
- ✅ UI category has 20+ icons

### Ideal Goals
- ✅ 150+ icons cataloged
- ✅ Updated README.md with new stats
- ✅ All changes committed and pushed to GitHub
- ✅ Created progress report

## Quality Checks

Before committing:
1. **Verify no duplicates:** Search for similar semantic names
2. **Check tagging consistency:** Similar icons should have similar tags
3. **Test search:** Try searching for common terms
4. **Validate categories:** All icons have valid categories

## Final Steps

### 1. Update README.md Stats
Edit the README badges and stats:
```markdown
![Cataloged](https://img.shields.io/badge/cataloged-[NEW_COUNT]-orange.svg)

## Library Stats
- **Total Icons:** 1,700+ PNG files
- **Cataloged:** [NEW_COUNT] icons (expanding)
```

### 2. Create Progress Report
Document what was cataloged:
```markdown
## Cataloging Session Report

**Date:** 2025-10-28
**Icons Cataloged:** [COUNT]
**Starting Count:** 9
**Ending Count:** [NEW_TOTAL]

### By Category:
- security: [count] icons
- development: [count] icons
- ui: [count] icons
- tools: [count] icons
- files: [count] icons
- network: [count] icons
- emoji: [count] icons

### Most Useful Additions:
- [list top 10 most useful icons added]
```

### 3. Final Commit and Push
```bash
git add README.md
git commit -m "docs: Update stats after cataloging session

Cataloged [N] icons across all categories.
Updated README badges and library stats.

New total: [TOTAL] cataloged icons"

git push origin master
```

## Important Notes

### DO:
- ✅ Read icons visually when filenames are unclear
- ✅ Commit progress regularly (every 25-50 icons)
- ✅ Focus on high-value, commonly-used icons first
- ✅ Use consistent naming conventions
- ✅ Add 4-6 tags per icon for good searchability
- ✅ Test searches periodically to verify cataloging quality

### DON'T:
- ❌ Catalog every icon - focus on useful ones
- ❌ Use vague or generic semantic names
- ❌ Rush through without visual verification
- ❌ Forget to push changes to GitHub
- ❌ Skip updating the README stats at the end
- ❌ Create new categories (use the existing 7)

## Expected Output

At the end of this task, provide:

1. **Summary Statistics:**
   - Starting count: 9
   - Icons cataloged: [N]
   - Ending count: [TOTAL]
   - Time taken: [duration]

2. **Category Breakdown:**
   - List count per category

3. **Notable Additions:**
   - Top 10-15 most useful icons added

4. **Git Status:**
   - Number of commits made
   - Confirmation of push to GitHub
   - Link to updated repository

5. **Recommendations:**
   - What should be cataloged next session
   - Any naming/organizational improvements

---

**Ready to Begin!**

Start by checking the current state, then proceed with Phase 1 high-priority icons.
