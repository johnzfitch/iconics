"""
Synonyms Utilities (local-first)

This module supports:
- Loading seed synonym maps from legacy sources
- Normalizing/deduplicating synonym maps
- Optionally using an on-disk, locally-cached model (Qwen2.5-VL / InternVL3)
  to expand/clean synonyms in a consistent format.

The goal is to keep search + taxonomy robust even when CLIP text embedding
dependencies aren't installed.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from PIL import Image


@dataclass
class SynonymBuildStats:
    concepts: int = 0
    updated: int = 0
    errors: int = 0


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _resolve_synonyms_seed_path(repo_root: Optional[Path] = None) -> Path:
    """
    Resolve the canonical local seed file for synonym expansion.

    The seed lives at `config/synonyms.json` under the repository root. Passing
    a file path is still supported for compatibility, but the default behavior
    no longer depends on legacy manager scripts.
    """
    if repo_root is None:
        return _repo_root() / "config" / "synonyms.json"

    candidate = Path(repo_root)
    if candidate.is_file():
        return candidate
    if candidate.suffix.lower() == ".json":
        return candidate
    if candidate.name == "config":
        return candidate / "synonyms.json"
    return candidate / "config" / "synonyms.json"


def load_concept_synonyms_seed(repo_root: Optional[Path] = None) -> Dict[str, List[str]]:
    """
    Load the local concept synonym seed from config/synonyms.json.
    """
    path = _resolve_synonyms_seed_path(repo_root)
    if not path.exists():
        raise FileNotFoundError(f"Synonyms seed not found: {path}")
    return load_synonyms_json(path)


def _normalize_token(value: str) -> str:
    token = value.strip().lower()
    token = re.sub(r"\s+", "-", token)
    token = re.sub(r"[^a-z0-9\-_]+", "", token)
    token = token.strip("-_")
    return token


def normalize_synonyms_map(data: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """
    Normalize keys and values into lowercase, hyphenated tokens; dedupe and sort.
    """
    out: Dict[str, List[str]] = {}
    for key, values in data.items():
        k = _normalize_token(key)
        if not k:
            continue

        seen = set([k])
        items = []
        for v in values:
            t = _normalize_token(v)
            if not t or t in seen:
                continue
            seen.add(t)
            items.append(t)
        items.sort()
        out[k] = items
    return out


def load_synonyms_json(path: Path) -> Dict[str, List[str]]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Synonyms JSON must be an object: {path}")
    normalized: Dict[str, List[str]] = {}
    for key, values in data.items():
        if not isinstance(key, str) or not isinstance(values, list):
            continue
        normalized[key] = [v for v in values if isinstance(v, str)]
    return normalize_synonyms_map(normalized)


def prune_synonyms_map(data: Dict[str, List[str]], max_synonyms: int) -> Dict[str, List[str]]:
    if max_synonyms <= 0:
        return data
    out: Dict[str, List[str]] = {}
    for k, values in data.items():
        out[k] = list(values)[:max_synonyms]
    return out


def validate_synonyms_map(data: Dict[str, List[str]]) -> List[str]:
    """
    Return a list of human-readable issues. Empty list means OK.
    """
    issues: List[str] = []
    if not isinstance(data, dict):
        return ["Synonyms map must be an object mapping concept -> [synonyms]"]

    for concept, syns in data.items():
        if not isinstance(concept, str) or not concept.strip():
            issues.append("Found invalid concept key (empty or non-string)")
            continue
        if not isinstance(syns, list):
            issues.append(f"{concept}: synonyms must be a list")
            continue

        normalized_concept = _normalize_token(concept)
        if normalized_concept != concept:
            issues.append(f"{concept}: concept is not normalized (expected '{normalized_concept}')")

        seen = set()
        for s in syns:
            if not isinstance(s, str) or not s.strip():
                issues.append(f"{concept}: contains empty/non-string synonym")
                continue
            normalized = _normalize_token(s)
            if normalized != s:
                issues.append(f"{concept}: synonym '{s}' not normalized (expected '{normalized}')")
            if normalized == normalized_concept:
                issues.append(f"{concept}: contains self synonym '{s}'")
            if normalized in seen:
                issues.append(f"{concept}: duplicate synonym '{s}'")
            seen.add(normalized)

    return issues


def diff_synonyms_maps(
    before: Dict[str, List[str]],
    after: Dict[str, List[str]],
) -> Dict[str, Dict[str, List[str]]]:
    """
    Compute a simple per-concept diff.
    Returns: { concept: { "added": [...], "removed": [...] } }
    """
    before = normalize_synonyms_map(before)
    after = normalize_synonyms_map(after)

    all_concepts = sorted(set(before.keys()) | set(after.keys()))
    diff: Dict[str, Dict[str, List[str]]] = {}

    for c in all_concepts:
        b = set(before.get(c, []))
        a = set(after.get(c, []))
        added = sorted(a - b)
        removed = sorted(b - a)
        if added or removed:
            diff[c] = {"added": added, "removed": removed}

    return diff


def merge_synonyms_maps(
    base: Dict[str, List[str]],
    overlay: Dict[str, List[str]],
) -> Dict[str, List[str]]:
    """
    Merge overlay into base, unioning synonym lists per concept.
    """
    base = normalize_synonyms_map(base)
    overlay = normalize_synonyms_map(overlay)
    out: Dict[str, List[str]] = {k: list(v) for k, v in base.items()}

    for concept, syns in overlay.items():
        merged = set(out.get(concept, []))
        merged.update(syns)
        out[concept] = sorted(merged)

    return out


def parse_json_object(text: str) -> Dict:
    """
    Extract and parse a JSON object from a model response.
    """
    s = text.strip()
    if s.startswith("```json"):
        s = s[7:]
    elif s.startswith("```"):
        s = s[3:]
    if s.endswith("```"):
        s = s[:-3]
    s = s.strip()

    start = s.find("{")
    end = s.rfind("}")
    if start != -1 and end != -1 and end > start:
        s = s[start : end + 1]

    return json.loads(s)


def build_synonym_prompt(concept: str, seed: List[str]) -> str:
    return f"""
You are a taxonomy assistant for an icon library.

Given a CONCEPT and an existing list of synonyms, return a cleaned + expanded synonym list.

CONCEPT: {concept}
EXISTING SYNONYMS: {seed}

RULES:
- Output strict JSON only.
- All synonyms must be single tokens: lowercase, hyphenated if needed, no spaces.
- Remove irrelevant synonyms.
- Add 5-15 high-signal synonyms that would realistically appear in icon names/tags.
- Do not include the concept itself in synonyms.

OUTPUT:
{{
  "concept": "{concept}",
  "synonyms": ["..."]
}}
""".strip()


def expand_synonyms_with_vision_model(
    seed_map: Dict[str, List[str]],
    labeler,
    limit: int = 0,
) -> tuple[Dict[str, List[str]], SynonymBuildStats]:
    """
    Use a locally-cached VLM as a text model (with a tiny blank image) to expand synonyms.

    `labeler` is expected to be an instance of iconics_vision.VisionLabeler.
    """
    concepts = list(seed_map.keys())
    if limit and limit > 0:
        concepts = concepts[:limit]

    stats = SynonymBuildStats(concepts=len(concepts))
    out = {k: list(v) for k, v in seed_map.items()}

    blank = Image.new("RGB", (32, 32), (255, 255, 255))

    for concept in concepts:
        try:
            prompt = build_synonym_prompt(concept, out.get(concept, []))
            response = labeler._run_inference(blank, prompt)  # intentionally reuse existing model runner
            obj = parse_json_object(response)
            syns = obj.get("synonyms", [])
            if not isinstance(syns, list):
                raise ValueError("synonyms field is not a list")

            merged = normalize_synonyms_map({concept: syns}).get(concept, [])
            out[concept] = merged
            stats.updated += 1
        except Exception:
            stats.errors += 1

    return out, stats
