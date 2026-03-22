"""
Iconics Vision Relabel Utilities

This module exists to fix large-scale taxonomy drift (e.g. too many 'ui' icons)
by re-running the vision labeler over existing icons and updating the catalog.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional


_SIZE_TOKEN_RE = re.compile(r"^\d+(?:x\d+)?(?:px)?$")
_PLACEHOLDER_HINTS = {
    "all",
    "default",
    "generic",
    "icon",
    "icons",
    "image",
    "pixel",
    "regular",
    "solid",
    "stroke",
    "ui",
    "outline",
    "blank",
    "placeholder",
}


def _normalize_text(value: object) -> str:
    return (
        str(value or "")
        .strip()
        .lower()
        .replace("_", " ")
        .replace("-", " ")
    )


def _tokenize(value: object) -> List[str]:
    normalized = _normalize_text(value)
    if not normalized:
        return []
    return [token for token in re.split(r"[\s\-/]+", normalized) if token]


def _icon_tokens(icon: Dict) -> List[str]:
    tokens: List[str] = []
    for key in ("id", "semanticName", "category"):
        tokens.extend(_tokenize(icon.get(key)))

    tags = icon.get("tags") or []
    if isinstance(tags, list):
        for tag in tags:
            if isinstance(tag, str):
                tokens.extend(_tokenize(tag))

    return tokens


def _is_placeholder_token(token: str) -> bool:
    if not token:
        return False
    if token.isdigit() or _SIZE_TOKEN_RE.match(token):
        return True
    return token in _PLACEHOLDER_HINTS


def placeholder_score(icon: Dict) -> float:
    """
    Score how likely an icon is a placeholder / boilerplate entry.

    Higher scores indicate numeric names, size-only labels, or UI boilerplate
    that should be prioritized in cleanup passes.
    """
    tokens = _icon_tokens(icon)
    if not tokens:
        return 0.0

    total = 0.0
    for token in tokens:
        if token.isdigit():
            total += 1.0
            continue
        if _SIZE_TOKEN_RE.match(token):
            total += 1.0
            continue
        if token in _PLACEHOLDER_HINTS:
            total += 0.65
            continue
        if len(token) <= 2:
            total += 0.15

    semantic = _normalize_text(icon.get("semanticName") or icon.get("id"))
    icon_id = _normalize_text(icon.get("id"))
    if semantic and semantic == icon_id:
        total += 0.25

    if semantic and _SIZE_TOKEN_RE.search(semantic):
        total += 0.15

    tags = icon.get("tags") or []
    if isinstance(tags, list):
        tag_hints = 0
        for tag in tags:
            if not isinstance(tag, str):
                continue
            tag_tokens = _tokenize(tag)
            if tag_tokens and all(_is_placeholder_token(token) for token in tag_tokens):
                tag_hints += 1
        total += 0.1 * tag_hints

    return total / max(len(tokens), 1)


def is_placeholder_icon(icon: Dict, threshold: float = 0.55) -> bool:
    """Return True when an icon looks like boilerplate or placeholder data."""
    return placeholder_score(icon) >= threshold


def iter_placeholder_icons(
    catalog: Dict,
    where_category: Optional[str] = None,
    *,
    threshold: float = 0.55,
) -> Iterable[Dict]:
    """Yield placeholder-heavy icons, optionally scoped to one category."""
    category = _normalize_text(where_category) if where_category else None
    for icon in catalog.get("icons", []):
        if not isinstance(icon, dict):
            continue
        if category is not None and _normalize_text(icon.get("category")) != category:
            continue
        if is_placeholder_icon(icon, threshold=threshold):
            yield icon


@dataclass
class RelabelStats:
    processed: int = 0
    updated: int = 0
    skipped_missing_file: int = 0
    skipped_no_path: int = 0
    errors: int = 0


def iter_icons_for_relabel(
    catalog: Dict,
    where_category: str,
    *,
    predicate: Optional[Callable[[Dict], bool]] = None,
) -> Iterable[Dict]:
    """Yield icons for a targeted relabel pass.

    The category match is normalized so legacy punctuation/spacing differences
    do not block a pass. An optional predicate lets callers further narrow the
    set without changing the existing call shape used by the CLI.
    """
    target_category = _normalize_text(where_category)
    for icon in catalog.get("icons", []):
        if not isinstance(icon, dict):
            continue
        if _normalize_text(icon.get("category")) != target_category:
            continue
        if predicate is not None and not predicate(icon):
            continue
        yield icon


def resolve_icon_path(repo_root: Path, icon: Dict) -> Optional[Path]:
    def _existing(candidate: Path) -> Optional[Path]:
        return candidate if candidate.exists() else None

    path = icon.get("sourceFile") or icon.get("filename")
    if isinstance(path, str) and path.strip():
        p = Path(path)
        if p.is_absolute():
            existing = _existing(p)
            if existing:
                return existing
        else:
            existing = _existing(repo_root / p)
            if existing:
                return existing

    for candidate_id in (icon.get("id"), icon.get("semanticName")):
        if not isinstance(candidate_id, str) or not candidate_id.strip():
            continue
        candidate = repo_root / "raw" / f"{candidate_id.strip()}.png"
        existing = _existing(candidate)
        if existing:
            return existing

    return None


def apply_label_to_icon(icon: Dict, label: Dict, update_fields: List[str]) -> Dict:
    updated = dict(icon)
    if "category" in update_fields and label.get("category"):
        updated["category"] = label["category"]
    if "tags" in update_fields and label.get("tags"):
        updated["tags"] = label["tags"]
    if "description" in update_fields and label.get("description") is not None:
        updated["description"] = label["description"]
    if "enrichment_confidence" in update_fields and label.get("confidence") is not None:
        try:
            updated["enrichment_confidence"] = float(label["confidence"])
        except Exception:
            pass
    return updated
