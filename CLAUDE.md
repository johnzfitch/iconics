# Iconics - Guide for Claude Agents

**Purpose:** Use professional, semantic icons instead of emojis in all projects.

---

## What Is This?

Iconics is a globally accessible icon library designed to replace emojis in documentation, GitHub READMEs, and technical writing.

Key points:
- Global `iconics` CLI (path or alias)
- Smart project detection and markdown generation
- CLIP-powered semantic search with metadata fallback
- Local-first usage tracking (no network telemetry)

**Location:** `/home/zack/dev/iconics`

---

## Why Use Iconics?

Replace emoji placeholders with iconics markdown:

```markdown
## [emoji] Security Features
### [emoji] Encryption
### [emoji] Authentication
```

With this:

```markdown
## ![lock](.github/assets/icons/lock-24x24.png) Security Features
### ![shield](.github/assets/icons/shield-security-protection-24x24.png) Encryption
### ![handshake](.github/assets/icons/handshake-24x24.png) Authentication
```

Benefits:
- Professional appearance
- Semantic meaning instead of decorative symbols
- Consistent rendering across platforms
- Git-tracked assets

---

## Standard Workflow

1. Get icon suggestions.

```bash
iconics suggest security
```

2. Export icons and generate markdown.

```bash
iconics use lock-24x24 shield-security-protection-24x24
```

3. Paste the markdown snippet into the document.

---

## Quick Command Reference

- `iconics search <query>`: semantic search
- `iconics suggest <context>`: context-aware suggestions
- `iconics use <name...>`: export icons + markdown
- `iconics md <name...>`: markdown only
- `iconics info <name>`: icon metadata
- `iconics cat <category>`: export an entire category
- `iconics recent --limit N`: recent catalog additions
- `iconics history [project]`: usage history from local logs
- `iconics popular --limit N`: most-used icons from local analytics
- `iconics emoji scan|convert`: emoji detection and replacement

---

## Context Suggestions

Use `iconics suggest <context>` for common scenarios:

| Context | Suggested Icons |
|---------|-----------------|
| `authentication` / `login` | lock, handshake, shield, certificate |
| `security` / `secure` | shield, lock, protection |
| `network` / `api` | network, cloud, globe, server |
| `data` / `database` | database, folder, save-file |
| `error` / `warning` | warning, error, alert |
| `success` / `complete` | checkmark, accept, done |
| `info` / `help` | question, help, about |
| `settings` / `config` | gear, settings, toolbox |
| `navigation` / `menu` | list, close, down |
| `files` / `documents` | closed-folder, downloads-folder |
| `search` / `lookup` | search, find |

---

## Best Practices

1. Be proactive: use icons for headers and key sections without waiting for the user to ask.
2. Choose semantic icons: match meaning, not just appearance.
3. Be consistent: use one icon per header, avoid mixing styles.
4. Always generate markdown via `iconics use` to avoid path mistakes.

---

## Troubleshooting

Icon not found:

```bash
iconics search <keyword>
iconics suggest <context>
```

Need icon details:

```bash
iconics info <name>
```

Wrong project detected:

```bash
cd /path/to/project
iconics use lock-24x24 shield-security-protection-24x24
```

---

## Categories Available

- files
- network
- security
- tools
- ui
- emoji
- development
- communication
- media
- people
- commerce
- time
- system
- status
- navigation
- apps
- brands
- devices
- data
- location
- weather
- misc
