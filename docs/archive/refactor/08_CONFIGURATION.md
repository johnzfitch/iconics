# CONFIGURATION

## config.yaml

```yaml
# Orchestration settings
orchestration:
  max_phase_retries: 3
  timeout_per_phase_minutes: 30
  parallel_validation: true
  checkpoint_after_phase: true
  log_level: INFO
  
# Agent configuration  
agents:
  model: "claude-opus-4-20250514"
  temperature: 0.3
  max_tokens: 16000
  timeout_seconds: 300
  
# CLIP embedding settings
embedding:
  clip_model: "ViT-B/32"        # or "ViT-L/14" for higher quality
  batch_size: 64                 # reduce if OOM
  device: "cuda"                 # or "cpu"
  normalize: true
  dtype: "float32"
  
# Subspace analysis settings
subspace:
  max_components: 100            # upper bound on effective dim
  variance_threshold: 0.95       # for automatic k selection
  correlation_pvalue: 0.01       # significance threshold
  min_correlations: 3            # required for interpretability
  
# Retrieval settings
retrieval:
  index_type: "flat"             # "flat", "ivf", or "hnsw"
  latency_target_ms: 50
  default_k: 10
  nprobe: 16                     # for IVF index
  ef_search: 64                  # for HNSW index
  include_residual: true         # always include residual_score in output
  
# Evaluation settings
evaluation:
  min_ground_truth: 50
  query_types:
    - literal
    - conceptual
    - emotional
    - compositional
    - negation
  metrics:
    - precision_at_k
    - recall_at_k
    - mrr
    - ndcg
  k_values: [1, 5, 10, 20]

# LLM Integration settings (NEW)
llm_integration:
  skill_output_path: "skill/SKILL.md"
  
  # Provisioning
  provisioning:
    default_dest: "./assets/icons/"
    manifest_filename: "manifest.json"
    copy_mode: "copy"            # "copy" or "symlink"
    
  # Emoji conversion
  emoji:
    extensions: ["md", "mdx", "tsx", "jsx", "html", "vue"]
    recursive: true
    min_confidence: 0.7          # minimum match confidence to suggest
    
  # Import generation
  imports:
    formats: ["react", "vue", "css", "typescript"]
    
  # Semantic axes for SKILL.md
  axes:
    - name: "valence"
      negative_pole: "danger, error, warning"
      positive_pole: "success, safe, approved"
    - name: "abstraction"
      negative_pole: "literal, concrete, specific"
      positive_pole: "metaphorical, conceptual, general"
    - name: "energy"
      negative_pole: "static, passive, complete"
      positive_pole: "active, dynamic, in-progress"
    - name: "complexity"
      negative_pole: "simple, minimal, clean"
      positive_pole: "detailed, rich, complex"
```

---

## Environment Variables

```bash
# Optional overrides
export ICONICS_WORKSPACE="/home/zack/dev/iconics"
export ICONICS_CLIP_MODEL="ViT-L/14"
export ICONICS_DEVICE="cuda:0"
export ICONICS_LOG_LEVEL="DEBUG"

# LLM Integration
export ICONICS_SKILL_PATH="/mnt/skills/user/iconics/SKILL.md"
export ICONICS_DEFAULT_ICON_DEST="./assets/icons/"

# API keys (if using cloud services)
export ANTHROPIC_API_KEY="sk-ant-..."
```

---

## Config Loader

```python
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Literal
import os

@dataclass
class OrchestrationConfig:
    max_phase_retries: int = 3
    timeout_per_phase_minutes: int = 30
    parallel_validation: bool = True
    checkpoint_after_phase: bool = True
    log_level: str = "INFO"

@dataclass
class AgentConfig:
    model: str = "claude-opus-4-20250514"
    temperature: float = 0.3
    max_tokens: int = 16000
    timeout_seconds: int = 300

@dataclass
class EmbeddingConfig:
    clip_model: str = "ViT-B/32"
    batch_size: int = 64
    device: str = "cuda"
    normalize: bool = True
    dtype: str = "float32"

@dataclass
class SubspaceConfig:
    max_components: int = 100
    variance_threshold: float = 0.95
    correlation_pvalue: float = 0.01
    min_correlations: int = 3

@dataclass
class RetrievalConfig:
    index_type: Literal["flat", "ivf", "hnsw"] = "flat"
    latency_target_ms: int = 50
    default_k: int = 10
    nprobe: int = 16
    ef_search: int = 64
    include_residual: bool = True

@dataclass
class EvaluationConfig:
    min_ground_truth: int = 50
    query_types: list[str] = field(default_factory=lambda: [
        "literal", "conceptual", "emotional", "compositional", "negation"
    ])
    metrics: list[str] = field(default_factory=lambda: [
        "precision_at_k", "recall_at_k", "mrr", "ndcg"
    ])
    k_values: list[int] = field(default_factory=lambda: [1, 5, 10, 20])

@dataclass
class ProvisioningConfig:
    default_dest: str = "./assets/icons/"
    manifest_filename: str = "manifest.json"
    copy_mode: Literal["copy", "symlink"] = "copy"

@dataclass
class EmojiConfig:
    extensions: list[str] = field(default_factory=lambda: [
        "md", "mdx", "tsx", "jsx", "html", "vue"
    ])
    recursive: bool = True
    min_confidence: float = 0.7

@dataclass
class ImportsConfig:
    formats: list[str] = field(default_factory=lambda: [
        "react", "vue", "css", "typescript"
    ])

@dataclass
class SemanticAxis:
    name: str
    negative_pole: str
    positive_pole: str

@dataclass
class LLMIntegrationConfig:
    skill_output_path: str = "skill/SKILL.md"
    provisioning: ProvisioningConfig = field(default_factory=ProvisioningConfig)
    emoji: EmojiConfig = field(default_factory=EmojiConfig)
    imports: ImportsConfig = field(default_factory=ImportsConfig)
    axes: list[SemanticAxis] = field(default_factory=lambda: [
        SemanticAxis("valence", "danger, error, warning", "success, safe, approved"),
        SemanticAxis("abstraction", "literal, concrete", "metaphorical, conceptual"),
        SemanticAxis("energy", "static, complete", "active, in-progress"),
        SemanticAxis("complexity", "simple, minimal", "detailed, rich"),
    ])

@dataclass
class IconicsConfig:
    orchestration: OrchestrationConfig = field(default_factory=OrchestrationConfig)
    agents: AgentConfig = field(default_factory=AgentConfig)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    subspace: SubspaceConfig = field(default_factory=SubspaceConfig)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)
    llm_integration: LLMIntegrationConfig = field(default_factory=LLMIntegrationConfig)
    
    @classmethod
    def load(cls, path: str | Path) -> "IconicsConfig":
        """Load config from YAML file with environment variable overrides."""
        path = Path(path)
        
        if path.exists():
            with open(path) as f:
                data = yaml.safe_load(f)
        else:
            data = {}
        
        config = cls()
        
        # Apply YAML values
        if "orchestration" in data:
            config.orchestration = OrchestrationConfig(**data["orchestration"])
        if "agents" in data:
            config.agents = AgentConfig(**data["agents"])
        if "embedding" in data:
            config.embedding = EmbeddingConfig(**data["embedding"])
        if "subspace" in data:
            config.subspace = SubspaceConfig(**data["subspace"])
        if "retrieval" in data:
            config.retrieval = RetrievalConfig(**data["retrieval"])
        if "evaluation" in data:
            config.evaluation = EvaluationConfig(**data["evaluation"])
        if "llm_integration" in data:
            llm_data = data["llm_integration"]
            config.llm_integration = LLMIntegrationConfig(
                skill_output_path=llm_data.get("skill_output_path", "skill/SKILL.md"),
                provisioning=ProvisioningConfig(**llm_data.get("provisioning", {})),
                emoji=EmojiConfig(**llm_data.get("emoji", {})),
                imports=ImportsConfig(**llm_data.get("imports", {})),
                axes=[SemanticAxis(**a) for a in llm_data.get("axes", [])]
            )
        
        # Apply environment variable overrides
        if os.getenv("ICONICS_CLIP_MODEL"):
            config.embedding.clip_model = os.getenv("ICONICS_CLIP_MODEL")
        if os.getenv("ICONICS_DEVICE"):
            config.embedding.device = os.getenv("ICONICS_DEVICE")
        if os.getenv("ICONICS_LOG_LEVEL"):
            config.orchestration.log_level = os.getenv("ICONICS_LOG_LEVEL")
        if os.getenv("ICONICS_SKILL_PATH"):
            config.llm_integration.skill_output_path = os.getenv("ICONICS_SKILL_PATH")
        if os.getenv("ICONICS_DEFAULT_ICON_DEST"):
            config.llm_integration.provisioning.default_dest = os.getenv("ICONICS_DEFAULT_ICON_DEST")
        
        return config
    
    def save(self, path: str | Path):
        """Save config to YAML file."""
        path = Path(path)
        
        data = {
            "orchestration": {
                "max_phase_retries": self.orchestration.max_phase_retries,
                "timeout_per_phase_minutes": self.orchestration.timeout_per_phase_minutes,
                "parallel_validation": self.orchestration.parallel_validation,
                "checkpoint_after_phase": self.orchestration.checkpoint_after_phase,
                "log_level": self.orchestration.log_level,
            },
            "agents": {
                "model": self.agents.model,
                "temperature": self.agents.temperature,
                "max_tokens": self.agents.max_tokens,
                "timeout_seconds": self.agents.timeout_seconds,
            },
            "embedding": {
                "clip_model": self.embedding.clip_model,
                "batch_size": self.embedding.batch_size,
                "device": self.embedding.device,
                "normalize": self.embedding.normalize,
                "dtype": self.embedding.dtype,
            },
            "subspace": {
                "max_components": self.subspace.max_components,
                "variance_threshold": self.subspace.variance_threshold,
                "correlation_pvalue": self.subspace.correlation_pvalue,
                "min_correlations": self.subspace.min_correlations,
            },
            "retrieval": {
                "index_type": self.retrieval.index_type,
                "latency_target_ms": self.retrieval.latency_target_ms,
                "default_k": self.retrieval.default_k,
                "nprobe": self.retrieval.nprobe,
                "ef_search": self.retrieval.ef_search,
                "include_residual": self.retrieval.include_residual,
            },
            "evaluation": {
                "min_ground_truth": self.evaluation.min_ground_truth,
                "query_types": self.evaluation.query_types,
                "metrics": self.evaluation.metrics,
                "k_values": self.evaluation.k_values,
            },
            "llm_integration": {
                "skill_output_path": self.llm_integration.skill_output_path,
                "provisioning": {
                    "default_dest": self.llm_integration.provisioning.default_dest,
                    "manifest_filename": self.llm_integration.provisioning.manifest_filename,
                    "copy_mode": self.llm_integration.provisioning.copy_mode,
                },
                "emoji": {
                    "extensions": self.llm_integration.emoji.extensions,
                    "recursive": self.llm_integration.emoji.recursive,
                    "min_confidence": self.llm_integration.emoji.min_confidence,
                },
                "imports": {
                    "formats": self.llm_integration.imports.formats,
                },
                "axes": [
                    {"name": a.name, "negative_pole": a.negative_pole, "positive_pole": a.positive_pole}
                    for a in self.llm_integration.axes
                ],
            },
        }
        
        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
```

---

## Usage

```python
# Load default config
config = IconicsConfig()

# Load from file
config = IconicsConfig.load("config.yaml")

# Access settings
print(config.embedding.clip_model)  # "ViT-B/32"
print(config.retrieval.latency_target_ms)  # 50
print(config.llm_integration.skill_output_path)  # "skill/SKILL.md"

# Check LLM integration settings
print(config.llm_integration.provisioning.default_dest)  # "./assets/icons/"
print(config.llm_integration.emoji.extensions)  # ["md", "mdx", "tsx", ...]

# Override and save
config.embedding.clip_model = "ViT-L/14"
config.save("config_highquality.yaml")
```

---

## Emoji Mapping Configuration

The emoji-to-query mapping can be extended via config:

```yaml
# emoji_overrides.yaml
emoji_map:
  "🔒": "lock security"
  "🔐": "lock security private"
  "⚠️": "warning alert"
  "✅": "success check complete"
  # ... add custom mappings
  "🤖": "robot automation ai"  # custom addition
  "🧠": "brain intelligence thinking"  # custom addition
```

Load with:
```python
def load_emoji_overrides(path: str) -> dict:
    with open(path) as f:
        data = yaml.safe_load(f)
    return data.get("emoji_map", {})
```
