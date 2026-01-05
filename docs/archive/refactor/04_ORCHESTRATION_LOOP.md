# ORCHESTRATION LOOP

```
┌─────────────────────────────────────────────────────────────────────┐
│                     ORCHESTRATOR MAIN LOOP                         │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 0: ARCHITECTURE REVIEW                                        │
│ Agent: architect                                                    │
│ Input: Full system prompt, existing icon-manager.py                 │
│ Output: architecture_decision.md                                    │
│   - Confirmed file structure                                        │
│   - Interface contracts between modules                             │
│   - Risk assessment                                                 │
│   - Phase dependencies graph                                        │
│ Gate: Human approval on architecture                                │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 1: EMBEDDING GENERATION                                       │
│ Agent: embedding_engineer                                           │
│ Input: architecture_decision.md, raw/ directory                     │
│ Output:                                                             │
│   - src/iconics_embeddings.py                                       │
│   - embeddings/icon_embeddings.npy                                  │
│   - embeddings/icon_index.json                                      │
│   - embeddings/metadata.json                                        │
│ Validation:                                                         │
│   - All icons in raw/ have embeddings                               │
│   - Embeddings are unit normalized (‖e‖ = 1 ± 1e-6)                 │
│   - No NaN/Inf values                                               │
│   - Metadata matches icon-catalog.json count                        │
│ Gate: Validation passes → proceed; else → retry with feedback       │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 2: SUBSPACE ANALYSIS                                          │
│ Agent: linear_algebra_specialist                                    │
│ Input: embeddings/*, icon-catalog.json (for metadata correlation)   │
│ Output:                                                             │
│   - src/iconics_subspace.py                                         │
│   - src/iconics_correlation.py                                      │
│   - subspace/singular_values.npy                                    │
│   - subspace/basis_vectors.npy                                      │
│   - subspace/effective_dim.json                                     │
│   - subspace/component_analysis.json                                │
│   - subspace/semantic_mapping.json                                  │
│ Validation:                                                         │
│   - SVD reconstruction error < 1e-10                                │
│   - Effective dim selected with clear criteria                      │
│   - At least 3 PCs correlate with metadata (p < 0.01)               │
│   - Component analysis includes top/bottom 10 icons per PC          │
│ Gate: Validation passes + architect reviews semantic_mapping.json   │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 3: RETRIEVAL ENGINE                                           │
│ Agent: retrieval_engineer                                           │
│ Input: embeddings/*, subspace/*, architecture_decision.md           │
│ Output:                                                             │
│   - src/iconics_retrieval.py                                        │
│   - src/iconics_index.py                                            │
│   - index/faiss_flat.index                                          │
│   - index/faiss_ivf.index (if n > 10k)                              │
│ Validation:                                                         │
│   - All IconicsRetriever methods implemented                        │
│   - Query latency < 50ms on flat index                              │
│   - retrieve() returns valid icon_ids                               │
│   - retrieve() includes residual_score in output                    │
│   - project_to_iconics() output satisfies ‖q_I‖² + ‖q_⊥‖² ≈ ‖q‖²   │
│ Gate: Unit tests pass + latency benchmark meets criteria            │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 4: EVALUATION FRAMEWORK                                       │
│ Agent: evaluation_specialist                                        │
│ Input: src/iconics_retrieval.py, existing SemanticMatcher code      │
│ Output:                                                             │
│   - src/iconics_eval.py                                             │
│   - eval/ground_truth.json (50+ curated query-result pairs)         │
│   - eval/test_queries.txt (100+ test queries by category)           │
│   - eval/results/baseline_comparison.json                           │
│ Validation:                                                         │
│   - Metrics implementation matches standard definitions             │
│   - Ground truth has coverage across query types                    │
│   - Comparison shows projected vs raw vs SemanticMatcher            │
│ Gate: Evaluation report reviewed by architect                       │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 5: CLI INTEGRATION                                            │
│ Agent: integration_engineer                                         │
│ Input: All src/*.py modules, existing icon-manager.py               │
│ Output:                                                             │
│   - Updated icon-manager.py with new commands                       │
│   - README.md updates                                               │
│   - requirements.txt updates                                        │
│ Validation:                                                         │
│   - All CLI commands from spec are implemented                      │
│   - --help works for all commands                                   │
│   - All commands support --output json                              │
│   - End-to-end test: embed → analyze → query pipeline               │
│ Gate: Integration tests pass                                        │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 6: CROSS-VALIDATION                                           │
│ Agent: architect                                                    │
│ Input: All outputs from phases 1-5                                  │
│ Tasks:                                                              │
│   - Verify interface contracts are honored                          │
│   - Run full pipeline on 100 sample queries                         │
│   - Compare retrieval quality to success criteria                   │
│   - Identify gaps or inconsistencies                                │
│ Output:                                                             │
│   - validation_report.md                                            │
│   - issues.json (if any)                                            │
│ Gate: All success criteria met OR issues assigned to agents         │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 7: LLM INTEGRATION                                            │
│ Agent: llm_integration_engineer                                     │
│ Input: All src/*.py, subspace/semantic_mapping.json                 │
│ Output:                                                             │
│   - src/iconics_provision.py                                        │
│   - src/iconics_emoji.py                                            │
│   - skill/SKILL.md                                                  │
│   - Updated icon-manager.py with new commands:                      │
│     - batch-query                                                   │
│     - provision                                                     │
│     - scan-emoji                                                    │
│     - convert-emoji                                                 │
│     - generate-imports                                              │
│ Validation:                                                         │
│   - Provisioning copies correct icons to destination                │
│   - Manifest.json generated with correct structure                  │
│   - Emoji scanner detects all emoji types in EMOJI_MAP              │
│   - Convert-emoji dry-run produces valid diff                       │
│   - Generate-imports produces valid React/Vue/CSS/TS                │
│   - SKILL.md contains all required sections                         │
│ Gate: LLM trigger tests pass + architect reviews SKILL.md           │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 8: FINAL VALIDATION                                           │
│ Agent: architect                                                    │
│ Input: All outputs from phases 1-7                                  │
│ Tasks:                                                              │
│   - End-to-end LLM workflow test:                                   │
│     1. Bootstrap new project with batch-query + provision           │
│     2. Scan existing repo for emoji, convert                        │
│     3. Generate framework imports                                   │
│   - Verify SKILL.md triggers work as expected                       │
│   - Performance benchmarks for all new commands                     │
│ Output:                                                             │
│   - final_validation_report.md                                      │
│   - performance_benchmarks.json                                     │
│ Gate: All success criteria met + Human approval                     │
└─────────────────────────────────────────────────────────────────────┘
                                │
                          ┌─────┴─────┐
                          │  ISSUES?  │
                          └─────┬─────┘
                         yes │     │ no
                             ▼     ▼
              ┌──────────────────┐  ┌──────────────────┐
              │  REMEDIATION     │  │  COMPLETION      │
              │  Route issues to │  │  Final report    │
              │  responsible     │  │  Documentation   │
              │  agents, re-run  │  │  Handoff ready   │
              │  affected phases │  │                  │
              └────────┬─────────┘  └──────────────────┘
                       │
                       └──────► (back to relevant phase)
```

---

## Phase Dependencies

```
Phase 0 (Architecture)
    │
    ▼
Phase 1 (Embeddings)
    │
    ▼
Phase 2 (Subspace) ──────────────────┐
    │                                │
    ▼                                │
Phase 3 (Retrieval) ◄────────────────┤
    │                                │
    ▼                                │
Phase 4 (Evaluation)                 │
    │                                │
    ▼                                │
Phase 5 (CLI Integration)            │
    │                                │
    ▼                                │
Phase 6 (Cross-Validation)           │
    │                                │
    ▼                                │
Phase 7 (LLM Integration) ◄──────────┘
    │         │
    │         └─► Needs semantic_mapping.json from Phase 2
    │         └─► Needs IconicsRetriever from Phase 3
    │
    ▼
Phase 8 (Final Validation)
```
