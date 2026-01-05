# CLI COMMANDS

## Orchestrator Commands

```bash
# Full orchestrated build (now includes LLM integration phases)
python orchestrate.py run --workspace /home/zack/dev/iconics --config config.yaml

# Resume from specific phase
python orchestrate.py run --workspace /home/zack/dev/iconics --start-phase 3

# Run single phase (for debugging)
python orchestrate.py run-phase 2 --workspace /home/zack/dev/iconics

# Run LLM integration phase only
python orchestrate.py run-phase 7 --workspace /home/zack/dev/iconics

# Validate existing outputs without re-running
python orchestrate.py validate --workspace /home/zack/dev/iconics

# Show orchestration status
python orchestrate.py status --workspace /home/zack/dev/iconics

# Generate report from completed run
python orchestrate.py report --workspace /home/zack/dev/iconics --output report.md
```

---

## Icon Manager Commands (Extended)

### Embedding Generation
```bash
# Generate embeddings with default settings
python icon-manager.py embed

# Specify model and batch size
python icon-manager.py embed --model ViT-L/14 --batch-size 32

# Force regeneration (overwrite existing)
python icon-manager.py embed --force

# Use CPU instead of GPU
python icon-manager.py embed --device cpu

# Verbose output
python icon-manager.py embed -v
```

### Subspace Analysis
```bash
# Analyze with automatic component selection
python icon-manager.py analyze-subspace

# Specify number of components
python icon-manager.py analyze-subspace --components 50

# Set variance threshold for automatic selection
python icon-manager.py analyze-subspace --variance-threshold 0.99

# Generate scree plot
python icon-manager.py analyze-subspace --plot scree.png

# Skip correlation analysis
python icon-manager.py analyze-subspace --skip-correlation
```

### Query Icons
```bash
# Text query with default settings
python icon-manager.py query "danger confirmation action"

# Specify number of results
python icon-manager.py query "folder organization" --k 20

# Use different retrieval modes
python icon-manager.py query "data protection" --mode raw
python icon-manager.py query "data protection" --mode projected
python icon-manager.py query "data protection" --mode weighted

# Filter by category
python icon-manager.py query "warning" --category alerts

# Filter by style
python icon-manager.py query "user profile" --style outline

# Output as JSON (required for LLM consumption)
python icon-manager.py query "settings gear" --output json

# Image query (find similar icons)
python icon-manager.py query --image /path/to/reference.png --k 10
```

### Batch Query (NEW)
```bash
# Query multiple concepts from file
python icon-manager.py batch-query --input concepts.txt --output results.json

# Specify results per concept
python icon-manager.py batch-query --input concepts.txt --output results.json --k 3

# Concepts file format (one concept per line):
# security lock authentication
# user profile account
# warning alert danger
# navigation menu home
```

### Semantic Axis Traversal
```bash
# Traverse along principal component
python icon-manager.py traverse lock-semantic-32 --axis 3 --steps 5

# Specify direction
python icon-manager.py traverse warning-alert-24 --axis 7 --direction positive
python icon-manager.py traverse warning-alert-24 --axis 7 --direction negative
python icon-manager.py traverse warning-alert-24 --axis 7 --direction both

# Use named axis (from semantic mapping)
python icon-manager.py traverse heart-favorite-16 --axis valence --steps 10

# Output as gallery HTML
python icon-manager.py traverse folder-open-32 --axis abstraction --output gallery.html
```

### Icon Interpolation
```bash
# Find icons between two reference icons
python icon-manager.py interpolate lock-secure-24 unlock-open-24 --steps 5

# Output as JSON
python icon-manager.py interpolate star-empty-16 star-filled-16 --output json
```

### Evaluation
```bash
# Run evaluation with default ground truth
python icon-manager.py eval-retrieval

# Specify custom test set
python icon-manager.py eval-retrieval --test-set custom_ground_truth.json

# Compare specific methods
python icon-manager.py eval-retrieval --methods raw,projected,semantic_matcher

# Output detailed report
python icon-manager.py eval-retrieval --report eval_report.md

# Run ablation on component count
python icon-manager.py eval-retrieval --ablation-components 10,25,50,75,100
```

### Method Comparison
```bash
# Compare methods on query file
python icon-manager.py compare-methods --queries test_queries.txt

# Side-by-side output
python icon-manager.py compare-methods --queries test_queries.txt --side-by-side

# Statistical significance testing
python icon-manager.py compare-methods --queries test_queries.txt --significance
```

### Utility Commands
```bash
# Show subspace info
python icon-manager.py subspace-info

# List semantic axes with correlations
python icon-manager.py list-axes

# Compute orthogonal residual for query
python icon-manager.py residual "abstract concept with no icon"

# Find library gaps (high residual queries)
python icon-manager.py find-gaps --queries common_queries.txt --threshold 0.5

# Export embeddings for external use
python icon-manager.py export-embeddings --format numpy --output embeddings.npz
python icon-manager.py export-embeddings --format csv --output embeddings.csv

# Rebuild index
python icon-manager.py rebuild-index --type flat
python icon-manager.py rebuild-index --type ivf --nlist 100
```

---

## LLM Integration Commands (NEW)

### Icon Provisioning
```bash
# Provision specific icons by ID
python icon-manager.py provision --icons lock-secure-24,user-circle-24,trash-delete-24 --dest ./assets/icons/

# Provision from manifest file
python icon-manager.py provision --manifest icon-manifest.json --dest ./assets/icons/

# Provision icons matching query (find + copy)
python icon-manager.py provision --query "navigation menu home settings" --dest ./src/assets/icons/ --k 2

# Provision with custom manifest filename
python icon-manager.py provision --icons lock-secure-24 --dest ./icons/ --manifest-name icons.json

# Dry run (show what would be copied)
python icon-manager.py provision --query "security" --dest ./icons/ --dry-run
```

### Emoji Scanning
```bash
# Scan directory for emoji usage
python icon-manager.py scan-emoji --path /path/to/repo --output emoji-report.json

# Specify file extensions
python icon-manager.py scan-emoji --path ./docs --extensions md,mdx,tsx,jsx,html --output report.json

# Non-recursive scan
python icon-manager.py scan-emoji --path ./src --no-recursive --output report.json

# Filter by minimum confidence
python icon-manager.py scan-emoji --path . --min-confidence 0.8 --output report.json
```

### Emoji Conversion
```bash
# Preview changes (dry run)
python icon-manager.py convert-emoji --report emoji-report.json --dry-run

# Apply conversions
python icon-manager.py convert-emoji --report emoji-report.json --icon-path assets/icons --apply

# Apply with custom icon path format
python icon-manager.py convert-emoji --report emoji-report.json --icon-path ./icons --format "![{alt}]({path})" --apply

# Interactive mode (confirm each change)
python icon-manager.py convert-emoji --report emoji-report.json --interactive
```

### Import Generation
```bash
# Generate React imports
python icon-manager.py generate-imports --manifest ./assets/icons/manifest.json --format react --output ./src/components/Icons.tsx

# Generate Vue imports
python icon-manager.py generate-imports --manifest manifest.json --format vue --output ./src/icons.ts

# Generate CSS classes
python icon-manager.py generate-imports --manifest manifest.json --format css --output ./src/styles/icons.css

# Generate TypeScript constants
python icon-manager.py generate-imports --manifest manifest.json --format typescript --output ./src/icons.ts

# Custom import path prefix
python icon-manager.py generate-imports --manifest manifest.json --format react --path-prefix "@/assets/icons" --output Icons.tsx
```

---

## Command Reference

| Command | Agent Owner | Phase | LLM Integration |
|---------|-------------|-------|-----------------|
| `embed` | embedding_engineer | 1 | - |
| `analyze-subspace` | linear_algebra_specialist | 2 | - |
| `query` | retrieval_engineer | 3 | Core |
| `batch-query` | llm_integration_engineer | 7 | Core |
| `traverse` | retrieval_engineer | 3 | - |
| `interpolate` | retrieval_engineer | 3 | - |
| `eval-retrieval` | evaluation_specialist | 4 | - |
| `compare-methods` | evaluation_specialist | 4 | - |
| `subspace-info` | linear_algebra_specialist | 2 | - |
| `list-axes` | linear_algebra_specialist | 2 | - |
| `residual` | retrieval_engineer | 3 | Core |
| `find-gaps` | retrieval_engineer | 3 | - |
| `export-embeddings` | embedding_engineer | 1 | - |
| `rebuild-index` | retrieval_engineer | 3 | - |
| `provision` | llm_integration_engineer | 7 | Core |
| `scan-emoji` | llm_integration_engineer | 7 | Core |
| `convert-emoji` | llm_integration_engineer | 7 | Core |
| `generate-imports` | llm_integration_engineer | 7 | Core |

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |
| 3 | File not found |
| 4 | Validation failed |
| 5 | Timeout |
| 10 | Embeddings not generated |
| 11 | Subspace not analyzed |
| 12 | Index not built |
| 20 | Provisioning failed |
| 21 | Emoji scan failed |
| 22 | Emoji conversion failed |
| 23 | Import generation failed |

---

## Example Workflows

### Initial Setup
```bash
# 1. Generate embeddings
python icon-manager.py embed --model ViT-B/32

# 2. Analyze subspace
python icon-manager.py analyze-subspace --components 50

# 3. Verify with sample queries
python icon-manager.py query "delete remove trash" --k 5
python icon-manager.py query "security lock protection" --k 5

# 4. Run evaluation
python icon-manager.py eval-retrieval --report initial_eval.md
```

### Quality Upgrade
```bash
# Switch to higher quality model
python icon-manager.py embed --model ViT-L/14 --force

# Re-analyze subspace
python icon-manager.py analyze-subspace

# Compare quality
python icon-manager.py compare-methods --queries test_queries.txt
```

### Find Missing Icons
```bash
# Generate common queries file
cat > common_queries.txt << EOF
machine learning model
cryptocurrency blockchain
video conference call
cloud storage sync
EOF

# Find gaps
python icon-manager.py find-gaps --queries common_queries.txt --threshold 0.4
```

### Project Bootstrapping (LLM Workflow)
```bash
# 1. Define concepts for your project
cat > concepts.txt << EOF
user authentication login
file upload document
team group sharing
notification alert bell
billing payment card
settings configuration
EOF

# 2. Batch query to find best icons
python icon-manager.py batch-query --input concepts.txt --output icon-manifest.json --k 2

# 3. Provision icons to project
python icon-manager.py provision --manifest icon-manifest.json --dest ./src/assets/icons/

# 4. Generate React imports
python icon-manager.py generate-imports --manifest ./src/assets/icons/manifest.json --format react --output ./src/components/Icons.tsx
```

### Emoji Conversion (LLM Workflow)
```bash
# 1. Scan repo for emoji
python icon-manager.py scan-emoji --path ./docs --output emoji-report.json

# 2. Review report
cat emoji-report.json | jq '.occurrences[] | {file, emoji, suggested_icon, confidence}'

# 3. Provision suggested icons
python icon-manager.py provision --manifest emoji-report.json --dest ./assets/icons/

# 4. Preview conversions
python icon-manager.py convert-emoji --report emoji-report.json --dry-run

# 5. Apply conversions
python icon-manager.py convert-emoji --report emoji-report.json --icon-path assets/icons --apply
```

### Full LLM Integration Test
```bash
# End-to-end test of all LLM workflows
python icon-manager.py batch-query --input test_concepts.txt --output /tmp/manifest.json --k 1
python icon-manager.py provision --manifest /tmp/manifest.json --dest /tmp/icons/
echo "# 🔒 Test" > /tmp/test.md
python icon-manager.py scan-emoji --path /tmp --output /tmp/emoji.json
python icon-manager.py convert-emoji --report /tmp/emoji.json --icon-path /tmp/icons --dry-run
python icon-manager.py generate-imports --manifest /tmp/icons/manifest.json --format react --output /tmp/Icons.tsx
```

---

## JSON Output Format

All commands support `--output json` for LLM consumption:

### Query Output
```json
{
  "query": "security lock",
  "results": [
    {
      "icon_id": "lock-secure-24",
      "path": "raw/lock-secure-24.png",
      "score": 0.847,
      "category": "security",
      "style": "outline"
    }
  ],
  "residual_score": 0.12,
  "query_projected": true,
  "mode": "projected"
}
```

### Batch Query Output
```json
{
  "queries": [
    {
      "concept": "security lock",
      "results": [{"icon_id": "lock-secure-24", "score": 0.85}],
      "residual_score": 0.12
    },
    {
      "concept": "user profile",
      "results": [{"icon_id": "user-circle-24", "score": 0.91}],
      "residual_score": 0.08
    }
  ],
  "total_icons_found": 2
}
```

### Provision Output
```json
{
  "provisioned": [
    {"icon_id": "lock-secure-24", "dest": "./assets/icons/lock-secure-24.png", "size_bytes": 1234},
    {"icon_id": "user-circle-24", "dest": "./assets/icons/user-circle-24.png", "size_bytes": 987}
  ],
  "manifest_path": "./assets/icons/manifest.json",
  "total_size_kb": 2.2
}
```

### Emoji Scan Output
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
    }
  ]
}
```
