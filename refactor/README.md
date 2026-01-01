# ICONICS VECTOR SUBSPACE IMPLEMENTATION SPEC

Multi-agent orchestrated implementation of CLIP-based semantic retrieval for the iconics icon library, with LLM integration via skill-based CLI.

## Document Index

| File | Description |
|------|-------------|
| [01_ARCHITECTURE.md](01_ARCHITECTURE.md) | Mathematical foundations, file structure, success criteria |
| [02_PHASES.md](02_PHASES.md) | Implementation phases 1-8 with code specs |
| [03_AGENTS.md](03_AGENTS.md) | Agent definitions and prompt templates |
| [04_ORCHESTRATION_LOOP.md](04_ORCHESTRATION_LOOP.md) | Phase flow diagram with inputs/outputs/gates |
| [05_COMMUNICATION_PROTOCOL.md](05_COMMUNICATION_PROTOCOL.md) | Message types and inter-agent communication |
| [06_ORCHESTRATOR.md](06_ORCHESTRATOR.md) | Orchestrator class implementation |
| [07_VALIDATION_GATES.md](07_VALIDATION_GATES.md) | Per-phase validation checks |
| [08_CONFIGURATION.md](08_CONFIGURATION.md) | YAML config and environment variables |
| [09_CLI_COMMANDS.md](09_CLI_COMMANDS.md) | CLI reference for orchestrator and icon-manager |
| [10_LLM_SKILL.md](10_LLM_SKILL.md) | **NEW** LLM skill file for context-aware icon usage |

## Quick Start

```bash
# Full orchestrated build (includes LLM integration)
python orchestrate.py run --workspace /home/zack/dev/iconics --config config.yaml

# Or run phases manually
python icon-manager.py embed --model ViT-B/32
python icon-manager.py analyze-subspace --components 50
python icon-manager.py query "security protection" --k 10 --output json

# LLM Integration commands
python icon-manager.py batch-query --input concepts.txt --output manifest.json
python icon-manager.py provision --manifest manifest.json --dest ./assets/icons/
python icon-manager.py scan-emoji --path ./docs --output emoji-report.json
python icon-manager.py convert-emoji --report emoji-report.json --apply
```

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                     ORCHESTRATOR                             │
│  Manages phase execution, validation, agent coordination     │
└──────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│   ARCHITECT   │◄──►│  SPECIALIST   │◄──►│  SPECIALIST   │
│  (Phase 0,6,8)│    │   AGENTS      │    │   AGENTS      │
└───────────────┘    └───────────────┘    └───────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                      ICONICS                                 │
│  embeddings/ │ subspace/ │ index/ │ src/ │ eval/ │ skill/   │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                    LLM INTEGRATION                           │
│  SKILL.md triggers → CLI commands → JSON output → LLM acts   │
└──────────────────────────────────────────────────────────────┘
```

## Agents

| Agent | Role | Owns |
|-------|------|------|
| architect | Lead System Architect | architecture_decision.md, validation_report.md |
| embedding_engineer | CLIP Embedding Specialist | iconics_embeddings.py, embeddings/* |
| linear_algebra_specialist | Subspace Analysis Expert | iconics_subspace.py, iconics_correlation.py, subspace/* |
| retrieval_engineer | Search & Retrieval Specialist | iconics_retrieval.py, iconics_index.py, index/* |
| evaluation_specialist | Metrics & Evaluation Expert | iconics_eval.py, eval/* |
| integration_engineer | CLI & System Integration | icon-manager.py extensions |
| **llm_integration_engineer** | **LLM Integration Specialist** | **iconics_provision.py, iconics_emoji.py, skill/SKILL.md** |

## Phase Summary

| Phase | Agent | Key Outputs | Gate |
|-------|-------|-------------|------|
| 0 | architect | architecture_decision.md | Human approval |
| 1 | embedding_engineer | icon_embeddings.npy | Auto-validate |
| 2 | linear_algebra_specialist | basis_vectors.npy, semantic_mapping.json | Architect approval |
| 3 | retrieval_engineer | IconicsRetriever, faiss_flat.index | Auto-validate |
| 4 | evaluation_specialist | ground_truth.json, baseline_comparison.json | Architect approval |
| 5 | integration_engineer | Updated icon-manager.py | Auto-validate |
| 6 | architect | validation_report.md | Architect approval |
| **7** | **llm_integration_engineer** | **provision/emoji commands, SKILL.md** | **Architect approval** |
| **8** | **architect** | **final_validation_report.md** | **Human + Architect** |

## Success Criteria

1. **Retrieval quality**: Projected retrieval beats raw CLIP on conceptual queries
2. **Interpretability**: ≥3 PCs correlate strongly (r > 0.5) with existing metadata
3. **Efficiency**: Query latency < 50ms for 8k icons
4. **Dimensionality**: Effective dimension < 100 (compression from 512)
5. **Coverage**: Orthogonal residual analysis identifies gaps in icon library
6. **LLM Integration**: Skill file enables context-aware icon retrieval without MCP overhead

## LLM Integration

### Why Skill-Based, Not MCP

MCP adds runtime overhead. The skill-based approach:
- Zero runtime overhead (context injection only)
- Uses existing CLI (no new servers)
- Trigger-based activation (LLM learns when to invoke)

### Trigger Conditions

The skill teaches LLMs to use iconics when:
1. About to write emoji in artifacts (not chat)
2. Creating documentation
3. Building websites/frontends
4. Developing applications
5. Processing repos with emoji usage

### Key LLM Commands

```bash
# Batch query for project bootstrapping
python icon-manager.py batch-query --input concepts.txt --output results.json

# Provision icons to project
python icon-manager.py provision --manifest results.json --dest ./assets/icons/

# Scan for emoji usage
python icon-manager.py scan-emoji --path ./docs --output emoji-report.json

# Convert emojis to icon references
python icon-manager.py convert-emoji --report emoji-report.json --apply

# Generate framework imports
python icon-manager.py generate-imports --manifest manifest.json --format react --output Icons.tsx
```

### Hosting Strategy

8k icons can't live in every project. Solution: project-local provisioning.

```
iconics/                    (source library)
└── raw/                    (8,000 icons)

your-project/               (destination)
└── assets/icons/           (only icons this project uses)
    ├── lock-secure-24.png
    └── manifest.json
```

## Dependencies

```
torch>=2.0
transformers
open-clip-torch
numpy
scipy
faiss-cpu
scikit-learn
pandas
matplotlib
pyyaml
emoji
```

## Related Work

This architecture draws from:
- CLIP (Radford et al. 2021) for visual-semantic alignment
- Protocol Genome theory for orthogonal dimension identification
- UISearch for graph-based UI element retrieval
- Hyperbolic embeddings for hierarchical structure (stretch goal)
