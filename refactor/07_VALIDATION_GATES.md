# VALIDATION GATES

```python
import numpy as np
from pathlib import Path

VALIDATION_GATES = {
    0: ValidationGate(
        phase=0,
        checks=[
            lambda ctx: Path(ctx["workspace"] / "architecture_decision.md").exists(),
            lambda ctx: "interface_contracts" in ctx["architecture_decision"],
        ],
        required_approvals=["human"],
        auto_retry_on_fail=False,
        max_retries=0
    ),
    
    1: ValidationGate(
        phase=1,
        checks=[
            lambda ctx: Path(ctx["workspace"] / "embeddings/icon_embeddings.npy").exists(),
            lambda ctx: ctx["embeddings_shape"][0] == ctx["icon_count"],
            lambda ctx: np.allclose(np.linalg.norm(ctx["embeddings"], axis=1), 1.0, atol=1e-6),
            lambda ctx: not np.any(np.isnan(ctx["embeddings"])),
        ],
        required_approvals=[],
        auto_retry_on_fail=True,
        max_retries=3
    ),
    
    2: ValidationGate(
        phase=2,
        checks=[
            lambda ctx: Path(ctx["workspace"] / "subspace/basis_vectors.npy").exists(),
            lambda ctx: ctx["effective_dim"] < 100,
            lambda ctx: len(ctx["significant_correlations"]) >= 3,
            lambda ctx: ctx["reconstruction_error"] < 1e-10,
        ],
        required_approvals=["architect"],
        auto_retry_on_fail=True,
        max_retries=2
    ),
    
    3: ValidationGate(
        phase=3,
        checks=[
            lambda ctx: Path(ctx["workspace"] / "index/faiss_flat.index").exists(),
            lambda ctx: ctx["query_latency_p50"] < 0.050,
            lambda ctx: ctx["retrieval_unit_tests_passed"],
            lambda ctx: ctx["retrieve_includes_residual_score"],  # NEW: LLM requirement
            lambda ctx: np.isclose(
                np.linalg.norm(ctx["q_proj"])**2 + np.linalg.norm(ctx["q_orth"])**2,
                np.linalg.norm(ctx["q"])**2,
                rtol=1e-5
            ),
        ],
        required_approvals=[],
        auto_retry_on_fail=True,
        max_retries=2
    ),
    
    4: ValidationGate(
        phase=4,
        checks=[
            lambda ctx: len(ctx["ground_truth"]) >= 50,
            lambda ctx: ctx["query_type_coverage"] == 5,
            lambda ctx: "projected_vs_raw" in ctx["comparison_results"],
        ],
        required_approvals=["architect"],
        auto_retry_on_fail=False,
        max_retries=1
    ),
    
    5: ValidationGate(
        phase=5,
        checks=[
            lambda ctx: all(cmd in ctx["cli_commands"] for cmd in 
                ["embed", "analyze-subspace", "query", "traverse", "eval-retrieval"]),
            lambda ctx: ctx["e2e_test_passed"],
            lambda ctx: ctx["backward_compat_test_passed"],
            lambda ctx: ctx["json_output_supported"],  # NEW: All commands support --output json
        ],
        required_approvals=[],
        auto_retry_on_fail=True,
        max_retries=2
    ),
    
    6: ValidationGate(
        phase=6,
        checks=[
            lambda ctx: ctx["success_criteria"]["retrieval_quality"],
            lambda ctx: ctx["success_criteria"]["interpretability"],
            lambda ctx: ctx["success_criteria"]["efficiency"],
            lambda ctx: ctx["success_criteria"]["dimensionality"],
        ],
        required_approvals=["architect"],
        auto_retry_on_fail=False,
        max_retries=0
    ),
    
    7: ValidationGate(
        phase=7,
        checks=[
            # Provisioning checks
            lambda ctx: Path(ctx["workspace"] / "src/iconics_provision.py").exists(),
            lambda ctx: ctx["provision_copies_icons"],
            lambda ctx: ctx["manifest_structure_valid"],
            
            # Emoji scanner checks
            lambda ctx: Path(ctx["workspace"] / "src/iconics_emoji.py").exists(),
            lambda ctx: ctx["emoji_scanner_detects_all_mapped"],
            lambda ctx: ctx["convert_dry_run_produces_diff"],
            
            # Import generation checks
            lambda ctx: ctx["react_imports_valid"],
            lambda ctx: ctx["vue_imports_valid"],
            lambda ctx: ctx["css_imports_valid"],
            
            # SKILL.md checks
            lambda ctx: Path(ctx["workspace"] / "skill/SKILL.md").exists(),
            lambda ctx: ctx["skill_has_trigger_conditions"],
            lambda ctx: ctx["skill_has_command_reference"],
            lambda ctx: ctx["skill_has_emoji_table"],
            lambda ctx: ctx["skill_has_semantic_axes"],
            lambda ctx: ctx["skill_has_decision_tree"],
            
            # CLI command checks
            lambda ctx: all(cmd in ctx["cli_commands"] for cmd in 
                ["batch-query", "provision", "scan-emoji", "convert-emoji", "generate-imports"]),
        ],
        required_approvals=["architect"],
        auto_retry_on_fail=True,
        max_retries=2
    ),
    
    8: ValidationGate(
        phase=8,
        checks=[
            lambda ctx: ctx["success_criteria"]["retrieval_quality"],
            lambda ctx: ctx["success_criteria"]["interpretability"],
            lambda ctx: ctx["success_criteria"]["efficiency"],
            lambda ctx: ctx["success_criteria"]["dimensionality"],
            lambda ctx: ctx["success_criteria"]["llm_integration"],  # NEW
            lambda ctx: ctx["e2e_llm_workflow_passed"],  # NEW
        ],
        required_approvals=["architect", "human"],
        auto_retry_on_fail=False,
        max_retries=0
    ),
}
```

---

## Gate Descriptions

### Phase 0: Architecture Review
| Check | Description |
|-------|-------------|
| `architecture_decision.md` exists | Architect produced design document |
| Contains `interface_contracts` | Module boundaries are defined |
| **Approval**: Human | Manual sign-off on architecture |

### Phase 1: Embedding Generation
| Check | Description |
|-------|-------------|
| `icon_embeddings.npy` exists | Embeddings file created |
| Shape matches icon count | All icons processed |
| L2 norms ≈ 1.0 | Properly normalized |
| No NaN values | Numerical stability |
| **Auto-retry**: Yes (3x) | |

### Phase 2: Subspace Analysis
| Check | Description |
|-------|-------------|
| `basis_vectors.npy` exists | SVD completed |
| Effective dim < 100 | Compression achieved |
| ≥3 significant correlations | Interpretable structure found |
| Reconstruction error < 1e-10 | SVD numerically correct |
| **Approval**: Architect | Review semantic mapping |

### Phase 3: Retrieval Engine
| Check | Description |
|-------|-------------|
| `faiss_flat.index` exists | Index built |
| P50 latency < 50ms | Performance target met |
| Unit tests pass | All methods work |
| Residual score in output | LLM integration ready |
| ‖q_I‖² + ‖q_⊥‖² ≈ ‖q‖² | Projection is orthogonal |
| **Auto-retry**: Yes (2x) | |

### Phase 4: Evaluation Framework
| Check | Description |
|-------|-------------|
| Ground truth ≥ 50 pairs | Sufficient test data |
| 5 query types covered | Comprehensive evaluation |
| Comparison results exist | Baseline vs new system |
| **Approval**: Architect | Review evaluation methodology |

### Phase 5: CLI Integration
| Check | Description |
|-------|-------------|
| All commands implemented | embed, analyze-subspace, query, traverse, eval-retrieval |
| E2E test passes | Full pipeline works |
| Backward compat passes | Existing commands unbroken |
| JSON output supported | All commands have --output json |
| **Auto-retry**: Yes (2x) | |

### Phase 6: Cross-Validation
| Check | Description |
|-------|-------------|
| Retrieval quality | Projected beats raw CLIP |
| Interpretability | ≥3 PCs correlate with metadata |
| Efficiency | Query latency < 50ms |
| Dimensionality | Effective dim < 100 |
| **Approval**: Architect | |

### Phase 7: LLM Integration
| Check | Description |
|-------|-------------|
| `iconics_provision.py` exists | Provisioner implemented |
| Provision copies icons | Files actually copied to dest |
| Manifest structure valid | JSON schema correct |
| `iconics_emoji.py` exists | Emoji scanner implemented |
| Scanner detects all mapped | All EMOJI_MAP entries found |
| Dry-run produces diff | Preview works |
| React imports valid | Syntax correct |
| Vue imports valid | Syntax correct |
| CSS imports valid | Syntax correct |
| `skill/SKILL.md` exists | Skill file generated |
| Has trigger conditions | Section present |
| Has command reference | Section present |
| Has emoji table | Section present |
| Has semantic axes | Section present |
| Has decision tree | Section present |
| New CLI commands | batch-query, provision, scan-emoji, convert-emoji, generate-imports |
| **Approval**: Architect | Review SKILL.md |

### Phase 8: Final Validation
| Check | Description |
|-------|-------------|
| Retrieval quality | Projected beats raw CLIP |
| Interpretability | ≥3 PCs correlate with metadata |
| Efficiency | Query latency < 50ms |
| Dimensionality | Effective dim < 100 |
| LLM integration | SKILL.md functional |
| E2E LLM workflow | Bootstrap + convert + provision works |
| **Approval**: Architect + Human | Final sign-off |

---

## Validation Context Builder

```python
def build_validation_context(workspace: Path, phase: int) -> dict:
    """Build context dict for validation checks."""
    ctx = {"workspace": workspace}
    
    if phase >= 1:
        emb_path = workspace / "embeddings/icon_embeddings.npy"
        if emb_path.exists():
            ctx["embeddings"] = np.load(emb_path)
            ctx["embeddings_shape"] = ctx["embeddings"].shape
        
        catalog = json.load(open(workspace / "icon-catalog.json"))
        ctx["icon_count"] = len(catalog)
    
    if phase >= 2:
        dim_path = workspace / "subspace/effective_dim.json"
        if dim_path.exists():
            dim_data = json.load(open(dim_path))
            ctx["effective_dim"] = dim_data["k"]
        
        corr_path = workspace / "subspace/semantic_mapping.json"
        if corr_path.exists():
            corr_data = json.load(open(corr_path))
            ctx["significant_correlations"] = [
                k for k, v in corr_data.items() 
                if v.get("p_value", 1.0) < 0.01
            ]
        
        # Compute reconstruction error
        if "embeddings" in ctx:
            basis = np.load(workspace / "subspace/basis_vectors.npy")
            projected = ctx["embeddings"] @ basis @ basis.T
            ctx["reconstruction_error"] = np.mean((ctx["embeddings"] - projected)**2)
    
    if phase >= 3:
        # Run latency benchmark
        ctx["query_latency_p50"] = run_latency_benchmark(workspace)
        ctx["retrieval_unit_tests_passed"] = run_unit_tests(workspace)
        
        # Check residual score in output
        ctx["retrieve_includes_residual_score"] = check_residual_in_output(workspace)
        
        # Test projection orthogonality
        q = np.random.randn(512)
        q = q / np.linalg.norm(q)
        ctx["q"] = q
        ctx["q_proj"], ctx["q_orth"] = project_query(workspace, q)
    
    if phase >= 4:
        gt_path = workspace / "eval/ground_truth.json"
        if gt_path.exists():
            gt = json.load(open(gt_path))
            ctx["ground_truth"] = gt
            ctx["query_type_coverage"] = len(set(q["type"] for q in gt))
        
        results_path = workspace / "eval/results/baseline_comparison.json"
        if results_path.exists():
            ctx["comparison_results"] = json.load(open(results_path))
    
    if phase >= 5:
        ctx["cli_commands"] = get_cli_commands(workspace / "icon-manager.py")
        ctx["e2e_test_passed"] = run_e2e_test(workspace)
        ctx["backward_compat_test_passed"] = run_backward_compat_test(workspace)
        ctx["json_output_supported"] = check_json_output_support(workspace)
    
    if phase >= 6:
        ctx["success_criteria"] = evaluate_success_criteria(workspace)
    
    if phase >= 7:
        # Provisioning validation
        ctx["provision_copies_icons"] = test_provision_copies(workspace)
        ctx["manifest_structure_valid"] = validate_manifest_schema(workspace)
        
        # Emoji scanner validation
        ctx["emoji_scanner_detects_all_mapped"] = test_emoji_detection(workspace)
        ctx["convert_dry_run_produces_diff"] = test_convert_dry_run(workspace)
        
        # Import generation validation
        ctx["react_imports_valid"] = validate_react_imports(workspace)
        ctx["vue_imports_valid"] = validate_vue_imports(workspace)
        ctx["css_imports_valid"] = validate_css_imports(workspace)
        
        # SKILL.md validation
        skill_path = workspace / "skill/SKILL.md"
        if skill_path.exists():
            skill_content = skill_path.read_text()
            ctx["skill_has_trigger_conditions"] = "## Trigger Conditions" in skill_content
            ctx["skill_has_command_reference"] = "## Quick Commands" in skill_content
            ctx["skill_has_emoji_table"] = "Emoji" in skill_content and "|" in skill_content
            ctx["skill_has_semantic_axes"] = "## Semantic Axes" in skill_content
            ctx["skill_has_decision_tree"] = "Decision" in skill_content
    
    if phase >= 8:
        ctx["success_criteria"]["llm_integration"] = all([
            ctx.get("provision_copies_icons", False),
            ctx.get("emoji_scanner_detects_all_mapped", False),
            (workspace / "skill/SKILL.md").exists()
        ])
        ctx["e2e_llm_workflow_passed"] = run_llm_workflow_test(workspace)
    
    return ctx


def run_llm_workflow_test(workspace: Path) -> bool:
    """
    End-to-end test of LLM workflow:
    1. Batch query concepts
    2. Provision icons to temp directory
    3. Scan temp files for emoji
    4. Convert emojis
    5. Generate imports
    """
    import tempfile
    import subprocess
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Step 1: Batch query
        concepts = tmpdir + "/concepts.txt"
        Path(concepts).write_text("security lock\nuser profile\nwarning alert")
        
        result = subprocess.run([
            "python", str(workspace / "icon-manager.py"), "batch-query",
            "--input", concepts, "--output", tmpdir + "/results.json", "--k", "1"
        ], capture_output=True)
        if result.returncode != 0:
            return False
        
        # Step 2: Provision
        result = subprocess.run([
            "python", str(workspace / "icon-manager.py"), "provision",
            "--manifest", tmpdir + "/results.json", "--dest", tmpdir + "/icons/"
        ], capture_output=True)
        if result.returncode != 0:
            return False
        
        # Step 3: Create test file with emoji
        test_md = tmpdir + "/test.md"
        Path(test_md).write_text("# 🔒 Security\n\n⚠️ Warning message")
        
        # Step 4: Scan emoji
        result = subprocess.run([
            "python", str(workspace / "icon-manager.py"), "scan-emoji",
            "--path", tmpdir, "--output", tmpdir + "/emoji-report.json"
        ], capture_output=True)
        if result.returncode != 0:
            return False
        
        # Step 5: Generate imports
        result = subprocess.run([
            "python", str(workspace / "icon-manager.py"), "generate-imports",
            "--manifest", tmpdir + "/icons/manifest.json",
            "--format", "react", "--output", tmpdir + "/Icons.tsx"
        ], capture_output=True)
        if result.returncode != 0:
            return False
        
        # Verify outputs exist
        return all([
            Path(tmpdir + "/results.json").exists(),
            Path(tmpdir + "/icons/manifest.json").exists(),
            Path(tmpdir + "/emoji-report.json").exists(),
            Path(tmpdir + "/Icons.tsx").exists()
        ])
```
