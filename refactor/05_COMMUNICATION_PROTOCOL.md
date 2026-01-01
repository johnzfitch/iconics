# AGENT COMMUNICATION PROTOCOL

## Message Types

```python
from dataclasses import dataclass
from typing import Literal, Callable

@dataclass
class AgentMessage:
    """Standard message format for inter-agent communication."""
    from_agent: str
    to_agent: str
    phase: int
    message_type: Literal["handoff", "query", "validation", "issue", "approval"]
    payload: dict
    requires_response: bool
    priority: Literal["blocking", "normal", "fyi"]
    
@dataclass  
class PhaseOutput:
    """Standard output format for each phase."""
    phase: int
    agent: str
    status: Literal["success", "partial", "failed"]
    files_created: list[str]
    files_modified: list[str]
    validation_results: dict[str, bool]
    metrics: dict[str, float]
    issues: list[str]
    notes_for_next_phase: str
    time_taken_seconds: float

@dataclass
class ValidationGate:
    """Defines pass/fail criteria for phase transitions."""
    phase: int
    checks: list[Callable[[], bool]]
    required_approvals: list[str]  # agent names
    auto_retry_on_fail: bool
    max_retries: int
```

---

## Message Flow Examples

### Handoff Message
```python
AgentMessage(
    from_agent="embedding_engineer",
    to_agent="linear_algebra_specialist",
    phase=1,
    message_type="handoff",
    payload={
        "files_created": [
            "embeddings/icon_embeddings.npy",
            "embeddings/icon_index.json",
            "embeddings/metadata.json"
        ],
        "embedding_shape": [8000, 512],
        "model_used": "ViT-B/32",
        "notes": "All icons embedded successfully. 3 corrupt PNGs skipped."
    },
    requires_response=False,
    priority="normal"
)
```

### Query Message
```python
AgentMessage(
    from_agent="retrieval_engineer",
    to_agent="linear_algebra_specialist",
    phase=3,
    message_type="query",
    payload={
        "query": "What is the recommended threshold for truncating singular values? Should I use explained variance ratio or elbow method?"
    },
    requires_response=True,
    priority="blocking"
)
```

### Issue Message
```python
AgentMessage(
    from_agent="architect",
    to_agent="embedding_engineer",
    phase=6,
    message_type="issue",
    payload={
        "severity": "medium",
        "description": "Embeddings for icons smaller than 16x16 have unusually high norms after normalization. Investigate CLIP preprocessing for small images.",
        "affected_files": ["embeddings/icon_embeddings.npy"],
        "suggested_action": "Add size-based filtering or padding for small icons"
    },
    requires_response=True,
    priority="normal"
)
```

### Approval Message
```python
AgentMessage(
    from_agent="architect",
    to_agent="orchestrator",
    phase=2,
    message_type="approval",
    payload={
        "approved": True,
        "rationale": "Semantic mapping shows strong correlations. PC3 maps to valence (r=0.72), PC7 maps to abstraction (r=0.65). Effective dimension of 47 is reasonable.",
        "conditions": None
    },
    requires_response=False,
    priority="normal"
)
```

### LLM Integration Handoff (Phase 7)
```python
AgentMessage(
    from_agent="integration_engineer",
    to_agent="llm_integration_engineer",
    phase=5,
    message_type="handoff",
    payload={
        "files_created": [
            "src/iconics_retrieval.py",
            "src/iconics_index.py"
        ],
        "cli_commands_available": [
            "embed", "analyze-subspace", "query", "traverse", 
            "interpolate", "eval-retrieval", "residual"
        ],
        "json_output_supported": True,
        "notes": "All core commands support --output json. Retriever includes residual_score in output."
    },
    requires_response=False,
    priority="normal"
)
```

### LLM Integration Query
```python
AgentMessage(
    from_agent="llm_integration_engineer",
    to_agent="linear_algebra_specialist",
    phase=7,
    message_type="query",
    payload={
        "query": "What are the human-readable names for the top 4 semantic axes? I need to populate the SKILL.md axis table with pole descriptions."
    },
    requires_response=True,
    priority="blocking"
)
```

---

## Phase Output Examples

### Successful Phase
```python
PhaseOutput(
    phase=1,
    agent="embedding_engineer",
    status="success",
    files_created=[
        "src/iconics_embeddings.py",
        "embeddings/icon_embeddings.npy",
        "embeddings/icon_index.json",
        "embeddings/metadata.json"
    ],
    files_modified=[],
    validation_results={
        "all_icons_embedded": True,
        "embeddings_normalized": True,
        "no_nan_values": True,
        "count_matches_catalog": True
    },
    metrics={
        "icon_count": 8000,
        "embedding_dim": 512,
        "processing_time_seconds": 342.5,
        "skipped_corrupt": 3
    },
    issues=[],
    notes_for_next_phase="Embeddings ready. Consider using randomized SVD for efficiency given matrix size.",
    time_taken_seconds=412.3
)
```

### Partial Success
```python
PhaseOutput(
    phase=4,
    agent="evaluation_specialist",
    status="partial",
    files_created=[
        "src/iconics_eval.py",
        "eval/ground_truth.json",
        "eval/test_queries.txt"
    ],
    files_modified=[],
    validation_results={
        "metrics_implemented": True,
        "ground_truth_coverage": True,
        "comparison_complete": False  # Failed
    },
    metrics={
        "ground_truth_pairs": 62,
        "query_types_covered": 5
    },
    issues=[
        "SemanticMatcher baseline comparison failed: module import error in icon-manager.py"
    ],
    notes_for_next_phase="Need integration_engineer to expose SemanticMatcher as importable module.",
    time_taken_seconds=287.1
)
```

### LLM Integration Phase Success
```python
PhaseOutput(
    phase=7,
    agent="llm_integration_engineer",
    status="success",
    files_created=[
        "src/iconics_provision.py",
        "src/iconics_emoji.py",
        "skill/SKILL.md"
    ],
    files_modified=[
        "icon-manager.py"  # Added new commands
    ],
    validation_results={
        "provision_copies_icons": True,
        "manifest_generated": True,
        "emoji_scanner_detects_all": True,
        "convert_dry_run_valid": True,
        "react_imports_valid": True,
        "vue_imports_valid": True,
        "css_imports_valid": True,
        "skill_md_complete": True
    },
    metrics={
        "emoji_types_mapped": 27,
        "skill_md_sections": 8,
        "cli_commands_added": 5,
        "provision_test_time_ms": 45
    },
    issues=[],
    notes_for_next_phase="LLM integration complete. SKILL.md ready for deployment to /mnt/skills/user/iconics/",
    time_taken_seconds=523.7
)
```

---

## Cross-Agent Query Examples

### Retrieval Engineer to Linear Algebra Specialist
```python
# Query about projection behavior
AgentMessage(
    from_agent="retrieval_engineer",
    to_agent="linear_algebra_specialist",
    phase=3,
    message_type="query",
    payload={
        "query": "For queries with high orthogonal residual (>0.5), should I still return the projection, or indicate no good match exists?"
    },
    requires_response=True,
    priority="blocking"
)

# Response
AgentMessage(
    from_agent="linear_algebra_specialist",
    to_agent="retrieval_engineer",
    phase=3,
    message_type="query",
    payload={
        "response": "Return results but include residual_score prominently. A score >0.5 means >50% of query energy is outside icon-space. Let the consumer decide threshold. For LLM integration, this is critical for coverage assessment."
    },
    requires_response=False,
    priority="normal"
)
```

### LLM Integration Engineer to Retrieval Engineer
```python
# Query about batch operations
AgentMessage(
    from_agent="llm_integration_engineer",
    to_agent="retrieval_engineer",
    phase=7,
    message_type="query",
    payload={
        "query": "Can IconicsRetriever handle batch queries efficiently? I need to query multiple concepts in one call for project bootstrapping."
    },
    requires_response=True,
    priority="blocking"
)

# Response
AgentMessage(
    from_agent="retrieval_engineer",
    to_agent="llm_integration_engineer",
    phase=7,
    message_type="query",
    payload={
        "response": "Current retrieve() is single-query. For batch, you can call it in a loop, but text embedding has startup cost. Better: add retrieve_batch() that encodes all queries in one CLIP forward pass, then does batch FAISS search. I'll add this to iconics_retrieval.py."
    },
    requires_response=False,
    priority="normal"
)
```

---

## Error Escalation Protocol

```python
def escalate_error(error: Exception, phase: int, agent: str) -> AgentMessage:
    """
    Standard error escalation to architect.
    """
    return AgentMessage(
        from_agent=agent,
        to_agent="architect",
        phase=phase,
        message_type="issue",
        payload={
            "severity": "high",
            "error_type": type(error).__name__,
            "description": str(error),
            "traceback": traceback.format_exc(),
            "suggested_action": "Review and determine if phase can continue or needs restart"
        },
        requires_response=True,
        priority="blocking"
    )
```
