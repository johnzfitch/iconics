# ICONICS VECTOR SUBSPACE ARCHITECTURE

## Context

You are implementing a CLIP-based semantic retrieval system for an icon library called "iconics". The library contains ~8,000 icons with existing metadata in `icon-catalog.json`. The current system uses text-based semantic matching with hand-engineered features (metaphor, emotional_valence, abstraction_level, action_type). We are replacing/augmenting this with a principled vector space approach.

## Goal

Build a retrieval system where:
1. Icons are embedded via CLIP's vision encoder into a shared visual-semantic space
2. Queries (text or image) are embedded via CLIP's text/vision encoder
3. The "iconics subspace" is explicitly modeled as a linear subspace of CLIP space
4. Retrieval happens via projection onto this subspace followed by nearest-neighbor search
5. The orthogonal structure within the subspace reveals interpretable semantic dimensions
6. **LLMs can consume icons via skill-based CLI integration with trigger-aware context injection**

## Mathematical Foundation

Let V = ℝ^d be CLIP's embedding space (d=512 for ViT-B/32).

Let X ∈ ℝ^(n×d) be the matrix of n icon embeddings (rows are icons).

The iconics subspace I = rowspan(X) ⊂ V.

SVD decomposition: X = UΣVᵀ where:
- U ∈ ℝ^(n×n): left singular vectors (icon coefficients)
- Σ ∈ ℝ^(n×d): singular values (importance of each dimension)  
- V ∈ ℝ^(d×d): right singular vectors (semantic basis of icon-space)

For query q ∈ V:
- Projection onto iconics subspace: q_I = V_k V_k^T q (using top-k components)
- Coordinates in icon-basis: c = V_k^T q
- Orthogonal residual: q_⊥ = q - q_I

## File Structure

```
r
```

## Dependencies

```
torch>=2.0
transformers
open-clip-torch
numpy
scipy
faiss-cpu  # or faiss-gpu
scikit-learn
pandas
matplotlib  # for visualization
emoji       # for emoji detection
```

## Success Criteria

1. **Retrieval quality**: Projected retrieval beats raw CLIP on conceptual queries
2. **Interpretability**: At least 3 PCs correlate strongly (r > 0.5) with existing metadata
3. **Efficiency**: Query latency < 50ms for 8k icons
4. **Dimensionality**: Effective dimension < 100 (compression from 512)
5. **Coverage**: Orthogonal residual analysis identifies gaps in icon library
6. **LLM Integration**: Skill file enables context-aware icon retrieval without MCP overhead

## LLM Integration Strategy

### Why Skill-Based, Not MCP

MCP (Model Context Protocol) adds runtime overhead and infrastructure complexity. For iconics, a skill-based approach is more efficient:

- **Zero runtime overhead**: Skill file is context injection, not a service
- **Uses existing CLI**: No new server infrastructure needed
- **Trigger-based activation**: LLM learns when to invoke iconics contextually

### Trigger Conditions

The skill teaches LLMs to use iconics when:
1. About to write emoji in artifacts/deliverables (not chat)
2. Creating documentation (README, guides, specs)
3. Building websites/frontends (navigation, actions, status)
4. Developing applications (GUI, toolbars, dialogs)
5. Processing existing repos with emoji usage

### Hosting Strategy

**Problem**: 8k icons can't live in every project repo.

**Solution**: Project-local provisioning. Icons are copied from the master library to individual projects on demand.

```
iconics/                    (source library)
└── raw/                    (8,000 icons)

your-project/               (destination)
└── assets/icons/           (only icons this project uses)
    ├── lock-secure-24.png
    └── manifest.json       (tracks provisioned icons)
```

## Notes for Implementation

1. Start with ViT-B/32 for speed, upgrade to ViT-L/14 if quality insufficient
2. Normalize all embeddings to unit norm before SVD
3. Use randomized SVD for efficiency if needed (sklearn.utils.extmath.randomized_svd)
4. The projection matrix P = V_k @ V_k.T can be precomputed and cached
5. For incremental updates, consider online SVD or periodic recomputation
6. Store icon_id -> embedding mapping bidirectionally for fast lookup both ways
7. All CLI commands must support `--output json` for LLM consumption
8. Residual score should be included in query output by default

## Stretch Goals

1. **Hyperbolic projection**: After subspace projection, map to Poincaré ball for hierarchical retrieval
2. **Polysemous embeddings**: Train attention heads to produce multiple embeddings per icon
3. **Cross-modal bridge**: Learn linear map between iconics subspace and LLM embedding space
4. **Active learning**: Use orthogonal residuals to identify queries that need new icons
5. **CDN hosting**: For web projects, optional CDN-hosted icon URLs instead of local copies
